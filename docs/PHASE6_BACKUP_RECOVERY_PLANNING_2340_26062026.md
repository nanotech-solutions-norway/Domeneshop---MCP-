# Phase 6 Recovery Planning — 23:40, 26.06.2026

## Scope

Phase 6 adds planning-only recovery evidence.

Implemented capabilities:

```text
backup evidence manifest model
changed-file backup candidate detection
backup path planning
restore-preview planning
workflow artifact generation
planning-only MCP handlers
```

## Added files

```text
src/domeneshop_mcp/recovery_plan.py
src/domeneshop_mcp/tools_recovery_plan.py
scripts/recovery_plan.py
tests/test_recovery_plan.py
```

## MCP tools registered

```text
recovery_build_backup_manifest
recovery_build_restore_preview
```

These tools only create planning data.

## GitHub Actions update

The validation workflow now emits one combined artifact package:

```text
deployment-planning-reports
```

Included files:

```text
artifacts/phase5-dry-run-report.json
artifacts/phase6-backup-evidence-report.json
artifacts/phase6-restore-preview-report.json
```

## Safety position

Phase 6 is planning-only and performs no live remote file change.

Planning reports include:

```json
{
  "will_write": false,
  "live_restore": false
}
```

## Local validation

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
python scripts/dry_run_plan.py --source-root . --target-root /www --output phase5-dry-run-report.json
python scripts/recovery_plan.py --dry-run-report phase5-dry-run-report.json --backup-root /www/backups/dry-run --backup-output phase6-backup-evidence-report.json --restore-output phase6-restore-preview-report.json
```

## Status

```text
PHASE_6_IMPLEMENTED_PENDING_CI_VALIDATION
WRITE_TOOLS_REMAIN_PAUSED
```
