# Domeneshop MCP agent instructions

## Governing records

- Treat `README.md`, `SECURITY.md` and `docs/` as the repository guidance and evidence base.
- Preserve `HOLD_LIVE_CHANGE_ACTIVATION` unless an approved change explicitly supersedes it.
- Never commit provider credentials, tokens, customer data, private runtime values or production secrets.

## Process progress reporting

- Follow `docs/PROCESS_PROGRESS_REPORTING_STANDARD.md` for every operator-facing process.
- End each discrete process result with a percentage progress bar, stated completion target, result and next evidence gate.
- Calculate progress from verified weighted milestones only.
- Failed or blocked processes do not increase the percentage.
- Recalculate explicitly when scope changes.
- Carry the current percentage into status records, transfer packs and continuation prompts.
- A progress percentage never authorizes deployment, provider calls, live changes or write enablement.

## Execution boundary

Do not activate live changes, alter production DNS or hosting state, enable write paths, or perform provider mutations without the applicable evidence and explicit operator authorization.