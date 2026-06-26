"""Create a Phase 7 change-control preflight report.

The script creates evidence only. It performs no provider operation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domeneshop_mcp.audit_model import build_audit_event
from domeneshop_mcp.change_control import ChangeGateConfig, ChangeRequest, evaluate_change_preflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a change-control preflight report.")
    parser.add_argument("--action", default="sftp_upload_file")
    parser.add_argument("--target", default="/www/index.html")
    parser.add_argument("--risk-level", default="medium", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--operator", default="ci-validation")
    parser.add_argument("--approval-reference", default="")
    parser.add_argument("--backup-evidence-reference", default="artifacts/phase6-backup-evidence-report.json")
    parser.add_argument("--preflight-reference", default="artifacts/phase5-dry-run-report.json")
    parser.add_argument("--output", default="phase7-change-preflight-report.json")
    args = parser.parse_args()

    request = ChangeRequest(
        action=args.action,
        target=args.target,
        risk_level=args.risk_level,
        operator=args.operator,
        approval_reference=args.approval_reference or None,
        backup_evidence_reference=args.backup_evidence_reference or None,
        preflight_reference=args.preflight_reference or None,
    )
    decision = evaluate_change_preflight(request, ChangeGateConfig.from_env())
    audit_event = build_audit_event(
        "change_preflight_evaluated",
        args.operator,
        args.target,
        decision.summary(),
    )
    payload = {"summary": decision.summary(), "decision": decision.__dict__, "audit_event": audit_event.__dict__}
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
