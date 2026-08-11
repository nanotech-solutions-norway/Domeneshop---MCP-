# D-R3 Isolated DNS TXT Pilot Server Configuration

## Scope

This prepares persistent server-side state for the isolated TXT pilot. It does not register a write tool, enable live execution, or authorize a provider mutation. No PHP, webroot, SFTP-hosted file, database, email, or production-domain change is required for this DNS-only pilot.

## Required protected values

Store these outside the repository:

- `DS_AUTH_USER` and `DS_AUTH_VALUE`: existing Domeneshop API token credentials;
- `DS_PILOT_DOMAIN_NAME`: the registered isolated domain name;
- `APPROVAL_SIGNING_SECRET`: a new random value of at least 32 bytes, used only for payload-bound pilot approvals.

Do not store the resolved Domeneshop numeric domain ID as the primary selector. The protected preflight resolves the exact domain name through an authenticated GET and fails on missing, duplicate, inactive, or ambiguous results.

## Non-secret fixed values

```text
DS_PILOT_TXT_HOST=_mcp-validation
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
REQUIRE_BACKUP_EVIDENCE=true
REQUIRE_PREFLIGHT_REPORT=true
```

Keep these values unchanged through registration and GET-only preflight. A later pilot release may change `WRITE_TOOLS_ENABLED` only inside a separately approved isolated runtime after a live-execution manifest, one-time approval token, dry-run evidence, and operator authorization exist.

## Persistent state layout

Create one runtime-owned directory outside the Git checkout. The service account must have exclusive write access; other users receive no access unless needed for backup or independent audit review.

```text
<pilot-state-root>/
  approval-nonces/
  idempotency/
  audit/
    controlled-write.jsonl
  controlled-write-release-manifest.json
```

Map the paths through a copy of `config/dns-txt-pilot.runtime.env.example` stored outside the repository:

```text
APPROVAL_NONCE_DIR=<pilot-state-root>/approval-nonces
IDEMPOTENCY_DIR=<pilot-state-root>/idempotency
CONTROLLED_WRITE_AUDIT_FILE=<pilot-state-root>/audit/controlled-write.jsonl
CONTROLLED_WRITE_RELEASE_MANIFEST=<pilot-state-root>/controlled-write-release-manifest.json
```

The signing secret must not be written to this file unless the file is managed by an approved OS secret mechanism. Prefer a service credential store or protected environment injection.

## Windows PowerShell host

Run the following locally on the MCP host after selecting an absolute state root. Do not paste secrets into the command history.

```powershell
$PilotStateRoot = 'C:\ProgramData\NanoTech\DomeneshopMcp\pilot-state'
New-Item -ItemType Directory -Force -Path $PilotStateRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PilotStateRoot 'approval-nonces') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PilotStateRoot 'idempotency') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PilotStateRoot 'audit') | Out-Null
```

Apply Windows ACLs so only the MCP service identity and the designated administrator can read or write the directory. Do not use a broadly writable user profile, webroot, shared folder, or repository directory.

For the GET-only preflight, configure the protected GitHub environment `domeneshop-readonly-validation`:

- secret `DS_PILOT_DOMAIN_NAME` = registered isolated domain;
- variable `DS_PILOT_TXT_HOST` = `_mcp-validation`;
- variables `WRITE_TOOLS_ENABLED=false`, `DRY_RUN_DEFAULT=true`, and `REQUIRE_OPERATOR_APPROVAL=true`.

Enter the domain manually in the GitHub environment secret UI. Do not echo it in PowerShell or workflow logs.

## Linux systemd host

Use a root-owned directory such as `/var/lib/domeneshop-mcp/pilot-state`, owned by the MCP service account with mode `0700`. Keep the environment file outside the repository with mode `0600`, or inject secrets through the host's secret manager. The existing systemd example remains read-only and must not be changed to enable writes during provisioning.

## Container host

Mount the state root as a dedicated persistent volume at `/var/lib/domeneshop-mcp/pilot-state`. Mount the release manifest read-only until the separately approved activation step. Inject credentials and the signing secret through the container platform's secret mechanism. The existing read-only Compose example remains unchanged.

## Registration-to-preflight sequence

1. Register the isolated domain with DNS only; do not add email or webhosting.
2. Confirm it appears in the Domeneshop control panel and authenticated API domain list.
3. Confirm there are no MX, NS override, forwarding, hosting, or customer dependencies.
4. Add `DS_PILOT_DOMAIN_NAME` to the protected GitHub environment.
5. Dispatch `prepare-dns-txt-pilot.yml` from accepted `main`.
6. Accept only sanitized GET-only evidence with `WRITE_TOOLS_ENABLED=false` and `PROVIDER_MUTATION_PERFORMED=false`.
7. Stop for a separate operator authorization before generating a live manifest or approval token.

## Fail-closed checks

The process stops if the domain is not an exact active match, the `_mcp-validation` TXT host already exists, a protected value is missing, any write flag is enabled, the state paths are inside the repository or webroot, or the accepted `main` commit cannot be identified.
