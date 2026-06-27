from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

required_files = [
    "README.md",
    "docs/DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md",
    "docs/SECURITY_AND_WRITE_CONTROL.md",
    "docs/TOOL_CATALOG.md",
    "docs/VALIDATION_CHECKLIST.md",
    "docs/PHASE13_RISK_REGISTER_AND_SCOPE.md",
    "docs/PHASE14_ACTIVATION_READINESS_GATE.md",
    "docs/PHASE15_CONTROL_BLUEPRINT.md",
    "docs/PHASE16_CONTINUITY_EVIDENCE_GATE.md",
    "docs/PHASE17_TRACEABILITY.md",
    "docs/PHASE18_REPOSITORY_SNAPSHOT.md",
    "docs/PHASE19_RELEASE_FREEZE_GATE.md",
    "docs/PHASE20_HANDOFF_PACKAGE_GATE.md",
    "docs/PHASE21_REVIEW_CLOSURE_GATE.md",
    "scripts/phase13_disabled_default_validate.py",
    "scripts/phase14_activation_readiness_validate.py",
    "scripts/phase15_control_blueprint_validate.py",
    "scripts/phase16_continuity_evidence_validate.py",
    "scripts/phase17_traceability_validate.py",
    "scripts/phase18_repository_snapshot_validate.py",
    "scripts/phase19_release_freeze_validate.py",
    "scripts/phase20_handoff_package_validate.py",
    "scripts/phase21_review_closure_validate.py",
    "config/domeneshop-mcp.env.example",
    ".github/workflows/validate-domeneshop-mcp.yml",
]

for rel in required_files:
    path = ROOT / rel
    if not path.exists():
        print(f"MISSING: {rel}")
        sys.exit(1)

name_prefix = "DOMENE" + "SHOP_"
sensitive_names = [
    name_prefix + "API_" + "SEC" + "RET",
    name_prefix + "API_" + "TOK" + "EN",
    name_prefix + "SFTP_" + "PASS" + "WORD",
]

secret_patterns = [
    re.compile(rf"{name}\s*=\s*(?!__SET_IN_SECRET_STORE__)(.+)", re.I)
    for name in sensitive_names
]
private_marker = "-----BEGIN " + "(RSA|OPENSSH|EC|DSA)" + " PRIVATE KEY-----"
secret_patterns.append(re.compile(private_marker))

for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in secret_patterns:
            if pattern.search(text):
                print(f"SECRET_PATTERN_DETECTED: {path.relative_to(ROOT)}")
                sys.exit(1)

print("Repository structure validation passed.")
