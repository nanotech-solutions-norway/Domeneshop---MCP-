# Production Deployment Runbook

## Scope

This runbook covers packaging and readiness checks for the Domeneshop MCP server.

It does not authorize live DNS changes, hosted-file transfers, restore execution, or shell execution.

## Install

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[server,sftp]"
```

## Configure runtime values

Use the template:

```text
config/domeneshop-mcp.env.example
```

Store live values outside the repository.

## Validate safe defaults

```bash
grep -q '^WRITE_TOOLS_ENABLED=false$' config/domeneshop-mcp.env.example
grep -q '^DRY_RUN_DEFAULT=true$' config/domeneshop-mcp.env.example
grep -q '^REQUIRE_OPERATOR_APPROVAL=true$' config/domeneshop-mcp.env.example
```

## Run readiness preflight

```bash
python scripts/readiness_preflight.py --output phase8-readiness-preflight-report.json
```

## Run server

```bash
domeneshop-mcp-server
```

Alternative:

```bash
python -m domeneshop_mcp.server
```

## Client configuration

Use:

```text
config/mcp-client.example.json
```

Copy the example into the client-specific MCP configuration location, then supply runtime values through the runtime environment.

## Release gate

Before any later live change phase, require:

```text
passing CI
Phase 5 dry-run report
Phase 6 backup evidence report
Phase 6 restore preview report
Phase 7 change-control preflight report
Phase 8 readiness preflight report
operator approval reference
```

## Current production posture

```text
READ_ONLY_AND_PLANNING_READY_AFTER_RUNTIME_VALUES
LIVE_CHANGE_OPERATIONS_NOT_REGISTERED
```
