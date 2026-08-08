# Domeneshop MCP Progress Reporting Governance Revision — 21:03, 08.08.2026

## Classification

APPROVED operator governance revision.

## Decision

Domeneshop MCP now displays a compact cumulative percentage progress bar after each discrete process or major work step.

```text
Process status: [██████░░░░] 60% — <brief status>
```

The percentage remains evidence-weighted against the active approved completion target. Failed or blocked work does not increase progress unless it closes a verified weighted gate.

The exact standalone `Status` command remains available for the expanded completed/ongoing/remaining report, but it is no longer the exclusive trigger for displaying progress.

## Superseded rule

The 05.08.2026 trigger-only rule requiring ordinary processes to omit the status bar is superseded.

## Preserved constraints

- `HOLD_LIVE_CHANGE_ACTIVATION` remains unchanged unless separately approved.
- Operator approval gates remain unchanged.
- Progress never authorizes provider calls, production DNS/hosting mutation, live changes or write enablement.
- No credentials, tokens, customer data or production secrets are added by this revision.

## Validation

Documentation-only governance change applied on a feature branch for draft-PR review. No runtime code or provider state changed.