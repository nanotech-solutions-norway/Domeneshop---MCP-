from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

phase_docs = {
    13: "PHASE13_RISK_REGISTER_AND_SCOPE.md",
    14: "PHASE14_ACTIVATION_READINESS_GATE.md",
    15: "PHASE15_CONTROL_BLUEPRINT.md",
    16: "PHASE16_CONTINUITY_EVIDENCE_GATE.md",
    17: "PHASE17_TRACEABILITY.md",
    18: "PHASE18_REPOSITORY_SNAPSHOT.md",
    19: "PHASE19_RELEASE_FREEZE_GATE.md",
    20: "PHASE20_HANDOFF_PACKAGE_GATE.md",
    21: "PHASE21_REVIEW_CLOSURE_GATE.md",
    22: "PHASE22_MAINTENANCE_BASELINE_GATE.md",
    23: "PHASE23_ARCHIVE_INDEX_GATE.md",
    24: "PHASE24_RETENTION_INDEX_GATE.md",
    25: "PHASE25_CHAIN_INDEX_GATE.md",
    26: "PHASE26_CONTINUITY_INDEX_GATE.md",
    27: "PHASE27_REVIEW_INDEX_GATE.md",
    28: "PHASE28_INVENTORY_INDEX_GATE.md",
    29: "PHASE29_CATALOG_INDEX_GATE.md",
    30: "PHASE30_CHECKPOINT.md",
    31: "PHASE31_CHECKPOINT.md",
    32: "PHASE32_CHECKPOINT.md",
    33: "PHASE33_CHECKPOINT.md",
}
phase_validators = {
    13: "phase13_disabled_default_validate.py",
    14: "phase14_activation_readiness_validate.py",
    15: "phase15_control_blueprint_validate.py",
    16: "phase16_continuity_evidence_validate.py",
    17: "phase17_traceability_validate.py",
    18: "phase18_repository_snapshot_validate.py",
    19: "phase19_release_freeze_validate.py",
    20: "phase20_handoff_package_validate.py",
    21: "phase21_review_closure_validate.py",
    22: "phase22_maintenance_baseline_validate.py",
    23: "phase23_archive_index_validate.py",
    24: "phase24_retention_index_validate.py",
    25: "phase25_chain_index_validate.py",
    26: "phase26_continuity_index_validate.py",
    27: "phase27_review_index_validate.py",
    28: "phase28_inventory_index_validate.py",
    29: "phase29_catalog_index_validate.py",
    30: "phase30_checkpoint_validate.py",
    31: "phase31_checkpoint_validate.py",
    32: "phase32_checkpoint_validate.py",
    33: "phase33_checkpoint_validate.py",
}
required_files = [
    "README.md",
    "docs/DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md",
    "docs/SECURITY_AND_WRITE_CONTROL.md",
    "docs/TOOL_CATALOG.md",
    "docs/VALIDATION_CHECKLIST.md",
    "config/domeneshop-mcp.env.example",
    ".github/workflows/validate-domeneshop-mcp.yml",
]
required_files.extend(f"docs/{name}" for name in phase_docs.values())
required_files.extend(f"scripts/{name}" for name in phase_validators.values())

for rel in required_files:
    if not (ROOT / rel).exists():
        print(f"MISSING: {rel}")
        sys.exit(1)

name_prefix = "DOMENE" + "SHOP_"
sensitive_names = [
    name_prefix + "API_" + "SEC" + "RET",
    name_prefix + "API_" + "TOK" + "EN",
    name_prefix + "SFTP_" + "PASS" + "WORD",
]
secret_patterns = [re.compile(rf"{name}\s*=\s*(?!__SET_IN_SECRET_STORE__)(.+)", re.I) for name in sensitive_names]
secret_patterns.append(re.compile("-----BEGIN " + "(RSA|OPENSSH|EC|DSA)" + " PRIVATE KEY-----"))

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in secret_patterns:
        if pattern.search(text):
            print(f"SECRET_PATTERN_DETECTED: {path.relative_to(ROOT)}")
            sys.exit(1)

print("Repository structure validation passed.")
