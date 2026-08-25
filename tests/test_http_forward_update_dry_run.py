from __future__ import annotations

import pytest

from domeneshop_mcp.controlled_write import canonical_payload_sha256
from domeneshop_mcp.http_forward_update_dry_run import (
    CREATE_URL,
    EXPECTED_TARGET_SHA256,
    EXPECTED_UPDATE_PAYLOAD_SHA256,
    FORWARD_HOST,
    REQUIRED_BEFORE_PAYLOAD_SHA256,
    UPDATE_URL,
    accepted_create_payload,
    build_update_dry_run_evidence,
    candidate_update_payload,
)


def test_update_payload_is_exactly_bound_and_keeps_host():
    before = accepted_create_payload()
    update = candidate_update_payload()

    assert before == {"host": FORWARD_HOST, "frame": False, "url": CREATE_URL}
    assert update == {"host": FORWARD_HOST, "frame": False, "url": UPDATE_URL}
    assert before["host"] == update["host"]
    assert before["url"] != update["url"]
    assert canonical_payload_sha256(before) == REQUIRED_BEFORE_PAYLOAD_SHA256
    assert canonical_payload_sha256(update) == EXPECTED_UPDATE_PAYLOAD_SHA256


def test_update_dry_run_reports_no_provider_mutation_or_authorization():
    evidence = build_update_dry_run_evidence(write_tools_enabled=False, dry_run_default=True)

    assert evidence["success"] is True
    assert evidence["status"] == "deterministic_update_dry_run_ok"
    assert evidence["target_sha256"] == EXPECTED_TARGET_SHA256
    assert evidence["required_before_payload_sha256"] == REQUIRED_BEFORE_PAYLOAD_SHA256
    assert evidence["update_payload_sha256"] == EXPECTED_UPDATE_PAYLOAD_SHA256
    assert evidence["host_change_performed"] is False
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
def test_update_dry_run_fails_closed_for_unsafe_runtime(write_tools_enabled, dry_run_default):
    with pytest.raises(RuntimeError, match="unsafe_runtime_configuration"):
        build_update_dry_run_evidence(
            write_tools_enabled=write_tools_enabled,
            dry_run_default=dry_run_default,
        )
