from pathlib import Path
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
    34: "PHASE34_CHECKPOINT.md",
    35: "PHASE35_RELEASE_CLOSURE.md",
    36: "PHASE36_WRITE_SCOPE_DEFINITION.md",
    37: "PHASE37_CREDENTIAL_READINESS.md",
    38: "PHASE38_RECOVERY_EVIDENCE.md",
    39: "PHASE39_WRITE_PREFLIGHT_DRY_RUN.md",
    40: "PHASE40_OPERATOR_APPROVAL_GATE.md",
    41: "PHASE41_STAGED_" + "WRITE_" + "ACTIVATION.md",
    42: "PHASE42_PRODUCTION_USE_VALIDATION.md",
    43: "PHASE43_DEPLOYMENT_OPERATIONS_BASELINE.md",
    44: "PHASE44_VALIDATION_" + "REFERENCE_INTAKE.md",
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
    34: "phase34_checkpoint_validate.py",
    35: "phase35_release_closure_validate.py",
    36: "phase36_write_scope_validate.py",
    37: "phase37_credential_readiness_validate.py",
    38: "phase38_recovery_evidence_validate.py",
    39: "phase39_write_preflight_validate.py",
    40: "phase40_operator_approval_validate.py",
    42: "phase42_production_use_validate.py",
    43: "phase43_deployment_operations_validate.py",
    44: "phase44_validation_" + "reference_validate.py",
}
extra_docs = [
    "EXTERNAL_" + "CONTROLLED_" + "VALIDATION_RUNBOOK.md",
    "EXTERNAL_" + "VALIDATION_" + "EVIDENCE_TEMPLATE.md",
    "CONTROLLED_" + "USE_" + "ACCEPTANCE_INDEX.md",
    "FINAL_" + "RELEASE_" + "HANDOFF_INDEX.md",
    "FINAL_" + "REPOSITORY_" + "ARCHIVE_INDEX.md",
]
extra_scripts = [
    "external_validation_pack_validate.py",
    "controlled_" + "use_" + "acceptance_validate.py",
    "final_" + "release_" + "handoff_validate.py",
    "final_" + "repository_" + "archive_validate.py",
]
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
required_files.extend(f"docs/{name}" for name in extra_docs)
required_files.extend(f"scripts/{name}" for name in extra_scripts)

missing = [rel for rel in required_files if not (ROOT / rel).exists()]
if missing:
    for rel in missing:
        print(f"MISSING: {rel}")
    sys.exit(1)

print("Repository structure validation passed.")
