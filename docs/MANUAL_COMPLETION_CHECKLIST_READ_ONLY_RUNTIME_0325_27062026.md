# Manual Completion Checklist — Read-Only Runtime — 03:25, 27.06.2026

## Purpose

This checklist defines what must be done manually outside the repository to complete the validated read-only runtime operation.

## 1. GitHub Actions artifact review

1. Open GitHub Actions.
2. Run the validation workflow on latest `main` if it has not already been run.
3. Download the artifact package:

```text
deployment-planning-reports
```

4. Confirm the artifact package includes:

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
read-only-release-manifest-validation-report.json
```

## 2. Runtime configuration

1. Copy `config/mcp-client.example.json` into the MCP client configuration location.
2. Configure provider access values only in the runtime environment.
3. Do not commit runtime values to the repository.
4. Confirm these runtime settings:

```text
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
```

## 3. Runtime access values

Configure the required values outside the repository:

```text
DS_AUTH_USER
DS_AUTH_VALUE
DS_SFTP_USER
DS_SFTP_VALUE
```

## 4. Install package

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[server,sftp]"
```

## 5. Run preflight checks

```bash
python scripts/readiness_preflight.py --output phase8-readiness-preflight-report.json
python scripts/runtime_deployment_validate.py --repo-root . --output phase9-runtime-deployment-validation-report.json
python scripts/release_manifest_validate.py --manifest config/read-only-release-manifest.example.json --output read-only-release-manifest-validation-report.json
```

## 6. Start runtime

```bash
domeneshop-mcp-server
```

Alternative:

```bash
python -m domeneshop_mcp.server
```

## 7. Run smoke checks

```bash
python scripts/domeneshop_read_smoke.py
python scripts/remote_read_smoke.py
python scripts/health_smoke.py
```

## 8. Preserve evidence

Preserve:

```text
startup logs
smoke check outputs
readiness report
runtime deployment report
release manifest validation report
deployment-planning-reports artifact package
```

## 9. Acceptance decision

Expected decision:

```text
APPROVE_READ_ONLY_RUNTIME
HOLD_LIVE_CHANGE_ACTIVATION
```

## 10. Boundary

Do not enable future provider-side operations until Phase 13 has been implemented, validated, and explicitly approved as a separate release phase.
