$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ExpectedBranch='main'
$ReleaseId='D-R4-SFTP-UPDATE-20260824-001'
$TargetHash='0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a'
$BeforeHash='9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a'
$AfterHash='482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R4 AUTHORIZED SFTP UPDATE'
Write-Host 'Exact one-file update / no delete / no rename'
Write-Host '============================================================'

if(-not(Test-Path '.git')){throw 'Run this script from the Domeneshop MCP repository root.'}
$Remote=(git remote get-url origin).Trim()
if($LASTEXITCODE-ne 0-or $Remote-notmatch'Domeneshop---MCP-'){throw 'Current repository is not the Domeneshop MCP checkout.'}
$WorkingTreeStatus=@(git status --porcelain)
if($WorkingTreeStatus.Count-ne 0){throw 'Repository working tree is not clean.'}

git fetch origin main
git checkout $ExpectedBranch
git pull --ff-only origin main
if($LASTEXITCODE-ne 0){throw 'Unable to synchronize accepted main.'}

if(-not $env:DS_SFTP_USER-or-not $env:DS_SFTP_VALUE){throw 'Correct atlas-mcp-sandbox.no SFTP credentials are not loaded locally.'}

$env:DOMENESHOP_SFTP_HOST='sftp.domeneshop.no'
$env:DOMENESHOP_SFTP_PORT='22'
$env:ALLOWED_REMOTE_ROOTS='/www'
$env:WRITE_TOOLS_ENABLED='false'
$env:DRY_RUN_DEFAULT='true'
$env:SFTP_D_R4_UPDATE_AUTHORIZED='true'
$env:SFTP_D_R4_RELEASE_ID=$ReleaseId
$env:SFTP_D_R4_TARGET_SHA256=$TargetHash
$env:SFTP_D_R4_BEFORE_SHA256=$BeforeHash
$env:SFTP_D_R4_AFTER_SHA256=$AfterHash
$env:SFTP_D_R4_DELETE_AUTHORIZED='false'
$env:SFTP_D_R4_RENAME_AUTHORIZED='false'
$env:SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED='false'

$Venv=Join-Path(Get-Location)'.venv-d-r4-sftp-preflight'
if(-not(Test-Path $Venv)){python -m venv $Venv}
$Python=Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check -e '.[sftp]'|Out-Host
if($LASTEXITCODE-ne 0){throw 'Failed to install accepted SFTP runtime.'}

$ExitCode=1
try{
    & $Python 'scripts\sftp_d_r4_live_update.py'
    $ExitCode=$LASTEXITCODE
}
finally{
    $env:SFTP_D_R4_UPDATE_AUTHORIZED='false'
    $env:SFTP_D_R4_RELEASE_ID=$null
    $env:SFTP_D_R4_TARGET_SHA256=$null
    $env:SFTP_D_R4_BEFORE_SHA256=$null
    $env:SFTP_D_R4_AFTER_SHA256=$null
    $env:SFTP_D_R4_DELETE_AUTHORIZED='false'
    $env:SFTP_D_R4_RENAME_AUTHORIZED='false'
    $env:SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED='false'
    $env:WRITE_TOOLS_ENABLED='false'
    $env:DRY_RUN_DEFAULT='true'
}

Write-Host ''
Write-Host '============================================================'
Write-Host "D_R4_SFTP_LIVE_UPDATE_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'SFTP_DELETE_AUTHORIZED=false'
Write-Host 'SFTP_RENAME_AUTHORIZED=false'
Write-Host 'BROADER_OVERWRITE_AUTHORIZED=false'
Write-Host '============================================================'
if($ExitCode-ne 0){throw 'D-R4 authorized SFTP UPDATE did not complete with verified readback. HOLD.'}
