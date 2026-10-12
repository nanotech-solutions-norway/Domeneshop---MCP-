"""Exact one-file live CREATE gate for D-R4 SFTP validation.

Authorization scope is intentionally hard-coded. This script cannot overwrite or
delete a remote file and does not expose a reusable SFTP write client.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig

RELEASE_ID = "D-R4-SFTP-CREATE-20260824-001"
TARGET = "/www/.mcp-d-r4-validation.txt"
PAYLOAD = b"mcp-validation=D-R4-SFTP-CREATE-20260824\n"
TARGET_SHA256 = "0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a"
PAYLOAD_SHA256 = "9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a"


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _emit(**kwargs: object) -> None:
    base = {
        "release_id": RELEASE_ID,
        "target_sha256": TARGET_SHA256,
        "payload_sha256": PAYLOAD_SHA256,
        "sftp_overwrite_authorized": False,
        "sftp_delete_authorized": False,
        "write_tools_enabled": False,
    }
    base.update(kwargs)
    print(json.dumps(base, sort_keys=True))


def _target_absent(config: SftpReadConfig) -> bool:
    client = SftpReadClient(config)
    try:
        try:
            client.get_file_metadata(TARGET)
            return False
        except (FileNotFoundError, OSError, IOError) as exc:
            err = getattr(exc, "errno", None)
            text = str(exc).lower()
            if err == 2 or "no such file" in text or "not found" in text:
                return True
            raise
    finally:
        client.close()


def _exclusive_create(config: SftpReadConfig) -> None:
    import paramiko

    transport = paramiko.Transport((config.host, config.port))
    sftp = None
    try:
        transport.connect(username=config.user, password=config.access_value)
        sftp = paramiko.SFTPClient.from_transport(transport)
        # Paramiko requires an explicit write flag in addition to 'x'.
        # 'wx' therefore requests WRITE + CREATE + TRUNC + EXCL; EXCL makes the
        # operation fail if the target already exists, so no existing file can
        # be truncated or overwritten by this CREATE-only gate.
        with sftp.open(TARGET, "wx") as handle:
            handle.write(PAYLOAD)
            handle.flush()
    finally:
        if sftp is not None:
            sftp.close()
        transport.close()


def _readback(config: SftpReadConfig) -> dict[str, object]:
    client = SftpReadClient(config)
    try:
        return client.read_text_file(TARGET)
    finally:
        client.close()


def main() -> int:
    created = False
    try:
        if os.environ.get("WRITE_TOOLS_ENABLED", "false").strip().lower() != "false":
            raise RuntimeError("global_write_tools_must_remain_disabled")
        if os.environ.get("SFTP_D_R4_CREATE_AUTHORIZED", "false").strip().lower() != "true":
            raise RuntimeError("exact_sftp_create_authorization_missing")
        if os.environ.get("SFTP_D_R4_RELEASE_ID", "") != RELEASE_ID:
            raise RuntimeError("release_id_mismatch")
        if os.environ.get("SFTP_D_R4_TARGET_SHA256", "") != TARGET_SHA256:
            raise RuntimeError("target_hash_authorization_mismatch")
        if os.environ.get("SFTP_D_R4_PAYLOAD_SHA256", "") != PAYLOAD_SHA256:
            raise RuntimeError("payload_hash_authorization_mismatch")
        if os.environ.get("SFTP_D_R4_OVERWRITE_AUTHORIZED", "false").strip().lower() != "false":
            raise RuntimeError("overwrite_must_remain_unauthorized")
        if os.environ.get("SFTP_D_R4_DELETE_AUTHORIZED", "false").strip().lower() != "false":
            raise RuntimeError("delete_must_remain_unauthorized")
        if _sha_text(TARGET) != TARGET_SHA256 or hashlib.sha256(PAYLOAD).hexdigest() != PAYLOAD_SHA256:
            raise RuntimeError("embedded_binding_hash_mismatch")

        config = SftpReadConfig.from_env()
        if not config.has_auth:
            raise RuntimeError("sftp_credentials_missing")
        if config.host != "sftp.domeneshop.no" or config.port != 22:
            raise RuntimeError("unexpected_sftp_endpoint")
        if "/www" not in config.allowed_roots:
            raise RuntimeError("www_root_not_allowed")

        if not _target_absent(config):
            _emit(success=False, status="target_exists_hold", provider_mutation_performed=False,
                  sftp_create_authorized=True, independent_readback_verified=False)
            return 2

        _exclusive_create(config)
        created = True

        readback = _readback(config)
        verified = readback.get("sha256") == PAYLOAD_SHA256 and readback.get("content") == PAYLOAD.decode("utf-8")
        if not verified:
            _emit(success=False, status="created_but_readback_failed_hold", provider_mutation_performed=True,
                  sftp_create_authorized=True, independent_readback_verified=False,
                  created_target_retained=True, automatic_delete_performed=False)
            return 3

        _emit(success=True, status="created_and_readback_verified", provider_mutation_performed=True,
              sftp_create_authorized=True, independent_readback_verified=True,
              automatic_delete_performed=False)
        return 0
    except Exception as exc:
        _emit(success=False,
              status="created_but_exception_hold" if created else "pre_create_hold",
              bounded_error_class=exc.__class__.__name__,
              provider_mutation_performed=created,
              sftp_create_authorized=True,
              independent_readback_verified=False,
              automatic_delete_performed=False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
