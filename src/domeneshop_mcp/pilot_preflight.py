"""Fail-closed, GET-only preparation for the isolated DNS TXT pilot."""

from __future__ import annotations

import hashlib
from typing import Any

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .controlled_write import canonical_payload_sha256
from .write_release import ControlledWriteRelease

PILOT_ACTION = "domeneshop_create_dns_txt"
PILOT_HOST = "_mcp-validation"
PILOT_RELEASE_ID = "D-R3-TXT-PREFLIGHT-20260810"


class PilotPreflightError(RuntimeError):
    """A sanitized pilot-preparation failure."""

    def __init__(self, error_class: str) -> None:
        super().__init__(error_class)
        self.error_class = error_class


def _target(domain_id: int, host: str) -> str:
    return f"domain:{domain_id}:dns:{host}"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_dns_txt_pilot_preflight(
    config: DomeneshopConfig,
    domain_id_value: str,
    *,
    host: str = PILOT_HOST,
    client: DomeneshopReadClient | None = None,
) -> dict[str, Any]:
    """Pre-read one exact TXT target and emit no provider or target payload."""

    try:
        domain_id = int(domain_id_value)
    except (TypeError, ValueError) as exc:
        raise PilotPreflightError("invalid_target") from exc
    if domain_id <= 0 or host != PILOT_HOST:
        raise PilotPreflightError("invalid_target")
    if config.write_tools_enabled or not config.dry_run_default:
        raise PilotPreflightError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise PilotPreflightError("credential_missing") from exc

    target = _target(domain_id, host)
    payload = {
        "host": host,
        "data": f"mcp-validation={PILOT_RELEASE_ID}",
        "ttl": 300,
        "type": "TXT",
    }
    release = ControlledWriteRelease.from_dict(
        {
            "release_id": PILOT_RELEASE_ID,
            "environment": "isolated-preflight",
            "decision": "APPROVE_CONTROLLED_WRITE_FOUNDATION",
            "approved_tools": [PILOT_ACTION],
            "approved_target_prefixes": [target],
            "live_execution_enabled": False,
            "controls": {
                "require_approval_token": True,
                "require_idempotency": True,
                "require_audit": True,
                "require_readback": True,
            },
        }
    )
    payload_sha256 = canonical_payload_sha256(payload)

    owned_client = client is None
    read_client = client or DomeneshopReadClient(config)
    try:
        records = read_client.list_dns_records(domain_id, host=host, record_type="TXT")
    except Exception as exc:
        raise PilotPreflightError("provider_read_failed") from exc
    finally:
        if owned_client:
            read_client.close()

    if not isinstance(records, list):
        raise PilotPreflightError("unexpected_shape")
    if records:
        raise PilotPreflightError("target_not_isolated")

    return {
        "evidence_type": "dns_txt_pilot_preflight",
        "success": True,
        "status": "ok",
        "mode": "read_only_dry_run",
        "target_sha256": _sha256(target),
        "payload_sha256": payload_sha256,
        "existing_txt_record_count": 0,
        "collision_detected": False,
        "allowed_by_manifest": release.allows(PILOT_ACTION, target),
        "live_execution_enabled": release.live_execution_enabled,
        "write_tools_enabled": config.write_tools_enabled,
        "provider_mutation_performed": False,
        "domain_id_included": False,
        "host_included": False,
        "payload_included": False,
    }
