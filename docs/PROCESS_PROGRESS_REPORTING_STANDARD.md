# MCP Process Progress Reporting Standard

This repository adopts the NanoTech Solutions Norway cross-project MCP progress-reporting standard.

## Mandatory rule

After every discrete process result, report a percentage status bar for the stated completion target. Apply the rule to successful, partial, blocked and failed processes.

## Calculation

- Use the approved rollout plan and weighted evidence gates as the denominator.
- Count only verified evidence and accepted completion markers.
- Failed or blocked processes do not increase progress.
- Partial credit is allowed only for independently defined and verified substeps.
- Do not calculate progress from elapsed time, message count, file count or subjective effort.
- Recalculate explicitly when the approved target or scope changes.
- Never show 100 percent before closure evidence, rollback or recovery evidence, documentation and operator handoff are complete.

## Display

Use a 20-character bar. The numeric percentage is authoritative.

```text
PROCESS PROGRESS
Target: <completion target>
Overall: [████████░░░░░░░░░░░░] 40%
Verified weight: 40/100
Process: <process name>
Result: PASSED | PARTIAL | BLOCKED | FAILED
Change: +<n>% | unchanged | recalculated
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

Every new rollout record, status update, transfer pack and continuation prompt must include the current target, percentage, current process and next gate.