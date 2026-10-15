#!/usr/bin/env python3
"""Secret-safe, read-only dependency audit for the Atlas-AI managed database.

The audit reads SFTP-hosted configuration/code and public GET endpoints only.
It never connects directly to MySQL, never writes remote files, and never logs
credential values.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import ssl
import urllib.error
import urllib.request
from pathlib import PurePosixPath
from typing import Any

import certifi
import paramiko

SFTP_HOST = "sftp.domeneshop.no"
SFTP_PORT = 22
PUBLIC_BASE = "https://www.atlas-ai.no"
MAX_READ = 1024 * 1024
MAX_SCAN_FILES = 500
MAX_SCAN_DEPTH = 6

PRIVATE_ROOT_CANDIDATES = (
    "/football_edge_api_private",
    "/home/6/a/atlas-ai/football_edge_api_private",
)
PUBLIC_API_CANDIDATES = (
    "/www/api",
    "/www/www.atlas-ai.no/api",
)

CORE_KEYS = ("DB_HOST", "DB_PORT", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD")
PIP_KEYS = ("PIP_DB_HOST", "PIP_DB_PORT", "PIP_DB_NAME", "PIP_DB_USER", "PIP_DB_PASSWORD")

class AuditStop(RuntimeError):
    pass

def exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False

def is_dir(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        import stat
        return stat.S_ISDIR(sftp.stat(path).st_mode)
    except OSError:
        return False

def read_bytes(sftp: paramiko.SFTPClient, path: str) -> bytes:
    st = sftp.stat(path)
    if st.st_size > MAX_READ:
        raise AuditStop("remote_file_too_large")
    with sftp.open(path, "rb") as handle:
        return handle.read()

def read_text(sftp: paramiko.SFTPClient, path: str) -> str:
    return read_bytes(sftp, path).decode("utf-8", errors="replace")

def parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            out[key] = value.strip()
    return out

def find_private_root(sftp: paramiko.SFTPClient) -> str:
    for candidate in PRIVATE_ROOT_CANDIDATES:
        if is_dir(sftp, candidate) and exists(sftp, posixpath.join(candidate, ".env")):
            return candidate
    try:
        top = sftp.listdir("/")
    except OSError:
        top = []
    for name in top:
        if name == "football_edge_api_private":
            candidate = "/" + name
            if is_dir(sftp, candidate) and exists(sftp, posixpath.join(candidate, ".env")):
                return candidate
    raise AuditStop("private_backend_not_found")

def find_public_api_root(sftp: paramiko.SFTPClient) -> str | None:
    for candidate in PUBLIC_API_CANDIDATES:
        if is_dir(sftp, candidate):
            return candidate
    return None

def iter_files(sftp: paramiko.SFTPClient, root: str):
    stack: list[tuple[str, int]] = [(root, 0)]
    emitted = 0
    while stack:
        current, depth = stack.pop()
        if depth > MAX_SCAN_DEPTH:
            continue
        try:
            entries = sftp.listdir_attr(current)
        except OSError:
            continue
        for item in entries:
            path = posixpath.join(current, item.filename)
            import stat
            if stat.S_ISDIR(item.st_mode):
                stack.append((path, depth + 1))
                continue
            emitted += 1
            if emitted > MAX_SCAN_FILES:
                raise AuditStop("remote_scan_file_limit_exceeded")
            yield path

def scan_private_consumers(sftp: paramiko.SFTPClient, root: str) -> dict[str, Any]:
    result = {
        "php_files_scanned": 0,
        "core_db_consumer_files": 0,
        "pip_db_consumer_files": 0,
        "pdo_files": 0,
        "mysqli_files": 0,
        "env_loader_files": 0,
    }
    for path in iter_files(sftp, root):
        suffix = PurePosixPath(path).suffix.lower()
        if suffix not in {".php", ".inc"}:
            continue
        result["php_files_scanned"] += 1
        try:
            text = read_text(sftp, path)
        except AuditStop:
            continue
        upper = text.upper()
        if any(key in upper for key in CORE_KEYS):
            result["core_db_consumer_files"] += 1
        if any(key in upper for key in PIP_KEYS):
            result["pip_db_consumer_files"] += 1
        if "PDO" in text or "PDO(" in text:
            result["pdo_files"] += 1
        if "MYSQLI" in upper:
            result["mysqli_files"] += 1
        if ".ENV" in upper and ("FILE" in upper or "PARSE" in upper or "GETENV" in upper):
            result["env_loader_files"] += 1
    return result

def public_diagnostic_present(sftp: paramiko.SFTPClient) -> bool:
    candidates = (
        "/www/football_edge_db_healthcheck.php",
        "/www/www.atlas-ai.no/football_edge_db_healthcheck.php",
    )
    if any(exists(sftp, p) for p in candidates):
        return True
    for root in ("/www",):
        if not is_dir(sftp, root):
            continue
        count = 0
        for path in iter_files(sftp, root):
            count += 1
            if count > MAX_SCAN_FILES:
                break
            name = posixpath.basename(path).lower()
            if name == "football_edge_db_healthcheck.php" or name.endswith("_db_healthcheck.php"):
                return True
    return False

def http_get_json(url: str) -> tuple[int, Any]:
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
            raw = response.read(262145)
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read(262145)
        status = exc.code
    if len(raw) > 262144:
        raise AuditStop("public_response_too_large")
    try:
        return status, json.loads(raw)
    except Exception:
        return status, None

def main() -> int:
    user = os.environ.get("DS_SFTP_USER", "").strip()
    password = os.environ.get("DS_SFTP_VALUE", "").strip()
    if not user or not password:
        raise AuditStop("protected_sftp_credentials_missing")

    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        private_root = find_private_root(sftp)
        env_path = posixpath.join(private_root, ".env")
        env = parse_env(read_text(sftp, env_path))
        public_api_root = find_public_api_root(sftp)
        consumers = scan_private_consumers(sftp, private_root)
        diagnostic = public_diagnostic_present(sftp)
    finally:
        sftp.close()
        transport.close()

    core_present = {key: bool(env.get(key, "").strip()) for key in CORE_KEYS}
    pip_present = {key: bool(env.get(key, "").strip()) for key in PIP_KEYS}
    same_host = (
        bool(env.get("DB_HOST", "").strip())
        and bool(env.get("PIP_DB_HOST", "").strip())
        and env.get("DB_HOST", "").strip() == env.get("PIP_DB_HOST", "").strip()
    )
    same_db = (
        bool(env.get("DB_DATABASE", "").strip())
        and bool(env.get("PIP_DB_NAME", "").strip())
        and env.get("DB_DATABASE", "").strip() == env.get("PIP_DB_NAME", "").strip()
    )

    h_status, health = http_get_json(PUBLIC_BASE + "/api/health")
    c_status, competitions = http_get_json(PUBLIC_BASE + "/api/competitions")
    s_status, safety = http_get_json(PUBLIC_BASE + "/api/system/safety-state")

    health_ok = isinstance(health, dict) and health.get("status") == "ok"
    database_ok = isinstance(health, dict) and health.get("database") == "ok"
    competitions_ok = (
        c_status == 200
        and isinstance(competitions, dict)
        and isinstance(competitions.get("count"), int)
        and competitions.get("count", 0) > 0
    )
    safe_state_ok = (
        s_status == 200
        and isinstance(safety, dict)
        and safety.get("required_safe_state_ok") is True
    )

    markers = {
        "SFTP_AUTHENTICATION_VERIFIED": True,
        "PRIVATE_BACKEND_PRESENT": True,
        "PRIVATE_ENV_PRESENT": True,
        "PUBLIC_API_ROOT_PRESENT": public_api_root is not None,
        "CORE_DB_HOST_CONFIGURED": core_present["DB_HOST"],
        "CORE_DB_PORT_CONFIGURED": core_present["DB_PORT"],
        "CORE_DB_DATABASE_CONFIGURED": core_present["DB_DATABASE"],
        "CORE_DB_USERNAME_CONFIGURED": core_present["DB_USERNAME"],
        "CORE_DB_PASSWORD_CONFIGURED": core_present["DB_PASSWORD"],
        "PIP_DB_HOST_CONFIGURED_IN_PRIVATE_ENV": pip_present["PIP_DB_HOST"],
        "PIP_DB_PORT_CONFIGURED_IN_PRIVATE_ENV": pip_present["PIP_DB_PORT"],
        "PIP_DB_NAME_CONFIGURED_IN_PRIVATE_ENV": pip_present["PIP_DB_NAME"],
        "PIP_DB_USER_CONFIGURED_IN_PRIVATE_ENV": pip_present["PIP_DB_USER"],
        "PIP_DB_PASSWORD_CONFIGURED_IN_PRIVATE_ENV": pip_present["PIP_DB_PASSWORD"],
        "PIP_DB_SAME_HOST_AS_CORE_WHEN_CONFIGURED": same_host,
        "PIP_DB_SAME_DATABASE_AS_CORE_WHEN_CONFIGURED": same_db,
        "PRIVATE_PHP_FILES_SCANNED": consumers["php_files_scanned"],
        "CORE_DB_CONSUMER_FILE_COUNT": consumers["core_db_consumer_files"],
        "PIP_DB_CONSUMER_FILE_COUNT": consumers["pip_db_consumer_files"],
        "PDO_CONSUMER_FILE_COUNT": consumers["pdo_files"],
        "MYSQLI_CONSUMER_FILE_COUNT": consumers["mysqli_files"],
        "ENV_LOADER_FILE_COUNT": consumers["env_loader_files"],
        "PUBLIC_DB_DIAGNOSTIC_PRESENT": diagnostic,
        "PUBLIC_API_HEALTH_HTTP_200": h_status == 200,
        "PUBLIC_API_HEALTH_OK": health_ok,
        "PUBLIC_API_DATABASE_OK": database_ok,
        "PUBLIC_API_COMPETITIONS_READ_OK": competitions_ok,
        "PUBLIC_API_SAFE_STATE_OK": safe_state_ok,
        "DIRECT_DATABASE_CONNECTION_PERFORMED": False,
        "DATABASE_QUERY_PERFORMED": False,
        "REMOTE_FILE_WRITE_PERFORMED": False,
        "PROVIDER_MUTATION_PERFORMED": False,
    }

    for key, value in markers.items():
        if isinstance(value, bool):
            print(f"{key}={'true' if value else 'false'}")
        else:
            print(f"{key}={value}")

    required = (
        core_present["DB_HOST"]
        and core_present["DB_DATABASE"]
        and core_present["DB_USERNAME"]
        and core_present["DB_PASSWORD"]
        and consumers["core_db_consumer_files"] > 0
        and h_status == 200
        and health_ok
        and database_ok
        and competitions_ok
        and safe_state_ok
        and not diagnostic
    )
    print(f"ATLAS_AI_DB_DEPENDENCY_AUDIT_PASSED={'true' if required else 'false'}")
    return 0 if required else 2

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditStop as exc:
        print("ATLAS_AI_DB_DEPENDENCY_AUDIT_PASSED=false")
        print(f"STOP_REASON={exc}")
        print("DIRECT_DATABASE_CONNECTION_PERFORMED=false")
        print("DATABASE_QUERY_PERFORMED=false")
        print("REMOTE_FILE_WRITE_PERFORMED=false")
        print("PROVIDER_MUTATION_PERFORMED=false")
        raise SystemExit(1)
