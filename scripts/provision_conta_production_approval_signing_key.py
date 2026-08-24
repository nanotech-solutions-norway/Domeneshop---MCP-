#!/usr/bin/env python3
from __future__ import annotations
import json, os, posixpath, re, secrets, stat
from pathlib import PurePosixPath
import paramiko

ROOT = "/Custom Models/conta-mcp"
CONFIG = f"{ROOT}/config/conta_config.local.php"
KILL = f"{ROOT}/storage/write-kill-switch.json"
AUTH = f"{ROOT}/storage/production-authorization.json"
MANIFEST = f"{ROOT}/storage/approved-release-manifest.json"
ACTION = "invoice_draft_create_v2"

class Stop(RuntimeError): pass

def exists(sftp, path):
    try: sftp.stat(path); return True
    except OSError: return False

def read(sftp, path):
    with sftp.open(path, "rb") as h: return h.read()

def publish(sftp, path, data, mode=0o600):
    tmp = path + ".approval-key-tmp"
    if exists(sftp, tmp): sftp.remove(tmp)
    with sftp.open(tmp, "wb") as h: h.write(data)
    sftp.chmod(tmp, mode)
    try: sftp.posix_rename(tmp, path)
    except OSError:
        if exists(sftp, path): sftp.remove(path)
        sftp.rename(tmp, path)

def php_quote(v): return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"

def update_config(raw: bytes, key: str, key_id: str) -> bytes:
    try: text = raw.decode("utf-8")
    except UnicodeDecodeError: raise Stop("server_config_not_utf8")
    updates = {"approval_signing_key": php_quote(key), "approval_key_id": php_quote(key_id)}
    for name, literal in updates.items():
        pat = re.compile(rf"(?m)^(?P<i>\s*)['\"]{re.escape(name)}['\"]\s*=>\s*[^,\r\n]*(?P<c>,\s*(?://[^\r\n]*)?)$")
        matches = list(pat.finditer(text))
        if len(matches) > 1: raise Stop(f"duplicate_config_key:{name}")
        if matches:
            m = matches[0]
            text = text[:m.start()] + f"{m.group('i')}'{name}' => {literal}{m.group('c')}" + text[m.end():]
        else:
            end = text.rfind("];")
            if end < 0: raise Stop("server_config_array_end_missing")
            text = text[:end] + f"    '{name}' => {literal},\n" + text[end:]
    return text.encode("utf-8")

def parse_bool_literal(text: str, key: str) -> str:
    m = re.search(rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>\s*(true|false)\s*,?", text)
    if not m: raise Stop(f"server_config_literal_missing:{key}")
    return m.group(1)

def main() -> int:
    if os.environ.get("GITHUB_REF_NAME") != "main": raise Stop("must_run_from_main")
    if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1": raise Stop("workflow_rerun_not_authorized")
    if os.environ.get("PROVISION_AUTHORIZATION") != "PROVISION_CONTA_APPROVAL_SIGNING_KEY_FAIL_CLOSED": raise Stop("authorization_mismatch")
    user = os.environ.get("DS_SFTP_USER", "").strip(); pw = os.environ.get("DS_SFTP_VALUE", "").strip()
    if not user or not pw: raise Stop("protected_sftp_credentials_missing")
    transport = paramiko.Transport(("sftp.domeneshop.no", 22)); transport.connect(username=user, password=pw)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        if not exists(sftp, CONFIG) or not exists(sftp, KILL): raise Stop("required_runtime_control_file_missing")
        if exists(sftp, AUTH) or exists(sftp, MANIFEST): raise Stop("temporary_execution_controls_must_be_absent")
        kill = json.loads(read(sftp, KILL))
        if not isinstance(kill, dict) or kill.get("globalBlocked") is not True: raise Stop("kill_switch_not_globally_blocked")
        info = sftp.stat(CONFIG); mode = stat.S_IMODE(info.st_mode); before = read(sftp, CONFIG); text = before.decode("utf-8")
        required_closed = {"enable_write_tools":"false","runtime_write_blocked":"true","execution_allowed":"false","production_write_approved":"false"}
        for k, v in required_closed.items():
            if parse_bool_literal(text, k) != v: raise Stop(f"runtime_not_fail_closed:{k}")
        key = secrets.token_hex(32); key_id = "conta-production-approval-v1"
        after = update_config(before, key, key_id)
        publish(sftp, CONFIG, after, mode)
        verify = read(sftp, CONFIG).decode("utf-8")
        if key not in verify or key_id not in verify: raise Stop("approval_signing_key_verification_failed")
        print("APPROVAL_SIGNING_KEY_PROVISIONED=true")
        print("APPROVAL_KEY_ID_PROVISIONED=true")
        print("KILL_SWITCH_GLOBAL_BLOCKED=true")
        print("WRITE_TOOLS_ENABLED=false")
        print("RUNTIME_WRITE_BLOCKED=true")
        print("EXECUTION_ALLOWED=false")
        print("PRODUCTION_WRITE_APPROVED=false")
        print("PROVIDER_CALL_PERFORMED=false")
        print("PRODUCTION_MUTATION_PERFORMED=false")
        print("SIGNING_KEY_PRINTED=false")
    finally:
        try: sftp.close(); transport.close()
        except Exception: pass
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Stop as exc:
        print(f"::error title=Conta approval key provisioning stopped::{exc}")
        raise SystemExit(1)
