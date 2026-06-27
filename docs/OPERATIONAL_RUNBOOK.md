# Operational Runbook

## Purpose

This runbook defines routine operation for the Domeneshop MCP bridge in read-only and planning mode.

## Operating posture

```text
READ_AND_PLAN_ONLY
CHANGE_ACTIONS_NOT_REGISTERED
OPERATOR_APPROVAL_REQUIRED_FOR_FUTURE_RELEASE
```

## Daily operator checklist

1. Confirm latest GitHub Actions validation is green.
2. Download `deployment-planning-reports` artifact.
3. Review Phase 5 dry-run report.
4. Review Phase 6 recovery planning reports.
5. Review Phase 7 control report.
6. Review Phase 8 readiness report.
7. Review Phase 9 runtime deployment report.
8. Confirm runtime values are stored outside the repository.
9. Confirm `WRITE_TOOLS_ENABLED=false` before starting the server.
10. Confirm `DRY_RUN_DEFAULT=true` before starting the server.

## Startup procedure

```bash
python -m pip install -e ".[server,sftp]"
python scripts/readiness_preflight.py --output phase8-readiness-preflight-report.json
python scripts/runtime_deployment_validate.py --repo-root . --output phase9-runtime-deployment-validation-report.json
domeneshop-mcp-server
```

## Shutdown procedure

1. Stop the MCP host process.
2. Preserve the latest runtime logs according to the host policy.
3. Preserve the latest planning artifacts.
4. Confirm no live change action was registered during runtime.

## Runtime value rotation procedure

1. Stop the MCP server.
2. Rotate provider values in the external runtime store.
3. Do not commit runtime values to the repository.
4. Restart the MCP server.
5. Run read-only smoke checks.
6. Save the new readiness report.

## Read-only smoke checks

```bash
python scripts/domeneshop_read_smoke.py
python scripts/remote_read_smoke.py
python scripts/health_smoke.py
```

## Artifact review order

```text
phase5-dry-run-report.json
phase6-backup-evidence-report.json
phase6-restore-preview-report.json
phase7-change-preflight-report.json
phase8-readiness-preflight-report.json
phase9-runtime-deployment-validation-report.json
```

## Escalation triggers

Escalate to manual review if:

```text
workflow validation fails
runtime value check fails
read-only smoke check fails
unexpected live action appears
path guard rejects expected path
HTTP diagnostics show degraded service
planning reports show blocked paths
```

## Current release position

```text
PHASE_10_OPERATIONAL_RUNBOOK_ADDED
LIVE_CHANGE_OPERATIONS_NOT_REGISTERED
```
