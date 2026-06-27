"""Final release gate validation for Phase 12."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_PHASE_DOCS = (
    "docs/PHASE2_READ_CONNECTOR_IMPLEMENTATION_1045_26062026.md",
    "docs/PHASE3_SFTP_READ_CONNECTOR_IMPLEMENTATION_1125_26062026.md",
    "docs/PHASE3B_4_SERVER_AND_HEALTH_IMPLEMENTATION_1145_26062026.md",
    "docs/PHASE5_DRY_RUN_DEPLOYMENT_LANE_1215_26062026.md",
    "docs/PHASE6_BACKUP_RECOVERY_PLANNING_2340_26062026.md",
    "docs/PHASE7_APPROVAL_GATED_CHANGE_CONTROL_0010_27062026.md",
    "docs/PHASE8_MCP_PACKAGING_DEPLOYMENT_SCAFFOLD_0035_27062026.md",
    "docs/PHASE9_PRODUCTION_DEPLOYMENT_SCAFFOLD_0105_27062026.md",
    "docs/PHASE10_OPERATIONAL_RUNBOOK_INCIDENTS_0135_27062026.md",
    "docs/PHASE11_ESTATE_INTEGRATION_0210_27062026.md",
    "docs/PHASE12_FINAL_VALIDATION_RELEASE_GATE_0245_27062026.md",
)

REQUIRED_CONTROL_DOCS = (
    "docs/SECURITY_AND_WRITE_CONTROL.md",
    "docs/VALIDATION_CHECKLIST.md",
    "docs/TOOL_CATALOG.md",
    "docs/OPERATIONAL_RUNBOOK.md",
    "docs/INCIDENT_RESPONSE_PROCEDURES.md",
    "docs/RELEASE_APPROVAL_CHECKLIST.md",
    "docs/FINAL_RELEASE_GATE_CHECKLIST.md",
    "docs/ESTATE_SERVICE_INVENTORY.md",
    "docs/DOMENESHOP_MCP_FINAL_TRANSFER_REPORT_0245_27062026.md",
)

REQUIRED_SCRIPTS = (
    "scripts/validate_repository_structure.py",
    "scripts/dry_run_plan.py",
    "scripts/recovery_plan.py",
    "scripts/change_preflight.py",
    "scripts/readiness_preflight.py",
    "scripts/runtime_deployment_validate.py",
    "scripts/operations_validate.py",
    "scripts/estate_validate.py",
    "scripts/final_release_gate.py",
)

REQUIRED_ENV_MARKERS = (
    "WRITE_TOOLS_ENABLED=false",
    "DRY_RUN_DEFAULT=true",
    "REQUIRE_OPERATOR_APPROVAL=true",
    "REQUIRE_BACKUP_EVIDENCE=true",
    "REQUIRE_PREFLIGHT_REPORT=true",
)

DISALLOWED_SERVER_MARKERS = (
    "create_dns_record",
    "update_dns_record",
    "delete_dns_record",
    "upload_file",
    "upload_folder",
    "restore_backup",
    "shell_command",
)


@dataclass(frozen=True)
class ReleaseGateValidation:
    mode: str
    release_decision: str
    passed: bool
    checks: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        failed = [item for item in self.checks if not item["passed"]]
        return {
            "mode": self.mode,
            "release_decision": self.release_decision,
            "passed": self.passed,
            "check_count": len(self.checks),
            "failed_count": len(failed),
        }


def validate_release_gate(repo_root: str | Path = ".") -> ReleaseGateValidation:
    root = Path(repo_root)
    checks: list[dict[str, Any]] = []

    for rel in REQUIRED_PHASE_DOCS:
        checks.append({"name": f"phase_doc_exists:{rel}", "passed": (root / rel).exists()})
    for rel in REQUIRED_CONTROL_DOCS:
        checks.append({"name": f"control_doc_exists:{rel}", "passed": (root / rel).exists()})
    for rel in REQUIRED_SCRIPTS:
        checks.append({"name": f"script_exists:{rel}", "passed": (root / rel).exists()})

    env_text = _read(root / "config" / "domeneshop-mcp.env.example")
    for marker in REQUIRED_ENV_MARKERS:
        checks.append({"name": f"env_marker:{marker}", "passed": marker in env_text})

    server_text = _read(root / "src" / "domeneshop_mcp" / "server.py")
    for marker in DISALLOWED_SERVER_MARKERS:
        checks.append({"name": f"server_marker_absent:{marker}", "passed": marker not in server_text})

    checklist_text = _read(root / "docs" / "RELEASE_APPROVAL_CHECKLIST.md")
    final_checklist_text = _read(root / "docs" / "FINAL_RELEASE_GATE_CHECKLIST.md")
    checks.append({"name": "release_checklist_read_only_decision", "passed": "APPROVE_READ_ONLY_RUNTIME" in checklist_text})
    checks.append({"name": "release_checklist_holds_live_change", "passed": "REJECT_LIVE_CHANGE_ACTIVATION" in checklist_text})
    checks.append({"name": "final_checklist_read_only_decision", "passed": "APPROVE_READ_ONLY_RUNTIME" in final_checklist_text})

    passed = all(item["passed"] for item in checks)
    return ReleaseGateValidation(
        mode="phase12_final_release_gate",
        release_decision="APPROVE_READ_ONLY_RUNTIME" if passed else "HOLD_FOR_FIX",
        passed=passed,
        checks=checks,
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
