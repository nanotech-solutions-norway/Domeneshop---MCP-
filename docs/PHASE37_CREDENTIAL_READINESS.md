# Phase 37 Credential Readiness — 14:50, 27.06.2026

```text
Phase: 37
Status: CREDENTIAL_READINESS_ONLY
Decision: HOLD_PHASE37_CREDENTIAL_READINESS_ONLY
Mode: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Class: WRITE_READINESS_SEQUENCE
```

Phase 37 defines how runtime credential material must be supplied for future write/live domain changes. It does not enable live changes and does not store credential values in the repository.

## Repository rule

```text
NO_CREDENTIAL_VALUES_IN_REPOSITORY
PLACEHOLDERS_ONLY_IN_EXAMPLES
RUNTIME_VALUES_SUPPLIED_EXTERNALLY
ROTATION_REQUIRED_BEFORE_PRODUCTION_USE
AUDIT_REQUIRED_FOR_CREDENTIAL_ACCESS
```

## Required runtime entries

```text
DOMENESHOP_API_TOKEN_REF
DOMENESHOP_API_SECRET_REF
DOMENESHOP_ACCOUNT_REF
APPROVED_DOMAIN_REGISTRY_REF
OPERATOR_APPROVAL_CHANNEL_REF
BACKUP_STORAGE_REF
```

The entries above are references only. Actual values must remain outside the repository.

## Required controls before any future live change

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
Phase 38: Backup and recovery evidence
Phase 39: Write preflight and dry-run
Phase 40: Operator approval gate
Phase 41: Staged write activation
Phase 42: Production use validation
```

Validation command:

```bash
python scripts/phase37_credential_readiness_validate.py --repo-root . --output phase37-credential-readiness-validation-report.json
```
