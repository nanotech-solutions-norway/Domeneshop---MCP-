from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
required = [
    "docs/CAPABILITY_REGISTRY.md",
    "docs/IMPLEMENTATION_RELEASE_TRAINS.md",
    "config/controlled-write-release-manifest.example.json",
    "src/domeneshop_mcp/credential_policy.py",
    "src/domeneshop_mcp/approval_token.py",
    "src/domeneshop_mcp/idempotency.py",
    "src/domeneshop_mcp/audit_store.py",
    "src/domeneshop_mcp/write_release.py",
    "src/domeneshop_mcp/controlled_write.py",
    "src/domeneshop_mcp/write_client.py",
]
checks = []
for rel in required:
    checks.append({"name": f"exists:{rel}", "passed": (ROOT / rel).exists()})

manifest_path = ROOT / "config/controlled-write-release-manifest.example.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks.extend(
        [
            {"name": "foundation_decision", "passed": manifest.get("decision") == "APPROVE_CONTROLLED_WRITE_FOUNDATION"},
            {"name": "live_execution_disabled", "passed": manifest.get("live_execution_enabled") is False},
            {"name": "txt_create_allowlisted", "passed": "domeneshop_create_dns_txt" in manifest.get("approved_tools", [])},
            {"name": "no_wildcard_target", "passed": "*" not in manifest.get("approved_target_prefixes", [])},
        ]
    )

passed = all(item["passed"] for item in checks)
report = {
    "summary": {
        "mode": "controlled_write_foundation",
        "passed": passed,
        "check_count": len(checks),
        "failed_count": sum(1 for item in checks if not item["passed"]),
        "live_execution_enabled": False,
    },
    "checks": checks,
}
output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "controlled-write-foundation-report.json"
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report["summary"], sort_keys=True))
raise SystemExit(0 if passed else 1)
