"""Read-only MCP tool handlers for Domeneshop API Phase 2."""

from __future__ import annotations

from typing import Callable

from .client import DomeneshopReadClient
from .envelope import ToolEnvelope, error, ok
from .errors import DomeneshopApiError
from .sanitizers import (
    sanitize_dns_record,
    sanitize_domain,
    sanitize_forward,
    sanitize_invoice,
    sanitize_list,
)


def _call(operation: Callable[[], object], sanitizer: Callable[[dict], dict] | None = None) -> ToolEnvelope:
    try:
        data = operation()
        if isinstance(data, list) and sanitizer:
            return ok(sanitize_list(data, sanitizer))
        if isinstance(data, dict) and sanitizer:
            return ok(sanitizer(data))
        return ok(data)
    except ValueError as exc:
        return error("credential_missing", str(exc))
    except DomeneshopApiError as exc:
        return error(exc.error_class, exc.message)
    except Exception:
        return error("unexpected_error", "Unexpected Domeneshop read connector error.")


def list_domains(client: DomeneshopReadClient, domain: str | None = None) -> ToolEnvelope:
    return _call(lambda: client.list_domains(domain=domain), sanitize_domain)


def get_domain(client: DomeneshopReadClient, domain_id: int) -> ToolEnvelope:
    return _call(lambda: client.get_domain(domain_id), sanitize_domain)


def list_dns_records(
    client: DomeneshopReadClient,
    domain_id: int,
    host: str | None = None,
    record_type: str | None = None,
) -> ToolEnvelope:
    return _call(lambda: client.list_dns_records(domain_id, host=host, record_type=record_type), sanitize_dns_record)


def get_dns_record(client: DomeneshopReadClient, domain_id: int, record_id: int) -> ToolEnvelope:
    return _call(lambda: client.get_dns_record(domain_id, record_id), sanitize_dns_record)


def list_http_forwards(client: DomeneshopReadClient, domain_id: int) -> ToolEnvelope:
    return _call(lambda: client.list_http_forwards(domain_id), sanitize_forward)


def get_http_forward(client: DomeneshopReadClient, domain_id: int, host: str) -> ToolEnvelope:
    return _call(lambda: client.get_http_forward(domain_id, host), sanitize_forward)


def list_invoices(client: DomeneshopReadClient, status: str | None = None) -> ToolEnvelope:
    return _call(lambda: client.list_invoices(status=status), sanitize_invoice)


def get_invoice(client: DomeneshopReadClient, invoice_id: int) -> ToolEnvelope:
    return _call(lambda: client.get_invoice(invoice_id), sanitize_invoice)
