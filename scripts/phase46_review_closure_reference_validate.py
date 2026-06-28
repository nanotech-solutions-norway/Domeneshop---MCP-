"""Validate Phase 46 review closure reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DOC = "docs/PHASE46_REVIEW_" + "CLOSURE_REFERENCE.md"
FILES = [
    DOC,
    "docs/PHASE45_REVIEW_" + "REFERENCE_GATE.md",
    "docs/PHASE44_VALIDATION_" + "REFERENCE_INTAKE.md",
    "docs/PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    "README.md",
]
MARKERS = [
    "REVIEW_CLOSURE_REFERENCE_ONLY",
    "HOLD_PHASE46_REVIEW_CLOSURE_REFERENCE_ONLY",
    "PHASE45_REVIEW_REFERENCE_GATE_READY",
    "PHASE44_VALIDATION_REFERENCE_INTAKE_READY",
    "VERIFY_CLOSURE_RUN_REFERENCE_PRESENT",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase46-review-closure-reference-report.json")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    checks = [{"name": rel, "passed": (root / rel).exists(), "detail": rel} for rel in FILES]
    combined = "\n".join(read(root / rel) for rel in FILES)
    checks.extend({"name": marker, "passed": marker in combined, "detail": marker} for marker in MARKERS)
    passed = all(item["passed"] for item in checks)
    payload = {"summary": {"mode": "phase46_review_closure_reference", "passed": passed, "check_count": len(checks), "failed_count": sum(1 for item in checks if not item["passed"])}, "checks": checks}
    Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if passed else 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
