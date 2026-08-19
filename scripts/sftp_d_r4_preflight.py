"""GET/read-only D-R4 SFTP pilot preflight for the isolated sandbox path."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys

from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig

PILOT_ROOT = "/www/atlas-mcp-sandbox.no"
PILOT_FILE = ".mcp-d-r4-validation.txt"
PILOT_PATH = f"{PILOT_ROOT}/{PILOT_FILE}"
CREATE_CONTENT = b"mcp-validation=D-R4-SFTP-CREATE-20260819\n"
EXPECTED_TARGET_SHA256 = "930975e51425f91b5896dd80c5205902a6bd958988726ce40ea8910ee3dc371a"
EXPECTED_PAYLOAD_SHA256 = "ca313ff4049457d2565a4e3f3c4accfd657491bba654dcdb6a48bb2a90867b4c"
RELEASE_ID = "D-R4-SFTP-CREATE-PREFLIGHT-20260819"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    client = None
    try:
        if os.environ.get("WRITE_TOOLS_ENABLED", "false").strip().lower() != "false":
            raise RuntimeError("write_tools_must_remain_disabled")
        if os.environ.get("DRY_RUN_DEFAULT", "true").strip().lower() != "true":
            raise RuntimeError("dry_run_default_must_remain_enabled")

        config = SftpReadConfig.from_env()
        if not config.has_auth:
            raise RuntimeError("sftp_credentials_missing")
        if "/www" not in config.allowed_roots:
            raise RuntimeError("www_root_not_allowed")

        target_sha = sha256_text(PILOT_PATH)
        payload_sha = hashlib.sha256(CREATE_CONTENT).hexdigest()
        if target_sha != EXPECTED_TARGET_SHA256:
            raise RuntimeError("deterministic_target_hash_mismatch")
        if payload_sha != EXPECTED_PAYLOAD_SHA256:
            raise RuntimeError("deterministic_payload_hash_mismatch")

        client = SftpReadClient(config)
        root_meta = client.get_file_metadata(PILOT_ROOT)
        if not stat.S_ISDIR(int(root_meta.get("mode", 0))):
            raise RuntimeError("pilot_root_is_not_directory")

        entries = client.list_files(PILOT_ROOT)
        if not isinstance(entries, list):
            raise RuntimeError("pilot_root_listing_unexpected_shape")
        collisions = [entry for entry in entries if str(entry.get("path", "")) == PILOT_PATH]
        if collisions:
            raise RuntimeError("pilot_file_collision_detected")

        print(json.dumps({
            "success": True,
            "status": "sftp_preflight_ok",
            "release_id": RELEASE_ID,
            "target_sha256": target_sha,
            "payload_sha256": payload_sha,
            "pilot_root_exists": True,
            "pilot_root_is_directory": True,
            "pilot_file_collision_detected": False,
            "existing_entry_count": len(entries),
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "approval_token_issued": False,
            "idempotency_reservation_created": False,
            "audit_event_created": False,
            "target_included": False,
            "payload_included": False,
            "remote_listing_included": False,
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
            "remote_listing_included": False,
        }, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
