# Phase 14 Activation Readiness Gate — 11:48, 27.06.2026

## Release position

**Phase 14 is an activation-readiness gate, not an activation phase.** It formalizes the approval matrix, evidence package, and live-change release prerequisites required before any future write-capable functionality can be considered.

```text
Phase: 14
Status: READINESS_GATE_ONLY
Release decision: HOLD_LIVE_CHANGE_ACTIVATION
Phase 13 carry-forward: HOLD_PHASE13_ACTIVATION
Operational mode: READ_ONLY_RUNTIME_PLUS_PLANNING_GUARDS
Approval class: PENDING_EXPLICIT_RELEASE_APPROVAL
```

## Objective

Phase 14 converts the Phase 13 risk register into a practical release gate. It defines who must approve, what evidence must exist, which controls must remain enforced, and which technical indicators would block any future activation attempt.

The immediate release outcome remains unchanged: no live change tools are registered, no write-capable operations are enabled, and the MCP bridge remains read-only plus planning/preflight/recovery-preview.

## Gate scope

| Area | Phase 14 action | Activation impact |
|---|---|---|
| Approval matrix | Define minimum approvals by operation class. | None |
| Evidence package | Define mandatory artifacts before live activation review. | None |
| Blocking conditions | Define conditions that must prevent activation. | Preventive only |
| Validator | Add CI-runnable check for required gate markers and disabled defaults. | Preventive only |
| Documentation update | Expose the phase in README and validation workflow. | None |

## Approval matrix

| Operation class | Examples | Minimum approval before future activation | Evidence required | Current decision |
|---|---|---|---|---|
| DNS read | List domains, inspect DNS records. | Existing read-only approval. | Normal read audit output. | Allowed |
| DNS write | Create/update/delete DNS records, change HTTP forwards, DDNS update. | Explicit release approval + operator confirmation per change. | DNS diff, rollback record, target allowlist, post-change health check. | Held |
| Hosted-file read | List files, read metadata, read permitted text files. | Existing read-only approval. | Path-jail validation and sanitized output. | Allowed |
| Hosted-file write | Upload, overwrite, delete, restore files. | Explicit release approval + protected environment review. | Manifest diff, backup evidence, restore preview, checksum plan, post-change health check. | Held |
| Deployment execution | Apply a deployment plan to `/www` or subroots. | Explicit release approval + GitHub Actions protected environment. | Dry-run artifact, backup artifact, approval event, deployment artifact, rollback plan. | Held |
| SSH diagnostics | Non-mutating inspection where hosting permits. | Separate read-only SSH diagnostics approval. | Command allowlist and sanitized output. | Held unless separately approved |
| SSH command execution | Any command capable of mutation, restart, write, install, delete, or permission change. | Separate high-risk release approval. | Full threat model, reviewed command allowlist, rollback plan, incident plan. | Held |
| Invoice/account operations | Invoice retrieval or account-impacting changes. | Separate data governance and privacy review. | Data-minimization plan and sanitized reports. | Held |

## Mandatory evidence package for any future live-change review

Before any future phase may propose activation, the repository or protected CI artifacts must include:

1. Updated risk register with all Phase 13 risks resolved, accepted, or mitigated.
2. Final activation release document with a decision string other than a hold state.
3. Dry-run report for the exact planned operation class.
4. Backup evidence report for file-impacting operations.
5. Restore preview report for file-impacting operations.
6. DNS rollback record for DNS-impacting operations.
7. Target allowlist for domains, subdomains, and remote roots.
8. CI report confirming disabled defaults remain unchanged in examples.
9. Operator approval record.
10. Incident response and rollback owner assignment.
11. Post-change validation plan.
12. Evidence that production credentials remain outside the repository.

## Blocking conditions

Any one of the following blocks live activation:

- `WRITE_TOOLS_ENABLED` is `true` in repository examples.
- `DRY_RUN_DEFAULT` is not `true` in repository examples.
- Operator approval is not required.
- Backup evidence or preflight evidence is not required.
- Write-capable MCP tools are registered in `src/domeneshop_mcp/server.py`.
- CI omits Phase 13 or Phase 14 guard validation.
- Activation approval is ambiguous, implicit, or only inferred from documentation.
- Credentials, tokens, SSH keys, private customer data, invoice detail, or hosting values are present in repository files.
- The target domain/root allowlist is missing or contains private runtime values.
- Rollback evidence is unavailable for the operation class.

## Required decision strings

The current release must continue to include these hold decisions:

```text
HOLD_LIVE_CHANGE_ACTIVATION
HOLD_PHASE13_ACTIVATION
HOLD_PHASE14_ACTIVATION_READINESS_ONLY
```

Any future activation release must remove ambiguity by replacing the Phase 14 hold state with a specific, dated, reviewed decision. A generic phrase such as "approved" is not sufficient.

## Validation command

```bash
python scripts/phase14_activation_readiness_validate.py --repo-root . --output phase14-activation-readiness-validation-report.json
```

Expected summary:

```text
phase14_gate: READINESS_ONLY
release_decision: HOLD_LIVE_CHANGE_ACTIVATION
passed: true
```

## Acceptance criteria for Phase 14

| Check | Required result |
|---|---|
| Phase 14 document exists | `docs/PHASE14_ACTIVATION_READINESS_GATE.md` present |
| Phase 13 remains held | Phase 13 document still contains `HOLD_PHASE13_ACTIVATION` |
| Phase 14 remains readiness-only | Phase 14 document contains `READINESS_GATE_ONLY` and `HOLD_PHASE14_ACTIVATION_READINESS_ONLY` |
| Safety defaults remain locked | Example config keeps write tools disabled, dry-run default true, approval required, backup evidence required, and preflight required |
| Server remains read/planning only | No write, upload, restore-execution, deployment-apply, DNS mutation, or SSH execution tools registered |
| Workflow validates Phase 14 | CI generates a Phase 14 activation-readiness report |

## Final Phase 14 position

Phase 14 is complete only when it proves the project is ready to discuss activation without actually activating it. The operational release remains read-only plus planning, validation, preflight, and recovery-preview. Live change activation remains held until a separate explicit release phase is created, reviewed, and approved.