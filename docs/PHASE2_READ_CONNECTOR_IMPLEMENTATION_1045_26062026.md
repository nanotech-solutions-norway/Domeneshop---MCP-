# Phase 2 Read Connector Implementation — 10:45, 26.06.2026

## Scope

Phase 2 implements read-only Domeneshop API access.

Included tools:

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

## Provider surface

The Domeneshop API documentation confirms:

- REST API, version `v0`.
- HTTP Basic Auth.
- API user value is supplied as the Basic Auth username.
- API auth value is supplied as the Basic Auth value.
- Feature areas include domains, invoices, DNS record management, HTTP forward management, and DDNS update.

## Deliberate exclusions

The following are not registered in Phase 2:

```text
domeneshop_create_dns_record
domeneshop_update_dns_record
domeneshop_delete_dns_record
domeneshop_create_http_forward
domeneshop_update_http_forward
domeneshop_delete_http_forward
domeneshop_ddns_update
sftp_upload_file
sftp_delete_file
ssh_run_command
```

## Runtime environment names

```text
DS_AUTH_USER
DS_AUTH_VALUE
```

These values must be supplied only through protected runtime configuration.

## Safety controls

- `WRITE_TOOLS_ENABLED=false` remains the default.
- The MCP server registers only read tools.
- Invoice output excludes provider invoice links because such links may include private access parameters.
- Provider errors are mapped to controlled error classes.

## Local validation

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
```

## Manual read smoke test

```bash
python scripts/domeneshop_read_smoke.py
```

The smoke test only calls `domeneshop_list_domains` and prints a sanitized response envelope.

## Status

```text
PHASE_2_IMPLEMENTED_PENDING_CI_VALIDATION
```
