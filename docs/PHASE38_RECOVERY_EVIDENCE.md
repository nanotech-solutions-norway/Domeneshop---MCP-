# Phase 38 Recovery Evidence — 00:47, 28.06.2026

```text
Phase: 38
Status: RECOVERY_EVIDENCE_ONLY
Decision: HOLD_PHASE38_RECOVERY_EVIDENCE_ONLY
Mode: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Class: WRITE_READINESS_SEQUENCE
```

Phase 38 defines evidence required before any future approved domain operation can proceed. It does not enable live changes.

## Required evidence package

```text
APPROVED_DOMAIN_REF
REQUESTED_OPERATION_ID
PRE_OPERATION_ZONE_SNAPSHOT_REF
ZONE_EXPORT_REF
RECOVERY_PLAN_REF
RESTORE_PREVIEW_REF
EVIDENCE_STORAGE_REF
OPERATOR_APPROVAL_REF
```

## Minimum evidence checks

```text
VERIFY_ZONE_SNAPSHOT_EXISTS
VERIFY_RECOVERY_PLAN_DEFINED
VERIFY_RESTORE_PREVIEW_AVAILABLE
VERIFY_OPERATOR_APPROVAL_REFERENCE_PRESENT
VERIFY_HELD_ACTIVATION_POSTURE
```

## Required controls

```text
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
DRY_RUN_DEFAULT=true
WRITE_TOOLS_ENABLED=false
HOLD_LIVE_CHANGE_ACTIVATION
```

## Next sequence

```text
Phase 39: Write preflight and dry-run
Phase 40: Operator approval gate
Phase 41: Staged write activation
Phase 42: Production use validation
```

Validation command:

```bash
python scripts/phase38_recovery_evidence_validate.py --repo-root . --output phase38-recovery-evidence-validation-report.json
```
