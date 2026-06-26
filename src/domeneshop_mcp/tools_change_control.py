"""Tool handlers for Phase 7 change-control preflight."""

from __future__ import annotations

from .audit_model import build_audit_event
from .change_control import ChangeGateConfig, ChangeRequest, evaluate_change_preflight
from .envelope import ToolEnvelope, error, ok


def control_evaluate_change_preflight(request_payload: dict, config_payload: dict | None = None) -> ToolEnvelope:
    try:
        request = ChangeRequest(
            action=str(request_payload.get("action", "")),
            target=str(request_payload.get("target", "")),
            risk_level=str(request_payload.get("risk_level", "")),
            operator=request_payload.get("operator"),
            approval_reference=request_payload.get("approval_reference"),
            backup_evidence_reference=request_payload.get("backup_evidence_reference"),
            preflight_reference=request_payload.get("preflight_reference"),
            requested_utc=request_payload.get("requested_utc"),
        )
        if config_payload:
            config = ChangeGateConfig(
                change_tools_enabled=bool(config_payload.get("change_tools_enabled", False)),
                dry_run_default=bool(config_payload.get("dry_run_default", True)),
                require_operator_approval=bool(config_payload.get("require_operator_approval", True)),
                require_backup_evidence=bool(config_payload.get("require_backup_evidence", True)),
                require_preflight_report=bool(config_payload.get("require_preflight_report", True)),
                live_action_registered=False,
            )
        else:
            config = ChangeGateConfig.from_env()
        decision = evaluate_change_preflight(request, config)
        return ok({"summary": decision.summary(), "decision": decision.__dict__}, mode="change_control_preflight")
    except Exception:
        return error("validation_failed", "Change preflight evaluation failed.", mode="change_control_preflight")


def control_build_audit_event(event_type: str, actor: str, target: str, decision_summary: dict) -> ToolEnvelope:
    try:
        event = build_audit_event(event_type, actor, target, decision_summary)
        return ok(event.__dict__, mode="audit_event_model")
    except Exception:
        return error("validation_failed", "Audit event construction failed.", mode="audit_event_model")
