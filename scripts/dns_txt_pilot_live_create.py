"""Execute the single authorized D-R3 DNS TXT CREATE on the isolated target.

This script is intentionally not an MCP tool and is not used by the read-only
server. It is a one-shot operator execution path for the Office PC after the
D-R3 dry-run evidence and exact CREATE authorization have been accepted.

Safety properties:
- fresh authenticated target resolution and collision pre-read;
- exact accepted target and payload hashes must match;
- exact CREATE-only live release manifest written outside Git;
- one-time payload-bound approval token;
- fixed idempotency identity for replay protection;
- append-only audit and independent provider readback;
- no UPDATE or DELETE capability;
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
from domeneshop_mcp.controlled_write import (
    ControlledWriteError,
    ControlledWriteExecutor,
    ControlledWriteRequest,
    canonical_payload_sha256,
)
from domeneshop_mcp.idempotency import FileIdempotencyStore
from domeneshop_mcp.pilot_preflight import (
    PILOT_ACTION,
    PILOT_HOST,
    _normalize_domain_name,
    _payload,
    _resolve_exact_domain_id,
    _target,
)
from domeneshop_mcp.write_client import DomeneshopWriteClient
from domeneshop_mcp.write_release import ControlledWriteRelease

RELEASE_ID = "D-R3-TXT-CREATE-20260819-001"
APPROVAL_ID = "D-R3-TXT-CREATE-20260819-001"
IDEMPOTENCY_KEY = "D-R3-TXT-CREATE-20260819-001"
EXPECTED_TARGET_SHA256 = "5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e"
EXPECTED_PAYLOAD_SHA256 = "6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c"
AUTHORIZATION_PHRASE = "AUTHORIZE_D_R3_TXT_CREATE"


class LiveCreateError(RuntimeError):
    """Fail-closed live CREATE preparation or execution error."""


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
    return DomeneshopConfig(
        api_base_url=base.api_base_url,
        auth_user=base.auth_user,
        auth_value=base.auth_value,
        write_tools_enabled=write_enabled,
        dry_run_default=not write_enabled,
        require_operator_approval=True,
        timeout_seconds=base.timeout_seconds,
    )


def _manifest(target: str, *, enabled: bool, decision: str) -> dict[str, Any]:
    return {
        "release_id": RELEASE_ID,
        "environment": "isolated-live-pilot",
        "decision": decision,
        "approved_tools": [PILOT_ACTION],
        "approved_target_prefixes": [target],
        "live_execution_enabled": enabled,
        "controls": {
            "require_approval_token": True,
            "require_idempotency": True,
            "require_audit": True,
            "require_readback": True,
        },
    }


class TxtCreateAdapter:
    """CREATE-only adapter with independent readback and no delete authority."""

    def __init__(
        self,
        *,
        read_client: DomeneshopReadClient,
        write_client: DomeneshopWriteClient,
        domain_id: int,
        target: str,
        payload: dict[str, Any],
    ) -> None:
        self.read_client = read_client
        self.write_client = write_client
        self.domain_id = domain_id
        self.target = target
        self.payload = payload
        self.provider_create_returned = False

    def pre_read(self, target: str) -> dict[str, Any] | None:
        if target != self.target:
            raise ControlledWriteError("Target changed before provider execution")
        records = self.read_client.list_dns_records(
            self.domain_id,
            host=PILOT_HOST,
            record_type="TXT",
        )
        if not isinstance(records, list):
            raise ControlledWriteError("Provider pre-read returned an unexpected shape")
        if records:
            raise ControlledWriteError("Exact TXT target is no longer collision-free")
        return {"existing_txt_record_count": 0, "collision_detected": False}

    def execute(self, action: str, target: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != PILOT_ACTION or target != self.target:
            raise ControlledWriteError("Mutation is outside the authorized CREATE scope")
        if canonical_payload_sha256(payload) != EXPECTED_PAYLOAD_SHA256:
            raise ControlledWriteError("Payload hash changed before provider execution")
        record_id = self.write_client.create_dns_record(self.domain_id, payload)
        self.provider_create_returned = True
        return {"record_id": record_id, "provider_create_returned": True}

    def read_back(self, target: str, result: dict[str, Any]) -> dict[str, Any] | None:
        if target != self.target:
            raise ControlledWriteError("Target changed before provider readback")
        record_id = int(result["record_id"])
        record = self.read_client.get_dns_record(self.domain_id, record_id)
        if not isinstance(record, dict):
            raise ControlledWriteError("Provider readback returned an unexpected shape")
        for key, expected in self.payload.items():
            observed = record.get(key)
            if key == "type":
                if str(observed).upper() != str(expected).upper():
                    raise ControlledWriteError("Provider readback did not match the authorized payload")
            elif observed != expected:
                raise ControlledWriteError("Provider readback did not match the authorized payload")
        return {
            "verified": True,
            "record_id": record_id,
            "payload_sha256": canonical_payload_sha256(self.payload),
        }

    def rollback(
        self,
        action: str,
        target: str,
        before: dict[str, Any] | None,
        result: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        # DELETE/rollback is explicitly outside this authorization class.
        return {
            "status": "not_performed",
            "reason": "separate_delete_or_rollback_authorization_required",
        }


def main() -> int:
    manifest_path: Path | None = None
    target_for_disable: str | None = None
    read_client: DomeneshopReadClient | None = None
    write_client: DomeneshopWriteClient | None = None
    adapter: TxtCreateAdapter | None = None

    try:
        if os.environ.get("D_R3_AUTHORIZATION_PHRASE", "") != AUTHORIZATION_PHRASE:
            raise LiveCreateError("exact_operator_authorization_missing")
        if os.environ.get("DS_PILOT_TXT_HOST", PILOT_HOST) != PILOT_HOST:
            raise LiveCreateError("invalid_txt_host")
        if os.environ.get("WRITE_TOOLS_ENABLED", "").strip().lower() != "true":
            raise LiveCreateError("write_switch_not_explicitly_enabled_for_process")
        if os.environ.get("DRY_RUN_DEFAULT", "").strip().lower() != "false":
            raise LiveCreateError("dry_run_flag_not_explicitly_disabled_for_authorized_process")
        if os.environ.get("REQUIRE_OPERATOR_APPROVAL", "").strip().lower() != "true":
            raise LiveCreateError("operator_approval_control_disabled")

        state_root_value = os.environ.get("PILOT_STATE_ROOT", "").strip()
        if not state_root_value:
            raise LiveCreateError("pilot_state_root_missing")
        root = Path(state_root_value)
        if not root.is_absolute():
            raise LiveCreateError("pilot_state_root_must_be_absolute")
        root = root.resolve()
        repository_root = Path.cwd().resolve()
        if root == repository_root or repository_root in root.parents:
            raise LiveCreateError("pilot_state_root_inside_repository")

        signing_secret = os.environ.get("APPROVAL_SIGNING_SECRET", "")
        operator = os.environ.get("D_R3_OPERATOR", "").strip()
        domain_name = _normalize_domain_name(os.environ.get("DS_PILOT_DOMAIN_NAME", ""))
        if not operator:
            raise LiveCreateError("operator_identity_missing")

        base = DomeneshopConfig.from_env()
        if not base.has_auth:
            raise LiveCreateError("provider_credentials_missing")
        read_config = _runtime_config(base, write_enabled=False)
        write_config = _runtime_config(base, write_enabled=True)

        read_client = DomeneshopReadClient(read_config)
        domain_id = _resolve_exact_domain_id(read_client, domain_name)
        target = _target(domain_id, PILOT_HOST)
        payload = _payload(PILOT_HOST)
        target_for_disable = target

        records = read_client.list_dns_records(domain_id, host=PILOT_HOST, record_type="TXT")
        if not isinstance(records, list):
            raise LiveCreateError("provider_pre_read_unexpected_shape")
        if records:
            raise LiveCreateError("txt_target_collision_detected")

        target_sha256 = _sha256(target)
        payload_sha256 = canonical_payload_sha256(payload)
        if target_sha256 != EXPECTED_TARGET_SHA256:
            raise LiveCreateError("accepted_target_hash_mismatch")
        if payload_sha256 != EXPECTED_PAYLOAD_SHA256:
            raise LiveCreateError("accepted_payload_hash_mismatch")

        manifest_path = root / "controlled-write-release-manifest.json"
        live_manifest = _manifest(
            target,
            enabled=True,
            decision="APPROVE_CONTROLLED_WRITE_PILOT",
        )
        release = ControlledWriteRelease.from_dict(live_manifest)
        if release.approved_tools != frozenset({PILOT_ACTION}):
            raise LiveCreateError("live_manifest_tool_scope_invalid")
        if release.approved_target_prefixes != (target,):
            raise LiveCreateError("live_manifest_target_scope_invalid")
        _atomic_json(manifest_path, live_manifest)

        nonce_store = UsedNonceStore(root / "approval-nonces")
        idempotency_store = FileIdempotencyStore(root / "idempotency")
        audit_store = AppendOnlyAuditStore(root / "audit" / "controlled-write.jsonl")
        approval_manager = ApprovalTokenManager(signing_secret, nonce_store)
        executor = ControlledWriteExecutor(
            release,
            approval_manager,
            idempotency_store,
            audit_store,
        )

        approval_token = approval_manager.issue(
            approval_id=APPROVAL_ID,
            operator=operator,
            action=PILOT_ACTION,
            target=target,
            payload_sha256=payload_sha256,
            ttl_seconds=300,
        )

        write_client = DomeneshopWriteClient(
            write_config,
            allowed_record_types=frozenset({"TXT"}),
            allow_delete=False,
        )
        adapter = TxtCreateAdapter(
            read_client=read_client,
            write_client=write_client,
            domain_id=domain_id,
            target=target,
            payload=payload,
        )
        request = ControlledWriteRequest(
            action=PILOT_ACTION,
            target=target,
            payload=payload,
            operator=operator,
            approval_token=approval_token,
            idempotency_key=IDEMPOTENCY_KEY,
            preflight_reference="runs:31966109707,32016205573",
        )
        result = executor.execute(request, adapter)
        if not audit_store.verify_chain():
            raise LiveCreateError("audit_chain_validation_failed")

        print(
            json.dumps(
                {
                    "success": True,
                    "status": "replayed_completed_result" if result.get("replayed") else "created_and_readback_verified",
                    "release_id": RELEASE_ID,
                    "approval_id": APPROVAL_ID,
                    "idempotency_key_sha256": _sha256(IDEMPOTENCY_KEY),
                    "target_sha256": target_sha256,
                    "payload_sha256": payload_sha256,
                    "provider_create_returned": bool(adapter.provider_create_returned),
                    "independent_readback_verified": True,
                    "audit_chain_valid": True,
                    "delete_authorized": False,
                    "update_authorized": False,
                    "target_included": False,
                    "payload_included": False,
                    "approval_token_included": False,
                },
                sort_keys=True,
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "status": "hold_for_review",
                    "error_class": exc.__class__.__name__,
                    "provider_create_returned": bool(adapter and adapter.provider_create_returned),
                    "automatic_delete_or_rollback_performed": False,
                    "delete_authorized": False,
                    "update_authorized": False,
                    "target_included": False,
                    "payload_included": False,
                    "approval_token_included": False,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        if manifest_path is not None and target_for_disable is not None:
            try:
                _atomic_json(
                    manifest_path,
                    _manifest(
                        target_for_disable,
                        enabled=False,
                        decision="HOLD_POST_CREATE",
                    ),
                )
            except Exception:
                # Do not mask the primary execution result. The PowerShell wrapper
                # also forces the process-level write switch back to false.
                pass
        if write_client is not None:
            write_client.close()
        if read_client is not None:
            read_client.close()


if __name__ == "__main__":
    raise SystemExit(main())
