# Domeneshop MCP Implementation Baseline — updated 16.08.2026

This repository is the system of record for the Domeneshop MCP bridge.

## Current posture

```text
Runtime posture: READ_ONLY_RUNTIME_PLUS_CONTROLLED_WRITE_FOUNDATION
Activation posture: HOLD_LIVE_CHANGE_ACTIVATION
Runtime access values: outside repository
Read-only MCP server: unchanged
Live write tools registered: false
Protected API/SFTP/MCP read validation: passed 10.08.2026
Public status-surface workflow validation: passed 10.08.2026
D-R3 isolated DNS TXT pilot: protected GET-only target preflight passed; live pilot not authorized
```

## Re-evaluated implementation state

| Release train | Status | Evidence |
|---|---|---|
| D-R0 baseline freeze and capability registry | Implemented | `docs/CAPABILITY_REGISTRY.md` |
| D-R1 credential placeholder hardening | Implemented; protected validation passed | `src/domeneshop_mcp/credential_policy.py` |
| D-R1 API/SFTP/MCP read runtime | Protected API/SFTP/MCP and public status-surface workflow validation passed | `docs/PROTECTED_READONLY_VALIDATION_20260810.md` |
| D-R2 approval-token control | Implemented; repository validation passed | `src/domeneshop_mcp/approval_token.py` |
| D-R2 idempotency control | Implemented; repository validation passed; runtime storage pending | `src/domeneshop_mcp/idempotency.py` |
| D-R2 persistent audit control | Implemented; repository validation passed; runtime storage pending | `src/domeneshop_mcp/audit_store.py` |
| D-R2 controlled-write release manifest | Implemented; live execution disabled | `config/controlled-write-release-manifest.example.json` |
| D-R2 shared controlled-write executor | Implemented; not registered in read server | `src/domeneshop_mcp/controlled_write.py` |
| D-R3 DNS TXT provider mutation client | Implemented; live pilot not authorized | `src/domeneshop_mcp/write_client.py` |
| D-R3 isolated TXT preflight | Protected GET-only run `31966109707` passed; zero collision; no mutation | `docs/DNS_TXT_PILOT_PREFLIGHT.md` |
| D-R3 controlled-write dry run | Protected exact-target workflow implemented; execution pending protected signing secret | `docs/DNS_TXT_PILOT_DRY_RUN.md` |
| HTTP-forward mutation | Planned | Starts after DNS pilot acceptance |
| SFTP upload/replace/restore | Planned | Separate D-R4 release |
| SQL read/edit/write | Planned | Separate D-R5 release |

## Mandatory boundary

```text
WRITE_TOOLS_ENABLED=false
LIVE_EXECUTION_MANIFEST=false
NO_WRITE_TOOL_REGISTRATION
NO_PROVIDER_MUTATION_AUTHORIZED
```

The controlled-write foundation is code-complete for repository validation, but it is not a production-write release. Live activation requires an approved isolated test target, external runtime credentials, a pilot release manifest, one-time approval evidence, dry-run evidence, readback, rollback, audit, and final operator sign-off.

## Historical phase-chain state

| Area | Status |
|---|---|
| Phase 13 through Phase 34 control chain | Implemented |
| Phase 35 through Phase 42 write-readiness sequence | Complete as repository readiness/reference evidence |
| External controlled validation handoff pack | Implemented |
| Controlled use acceptance index | Implemented |
| Final release handoff index | Implemented |
| Final repository archive index | Implemented |
| Phase 43 through Phase 48 deployment reference sequence | Implemented as reference/closure evidence |
| Runtime access values | Not stored in repository |
| Live changes | Still held |

Phases 35–48 do not constitute provider mutation code or live authorization. The canonical executable status is maintained in `docs/CAPABILITY_REGISTRY.md`.

## Local validation

```bash
python -m pip install -e ".[test]"
python scripts/validate_repository_structure.py
pytest -q
mkdir -p artifacts
python scripts/validate_controlled_write_foundation.py artifacts/controlled-write-foundation-report.json
```

The existing Phase 13–48 validators and read-only release-manifest validator remain active in GitHub Actions. The workflow artifact package remains:

```text
deployment-planning-reports
```

It now also includes:

```text
controlled-write-foundation-report.json
```

## Current decision index

```text
APPROVE_READ_ONLY_RUNTIME
PROCEED_WITH_TARGETED_IMPLEMENTATION
CONTROLLED_WRITE_FOUNDATION_IMPLEMENTED
DNS_TXT_PILOT_TARGET_PROVISIONING_PREPARED
DNS_TXT_PILOT_GET_ONLY_PREFLIGHT_PASSED
PROTECTED_READONLY_VALIDATION_PASSED
STATUS_SURFACE_WORKFLOW_GET_VALIDATED
NO_AUTONOMOUS_LIVE_CHANGE
RUNTIME_VALUES_OUTSIDE_REPOSITORY
HOLD_LIVE_CHANGE_ACTIVATION
HOLD_PENDING_RUNTIME_STORAGE_AND_DRY_RUN
```

## Repository target

```text
nanotech-solutions-norway/Domeneshop---MCP-
```
