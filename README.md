# Domeneshop MCP Implementation Plan — 11:25, 26.06.2026

This repository is the system of record for a controlled Domeneshop MCP bridge.

## Purpose

Build a governed MCP/API bridge for Domeneshop-related infrastructure operations:

- Domeneshop API operations for domains, DNS records, HTTP forwards, DDNS, and invoices.
- SFTP/SCP/FTP-based website file inspection and later controlled deployment for Domeneshop webhosting.
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
│   ├── SECURITY_AND_WRITE_CONTROL.md
│   ├── TOOL_CATALOG.md
│   └── VALIDATION_CHECKLIST.md
├── scripts/
│   ├── domeneshop_read_smoke.py
│   ├── remote_read_smoke.py
│   └── validate_repository_structure.py
├── src/
│   └── domeneshop_mcp/
│       ├── __init__.py
│       ├── client.py
│       ├── config.py
│       ├── envelope.py
│       ├── errors.py
│       ├── path_jail.py
│       ├── sanitizers.py
│       ├── server.py
│       ├── sftp_read.py
│       ├── tools_read.py
│       └── tools_sftp_read.py
├── tests/
│   ├── test_client_dns.py
│   ├── test_client_domains.py
│   ├── test_client_invoices.py
│   ├── test_config.py
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
| Phase 3 SFTP read connector | Implemented, pending CI validation and MCP server registration |
| Write operations | Paused |
| Runtime auth values | Not stored in repository |

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

## Phase 3 SFTP read handlers

```text
sftp_list_allowed_roots
sftp_list_files
sftp_get_file_metadata
sftp_read_text_file
```

These are implemented as read-only handlers. Direct MCP server registration remains pending because the connector safety layer blocked the server update during implementation.

## Local validation

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
```

## Manual Phase 3 smoke check

```bash
python scripts/remote_read_smoke.py
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
