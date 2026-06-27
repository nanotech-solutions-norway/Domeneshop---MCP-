# Phase 36 Write Scope Definition — 14:42, 27.06.2026

```text
Phase: 36
Status: WRITE_SCOPE_DEFINITION_ONLY
Decision: HOLD_PHASE36_WRITE_SCOPE_DEFINITION_ONLY
Mode: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Class: WRITE_READINESS_SEQUENCE
```

Phase 36 defines the future write scope for live domain changes. It does not enable live changes.

## Future allowlist

```text
SCOPE_DNS_RECORD_REVIEW
SCOPE_DNS_RECORD_CREATE
SCOPE_DNS_RECORD_UPDATE
SCOPE_DNS_RECORD_DELETE
SCOPE_DNS_TTL_UPDATE
SCOPE_ZONE_EXPORT_REVIEW
```

Allowed future changes are limited to explicitly approved DNS record work for approved domains and hostnames.

## Denylist

```text
NO_DOMAIN_TRANSFER
NO_REGISTRANT_CHANGE
NO_NAMESERVER_CHANGE_WITHOUT_SEPARATE_APPROVAL
NO_EMAIL_ROUTING_CHANGE_WITHOUT_SEPARATE_APPROVAL
NO_BULK_DELETE_WITHOUT_SEPARATE_APPROVAL
NO_AUTONOMOUS_LIVE_CHANGE
```

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
Phase 37: Secret readiness
Phase 38: Backup and recovery evidence
Phase 39: Write preflight and dry-run
Phase 40: Operator approval gate
Phase 41: Staged write activation
Phase 42: Production use validation
```

Validation command:

```bash
python scripts/phase36_write_scope_validate.py --repo-root . --output phase36-write-scope-validation-report.json
```
