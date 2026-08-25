"""Fail-closed, GET-only preparation for the isolated HTTP-forward pilot."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .controlled_write import canonical_payload_sha256
from .errors import DomeneshopApiError

PILOT_FORWARD_HOST = "mcp-forward-validation"
PILOT_FORWARD_URL = "https://atlas-mcp-sandbox.no/"
PILOT_RELEASE_ID = "D-R4B-HTTP-FORWARD-PREFLIGHT-20260825"
BLOCKING_DNS_TYPES = frozenset({"A", "AAAA", "ANAME", "CNAME"})


class HttpForwardPreflightError(RuntimeError):
    """A sanitized HTTP-forward pilot-preparation failure."""

    def __init__(self, error_class: str) -> None:
        super().__init__(error_class)
        self.error_class = error_class


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_domain_name(value: str) -> str:
    domain_name = str(value).strip().lower().rstrip(".")
    labels = domain_name.split(".")
    if not domain_name or len(domain_name) > 253 or len(labels) < 2:
        raise HttpForwardPreflightError("invalid_target")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or re.fullmatch(r"[a-z0-9-]+", label) is None
        for label in labels
    ):
        raise HttpForwardPreflightError("invalid_target")
    return domain_name


def _resolve_exact_domain_id(read_client: DomeneshopReadClient, domain_name: str) -> int:
    try:
        domains = read_client.list_domains(domain=domain_name)
    except DomeneshopApiError as exc:
        raise HttpForwardPreflightError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardPreflightError("provider_read_failed") from exc

    if not isinstance(domains, list):
        raise HttpForwardPreflightError("unexpected_shape")
    matches = [
        item
        for item in domains
        if isinstance(item, dict)
        and str(item.get("domain", "")).strip().lower().rstrip(".") == domain_name
    ]
    if not matches:
        raise HttpForwardPreflightError("target_not_found")
    if len(matches) != 1:
        raise HttpForwardPreflightError("ambiguous_target")

    selected = matches[0]
    try:
        domain_id = int(selected["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HttpForwardPreflightError("unexpected_shape") from exc
    services = selected.get("services")
    if not isinstance(services, dict):
        raise HttpForwardPreflightError("unexpected_shape")
    if services.get("dns") is not True:
        raise HttpForwardPreflightError("dns_service_inactive")
    return domain_id


def _target(domain_id: int, host: str) -> str:
    return f"domain:{domain_id}:forward:{host}"


def _payload(host: str) -> dict[str, Any]:
    return {"host": host, "frame": False, "url": PILOT_FORWARD_URL}


def validate_http_forward_pilot_preflight(
    config: DomeneshopConfig,
    domain_name_value: str,
    *,
    host: str = PILOT_FORWARD_HOST,
    client: DomeneshopReadClient | None = None,
) -> dict[str, Any]:
    """Resolve one sandbox target and verify forward/DNS collision absence using GET only."""

    domain_name = _normalize_domain_name(domain_name_value)
    if host != PILOT_FORWARD_HOST:
        raise HttpForwardPreflightError("invalid_target")
    if config.write_tools_enabled or not config.dry_run_default:
        raise HttpForwardPreflightError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise HttpForwardPreflightError("credential_missing") from exc

    owned_client = client is None
    read_client = client or DomeneshopReadClient(config)
    try:
        domain_id = _resolve_exact_domain_id(read_client, domain_name)
        try:
            forwards = read_client.list_http_forwards(domain_id)
            dns_records = read_client.list_dns_records(domain_id, host=host)
        except DomeneshopApiError as exc:
            raise HttpForwardPreflightError(exc.error_class) from exc
        except Exception as exc:
            raise HttpForwardPreflightError("provider_read_failed") from exc
    finally:
        if owned_client:
            read_client.close()

    if not isinstance(forwards, list) or not isinstance(dns_records, list):
        raise HttpForwardPreflightError("unexpected_shape")

    matching_forwards = [
        item for item in forwards
        if isinstance(item, dict) and str(item.get("host", "")).strip() == host
    ]
    blocking_dns = [
        item for item in dns_records
        if isinstance(item, dict)
        and str(item.get("host", "")).strip() == host
        and str(item.get("type", "")).strip().upper() in BLOCKING_DNS_TYPES
    ]
    if matching_forwards or blocking_dns:
        raise HttpForwardPreflightError("target_not_isolated")

    target = _target(domain_id, host)
    payload = _payload(host)
    return {
        "evidence_type": "http_forward_pilot_preflight",
        "release_id": PILOT_RELEASE_ID,
        "success": True,
        "status": "isolated_target_available",
        "mode": "read_only_dry_run",
        "target_sha256": _sha256(target),
        "payload_sha256": canonical_payload_sha256(payload),
        "existing_forward_count": 0,
        "blocking_dns_record_count": 0,
        "collision_detected": False,
        "write_tools_enabled": config.write_tools_enabled,
        "dry_run_default": config.dry_run_default,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "provider_mutation_performed": False,
        "domain_id_included": False,
        "domain_name_included": False,
        "host_included": False,
        "payload_included": False,
    }
