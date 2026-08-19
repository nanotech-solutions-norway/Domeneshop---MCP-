"""Read-only D-R3 TXT UPDATE dry run for the isolated pilot record.

This script performs authenticated GET operations only. It proves that the
CREATE result is present exactly once and derives the deterministic UPDATE
payload/hash without creating approval, idempotency, audit, or provider-write
state.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.controlled_write import canonical_payload_sha256
from domeneshop_mcp.pilot_preflight import (
    PILOT_HOST,
    _normalize_domain_name,
    _payload as create_payload,
    _resolve_exact_domain_id,
    _target,
)

UPDATE_ACTION = "domeneshop_update_dns_txt"
UPDATE_RELEASE_ID = "D-R3-TXT-UPDATE-20260819-001"
EXPECTED_TARGET_SHA256 = "5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e"
EXPECTED_CREATE_PAYLOAD_SHA256 = "6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c"
EXPECTED_UPDATE_PAYLOAD_SHA256 = "58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def update_payload() -> dict[str, Any]:
    return {
        "host": PILOT_HOST,
        "data": "mcp-validation=D-R3-TXT-UPDATE-20260819",
        "ttl": 300,
        "type": "TXT",
    }


def _matches_payload(record: dict[str, Any], payload: dict[str, Any]) -> bool:
    for key, expected in payload.items():
        observed = record.get(key)
        if key == "type":
            if str(observed).upper() != str(expected).upper():
                return False
        elif observed != expected:
            return False
    return True


def main() -> int:
    client: DomeneshopReadClient | None = None
    try:
        if os.environ.get("WRITE_TOOLS_ENABLED", "false").strip().lower() != "false":
            raise RuntimeError("write_tools_must_remain_disabled")
        if os.environ.get("DRY_RUN_DEFAULT", "true").strip().lower() != "true":
            raise RuntimeError("dry_run_default_must_remain_enabled")

        config = DomeneshopConfig.from_env()
        if not config.has_auth:
            raise RuntimeError("provider_credentials_missing")
        domain_name = _normalize_domain_name(os.environ.get("DS_PILOT_DOMAIN_NAME", ""))

        client = DomeneshopReadClient(config)
        domain_id = _resolve_exact_domain_id(client, domain_name)
        target = _target(domain_id, PILOT_HOST)
        before = create_payload(PILOT_HOST)
        after = update_payload()

        target_sha256 = _sha256(target)
        before_sha256 = canonical_payload_sha256(before)
        after_sha256 = canonical_payload_sha256(after)
        if target_sha256 != EXPECTED_TARGET_SHA256:
            raise RuntimeError("accepted_target_hash_mismatch")
        if before_sha256 != EXPECTED_CREATE_PAYLOAD_SHA256:
            raise RuntimeError("accepted_create_payload_hash_mismatch")
        if after_sha256 != EXPECTED_UPDATE_PAYLOAD_SHA256:
            raise RuntimeError("deterministic_update_payload_hash_mismatch")

        records = client.list_dns_records(domain_id, host=PILOT_HOST, record_type="TXT")
        if not isinstance(records, list):
            raise RuntimeError("provider_pre_read_unexpected_shape")
        if len(records) != 1:
            raise RuntimeError("expected_exactly_one_txt_record")
        record = records[0]
        if not isinstance(record, dict) or not _matches_payload(record, before):
            raise RuntimeError("existing_txt_record_does_not_match_accepted_create_state")
        record_id = record.get("id")
        if not isinstance(record_id, int):
            raise RuntimeError("existing_txt_record_id_missing")

        print(json.dumps({
            "success": True,
            "status": "update_dry_run_ok",
            "release_id": UPDATE_RELEASE_ID,
            "action": UPDATE_ACTION,
            "target_sha256": target_sha256,
            "before_payload_sha256": before_sha256,
            "update_payload_sha256": after_sha256,
            "record_id_sha256": _sha256(str(record_id)),
            "existing_txt_record_count": 1,
            "existing_create_state_verified": True,
            "approval_token_issued": False,
            "idempotency_reservation_created": False,
            "audit_event_created": False,
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "target_included": False,
            "payload_included": False,
            "record_id_included": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "status": "hold_for_review",
            "bounded_error_class": str(exc),
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "target_included": False,
            "payload_included": False,
            "record_id_included": False,
        }, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
