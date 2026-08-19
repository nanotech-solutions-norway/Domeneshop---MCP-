$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ExpectedBranch = 'main'
$Repo = 'nanotech-solutions-norway/Domeneshop---MCP-'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R3 TXT UPDATE DRY RUN'
Write-Host 'GET-only / no provider mutation'
Write-Host '============================================================'

if (-not (Test-Path '.git')) {
    throw 'Run this script from the Domeneshop MCP repository root.'
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
    $env:DS_PILOT_DOMAIN_NAME = Read-Host 'Enter the registered isolated pilot domain name'
}
if (-not $env:DS_AUTH_USER -or -not $env:DS_AUTH_VALUE) {
    throw 'DS_AUTH_USER / DS_AUTH_VALUE are not loaded in this PowerShell process.'
}

$env:WRITE_TOOLS_ENABLED = 'false'
$env:DRY_RUN_DEFAULT = 'true'
$env:REQUIRE_OPERATOR_APPROVAL = 'true'

$Venv = Join-Path (Get-Location) '.venv-d-r3-live-create'
$Python = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $Python)) {
    python -m venv $Venv
    $Python = Join-Path $Venv 'Scripts\python.exe'
}
& $Python -m pip install --disable-pip-version-check -e '.' | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install the accepted Domeneshop MCP package.'
}

try {
    & $Python 'scripts\dns_txt_pilot_update_dry_run.py'
    $ExitCode = $LASTEXITCODE
}
finally {
    $env:WRITE_TOOLS_ENABLED = 'false'
    $env:DRY_RUN_DEFAULT = 'true'
}

Write-Host ''
Write-Host "UPDATE_DRY_RUN_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'TXT_UPDATE_AUTHORIZED=false'
Write-Host 'TXT_DELETE_AUTHORIZED=false'

if ($ExitCode -ne 0) {
    throw 'D-R3 TXT UPDATE dry run did not complete cleanly.'
}
