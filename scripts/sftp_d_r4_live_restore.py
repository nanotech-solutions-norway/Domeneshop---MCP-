"""Exact one-file live RESTORE gate for D-R4 SFTP validation.

Authorization scope is intentionally hard-coded. This script restores only the
known validation target from one exact UPDATE hash back to the accepted CREATE
payload. It does not expose a reusable SFTP write client and cannot delete or
rename.
"""
from __future__ import annotations

import hashlib
import json
import os

from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig

RELEASE_ID = "D-R4-SFTP-RESTORE-20260824-001"
TARGET = "/www/.mcp-d-r4-validation.txt"
PAYLOAD = b"mcp-validation=D-R4-SFTP-CREATE-20260824\n"
TARGET_SHA256 = "0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a"
BEFORE_SHA256 = "482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203"
AFTER_SHA256 = "9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a"


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _emit(**kwargs: object) -> None:
    base = {
        "release_id": RELEASE_ID,
        "target_sha256": TARGET_SHA256,
        "required_before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256,
        "sftp_delete_authorized": False,
        "sftp_rename_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": False,
    }
    base.update(kwargs)
    print(json.dumps(base, sort_keys=True))


def _read(config: SftpReadConfig) -> dict[str, object]:
    client = SftpReadClient(config)
    try:
        return client.read_text_file(TARGET)
    finally:
        client.close()


def _write_exact(config: SftpReadConfig) -> None:
    import paramiko

    transport = paramiko.Transport((config.host, config.port))
    sftp = None
    try:
        transport.connect(username=config.user, password=config.access_value)
        sftp = paramiko.SFTPClient.from_transport(transport)
        # This is the one explicitly authorized restore overwrite of the exact target.
        with sftp.open(TARGET, "wb") as handle:
            handle.write(PAYLOAD)
            handle.flush()
    finally:
        if sftp is not None:
            sftp.close()
        transport.close()


def main() -> int:
    mutated = False
    try:
        if os.environ.get("WRITE_TOOLS_ENABLED", "false").strip().lower() != "false":
            raise RuntimeError("global_write_tools_must_remain_disabled")
        if os.environ.get("SFTP_D_R4_RESTORE_AUTHORIZED", "false").strip().lower() != "true":
            raise RuntimeError("exact_sftp_restore_authorization_missing")
        if os.environ.get("SFTP_D_R4_RELEASE_ID", "") != RELEASE_ID:
            raise RuntimeError("release_id_mismatch")
        if os.environ.get("SFTP_D_R4_TARGET_SHA256", "") != TARGET_SHA256:
            raise RuntimeError("target_hash_authorization_mismatch")
        if os.environ.get("SFTP_D_R4_BEFORE_SHA256", "") != BEFORE_SHA256:
            raise RuntimeError("before_hash_authorization_mismatch")
        if os.environ.get("SFTP_D_R4_AFTER_SHA256", "") != AFTER_SHA256:
            raise RuntimeError("after_hash_authorization_mismatch")
        if os.environ.get("SFTP_D_R4_DELETE_AUTHORIZED", "false").strip().lower() != "false":
            raise RuntimeError("delete_must_remain_unauthorized")
        if os.environ.get("SFTP_D_R4_RENAME_AUTHORIZED", "false").strip().lower() != "false":
            raise RuntimeError("rename_must_remain_unauthorized")
        if os.environ.get("SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED", "false").strip().lower() != "false":
            raise RuntimeError("broader_overwrite_must_remain_unauthorized")
        if _sha_text(TARGET) != TARGET_SHA256 or hashlib.sha256(PAYLOAD).hexdigest() != AFTER_SHA256:
            raise RuntimeError("embedded_binding_hash_mismatch")

        config = SftpReadConfig.from_env()
        if not config.has_auth:
            raise RuntimeError("sftp_credentials_missing")
        if config.host != "sftp.domeneshop.no" or config.port != 22:
            raise RuntimeError("unexpected_sftp_endpoint")
        if "/www" not in config.allowed_roots:
            raise RuntimeError("www_root_not_allowed")

        before = _read(config)
        if before.get("sha256") != BEFORE_SHA256:
            _emit(success=False, status="before_state_mismatch_hold", provider_mutation_performed=False,
                  sftp_restore_authorized=True, independent_readback_verified=False,
                  observed_before_sha256=before.get("sha256"))
            return 2

        _write_exact(config)
        mutated = True

        readback = _read(config)
        verified = readback.get("sha256") == AFTER_SHA256 and readback.get("content") == PAYLOAD.decode("utf-8")
        if not verified:
            _emit(success=False, status="restored_but_readback_failed_hold", provider_mutation_performed=True,
                  sftp_restore_authorized=True, independent_readback_verified=False,
                  automatic_delete_performed=False)
            return 3

        _emit(success=True, status="restored_and_readback_verified", provider_mutation_performed=True,
              sftp_restore_authorized=True, independent_readback_verified=True,
              restore_returns_to_accepted_create_state=True,
              automatic_delete_performed=False)
        return 0
    except Exception as exc:
        _emit(success=False,
              status="restored_but_exception_hold" if mutated else "pre_restore_hold",
              bounded_error_class=exc.__class__.__name__,
              provider_mutation_performed=mutated,
              sftp_restore_authorized=True,
              independent_readback_verified=False,
              automatic_delete_performed=False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
