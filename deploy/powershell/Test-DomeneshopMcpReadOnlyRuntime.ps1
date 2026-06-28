param(
    [string]$RepoRoot = "/cm/domeneshop-mcp",
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}

$srcPath = Join-Path $RepoRoot "src"
$env:PYTHONPATH = $srcPath
$env:WRITE_TOOLS_ENABLED = "false"
$env:DRY_RUN_DEFAULT = "true"
$env:REQUIRE_OPERATOR_APPROVAL = "true"
$env:REQUIRE_BACKUP_EVIDENCE = "true"
$env:REQUIRE_PREFLIGHT_REPORT = "true"

Set-Location -LiteralPath $RepoRoot

& $PythonCommand scripts/readiness_preflight.py --output phase8-readiness-preflight-report.json
& $PythonCommand scripts/runtime_deployment_validate.py --repo-root . --output phase9-runtime-deployment-validation-report.json
& $PythonCommand scripts/release_manifest_validate.py --manifest config/read-only-release-manifest.example.json --output read-only-release-manifest-validation-report.json

Write-Host "Read-only runtime validation completed."
