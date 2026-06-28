"""Validate the Phase 44 validation reference intake."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = [
    "docs/PHASE44_VALIDATION_REFERENCE_INTAKE.md",
    "docs/PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    "docs/CONTROLLED_USE_ACCEPTANCE_INDEX.md",
    "docs/FINAL_RELEASE_HANDOFF_INDEX.md",
    "docs/FINAL_REPOSITORY_ARCHIVE_INDEX.md",
    "README.md",
]
MARKERS = [
    "VALIDATION_REFERENCE_INTAKE_ONLY",
    "HOLD_PHASE44_VALIDATION_REFERENCE_INTAKE_ONLY",
    "PHASE43_DEPLOYMENT_OPERATIONS_BASELINE_READY",
    "FINAL_OPERATOR_SIGNOFF_REQUIRED",
    "RUNTIME_VALUES_OUTSIDE_REPOSITORY",
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "NO_AUTONOMOUS_LIVE_CHANGE",
    "VERIFY_PRIVATE_MATERIAL_OUTSIDE_REPOSITORY",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 44 validation reference intake.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase44-validation-reference-report.json")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    checks = []
    for rel in FILES:
        checks.append({"name": rel, "passed": (root / rel).exists(), "detail": rel})
    combined = "\n".join(read(root / rel) for rel in FILES)
    for marker in MARKERS:
        checks.append({"name": marker, "passed": marker in combined, "detail": marker})
    passed = all(item["passed"] for item in checks)
    payload = {
        "summary": {
            "mode": "phase44_validation_reference",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for item in checks if not item["passed"]),
        },
        "checks": checks,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
