from __future__ import annotations

import pytest

from domeneshop_mcp.http_forward_create_dry_run import (
    DOMAIN_NAME,
    EXPECTED_PAYLOAD_SHA256,
    EXPECTED_TARGET_SHA256,
    FORWARD_HOST,
    RELEASE_ID,
    build_create_dry_run_evidence,
    candidate_payload,
)
from domeneshop_mcp.controlled_write import canonical_payload_sha256


def test_candidate_payload_matches_accepted_preflight_hash():
    assert candidate_payload() == {
        "host": "mcp-forward-validation",
        "frame": False,
        "url": "https://atlas-mcp-sandbox.no/",
    }
    assert canonical_payload_sha256(candidate_payload()) == EXPECTED_PAYLOAD_SHA256


def test_dry_run_is_exact_bound_and_non_mutating():
    evidence = build_create_dry_run_evidence(write_tools_enabled=False, dry_run_default=True)
    assert evidence["release_id"] == RELEASE_ID
    assert evidence["target_domain"] == DOMAIN_NAME
    assert evidence["target_host"] == FORWARD_HOST
    assert evidence["target_sha256"] == EXPECTED_TARGET_SHA256
    assert evidence["payload_sha256"] == EXPECTED_PAYLOAD_SHA256
    assert evidence["status"] == "deterministic_create_dry_run_ok"
    assert evidence["provider_mutation_performed"] is False
    assert evidence["http_forward_create_authorized"] is False
    assert evidence["http_forward_update_authorized"] is False
    assert evidence["http_forward_delete_authorized"] is False
    assert evidence["broader_overwrite_authorized"] is False
    assert evidence["write_tools_enabled"] is False
    assert evidence["dry_run_default"] is True


@pytest.mark.parametrize(
    ("write_tools_enabled", "dry_run_default"),
    [(True, True), (False, False), (True, False)],
)
def test_dry_run_fails_closed_for_unsafe_runtime(write_tools_enabled: bool, dry_run_default: bool):
    with pytest.raises(RuntimeError, match="unsafe_runtime_configuration"):
        build_create_dry_run_evidence(
            write_tools_enabled=write_tools_enabled,
            dry_run_default=dry_run_default,
        )
