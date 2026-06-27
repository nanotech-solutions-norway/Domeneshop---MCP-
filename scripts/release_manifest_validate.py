"""Create a read-only release manifest validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.release_manifest import validate_release_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a read-only release manifest validation report.")
    parser.add_argument("--manifest", default="config/read-only-release-manifest.example.json")
    parser.add_argument("--output", default="read-only-release-manifest-validation-report.json")
    args = parser.parse_args()

    validation = validate_release_manifest(args.manifest)
    payload = {"summary": validation.summary(), "validation": validation.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
