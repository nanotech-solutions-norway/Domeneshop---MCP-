"""Deploy the authorized Conta MCP production-write implementation fail closed.

This controller is hard-bound to the operator-authorized deployment request and
implementation commit. It may provision the validated production Conta API
credential and organization identifier into the existing server-only config,
deploy exactly the protected runtime files, and validate the fail-closed public
contract. It never calls Conta and never enables production execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import ssl
import stat
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

import certifi
import paramiko

SOURCE_COMMIT = "19d8b9fd3e7aec7fec7405df2ffec0e72839c9ac"
AUTHORIZATION_REQUEST_COMMIT = "04b3d828845e7220751dfde7b54a2316d3cabdcd"
ORGANIZATION_REFERENCE_SHA256 = "9ee050155b0c35066a2ea426c72a65e5cdd2806f18a3cf9829fb132bd66634ab"
DECISION_PACKET_SHA256 = "cfc5fc9ab38b8fa23fe813b191b1dd401ffa4b217cf14af8d8f8fda7c555117f"
REMOTE_RUNTIME_ROOT = "/Custom Models/conta-mcp"
REMOTE_BACKUP_ROOT = "/Custom Models/conta-mcp-backups"
PUBLIC_BASE_URL = "https://mcp.atlas-ai.no"

RUNTIME_PATHS = (
    "app/ApprovalEnvelopeVerifier.php",
    "app/AuditLogger.php",
    "app/Config.php",
    "app/ContaClient.php",
    "app/ContaTools.php",
    "app/HttpClient.php",
    "app/InvoiceDraftPreview.php",
    "app/InvoiceDraftReadbackVerifier.php",
    "app/McpServer.php",
    "app/ProductionAuthorizationGate.php",
    "app/ReleaseManifestGuard.php",
    "app/SandboxAuthorizationGate.php",
    "app/Security.php",
    "app/WriteDispatchPermit.php",
    "app/WriteExecutionLedger.php",
    "app/WriteKillSwitch.php",
    "app/WritePolicy.php",
    "app/bootstrap.php",
    "config/tool_policy.php",
)
SERVER_CONFIG_PATH = f"{REMOTE_RUNTIME_ROOT}/config/conta_config.local.php"
KILL_SWITCH_PATH = f"{REMOTE_RUNTIME_ROOT}/storage/write-kill-switch.json"
PRODUCTION_AUTHORIZATION_PATH = f"{REMOTE_RUNTIME_ROOT}/storage/production-authorization.json"
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
                raise RuntimeError("remote_path_not_directory")
        except OSError:
            sftp.mkdir(current, mode=0o700)


def publish_bytes(sftp: paramiko.SFTPClient, target: str, data: bytes, mode: int) -> None:
    temp = f"{target}.conta-production-deploy-tmp"
    if remote_exists(sftp, temp):
        sftp.remove(temp)
    ensure_remote_directory(sftp, posixpath.dirname(target))
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


def validate_basic_public_contract() -> None:
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
                "clientInfo": {"name": "production-deployment-gate", "version": "1.0.0"},
            },
        },
        separators=(",", ":"),
    ).encode()
    status_code, _ = http_request("/mcp", method="POST", body=initialize)
    if status_code != 401:
        raise RuntimeError("unauthenticated_initialize_not_rejected")


def validate_post_deployment_health() -> None:
    status_code, body = http_request("/health")
    if status_code != 200:
        raise RuntimeError("health_check_failed")
    try:
        health = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("health_json_invalid") from None
    config = health.get("config", {}) if isinstance(health, dict) else {}
    required = {
        "environment": "production",
        "base_url": "https://api.gateway.conta.no",
        "has_conta_api_key": True,
        "has_default_organization_id": True,
        "write_preview_enabled": True,
        "write_tools_enabled": False,
        "runtime_write_blocked": True,
        "execution_allowed": False,
        "production_write_approved": False,
        "allowed_write_action_count": 0,
        "allowed_write_organization_count": 0,
        "has_production_organization_reference_hash": True,
        "has_production_decision_packet_hash": True,
        "production_max_invoice_draft_lines": 1,
        "production_max_invoice_draft_line_amount": 1,
        "production_max_invoice_draft_total": 1,
        "require_signed_approvals": True,
        "has_release_commit": True,
    }
    if health.get("status") != "ok" or health.get("service") != "conta-mcp-server":
        raise RuntimeError("unexpected_health_identity")
    for key, expected in required.items():
        if config.get(key) != expected:
            raise RuntimeError(f"fail_closed_health_mismatch:{key}")


def verify_candidate_commit(candidate_root: Path) -> None:
    try:
        observed = subprocess.check_output(
            ["git", "-C", str(candidate_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        raise RuntimeError("candidate_commit_unverifiable") from None
    if observed != SOURCE_COMMIT:
        raise RuntimeError("candidate_commit_mismatch")


def local_candidate(candidate_root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    verify_candidate_commit(candidate_root)
    payload: dict[str, bytes] = {}
    hashes: dict[str, str] = {}
    for relative in RUNTIME_PATHS:
        safe_relative_path(relative)
        source = candidate_root / Path(relative)
        if not source.is_file():
            raise RuntimeError(f"candidate_file_missing:{relative}")
        data = source.read_bytes()
        payload[relative] = data
        hashes[relative] = sha256(data)
    if len(payload) != 19:
        raise RuntimeError("candidate_scope_count_mismatch")
    return payload, hashes


def php_single_quoted(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def update_php_config(existing: bytes, api_key: str, org_id: str) -> bytes:
    try:
        text = existing.decode("utf-8")
    except UnicodeDecodeError:
        raise RuntimeError("server_config_not_utf8") from None
    if "<?php" not in text or "return [" not in text or "];" not in text:
        raise RuntimeError("server_config_unexpected_shape")
    if sha256(org_id.encode()) != ORGANIZATION_REFERENCE_SHA256:
        raise RuntimeError("production_organization_hash_mismatch")
    if not api_key.strip() or not org_id.strip():
        raise RuntimeError("production_credential_input_missing")

    updates = {
        "environment": php_single_quoted("production"),
        "conta_api_key": php_single_quoted(api_key),
        "default_organization_id": php_single_quoted(org_id),
        "enable_write_preview": "true",
        "enable_write_tools": "false",
        "runtime_write_blocked": "true",
        "execution_allowed": "false",
        "production_write_approved": "false",
        "allowed_write_organization_ids": php_single_quoted(""),
        "allowed_write_actions": php_single_quoted(""),
        "production_organization_reference_hash": php_single_quoted(ORGANIZATION_REFERENCE_SHA256),
        "production_decision_packet_sha256": php_single_quoted(DECISION_PACKET_SHA256),
        "production_max_invoice_draft_lines": "1",
        "production_max_invoice_draft_line_amount": "1.00",
        "production_max_invoice_draft_total": "1.00",
        "release_commit": php_single_quoted(SOURCE_COMMIT),
        "write_policy_version": php_single_quoted("2026-08-19-production-gate1"),
        "require_signed_approvals": "true",
    }

    missing: list[tuple[str, str]] = []
    for key, literal in updates.items():
        pattern = re.compile(
            rf"(?m)^(?P<indent>\s*)['\"]{re.escape(key)}['\"]\s*=>\s*[^,\r\n]*(?P<comma>,\s*(?://[^\r\n]*)?)$"
        )
        matches = list(pattern.finditer(text))
        if len(matches) > 1:
            raise RuntimeError("server_config_duplicate_authorized_key")
        if len(matches) == 1:
            match = matches[0]
            replacement = f"{match.group('indent')}'{key}' => {literal}{match.group('comma')}"
            text = text[: match.start()] + replacement + text[match.end() :]
        else:
            missing.append((key, literal))

    if missing:
        insertion_point = text.rfind("];")
        if insertion_point < 0:
            raise RuntimeError("server_config_closing_array_missing")
        block = "".join(f"    '{key}' => {literal},\n" for key, literal in missing)
        text = text[:insertion_point] + block + text[insertion_point:]

    for key in updates:
        occurrences = len(re.findall(rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>", text))
        if occurrences != 1:
            raise RuntimeError("server_config_authorized_key_verification_failed")
    return text.encode("utf-8")


def validate_kill_switch(data: bytes) -> None:
    try:
        document = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("kill_switch_invalid") from None
    if not isinstance(document, dict) or document.get("globalBlocked") is not True:
        raise RuntimeError("kill_switch_not_globally_blocked")


def deploy(candidate_root: Path, run_token: str) -> dict[str, Any]:
    if not run_token.replace("-", "").isdigit():
        raise ValueError("invalid_run_token")
    sftp_user = os.environ.get("DS_SFTP_USER", "")
    sftp_password = os.environ.get("DS_SFTP_VALUE", "")
    api_key = os.environ.get("CONTA_PROD_API_KEY", "")
    org_id = os.environ.get("CONTA_PROD_ORG_ID", "")
    if not sftp_user or not sftp_password:
        raise RuntimeError("protected_sftp_credentials_missing")
    if not api_key or not org_id:
        raise RuntimeError("protected_conta_production_inputs_missing")
    if sha256(org_id.encode()) != ORGANIZATION_REFERENCE_SHA256:
        raise RuntimeError("production_organization_hash_mismatch")

    payload, candidate_hashes = local_candidate(candidate_root)
    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=sftp_user, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    backup_root = f"{REMOTE_BACKUP_ROOT}/production-{SOURCE_COMMIT[:12]}-{run_token}"
    prior: dict[str, dict[str, Any]] = {}
    preserved_before: dict[str, str] = {}
    config_before: bytes | None = None
    config_mode = 0o600
    kill_switch_before: bytes | None = None
    mutation_started = False

    try:
        if not remote_exists(sftp, SERVER_CONFIG_PATH):
            raise RuntimeError("server_only_config_missing")
        config_info = sftp.stat(SERVER_CONFIG_PATH)
        config_mode = stat.S_IMODE(config_info.st_mode)
        config_before = read_remote(sftp, SERVER_CONFIG_PATH)
        config_after_bytes = update_php_config(config_before, api_key, org_id)

        if not remote_exists(sftp, KILL_SWITCH_PATH):
            raise RuntimeError("kill_switch_file_missing")
        kill_switch_before = read_remote(sftp, KILL_SWITCH_PATH)
        validate_kill_switch(kill_switch_before)
        if remote_exists(sftp, PRODUCTION_AUTHORIZATION_PATH):
            raise RuntimeError("production_authorization_packet_must_be_absent")

        for path in PRESERVED_HASH_PATHS:
            if not remote_exists(sftp, path):
                raise RuntimeError("required_preserved_path_missing")
            preserved_before[path] = sha256(read_remote(sftp, path))

        ensure_remote_directory(sftp, backup_root)
        for relative in RUNTIME_PATHS:
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            exists = remote_exists(sftp, target)
            item: dict[str, Any] = {"existed": exists}
            if exists:
                info = sftp.stat(target)
                data = read_remote(sftp, target)
                item.update({"sha256": sha256(data), "mode": stat.S_IMODE(info.st_mode)})
                backup_path = posixpath.join(backup_root, relative)
                publish_bytes(sftp, backup_path, data, 0o600)
            prior[relative] = item

        publish_bytes(sftp, f"{backup_root}/conta_config.local.php", config_before, 0o600)
        publish_bytes(sftp, f"{backup_root}/write-kill-switch.json", kill_switch_before, 0o600)
        evidence = {
            "classification": "CONTA_PRODUCTION_FAIL_CLOSED_PREDEPLOYMENT_BACKUP",
            "authorization_request_commit": AUTHORIZATION_REQUEST_COMMIT,
            "source_commit": SOURCE_COMMIT,
            "organization_reference_sha256": ORGANIZATION_REFERENCE_SHA256,
            "candidate_file_count": len(RUNTIME_PATHS),
            "candidate_hashes": candidate_hashes,
            "targets": prior,
            "server_config_backed_up": True,
            "kill_switch_backed_up": True,
            "kill_switch_global_blocked": True,
            "production_authorization_packet_present": False,
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
        print("KILL_SWITCH_GLOBAL_BLOCKED=true")
        print("PRODUCTION_AUTHORIZATION_PACKET_PRESENT=false")

        mutation_started = True
        for relative, data in payload.items():
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            mode = int(prior[relative].get("mode", 0o644))
            publish_bytes(sftp, target, data, mode)
        publish_bytes(sftp, SERVER_CONFIG_PATH, config_after_bytes, config_mode)

        for relative, expected in candidate_hashes.items():
            target = posixpath.join(REMOTE_RUNTIME_ROOT, relative)
            if sha256(read_remote(sftp, target)) != expected:
                raise RuntimeError("remote_candidate_hash_mismatch")
        if sha256(read_remote(sftp, SERVER_CONFIG_PATH)) != sha256(config_after_bytes):
            raise RuntimeError("remote_server_config_hash_mismatch")
        if sha256(read_remote(sftp, KILL_SWITCH_PATH)) != sha256(kill_switch_before):
            raise RuntimeError("kill_switch_changed")
        validate_kill_switch(read_remote(sftp, KILL_SWITCH_PATH))
        if remote_exists(sftp, PRODUCTION_AUTHORIZATION_PATH):
            raise RuntimeError("production_authorization_packet_appeared")
        for path, expected in preserved_before.items():
            if sha256(read_remote(sftp, path)) != expected:
                raise RuntimeError("preserved_path_changed")

        validate_basic_public_contract()
        validate_post_deployment_health()
        print("IMPLEMENTATION_DEPLOYED=true")
        print(f"DEPLOYED_IMPLEMENTATION_COMMIT={SOURCE_COMMIT}")
        print("PRODUCTION_CREDENTIAL_PRESENT=true")
        print("PRODUCTION_ORGANIZATION_CONFIG_PRESENT=true")
        print(f"PRODUCTION_ORGANIZATION_REFERENCE_SHA256={ORGANIZATION_REFERENCE_SHA256}")
        print("WRITE_PREVIEW_ENABLED=true")
        print("WRITE_TOOLS_ENABLED=false")
        print("RUNTIME_WRITE_BLOCKED=true")
        print("EXECUTION_ALLOWED=false")
        print("PRODUCTION_WRITE_APPROVED=false")
        print("ALLOWED_WRITE_ACTION_COUNT=0")
        print("ALLOWED_WRITE_ORGANIZATION_COUNT=0")
        print("KILL_SWITCH_GLOBAL_BLOCKED=true")
        print("PUBLIC_BRIDGE_PRESERVED=true")
        print("SERVER_ONLY_CONFIG_PROVISIONED=true")
        print("REMOTE_PAYLOAD_HASHES_VERIFIED=true")
        print("PROVIDER_WRITE_CALL_PERFORMED=false")
        print("PRODUCTION_MUTATION_PERFORMED=false")
        print("SECRET_VALUE_PRINTED=false")
        print("RAW_ORGANIZATION_ID_PRINTED=false")
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
            try:
                if config_before is not None:
                    publish_bytes(sftp, SERVER_CONFIG_PATH, config_before, config_mode)
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
        payload, _ = local_candidate(args.candidate_root)
        if len(payload) != 19:
            raise RuntimeError("candidate_scope_count_mismatch")
        validate_basic_public_contract()
        print("IMMUTABLE_PRODUCTION_CANDIDATE_VALIDATED=true")
        print(f"CANDIDATE_FILE_COUNT={len(payload)}")
        print("PROVIDER_CALL_PERFORMED=false")
        print("PRODUCTION_WRITE_AUTHORIZED=false")
        if args.validate_only:
            return 0
        if not args.run_token:
            raise RuntimeError("run_token_required")
        deploy(args.candidate_root, args.run_token)
        return 0
    except Exception as exc:
        error_class = str(exc).split(":", 1)[0] or exc.__class__.__name__
        print(f"::error title=Fail-closed production deployment stopped::{error_class}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
