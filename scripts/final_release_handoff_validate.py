"""Validate the final release handoff index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FILES = [
    "docs/FINAL_RELEASE_HANDOFF_INDEX.md",
    "docs/PHASE42_PRODUCTION_USE_VALIDATION.md",
    "docs/EXTERNAL_CONTROLLED_VALIDATION_RUNBOOK.md",
    "docs/EXTERNAL_VALIDATION_EVIDENCE_TEMPLATE.md",
    "docs/CONTROLLED_USE_ACCEPTANCE_INDEX.md",
    "scripts/phase42_production_use_validate.py",
    "scripts/external_validation_pack_validate.py",
    "scripts/controlled_use_acceptance_validate.py",
    "README.md",
]
MARKERS = [
    "PHASE_35_TO_42_COMPLETE",
    "EXTERNAL_VALIDATION_HANDOFF_COMPLETE",
    "CONTROLLED_USE_ACCEPTANCE_INDEX_COMPLETE",
    "REPOSITORY_SIDE_READINESS_COMPLETE",
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "NO_AUTONOMOUS_LIVE_CHANGE",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate final release handoff index.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="final-release-handoff-report.json")
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
            "mode": "final_release_handoff",
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
