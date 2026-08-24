#!/usr/bin/env python3
"""Provision non-secret Conta execution metadata while remaining fail closed."""
from __future__ import annotations

import json
import os
import posixpath
import re
import stat
from pathlib import PurePosixPath

import paramiko


ROOT = "/Custom Models/conta-mcp"
BACKUP_ROOT = "/Custom Models/conta-mcp-backups"
CONFIG = f"{ROOT}/config/conta_config.local.php"
KILL = f"{ROOT}/storage/write-kill-switch.json"
AUTH = f"{ROOT}/storage/production-authorization.json"
MANIFEST = f"{ROOT}/storage/approved-release-manifest.json"
ACTION = "invoice_draft_create_v2"
SOURCE_COMMIT = "19d8b9fd3e7aec7fec7405df2ffec0e72839c9ac"
SCHEMA_SHA256 = "8c8be48fb6cabf22f097f4879be495dbc789a68ceebbad763b526bff85b598a6"
CREATE_ROUTE = "/invoice/organizations/{opContextOrgId}/invoice-drafts"
READBACK_ROUTE = "/invoice/organizations/{opContextOrgId}/invoice-drafts/{invoiceDraftId}"
AUTHORIZATION = "PROVISION_CONTA_EXECUTION_CONFIG_FAIL_CLOSED_A6B94702"


class Stop(RuntimeError):
    pass


def exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def read(sftp: paramiko.SFTPClient, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def ensure_directory(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/"
    for part in PurePosixPath(path).parts:
        if part == "/":
            continue
        current = posixpath.join(current, part)
        try:
            info = sftp.stat(current)
            if not stat.S_ISDIR(info.st_mode):
                raise Stop("backup_path_not_directory")
        except OSError:
            sftp.mkdir(current, mode=0o700)


def publish(sftp: paramiko.SFTPClient, path: str, data: bytes, mode: int = 0o600) -> None:
    temp = path + ".execution-config-tmp"
    if exists(sftp, temp):
        sftp.remove(temp)
    ensure_directory(sftp, posixpath.dirname(path))
    with sftp.open(temp, "wb") as handle:
        handle.write(data)
    sftp.chmod(temp, mode)
    if read(sftp, temp) != data:
        sftp.remove(temp)
        raise Stop("remote_temporary_readback_mismatch")
    try:
        sftp.posix_rename(temp, path)
    except OSError:
        if exists(sftp, path):
            sftp.remove(path)
        sftp.rename(temp, path)


def php_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def parse_string(text: str, key: str) -> str:
    match = re.search(
        rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>\s*'(?P<v>(?:\\\\.|[^'])*)'\s*,?",
        text,
    )
    if not match:
        raise Stop(f"server_config_literal_missing:{key}")
    return match.group("v").replace("\\'", "'").replace("\\\\", "\\")


def parse_bool(text: str, key: str) -> bool:
    match = re.search(
        rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>\s*(true|false)\s*,?",
        text,
    )
    if not match:
        raise Stop(f"server_config_literal_missing:{key}")
    return match.group(1) == "true"


def update_config(raw: bytes) -> bytes:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Stop("server_config_not_utf8") from None
    updates = {
        "provider_schema_sha256": php_quote(SCHEMA_SHA256),
        "create_invoice_draft_route": php_quote(CREATE_ROUTE),
        "readback_invoice_draft_route": php_quote(READBACK_ROUTE),
    }
    for name, literal in updates.items():
        pattern = re.compile(
            rf"(?m)^(?P<i>\s*)['\"]{re.escape(name)}['\"]\s*=>\s*[^,\r\n]*(?P<c>,\s*(?://[^\r\n]*)?)$"
        )
        matches = list(pattern.finditer(text))
        if len(matches) > 1:
            raise Stop(f"duplicate_config_key:{name}")
        if matches:
            match = matches[0]
            replacement = f"{match.group('i')}'{name}' => {literal}{match.group('c')}"
            text = text[: match.start()] + replacement + text[match.end() :]
        else:
            end = text.rfind("];")
            if end < 0:
                raise Stop("server_config_array_end_missing")
            text = text[:end] + f"    '{name}' => {literal},\n" + text[end:]
    return text.encode("utf-8")


