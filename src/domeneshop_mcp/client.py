"""Read-only Domeneshop API client."""

from __future__ import annotations

from typing import Any

import httpx

from .config import DomeneshopConfig
from .errors import DomeneshopApiError, classify_status


class DomeneshopReadClient:
    """Small Domeneshop API client for Phase 2 read operations only."""

    def __init__(self, config: DomeneshopConfig, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=config.api_base_url,
            auth=(config.auth_user, config.auth_value) if config.has_auth else None,
            timeout=config.timeout_seconds,
            transport=transport,
            headers={"Accept": "application/json", "User-Agent": "domeneshop-mcp/0.2.0"},
        )

    def close(self) -> None:
        self._client.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self.config.require_auth()
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise DomeneshopApiError("provider_error", "Domeneshop API request failed.") from exc

        if response.status_code >= 400:
            raise DomeneshopApiError(
                classify_status(response.status_code),
                "Domeneshop API returned an error status.",
                status_code=response.status_code,
            )

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise DomeneshopApiError("invalid_provider_response", "Domeneshop API returned non-JSON content.") from exc

    def list_domains(self, domain: str | None = None) -> Any:
        params = {"domain": domain} if domain else None
        return self._get("/domains", params=params)

    def get_domain(self, domain_id: int) -> Any:
        return self._get(f"/domains/{domain_id}")

    def list_dns_records(self, domain_id: int, host: str | None = None, record_type: str | None = None) -> Any:
        params: dict[str, Any] = {}
        if host:
            params["host"] = host
        if record_type:
            params["type"] = record_type.upper()
        return self._get(f"/domains/{domain_id}/dns", params=params or None)

    def get_dns_record(self, domain_id: int, record_id: int) -> Any:
        return self._get(f"/domains/{domain_id}/dns/{record_id}")

    def list_http_forwards(self, domain_id: int) -> Any:
        return self._get(f"/domains/{domain_id}/forwards/")

    def get_http_forward(self, domain_id: int, host: str) -> Any:
        return self._get(f"/domains/{domain_id}/forwards/{host}")

    def list_invoices(self, status: str | None = None) -> Any:
        params = {"status": status} if status else None
        return self._get("/invoices", params=params)

    def get_invoice(self, invoice_id: int) -> Any:
        return self._get(f"/invoices/{invoice_id}")
