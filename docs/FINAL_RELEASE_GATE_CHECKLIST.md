# Final Release Gate Checklist

## Purpose

This checklist defines the final evidence package for the Domeneshop MCP bridge before accepting read-only runtime operation.

## Required validation commands

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
python scripts/dry_run_plan.py --source-root . --target-root /www --output phase5-dry-run-report.json
python scripts/recovery_plan.py --dry-run-report phase5-dry-run-report.json --backup-root /www/backups/dry-run --backup-output phase6-backup-evidence-report.json --restore-output phase6-restore-preview-report.json
python scripts/change_preflight.py --output phase7-change-preflight-report.json
python scripts/readiness_preflight.py --output phase8-readiness-preflight-report.json
python scripts/runtime_deployment_validate.py --repo-root . --output phase9-runtime-deployment-validation-report.json
python scripts/operations_validate.py --repo-root . --output phase10-operations-validation-report.json
python scripts/estate_validate.py --registry config/estate-targets.example.json --output phase11-estate-validation-report.json
python scripts/final_release_gate.py --repo-root . --output phase12-final-release-gate-report.json
```

## Required artifact package

```text
deployment-planning-reports
```

Expected files:

```text
phase5-dry-run-report.json
phase6-backup-evidence-report.json
phase6-restore-preview-report.json
phase7-change-preflight-report.json
phase8-readiness-preflight-report.json
phase9-runtime-deployment-validation-report.json
phase10-operations-validation-report.json
phase11-estate-validation-report.json
phase12-final-release-gate-report.json
```

## Final decision

```text
APPROVE_READ_ONLY_RUNTIME
HOLD_FOR_FIX
```

## Current intended decision

```text
APPROVE_READ_ONLY_RUNTIME
```

## Explicit boundary

The final gate does not approve provider-side changes, hosted-file transfers, recovery execution, or shell execution.
