# Domeneshop MCP Canonical Capability Registry — 16:07, 16.07.2026

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
| Domain listing and domain read | IMPLEMENTED | VALIDATED | D-R1 | Protected runs `31384070264` and `31403862923` completed authenticated GETs with payload-free aggregate evidence. |
| DNS listing and record read | IMPLEMENTED | PENDING_REVIEW | D-R1 | GET-only client implemented. |
| HTTP forward listing and read | IMPLEMENTED | PENDING_REVIEW | D-R1 | GET-only client implemented. |
| Sanitized invoice read | IMPLEMENTED | PENDING_REVIEW | D-R1 | Remains read-only. |
| SFTP list, metadata, text read | IMPLEMENTED | PENDING_REVIEW | D-R1 | Allowed-root and directory-list reads passed in runs `31384070264` and `31403862923`; bounded text-file read was not exercised. |
| Local MCP stdio transport and read-only discovery | IMPLEMENTED | VALIDATED | D-R1 | Protected runs `31384070264` and `31403862923` passed initialize/tools-list smoke validation; write tool absent. |
| HTTP/TLS diagnostics | IMPLEMENTED | VALIDATED | D-R1 | Protected workflow run `31403862923` completed a bounded public status GET: HTTP 200, JSON object, no authentication, no payload retained. |
| Deployment dry-run and recovery preview | IMPLEMENTED | VALIDATED_AT_REPOSITORY_LEVEL | Baseline | Does not execute remote changes. |
| Credential placeholder hardening | IMPLEMENTED | VALIDATED | D-R1 | Repository validation and protected credential gates passed in run `31384070264`. |
| Approval token issue/verify/consume | IMPLEMENTED | VALIDATED_AT_REPOSITORY_LEVEL | D-R2 | One-time, HMAC-signed, payload-bound approvals; no live token issued. |
| Idempotency ledger | IMPLEMENTED | VALIDATED_AT_REPOSITORY_LEVEL | D-R2 | File-backed atomic reservation and completion; runtime storage not configured. |
| Append-only audit persistence | IMPLEMENTED | VALIDATED_AT_REPOSITORY_LEVEL | D-R2 | Redaction and hash-chain validation passed; runtime storage not configured. |
| Controlled-write release manifest | IMPLEMENTED | FOUNDATION_ONLY | D-R2 | Example manifest keeps live execution disabled. |
| Shared controlled-write executor | IMPLEMENTED | FOUNDATION_ONLY | D-R2 | No live tool registration on read-only server. |
| DNS TXT provider mutation adapter | IMPLEMENTED | BLOCKED | D-R3 | TXT-only by default; deletion disabled. Isolated domain registration verified on 11.08.2026; authenticated API discovery, isolation validation, and operator acceptance remain pending. |
| HTTP forward mutation adapter | PLANNED | BLOCKED | D-R3 | Starts only after DNS pilot acceptance. |
| SFTP upload/replace/restore | PLANNED | BLOCKED | D-R4 | Requires atomic upload, backup, readback, and restore proof. |
| SQL read/edit/write | PLANNED | BLOCKED | D-R5 | Separate adapter and least-privilege credentials required. |
| Arbitrary shell execution | BLOCKED | BLOCKED | Excluded | Must not be exposed as a general MCP tool. |
| Arbitrary SQL text | BLOCKED | BLOCKED | Excluded | Parameterized allowlisted operations only. |

## Current release boundary

```text
READ_ONLY_SERVER_UNCHANGED
WRITE_TOOLS_ENABLED=false
CONTROLLED_WRITE_FOUNDATION_IMPLEMENTED
LIVE_WRITE_NOT_REGISTERED
DNS_TXT_PILOT_TARGET_PROVISIONING_PREPARED
PROTECTED_READONLY_RUNS_31384070264_AND_31403862923_ACCEPTED
STATUS_SURFACE_WORKFLOW_GET_VALIDATED
HOLD_PENDING_DOMAIN_REGISTRATION
```
