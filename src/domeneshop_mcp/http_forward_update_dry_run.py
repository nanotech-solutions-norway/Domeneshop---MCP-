"""Deterministic, non-mutating binding for the D-R4B HTTP-forward UPDATE candidate."""

from __future__ import annotations

from typing import Any

from .controlled_write import canonical_payload_sha256

RELEASE_ID = "D-R4B-HTTP-FORWARD-UPDATE-20260826-001"
CREATE_RELEASE_ID = "D-R4B-HTTP-FORWARD-CREATE-20260825-001"
DOMAIN_NAME = "atlas-mcp-sandbox.no"
FORWARD_HOST = "mcp-forward-validation"
CREATE_URL = "https://atlas-mcp-sandbox.no/"
UPDATE_URL = "https://atlas-mcp-sandbox.no/?mcp-forward-validation=updated"
EXPECTED_TARGET_SHA256 = "23cc343ce4a03fb910e58a371604ff85a7c49c16c062e15ba8238ec662fea831"
REQUIRED_BEFORE_PAYLOAD_SHA256 = "2fbfc99c2747d313ecdd0477aab0c9c67f8f9e66c19c7fa90920bb20ce57a926"
EXPECTED_UPDATE_PAYLOAD_SHA256 = "961fea82b0837c992c66f11aaacadf9642782b0cd263ce374d4d07b4d18c8ebb"


def accepted_create_payload() -> dict[str, Any]:
    return {"host": FORWARD_HOST, "frame": False, "url": CREATE_URL}


def candidate_update_payload() -> dict[str, Any]:
    return {"host": FORWARD_HOST, "frame": False, "url": UPDATE_URL}


def build_update_dry_run_evidence(*, write_tools_enabled: bool, dry_run_default: bool) -> dict[str, Any]:
    """Return exact-bound UPDATE evidence without making any provider request."""

    if write_tools_enabled or not dry_run_default:
        raise RuntimeError("unsafe_runtime_configuration")

    before = accepted_create_payload()
    update = candidate_update_payload()
    before_hash = canonical_payload_sha256(before)
    update_hash = canonical_payload_sha256(update)

    if before_hash != REQUIRED_BEFORE_PAYLOAD_SHA256:
        raise RuntimeError("required_before_binding_mismatch")
    if update_hash != EXPECTED_UPDATE_PAYLOAD_SHA256:
        raise RuntimeError("update_payload_binding_mismatch")
    if before["host"] != update["host"] or update["host"] != FORWARD_HOST:
        raise RuntimeError("host_change_forbidden")
    if before["url"] == update["url"]:
        raise RuntimeError("update_must_change_url")
    if before["frame"] is not False or update["frame"] is not False:
        raise RuntimeError("frame_change_forbidden")

    return {
        "evidence_type": "http_forward_update_dry_run",
        "release_id": RELEASE_ID,
        "required_before_release_id": CREATE_RELEASE_ID,
        "success": True,
        "status": "deterministic_update_dry_run_ok",
        "target_sha256": EXPECTED_TARGET_SHA256,
        "required_before_payload_sha256": before_hash,
        "update_payload_sha256": update_hash,
        "target_domain": DOMAIN_NAME,
        "target_host": FORWARD_HOST,
        "host_change_performed": False,
        "provider_mutation_performed": False,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": write_tools_enabled,
        "dry_run_default": dry_run_default,
        "exact_binding_confirmed": True,
    }
