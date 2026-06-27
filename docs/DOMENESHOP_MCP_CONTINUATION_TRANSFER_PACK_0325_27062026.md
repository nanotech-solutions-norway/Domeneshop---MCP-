# Domeneshop MCP Continuation Transfer Pack — 03:25, 27.06.2026

## Purpose

Use this transfer pack to continue the Domeneshop MCP project in a new ChatGPT project thread.

## Repository

```text
nanotech-solutions-norway/Domeneshop---MCP-
```

## Current release position

```text
READ_ONLY_RUNTIME_RELEASE_PACKAGE_VALIDATED_BY_OPERATOR
APPROVE_READ_ONLY_RUNTIME
HOLD_LIVE_CHANGE_ACTIVATION
LIVE_CHANGE_OPERATIONS_NOT_REGISTERED
```

## What has been completed

```text
Phase 1: repository baseline and governance
Phase 2: Domeneshop API read connector
Phase 3: hosted-file read connector
Phase 3B: MCP server registration
Phase 4: HTTP diagnostics
Phase 5: dry-run deployment planning
Phase 6: recovery planning
Phase 7: control-plane preflight
Phase 8: packaging and readiness scaffold
Phase 9: production runtime scaffold
Phase 10: operational runbook and incident procedures
Phase 11: estate integration
Phase 12: final validation and release gate
Read-only runtime release package
```

## Key files to inspect first

```text
README.md
docs/DOMENESHOP_MCP_FINAL_TRANSFER_REPORT_0245_27062026.md
docs/FINAL_RELEASE_GATE_CHECKLIST.md
docs/READ_ONLY_RUNTIME_RELEASE_PACKAGE_0310_27062026.md
config/read-only-release-manifest.example.json
.github/workflows/validate-domeneshop-mcp.yml
```

## Current validation command set

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
python scripts/release_manifest_validate.py --manifest config/read-only-release-manifest.example.json --output read-only-release-manifest-validation-report.json
```

## Manual actions still required to complete read-only runtime operation

1. Download the GitHub Actions artifact package named `deployment-planning-reports`.
2. Review all Phase 5 through Phase 12 reports plus the read-only release manifest report.
3. Confirm runtime values are stored outside the repository.
4. Configure the MCP client from `config/mcp-client.example.json`.
5. Install the package in the selected runtime using `python -m pip install -e ".[server,sftp]"`.
6. Set runtime values in the deployment environment.
7. Confirm these runtime safety values before startup:

```text
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
```

8. Run readiness and runtime deployment checks.
9. Start the server with `domeneshop-mcp-server`.
10. Run read-only smoke checks.
11. Preserve startup logs and the final artifact package.

## Runtime values that must not be committed

```text
DS_AUTH_USER
DS_AUTH_VALUE
DS_SFTP_USER
DS_SFTP_VALUE
```

## Current allowed roots

```text
/www
/www/solarex_forms
/www/atlas_control
/www/atlas_pip2
```

## Estate targets

```text
SolarEX Forms API -> forms.nanotech-solutions.com -> /www/solarex_forms
SolarEX Admin -> forms.nanotech-solutions.com -> /www/solarex_forms
Atlas Monitor -> monitor.atlas-ai.no -> /www/atlas_control
Atlas PIP -> pip.atlas-ai.no -> /www/atlas_pip2
```

## New explicit release phase to continue with

```text
Phase 13: Explicit Live Change Release Planning
```

Phase 13 must be treated as a separate release track. It must not enable live changes until operator approval, evidence review, test coverage, dry-run evidence, backup evidence, rollback evidence, and a separate release decision are complete.

## Prompt for new chat

```text
Continue the Domeneshop MCP project in repo nanotech-solutions-norway/Domeneshop---MCP-. Start by reading docs/DOMENESHOP_MCP_CONTINUATION_TRANSFER_PACK_0325_27062026.md and docs/PHASE13_EXPLICIT_LIVE_CHANGE_RELEASE_PLANNING_0325_27062026.md. The read-only runtime package has been validated by the operator. Continue with Phase 13 as a separate explicit release phase. Do not enable live change tools by default. Do not store runtime values in the repo. Keep WRITE_TOOLS_ENABLED=false until a later explicit operator approval step.
```

## Note to future self

The read-only path is complete. Do not treat live write/change activation as a continuation of Phase 12. It is a new release phase with a higher risk class and must remain disabled until all Phase 13 evidence is complete and explicitly approved.
