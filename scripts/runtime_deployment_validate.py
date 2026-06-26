"""Create a Phase 9 runtime deployment validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.runtime_validation import validate_runtime_deployment


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Phase 9 runtime deployment validation report.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="phase9-runtime-deployment-validation-report.json")
    args = parser.parse_args()

    validation = validate_runtime_deployment(args.repo_root)
    payload = {"summary": validation.summary(), "validation": validation.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
