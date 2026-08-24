#!/usr/bin/env python3
"""GET-only reconciliation for the authorized first Conta production draft."""
from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any

import certifi

from conta_invoice_draft_duplicate_guard import (
    DuplicateGuardError,
    detail_contains_line_description,
    extract_draft_entries,
    extract_draft_identifier,
)


PROVIDER_BASE = "https://api.gateway.conta.no"
ORG_SHA256 = "9ee050155b0c35066a2ea426c72a65e5cdd2806f18a3cf9829fb132bd66634ab"
LINE_DESCRIPTION = "Conta MCP First Production Validation"
AUTHORIZATION = "RECONCILE_CONTA_FIRST_PRODUCTION_A6B94702"
EXPECTED_TOTAL_DRAFT_COUNT = 2
MAX_RESPONSE = 524_288


class Stop(RuntimeError):
    pass


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def http_get_json(url: str, api_key: str) -> tuple[int, Any]:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "apiKey": api_key})
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            raw = response.read(MAX_RESPONSE + 1)
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE + 1)
        status = exc.code
    except (urllib.error.URLError, TimeoutError):
        raise Stop("get_only_network_outcome_ambiguous") from None
    if len(raw) > MAX_RESPONSE:
        raise Stop("response_too_large")
    try:
        return status, json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, None


def count_drafts(body: Any) -> int:
    if isinstance(body, list):
        return len(body)
    if not isinstance(body, dict):
        raise Stop("invoice_draft_list_unrecognized")
    for key in ("hitCount", "totalCount", "totalElements", "total", "count"):
        value = body.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
    for key in ("hits", "items", "content", "data", "results", "invoiceDrafts"):
        if isinstance(body.get(key), list):
            return len(body[key])
    raise Stop("invoice_draft_list_unrecognized")


def controlled_draft(detail: Any) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("invoiceDraftLines"), list) or isinstance(node.get("lines"), list):
                candidates.append(node)
            else:
                for value in node.values():
                    collect(value)
        elif isinstance(node, list):
            for child in node:
                collect(child)

    collect(detail)
    if len(candidates) != 1:
        raise Stop(f"controlled_draft_candidate_count_{len(candidates)}")
    return candidates[0]


def decimal_equal(value: Any, expected: str) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return Decimal(str(value)) == Decimal(expected)
    except (InvalidOperation, ValueError):
        return False


def assert_controlled_fields(draft: dict[str, Any], customer_ref: str, vat_code: str) -> None:
    lines = draft.get("invoiceDraftLines") if isinstance(draft.get("invoiceDraftLines"), list) else draft.get("lines")
    if not isinstance(lines, list) or len(lines) != 1 or not isinstance(lines[0], dict):
        raise Stop("readback_line_shape_mismatch")
    line = lines[0]
    expected_scalars = {
        "registrationSource": "CONTA",
        "type": "NORMAL",
        "invoiceLanguage": "NO",
        "invoiceCurrency": "NOK",
    }
    for key, expected in expected_scalars.items():
        if str(draft.get(key, "")) != expected:
            raise Stop(f"readback_{key}_mismatch")
    if str(draft.get("customerId", "")) != customer_ref:
        raise Stop("readback_customer_mismatch")
    if str(line.get("description", "")) != LINE_DESCRIPTION:
        raise Stop("readback_description_mismatch")
    if str(line.get("vatCode", "")) != vat_code:
        raise Stop("readback_vat_code_mismatch")
    numeric = {"price": "1", "quantity": "1", "discount": "0", "lineNo": "1"}
    for key, expected in numeric.items():
        if not decimal_equal(line.get(key), expected):
            raise Stop(f"readback_{key}_mismatch")


