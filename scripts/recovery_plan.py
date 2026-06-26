"""Create Phase 6 backup evidence and restore-preview reports.

The script reads a dry-run plan and remote metadata, then writes planning reports.
It performs no remote write.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.deploy_plan import DeploymentPlan, remote_entries_from_metadata
from domeneshop_mcp.recovery_plan import build_backup_evidence_manifest, build_restore_preview


def main() -> int:
    parser = argparse.ArgumentParser(description="Create backup evidence and restore-preview reports.")
    parser.add_argument("--dry-run-report", required=True)
    parser.add_argument("--remote-metadata-json", default="")
    parser.add_argument("--backup-root", default="/www/backups/dry-run")
    parser.add_argument("--allowed-roots", default="/www,/www/solarex_forms,/www/atlas_control,/www/atlas_pip2")
    parser.add_argument("--backup-output", default="backup-evidence-report.json")
    parser.add_argument("--restore-output", default="restore-preview-report.json")
    args = parser.parse_args()

    dry_run_payload = json.loads(Path(args.dry_run_report).read_text(encoding="utf-8"))
    plan_payload = dry_run_payload.get("plan", dry_run_payload)
    plan = DeploymentPlan(
        mode=str(plan_payload["mode"]),
        source_root=str(plan_payload["source_root"]),
        target_root=str(plan_payload["target_root"]),
        new_files=list(plan_payload.get("new_files", [])),
        changed_files=list(plan_payload.get("changed_files", [])),
        unchanged_files=list(plan_payload.get("unchanged_files", [])),
        blocked_files=list(plan_payload.get("blocked_files", [])),
    )

    remote_metadata = []
    if args.remote_metadata_json:
        remote_metadata = json.loads(Path(args.remote_metadata_json).read_text(encoding="utf-8"))
    remote_entries = remote_entries_from_metadata(remote_metadata)
    allowed_roots = tuple(x.strip() for x in args.allowed_roots.split(",") if x.strip())

    manifest = build_backup_evidence_manifest(
        plan,
        remote_entries,
        backup_root=args.backup_root,
        allowed_roots=allowed_roots,
    )
    preview = build_restore_preview(manifest, allowed_roots=allowed_roots)

    backup_payload = {"summary": manifest.summary(), "manifest": manifest.__dict__}
    preview_payload = {"summary": preview.summary(), "preview": preview.__dict__}
    Path(args.backup_output).write_text(json.dumps(backup_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.restore_output).write_text(json.dumps(preview_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"backup": backup_payload["summary"], "restore_preview": preview_payload["summary"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