def assert_closed_and_ready(text: str, *, metadata_required: bool) -> None:
    required_closed = {
        "enable_write_tools": False,
        "runtime_write_blocked": True,
        "execution_allowed": False,
        "production_write_approved": False,
    }
    for key, expected in required_closed.items():
        if parse_bool(text, key) is not expected:
            raise Stop(f"runtime_not_fail_closed:{key}")
    if parse_string(text, "release_commit").lower() != SOURCE_COMMIT:
        raise Stop("deployed_release_commit_mismatch")
    if not parse_string(text, "write_policy_version"):
        raise Stop("write_policy_version_missing")
    if not parse_string(text, "mcp_bearer_token"):
        raise Stop("mcp_bearer_token_missing")
    if len(parse_string(text, "approval_signing_key")) < 32:
        raise Stop("approval_signing_key_unavailable")
    if not parse_string(text, "approval_key_id"):
        raise Stop("approval_key_id_missing")
    if metadata_required:
        expected = {
            "provider_schema_sha256": SCHEMA_SHA256,
            "create_invoice_draft_route": CREATE_ROUTE,
            "readback_invoice_draft_route": READBACK_ROUTE,
        }
        for key, value in expected.items():
            if parse_string(text, key) != value:
                raise Stop(f"execution_metadata_mismatch:{key}")


def main() -> int:
    if os.environ.get("GITHUB_REF_NAME") != "main":
        raise Stop("must_run_from_main")
    if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
        raise Stop("workflow_rerun_not_authorized")
    if os.environ.get("PROVISION_AUTHORIZATION") != AUTHORIZATION:
        raise Stop("authorization_mismatch")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not run_id.isdigit():
        raise Stop("run_id_invalid")
    user = os.environ.get("DS_SFTP_USER", "").strip()
    password = os.environ.get("DS_SFTP_VALUE", "").strip()
    if not user or not password:
        raise Stop("protected_sftp_credentials_missing")

    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    before: bytes | None = None
    mode = 0o600
    config_written = False
    try:
        if not exists(sftp, CONFIG) or not exists(sftp, KILL):
            raise Stop("required_runtime_control_file_missing")
        if exists(sftp, AUTH) or exists(sftp, MANIFEST):
            raise Stop("temporary_execution_controls_must_be_absent")
        kill = json.loads(read(sftp, KILL))
        if not isinstance(kill, dict) or kill.get("globalBlocked") is not True:
            raise Stop("kill_switch_not_globally_blocked")

        info = sftp.stat(CONFIG)
        mode = stat.S_IMODE(info.st_mode)
        before = read(sftp, CONFIG)
        assert_closed_and_ready(before.decode("utf-8"), metadata_required=False)

        backup = f"{BACKUP_ROOT}/execution-config-{run_id}/conta_config.local.php"
        publish(sftp, backup, before, 0o600)
        print("SERVER_CONFIG_BACKUP_COMPLETE=true")

        after = update_config(before)
        publish(sftp, CONFIG, after, mode)
        config_written = True
        observed = read(sftp, CONFIG)
        if observed != after:
            raise Stop("server_config_readback_mismatch")
        assert_closed_and_ready(observed.decode("utf-8"), metadata_required=True)

        print("PROVIDER_SCHEMA_SHA256_CONFIGURED=true")
        print("CREATE_INVOICE_DRAFT_ROUTE_CONFIGURED=true")
        print("READBACK_INVOICE_DRAFT_ROUTE_CONFIGURED=true")
        print("APPROVAL_SIGNING_KEY_PRESENT=true")
        print("KILL_SWITCH_GLOBAL_BLOCKED=true")
        print("WRITE_TOOLS_ENABLED=false")
        print("RUNTIME_WRITE_BLOCKED=true")
        print("EXECUTION_ALLOWED=false")
        print("PRODUCTION_WRITE_APPROVED=false")
        print("PROVIDER_CALL_PERFORMED=false")
        print("PRODUCTION_MUTATION_PERFORMED=false")
        print("SECRET_VALUE_PRINTED=false")
        return 0
    except Exception:
        if config_written and before is not None:
            publish(sftp, CONFIG, before, mode)
            print("ROLLBACK_COMPLETED=true")
        raise
    finally:
        try:
            sftp.close()
            transport.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(f"::error title=Conta execution metadata provisioning stopped::{exc}")
        raise SystemExit(1)
    except Exception:
        print("::error title=Conta execution metadata provisioning stopped::unexpected_error")
        raise SystemExit(1)
