# Domeneshop MCP agent instructions

## Governing records

- Treat `README.md`, `SECURITY.md` and `docs/` as the repository guidance and evidence base.
- Preserve `HOLD_LIVE_CHANGE_ACTIVATION` unless an approved change explicitly supersedes it.
- Never commit provider credentials, tokens, customer data, private runtime values or production secrets.

## Process progress reporting

- Follow `docs/PROCESS_PROGRESS_REPORTING_STANDARD.md` for every operator-facing process.
- After each discrete process or major work step, display a compact cumulative evidence-weighted progress bar with a percentage and brief status label.
- Use `Process status: [██████░░░░] 60% — <brief status>` as the default compact format; do not emit a bar for every low-level tool call or internal substep.
- Display the compact bar after successful, partial, blocked and failed processes. Failed or blocked work does not increase the percentage unless it closes a verified weighted gate.
- The exact standalone `Status` command remains the trigger for the expanded completed/ongoing/remaining status block; it is no longer the exclusive trigger for showing progress.
- Calculate progress from verified weighted milestones only.
- Recalculate explicitly when scope changes.
- Carry the current percentage into status records, transfer packs and continuation prompts.
- A progress percentage never authorizes deployment, provider calls, live changes or write enablement.

## Execution boundary

Do not activate live changes, alter production DNS or hosting state, enable write paths, or perform provider mutations without the applicable evidence and explicit operator authorization.