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
    "scripts/phase13_disabled_default_validate.py",
    "scripts/phase14_activation_readiness_validate.py",
    "scripts/phase15_control_blueprint_validate.py",
    "config/domeneshop-mcp.env.example",
    ".github/workflows/validate-domeneshop-mcp.yml",
]

for rel in required_files:
    path = ROOT / rel
    if not path.exists():
        print(f"MISSING: {rel}")
        sys.exit(1)

secret_patterns = [
    re.compile(r"DOMENESHOP_API_SECRET\s*=\s*(?!__SET_IN_SECRET_STORE__)(.+)", re.I),
    re.compile(r"DOMENESHOP_API_TOKEN\s*=\s*(?!__SET_IN_SECRET_STORE__)(.+)", re.I),
    re.compile(r"DOMENESHOP_SFTP_PASSWORD\s*=\s*(?!__SET_IN_SECRET_STORE__)(.+)", re.I),
    re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
]

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
