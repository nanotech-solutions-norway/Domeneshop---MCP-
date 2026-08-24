$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ExpectedBranch='main'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R4 SFTP SINGLE-ROOT DIAGNOSTIC (READ-ONLY)'
Write-Host 'Office PC / dedicated atlas-mcp-sandbox.no webhotel credentials'
Write-Host '============================================================'

if(-not(Test-Path '.git')){throw 'Run this script from the Domeneshop MCP repository root.'}
$Remote=(git remote get-url origin).Trim()
if($LASTEXITCODE-ne 0-or $Remote-notmatch'Domeneshop---MCP-'){throw 'Current repository is not the Domeneshop MCP checkout.'}

Write-Host ''
Write-Host '=== 1. Synchronize accepted main ==='
$WorkingTreeStatus=@(git status --porcelain)
if($WorkingTreeStatus.Count-ne 0){throw 'Repository working tree is not clean.'}
git fetch origin main
git checkout $ExpectedBranch
git pull --ff-only origin main
if($LASTEXITCODE-ne 0){throw 'Unable to synchronize accepted main.'}

Write-Host ''
Write-Host '=== 2. Validate local SFTP credentials ==='
if(-not $env:DS_SFTP_USER-or-not $env:DS_SFTP_VALUE){throw 'DS_SFTP_USER / DS_SFTP_VALUE are not loaded locally.'}
$env:DOMENESHOP_SFTP_HOST='sftp.domeneshop.no'
$env:DOMENESHOP_SFTP_PORT='22'
$env:ALLOWED_REMOTE_ROOTS='/www'
$env:WRITE_TOOLS_ENABLED='false'
$env:DRY_RUN_DEFAULT='true'

Write-Host ''
Write-Host '=== 3. Refresh isolated Python runtime ==='
$Venv=Join-Path(Get-Location)'.venv-d-r4-sftp-preflight'
if(-not(Test-Path $Venv)){python -m venv $Venv}
$Python=Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check -e '.[sftp]'|Out-Host
if($LASTEXITCODE-ne 0){throw 'Failed to install accepted SFTP runtime.'}

Write-Host ''
Write-Host '=== 4. Execute strict single-root read-only diagnostic ==='
Write-Host 'Search root: /www'
Write-Host 'Required root entry count: 1'
Write-Host 'Maximum nested depth: 1'
Write-Host 'SFTP mutation authorized: false'
Write-Host 'WRITE_TOOLS_ENABLED=false'
$ExitCode=1
try{
    & $Python 'scripts\sftp_d_r4_single_root_diagnostic.py'
    $ExitCode=$LASTEXITCODE
}
finally{
    $env:WRITE_TOOLS_ENABLED='false'
    $env:DRY_RUN_DEFAULT='true'
}
Write-Host ''
Write-Host '============================================================'
Write-Host "D_R4_SFTP_SINGLE_ROOT_DIAGNOSTIC_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'SFTP_CREATE_AUTHORIZED=false'
Write-Host 'SFTP_OVERWRITE_AUTHORIZED=false'
Write-Host 'SFTP_DELETE_AUTHORIZED=false'
Write-Host '============================================================'
if($ExitCode-ne 0){throw 'D-R4 SFTP single-root diagnostic did not pass. HOLD.'}
