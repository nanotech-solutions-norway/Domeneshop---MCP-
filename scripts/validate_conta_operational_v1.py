#!/usr/bin/env python3
"""Read-only operational-v1 acceptance for the deployed Conta MCP runtime.

This validator performs no provider mutation and never opens a write gate.
It verifies the public contract, closed production controls, deployed runtime
hashes, authenticated MCP initialize/tools/list, read-only MCP calls, and the
non-mutating invoice-draft preview.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import certifi
import paramiko

SOURCE_COMMIT = "19d8b9fd3e7aec7fec7405df2ffec0e72839c9ac"
PUBLIC_BASE = "https://mcp.atlas-ai.no"
PUBLIC_MCP = PUBLIC_BASE + "/mcp"
REMOTE_ROOT = "/Custom Models/conta-mcp"
CONFIG_PATH = REMOTE_ROOT + "/config/conta_config.local.php"
KILL_PATH = REMOTE_ROOT + "/storage/write-kill-switch.json"
AUTH_PATH = REMOTE_ROOT + "/storage/production-authorization.json"
MANIFEST_PATH = REMOTE_ROOT + "/storage/approved-release-manifest.json"
EXECUTION_TOOL = "conta_create_invoice_draft"
PREVIEW_TOOL = "conta_preview_invoice_draft"
MAX_RESPONSE = 524288

RUNTIME_PATHS = (
    "app/ApprovalEnvelopeVerifier.php", "app/AuditLogger.php", "app/Config.php",
    "app/ContaClient.php", "app/ContaTools.php", "app/HttpClient.php",
    "app/InvoiceDraftPreview.php", "app/InvoiceDraftReadbackVerifier.php",
    "app/McpServer.php", "app/ProductionAuthorizationGate.php",
    "app/ReleaseManifestGuard.php", "app/SandboxAuthorizationGate.php",
    "app/Security.php", "app/WriteDispatchPermit.php",
    "app/WriteExecutionLedger.php", "app/WriteKillSwitch.php",
    "app/WritePolicy.php", "app/bootstrap.php", "config/tool_policy.php",
)

EXPECTED_TOOLS = {
    "conta_health_check",
    "conta_list_organizations",
    "conta_list_customers",
    "conta_get_customer",
    "conta_list_invoices",
    "conta_get_invoice",
    PREVIEW_TOOL,
}


class Stop(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remote_exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def read_remote(sftp: paramiko.SFTPClient, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def parse_php_single_string(text: str, key: str) -> str:
    pattern = re.compile(
        rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>\s*'(?P<v>(?:\\\\.|[^'])*)'\s*,?"
    )
    match = pattern.search(text)
    if not match:
        raise Stop(f"server_config_literal_missing:{key}")
    raw = match.group("v")
    return raw.replace("\\'", "'").replace("\\\\", "\\")


def http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: Any | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=request_headers)
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            raw = response.read(MAX_RESPONSE + 1)
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE + 1)
        status = exc.code
    if len(raw) > MAX_RESPONSE:
        raise Stop("response_too_large")
    try:
        decoded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        decoded = None
    return status, decoded


def mcp_call(token: str, request_id: int, method: str, params: dict[str, Any]) -> dict[str, Any]:
    status, envelope = http_json(
        PUBLIC_MCP,
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
        payload={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
    )
    if status != 200 or not isinstance(envelope, dict) or "error" in envelope:
        raise Stop(f"mcp_call_failed:{method}:http_{status}")
    result = envelope.get("result")
    if not isinstance(result, dict):
        raise Stop(f"mcp_result_missing:{method}")
    return result


def mcp_tool(token: str, request_id: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return mcp_call(token, request_id, "tools/call", {"name": name, "arguments": arguments})


def successful_tool_data(result: dict[str, Any]) -> Any:
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        raise Stop("mcp_structured_content_missing")
    if result.get("isError") is not False or structured.get("ok") is not True or structured.get("status") != 200:
        raise Stop("mcp_tool_failed")
    return structured.get("data")


def validate_public_health() -> dict[str, Any]:
    for path in ("/", "/health", "/mcp"):
        status, _ = http_json(PUBLIC_BASE + path)
        if status != 200:
            raise Stop(f"public_endpoint_failed:{path}:{status}")
    for path in ("/app/", "/config/", "/storage/", "/docs/", "/tests/", "/bin/"):
        status, _ = http_json(PUBLIC_BASE + path)
        if status == 200:
            raise Stop(f"protected_path_public:{path}")

    unauth_status, _ = http_json(
        PUBLIC_MCP,
        method="POST",
        payload={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "operational-v1-acceptance", "version": "1.0.0"},
            },
        },
    )
    if unauth_status != 401:
        raise Stop("unauthenticated_initialize_not_rejected")

    status, health = http_json(PUBLIC_BASE + "/health")
    if status != 200 or not isinstance(health, dict):
        raise Stop("health_invalid")
    cfg = health.get("config")
    if health.get("status") != "ok" or health.get("service") != "conta-mcp-server" or not isinstance(cfg, dict):
        raise Stop("health_identity_invalid")
    required = {
        "environment": "production",
        "write_preview_enabled": True,
        "write_tools_enabled": False,
        "runtime_write_blocked": True,
        "execution_allowed": False,
        "production_write_approved": False,
        "allowed_write_action_count": 0,
        "allowed_write_organization_count": 0,
        "require_signed_approvals": True,
    }
    for key, expected in required.items():
        if cfg.get(key) != expected:
            raise Stop(f"closed_health_mismatch:{key}")
    return health


def candidate_hashes(candidate_root: Path) -> dict[str, str]:
    observed = subprocess.check_output(
        ["git", "-C", str(candidate_root), "rev-parse", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    if observed != SOURCE_COMMIT:
        raise Stop("candidate_commit_mismatch")
    hashes: dict[str, str] = {}
    for relative in RUNTIME_PATHS:
        path = candidate_root / relative
        if not path.is_file():
            raise Stop(f"candidate_file_missing:{relative}")
        hashes[relative] = sha256_bytes(path.read_bytes())
    return hashes


def first_identifier(value: Any) -> str | None:
    if isinstance(value, dict):
        if "id" in value and isinstance(value["id"], (str, int)) and str(value["id"]).strip():
            return str(value["id"]).strip()
        for key in ("hits", "items", "content", "data", "results", "invoices"):
            if key in value:
                candidate = first_identifier(value[key])
                if candidate:
                    return candidate
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                candidate = first_identifier(nested)
                if candidate:
                    return candidate
    elif isinstance(value, list):
        for item in value:
            candidate = first_identifier(item)
            if candidate:
                return candidate
    return None


def run(candidate_root: Path) -> int:
    sftp_user = os.environ.get("DS_SFTP_USER", "").strip()
    sftp_password = os.environ.get("DS_SFTP_VALUE", "").strip()
    customer_ref = os.environ.get("CONTA_PROD_CUSTOMER_REFERENCE", "").strip()
    vat_code = os.environ.get("CONTA_PROD_VAT_CODE", "").strip()
    if not sftp_user or not sftp_password:
        raise Stop("protected_sftp_credentials_missing")
    if not customer_ref or not vat_code:
        raise Stop("protected_preview_inputs_missing")
    if not customer_ref.isdigit():
        raise Stop("customer_reference_format_invalid")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", vat_code):
        raise Stop("vat_code_format_invalid")

    validate_public_health()
    expected_hashes = candidate_hashes(candidate_root)

    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=sftp_user, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        if not remote_exists(sftp, CONFIG_PATH) or not remote_exists(sftp, KILL_PATH):
            raise Stop("required_runtime_control_file_missing")
        if remote_exists(sftp, AUTH_PATH):
            raise Stop("production_authorization_packet_present")
        if remote_exists(sftp, MANIFEST_PATH):
            raise Stop("approved_release_manifest_present")

        kill = json.loads(read_remote(sftp, KILL_PATH))
        if not isinstance(kill, dict) or kill.get("globalBlocked") is not True:
            raise Stop("kill_switch_not_globally_blocked")

        config_text = read_remote(sftp, CONFIG_PATH).decode("utf-8")
        bearer = parse_php_single_string(config_text, "mcp_bearer_token")
        release_commit = parse_php_single_string(config_text, "release_commit")
        if not bearer:
            raise Stop("mcp_bearer_token_missing")
        if release_commit.lower() != SOURCE_COMMIT:
            raise Stop("deployed_release_commit_mismatch")

        for relative, expected in expected_hashes.items():
            remote_path = posixpath.join(REMOTE_ROOT, relative)
            if not remote_exists(sftp, remote_path):
                raise Stop(f"runtime_file_missing:{relative}")
            if sha256_bytes(read_remote(sftp, remote_path)) != expected:
                raise Stop(f"runtime_hash_mismatch:{relative}")
    finally:
        sftp.close()
        transport.close()

    init = mcp_call(
        bearer,
        10,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "operational-v1-acceptance", "version": "1.0.0"},
        },
    )
    if not isinstance(init, dict):
        raise Stop("authenticated_initialize_invalid")

    listed = mcp_call(bearer, 11, "tools/list", {})
    tools = listed.get("tools")
    if not isinstance(tools, list):
        raise Stop("tools_list_invalid")
    names = {item.get("name") for item in tools if isinstance(item, dict)}
    if not EXPECTED_TOOLS.issubset(names):
        raise Stop("expected_tool_missing")
    if EXECUTION_TOOL in names:
        raise Stop("execution_tool_visible_while_closed")

    successful_tool_data(mcp_tool(bearer, 20, "conta_health_check", {"checkConta": True}))
    successful_tool_data(mcp_tool(bearer, 21, "conta_list_organizations", {}))
    successful_tool_data(mcp_tool(bearer, 22, "conta_list_customers", {"hits": 1, "page": 0}))
    successful_tool_data(mcp_tool(bearer, 23, "conta_get_customer", {"customerId": customer_ref}))
    invoice_list = successful_tool_data(mcp_tool(bearer, 24, "conta_list_invoices", {"hits": 1, "page": 0}))
    invoice_id = first_identifier(invoice_list)
    if invoice_id:
        successful_tool_data(mcp_tool(bearer, 25, "conta_get_invoice", {"invoiceId": invoice_id}))

    payload = {
        "registrationSource": "CONTA",
        "invoiceDraftLines": [{
            "description": "Conta MCP Operational V1 Acceptance Preview",
            "price": 1.0,
            "quantity": 1,
            "discount": 0,
            "vatCode": vat_code,
            "lineNo": 1,
        }],
        "type": "NORMAL",
        "customerId": int(customer_ref),
        "invoiceLanguage": "NO",
        "invoiceCurrency": "NOK",
    }
    preview = successful_tool_data(mcp_tool(bearer, 30, PREVIEW_TOOL, {"invoice": payload}))
    if not isinstance(preview, dict):
        raise Stop("preview_data_invalid")
    if preview.get("provider_call_performed") is not False:
        raise Stop("preview_provider_call_unexpected")
    if preview.get("execution_eligible_now") is not False:
        raise Stop("preview_execution_eligible_while_closed")
    if not isinstance(preview.get("payload_hash_sha256"), str):
        raise Stop("preview_payload_hash_missing")

    print("PUBLIC_CONTRACT_VALIDATED=true")
    print("REMOTE_RUNTIME_HASHES_VERIFIED=true")
    print("DEPLOYED_RELEASE_COMMIT_VERIFIED=true")
    print("KILL_SWITCH_GLOBAL_BLOCKED=true")
    print("PRODUCTION_AUTHORIZATION_PRESENT=false")
    print("APPROVED_RELEASE_MANIFEST_PRESENT=false")
    print("AUTHENTICATED_INITIALIZE_VERIFIED=true")
    print("TOOLS_LIST_CONTRACT_VERIFIED=true")
    print("EXECUTION_TOOL_VISIBLE=false")
    print("READ_ONLY_MCP_SMOKE_VERIFIED=true")
    print(f"GET_INVOICE_READBACK_EXERCISED={'true' if invoice_id else 'false'}")
    print("PREVIEW_VERIFIED=true")
    print("PREVIEW_PROVIDER_CALL_PERFORMED=false")
    print("PROVIDER_MUTATION_PERFORMED=false")
    print("CONTA_MCP_V1_ACCEPTANCE_PASSED=true")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True)
    args = parser.parse_args()
    return run(Path(args.candidate_root))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(f"CONTA_MCP_V1_ACCEPTANCE_PASSED=false")
        print(f"STOP_REASON={exc}")
        print("PROVIDER_MUTATION_PERFORMED=false")
        raise SystemExit(1)
