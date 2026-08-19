$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ExpectedBranch = 'main'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R3 TXT RESTORE DRY RUN'
Write-Host 'GET-only / no provider mutation'
Write-Host '============================================================'

if (-not (Test-Path '.git')) {
    throw 'Run this script from the Domeneshop MCP repository root.'
}

$Remote = (git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $Remote -notmatch 'Domeneshop---MCP-') {
    throw 'Current repository is not the Domeneshop MCP checkout.'
}

$WorkingTreeStatus = @(git status --porcelain)
if ($WorkingTreeStatus.Count -ne 0) {
    throw 'Repository working tree is not clean.'
}

git fetch origin main
git checkout $ExpectedBranch
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to synchronize accepted main.'
}

if (-not $env:DS_PILOT_DOMAIN_NAME) {
    $env:DS_PILOT_DOMAIN_NAME = 'atlas-mcp-sandbox.no'
}
if (-not $env:DS_AUTH_USER -or -not $env:DS_AUTH_VALUE) {
    throw 'DS_AUTH_USER / DS_AUTH_VALUE are not loaded on this Office PC.'
}

$env:WRITE_TOOLS_ENABLED = 'false'
$env:DRY_RUN_DEFAULT = 'true'
$env:REQUIRE_OPERATOR_APPROVAL = 'true'

$Venv = Join-Path (Get-Location) '.venv-d-r3-live-create'
if (-not (Test-Path $Venv)) {
    python -m venv $Venv
}
$Python = Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check -e '.' | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install the accepted Domeneshop MCP package.'
}

$ExitCode = 1
try {
    & $Python 'scripts\dns_txt_pilot_restore_dry_run.py'
    $ExitCode = $LASTEXITCODE
}
finally {
    $env:WRITE_TOOLS_ENABLED = 'false'
    $env:DRY_RUN_DEFAULT = 'true'
}

Write-Host ''
Write-Host "RESTORE_DRY_RUN_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'TXT_RESTORE_AUTHORIZED=false'
Write-Host 'TXT_DELETE_AUTHORIZED=false'

if ($ExitCode -ne 0) {
    throw 'D-R3 TXT RESTORE dry run did not complete cleanly. STOP. No restore/delete is authorized.'
}
