"""Approval-gated change control scaffold for Phase 7.

This module evaluates whether a future change request satisfies governance
controls. It does not perform provider mutations or file transfers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class ChangeGateConfig:
    change_tools_enabled: bool = False
    dry_run_default: bool = True
    require_operator_approval: bool = True
    require_backup_evidence: bool = True
    require_preflight_report: bool = True
    live_action_registered: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "ChangeGateConfig":
        source = os.environ if env is None else env
        return cls(
            change_tools_enabled=_as_bool(source.get("WRITE_TOOLS_ENABLED", "false")),
            dry_run_default=_as_bool(source.get("DRY_RUN_DEFAULT", "true")),
            require_operator_approval=_as_bool(source.get("REQUIRE_OPERATOR_APPROVAL", "true")),
            require_backup_evidence=_as_bool(source.get("REQUIRE_BACKUP_EVIDENCE", "true")),
            require_preflight_report=_as_bool(source.get("REQUIRE_PREFLIGHT_REPORT", "true")),
            live_action_registered=False,
        )


@dataclass(frozen=True)
class ChangeRequest:
    action: str
    target: str
    risk_level: str
    operator: str | None = None
    approval_reference: str | None = None
    backup_evidence_reference: str | None = None
    preflight_reference: str | None = None
    requested_utc: str | None = None


@dataclass(frozen=True)
class ChangePreflightDecision:
    mode: str
    preflight_passed: bool
    execute_now: bool
    live_action_registered: bool
    reason_codes: list[str]
    required_controls: list[str]
    request: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "preflight_passed": self.preflight_passed,
            "execute_now": self.execute_now,
            "live_action_registered": self.live_action_registered,
            "reason_count": len(self.reason_codes),
            "required_control_count": len(self.required_controls),
        }


def evaluate_change_preflight(request: ChangeRequest, config: ChangeGateConfig) -> ChangePreflightDecision:
    reasons: list[str] = []
    controls: list[str] = []

    if not request.action.strip():
        reasons.append("action_missing")
    if not request.target.strip():
        reasons.append("target_missing")
    if request.risk_level not in {"low", "medium", "high", "critical"}:
        reasons.append("risk_level_invalid")

    if not config.change_tools_enabled:
        reasons.append("change_tools_disabled")
        controls.append("set_WRITE_TOOLS_ENABLED_true_only_after_release_gate")

    if config.dry_run_default:
        controls.append("dry_run_default_enabled")

    if config.require_operator_approval and not request.approval_reference:
        reasons.append("approval_reference_missing")
        controls.append("operator_approval_required")

    if config.require_backup_evidence and request.risk_level in {"medium", "high", "critical"} and not request.backup_evidence_reference:
        reasons.append("backup_evidence_missing")
        controls.append("backup_evidence_required")

    if config.require_preflight_report and not request.preflight_reference:
        reasons.append("preflight_reference_missing")
        controls.append("preflight_report_required")

    if request.risk_level == "critical":
        reasons.append("critical_risk_manual_release_required")
        controls.append("manual_release_review_required")

    if not config.live_action_registered:
        reasons.append("live_action_not_registered")
        controls.append("implementation_scaffold_only")

    passed = len(reasons) == 0
    return ChangePreflightDecision(
        mode="change_control_preflight",
        preflight_passed=passed,
        execute_now=False,
        live_action_registered=config.live_action_registered,
        reason_codes=reasons,
        required_controls=sorted(set(controls)),
        request={
            "action": request.action,
            "target": request.target,
            "risk_level": request.risk_level,
            "operator": request.operator,
            "approval_reference": request.approval_reference,
            "backup_evidence_reference": request.backup_evidence_reference,
            "preflight_reference": request.preflight_reference,
            "requested_utc": request.requested_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
    )


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
