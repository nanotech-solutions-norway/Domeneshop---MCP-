# MCP Client Configuration Examples

## Purpose

This document provides client-side configuration examples for launching the Domeneshop MCP server after installing the package.

## Package install

```bash
python -m pip install -e ".[server,sftp]"
```

## Console entrypoint

```bash
domeneshop-mcp-server
```

Equivalent module invocation:

```bash
python -m domeneshop_mcp.server
```

## Example client configuration

Use:

```text
config/mcp-client.example.json
```

The example config includes only non-sensitive runtime defaults. Provider access values must be supplied through the host environment, operating-system key store, or deployment platform settings.

## Required runtime values

```text
DOMENESHOP_API_BASE_URL
DS_AUTH_USER
DS_AUTH_VALUE
DOMENESHOP_SFTP_HOST
DOMENESHOP_SFTP_PORT
DS_SFTP_USER
DS_SFTP_VALUE
DOMENESHOP_REMOTE_ROOT
ALLOWED_REMOTE_ROOTS
```

## Required safety defaults

```text
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
```

## Registered tool categories

```text
Domeneshop API read tools
hosted-file read tools
HTTP diagnostics
planning-only deployment tools
planning-only recovery tools
control-plane preflight tools
```

## Not registered by default

```text
DNS mutation tools
HTTP forward mutation tools
hosted-file transfer tools
restore execution tools
shell command tools
```
