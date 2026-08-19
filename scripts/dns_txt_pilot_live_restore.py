"""Execute the single authorized D-R3 DNS TXT RESTORE on the isolated target.

The RESTORE is a bounded UPDATE of the existing pilot TXT record back to the
original accepted CREATE payload. It is not a DELETE operation.
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
from domeneshop_mcp.pilot_preflight import PILOT_HOST, _normalize_domain_name, _resolve_exact_domain_id, _target
from domeneshop_mcp.write_client import DomeneshopWriteClient
from domeneshop_mcp.write_release import ControlledWriteRelease
from dns_txt_pilot_restore_dry_run import restore_payload
from dns_txt_pilot_update_dry_run import update_payload

RESTORE_ACTION = "domeneshop_restore_dns_txt"
RELEASE_ID = "D-R3-TXT-RESTORE-20260819-001"
APPROVAL_ID = RELEASE_ID
IDEMPOTENCY_KEY = RELEASE_ID
EXPECTED_TARGET_SHA256 = "5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e"
EXPECTED_BEFORE_PAYLOAD_SHA256 = "58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087"
EXPECTED_RESTORE_PAYLOAD_SHA256 = "6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c"
AUTHORIZATION_PHRASE = "AUTHORIZE_D_R3_TXT_RESTORE"

class LiveRestoreError(RuntimeError):
    pass

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)

def _runtime_config(base: DomeneshopConfig, *, write_enabled: bool) -> DomeneshopConfig:
    return DomeneshopConfig(api_base_url=base.api_base_url, auth_user=base.auth_user, auth_value=base.auth_value, write_tools_enabled=write_enabled, dry_run_default=not write_enabled, require_operator_approval=True, timeout_seconds=base.timeout_seconds)

def _manifest(target: str, *, enabled: bool, decision: str) -> dict[str, Any]:
    return {"release_id": RELEASE_ID, "environment": "isolated-live-pilot", "decision": decision, "approved_tools": [RESTORE_ACTION], "approved_target_prefixes": [target], "live_execution_enabled": enabled, "controls": {"require_approval_token": True, "require_idempotency": True, "require_audit": True, "require_readback": True}}

def _matches(record: dict[str, Any], payload: dict[str, Any]) -> bool:
    for key, expected in payload.items():
        observed = record.get(key)
        if key == "type":
            if str(observed).upper() != str(expected).upper(): return False
        elif observed != expected: return False
    return True

class TxtRestoreAdapter:
    def __init__(self, *, read_client, write_client, domain_id: int, record_id: int, target: str, before_payload: dict[str, Any], payload: dict[str, Any]) -> None:
        self.read_client=read_client; self.write_client=write_client; self.domain_id=domain_id; self.record_id=record_id; self.target=target; self.before_payload=before_payload; self.payload=payload; self.provider_restore_returned=False
    def pre_read(self, target: str):
        if target != self.target: raise ControlledWriteError("Target changed before provider execution")
        record=self.read_client.get_dns_record(self.domain_id,self.record_id)
        if not isinstance(record,dict) or not _matches(record,self.before_payload): raise ControlledWriteError("Exact TXT record no longer matches accepted UPDATE state")
        return {"existing_update_state_verified":True,"before_payload_sha256":canonical_payload_sha256(self.before_payload),"record_id_sha256":_sha256(str(self.record_id))}
    def execute(self, action: str, target: str, payload: dict[str, Any]):
        if action != RESTORE_ACTION or target != self.target: raise ControlledWriteError("Mutation is outside authorized RESTORE scope")
        if canonical_payload_sha256(payload) != EXPECTED_RESTORE_PAYLOAD_SHA256: raise ControlledWriteError("Restore payload hash changed before provider execution")
        self.write_client.update_dns_record(self.domain_id,self.record_id,payload); self.provider_restore_returned=True
        return {"provider_restore_returned":True,"record_id_sha256":_sha256(str(self.record_id))}
    def read_back(self,target: str,result: dict[str,Any]):
        record=self.read_client.get_dns_record(self.domain_id,self.record_id)
        if target != self.target or not isinstance(record,dict) or not _matches(record,self.payload): raise ControlledWriteError("Provider readback did not match authorized RESTORE payload")
        return {"verified":True,"record_id_sha256":_sha256(str(self.record_id)),"payload_sha256":canonical_payload_sha256(self.payload)}
    def rollback(self,action,target,before,result):
        return {"status":"not_performed","reason":"no_additional_mutation_authorized"}

def main() -> int:
    manifest_path=None; target_for_disable=None; read_client=None; write_client=None; adapter=None
    try:
        if os.environ.get("D_R3_RESTORE_AUTHORIZATION_PHRASE","") != AUTHORIZATION_PHRASE: raise LiveRestoreError("exact_operator_authorization_missing")
        if os.environ.get("DS_PILOT_TXT_HOST",PILOT_HOST) != PILOT_HOST: raise LiveRestoreError("invalid_txt_host")
        if os.environ.get("WRITE_TOOLS_ENABLED","").strip().lower() != "true": raise LiveRestoreError("write_switch_not_explicitly_enabled_for_process")
        if os.environ.get("DRY_RUN_DEFAULT","").strip().lower() != "false": raise LiveRestoreError("dry_run_flag_not_explicitly_disabled_for_authorized_process")
        if os.environ.get("REQUIRE_OPERATOR_APPROVAL","").strip().lower() != "true": raise LiveRestoreError("operator_approval_control_disabled")
        root=Path(os.environ.get("PILOT_STATE_ROOT","").strip())
        if not root.is_absolute(): raise LiveRestoreError("pilot_state_root_missing_or_not_absolute")
        root=root.resolve(); repo=Path.cwd().resolve()
        if root==repo or repo in root.parents: raise LiveRestoreError("pilot_state_root_inside_repository")
        signing_secret=os.environ.get("APPROVAL_SIGNING_SECRET",""); operator=os.environ.get("D_R3_OPERATOR","").strip()
        domain_name=_normalize_domain_name(os.environ.get("DS_PILOT_DOMAIN_NAME",""))
        if not operator: raise LiveRestoreError("operator_identity_missing")
        base=DomeneshopConfig.from_env()
        if not base.has_auth: raise LiveRestoreError("provider_credentials_missing")
        read_client=DomeneshopReadClient(_runtime_config(base,write_enabled=False)); domain_id=_resolve_exact_domain_id(read_client,domain_name); target=_target(domain_id,PILOT_HOST); target_for_disable=target
        before=update_payload(); payload=restore_payload(); target_sha=_sha256(target); before_sha=canonical_payload_sha256(before); payload_sha=canonical_payload_sha256(payload)
        if target_sha != EXPECTED_TARGET_SHA256: raise LiveRestoreError("accepted_target_hash_mismatch")
        if before_sha != EXPECTED_BEFORE_PAYLOAD_SHA256: raise LiveRestoreError("accepted_before_payload_hash_mismatch")
        if payload_sha != EXPECTED_RESTORE_PAYLOAD_SHA256: raise LiveRestoreError("accepted_restore_payload_hash_mismatch")
        records=read_client.list_dns_records(domain_id,host=PILOT_HOST,record_type="TXT")
        if not isinstance(records,list) or len(records)!=1: raise LiveRestoreError("expected_exactly_one_txt_record")
        record=records[0]
        if not isinstance(record,dict) or not _matches(record,before): raise LiveRestoreError("existing_txt_record_does_not_match_accepted_update_state")
        record_id=record.get("id")
        if not isinstance(record_id,int): raise LiveRestoreError("existing_txt_record_id_missing")
        manifest_path=root/"controlled-write-release-manifest.json"; live_manifest=_manifest(target,enabled=True,decision="APPROVE_CONTROLLED_WRITE_PILOT"); release=ControlledWriteRelease.from_dict(live_manifest)
        if release.approved_tools != frozenset({RESTORE_ACTION}) or release.approved_target_prefixes != (target,): raise LiveRestoreError("live_manifest_scope_invalid")
        _atomic_json(manifest_path,live_manifest)
        nonce_store=UsedNonceStore(root/"approval-nonces"); idem=FileIdempotencyStore(root/"idempotency"); audit=AppendOnlyAuditStore(root/"audit"/"controlled-write.jsonl"); approvals=ApprovalTokenManager(signing_secret,nonce_store); executor=ControlledWriteExecutor(release,approvals,idem,audit)
        token=approvals.issue(approval_id=APPROVAL_ID,operator=operator,action=RESTORE_ACTION,target=target,payload_sha256=payload_sha,ttl_seconds=300)
        write_client=DomeneshopWriteClient(_runtime_config(base,write_enabled=True),allowed_record_types=frozenset({"TXT"}),allow_delete=False); adapter=TxtRestoreAdapter(read_client=read_client,write_client=write_client,domain_id=domain_id,record_id=record_id,target=target,before_payload=before,payload=payload)
        request=ControlledWriteRequest(action=RESTORE_ACTION,target=target,payload=payload,operator=operator,approval_token=token,idempotency_key=IDEMPOTENCY_KEY,preflight_reference="D-R3-TXT-RESTORE-DRY-RUN-20260819")
        result=executor.execute(request,adapter)
        if not audit.verify_chain(): raise LiveRestoreError("audit_chain_validation_failed")
        print(json.dumps({"success":True,"status":"replayed_completed_result" if result.get("replayed") else "restored_and_readback_verified","release_id":RELEASE_ID,"approval_id":APPROVAL_ID,"idempotency_key_sha256":_sha256(IDEMPOTENCY_KEY),"target_sha256":target_sha,"before_payload_sha256":before_sha,"restore_payload_sha256":payload_sha,"record_id_sha256":_sha256(str(record_id)),"provider_restore_returned":bool(adapter.provider_restore_returned),"independent_readback_verified":True,"audit_chain_valid":True,"restore_returns_to_original_create_state":True,"delete_authorized":False,"target_included":False,"payload_included":False,"record_id_included":False,"approval_token_included":False},sort_keys=True)); return 0
    except Exception as exc:
        print(json.dumps({"success":False,"status":"hold_for_review","error_class":exc.__class__.__name__,"provider_restore_returned":bool(adapter and adapter.provider_restore_returned),"automatic_additional_mutation_performed":False,"delete_authorized":False,"target_included":False,"payload_included":False,"record_id_included":False,"approval_token_included":False},sort_keys=True),file=sys.stderr); return 1
    finally:
        if manifest_path is not None and target_for_disable is not None:
            try: _atomic_json(manifest_path,_manifest(target_for_disable,enabled=False,decision="HOLD_POST_RESTORE"))
            except Exception: pass
        if write_client is not None: write_client.close()
        if read_client is not None: read_client.close()

if __name__ == "__main__": raise SystemExit(main())
