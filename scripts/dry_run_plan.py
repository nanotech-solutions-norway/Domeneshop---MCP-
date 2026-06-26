"""Create a local dry-run deployment report.

This script creates a manifest and comparison report only. It performs no remote write.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.deploy_plan import build_local_manifest, compare_manifest, remote_entries_from_metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a dry-run deployment report.")
    parser.add_argument("--source-root", default=".")
    parser.add_argument("--target-root", default="/www")
    parser.add_argument("--allowed-roots", default="/www,/www/solarex_forms,/www/atlas_control,/www/atlas_pip2")
    parser.add_argument("--remote-metadata-json", default="")
    parser.add_argument("--output", default="dry-run-report.json")
    args = parser.parse_args()

    remote_metadata = []
    if args.remote_metadata_json:
        remote_metadata = json.loads(Path(args.remote_metadata_json).read_text(encoding="utf-8"))

    local_entries = build_local_manifest(args.source_root)
    remote_entries = remote_entries_from_metadata(remote_metadata)
    plan = compare_manifest(
        local_entries,
        remote_entries,
        target_root=args.target_root,
        allowed_roots=tuple(x.strip() for x in args.allowed_roots.split(",") if x.strip()),
        source_root=args.source_root,
    )
    payload = {"summary": plan.summary(), "plan": plan.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
