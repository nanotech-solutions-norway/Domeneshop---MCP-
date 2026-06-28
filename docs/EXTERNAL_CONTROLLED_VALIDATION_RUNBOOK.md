# External Controlled Validation Runbook — 01:42, 28.06.2026

This runbook starts after Phase 42 is validated.

Repository-side state:

```text
WRITE_READINESS_SEQUENCE_COMPLETE
READY_FOR_EXTERNAL_CONTROLLED_VALIDATION
RUNTIME_VALUES_OUTSIDE_REPOSITORY
HOLD_LIVE_CHANGE_ACTIVATION
NO_AUTONOMOUS_LIVE_CHANGE
```

## Purpose

Provide the operator checklist for external controlled validation of the Domeneshop MCP bridge.

This runbook does not store runtime values, credentials, domain account data, or external evidence files in the repository.

## Operator sequence

```text
1. Confirm approved domain target.
2. Confirm approved operation ID.
3. Confirm runtime credential references are available outside the repository.
4. Confirm current zone snapshot evidence reference.
5. Confirm recovery plan evidence reference.
6. Confirm preflight report evidence reference.
7. Confirm dry-run report evidence reference.
8. Confirm operator approval evidence reference.
9. Confirm staged-gate evidence reference.
10. Execute external controlled validation in the approved runtime environment.
11. Record post-change verification evidence reference.
12. Record audit log evidence reference.
13. Record final operator signoff reference.
```

## External validation acceptance criteria

```text
APPROVED_DOMAIN_CONFIRMED
OPERATION_SCOPE_CONFIRMED
RUNTIME_REFERENCES_CONFIRMED
RECOVERY_REFERENCE_CONFIRMED
PREFLIGHT_REFERENCE_CONFIRMED
DRY_RUN_REFERENCE_CONFIRMED
OPERATOR_APPROVAL_CONFIRMED
STAGED_GATE_CONFIRMED
POST_CHANGE_VERIFICATION_CONFIRMED
AUDIT_LOG_CONFIRMED
FINAL_OPERATOR_SIGNOFF_CONFIRMED
```

## Stop conditions

```text
MISSING_APPROVED_DOMAIN
MISSING_RUNTIME_REFERENCE
MISSING_RECOVERY_REFERENCE
MISSING_PREFLIGHT_REFERENCE
MISSING_DRY_RUN_REFERENCE
MISSING_OPERATOR_APPROVAL
MISSING_FINAL_SIGNOFF
UNEXPECTED_SCOPE_CHANGE
UNVERIFIED_POST_CHANGE_STATE
```

## Repository rule

```text
Do not commit runtime values or external evidence files unless explicitly safe for documentation.
```
