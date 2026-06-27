"""Operations documentation validation for Phase 10."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_OPERATION_DOCS = (
    "docs/OPERATIONAL_RUNBOOK.md",
    "docs/INCIDENT_RESPONSE_PROCEDURES.md",
    "docs/RELEASE_APPROVAL_CHECKLIST.md",
    "docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md",
)

REQUIRED_RUNBOOK_MARKERS = (
    "Daily operator checklist",
    "Startup procedure",
    "Shutdown procedure",
    "Runtime value rotation procedure",
    "Read-only smoke checks",
)

REQUIRED_INCIDENT_MARKERS = (
    "Incident classes",
    "Immediate containment",
    "Evidence package",
    "Rollback decision tree",
    "Closure requirements",
)

REQUIRED_RELEASE_MARKERS = (
    "Mandatory evidence",
    "Runtime safety checks",
    "Tool registration checks",
    "Release decision",
)


@dataclass(frozen=True)
class OperationsValidation:
    mode: str
    passed: bool
    checks: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        failed = [item for item in self.checks if not item["passed"]]
        return {
            "mode": self.mode,
            "passed": self.passed,
            "check_count": len(self.checks),
            "failed_count": len(failed),
        }


def validate_operations_docs(repo_root: str | Path = ".") -> OperationsValidation:
    root = Path(repo_root)
    checks: list[dict[str, Any]] = []

    for rel in REQUIRED_OPERATION_DOCS:
        checks.append({"name": f"file_exists:{rel}", "passed": (root / rel).exists()})

    runbook_text = _read(root / "docs" / "OPERATIONAL_RUNBOOK.md")
    for marker in REQUIRED_RUNBOOK_MARKERS:
        checks.append({"name": f"runbook_marker:{marker}", "passed": marker in runbook_text})

    incident_text = _read(root / "docs" / "INCIDENT_RESPONSE_PROCEDURES.md")
    for marker in REQUIRED_INCIDENT_MARKERS:
        checks.append({"name": f"incident_marker:{marker}", "passed": marker in incident_text})

    release_text = _read(root / "docs" / "RELEASE_APPROVAL_CHECKLIST.md")
    for marker in REQUIRED_RELEASE_MARKERS:
        checks.append({"name": f"release_marker:{marker}", "passed": marker in release_text})

    checks.append({"name": "release_holds_live_activation", "passed": "REJECT_LIVE_CHANGE_ACTIVATION" in release_text})
    checks.append({"name": "runbook_confirms_read_plan_only", "passed": "READ_AND_PLAN_ONLY" in runbook_text})

    return OperationsValidation(
        mode="phase10_operations_validation",
        passed=all(item["passed"] for item in checks),
        checks=checks,
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
