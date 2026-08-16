"""Fail-closed, GET-only preparation for the isolated DNS TXT pilot."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .approval_token import ApprovalTokenManager, UsedNonceStore
from .audit_store import AppendOnlyAuditStore
from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .controlled_write import ControlledWriteExecutor, canonical_payload_sha256
from .errors import DomeneshopApiError
from .idempotency import FileIdempotencyStore
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


def _payload(host: str) -> dict[str, Any]:
    return {
        "host": host,
        "data": f"mcp-validation={PILOT_RELEASE_ID}",
        "ttl": 300,
        "type": "TXT",
    }


def _release(target: str) -> ControlledWriteRelease:
    return ControlledWriteRelease.from_dict(
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


def _normalize_domain_name(value: str) -> str:
    domain_name = str(value).strip().lower().rstrip(".")
    labels = domain_name.split(".")
    if not domain_name or len(domain_name) > 253 or len(labels) < 2:
        raise PilotPreflightError("invalid_target")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or re.fullmatch(r"[a-z0-9-]+", label) is None
        for label in labels
    ):
        raise PilotPreflightError("invalid_target")
    return domain_name


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
    payload = _payload(host)
    release = _release(target)
    payload_sha256 = canonical_payload_sha256(payload)

    owned_client = client is None
    read_client = client or DomeneshopReadClient(config)
    try:
        records = read_client.list_dns_records(domain_id, host=host, record_type="TXT")
    except DomeneshopApiError as exc:
        raise PilotPreflightError(exc.error_class) from exc
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
        "domain_name_included": False,
        "host_included": False,
        "payload_included": False,
    }


def validate_dns_txt_pilot_preflight_by_domain_name(
    config: DomeneshopConfig,
    domain_name_value: str,
    *,
    host: str = PILOT_HOST,
    client: DomeneshopReadClient | None = None,
) -> dict[str, Any]:
    """Resolve one exact protected domain name, then run the ID-bound preflight."""

    domain_name = _normalize_domain_name(domain_name_value)
    if config.write_tools_enabled or not config.dry_run_default:
        raise PilotPreflightError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise PilotPreflightError("credential_missing") from exc

    owned_client = client is None
    read_client = client or DomeneshopReadClient(config)
    try:
        domain_id = _resolve_exact_domain_id(read_client, domain_name)
        return validate_dns_txt_pilot_preflight(config, str(domain_id), host=host, client=read_client)
    finally:
        if owned_client:
            read_client.close()


def _resolve_exact_domain_id(read_client: DomeneshopReadClient, domain_name: str) -> int:
    try:
        domains = read_client.list_domains(domain=domain_name)
    except DomeneshopApiError as exc:
        raise PilotPreflightError(exc.error_class) from exc
    except Exception as exc:
        raise PilotPreflightError("provider_read_failed") from exc

    if not isinstance(domains, list):
        raise PilotPreflightError("unexpected_shape")
    matches = [
        item
        for item in domains
        if isinstance(item, dict)
        and str(item.get("domain", "")).strip().lower().rstrip(".") == domain_name
    ]
    if not matches:
        raise PilotPreflightError("target_not_found")
    if len(matches) != 1:
        raise PilotPreflightError("ambiguous_target")

    selected = matches[0]
    try:
        domain_id = int(selected["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PilotPreflightError("unexpected_shape") from exc
    services = selected.get("services")
    if not isinstance(services, dict):
        raise PilotPreflightError("unexpected_shape")
    if services.get("dns") is not True:
        raise PilotPreflightError("dns_service_inactive")
    return domain_id


def validate_dns_txt_pilot_controlled_write_dry_run(
    config: DomeneshopConfig,
    domain_name_value: str,
    signing_secret: str,
    state_root: str | Path,
    *,
    host: str = PILOT_HOST,
    client: DomeneshopReadClient | None = None,
) -> dict[str, Any]:
    """Build an exact-target controlled-write preview without issuing or executing an approval."""

    domain_name = _normalize_domain_name(domain_name_value)
    if config.write_tools_enabled or not config.dry_run_default or host != PILOT_HOST:
        raise PilotPreflightError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise PilotPreflightError("credential_missing") from exc

    state_root_value = str(state_root).strip()
    state_root_path = Path(state_root_value)
    if not state_root_value or not state_root_path.is_absolute():
        raise PilotPreflightError("invalid_state_root")
    root = state_root_path.resolve()
    repository_root = Path.cwd().resolve()
    if root == repository_root or repository_root in root.parents:
        raise PilotPreflightError("invalid_state_root")

    owned_client = client is None
    read_client = client or DomeneshopReadClient(config)
    try:
        domain_id = _resolve_exact_domain_id(read_client, domain_name)
        preflight = validate_dns_txt_pilot_preflight(config, str(domain_id), host=host, client=read_client)
        target = _target(domain_id, host)
        payload = _payload(host)
        release = _release(target)
        try:
            approval_manager = ApprovalTokenManager(signing_secret, UsedNonceStore(root / "approval-nonces"))
        except ValueError as exc:
            raise PilotPreflightError("approval_secret_invalid") from exc
        idempotency_store = FileIdempotencyStore(root / "idempotency")
        audit_path = root / "audit" / "controlled-write.jsonl"
        audit_store = AppendOnlyAuditStore(audit_path)
        executor = ControlledWriteExecutor(release, approval_manager, idempotency_store, audit_store)
        preview = executor.preview(PILOT_ACTION, target, payload)

        if any((root / "approval-nonces").iterdir()):
            raise PilotPreflightError("unexpected_approval_artifact")
        if any((root / "idempotency").iterdir()):
            raise PilotPreflightError("unexpected_idempotency_artifact")
        if audit_path.exists() and audit_path.stat().st_size != 0:
            raise PilotPreflightError("unexpected_audit_artifact")

        return {
            **preflight,
            "evidence_type": "dns_txt_pilot_controlled_write_dry_run",
            "mode": "controlled_write_preview",
            "release_id": release.release_id,
            "allowed_by_manifest": preview["allowed_by_manifest"],
            "live_execution_enabled": preview["live_execution_enabled"],
            "mandatory_controls": preview["requires"],
            "state_directories_ready": True,
            "approval_signing_secret_validated": True,
            "approval_token_issued": False,
            "idempotency_reservation_created": False,
            "audit_event_created": False,
            "provider_mutation_performed": False,
            "target_included": False,
        }
    finally:
        if owned_client:
            read_client.close()
