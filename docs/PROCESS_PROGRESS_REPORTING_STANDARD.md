# MCP Process Progress Reporting Standard

This repository adopts the NanoTech Solutions Norway cross-project MCP progress-reporting standard.

## Mandatory per-process progress display

After every discrete process or major work step in a Domeneshop MCP workflow, display a compact cumulative evidence-weighted progress bar with a percentage and short status label.

Default format:

```text
Process status: [██████░░░░] 60% — <brief status>
```

A process is a coherent operator-facing work unit or major step, not every low-level tool call, file read, API request or internal substep.

Show the compact bar after successful, partial, blocked and failed processes. Failed or blocked work does not increase the percentage unless it closes a previously incomplete verified evidence gate.

## Standalone Status command

The exact standalone `Status` command remains the trigger for the expanded Domeneshop MCP status block; it is no longer the exclusive trigger for displaying progress.

The expanded response must contain:

1. the applicable Domeneshop MCP completion target;
2. the current evidence-weighted percentage and expanded bar;
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

## Expanded Status display

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

Every new rollout record, status update, transfer pack and continuation prompt must keep the current target, percentage, current process and next gate. The compact operator-facing progress bar is mandatory after each discrete process or major work step.

## Superseding governance revision — 08.08.2026

This revision supersedes the 05.08.2026 trigger-only rule that hid progress during ordinary processes. The standalone `Status` command remains the expanded reporting command, while compact progress bars are now displayed by default after each discrete process or major work step.