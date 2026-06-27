# Release Approval Checklist

## Purpose

This checklist defines the evidence required before advancing beyond read-only and planning operation.

## Mandatory evidence

```text
GitHub Actions validation green on latest main
phase5-dry-run-report.json reviewed
phase6-backup-evidence-report.json reviewed
phase6-restore-preview-report.json reviewed
phase7-change-preflight-report.json reviewed
phase8-readiness-preflight-report.json reviewed
phase9-runtime-deployment-validation-report.json reviewed
operational runbook reviewed
incident response procedure reviewed
```

## Runtime safety checks

```text
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
```

## Tool registration checks

Confirm server exposes only:

```text
read tools
diagnostics tools
planning tools
recovery planning tools
control-plane tools
```

Confirm server does not expose:

```text
DNS mutation tools
HTTP forwarding mutation tools
hosted-file transfer tools
restore execution tools
shell command tools
```

## Operator approval section

```text
Operator name:
Approval reference:
Approved scope:
Approved timestamp:
Validation run URL:
Artifact package reviewed: yes/no
```

## Release decision

```text
APPROVE_READ_ONLY_RUNTIME
HOLD_FOR_FIX
REJECT_LIVE_CHANGE_ACTIVATION
```

## Current expected decision

```text
APPROVE_READ_ONLY_RUNTIME
REJECT_LIVE_CHANGE_ACTIVATION
```
