$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Repo = 'nanotech-solutions-norway/Domeneshop---MCP-'
$Environment = 'domeneshop-readonly-validation'
$ExpectedBranch = 'main'
$StateRoot = Join-Path $env:LOCALAPPDATA 'NanoTech\DomeneshopMcp\pilot-state'
$SecretFile = Join-Path $StateRoot 'approval-signing-secret.txt'
$ResultFile = Join-Path $StateRoot 'audit\d-r3-txt-create-result.json'

Write-Host ''
Write-Host '============================================================'
Write-Host 'DOMENESHOP MCP — D-R3 AUTHORIZED TXT CREATE'
Write-Host 'Office PC / isolated non-production target only'
Write-Host '============================================================'

# The repository package must be executed from its canonical checkout root.
if (-not (Test-Path '.git')) {
    throw 'Run this script from the Domeneshop MCP repository root.'
}

$Remote = (git remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $Remote -notmatch 'Domeneshop---MCP-') {
    throw 'Current repository is not the Domeneshop MCP checkout.'
}

Write-Host ''
Write-Host '=== 1. Synchronize accepted main ==='
git status --short
$WorkingTreeStatus = @(git status --porcelain)
if ($WorkingTreeStatus.Count -ne 0) {
    throw 'Repository working tree is not clean. Stop before live execution.'
}
git fetch origin main
git checkout $ExpectedBranch
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to synchronize accepted main.'
}

Write-Host ''
Write-Host '=== 2. Verify GitHub identity ==='
gh auth status
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated.'
}
$Operator = (gh api user --jq '.login').Trim()
if (-not $Operator) {
    throw 'Unable to resolve operator identity from GitHub.'
}
Write-Host "Operator identity: $Operator"

Write-Host ''
Write-Host '=== 3. Prepare protected Office-PC state root ==='
New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateRoot 'approval-nonces') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateRoot 'idempotency') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $StateRoot 'audit') | Out-Null

# Restrict inheritance and grant access only to the current operator, SYSTEM,
# and the local Administrators group by SID. Ignore already-applied ACL messages.
icacls $StateRoot /inheritance:r | Out-Null
icacls $StateRoot /grant:r "${env:USERNAME}:(OI)(CI)F" | Out-Null
icacls $StateRoot /grant:r 'SYSTEM:(OI)(CI)F' | Out-Null
icacls $StateRoot /grant:r '*S-1-5-32-544:(OI)(CI)F' | Out-Null

Write-Host ''
Write-Host '=== 4. Resolve protected pilot inputs ==='
if (-not $env:DS_PILOT_DOMAIN_NAME) {
    $env:DS_PILOT_DOMAIN_NAME = Read-Host 'Enter the registered isolated pilot domain name'
}
if (-not $env:DS_AUTH_USER -or -not $env:DS_AUTH_VALUE) {
    throw 'DS_AUTH_USER / DS_AUTH_VALUE are not loaded on this Office PC. Load them from the existing protected credential store; do not paste credentials into ChatGPT.'
}
$env:DS_PILOT_TXT_HOST = '_mcp-validation'

Write-Host ''
Write-Host '=== 5. Rotate and persist the approval signing secret for live CREATE ==='
if (-not (Test-Path $SecretFile)) {
    $SecretBytes = New-Object byte[] 32
    $Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $Rng.GetBytes($SecretBytes)
    }
    finally {
        $Rng.Dispose()
    }
    $SigningSecret = [Convert]::ToBase64String($SecretBytes)
    [System.IO.File]::WriteAllText($SecretFile, $SigningSecret, [System.Text.Encoding]::UTF8)
    [Array]::Clear($SecretBytes, 0, $SecretBytes.Length)
    icacls $SecretFile /inheritance:r | Out-Null
    icacls $SecretFile /grant:r "${env:USERNAME}:F" | Out-Null
    icacls $SecretFile /grant:r 'SYSTEM:F' | Out-Null
    icacls $SecretFile /grant:r '*S-1-5-32-544:F' | Out-Null

    # Keep the protected GitHub environment aligned with the live Office-PC secret.
    $SigningSecret | gh secret set APPROVAL_SIGNING_SECRET --env $Environment --repo $Repo
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to rotate the protected GitHub approval signing secret.'
    }
    $SigningSecret = $null
}

$env:APPROVAL_SIGNING_SECRET = [System.IO.File]::ReadAllText($SecretFile, [System.Text.Encoding]::UTF8).Trim()
if ([System.Text.Encoding]::UTF8.GetByteCount($env:APPROVAL_SIGNING_SECRET) -lt 32) {
    throw 'Local approval signing secret is invalid.'
}

Write-Host ''
Write-Host '=== 6. Create isolated Python runtime ==='
$Venv = Join-Path (Get-Location) '.venv-d-r3-live-create'
if (-not (Test-Path $Venv)) {
    python -m venv $Venv
}
$Python = Join-Path $Venv 'Scripts\python.exe'
& $Python -m pip install --disable-pip-version-check -e '.' | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install the accepted Domeneshop MCP package.'
}

Write-Host ''
Write-Host '=== 7. Arm exact one-shot CREATE process ==='
$env:PILOT_STATE_ROOT = $StateRoot
$env:D_R3_OPERATOR = $Operator
$env:D_R3_AUTHORIZATION_PHRASE = 'AUTHORIZE_D_R3_TXT_CREATE'
$env:WRITE_TOOLS_ENABLED = 'true'
$env:DRY_RUN_DEFAULT = 'false'
$env:REQUIRE_OPERATOR_APPROVAL = 'true'

Write-Host 'Exact authorization: D-R3 TXT CREATE'
Write-Host 'TXT UPDATE authorized: false'
Write-Host 'TXT DELETE/rollback authorized: false'
Write-Host 'MX/NS/general DNS changes authorized: false'
Write-Host ''

$ExitCode = 1
try {
    $Output = & $Python 'scripts\dns_txt_pilot_live_create.py' 2>&1
    $ExitCode = $LASTEXITCODE
    $Output | Tee-Object -FilePath $ResultFile | Out-Host
}
finally {
    # Return the current PowerShell process to read-only defaults regardless of outcome.
    $env:WRITE_TOOLS_ENABLED = 'false'
    $env:DRY_RUN_DEFAULT = 'true'
    $env:D_R3_AUTHORIZATION_PHRASE = ''
    $env:APPROVAL_SIGNING_SECRET = ''
}

Write-Host ''
Write-Host '============================================================'
Write-Host "LIVE_CREATE_EXIT_CODE=$ExitCode"
Write-Host 'WRITE_TOOLS_ENABLED=false'
Write-Host 'TXT_UPDATE_AUTHORIZED=false'
Write-Host 'TXT_DELETE_AUTHORIZED=false'
Write-Host "LOCAL_RESULT_FILE=$ResultFile"
Write-Host '============================================================'

if ($ExitCode -ne 0) {
    throw 'D-R3 TXT CREATE did not complete cleanly. STOP. Do not retry with a new idempotency identity and do not delete/rollback without separate authorization.'
}