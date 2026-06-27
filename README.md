# Domeneshop MCP Implementation Plan — 03:10, 27.06.2026

This repository is the system of record for a controlled Domeneshop MCP bridge.

## Purpose

Build a governed MCP/API bridge for Domeneshop-related infrastructure operations:

- Domeneshop API operations for domains, DNS records, HTTP forwards, DDNS, and invoices.
- SFTP/SCP/FTP-based website file inspection and later controlled deployment for Domeneshop webhosting.
- HTTP health checks for hosted services and subdomains.
- Dry-run deployment planning through GitHub Actions.
- Planning-only recovery evidence for future controlled deployment.
- Approval-gated change-control preflight before any future live operation.
- MCP server packaging and deployment readiness preflight.
- Production runtime deployment scaffold.
- Operational runbook and incident procedures.
- Atlas/SolarEX/Domeneshop estate inventory and validation.
- Final release gate for read-only runtime acceptance.
- Read-only runtime release package.
- Optional SSH diagnostics where hosting plan and access permit it.
- Phase 13 risk register and disabled-default guard for future live-change scope control.
- GitHub Actions as the preferred controlled deployment lane.

## Core rule

Change actions remain paused until the full deployment package, tests, backup logic, validation gates, and approval controls are complete and explicitly released.

## Source constraints

Domeneshop REST API is not a general file-upload API. It is used for domain/DNS/forward/DDNS/invoice operations. Website file operations must use SFTP/SCP/FTP.

## Repository structure

```text
.
├── README.md
├── pyproject.toml
├── config/
│   ├── domeneshop-mcp.env.example
│   ├── estate-targets.example.json
│   ├── mcp-client.example.json
│   └── read-only-release-manifest.example.json
├── deploy/
│   ├── compose/
│   │   └── compose.readonly.example.yml
│   ├── container/
│   │   └── Dockerfile.example
│   └── systemd/
│       └── domeneshop-mcp.service.example
├── docs/
│   ├── ATLAS_SOLAREX_DOMENESHOP_INTEGRATION_NOTES.md
│   ├── DOMENESHOP_MCP_FINAL_TRANSFER_REPORT_0245_27062026.md
│   ├── DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md
│   ├── ESTATE_SERVICE_INVENTORY.md
│   ├── FINAL_RELEASE_GATE_CHECKLIST.md
│   ├── INCIDENT_RESPONSE_PROCEDURES.md
│   ├── MCP_CLIENT_CONFIGURATION_EXAMPLES.md
│   ├── OPERATIONAL_RUNBOOK.md
│   ├── PHASE10_OPERATIONAL_RUNBOOK_INCIDENTS_0135_27062026.md
│   ├── PHASE11_ESTATE_INTEGRATION_0210_27062026.md
│   ├── PHASE12_FINAL_VALIDATION_RELEASE_GATE_0245_27062026.md
│   ├── PHASE13_RISK_REGISTER_AND_SCOPE.md
│   ├── PHASE2_READ_CONNECTOR_IMPLEMENTATION_1045_26062026.md
│   ├── PHASE3_SFTP_READ_CONNECTOR_IMPLEMENTATION_1125_26062026.md
│   ├── PHASE3B_4_SERVER_AND_HEALTH_IMPLEMENTATION_1145_26062026.md
│   ├── PHASE5_DRY_RUN_DEPLOYMENT_LANE_1215_26062026.md
│   ├── PHASE5_VALIDATION_ERROR_FIX_2320_26062026.md
│   ├── PHASE6_BACKUP_RECOVERY_PLANNING_2340_26062026.md
│   ├── PHASE7_APPROVAL_GATED_CHANGE_CONTROL_0010_27062026.md
│   ├── PHASE8_MCP_PACKAGING_DEPLOYMENT_SCAFFOLD_0035_27062026.md
│   ├── PHASE9_PRODUCTION_DEPLOYMENT_SCAFFOLD_0105_27062026.md
│   ├── PRODUCTION_DEPLOYMENT_RUNBOOK.md
│   ├── READ_ONLY_RUNTIME_RELEASE_PACKAGE_0310_27062026.md
│   ├── RELEASE_APPROVAL_CHECKLIST.md
│   ├── SECURITY_AND_WRITE_CONTROL.md
│   ├── TOOL_CATALOG.md
│   └── VALIDATION_CHECKLIST.md
├── scripts/
│   ├── change_preflight.py
│   ├── domeneshop_read_smoke.py
│   ├── dry_run_plan.py
│   ├── estate_validate.py
│   ├── final_release_gate.py
│   ├── health_smoke.py
│   ├── operations_validate.py
│   ├── phase13_disabled_default_validate.py
│   ├── readiness_preflight.py
│   ├── recovery_plan.py
│   ├── release_manifest_validate.py
│   ├── remote_read_smoke.py
│   ├── runtime_deployment_validate.py
│   └── validate_repository_structure.py
├── src/
│   └── domeneshop_mcp/
│       ├── __init__.py
│       ├── audit_model.py
│       ├── change_control.py
│       ├── client.py
│       ├── config.py
│       ├── deploy_plan.py
│       ├── envelope.py
│       ├── errors.py
│       ├── estate_validation.py
│       ├── health.py
│       ├── operations_validation.py
│       ├── path_jail.py
│       ├── readiness.py
│       ├── recovery_plan.py
│       ├── release_gate.py
│       ├── release_manifest.py
│       ├── runtime_validation.py
│       ├── sanitizers.py
│       ├── server.py
│       ├── sftp_read.py
│       ├── tools_change_control.py
│       ├── tools_dry_run.py
│       ├── tools_health.py
│       ├── tools_read.py
│       ├── tools_recovery_plan.py
│       └── tools_sftp_read.py
├── tests/
│   ├── test_change_control.py
│   ├── test_client_dns.py
│   ├── test_client_domains.py
│   ├── test_client_invoices.py
│   ├── test_config.py
│   ├── test_deploy_plan.py
│   ├── test_estate_validation.py
│   ├── test_final_gate.py
│   ├── test_health.py
│   ├── test_operations_validation.py
│   ├── test_packaging.py
│   ├── test_path_guard.py
│   ├── test_readiness.py
│   ├── test_recovery_plan.py
│   ├── test_release_manifest.py
│   ├── test_runtime_deployment.py
│   ├── test_sanitizers.py
│   └── test_sftp_read_tools.py
└── .github/
    └── workflows/
        └── validate-domeneshop-mcp.yml
```

