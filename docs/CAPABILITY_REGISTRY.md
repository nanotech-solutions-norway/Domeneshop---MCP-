# Domeneshop MCP Canonical Capability Registry — 24.08.2026

This registry replaces ambiguous phase-completion language with executable capability states.

## Status vocabulary

- `IMPLEMENTED`: executable code exists.
- `VALIDATED`: executable code has passed the defined test in the relevant environment.
- `OPERATOR_ACCEPTED`: the operator reviewed evidence and accepted the result.
- `PLANNED`: design or documentation exists but executable behavior is absent.
- `REFERENCE_ONLY`: an index or handoff reference; it does not implement behavior.
- `PENDING_REVIEW`: evidence is incomplete, stale, conflicting, or requires owner validation.
- `BLOCKED`: prohibited or missing mandatory controls.

## Registry

| Capability | Repository state | Runtime state | Release train | Notes |
|---|---|---|---|---|
| Domain listing and domain read | IMPLEMENTED | VALIDATED | D-R1 | Authenticated GET validation accepted. |
| DNS listing and record read | IMPLEMENTED | OPERATOR_ACCEPTED | D-R1 / D-R3 | Exercised repeatedly during isolated DNS TXT preflight and independent readback. |
| HTTP forward listing and read | IMPLEMENTED | PENDING_REVIEW | D-R1 / D-R4B | GET-only client exists. Exact isolated preflight validation is the next gate in Issue #56. |
| Sanitized invoice read | IMPLEMENTED | PENDING_REVIEW | D-R1 | Remains read-only. |
| SFTP list, metadata, text read | IMPLEMENTED | OPERATOR_ACCEPTED | D-R1 / D-R4 | Exact isolated-file read/readback accepted during D-R4. |
| Local MCP stdio transport and read-only discovery | IMPLEMENTED | VALIDATED | D-R1 | Protected initialize/tools-list smoke validation accepted; write tools remain absent by default. |
| HTTP/TLS diagnostics | IMPLEMENTED | VALIDATED | D-R1 | Bounded public status GET validation accepted. |
| Deployment dry-run and recovery preview | IMPLEMENTED | VALIDATED | Baseline | Does not execute remote changes by default. |
| Credential placeholder hardening | IMPLEMENTED | VALIDATED | D-R1 | Repository and protected credential gates accepted. |
| Approval token issue/verify/consume | IMPLEMENTED | VALIDATED | D-R2 | One-time, HMAC-signed, payload-bound approvals. |
| Idempotency ledger | IMPLEMENTED | VALIDATED | D-R2 | File-backed atomic reservation/completion foundation accepted. |
| Append-only audit persistence | IMPLEMENTED | VALIDATED | D-R2 | Redaction and hash-chain validation accepted. |
| Controlled-write release manifest | IMPLEMENTED | VALIDATED | D-R2 | Runtime release bindings remain exact-scope and fail closed. |
| Shared controlled-write executor | IMPLEMENTED | VALIDATED | D-R2 | Used by controlled DNS validation; no general live write registration. |
| Isolated DNS TXT target preflight | IMPLEMENTED | OPERATOR_ACCEPTED | D-R3 | Exact sandbox target accepted. |
| Isolated DNS TXT controlled-write dry run | IMPLEMENTED | OPERATOR_ACCEPTED | D-R3 | Deterministic dry-run accepted. |
| DNS TXT CREATE/UPDATE/RESTORE pilot | IMPLEMENTED | OPERATOR_ACCEPTED | D-R3 | Exact isolated sandbox sequence accepted; final state restored to accepted CREATE state. TXT DELETE remains unauthorized. |
| General DNS mutation | IMPLEMENTED | BLOCKED | D-R3 | No MX, NS, general record mutation, general delete, or global write activation authorized. |
| HTTP forward isolated target preflight | IMPLEMENTED | PENDING_REVIEW | D-R4B | GET-only collision preflight introduced under Issue #56; no POST/PUT/DELETE authorization. |
| HTTP forward CREATE/UPDATE/RESTORE pilot | PLANNED | BLOCKED | D-R4B | Starts only after GET-only preflight and deterministic dry-run acceptance plus separate operator authorization for each mutation. DELETE separately gated. |
| SFTP CREATE/UPDATE/RESTORE pilot | IMPLEMENTED | OPERATOR_ACCEPTED | D-R4 | Exact isolated file sequence accepted. Final provider state is accepted CREATE state. |
| General SFTP write/delete/rename | PLANNED | BLOCKED | D-R4 | D-R4 acceptance does not authorize arbitrary upload, overwrite, delete, rename, or production file deployment. |
| SQL read/edit/write | PLANNED | BLOCKED | D-R5 | Separate adapter, least-privilege credentials, isolated target, and controlled validation required. |
| Arbitrary shell execution | BLOCKED | BLOCKED | Excluded | Must not be exposed as a general MCP tool. |
| Arbitrary SQL text | BLOCKED | BLOCKED | Excluded | Parameterized allowlisted operations only. |

## Security/governance state

```text
GITHUB_SECURITY_REVIEW_COMPLETE=true
MAIN_BRANCH_RULESET_ACTIVE=true
SECRET_SCANNING_CLEAR=true
CODE_SCANNING_OPEN_ALERTS=0
SINGLE_OPERATOR_COMPENSATING_CONTROLS_ACCEPTED=true
```

## Current release boundary

```text
D_R3_DNS_COMPLETE=true
D_R4_SFTP_COMPLETE=true
D_R4B_HTTP_FORWARD_PREFLIGHT=IN_PROGRESS
D_R5_SQL=BLOCKED_PENDING_PRIOR_GATE
HOLD_LIVE_CHANGE_ACTIVATION
NO_AUTONOMOUS_LIVE_CHANGE
WRITE_TOOLS_ENABLED=false
HTTP_FORWARD_CREATE_AUTHORIZED=false
HTTP_FORWARD_UPDATE_AUTHORIZED=false
HTTP_FORWARD_DELETE_AUTHORIZED=false
GENERAL_SFTP_WRITE_AUTHORIZED=false
GENERAL_DNS_WRITE_AUTHORIZED=false
SQL_WRITE_AUTHORIZED=false
```
