"""Create a Phase 11 estate validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.estate_validation import validate_estate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Phase 11 estate validation report.")
    parser.add_argument("--registry", default="config/estate-targets.example.json")
    parser.add_argument("--output", default="phase11-estate-validation-report.json")
    args = parser.parse_args()

    validation = validate_estate_registry(args.registry)
    payload = {"summary": validation.summary(), "validation": validation.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
