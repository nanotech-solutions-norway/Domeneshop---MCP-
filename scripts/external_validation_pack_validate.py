"""Validate the external controlled validation handoff pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = [
    "docs/EXTERNAL_CONTROLLED_VALIDATION_RUNBOOK.md",
    "docs/EXTERNAL_VALIDATION_EVIDENCE_TEMPLATE.md",
    "docs/PHASE42_PRODUCTION_USE_VALIDATION.md",
    "README.md",
]
MARKERS = [
    "WRITE_READINESS_SEQUENCE_COMPLETE",
    "READY_FOR_EXTERNAL_CONTROLLED_VALIDATION",
    "RUNTIME_VALUES_OUTSIDE_REPOSITORY",
    "FINAL_OPERATOR_SIGNOFF",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate external validation handoff pack.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="external-validation-pack-report.json")
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
            "mode": "external_validation_pack",
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