def main() -> int:
    if os.environ.get("GITHUB_REF_NAME") != "main":
        raise Stop("must_run_from_main")
    if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
        raise Stop("workflow_rerun_not_authorized")
    if os.environ.get("RECONCILE_AUTHORIZATION") != AUTHORIZATION:
        raise Stop("authorization_mismatch")
    api_key = os.environ.get("CONTA_PROD_API_KEY", "").strip()
    org_id = os.environ.get("CONTA_PROD_ORG_ID", "").strip()
    customer_ref = os.environ.get("CONTA_PROD_CUSTOMER_REFERENCE", "").strip()
    vat_code = os.environ.get("CONTA_PROD_VAT_CODE", "").strip()
    if not all((api_key, org_id, customer_ref, vat_code)):
        raise Stop("protected_reconciliation_inputs_missing")
    if sha256_text(org_id) != ORG_SHA256:
        raise Stop("production_organization_hash_mismatch")
    if not customer_ref.isdigit() or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", vat_code):
        raise Stop("protected_reference_format_invalid")

    encoded_org = urllib.parse.quote(org_id, safe="")
    list_url = f"{PROVIDER_BASE}/invoice/organizations/{encoded_org}/invoice-drafts?hits=100&page=0&sort=id"
    status, body = http_get_json(list_url, api_key)
    if status != 200:
        raise Stop(f"invoice_draft_list_get_failed_http_{status}")
    count = count_drafts(body)
    if count != EXPECTED_TOTAL_DRAFT_COUNT:
        raise Stop(f"invoice_draft_reconciliation_count_{count}")
    try:
        entries = extract_draft_entries(body, count)
    except DuplicateGuardError as exc:
        raise Stop(f"invoice_draft_reconciliation_ambiguous:{exc}") from None

    matches: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        try:
            draft_id = extract_draft_identifier(entry)
        except DuplicateGuardError as exc:
            raise Stop(f"invoice_draft_reconciliation_ambiguous:{exc}") from None
        detail_url = f"{PROVIDER_BASE}/invoice/organizations/{encoded_org}/invoice-drafts/{urllib.parse.quote(draft_id, safe='')}"
        detail_status, detail = http_get_json(detail_url, api_key)
        if detail_status != 200 or not isinstance(detail, (dict, list)):
            raise Stop(f"invoice_draft_detail_get_failed_http_{detail_status}")
        try:
            is_match = detail_contains_line_description(detail, LINE_DESCRIPTION)
        except DuplicateGuardError as exc:
            raise Stop(f"invoice_draft_reconciliation_ambiguous:{exc}") from None
        if is_match:
            matches.append((draft_id, controlled_draft(detail)))

    if len(matches) != 1:
        raise Stop(f"matching_validation_draft_count_{len(matches)}")
    draft_id, draft = matches[0]
    assert_controlled_fields(draft, customer_ref, vat_code)
    safe_projection = {
        "registrationSource": "CONTA",
        "type": "NORMAL",
        "invoiceLanguage": "NO",
        "invoiceCurrency": "NOK",
        "customerIdSha256": sha256_text(customer_ref),
        "lineCount": 1,
        "description": LINE_DESCRIPTION,
        "price": 1,
        "quantity": 1,
        "discount": 0,
        "vatCode": vat_code,
        "lineNo": 1,
    }
    projection_hash = hashlib.sha256(
        json.dumps(safe_projection, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(f"RECONCILIATION_DRAFT_COUNT={count}")
    print("MATCHING_VALIDATION_DRAFT_COUNT=1")
    print("GET_ONLY_RECONCILIATION_PERFORMED=true")
    print("READBACK_VERIFIED=true")
    print(f"INVOICE_DRAFT_ID_SHA256={sha256_text(draft_id)}")
    print(f"CONTROLLED_PROJECTION_SHA256={projection_hash}")
    print("PROVIDER_MUTATION_PERFORMED=false")
    print("RAW_DRAFT_ID_PRINTED=false")
    print("RAW_ORGANIZATION_ID_PRINTED=false")
    print("RAW_CUSTOMER_ID_PRINTED=false")
    print("FULL_PAYLOAD_PRINTED=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(f"::error title=Conta first-production GET-only reconciliation stopped::{exc}")
        raise SystemExit(1)
    except Exception:
        print("::error title=Conta first-production GET-only reconciliation stopped::unexpected_error")
        raise SystemExit(1)
