"""Bootstrap the Conta MCP production write kill switch in a fail-closed state.

This helper is intentionally narrower than the deployment controller. It connects
only to the Domeneshop SFTP target, validates an existing kill-switch document,
or creates the missing document atomically with globalBlocked=true. It never
calls Conta, never installs provider credentials, and never opens write access.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import stat
import sys
from pathlib import PurePosixPath

import paramiko

REMOTE_RUNTIME_ROOT = "/Custom Models/conta-mcp"
KILL_SWITCH_PATH = f"{REMOTE_RUNTIME_ROOT}/storage/write-kill-switch.json"
EXPECTED_DOCUMENT = {
    "globalBlocked": True,
    "blockedActions": ["invoice_draft_create_v2"],
    "reason": "production_fail_closed_bootstrap",
}
EXPECTED_BYTES = (json.dumps(EXPECTED_DOCUMENT, indent=2, sort_keys=True) + "\n").encode("utf-8")


def remote_exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def ensure_remote_directory(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/"
    for part in PurePosixPath(path).parts:
        if part == "/":
            continue
        current = posixpath.join(current, part)
        try:
            info = sftp.stat(current)
            if not stat.S_ISDIR(info.st_mode):
                raise RuntimeError("remote_path_not_directory")
        except OSError:
            sftp.mkdir(current, mode=0o700)


def read_remote(sftp: paramiko.SFTPClient, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def validate_document(data: bytes) -> dict[str, object]:
    try:
        document = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("kill_switch_invalid") from None
    if not isinstance(document, dict):
        raise RuntimeError("kill_switch_invalid")
    if document.get("globalBlocked") is not True:
        raise RuntimeError("kill_switch_not_globally_blocked")
    blocked_actions = document.get("blockedActions", [])
    if not isinstance(blocked_actions, list):
        raise RuntimeError("kill_switch_blocked_actions_invalid")
    return document


def publish_missing_kill_switch(sftp: paramiko.SFTPClient) -> None:
    ensure_remote_directory(sftp, posixpath.dirname(KILL_SWITCH_PATH))
    temp = f"{KILL_SWITCH_PATH}.conta-bootstrap-tmp"
    if remote_exists(sftp, temp):
        sftp.remove(temp)
    with sftp.open(temp, "wb") as handle:
        handle.write(EXPECTED_BYTES)
    sftp.chmod(temp, 0o600)
    if read_remote(sftp, temp) != EXPECTED_BYTES:
        sftp.remove(temp)
        raise RuntimeError("kill_switch_temporary_verification_failed")
    try:
        sftp.posix_rename(temp, KILL_SWITCH_PATH)
    except OSError:
        # Never overwrite an independently-created file. If another actor created
        # the target concurrently, remove our temp and validate the target.
        if remote_exists(sftp, KILL_SWITCH_PATH):
            if remote_exists(sftp, temp):
                sftp.remove(temp)
            validate_document(read_remote(sftp, KILL_SWITCH_PATH))
            return
        sftp.rename(temp, KILL_SWITCH_PATH)

    info = sftp.stat(KILL_SWITCH_PATH)
    if stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError("kill_switch_mode_mismatch")
    if read_remote(sftp, KILL_SWITCH_PATH) != EXPECTED_BYTES:
        raise RuntimeError("kill_switch_publish_verification_failed")
    validate_document(read_remote(sftp, KILL_SWITCH_PATH))


def bootstrap() -> bool:
    sftp_user = os.environ.get("DS_SFTP_USER", "")
    sftp_password = os.environ.get("DS_SFTP_VALUE", "")
    if not sftp_user or not sftp_password:
        raise RuntimeError("protected_sftp_credentials_missing")

    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=sftp_user, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        if remote_exists(sftp, KILL_SWITCH_PATH):
            validate_document(read_remote(sftp, KILL_SWITCH_PATH))
            print("KILL_SWITCH_BOOTSTRAPPED=false")
            print("KILL_SWITCH_EXISTING_VALIDATED=true")
            print("KILL_SWITCH_GLOBAL_BLOCKED=true")
            print("PROVIDER_CALL_PERFORMED=false")
            print("PRODUCTION_WRITE_AUTHORIZED=false")
            return False

        publish_missing_kill_switch(sftp)
        print("KILL_SWITCH_BOOTSTRAPPED=true")
        print("KILL_SWITCH_EXISTING_VALIDATED=false")
        print("KILL_SWITCH_GLOBAL_BLOCKED=true")
        print("KILL_SWITCH_MODE_0600=true")
        print("PROVIDER_CALL_PERFORMED=false")
        print("PRODUCTION_WRITE_AUTHORIZED=false")
        return True
    finally:
        sftp.close()
        transport.close()


def self_test() -> None:
    document = validate_document(EXPECTED_BYTES)
    if document != EXPECTED_DOCUMENT:
        raise RuntimeError("self_test_document_mismatch")
    try:
        validate_document(b'{"globalBlocked":false}')
    except RuntimeError as exc:
        if str(exc) != "kill_switch_not_globally_blocked":
            raise
    else:
        raise RuntimeError("self_test_open_switch_accepted")
    print("KILL_SWITCH_BOOTSTRAP_SELF_TEST=true")
    print("PROVIDER_CALL_PERFORMED=false")
    print("PRODUCTION_WRITE_AUTHORIZED=false")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        else:
            bootstrap()
        return 0
    except Exception as exc:
        error_class = str(exc).split(":", 1)[0] or exc.__class__.__name__
        print(f"::error title=Fail-closed kill-switch bootstrap stopped::{error_class}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
