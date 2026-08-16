"""Deploy one immutable Conta MCP runtime candidate through a protected gate.

The script is intentionally hard-bound to the operator-authorized 2026-08-16
candidate. It backs up every existing overwrite target on the server, preserves
server-only configuration and the public bridge, verifies all uploaded hashes,
and rolls the target paths back on any deployment or public-contract failure.
It never calls Conta and never enables a write tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import ssl
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

import paramiko
import certifi


SOURCE_COMMIT = "7d97a6330e4aff5a6e251ad19d717d7408cf3825"
REMOTE_RUNTIME_ROOT = "/Custom Models/conta-mcp"
REMOTE_BACKUP_ROOT = "/Custom Models/conta-mcp-backups"
PUBLIC_BASE_URL = "https://mcp.atlas-ai.no"

EXPECTED_HASHES = {
    "app/ApprovalEnvelopeVerifier.php": "15be802a1fcdf5608d58ac187d0c783f36b70ba7ef764a69f23da8e5e1ebcd51",
    "app/AuditLogger.php": "7be47f4d66b9e0bea5a94a436dbbb343ca9bf394705db17a16750f40da4c12fb",
    "app/Config.php": "01def2a0254d4c1f7e2a83159aa37ad2d49172de5870022d583a51ff13701bea",
    "app/ContaClient.php": "c9b4633749409af2a6b76145593839cd72e9f6ffc6d15feef13e2c503fb1bbe1",
    "app/ContaTools.php": "5626cc5b4374e510cdc989df59b11c4fd3fe04d54fac3735a6e5464619f7cd18",
    "app/HttpClient.php": "e088dcb506d6b670a6103828f3cf2344dcbfb56b2b8f9dbf85e96509cdac0dd9",
    "app/InvoiceDraftPreview.php": "d976b54b1ddc55a5399367ce35b35144d687d462cbf1217a7d5d469572c54fc8",
    "app/InvoiceDraftReadbackVerifier.php": "04aea42187834c5f692e4ef85b337aaf5a8b9af043259971ec4d557aa06e138d",
    "app/McpServer.php": "6b12f5fb849e4055aef8342117f5efdd3a59433c1a9e6541440033ef9e1ca54a",
    "app/ReleaseManifestGuard.php": "35989dd9678769b02c33c235a751c7dfea98139a5befb0568b27c37d5bc3a63f",
    "app/SandboxAuthorizationGate.php": "0c62c37e2fafb0a518be6b6dc4f7682cc9999a601dbad05d3cfbee4dfd469c71",
    "app/Security.php": "f7c3ba277387c01a0a41d15af5136c19eca59cb90cd966dae55c25a7d5b394d0",
    "app/WriteDispatchPermit.php": "1bbf1dee22de280f8902dd65359b218f5e2f7aee4eae8e1d41af7293b90e5fcf",
    "app/WriteExecutionLedger.php": "86639a2eb588b4c4d9402027f2f957da462f665b306408a8fed1b51e6332b008",
    "app/WriteKillSwitch.php": "27df547e9330a8342e41fc665f58caed3b19b53bae2ed2d3635ec5bf291bd373",
    "app/WritePolicy.php": "ba455e6c969541ab9ee96a7318288ce4a5b8addcb1c9f2bcc44849586361e472",
    "app/bootstrap.php": "54d1b4aa442f3529a0b72885aa6f73d6e106c1bae33c01bf43b2b6f04a4297a9",
    "config/tool_policy.php": "1b2d27fb5c8d1098b73810d0036636284fde8f5b1a1388c3bfde8c2088cabe7d",
}

SERVER_CONFIG_PATH = f"{REMOTE_RUNTIME_ROOT}/config/conta_config.local.php"
PRESERVED_HASH_PATHS = (
    f"{REMOTE_RUNTIME_ROOT}/.htaccess",
    "/www/cm/.htaccess",
    "/www/cm/index.php",
    "/www/cm/health.php",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative_path(value: str) -> str:
    normalized = str(PurePosixPath(value))
    if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        raise ValueError("candidate_path_outside_runtime")
    return normalized


def remote_exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def read_remote(sftp: paramiko.SFTPClient, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def ensure_remote_directory(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/"
    for part in PurePosixPath(path).parts:
        if part == "/":
            continue
        current = posixpath.join(current, part)
        try:
            info = sftp.stat(current)
            if not stat.S_ISDIR(info.st_mode):
                raise RuntimeError("remote_backup_path_not_directory")
        except OSError:
            sftp.mkdir(current, mode=0o700)


def publish_bytes(sftp: paramiko.SFTPClient, target: str, data: bytes, mode: int) -> None:
    temp = f"{target}.conta-deploy-tmp"
    if remote_exists(sftp, temp):
        sftp.remove(temp)
    with sftp.open(temp, "wb") as handle:
        handle.write(data)
    sftp.chmod(temp, mode)
    if sha256(read_remote(sftp, temp)) != sha256(data):
        sftp.remove(temp)
        raise RuntimeError("remote_temporary_hash_mismatch")
    try:
        sftp.posix_rename(temp, target)
    except OSError:
        if remote_exists(sftp, target):
            sftp.remove(target)
        sftp.rename(temp, target)


def http_request(path: str, *, method: str = "GET", body: bytes | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(
        f"{PUBLIC_BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=20, context=context) as response:
            return response.status, response.read(262_145)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(262_145)


def validate_public_contract() -> None:
    for path in ("/", "/health", "/mcp"):
        status_code, _ = http_request(path)
        if status_code != 200:
            raise RuntimeError("public_service_check_failed")

    for path in ("/app/", "/config/", "/storage/", "/docs/", "/tests/", "/bin/"):
        status_code, _ = http_request(path)
        if status_code == 200:
            raise RuntimeError("protected_path_became_public")

    initialize = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "deployment-gate", "version": "1.0.0"},
            },
        },
        separators=(",", ":"),
    ).encode()
    status_code, _ = http_request("/mcp", method="POST", body=initialize)
    if status_code != 401:
        raise RuntimeError("unauthenticated_initialize_not_rejected")

    status_code, health_body = http_request("/health")
    if status_code != 200:
        raise RuntimeError("health_check_failed")
    health = json.loads(health_body)
    config = health.get("config", {})
    required = {
        "write_preview_enabled": True,
        "write_tools_enabled": False,
        "runtime_write_blocked": True,
        "execution_allowed": False,
        "production_write_approved": False,
        "allowed_write_action_count": 0,
        "allowed_write_organization_count": 0,
    }
    if health.get("status") != "ok" or health.get("service") != "conta-mcp-server":
        raise RuntimeError("unexpected_health_identity")
    for key, expected in required.items():
        if config.get(key) != expected:
            raise RuntimeError(f"fail_closed_health_mismatch:{key}")


def local_candidate(candidate_root: Path) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for relative, expected in EXPECTED_HASHES.items():
        safe_relative_path(relative)
        source = candidate_root / Path(relative)
        data = source.read_bytes()
        if sha256(data) != expected:
            raise RuntimeError(f"candidate_hash_mismatch:{relative}")
        payload[relative] = data
    return payload


def deploy(candidate_root: Path, run_token: str) -> dict[str, Any]:
    if not run_token.replace("-", "").isdigit():
        raise ValueError("invalid_run_token")
    user = os.environ.get("DS_SFTP_USER", "")
    password = os.environ.get("DS_SFTP_VALUE", "")
    if not user or not password:
        raise RuntimeError("protected_sftp_credentials_missing")

    payload = local_candidate(candidate_root)
    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    backup_root = f"{REMOTE_BACKUP_ROOT}/{SOURCE_COMMIT[:12]}-{run_token}"
    prior: dict[str, dict[str, Any]] = {}
    preserved_before: dict[str, str] = {}
    server_config_metadata: tuple[int, int, int]
    mutation_started = False

    try:
        if not remote_exists(sftp, SERVER_CONFIG_PATH):
            raise RuntimeError("server_only_config_missing")
        config_info = sftp.stat(SERVER_CONFIG_PATH)
        server_config_metadata = (
            int(config_info.st_size),
            stat.S_IMODE(config_info.st_mode),
            int(config_info.st_mtime),
        )

        for path in PRESERVED_HASH_PATHS:
            if not remote_exists(sftp, path):
                raise RuntimeError("required_preserved_path_missing")
            preserved_before[path] = sha256(read_remote(sftp, path))

        ensure_remote_directory(sftp, backup_root)
        for relative in EXPECTED_HASHES:
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            exists = remote_exists(sftp, target)
            item: dict[str, Any] = {"existed": exists}
            if exists:
                info = sftp.stat(target)
                data = read_remote(sftp, target)
                item.update({"sha256": sha256(data), "mode": stat.S_IMODE(info.st_mode)})
                backup_path = posixpath.join(backup_root, relative)
                ensure_remote_directory(sftp, posixpath.dirname(backup_path))
                publish_bytes(sftp, backup_path, data, 0o600)
            prior[relative] = item

        evidence = {
            "classification": "CONTA_FAIL_CLOSED_PREDEPLOYMENT_BACKUP",
            "source_commit": SOURCE_COMMIT,
            "target_root": REMOTE_RUNTIME_ROOT,
            "candidate_file_count": len(EXPECTED_HASHES),
            "targets": prior,
            "preserved_path_hashes": preserved_before,
            "server_only_config": {
                "present": True,
                "content_read": False,
                "size": server_config_metadata[0],
                "mode": server_config_metadata[1],
                "modified_epoch": server_config_metadata[2],
            },
            "provider_mutation_performed": False,
            "production_write_authorized": False,
        }
        publish_bytes(
            sftp,
            f"{backup_root}/rollback-evidence.json",
            json.dumps(evidence, indent=2, sort_keys=True).encode(),
            0o600,
        )
        print("PREDEPLOYMENT_SERVER_BACKUP_COMPLETE=true")
        print(f"BACKUP_TARGET_COUNT={len(prior)}")

        mutation_started = True
        for relative, data in payload.items():
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            mode = int(prior[relative].get("mode", 0o644))
            publish_bytes(sftp, target, data, mode)

        for relative, expected in EXPECTED_HASHES.items():
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            if sha256(read_remote(sftp, target)) != expected:
                raise RuntimeError("remote_candidate_hash_mismatch")

        for path, expected in preserved_before.items():
            if sha256(read_remote(sftp, path)) != expected:
                raise RuntimeError("preserved_path_changed")
        config_after = sftp.stat(SERVER_CONFIG_PATH)
        if (
            int(config_after.st_size),
            stat.S_IMODE(config_after.st_mode),
            int(config_after.st_mtime),
        ) != server_config_metadata:
            raise RuntimeError("server_only_config_metadata_changed")

        validate_public_contract()
        print("REMOTE_PAYLOAD_HASHES_VERIFIED=true")
        print("PUBLIC_BRIDGE_PRESERVED=true")
        print("SERVER_ONLY_CONFIG_PRESERVED=true")
        print("IMMEDIATE_FAIL_CLOSED_HTTP_VALIDATION_PASSED=true")
        print("PROVIDER_MUTATION_PERFORMED=false")
        print("PRODUCTION_WRITE_AUTHORIZED=false")
        return {"deployed": True, "rolled_back": False, "backup_root": backup_root}
    except Exception:
        if mutation_started:
            rollback_failed = False
            for relative, item in prior.items():
                target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
                try:
                    if item["existed"]:
                        backup_path = posixpath.join(backup_root, relative)
                        publish_bytes(sftp, target, read_remote(sftp, backup_path), int(item["mode"]))
                    elif remote_exists(sftp, target):
                        sftp.remove(target)
                except Exception:
                    rollback_failed = True
            print(f"ROLLBACK_COMPLETED={str(not rollback_failed).lower()}")
            if rollback_failed:
                print("::error title=Rollback incomplete::Manual server recovery is required.")
        raise
    finally:
        sftp.close()
        transport.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--run-token")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        local_candidate(args.candidate_root)
        validate_public_contract()
        print("IMMUTABLE_CANDIDATE_AND_PUBLIC_CONTRACT_VALIDATED=true")
        if args.validate_only:
            return 0
        if not args.run_token:
            raise RuntimeError("run_token_required")
        deploy(args.candidate_root, args.run_token)
        return 0
    except Exception as exc:
        error_class = str(exc).split(":", 1)[0] or exc.__class__.__name__
        print(f"::error title=Fail-closed deployment stopped::{error_class}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
