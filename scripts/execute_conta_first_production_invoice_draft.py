#!/usr/bin/env python3
"""One-shot controller for the authorized first Conta production invoice draft.

This controller is hard-bound to request commit a6b9470... and source commit
19d8b9f.... It opens the deployed MCP runtime only for one approved draft
attempt, never retries the execution call, performs GET-only reconciliation,
and always re-closes the runtime before returning.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import posixpath
import re
import ssl
import stat
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

import certifi
import paramiko

REQUEST_COMMIT = "a6b9470204775598c4f569ea2837c0bc712b0dc3"
SOURCE_COMMIT = "19d8b9fd3e7aec7fec7405df2ffec0e72839c9ac"
ORG_SHA256 = "9ee050155b0c35066a2ea426c72a65e5cdd2806f18a3cf9829fb132bd66634ab"
ACTION = "invoice_draft_create_v2"
TOOL = "conta_create_invoice_draft"
PREVIEW_TOOL = "conta_preview_invoice_draft"
PUBLIC_MCP = "https://mcp.atlas-ai.no/mcp"
PROVIDER_BASE = "https://api.gateway.conta.no"
REMOTE_ROOT = "/Custom Models/conta-mcp"
CONFIG_PATH = f"{REMOTE_ROOT}/config/conta_config.local.php"
KILL_PATH = f"{REMOTE_ROOT}/storage/write-kill-switch.json"
AUTH_PATH = f"{REMOTE_ROOT}/storage/production-authorization.json"
MANIFEST_PATH = f"{REMOTE_ROOT}/storage/approved-release-manifest.json"
MAX_RESPONSE = 524_288
LINE_DESCRIPTION = "Conta MCP First Production Validation"

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


class Stop(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), ensure_ascii=False, separators=(",", ":"))


def payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def signed_document(document: dict[str, Any], key: str, key_id: str) -> dict[str, Any]:
    unsigned = dict(document)
    unsigned.pop("signature", None)
    unsigned["signatureAlgorithm"] = "HMAC-SHA256"
    unsigned["keyId"] = key_id
    signature = hmac.new(key.encode(), canonical_json(unsigned).encode(), hashlib.sha256).hexdigest()
    return {**unsigned, "signature": signature}


def remote_exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def read_remote(sftp: paramiko.SFTPClient, path: str) -> bytes:
    with sftp.open(path, "rb") as handle:
        return handle.read()


def publish(sftp: paramiko.SFTPClient, path: str, data: bytes, mode: int = 0o600) -> None:
    temp = path + ".conta-first-production-tmp"
    if remote_exists(sftp, temp):
        sftp.remove(temp)
    with sftp.open(temp, "wb") as handle:
        handle.write(data)
    sftp.chmod(temp, mode)
    if sha256_bytes(read_remote(sftp, temp)) != sha256_bytes(data):
        sftp.remove(temp)
        raise Stop("remote_temporary_hash_mismatch")
    try:
        sftp.posix_rename(temp, path)
    except OSError:
        if remote_exists(sftp, path):
            sftp.remove(path)
        sftp.rename(temp, path)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def parse_php_single_string(text: str, key: str) -> str:
    pattern = re.compile(
        rf"(?m)^\s*['\"]{re.escape(key)}['\"]\s*=>\s*'(?P<v>(?:\\\\.|[^'])*)'\s*,?"
    )
    match = pattern.search(text)
    if not match:
        raise Stop(f"server_config_literal_missing:{key}")
    raw = match.group("v")
    return raw.replace("\\'", "'").replace("\\\\", "\\")


def php_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def update_php_config(existing: bytes, updates: dict[str, str]) -> bytes:
    try:
        text = existing.decode("utf-8")
    except UnicodeDecodeError:
        raise Stop("server_config_not_utf8") from None
    for key, literal in updates.items():
        pattern = re.compile(
            rf"(?m)^(?P<i>\s*)['\"]{re.escape(key)}['\"]\s*=>\s*[^,\r\n]*(?P<c>,\s*(?://[^\r\n]*)?)$"
        )
        matches = list(pattern.finditer(text))
        if len(matches) > 1:
            raise Stop(f"server_config_duplicate_key:{key}")
        if matches:
            match = matches[0]
            replacement = f"{match.group('i')}'{key}' => {literal}{match.group('c')}"
            text = text[:match.start()] + replacement + text[match.end():]
        else:
            end = text.rfind("];")
            if end < 0:
                raise Stop("server_config_array_end_missing")
            text = text[:end] + f"    '{key}' => {literal},\n" + text[end:]
    return text.encode("utf-8")


def http_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
              payload: Any | None = None, timeout: int = 30) -> tuple[int, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, method=method, headers=request_headers)
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read(MAX_RESPONSE + 1)
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE + 1)
        status = exc.code
    except (urllib.error.URLError, TimeoutError):
        raise Stop("network_outcome_ambiguous") from None
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
    if status != 200 or not isinstance(envelope, dict):
        raise Stop(f"mcp_call_failed_http_{status}")
    if "error" in envelope:
        raise Stop("mcp_jsonrpc_error")
    result = envelope.get("result")
    if not isinstance(result, dict):
        raise Stop("mcp_result_missing")
    return result


def mcp_tool(token: str, request_id: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return mcp_call(token, request_id, "tools/call", {"name": name, "arguments": arguments})


def tool_names(token: str) -> list[str]:
    result = mcp_call(token, 50, "tools/list", {})
    entries = result.get("tools")
    if not isinstance(entries, list):
        raise Stop("tools_list_invalid")
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    if len(names) != len(entries) or not all(isinstance(name, str) for name in names):
        raise Stop("tools_list_invalid")
    return names


def successful_tool_data(result: dict[str, Any]) -> Any:
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        raise Stop("mcp_structured_content_missing")
    if result.get("isError") is not False or structured.get("ok") is not True or structured.get("status") != 200:
        raise Stop("mcp_tool_failed")
    return structured.get("data")


def count_drafts(body: Any) -> int:
    if isinstance(body, list):
        return len(body)
    if not isinstance(body, dict):
        raise Stop("invoice_draft_prestate_unrecognized")
    for key in ("hitCount", "totalCount", "totalElements", "total", "count"):
        value = body.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
    for key in ("hits", "items", "content", "data", "results", "invoiceDrafts"):
        value = body.get(key)
        if isinstance(value, list):
            return len(value)
    raise Stop("invoice_draft_prestate_unrecognized")


def iso_utc(seconds_from_now: int = 0) -> str:
    value = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds_from_now)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_expiry(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Stop("decision_expiry_invalid") from None
    if parsed.tzinfo is None:
        raise Stop("decision_expiry_invalid")
    return parsed.astimezone(dt.timezone.utc)


def oslo_today() -> str:
    # The authorized first run is on 2026-08-24 while Oslo is UTC+2.
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=2)).date().isoformat()


def safe_draft_list(api_key: str, org_id: str) -> tuple[int, Any]:
    url = (
        f"{PROVIDER_BASE}/invoice/organizations/{urllib.parse.quote(org_id, safe='')}"
        "/invoice-drafts?hits=100&page=0&sort=id"
    )
    status, body = http_json(url, headers={"apiKey": api_key})
    if status != 200:
        raise Stop(f"invoice_draft_list_get_failed_http_{status}")
    return count_drafts(body), body


def build_manifest(sftp: paramiko.SFTPClient, config: dict[str, str]) -> dict[str, Any]:
    runtime_files: dict[str, str] = {}
    for relative in RUNTIME_PATHS:
        path = posixpath.join(REMOTE_ROOT, relative)
        if not remote_exists(sftp, path):
            raise Stop(f"runtime_file_missing:{relative}")
        runtime_files[relative] = sha256_bytes(read_remote(sftp, path))
    runtime_files = dict(sorted(runtime_files.items()))
    route_map = {
        "create_invoice_draft_route": config["create_invoice_draft_route"],
        "readback_invoice_draft_route": config["readback_invoice_draft_route"],
    }
    return {
        "manifest_version": "2.0",
        "status": "APPROVED",
        "generated_at_utc": iso_utc(),
        "repository_commit": SOURCE_COMMIT,
        "write_policy_version": config["write_policy_version"],
        "provider_schema_sha256": config["provider_schema_sha256"].lower(),
        "route_map": route_map,
        "route_map_sha256": hashlib.sha256(canonical_json(route_map).encode()).hexdigest(),
        "runtime_files": runtime_files,
        "effective_write_state": {
            "write_tools_enabled": True,
            "runtime_write_blocked": False,
            "execution_allowed": True,
            "production_write_approved": True,
        },
        "approved_by": "operator_authorization_request_" + REQUEST_COMMIT[:12],
        "approved_at_utc": iso_utc(),
    }


def extract_execution_result(result: dict[str, Any]) -> tuple[bool, str | None, int | None]:
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        return False, None, None
    data = structured.get("data")
    if not isinstance(data, dict):
        return False, None, None
    verification = data.get("verification")
    verified = isinstance(verification, dict) and verification.get("verified") is True
    mismatches = verification.get("mismatches") if isinstance(verification, dict) else None
    mismatch_count = len(mismatches) if isinstance(mismatches, list) else None
    create = data.get("create")
    draft_id = None
    if isinstance(create, dict):
        for key in ("id", "invoiceDraftId", "invoice_draft_id"):
            if key in create and str(create[key]).strip():
                draft_id = str(create[key]).strip()
                break
    return verified, draft_id, mismatch_count


def run(args: argparse.Namespace) -> int:
    if args.authorization != "EXECUTE_CONTA_FIRST_PRODUCTION_A6B94702":
        raise Stop("execution_dispatch_authorization_mismatch")
    if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
        raise Stop("workflow_rerun_not_authorized")
    if os.environ.get("GITHUB_REF_NAME", "") != "main":
        raise Stop("execution_must_run_from_main")

    decision_hash = args.decision_packet_sha256.strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", decision_hash):
        raise Stop("decision_packet_sha256_invalid")
    expiry = parse_expiry(args.decision_packet_expires_at.strip())
    now = dt.datetime.now(dt.timezone.utc)
    if expiry <= now or expiry - now > dt.timedelta(hours=24, minutes=5):
        raise Stop("decision_attestation_expired_or_implausible")

    names = (
        "DS_SFTP_USER", "DS_SFTP_VALUE", "CONTA_PROD_API_KEY", "CONTA_PROD_ORG_ID",
        "CONTA_PROD_CUSTOMER_REFERENCE", "CONTA_PROD_VAT_CODE", "CONTA_PROD_INVOICE_DATE",
    )
    protected = {name: os.environ.get(name, "").strip() for name in names}
    missing = [name for name, value in protected.items() if not value]
    if missing:
        raise Stop("protected_execution_inputs_missing:" + ",".join(missing))

    org_id = protected["CONTA_PROD_ORG_ID"]
    customer_ref = protected["CONTA_PROD_CUSTOMER_REFERENCE"]
    vat_code = protected["CONTA_PROD_VAT_CODE"]
    invoice_date = protected["CONTA_PROD_INVOICE_DATE"]
    api_key = protected["CONTA_PROD_API_KEY"]
    if sha256_bytes(org_id.encode()) != ORG_SHA256:
        raise Stop("production_organization_hash_mismatch")
    if not customer_ref.isdigit():
        raise Stop("customer_reference_format_invalid")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", vat_code):
        raise Stop("vat_code_format_invalid")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", invoice_date):
        raise Stop("invoice_date_format_invalid")
    if invoice_date != oslo_today():
        raise Stop("invoice_date_not_current_oslo_date")

    transport = paramiko.Transport(("sftp.domeneshop.no", 22))
    transport.connect(username=protected["DS_SFTP_USER"], password=protected["DS_SFTP_VALUE"])
    sftp = paramiko.SFTPClient.from_transport(transport)
    config_before: bytes | None = None
    config_mode = 0o600
    provider_outcome = "NOT_DISPATCHED"
    execution_attempted = False
    readback_verified = False
    mismatch_count: int | None = None
    draft_id_hash: str | None = None
    reconciliation_count: int | None = None

    try:
        if not remote_exists(sftp, CONFIG_PATH) or not remote_exists(sftp, KILL_PATH):
            raise Stop("required_runtime_control_file_missing")
        if remote_exists(sftp, AUTH_PATH):
            raise Stop("unexpected_existing_production_authorization")
        if remote_exists(sftp, MANIFEST_PATH):
            raise Stop("unexpected_existing_approved_release_manifest")
        config_info = sftp.stat(CONFIG_PATH)
        config_mode = stat.S_IMODE(config_info.st_mode)
        config_before = read_remote(sftp, CONFIG_PATH)
        kill_before = read_remote(sftp, KILL_PATH)
        try:
            kill_doc = json.loads(kill_before)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise Stop("kill_switch_invalid") from None
        if not isinstance(kill_doc, dict) or kill_doc.get("globalBlocked") is not True:
            raise Stop("kill_switch_not_globally_blocked")

        config_text = config_before.decode("utf-8")
        config_values = {
            key: parse_php_single_string(config_text, key)
            for key in (
                "mcp_bearer_token", "approval_signing_key", "approval_key_id",
                "provider_schema_sha256", "create_invoice_draft_route",
                "readback_invoice_draft_route", "write_policy_version", "release_commit",
            )
        }
        if config_values["release_commit"].lower() != SOURCE_COMMIT:
            raise Stop("deployed_release_commit_mismatch")
        if len(config_values["approval_signing_key"]) < 32:
            raise Stop("approval_signing_key_unavailable")
        if not re.fullmatch(r"[a-f0-9]{64}", config_values["provider_schema_sha256"].lower()):
            raise Stop("provider_schema_hash_invalid")
        if config_values["create_invoice_draft_route"] != "/invoice/organizations/{opContextOrgId}/invoice-drafts":
            raise Stop("create_route_mismatch")
        if "{id}" not in config_values["readback_invoice_draft_route"] and "{invoiceDraftId}" not in config_values["readback_invoice_draft_route"]:
            raise Stop("readback_route_mismatch")

        # Deliberately stricter than the general duplicate rule: first production
        # execution is allowed only when the organization has zero existing drafts.
        prestate_count, _ = safe_draft_list(api_key, org_id)
        if prestate_count != 0:
            raise Stop(f"invoice_draft_prestate_not_empty_count_{prestate_count}")
        print("PRESTATE_INVOICE_DRAFT_COUNT=0")
        print("DUPLICATE_STOP_RULE=ZERO_EXISTING_DRAFTS")

        customer_url = (
            f"{PROVIDER_BASE}/invoice/organizations/{urllib.parse.quote(org_id, safe='')}"
            f"/customers/{urllib.parse.quote(customer_ref, safe='')}"
        )
        customer_status, customer_body = http_json(customer_url, headers={"apiKey": api_key})
        if customer_status != 200 or not isinstance(customer_body, dict):
            raise Stop(f"protected_customer_get_failed_http_{customer_status}")
        if str(customer_body.get("id", "")).strip() != customer_ref:
            raise Stop("protected_customer_identity_mismatch")
        if customer_body.get("isActive") is False:
            raise Stop("protected_customer_inactive")
        print("PROTECTED_CUSTOMER_GET_VERIFIED=true")
        print("CUSTOMER_REFERENCE_PRINTED=false")

        payload = {
            "registrationSource": "CONTA",
            "invoiceDraftLines": [{
                "description": LINE_DESCRIPTION,
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
        expected_payload_hash = payload_hash(payload)
        encoded_org = urllib.parse.quote(org_id, safe="")
        create_path = config_values["create_invoice_draft_route"].replace("{opContextOrgId}", encoded_org).replace("{orgId}", encoded_org)
        token = config_values["mcp_bearer_token"]

        if TOOL in tool_names(token):
            raise Stop("execution_tool_visible_before_gate_open")
        preview = mcp_tool(token, 10, PREVIEW_TOOL, {"organizationId": org_id, "invoice": payload})
        preview_data = successful_tool_data(preview)
        if not isinstance(preview_data, dict):
            raise Stop("preview_data_invalid")
        if preview_data.get("provider_call_performed") is not False:
            raise Stop("preview_provider_call_unexpected")
        if preview_data.get("payload_hash_sha256") != expected_payload_hash:
            raise Stop("runtime_preview_payload_hash_mismatch")
        if preview_data.get("execution_eligible_now") is not False:
            raise Stop("runtime_execution_eligible_before_gate_open")
        print(f"PAYLOAD_SHA256={expected_payload_hash}")
        print("PREVIEW_VERIFIED=true")
        print("PREVIEW_PROVIDER_CALL_PERFORMED=false")
        print("FISCAL_EXECUTION_DATE_BOUND=true")

        manifest = build_manifest(sftp, config_values)
        signing_key = config_values["approval_signing_key"]
        key_id = config_values["approval_key_id"]
        not_before = iso_utc(-5)
        expires_at = iso_utc(300)
        authorization_id = "prod-auth-" + uuid.uuid4().hex
        approval_id = "prod-approval-" + uuid.uuid4().hex
        nonce = uuid.uuid4().hex
        idempotency_key = "prod-idem-" + uuid.uuid4().hex

        authorization_packet = signed_document({
            "status": "APPROVED", "authorizationId": authorization_id,
            "candidateId": ACTION, "action": ACTION, "environment": "production",
            "organizationIdHash": ORG_SHA256, "payloadHash": expected_payload_hash,
            "method": "POST", "pathHash": hashlib.sha256(create_path.encode()).hexdigest(),
            "decisionPacketSha256": decision_hash, "notBefore": not_before,
            "expiresAt": expires_at, "maxProviderMutations": 1,
            "automaticRetry": False, "readbackRequired": True, "releaseApproved": True,
        }, signing_key, key_id)
        approval = signed_document({
            "approved": True, "oneUse": True, "approvalId": approval_id,
            "approvedBy": "operator_request_" + REQUEST_COMMIT[:12], "action": ACTION,
            "organizationId": org_id, "environment": "production",
            "payloadHash": expected_payload_hash, "method": "POST", "path": create_path,
            "issuedAt": not_before, "expiresAt": expires_at, "nonce": nonce,
            "idempotencyKey": idempotency_key,
        }, signing_key, key_id)

        publish(sftp, MANIFEST_PATH, json_bytes(manifest))
        publish(sftp, AUTH_PATH, json_bytes(authorization_packet))
        open_config = update_php_config(config_before, {
            "production_decision_packet_sha256": php_quote(decision_hash),
            "enable_write_tools": "true", "runtime_write_blocked": "false",
            "execution_allowed": "true", "production_write_approved": "true",
            "allowed_write_organization_ids": php_quote(org_id),
            "allowed_write_actions": php_quote(ACTION),
        })
        publish(sftp, CONFIG_PATH, open_config, config_mode)

        # The kill switch is intentionally the final gate opened.
        publish(sftp, KILL_PATH, json_bytes({
            "globalBlocked": False, "blockedActions": [],
            "reason": "authorized first production invoice draft; one-use window",
            "updatedAtUtc": iso_utc(),
        }))

        if TOOL not in tool_names(token):
            raise Stop("execution_tool_not_visible_after_gate_open")
        health = successful_tool_data(mcp_tool(token, 11, "conta_health_check", {"checkConta": False}))
        policy = health.get("config", {}).get("effective_write_policy", {}) if isinstance(health, dict) else {}
        if not isinstance(policy, dict) or policy.get("effective_execution_enabled") is not True:
            raise Stop("effective_execution_gate_not_open")
        print("RELEASE_APPROVED=true")
        print("FIRST_PRODUCTION_MUTATION_AUTHORIZED=true")
        print("EXECUTION_TOOL_VISIBLE=true")
        print("EFFECTIVE_EXECUTION_GATE_OPEN=true")

        # Exactly one call. No retry occurs even if this call times out or returns
        # an indeterminate result.
        execution_attempted = True
        try:
            execution_result = mcp_tool(token, 12, TOOL, {
                "organizationId": org_id, "invoice": payload, "approval": approval,
            })
            verified, raw_draft_id, mismatch_count = extract_execution_result(execution_result)
            if raw_draft_id:
                draft_id_hash = sha256_bytes(raw_draft_id.encode())
            if verified:
                provider_outcome = "CREATED_AND_READBACK_VERIFIED"
                readback_verified = True
            else:
                provider_outcome = "EXECUTION_RETURNED_UNVERIFIED"
        except Stop:
            provider_outcome = "AMBIGUOUS_EXECUTION_OUTCOME"

        # GET-only reconciliation is mandatory after the single execution call.
        reconciliation_count, _ = safe_draft_list(api_key, org_id)
        if reconciliation_count not in (0, 1):
            provider_outcome = "RECONCILIATION_UNEXPECTED_DRAFT_COUNT"
        print(f"RECONCILIATION_DRAFT_COUNT={reconciliation_count}")
        print("RECONCILIATION_GET_PERFORMED=true")

    finally:
        close_errors: list[str] = []
        try:
            publish(sftp, KILL_PATH, json_bytes({
                "globalBlocked": True, "blockedActions": [ACTION],
                "reason": "first production execution window closed", "updatedAtUtc": iso_utc(),
            }))
        except Exception:
            close_errors.append("kill_switch_reclose_failed")
        try:
            if config_before is not None:
                publish(sftp, CONFIG_PATH, config_before, config_mode)
        except Exception:
            close_errors.append("config_restore_failed")
        for path in (AUTH_PATH, MANIFEST_PATH):
            try:
                if remote_exists(sftp, path):
                    sftp.remove(path)
            except Exception:
                close_errors.append("temporary_control_cleanup_failed")
        try:
            sftp.close()
            transport.close()
        except Exception:
            pass
        if close_errors:
            print("KILL_SWITCH_RE_CLOSED=false")
            print("EXECUTION_GATE_RE_CLOSED=false")
            raise Stop(",".join(close_errors))

    health_status, final_health = http_json("https://mcp.atlas-ai.no/health")
    final_config = final_health.get("config", {}) if health_status == 200 and isinstance(final_health, dict) else {}
    expected_closed = {
        "write_tools_enabled": False, "runtime_write_blocked": True,
        "execution_allowed": False, "production_write_approved": False,
        "allowed_write_action_count": 0, "allowed_write_organization_count": 0,
    }
    if health_status != 200 or any(final_config.get(key) != value for key, value in expected_closed.items()):
        raise Stop("post_attempt_fail_closed_health_verification_failed")

    provider_mutation_count = 1 if reconciliation_count == 1 else 0
    print(f"ACTION={ACTION}")
    print(f"DEPLOYED_IMPLEMENTATION_COMMIT={SOURCE_COMMIT}")
    print(f"PRODUCTION_ORGANIZATION_REFERENCE_SHA256={ORG_SHA256}")
    print("MAX_PROVIDER_MUTATIONS=1")
    print("AUTOMATIC_RETRY_ALLOWED=false")
    print(f"EXECUTION_CALL_COUNT={1 if execution_attempted else 0}")
    print(f"PROVIDER_MUTATION_COUNT={provider_mutation_count}")
    print(f"PROVIDER_OUTCOME={provider_outcome}")
    print(f"READBACK_PERFORMED={'true' if execution_attempted else 'false'}")
    print(f"READBACK_VERIFIED={'true' if readback_verified else 'false'}")
    if mismatch_count is not None:
        print(f"READBACK_MISMATCH_COUNT={mismatch_count}")
    if draft_id_hash is not None:
        print(f"INVOICE_DRAFT_ID_SHA256={draft_id_hash}")
    print("KILL_SWITCH_RE_CLOSED=true")
    print("EXECUTION_GATE_RE_CLOSED=true")
    print("SECRET_VALUE_PRINTED=false")
    print("RAW_ORGANIZATION_ID_PRINTED=false")
    print("RAW_CUSTOMER_ID_PRINTED=false")
    print("FULL_PAYLOAD_PRINTED=false")
    print("FINAL_FAIL_CLOSED_HEALTH_VERIFIED=true")

    if provider_outcome != "CREATED_AND_READBACK_VERIFIED":
        raise Stop("first_production_execution_not_verified")
    if reconciliation_count != 1:
        raise Stop("first_production_reconciliation_count_not_one")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-packet-sha256", required=True)
    parser.add_argument("--decision-packet-expires-at", required=True)
    parser.add_argument("--authorization", required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(f"::error title=Conta first-production execution stopped::{exc}")
        raise SystemExit(1)
    except Exception:
        print("::error title=Conta first-production execution stopped::unexpected_error")
        raise SystemExit(1)
