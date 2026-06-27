# Phase 13 Risk Register and Scope — 11:40, 27.06.2026

## Release position

**Phase 13 is scope definition and risk-control documentation only.** It does not activate live write capabilities, deployment execution, production SSH execution, DNS mutation, file upload, file overwrite, restore execution, or invoice/account changes.

```text
Phase: 13
Status: DISABLED_BY_DEFAULT
Release decision: HOLD_PHASE13_ACTIVATION
Operational mode: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Approval class: PENDING_EXPLICIT_RELEASE_APPROVAL
```

## Objective

Phase 13 defines the controlled boundary for a possible future live-change lane in the Domeneshop MCP bridge. The immediate purpose is to keep the current release safe while documenting risk, scope, acceptance criteria, and the validation evidence required before any later activation can be considered.

## Current mandatory constraints

- Phase 13 must remain disabled by default in repository files, example configuration, CI, runtime scaffolds, and MCP server registration.
- Existing safety defaults remain binding: write tools disabled, dry-run enabled, operator approval required, backup evidence required, and preflight report required.
- No production credential, token, SSH key, API secret, customer/accounting detail, or private hosting value may be stored in the repository.
- No write-capable MCP tool may be registered until a separate explicit release decision authorizes it.
- Domeneshop REST API usage remains limited to the documented API surface; website file operations must use SFTP/SCP/FTP where access permits.
- GitHub Actions remains the preferred controlled deployment lane for any future release package.

## In scope for Phase 13

| Area | Included work | Activation impact |
|---|---|---|
| Risk register | Identify live-change, DNS, file-transfer, SSH, rollback, credential, and approval risks. | None |
| Scope boundary | Define what a future live-change lane may and may not include. | None |
| Default-disabled validation | Provide a script that fails if Phase 13 appears enabled in operational defaults. | Preventive only |
| Acceptance gates | Define minimum checks before a later release can activate live changes. | Documentation only |
| Evidence model | Define required reports and audit evidence for future review. | Documentation only |

## Out of scope for Phase 13 until separately approved

- Creating, updating, or deleting Domeneshop DNS records.
- Creating, updating, or deleting HTTP forwards or DDNS configuration.
- Uploading, overwriting, deleting, or restoring website files on Domeneshop hosting.
- Running shell commands against Domeneshop hosting or any production host.
- Executing production deployments from MCP tools.
- Registering write-capable tools in `src/domeneshop_mcp/server.py`.
- Storing or exposing runtime secrets, hosting credentials, customer data, invoice detail, or private logs.
- Bypassing GitHub Actions, review, backup evidence, or preflight controls.

## Risk register

| ID | Risk | Severity | Likelihood before controls | Required controls | Current Phase 13 decision |
|---|---:|---:|---:|---|---|
| R13-001 | Accidental live DNS mutation causes service outage. | High | Medium | Explicit approval, DNS dry-run diff, record-level allowlist, rollback plan, post-change verification. | Hold activation |
| R13-002 | Website file overwrite breaks a hosted service. | High | Medium | Manifest diff, backup evidence, path jail, checksum validation, restore preview, GitHub Actions execution lane. | Hold activation |
| R13-003 | Secrets or credentials are committed to repository. | Critical | Low | Placeholder-only config, secret scanning, protected variables, runtime-only values. | Hold activation |
| R13-004 | Operator approval is bypassed by automation. | Critical | Medium | Approval gate, release checklist, audit event, protected environment, manual dispatch with reviewer. | Hold activation |
| R13-005 | Restore procedure is incomplete during incident. | High | Medium | Tested backup manifest, restore preview, recovery report, incident runbook. | Hold activation |
| R13-006 | Wrong domain, subdomain, or hosting root is targeted. | High | Medium | Estate registry, target allowlist, path jail, preflight target summary, operator confirmation. | Hold activation |
| R13-007 | CI/workflow drift activates a live path unintentionally. | High | Low | Disabled-default validation, workflow review, artifact review, release decision string checks. | Hold activation |
| R13-008 | Optional SSH diagnostics become command execution. | Critical | Medium | Read-only diagnostic scope, explicit SSH exclusion, separate approval for any command lane. | Hold activation |
| R13-009 | Invoice or account data is exposed in logs or reports. | High | Low | Sanitized output, no private values in artifacts, minimum necessary metadata. | Hold activation |
| R13-010 | Documentation becomes stale and conflicts with runtime behavior. | Medium | Medium | CI validation, README update, final gate review, dated transfer report. | Hold activation |

## Future activation prerequisites

A future release may only move beyond disabled-by-default if all prerequisites below are satisfied in a separate phase and accepted by explicit approval.

1. A separate release document changes the decision from `HOLD_PHASE13_ACTIVATION` to a clearly named approval decision.
2. Threat model and rollback plan are complete and reviewed.
3. Write-capable functions remain behind explicit configuration gates and are not active in example configuration.
4. CI validates disabled defaults, secret hygiene, dry-run behavior, path jail behavior, and approval-gate behavior.
5. GitHub Actions workflow uses protected environments for any live action.
6. Live target allowlists are defined in configuration examples without real credentials.
7. Backup evidence and restore preview are mandatory for file-impacting operations.
8. DNS-impacting operations produce before/after diffs and rollback records.
9. Audit events are generated for every approval, rejection, and execution attempt.
10. Production credentials are stored only in approved secret stores outside the repository.

## Validation command

```bash
python scripts/phase13_disabled_default_validate.py --repo-root . --output phase13-disabled-default-validation-report.json
```

Expected summary:

```text
phase13_default: DISABLED
release_decision: HOLD_PHASE13_ACTIVATION
passed: true
```

## Acceptance criteria for this phase

| Check | Required result |
|---|---|
| Risk register exists | `docs/PHASE13_RISK_REGISTER_AND_SCOPE.md` present |
| Disabled-default validator exists | `scripts/phase13_disabled_default_validate.py` present |
| Write defaults remain locked | Existing environment template remains disabled/dry-run/approval-gated |
| MCP server remains read/planning only | No live mutation or upload tools registered |
| CI can execute the validator | Workflow includes the disabled-default validator |

## Final Phase 13 position

Phase 13 is approved only as a documentation and guard-validation layer. The bridge remains a read-only runtime with planning, validation, preflight, and recovery evidence tooling. Live change activation remains on hold pending a separate explicit release phase.