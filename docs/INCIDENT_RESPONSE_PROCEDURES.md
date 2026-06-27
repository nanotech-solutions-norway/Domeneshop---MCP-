# Incident Response Procedures

## Purpose

This document defines incident handling for the Domeneshop MCP bridge.

## Incident classes

| Class | Description | Initial action |
|---|---|---|
| CI failure | GitHub Actions validation fails | Stop phase progression |
| Runtime failure | MCP server does not start | Keep offline and review logs |
| Provider access failure | Read-only provider call fails | Verify runtime values outside repo |
| Path guard event | Expected path is blocked | Review allowed roots and path input |
| Degraded endpoint | Health check reports degraded status | Review upstream service state |
| Unexpected action exposure | A live change tool appears | Stop server and block release |

## Immediate containment

1. Stop phase progression.
2. Do not enable change mode.
3. Preserve workflow logs and artifacts.
4. Preserve runtime logs according to host policy.
5. Confirm `WRITE_TOOLS_ENABLED=false`.
6. Confirm no live change tool is registered in `server.py`.

## Evidence package

Collect:

```text
GitHub Actions run URL
workflow logs
all planning artifacts
runtime readiness report
runtime deployment validation report
server startup logs
operator notes
```

## Triage sequence

1. Classify incident type.
2. Confirm whether production runtime is affected.
3. Confirm whether provider read access is affected.
4. Confirm whether path guard or allowed roots are involved.
5. Confirm whether a configuration drift occurred.
6. Decide whether rollback planning evidence is required.

## Rollback decision tree

```text
Did a live change occur?
  No  -> No restore action. Fix config/code and rerun validation.
  Yes -> Stop runtime, collect evidence, use recovery preview, require manual release review.

Is the issue only CI/test related?
  Yes -> Patch repository and rerun validation.
  No  -> Continue runtime triage.

Is read-only runtime degraded?
  Yes -> Stop server if repeated errors persist.
  No  -> Continue monitoring and document.
```

## Release hold criteria

Hold release if any of the following is true:

```text
CI is not green
planning artifact is missing
readiness report failed unexpectedly
runtime deployment validation failed
unexpected tool registration detected
operator approval reference is missing for future change phase
```

## Closure requirements

1. Root cause recorded.
2. Corrective commit linked.
3. Validation rerun on latest main.
4. Artifact package reviewed.
5. Operator confirms no live change occurred.
