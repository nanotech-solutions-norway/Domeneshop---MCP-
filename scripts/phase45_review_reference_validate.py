"""Validate the Phase 45 review reference gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = [
    "docs/PHASE45_REVIEW_REFERENCE_GATE.md",
    "docs/PHASE44_VALIDATION_REFERENCE_INTAKE.md",
    "docs/PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    "docs/FINAL_REPOSITORY_ARCHIVE_INDEX.md",
    "README.md",
]
MARKERS = [
    "REVIEW_REFERENCE_GATE_ONLY",
    "HOLD_PHASE45_REVIEW_REFERENCE_GATE_ONLY",
    "PHASE44_VALIDATION_REFERENCE_INTAKE_READY",
    "PHASE43_DEPLOYMENT_OPERATIONS_BASELINE_READY",
    "REPOSITORY_ARCHIVE_BASELINE_READY",
    "RUNTIME_VALUES_OUTSIDE_REPOSITORY",
    "VERIFY_REVIEW_RUN_REFERENCE_PRESENT",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 45 review reference gate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase45-review-reference-report.json")
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
            "mode": "phase45_review_reference",
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
