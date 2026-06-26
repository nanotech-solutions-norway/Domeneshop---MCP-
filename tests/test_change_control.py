from domeneshop_mcp.audit_model import build_audit_event
from domeneshop_mcp.change_control import ChangeGateConfig, ChangeRequest, evaluate_change_preflight
from domeneshop_mcp.tools_change_control import control_evaluate_change_preflight, control_build_audit_event


def test_default_gate_blocks_execution():
    request = ChangeRequest(
        action="sftp_upload_file",
        target="/www/index.html",
        risk_level="medium",
        operator="operator",
        backup_evidence_reference="phase6.json",
        preflight_reference="phase5.json",
    )
    decision = evaluate_change_preflight(request, ChangeGateConfig())
    assert decision.preflight_passed is False
    assert decision.execute_now is False
    assert "change_tools_disabled" in decision.reason_codes
    assert "approval_reference_missing" in decision.reason_codes


def test_even_complete_request_has_no_live_action_registered():
    request = ChangeRequest(
        action="sftp_upload_file",
        target="/www/index.html",
        risk_level="medium",
        operator="operator",
        approval_reference="APPROVED-1",
        backup_evidence_reference="phase6.json",
        preflight_reference="phase5.json",
    )
    config = ChangeGateConfig(change_tools_enabled=True, dry_run_default=False, require_operator_approval=True)
    decision = evaluate_change_preflight(request, config)
    assert decision.execute_now is False
    assert decision.live_action_registered is False
    assert "live_action_not_registered" in decision.reason_codes


def test_audit_event_has_hash():
    event = build_audit_event("preflight", "operator", "/www/index.html", {"execute_now": False})
    assert event.event_hash
    assert len(event.event_hash) == 64


def test_control_preflight_tool_envelope():
    result = control_evaluate_change_preflight(
        {
            "action": "sftp_upload_file",
            "target": "/www/index.html",
            "risk_level": "medium",
            "operator": "operator",
            "backup_evidence_reference": "phase6.json",
            "preflight_reference": "phase5.json",
        },
        {"change_tools_enabled": False},
    )
    assert result["success"] is True
    assert result["data"]["summary"]["execute_now"] is False


def test_control_audit_event_tool_envelope():
    result = control_build_audit_event("preflight", "operator", "/www/index.html", {"execute_now": False})
    assert result["success"] is True
    assert result["data"]["event_hash"]
