"""Validate the Phase 43 deployment operations baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = [
    "docs/PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    "docs/FINAL_REPOSITORY_ARCHIVE_INDEX.md",
    "docs/FINAL_RELEASE_HANDOFF_INDEX.md",
    "docs/CONTROLLED_USE_ACCEPTANCE_INDEX.md",
    "docs/EXTERNAL_CONTROLLED_VALIDATION_RUNBOOK.md",
    "README.md",
]
MARKERS = [
    "DEPLOYMENT_OPERATIONS_BASELINE_ONLY",
    "HOLD_PHASE43_DEPLOYMENT_OPERATIONS_BASELINE_ONLY",
    "READY_FOR_EXTERNAL_CONTROLLED_VALIDATION",
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "NO_AUTONOMOUS_LIVE_CHANGE",
    "FINAL_OPERATOR_SIGNOFF_REF",
    "VERIFY_RUNTIME_VALUES_EXTERNAL",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 43 deployment operations baseline.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase43-deployment-operations-report.json")
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
            "mode": "phase43_deployment_operations",
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
