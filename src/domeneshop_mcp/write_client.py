"""Approval-external Domeneshop DNS mutation adapter.

This client implements provider calls only. It must be invoked through the
controlled-write executor, which owns approval, idempotency, audit, backup,
and readback enforcement. The adapter is not registered by the read-only MCP
server.
"""
from __future__ import annotations

from typing import Any

import httpx

from .config import DomeneshopConfig
from .errors import DomeneshopApiError, classify_status

VALID_DNS_TYPES = frozenset({"A", "AAAA", "CNAME", "ANAME", "TLSA", "MX", "SRV", "DS", "CAA", "NS", "TXT"})
COMMON_KEYS = frozenset({"host", "data", "ttl", "type"})
TYPE_KEYS = {
    "MX": frozenset({"priority"}),
    "SRV": frozenset({"priority", "weight", "port"}),
    "TLSA": frozenset({"usage", "selector", "dtype"}),
    "DS": frozenset({"tag", "alg", "digest"}),
    "CAA": frozenset({"flags", "tag"}),
}


class DomeneshopWriteClient:
    """Bounded DNS mutation adapter with a default TXT-only pilot allowlist."""

    def __init__(
        self,
        config: DomeneshopConfig,
        *,
        allowed_record_types: frozenset[str] = frozenset({"TXT"}),
        allow_delete: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config
        self.allowed_record_types = frozenset(item.upper() for item in allowed_record_types)
        self.allow_delete = allow_delete
        self._client = httpx.Client(
            base_url=config.api_base_url,
            auth=(config.auth_user, config.auth_value) if config.has_auth else None,
            timeout=config.timeout_seconds,
            transport=transport,
            headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "domeneshop-mcp/0.9.0"},
        )

    def close(self) -> None:
        self._client.close()

    def _require_write_ready(self) -> None:
        self.config.require_auth()
        if not self.config.write_tools_enabled:
            raise DomeneshopApiError("write_paused", "Domeneshop write operations are disabled.")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> httpx.Response:
        self._require_write_ready()
        try:
            response = self._client.request(method, path, json=payload)
        except httpx.HTTPError as exc:
            raise DomeneshopApiError("provider_error", "Domeneshop API mutation request failed.") from exc
        if response.status_code >= 400:
            raise DomeneshopApiError(
                classify_status(response.status_code),
                "Domeneshop API returned an error status for a mutation request.",
                status_code=response.status_code,
            )
        return response

    def _validate_record(self, record: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record)
        record_type = str(normalized.get("type", "")).upper()
        normalized["type"] = record_type
        if record_type not in VALID_DNS_TYPES:
            raise ValueError("DNS record type is not supported by the provider adapter")
        if record_type not in self.allowed_record_types:
            raise ValueError("DNS record type is outside the active write release allowlist")
        required = COMMON_KEYS | TYPE_KEYS.get(record_type, frozenset())
        if set(normalized) != required:
            raise ValueError(f"DNS record keys must be exactly: {', '.join(sorted(required))}")
        if not isinstance(normalized.get("ttl"), int) or int(normalized["ttl"]) <= 0:
            raise ValueError("DNS record ttl must be a positive integer")
        if not str(normalized.get("host", "")).strip():
            raise ValueError("DNS record host is required")
        if not str(normalized.get("data", "")).strip():
            raise ValueError("DNS record data is required")
        return normalized

    def create_dns_record(self, domain_id: int, record: dict[str, Any]) -> int:
        payload = self._validate_record(record)
        response = self._request("POST", f"/domains/{int(domain_id)}/dns", payload)
        location = response.headers.get("location")
        if not location:
            raise DomeneshopApiError("invalid_provider_response", "Created DNS record response did not include Location header.")
        try:
            return int(location.rstrip("/").split("/")[-1])
        except ValueError as exc:
            raise DomeneshopApiError("invalid_provider_response", "Created DNS record Location header was invalid.") from exc

    def update_dns_record(self, domain_id: int, record_id: int, record: dict[str, Any]) -> None:
        payload = self._validate_record(record)
        self._request("PUT", f"/domains/{int(domain_id)}/dns/{int(record_id)}", payload)

    def delete_dns_record(self, domain_id: int, record_id: int) -> None:
        if not self.allow_delete:
            raise DomeneshopApiError("manual_review_required", "DNS deletion is not enabled for the active pilot release.")
        self._request("DELETE", f"/domains/{int(domain_id)}/dns/{int(record_id)}")
