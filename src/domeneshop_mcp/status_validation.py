"""Sanitized GET-only validation for the Domeneshop status surface."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

import httpx

from .errors import classify_status

DEFAULT_STATUS_URL = "https://ds.atlas-ai.no/"
ALLOWED_STATUS_HOST = "ds.atlas-ai.no"
MAX_STATUS_BYTES = 65_536


class StatusValidationError(RuntimeError):
    """A sanitized status-surface validation failure."""

    def __init__(self, error_class: str) -> None:
        super().__init__(error_class)
        self.error_class = error_class


def validate_status_surface(
    url: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Perform one bounded unauthenticated GET and return payload-free evidence."""

    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_STATUS_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise StatusValidationError("invalid_target")

    client = httpx.Client(timeout=15.0, follow_redirects=False, transport=transport)
    try:
        try:
            with client.stream(
                "GET",
                url,
                headers={"Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    raise StatusValidationError(classify_status(response.status_code))
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_STATUS_BYTES:
                        raise StatusValidationError("response_too_large")
        except StatusValidationError:
            raise
        except httpx.HTTPError as exc:
            raise StatusValidationError("provider_error") from exc

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StatusValidationError("invalid_json") from exc
        if not isinstance(payload, dict):
            raise StatusValidationError("unexpected_shape")

        return {
            "evidence_type": "status_surface_get",
            "success": True,
            "status": "ok",
            "mode": "read_only_http_get",
            "http_status": 200,
            "authentication_sent": False,
            "json_object": True,
            "json_key_count": len(payload),
            "payload_included": False,
        }
    finally:
        client.close()