## Implementation status

| Area | Status |
|---|---|
| Repository baseline | Complete |
| Phase plan | Complete |
| Security model | Complete |
| Tool catalog | Complete |
| Validation checklist | Complete |
| Phase 2 API read connector | Implemented and validated |
| Phase 3 SFTP read connector | Implemented and validated |
| Phase 3B MCP server registration | Complete |
| Phase 4 HTTP health diagnostics | Implemented and validated |
| Phase 5 dry-run deployment lane | Implemented and validated |
| Phase 6 recovery planning | Implemented and validated |
| Phase 7 change-control scaffold | Implemented and validated |
| Phase 8 packaging and readiness scaffold | Implemented and validated |
| Phase 9 production deployment scaffold | Implemented and validated |
| Phase 10 operational runbook and incidents | Implemented and validated |
| Phase 11 estate integration | Implemented and validated |
| Phase 12 final validation and release gate | Implemented and validated |
| Phase 13 risk register and scope | Implemented as disabled-default control layer |
| Phase 13 live activation | Held / not authorized |
| Read-only runtime release package | Implemented, pending CI validation |
| Live change operations | Not registered |
| Runtime access values | Not stored in repository |

## Server entrypoints

```bash
domeneshop-mcp-server
python -m domeneshop_mcp.server
```

## Deployment scaffold

```text
deploy/container/Dockerfile.example
deploy/compose/compose.readonly.example.yml
deploy/systemd/domeneshop-mcp.service.example
```

## Operations documents

```text
docs/OPERATIONAL_RUNBOOK.md
docs/INCIDENT_RESPONSE_PROCEDURES.md
docs/RELEASE_APPROVAL_CHECKLIST.md
docs/FINAL_RELEASE_GATE_CHECKLIST.md
docs/DOMENESHOP_MCP_FINAL_TRANSFER_REPORT_0245_27062026.md
docs/PHASE13_RISK_REGISTER_AND_SCOPE.md
```

## Estate registry and release manifest

```text
config/estate-targets.example.json
config/read-only-release-manifest.example.json
```

## Tool groups

```text
Phase 2: Domeneshop API read tools
Phase 3: hosted-file read tools
Phase 4: HTTP diagnostic tools
Phase 5: dry-run planning tools
Phase 6: recovery planning tools
Phase 7: control-plane tools
Phase 11: estate validation tooling
Phase 12: final release gate tooling
Phase 13: disabled-default risk/scope validation
Read-only release package: release manifest validation
```

The workflow produces a report artifact package named:

```text
deployment-planning-reports
```

## Local validation

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
python scripts/phase13_disabled_default_validate.py --repo-root . --output phase13-disabled-default-validation-report.json
python scripts/release_manifest_validate.py --manifest config/read-only-release-manifest.example.json --output read-only-release-manifest-validation-report.json
```

## Manual smoke checks

```bash
python scripts/domeneshop_read_smoke.py
python scripts/remote_read_smoke.py
python scripts/health_smoke.py
```

Runtime access values must be supplied outside the repository.

## Recommended release decision

```text
APPROVE_READ_ONLY_RUNTIME
HOLD_LIVE_CHANGE_ACTIVATION
HOLD_PHASE13_ACTIVATION
```

## Recommended implementation route

```text
ChatGPT / MCP client
        ↓
Domeneshop MCP bridge
        ↓
Controlled service layer
        ↓
Domeneshop API + SFTP/SCP + optional SSH
        ↓
Domeneshop DNS and webhosting
```

## GitHub upload target

Target repository:

```text
nanotech-solutions-norway/Domeneshop---MCP-
```

## External references

- Domeneshop API documentation: https://api.domeneshop.no/docs/
- Domeneshop file upload documentation: https://domainname.shop/faq?id=56
- Domeneshop shell access documentation: https://domainname.shop/faq?id=64
- MCP tools specification: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
