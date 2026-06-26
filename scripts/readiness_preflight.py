"""Create a Phase 8 readiness preflight report."""

from __future__ import annotations

import json
from pathlib import Path
import argparse

from domeneshop_mcp.readiness import evaluate_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Phase 8 readiness report.")
    parser.add_argument("--output", default="phase8-readiness-preflight-report.json")
    args = parser.parse_args()

    decision = evaluate_readiness()
    payload = {"summary": decision.summary(), "decision": decision.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
