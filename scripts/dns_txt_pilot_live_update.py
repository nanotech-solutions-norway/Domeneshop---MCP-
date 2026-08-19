"""Execute the single authorized D-R3 DNS TXT UPDATE on the isolated target.

Safety properties:
- fresh authenticated target resolution and exact CREATE-state pre-read;
- exact accepted target, before-state, and UPDATE payload hashes must match;
- exact UPDATE-only live release manifest written outside Git;
- one-time payload-bound approval token;
- fixed idempotency identity for replay protection;
- append-only audit and independent provider readback;
- no CREATE or DELETE capability;
- rollback is deliberately non-mutating because restore/delete needs separate authorization;
- live manifest is disabled again in a finally block.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from domeneshop_mcp.approval_token import ApprovalTokenManager, UsedNonceStore
from domeneshop_mcp.audit_store import AppendOnlyAuditStore
from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.controlled_write import ControlledWriteError, ControlledWriteExecutor, ControlledWriteRequest, canonical_payload_sha256
from domeneshop_mcp.idempotency import FileIdempotencyStore
from domeneshop_mcp.pilot_preflight import PILOT_HOST, _normalize_domain_name, _payload as create_payload, _resolve_exact_domain_id, _target
from domeneshop_mcp.write_client import DomeneshopWriteClient
from domeneshop_mcp.write_release import ControlledWriteRelease
from dns_txt_pilot_update_dry_run import update_payload

UPDATE_ACTION = "domeneshop_update_dns_txt"
RELEASE_ID = "D-R3-TXT-UPDATE-20260819-001"
APPROVAL_ID = "D-R3-TXT-UPDATE-20260819-001"
IDEMPOTENCY_KEY = "D-R3-TXT-UPDATE-20260819-001"
EXPECTED_TARGET_SHA256 = "5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e"
EXPECTED_BEFORE_PAYLOAD_SHA256 = "6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c"
EXPECTED_UPDATE_PAYLOAD_SHA256 = "58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087"
AUTHORIZATION_PHRASE = "AUTHORIZE_D_R3_TXT_UPDATE"

class LiveUpdateError(RuntimeError):
    pass

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)

def _runtime_config(base: DomeneshopConfig, *, write_enabled: bool) -> DomeneshopConfig:
    return DomeneshopConfig(api_base_url=base.api_base_url, auth_user=base.auth_user, auth_value=base.auth_value, write_tools_enabled=write_enabled, dry_run_default=not write_enabled, require_operator_approval=True, timeout_seconds=base.timeout_seconds)

def _manifest(target: str, *, enabled: bool, decision: str) -> dict[str, Any]:
    return {"release_id": RELEASE_ID, "environment": "isolated-live-pilot", "decision": decision, "approved_tools": [UPDATE_ACTION], "approved_target_prefixes": [target], "live_execution_enabled": enabled, "controls": {"require_approval_token": True, "require_idempotency": True, "require_audit": True, "require_readback": True}}

def _matches_payload(record: dict[str, Any], payload: dict[str, Any]) -> bool:
    for key, expected in payload.items():
        observed = record.get(key)
        if key == "type":
            if str(observed).upper() != str(expected).upper():
                return False
        elif observed != expected:
            return False
    return True

class TxtUpdateAdapter:
    def __init__(self, *, read_client: DomeneshopReadClient, write_client: DomeneshopWriteClient, domain_id: int, record_id: int, target: str, before_payload: dict[str, Any], payload: dict[str, Any]) -> None:
        self.read_client = read_client
        self.write_client = write_client
        self.domain_id = domain_id
        self.record_id = record_id
        self.target = target
        self.before_payload = before_payload
        self.payload = payload
        self.provider_update_returned = False

    def pre_read(self, target: str) -> dict[str, Any] | None:
        if target != self.target:
            raise ControlledWriteError("Target changed before provider execution")
        record = self.read_client.get_dns_record(self.domain_id, self.record_id)
        if not isinstance(record, dict) or not _matches_payload(record, self.before_payload):
            raise ControlledWriteError("Exact TXT record no longer matches accepted CREATE state")
        return {"existing_create_state_verified": True, "before_payload_sha256": canonical_payload_sha256(self.before_payload), "record_id_sha256": _sha256(str(self.record_id))}

    def execute(self, action: str, target: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != UPDATE_ACTION or target != self.target:
            raise ControlledWriteError("Mutation is outside the authorized UPDATE scope")
        if canonical_payload_sha256(payload) != EXPECTED_UPDATE_PAYLOAD_SHA256:
            raise ControlledWriteError("Payload hash changed before provider execution")
        self.write_client.update_dns_record(self.domain_id, self.record_id, payload)
        self.provider_update_returned = True
        return {"provider_update_returned": True, "record_id_sha256": _sha256(str(self.record_id))}

    def read_back(self, target: str, result: dict[str, Any]) -> dict[str, Any] | None:
        if target != self.target:
            raise ControlledWriteError("Target changed before provider readback")
        record = self.read_client.get_dns_record(self.domain_id, self.record_id)
        if not isinstance(record, dict) or not _matches_payload(record, self.payload):
            raise ControlledWriteError("Provider readback did not match the authorized UPDATE payload")
        return {"verified": True, "record_id_sha256": _sha256(str(self.record_id)), "payload_sha256": canonical_payload_sha256(self.payload)}

    def rollback(self, action: str, target: str, before: dict[str, Any] | None, result: dict[str, Any] | None) -> dict[str, Any] | None:
        return {"status": "not_performed", "reason": "separate_restore_or_delete_authorization_required"}

def main() -> int:
    manifest_path: Path | None = None
    target_for_disable: str | None = None
    read_client: DomeneshopReadClient | None = None
    write_client: DomeneshopWriteClient | None = None
    adapter: TxtUpdateAdapter | None = None
    try:
        if os.environ.get("D_R3_UPDATE_AUTHORIZATION_PHRASE", "") != AUTHORIZATION_PHRASE:
            raise LiveUpdateError("exact_operator_authorization_missing")
        if os.environ.get("DS_PILOT_TXT_HOST", PILOT_HOST) != PILOT_HOST:
            raise LiveUpdateError("invalid_txt_host")
        if os.environ.get("WRITE_TOOLS_ENABLED", "").strip().lower() != "true":
            raise LiveUpdateError("write_switch_not_explicitly_enabled_for_process")
        if os.environ.get("DRY_RUN_DEFAULT", "").strip().lower() != "false":
            raise LiveUpdateError("dry_run_flag_not_explicitly_disabled_for_authorized_process")
        if os.environ.get("REQUIRE_OPERATOR_APPROVAL", "").strip().lower() != "true":
            raise LiveUpdateError("operator_approval_control_disabled")

        state_root_value = os.environ.get("PILOT_STATE_ROOT", "").strip()
        if not state_root_value:
            raise LiveUpdateError("pilot_state_root_missing")
        root = Path(state_root_value)
        if not root.is_absolute():
            raise LiveUpdateError("pilot_state_root_must_be_absolute")
        root = root.resolve()
        repository_root = Path.cwd().resolve()
        if root == repository_root or repository_root in root.parents:
            raise LiveUpdateError("pilot_state_root_inside_repository")

        signing_secret = os.environ.get("APPROVAL_SIGNING_SECRET", "")
        operator = os.environ.get("D_R3_OPERATOR", "").strip()
        domain_name = _normalize_domain_name(os.environ.get("DS_PILOT_DOMAIN_NAME", ""))
        if not operator:
            raise LiveUpdateError("operator_identity_missing")

        base = DomeneshopConfig.from_env()
        if not base.has_auth:
            raise LiveUpdateError("provider_credentials_missing")
        read_config = _runtime_config(base, write_enabled=False)
        write_config = _runtime_config(base, write_enabled=True)
        read_client = DomeneshopReadClient(read_config)
        domain_id = _resolve_exact_domain_id(read_client, domain_name)
        target = _target(domain_id, PILOT_HOST)
        before_payload = create_payload(PILOT_HOST)
        payload = update_payload()
        target_for_disable = target

        target_sha256 = _sha256(target)
        before_sha256 = canonical_payload_sha256(before_payload)
        payload_sha256 = canonical_payload_sha256(payload)
        if target_sha256 != EXPECTED_TARGET_SHA256:
            raise LiveUpdateError("accepted_target_hash_mismatch")
        if before_sha256 != EXPECTED_BEFORE_PAYLOAD_SHA256:
            raise LiveUpdateError("accepted_before_payload_hash_mismatch")
        if payload_sha256 != EXPECTED_UPDATE_PAYLOAD_SHA256:
            raise LiveUpdateError("accepted_update_payload_hash_mismatch")

        records = read_client.list_dns_records(domain_id, host=PILOT_HOST, record_type="TXT")
        if not isinstance(records, list):
            raise LiveUpdateError("provider_pre_read_unexpected_shape")
        if len(records) != 1:
            raise LiveUpdateError("expected_exactly_one_txt_record")
        record = records[0]
        if not isinstance(record, dict) or not _matches_payload(record, before_payload):
            raise LiveUpdateError("existing_txt_record_does_not_match_accepted_create_state")
        record_id = record.get("id")
        if not isinstance(record_id, int):
            raise LiveUpdateError("existing_txt_record_id_missing")

        manifest_path = root / "controlled-write-release-manifest.json"
        live_manifest = _manifest(target, enabled=True, decision="APPROVE_CONTROLLED_WRITE_PILOT")
        release = ControlledWriteRelease.from_dict(live_manifest)
        if release.approved_tools != frozenset({UPDATE_ACTION}):
            raise LiveUpdateError("live_manifest_tool_scope_invalid")
        if release.approved_target_prefixes != (target,):
            raise LiveUpdateError("live_manifest_target_scope_invalid")
        _atomic_json(manifest_path, live_manifest)

        nonce_store = UsedNonceStore(root / "approval-nonces")
        idempotency_store = FileIdempotencyStore(root / "idempotency")
        audit_store = AppendOnlyAuditStore(root / "audit" / "controlled-write.jsonl")
        approval_manager = ApprovalTokenManager(signing_secret, nonce_store)
        executor = ControlledWriteExecutor(release, approval_manager, idempotency_store, audit_store)
        approval_token = approval_manager.issue(approval_id=APPROVAL_ID, operator=operator, action=UPDATE_ACTION, target=target, payload_sha256=payload_sha256, ttl_seconds=300)

        write_client = DomeneshopWriteClient(write_config, allowed_record_types=frozenset({"TXT"}), allow_delete=False)
        adapter = TxtUpdateAdapter(read_client=read_client, write_client=write_client, domain_id=domain_id, record_id=record_id, target=target, before_payload=before_payload, payload=payload)
        request = ControlledWriteRequest(action=UPDATE_ACTION, target=target, payload=payload, operator=operator, approval_token=approval_token, idempotency_key=IDEMPOTENCY_KEY, preflight_reference="D-R3-TXT-UPDATE-DRY-RUN-20260819")
        result = executor.execute(request, adapter)
        if not audit_store.verify_chain():
            raise LiveUpdateError("audit_chain_validation_failed")

        print(json.dumps({"success": True, "status": "replayed_completed_result" if result.get("replayed") else "updated_and_readback_verified", "release_id": RELEASE_ID, "approval_id": APPROVAL_ID, "idempotency_key_sha256": _sha256(IDEMPOTENCY_KEY), "target_sha256": target_sha256, "before_payload_sha256": before_sha256, "update_payload_sha256": payload_sha256, "record_id_sha256": _sha256(str(record_id)), "provider_update_returned": bool(adapter.provider_update_returned), "independent_readback_verified": True, "audit_chain_valid": True, "delete_authorized": False, "restore_authorized": False, "target_included": False, "payload_included": False, "record_id_included": False, "approval_token_included": False}, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "status": "hold_for_review", "error_class": exc.__class__.__name__, "provider_update_returned": bool(adapter and adapter.provider_update_returned), "automatic_restore_or_delete_performed": False, "delete_authorized": False, "restore_authorized": False, "target_included": False, "payload_included": False, "record_id_included": False, "approval_token_included": False}, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if manifest_path is not None and target_for_disable is not None:
            try:
                _atomic_json(manifest_path, _manifest(target_for_disable, enabled=False, decision="HOLD_POST_UPDATE"))
            except Exception:
                pass
        if write_client is not None:
            write_client.close()
        if read_client is not None:
            read_client.close()

if __name__ == "__main__":
    raise SystemExit(main())
