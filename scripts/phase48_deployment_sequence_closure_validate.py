"""Validate Phase 48 deployment sequence closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DOC = "docs/PHASE48_DEPLOYMENT_SEQUENCE_CLOSURE_INDEX.md"
FILES = [
    DOC,
    "docs/PHASE47_REFERENCE_CHAIN_SUMMARY.md",
    "docs/PHASE46_REVIEW_" + "CLOSURE_REFERENCE.md",
    "docs/PHASE45_REVIEW_" + "REFERENCE_GATE.md",
    "docs/PHASE44_VALIDATION_" + "REFERENCE_INTAKE.md",
    "docs/PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    "README.md",
]
MARKERS = [
    "DEPLOYMENT_SEQUENCE_CLOSURE_INDEX_ONLY",
    "HOLD_PHASE48_DEPLOYMENT_SEQUENCE_CLOSURE_INDEX_ONLY",
    "PHASE47_REFERENCE_CHAIN_SUMMARY_READY",
    "DEPLOYMENT_SEQUENCE_CLOSURE_INDEX_READY",
    "VERIFY_SEQUENCE_CLOSURE_INDEX_READY",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase48-deployment-sequence-closure-report.json")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    checks = [{"name": rel, "passed": (root / rel).exists(), "detail": rel} for rel in FILES]
    combined = "\n".join(read(root / rel) for rel in FILES)
    checks.extend({"name": marker, "passed": marker in combined, "detail": marker} for marker in MARKERS)
    passed = all(item["passed"] for item in checks)
    payload = {"summary": {"mode": "phase48_deployment_sequence_closure", "passed": passed, "check_count": len(checks), "failed_count": sum(1 for item in checks if not item["passed"])}, "checks": checks}
    Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0 if passed else 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


if __name__ == "__main__":
    raise SystemExit(main())
