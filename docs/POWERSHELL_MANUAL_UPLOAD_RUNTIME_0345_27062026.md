# PowerShell Manual Upload Runtime — 03:45, 27.06.2026

## Purpose

This document defines the manual-upload runtime path using PowerShell as the operator shell and `/cm/domeneshop-mcp` as the server-side location.

## Canonical server-side location

```text
/cm/domeneshop-mcp
```

## Important runtime note

The operator shell is PowerShell. The MCP codebase is still Python and requires a Python interpreter plus dependencies. PowerShell launches and validates the runtime.

## Required server-side folder layout

```text
/cm/domeneshop-mcp/
  config/
  deploy/
  docs/
  scripts/
  src/
  tests/
  pyproject.toml
  README.md
```

## PowerShell files

```text
deploy/powershell/Start-DomeneshopMcp.ps1
deploy/powershell/Test-DomeneshopMcpReadOnlyRuntime.ps1
config/mcp-client.powershell.example.json
```

## Runtime dependencies

Install dependencies according to the server policy. The minimum Python packages are:

```text
httpx>=0.27.0
pydantic>=2.6.0
mcp>=1.0.0
paramiko>=3.4.0
```

## Runtime values

Set runtime values outside the repository:

```powershell
$env:DS_AUTH_USER = "<Domeneshop API user value>"
$env:DS_AUTH_VALUE = "<Domeneshop API auth value>"
$env:DS_SFTP_USER = "<Domeneshop SFTP user value>"
$env:DS_SFTP_VALUE = "<Domeneshop SFTP auth value>"
```

## Safety values

These are set by the PowerShell launcher and must remain unchanged:

```powershell
$env:WRITE_TOOLS_ENABLED = "false"
$env:DRY_RUN_DEFAULT = "true"
$env:REQUIRE_OPERATOR_APPROVAL = "true"
$env:REQUIRE_BACKUP_EVIDENCE = "true"
$env:REQUIRE_PREFLIGHT_REPORT = "true"
```

## Validate runtime with PowerShell

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File /cm/domeneshop-mcp/deploy/powershell/Test-DomeneshopMcpReadOnlyRuntime.ps1 -RepoRoot /cm/domeneshop-mcp -PythonCommand python
```

## Start MCP runtime with PowerShell

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File /cm/domeneshop-mcp/deploy/powershell/Start-DomeneshopMcp.ps1 -RepoRoot /cm/domeneshop-mcp -PythonCommand python
```

## MCP client configuration

Use:

```text
config/mcp-client.powershell.example.json
```

This config starts PowerShell, which then launches the MCP server from `/cm/domeneshop-mcp`.

## Boundary

```text
READ_ONLY_RUNTIME
LIVE_CHANGE_OPERATIONS_NOT_REGISTERED
WRITE_TOOLS_ENABLED=false
```
