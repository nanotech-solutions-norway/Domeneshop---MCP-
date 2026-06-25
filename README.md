# Domeneshop MCP Implementation Plan — 22:34, 25.06.2026

This repository is the system of record for a controlled Domeneshop MCP bridge.

## Purpose

Build a governed MCP/API bridge for Domeneshop-related infrastructure operations:

- Domeneshop API operations for domains, DNS records, HTTP forwards, DDNS, and invoices.
- SFTP/SCP/FTP-based website file deployment for Domeneshop webhosting.
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
├── config/
│   └── domeneshop-mcp.env.example
├── docs/
│   ├── DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md
│   ├── SECURITY_AND_WRITE_CONTROL.md
│   ├── TOOL_CATALOG.md
│   └── VALIDATION_CHECKLIST.md
├── scripts/
│   └── validate_repository_structure.py
└── .github/
    └── workflows/
        └── validate-domeneshop-mcp.yml
```

## Implementation status

| Area | Status |
|---|---|
| Repository baseline | Prepared |
| Phase plan | Prepared |
| Security model | Prepared |
| Tool catalog | Prepared |
| Validation checklist | Prepared |
| Write operations | Paused |
| Credentials | Not stored in repository |

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
