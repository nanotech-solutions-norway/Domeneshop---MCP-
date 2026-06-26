"""Sanitizers for provider payloads."""

from __future__ import annotations

from typing import Any


REDACT_KEYS = {
    "authorization",
    "code",
    "api_key",
    "apikey",
}


def hidden(value: Any) -> str:
    if value in (None, ""):
        return ""
    return "[REDACTED]"


def redact_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        lower_key = key.lower()
        if lower_key in REDACT_KEYS or "auth" in lower_key:
            sanitized[key] = hidden(value)
        elif isinstance(value, dict):
            sanitized[key] = redact_mapping(value)
        elif isinstance(value, list):
            sanitized[key] = [redact_mapping(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def sanitize_domain(domain: dict[str, Any]) -> dict[str, Any]:
    return redact_mapping(domain)


def sanitize_dns_record(record: dict[str, Any]) -> dict[str, Any]:
    return redact_mapping(record)


def sanitize_forward(forward: dict[str, Any]) -> dict[str, Any]:
    return redact_mapping(forward)


def sanitize_invoice(invoice: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "id",
        "type",
        "amount",
        "currency",
        "due_date",
        "issued_date",
        "paid_date",
        "status",
    }
    return {key: invoice.get(key) for key in allowed if key in invoice}


def sanitize_list(items: Any, sanitizer) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [sanitizer(item) for item in items if isinstance(item, dict)]
