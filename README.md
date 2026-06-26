# Domeneshop MCP Implementation Plan — 12:15, 26.06.2026

This repository is the system of record for a controlled Domeneshop MCP bridge.

## Purpose

Build a governed MCP/API bridge for Domeneshop-related infrastructure operations:

- Domeneshop API operations for domains, DNS records, HTTP forwards, DDNS, and invoices.
- SFTP/SCP/FTP-based website file inspection and later controlled deployment for Domeneshop webhosting.
- HTTP health checks for hosted services and subdomains.
- Dry-run deployment planning through GitHub Actions.
- Optional SSH diagnostics where hosting plan and access permit it.
- GitHub Actions as the preferred controlled deployment lane.

## Core rule

Write actions remain paused until the full deployment package, tests, backup logic, validation gates, and approval controls are complete.

## Source constraints

Domeneshop REST API is not a general file-upload API. It is used for domain/DNS/forward/DDNS/invoice operations. Website file operations must use SFTP/SCP/FTP.

## Repository structure

```text
.
├── README.md
├── pyproject.toml
├── config/
│   └── domeneshop-mcp.env.example
├── docs/
│   ├── DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md
│   ├── PHASE2_READ_CONNECTOR_IMPLEMENTATION_1045_26062026.md
│   ├── PHASE3_SFTP_READ_CONNECTOR_IMPLEMENTATION_1125_26062026.md
│   ├── PHASE3B_4_SERVER_AND_HEALTH_IMPLEMENTATION_1145_26062026.md
│   ├── PHASE5_DRY_RUN_DEPLOYMENT_LANE_1215_26062026.md
│   ├── SECURITY_AND_WRITE_CONTROL.md
│   ├── TOOL_CATALOG.md
│   └── VALIDATION_CHECKLIST.md
├── scripts/
│   ├── domeneshop_read_smoke.py
│   ├── dry_run_plan.py
│   ├── health_smoke.py
│   ├── remote_read_smoke.py
│   └── validate_repository_structure.py
├── src/
│   └── domeneshop_mcp/
│       ├── __init__.py
│       ├── client.py
│       ├── config.py
│       ├── deploy_plan.py
│       ├── envelope.py
│       ├── errors.py
│       ├── health.py
│       ├── path_jail.py
│       ├── sanitizers.py
│       ├── server.py
│       ├── sftp_read.py
│       ├── tools_dry_run.py
│       ├── tools_health.py
│       ├── tools_read.py
│       └── tools_sftp_read.py
├── tests/
│   ├── test_client_dns.py
│   ├── test_client_domains.py
│   ├── test_client_invoices.py
│   ├── test_config.py
│   ├── test_deploy_plan.py
│   ├── test_health.py
│   ├── test_path_guard.py
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
| Phase 5 dry-run deployment lane | Implemented, pending CI validation |
| Write operations | Paused |
| Runtime access values | Not stored in repository |

## Phase 2 API read tools

```text
domeneshop_list_domains
domeneshop_get_domain
domeneshop_list_dns_records
domeneshop_get_dns_record
domeneshop_list_http_forwards
domeneshop_get_http_forward
domeneshop_list_invoices
domeneshop_get_invoice
```

## Phase 3 hosted-file read tools

```text
sftp_list_allowed_roots
sftp_list_files
sftp_get_file_metadata
sftp_read_text_file
```

## Phase 4 HTTP diagnostic tools

```text
http_check_endpoint
http_check_json_health
http_check_tls
```

## Phase 5 dry-run planning tools

```text
deployment_build_local_manifest
deployment_compare_manifest
```

The Phase 5 lane produces a report artifact named:

```text
phase5-dry-run-report
```

## Local validation

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
python scripts/dry_run_plan.py --source-root . --target-root /www --output phase5-dry-run-report.json
```

## Manual smoke checks

```bash
python scripts/domeneshop_read_smoke.py
python scripts/remote_read_smoke.py
python scripts/health_smoke.py
```

Runtime access values must be supplied outside the repository.

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
