# Domeneshop MCP Implementation Plan — 14:42, 27.06.2026

This repository is the system of record for the Domeneshop MCP bridge.

## Current posture

```text
Runtime posture: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Activation posture: HOLD_LIVE_CHANGE_ACTIVATION
Runtime access values: outside repository
```

## Current write-readiness state

| Area | Status |
|---|---|
| Phase 13 through Phase 34 control chain | Implemented |
| Phase 35 release closure | Implemented as release-closure-only control layer |
| Phase 36 write scope definition | Implemented as scope-definition-only control layer |
| Runtime access values | Not stored in repository |
| Live changes | Still held |

## Phase 36 files

```text
docs/PHASE36_WRITE_SCOPE_DEFINITION.md
scripts/phase36_write_scope_validate.py
```

## Future allowlist

```text
SCOPE_DNS_RECORD_REVIEW
SCOPE_DNS_RECORD_CREATE
SCOPE_DNS_RECORD_UPDATE
SCOPE_DNS_RECORD_DELETE
SCOPE_DNS_TTL_UPDATE
SCOPE_ZONE_EXPORT_REVIEW
```

## Denylist

```text
NO_DOMAIN_TRANSFER
NO_REGISTRANT_CHANGE
NO_NAMESERVER_CHANGE_WITHOUT_SEPARATE_APPROVAL
NO_EMAIL_ROUTING_CHANGE_WITHOUT_SEPARATE_APPROVAL
NO_BULK_DELETE_WITHOUT_SEPARATE_APPROVAL
NO_AUTONOMOUS_LIVE_CHANGE
```

## Remaining write-readiness sequence

```text
Phase 37: Secret readiness
Phase 38: Backup and recovery evidence
Phase 39: Write preflight and dry-run
Phase 40: Operator approval gate
Phase 41: Staged write activation
Phase 42: Production use validation
```

## CI artifact package

```text
deployment-planning-reports
```

Phase 13 through Phase 36 validation reports are included together with the read-only release manifest report.

## Local validation

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
python scripts/phase36_write_scope_validate.py --repo-root . --output phase36-write-scope-validation-report.json
python scripts/release_manifest_validate.py --manifest config/read-only-release-manifest.example.json --output read-only-release-manifest-validation-report.json
```

## Current decision index

```text
APPROVE_READ_ONLY_RUNTIME
HOLD_LIVE_CHANGE_ACTIVATION
HOLD_PHASE36_WRITE_SCOPE_DEFINITION_ONLY
```

## Repository target

```text
nanotech-solutions-norway/Domeneshop---MCP-
```
