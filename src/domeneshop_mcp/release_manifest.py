"""Read-only release manifest validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_REPORTS = {
    "phase5-dry-run-report.json",
    "phase6-backup-evidence-report.json",
    "phase6-restore-preview-report.json",
    "phase7-change-preflight-report.json",
    "phase8-readiness-preflight-report.json",
    "phase9-runtime-deployment-validation-report.json",
    "phase10-operations-validation-report.json",
    "phase11-estate-validation-report.json",
    "phase12-final-release-gate-report.json",
}


@dataclass(frozen=True)
class ReleaseManifestValidation:
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


def validate_release_manifest(path: str | Path = "config/read-only-release-manifest.example.json") -> ReleaseManifestValidation:
    manifest_path = Path(path)
    checks: list[dict[str, Any]] = []
    if not manifest_path.exists():
        return ReleaseManifestValidation("read_only_release_manifest", False, [{"name": "manifest_exists", "passed": False}])

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    reports = set(data.get("required_reports", []))
    boundary = dict(data.get("runtime_boundary", {}))

    checks.append({"name": "release_type_read_only", "passed": data.get("release_type") == "read_only_runtime"})
    checks.append({"name": "decision_read_only", "passed": data.get("decision") == "APPROVE_READ_ONLY_RUNTIME"})
    checks.append({"name": "artifact_package_named", "passed": data.get("artifact_package") == "deployment-planning-reports"})
    checks.append({"name": "all_expected_reports_present", "passed": EXPECTED_REPORTS.issubset(reports)})
    checks.append({"name": "no_live_change_registration", "passed": boundary.get("live_change_operations_registered") is False})
    checks.append({"name": "no_runtime_values_in_repo", "passed": boundary.get("runtime_values_in_repository") is False})
    checks.append({"name": "read_only_tools_allowed", "passed": boundary.get("read_only_tools_allowed") is True})
    checks.append({"name": "planning_tools_allowed", "passed": boundary.get("planning_tools_allowed") is True})

    return ReleaseManifestValidation(
        mode="read_only_release_manifest",
        passed=all(item["passed"] for item in checks),
        checks=checks,
    )
