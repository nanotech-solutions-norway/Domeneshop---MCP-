# MCP Process Progress Reporting Standard

This repository adopts the NanoTech Solutions Norway cross-project MCP progress-reporting standard.

## Exact trigger rule

Display the Domeneshop MCP status bar and short process summary only when the user's complete message, after trimming surrounding whitespace, is exactly:

```text
Status
```

Treat the standalone command case-insensitively. Do not trigger the status block when the message contains any other words, punctuation, request, instruction, mention or context.

Examples that do not trigger the special status block include `Status please`, `Project status`, `What's the status?`, `Status @GitHub`, and `Continue and show status`.

Do not automatically show a progress bar after an ordinary successful, partial, blocked or failed process. Maintain progress in canonical records and show it in chat only after the exact standalone command.

## Required status-command response

The standalone `Status` response must contain:

1. the applicable Domeneshop MCP completion target;
2. the current evidence-weighted percentage and 20-character bar;
3. a short description of completed processes;
4. a short description of the ongoing process;
5. a short description of remaining processes;
6. the next evidence gate;
7. the preserved safety state.

## Calculation

- Use the approved rollout plan and weighted evidence gates as the denominator.
- Count only verified evidence and accepted completion markers.
- Failed or blocked processes do not increase progress.
- Partial credit is allowed only for independently defined and verified substeps.
- Do not calculate progress from elapsed time, message count, file count or subjective effort.
- Recalculate explicitly when the approved target or scope changes.
- Never show 100 percent before closure evidence, rollback or recovery evidence, documentation and operator handoff are complete.

## Status-command display

Use a 20-character bar. The numeric percentage is authoritative.

```text
STATUS — Domeneshop MCP
Target: <completion target>
Progress: [████████░░░░░░░░░░░░] 40%
Completed: <short description>
Ongoing: <short description>
Remaining: <short description>
Next gate: <next evidence gate>
Safety: <preserved safety state>
```

## Domeneshop MCP targets

Track separate percentages where applicable:

1. validated read-only runtime;
2. controlled DNS or hosting change capability;
3. controlled edit capability;
4. production activation and rollback validation;
5. full project closure.

Do not merge these targets into one unexplained percentage.

## Safety boundary

Progress never grants deployment, provider-call, live-change or write-enablement authority. Existing explicit operator gates remain mandatory.

## Status and handoff records

Every new rollout record, status update, transfer pack and continuation prompt must keep the current target, percentage, current process and next gate. The operator-facing status bar remains hidden unless the exact standalone `Status` command is received.