"""Validate the Phase 38 recovery evidence gate."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

DOCS = {
    13: "PHASE13_RISK_REGISTER_AND_SCOPE.md",
    14: "PHASE14_ACTIVATION_READINESS_GATE.md",
    15: "PHASE15_CONTROL_BLUEPRINT.md",
    16: "PHASE16_CONTINUITY_EVIDENCE_GATE.md",
    17: "PHASE17_TRACEABILITY.md",
    18: "PHASE18_REPOSITORY_SNAPSHOT.md",
    19: "PHASE19_RELEASE_FREEZE_GATE.md",
    20: "PHASE20_HANDOFF_PACKAGE_GATE.md",
    21: "PHASE21_REVIEW_CLOSURE_GATE.md",
    22: "PHASE22_MAINTENANCE_BASELINE_GATE.md",
    23: "PHASE23_ARCHIVE_INDEX_GATE.md",
    24: "PHASE24_RETENTION_INDEX_GATE.md",
    25: "PHASE25_CHAIN_INDEX_GATE.md",
    26: "PHASE26_CONTINUITY_INDEX_GATE.md",
    27: "PHASE27_REVIEW_INDEX_GATE.md",
    28: "PHASE28_INVENTORY_INDEX_GATE.md",
    29: "PHASE29_CATALOG_INDEX_GATE.md",
    30: "PHASE30_CHECKPOINT.md",
    31: "PHASE31_CHECKPOINT.md",
    32: "PHASE32_CHECKPOINT.md",
    33: "PHASE33_CHECKPOINT.md",
    34: "PHASE34_CHECKPOINT.md",
    35: "PHASE35_RELEASE_CLOSURE.md",
    36: "PHASE36_WRITE_SCOPE_DEFINITION.md",
    37: "PHASE37_CREDENTIAL_READINESS.md",
    38: "PHASE38_RECOVERY_EVIDENCE.md",
}
VALIDATORS = {
    13: "phase13_disabled_default_validate.py",
    14: "phase14_activation_readiness_validate.py",
    15: "phase15_control_blueprint_validate.py",
    16: "phase16_continuity_evidence_validate.py",
    17: "phase17_traceability_validate.py",
    18: "phase18_repository_snapshot_validate.py",
    19: "phase19_release_freeze_validate.py",
    20: "phase20_handoff_package_validate.py",
    21: "phase21_review_closure_validate.py",
    22: "phase22_maintenance_baseline_validate.py",
    23: "phase23_archive_index_validate.py",
    24: "phase24_retention_index_validate.py",
    25: "phase25_chain_index_validate.py",
    26: "phase26_continuity_index_validate.py",
    27: "phase27_review_index_validate.py",
    28: "phase28_inventory_index_validate.py",
    29: "phase29_catalog_index_validate.py",
    30: "phase30_checkpoint_validate.py",
    31: "phase31_checkpoint_validate.py",
    32: "phase32_checkpoint_validate.py",
    33: "phase33_checkpoint_validate.py",
    34: "phase34_checkpoint_validate.py",
    35: "phase35_release_closure_validate.py",
    36: "phase36_write_scope_validate.py",
    37: "phase37_credential_readiness_validate.py",
    38: "phase38_recovery_evidence_validate.py",
}
REPORTS = {
    13: "phase13-disabled-default-validation-report.json",
    14: "phase14-activation-readiness-validation-report.json",
    15: "phase15-control-blueprint-validation-report.json",
    16: "phase16-continuity-evidence-validation-report.json",
    17: "phase17-traceability-validation-report.json",
    18: "phase18-repository-snapshot-validation-report.json",
    19: "phase19-release-freeze-validation-report.json",
    20: "phase20-handoff-package-validation-report.json",
    21: "phase21-review-closure-validation-report.json",
    22: "phase22-maintenance-baseline-validation-report.json",
    23: "phase23-archive-index-validation-report.json",
    24: "phase24-retention-index-validation-report.json",
    25: "phase25-chain-index-validation-report.json",
    26: "phase26-continuity-index-validation-report.json",
    27: "phase27-review-index-validation-report.json",
    28: "phase28-inventory-index-validation-report.json",
    29: "phase29-catalog-index-validation-report.json",
    30: "phase30-checkpoint-validation-report.json",
    31: "phase31-checkpoint-validation-report.json",
    32: "phase32-checkpoint-validation-report.json",
    33: "phase33-checkpoint-validation-report.json",
    34: "phase34-checkpoint-validation-report.json",
    35: "phase35-release-closure-validation-report.json",
    36: "phase36-write-scope-validation-report.json",
    37: "phase37-credential-readiness-validation-report.json",
    38: "phase38-recovery-evidence-validation-report.json",
}
ENV_DEFAULTS = {
    "WRITE_TOOLS_ENABLED": "false",
    "DRY_RUN_DEFAULT": "true",
    "REQUIRE_OPERATOR_APPROVAL": "true",
    "REQUIRE_BACKUP_EVIDENCE": "true",
    "REQUIRE_PREFLIGHT_REPORT": "true",
}
REQUIRED_MARKERS = [
    "APPROVED_DOMAIN_REF",
    "PRE_OPERATION_ZONE_SNAPSHOT_REF",
    "ZONE_EXPORT_REF",
    "RECOVERY_PLAN_REF",
    "RESTORE_PREVIEW_REF",
    "EVIDENCE_STORAGE_REF",
    "VERIFY_ZONE_SNAPSHOT_EXISTS",
    "VERIFY_RECOVERY_PLAN_DEFINED",
    "VERIFY_RESTORE_PREVIEW_AVAILABLE",
    "VERIFY_HELD_ACTIVATION_POSTURE",
]

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Phase 38 recovery evidence gate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase38-recovery-evidence-validation-report.json")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    checks = validate(root)
    passed = all(item.passed for item in checks)
    payload = {
        "summary": {
            "mode": "phase38_recovery_evidence_validation",
            "phase38_recovery_evidence": "RECOVERY_EVIDENCE_ONLY" if passed else "CHECK_FAILED",
            "release_decision": "HOLD_PHASE38_RECOVERY_EVIDENCE_ONLY" if passed else "HOLD_FOR_FIX",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for item in checks if not item.passed),
        },
        "checks": [item.__dict__ for item in checks],
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def validate(root: Path) -> list[Check]:
    checks: list[Check] = []
    for name in DOCS.values():
        checks.append(exists(f"doc:{name}", root / "docs" / name))
    for name in VALIDATORS.values():
        checks.append(exists(f"validator:{name}", root / "scripts" / name))
    for rel in ["README.md", "config/domeneshop-mcp.env.example", ".github/workflows/validate-domeneshop-mcp.yml"]:
        checks.append(exists(f"required:{rel}", root / rel))

    env = parse_env(read(root / "config/domeneshop-mcp.env.example"))
    for key, expected in ENV_DEFAULTS.items():
        checks.append(Check(f"env:{key}", env.get(key) == expected, f"Expected {expected}; observed {env.get(key)!r}."))

    phase_doc = read(root / "docs" / DOCS[38])
    combined = "\n".join(read(root / "docs" / name) for name in DOCS.values()) + "\n" + read(root / "README.md")
    checks.append(Check("hold:phase38", "HOLD_PHASE38_RECOVERY_EVIDENCE_ONLY" in combined, "Required Phase 38 hold marker."))
    checks.append(Check("hold:live", "HOLD_LIVE_CHANGE_ACTIVATION" in combined, "Required live hold marker."))
    for marker in REQUIRED_MARKERS:
        checks.append(Check(f"evidence:{marker}", marker in phase_doc, f"Required marker: {marker}."))
    checks.append(Check("sequence:remaining", "Phase 39" in combined and "Phase 42" in combined, "Required remaining sequence markers."))

    workflow = read(root / ".github/workflows/validate-domeneshop-mcp.yml")
    for report in [*REPORTS.values(), "read-only-release-manifest-validation-report.json"]:
        checks.append(Check(f"report:{report}", report in workflow, f"Workflow must include {report}."))
    return checks


def exists(name: str, path: Path) -> Check:
    return Check(name, path.exists(), f"Required path: {path}")


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"\'').lower()
    return values


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
