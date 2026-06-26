"""HTTP health diagnostics for Phase 4."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class HealthCheckConfig:
    timeout_seconds: float = 15.0


class HealthDiagnostics:
    def __init__(self, config: HealthCheckConfig | None = None, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or HealthCheckConfig()
        self._client = httpx.Client(timeout=self.config.timeout_seconds, transport=transport, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def check_endpoint(self, url: str) -> dict[str, Any]:
        checked_url = _validate_url(url)
        started = time.perf_counter()
        try:
            response = self._client.get(checked_url)
        except httpx.HTTPError:
            return _result(checked_url, False, "degraded", None, None, None, "Endpoint request failed.")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        status = _classify(response.status_code)
        return _result(
            checked_url,
            status in {"healthy", "protected", "redirect"},
            status,
            response.status_code,
            response.headers.get("content-type"),
            elapsed_ms,
            None,
        )

    def check_json_health(self, url: str) -> dict[str, Any]:
        checked_url = _validate_url(url)
        base = self.check_endpoint(checked_url)
        if not base["success"] or base.get("http_status") is None:
            return base
        try:
            response = self._client.get(checked_url)
            data = response.json()
        except Exception:
            base["success"] = False
            base["status"] = "invalid_json"
            base["message"] = "Endpoint did not return valid JSON."
            return base
        base["json_keys"] = sorted(list(data.keys())) if isinstance(data, dict) else []
        base["json_summary"] = _summarize(data)
        return base

    def check_tls(self, url: str) -> dict[str, Any]:
        checked_url = _validate_url(url)
        parsed = urlparse(checked_url)
        return {
            "success": parsed.scheme == "https",
            "status": "https" if parsed.scheme == "https" else "not_https",
            "url": _safe_url(checked_url),
            "host": parsed.hostname,
        }


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("A valid http or https URL is required.")
    return url


def _classify(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "healthy"
    if status_code in {301, 302, 303, 307, 308}:
        return "redirect"
    if status_code in {401, 403}:
        return "protected"
    if status_code == 404:
        return "not_found"
    if 500 <= status_code:
        return "degraded"
    return "manual_review_required"


def _result(url: str, success: bool, status: str, http_status: int | None, content_type: str | None, elapsed_ms: float | None, message: str | None) -> dict[str, Any]:
    return {
        "success": success,
        "status": status,
        "url": _safe_url(url),
        "http_status": http_status,
        "content_type": content_type,
        "elapsed_ms": elapsed_ms,
        "message": message,
    }


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl()


def _summarize(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"type": type(data).__name__}
    summary: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            summary[key] = value
        else:
            summary[key] = type(value).__name__
    return summary
