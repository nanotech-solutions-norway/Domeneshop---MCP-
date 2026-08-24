$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ExpectedBranch='main'
$ReleaseId='D-R4-SFTP-REPAIR-UPDATE-20260824-001'
$TargetHash='0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a'
$BeforeHash='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
$AfterHash='9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R4 AUTHORIZED SFTP REPAIR/UPDATE'
Write-Host 'Exact empty artifact -> accepted payload / no delete / no rename'
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
$env:SFTP_D_R4_REPAIR_AUTHORIZED='true'
$env:SFTP_D_R4_REPAIR_RELEASE_ID=$ReleaseId
$env:SFTP_D_R4_REPAIR_TARGET_SHA256=$TargetHash
$env:SFTP_D_R4_REPAIR_BEFORE_SHA256=$BeforeHash
$env:SFTP_D_R4_REPAIR_AFTER_SHA256=$AfterHash
$env:SFTP_D_R4_DELETE_AUTHORIZED='false'
$env:SFTP_D_R4_RENAME_AUTHORIZED='false'

$Venv=Join-Path(Get-Location)'.venv-d-r4-sftp-preflight'
if(-not(Test-Path $Venv)){python -m venv $Venv}
$Python=Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check -e '.[sftp]'|Out-Host
if($LASTEXITCODE-ne 0){throw 'Failed to install accepted SFTP runtime.'}

$ExitCode=1
try{
    & $Python 'scripts\sftp_d_r4_repair_update.py'
    $ExitCode=$LASTEXITCODE
}
finally{
    $env:SFTP_D_R4_REPAIR_AUTHORIZED='false'
    $env:SFTP_D_R4_REPAIR_RELEASE_ID=$null
    $env:SFTP_D_R4_REPAIR_TARGET_SHA256=$null
    $env:SFTP_D_R4_REPAIR_BEFORE_SHA256=$null
    $env:SFTP_D_R4_REPAIR_AFTER_SHA256=$null
    $env:SFTP_D_R4_DELETE_AUTHORIZED='false'
    $env:SFTP_D_R4_RENAME_AUTHORIZED='false'
    $env:WRITE_TOOLS_ENABLED='false'
    $env:DRY_RUN_DEFAULT='true'
}

Write-Host ''
Write-Host '============================================================'
Write-Host "D_R4_SFTP_REPAIR_UPDATE_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'SFTP_DELETE_AUTHORIZED=false'
Write-Host 'SFTP_RENAME_AUTHORIZED=false'
Write-Host '============================================================'
if($ExitCode-ne 0){throw 'D-R4 authorized SFTP repair/update did not complete with verified readback. HOLD.'}
