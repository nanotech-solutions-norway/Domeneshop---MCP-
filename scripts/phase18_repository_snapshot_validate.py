"""Validate the Phase 18 repository snapshot gate."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

PHASE_DOCS = [
    Path("docs/PHASE13_RISK_REGISTER_AND_SCOPE.md"),
    Path("docs/PHASE14_ACTIVATION_READINESS_GATE.md"),
    Path("docs/PHASE15_CONTROL_BLUEPRINT.md"),
    Path("docs/PHASE16_CONTINUITY_EVIDENCE_GATE.md"),
    Path("docs/PHASE17_TRACEABILITY.md"),
    Path("docs/PHASE18_REPOSITORY_SNAPSHOT.md"),
]
PHASE_VALIDATORS = [
    Path("scripts/phase13_disabled_default_validate.py"),
    Path("scripts/phase14_activation_readiness_validate.py"),
    Path("scripts/phase15_control_blueprint_validate.py"),
    Path("scripts/phase16_continuity_evidence_validate.py"),
    Path("scripts/phase17_traceability_validate.py"),
    Path("scripts/phase18_repository_snapshot_validate.py"),
]
ENV_EXAMPLE = Path("config/domeneshop-mcp.env.example")
WORKFLOW = Path(".github/workflows/validate-domeneshop-mcp.yml")
README = Path("README.md")

REQUIRED_ENV_DEFAULTS = {
    "WRITE_TOOLS_ENABLED": "false",
    "DRY_RUN_DEFAULT": "true",
    "REQUIRE_OPERATOR_APPROVAL": "true",
    "REQUIRE_BACKUP_EVIDENCE": "true",
    "REQUIRE_PREFLIGHT_REPORT": "true",
}

REQUIRED_HOLD_MARKERS = (
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "HOLD_PHASE13_ACTIVATION",
    "HOLD_PHASE14_ACTIVATION_READINESS_ONLY",
    "HOLD_PHASE15_CONTROL_BLUEPRINT_ONLY",
    "HOLD_PHASE16_CONTINUITY_EVIDENCE_ONLY",
    "HOLD_PHASE17_TRACEABILITY_ONLY",
    "HOLD_PHASE18_REPOSITORY_SNAPSHOT_ONLY",
)

REQUIRED_REPORT_NAMES = (
    "phase13-disabled-default-validation-report.json",
    "phase14-activation-readiness-validation-report.json",
    "phase15-control-blueprint-validation-report.json",
    "phase16-continuity-evidence-validation-report.json",
    "phase17-traceability-validation-report.json",
    "phase18-repository-snapshot-validation-report.json",
    "read-only-release-manifest-validation-report.json",
)

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Phase 18 repository snapshot gate.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--output", default="phase18-repository-snapshot-validation-report.json", help="JSON report path.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    checks = validate_phase18_repository_snapshot(root)
    passed = all(check.passed for check in checks)

    payload = {
        "summary": {
            "mode": "phase18_repository_snapshot_validation",
            "phase18_snapshot": "SNAPSHOT_ONLY" if passed else "CHECK_FAILED",
            "release_decision": "HOLD_PHASE18_REPOSITORY_SNAPSHOT_ONLY" if passed else "HOLD_FOR_FIX",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for check in checks if not check.passed),
        },
        "checks": [check.__dict__ for check in checks],
    }

    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def validate_phase18_repository_snapshot(repo_root: Path) -> list[Check]:
    checks: list[Check] = []
    for rel in PHASE_DOCS:
        checks.append(_exists_check(f"doc_exists:{rel.name}", repo_root / rel))
    for rel in PHASE_VALIDATORS:
        checks.append(_exists_check(f"validator_exists:{rel.name}", repo_root / rel))
    checks.append(_exists_check("env_example_exists", repo_root / ENV_EXAMPLE))
    checks.append(_exists_check("workflow_exists", repo_root / WORKFLOW))
    checks.append(_exists_check("readme_exists", repo_root / README))

    env_values = _parse_key_value_lines(_read_text(repo_root / ENV_EXAMPLE))
    for key, expected in REQUIRED_ENV_DEFAULTS.items():
        actual = env_values.get(key)
        checks.append(Check(f"env_default:{key}", actual == expected, f"Expected {key}={expected}; observed {key}={actual!r}."))

    combined_text = "\n".join(_read_text(repo_root / rel) for rel in PHASE_DOCS) + "\n" + _read_text(repo_root / README)
    for marker in REQUIRED_HOLD_MARKERS:
        checks.append(Check(f"hold_marker:{marker}", marker in combined_text, f"Required marker must appear in repository snapshot text: {marker}."))

    workflow_text = _read_text(repo_root / WORKFLOW)
    for report_name in REQUIRED_REPORT_NAMES:
        checks.append(Check(f"workflow_report:{report_name}", report_name in workflow_text, f"Workflow must include report: {report_name}."))

    return checks


def _exists_check(name: str, path: Path) -> Check:
    return Check(name, path.exists(), f"Required path: {path}")


def _parse_key_value_lines(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'').lower()
    return values


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
