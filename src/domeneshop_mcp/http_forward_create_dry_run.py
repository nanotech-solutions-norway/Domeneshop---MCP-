"""Deterministic, non-mutating binding for the D-R4B HTTP-forward CREATE candidate."""

from __future__ import annotations

from typing import Any

from .controlled_write import canonical_payload_sha256

RELEASE_ID = "D-R4B-HTTP-FORWARD-CREATE-20260825-001"
PREFLIGHT_RELEASE_ID = "D-R4B-HTTP-FORWARD-PREFLIGHT-20260825"
DOMAIN_NAME = "atlas-mcp-sandbox.no"
FORWARD_HOST = "mcp-forward-validation"
FORWARD_URL = "https://atlas-mcp-sandbox.no/"
EXPECTED_TARGET_SHA256 = "23cc343ce4a03fb910e58a371604ff85a7c49c16c062e15ba8238ec662fea831"
EXPECTED_PAYLOAD_SHA256 = "2fbfc99c2747d313ecdd0477aab0c9c67f8f9e66c19c7fa90920bb20ce57a926"


def candidate_payload() -> dict[str, Any]:
    return {"host": FORWARD_HOST, "frame": False, "url": FORWARD_URL}


def build_create_dry_run_evidence(*, write_tools_enabled: bool, dry_run_default: bool) -> dict[str, Any]:
    """Return exact-bound evidence without making any provider request."""

    if write_tools_enabled or not dry_run_default:
        raise RuntimeError("unsafe_runtime_configuration")

    payload_sha256 = canonical_payload_sha256(candidate_payload())
    if payload_sha256 != EXPECTED_PAYLOAD_SHA256:
        raise RuntimeError("payload_binding_mismatch")

    return {
        "evidence_type": "http_forward_create_dry_run",
        "release_id": RELEASE_ID,
        "preflight_release_id": PREFLIGHT_RELEASE_ID,
        "success": True,
        "status": "deterministic_create_dry_run_ok",
        "target_sha256": EXPECTED_TARGET_SHA256,
        "payload_sha256": payload_sha256,
        "target_domain": DOMAIN_NAME,
        "target_host": FORWARD_HOST,
        "provider_mutation_performed": False,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": write_tools_enabled,
        "dry_run_default": dry_run_default,
        "exact_binding_confirmed": True,
    }
