param(
    [string]$RepoRoot = "/cm/domeneshop-mcp",
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}

$srcPath = Join-Path $RepoRoot "src"
$serverPath = Join-Path $srcPath "domeneshop_mcp/server.py"

if (-not (Test-Path -LiteralPath $serverPath)) {
    throw "MCP server module not found at: $serverPath"
}

$env:PYTHONPATH = $srcPath
$env:WRITE_TOOLS_ENABLED = "false"
$env:DRY_RUN_DEFAULT = "true"
$env:REQUIRE_OPERATOR_APPROVAL = "true"
$env:REQUIRE_BACKUP_EVIDENCE = "true"
$env:REQUIRE_PREFLIGHT_REPORT = "true"

Set-Location -LiteralPath $RepoRoot
& $PythonCommand -m domeneshop_mcp.server
