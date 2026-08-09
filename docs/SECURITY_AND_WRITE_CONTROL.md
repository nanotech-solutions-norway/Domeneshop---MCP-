# Domeneshop MCP Security and Write Control — updated 00:09, 09.08.2026

## Universal Atlas/MCP baseline

Domeneshop MCP must meet the NTSN Atlas AI & MCP Universal Security Standard. The canonical cross-project standard is maintained in the private `nanotech-solutions-norway/ntsn-mcp-integrations` governance repository. This public file repeats the implementation-critical non-sensitive requirements.

The existing read-first, least-privilege, auditable and reversible posture remains mandatory and is extended by these rules:

- Raw API tokens, secrets, passwords and private keys never enter LLM/agent prompts, memory, RAG, tool results, screenshots, logs, Drive evidence or Git.
- Prefer OAuth/OIDC, workload identity and short-lived/dynamic credentials. Provider static credentials are a compatibility fallback and remain in an approved server-side secret manager/credential boundary.
- A credential broker/provider adapter attaches provider credentials server-side. The model receives only opaque connector/resource references and sanitized results.
- For HTTP MCP authorization, client access tokens must be audience/resource-bound to the MCP server and must never be passed through to Domeneshop or another upstream service.
- Office PC and laptop PC are separate machine identities/configurations; credential files and private keys are not synchronized between them.
- Authorization binds actor/workload, tenant/site/domain, environment, exact action, target, risk, policy/schema version and expiry.
- Consequential writes require a short-lived one-use approval bound to exact target and canonical payload hash. Model judgment is not authorization.
- Disabled execute tools are absent from effective tool discovery and rejected again at the final provider/file/database dispatch boundary.
- Mutations require idempotency/replay protection, deterministic preview, pre-read/backup where relevant, readback, audit closure and tested recovery.
- Ambiguous mutation responses are not automatically retried; read back provider state first.
- Global and action-specific kill switches fail closed.
- General shell, arbitrary filesystem, unrestricted SQL and broad recursive delete remain prohibited MCP capabilities.
- Runtime/release-manifest drift blocks write activation.

Governance adoption does not claim the current runtime has completed the credential-broker/OAuth migration or live write implementation. Those remain implementation and validation gates.

## Security posture

The Domeneshop MCP bridge must be read-first, least-privilege, auditable and reversible.

## Mandatory controls

### 1. Write pause

Default:

```text
WRITE_TOOLS_ENABLED=false
```

When false:

- DNS write tools are not registered.
- HTTP forward write tools are not registered.
- SFTP upload/delete/restore tools are not registered.
- Deployment workflow remains dry-run only.

### 2. Secrets handling

Never commit or expose through an AI context:

- Domeneshop API token
- Domeneshop API secret
- FTP/SFTP/SCP password
- SSH private key
- production `.env`
- OAuth access/refresh token
- signing or webhook secret
- private customer/accounting data
- bank/account identifiers

Preferred mechanisms, in order:

1. workload/managed identity or federation where supported;
2. OAuth authorization with short-lived access tokens;
3. dynamic/temporary credentials;
4. static credentials held only in an approved secret manager/server-side credential boundary when no stronger provider method exists.

GitHub Actions should use OIDC/workload federation for cloud/deployment access where supported instead of long-lived deployment secrets. Repository/environment secrets remain a fallback for systems that cannot federate and must be scoped, rotated and never echoed.

### 3. Path jail

Allowed roots are explicitly configured and canonicalized. Block path traversal and unapproved roots, including:

```text
../
~
/etc/
/home/
/private/ unless explicitly approved
recursive delete
chmod 777
shell command injection
```

Every file operation resolves the final canonical path and verifies that it remains inside the approved root before opening or writing it.

### 4. Backup-before-write

All overwrites require:

1. Remote read/current-state capture.
2. Hash before write.
3. Timestamped/versioned backup.
4. Upload/replace through a bounded adapter.
5. Remote re-read.
6. Hash/content verification.
7. Audit closure.

### 5. Approval-gated writes

A write operation must include:

- authenticated actor/workload and tenant/site scope;
- target path/domain/object;
- exact operation and risk class;
- dry-run preview;
- canonical payload hash;
- backup/rollback evidence where applicable;
- one-use expiring approval when required;
- idempotency/replay key;
- audit entry and post-write readback.

### 6. Logging and redaction

Logs may include:

- timestamp and correlation ID
- actor/workload and tenant/site
- operation type and risk class
- relative approved path/domain/object reference
- policy/schema/release version
- payload/file hash
- approval and idempotency references
- provider request/reference ID
- status/readback/rollback state
- sanitized error class

Logs must not include:

- passwords
- API secrets
- access/refresh tokens
- authorization headers
- private keys
- full confidential payloads
- raw backend exceptions if they may disclose sensitive values

### 7. Network/API controls

Remote HTTP MCP and provider-facing services require TLS, explicit origin/host validation, authentication, tenant/object authorization, request-size/content-type limits, rate/concurrency limits, timeouts, circuit breakers and sanitized errors. Outbound URL access must be restricted to reduce SSRF and credential-exfiltration risk.

### 8. Tool and supply-chain controls

Tool names, descriptions, schemas, routes and server identity are versioned and treated as security-relevant. Unexpected tool-manifest drift fails closed. Third-party MCP servers, packages and Actions require review/allowlisting; dynamic unreviewed production MCP installation is prohibited.

## Risk classification

| Operation | Risk | Default mode |
|---|---:|---|
| Domain listing | Low | Allowed after authorization |
| DNS listing | Low/medium | Allowed after authorization |
| Invoice listing | Medium | Sanitized read only |
| DNS create/update/delete | High | Paused until controlled-write release |
| HTTP forward create/update/delete | High | Paused until controlled-write release |
| SFTP file list | Medium | Allowed after path-jail validation |
| SFTP file read | Medium/high | Limited extensions, size and roots |
| SFTP upload/replace | High | Paused until backup/readback/approval controls pass |
| SFTP delete | Very high | Disabled unless separately approved |
| SQL parameterized read | Medium/high | Separate least-privilege adapter if implemented |
| SQL mutation/migration | Very high | Separate release train; transaction/rollback/approval required |
| Arbitrary SQL/shell | Critical | Prohibited MCP capability |

## Production release rule

Production write access may only be enabled for the exact approved action when all applicable gates pass:

```text
validation_passed=true
identity_and_tenant_authz_verified=true
credential_boundary_verified=true
backup_verified=true
rollback_or_rectification_verified=true
idempotency_and_replay_verified=true
readback_verified=true
audit_log_verified=true
kill_switch_verified=true
operator_approval=true
release_manifest_matches_runtime=true
```

A single global `WRITE_TOOLS_ENABLED=true` is never sufficient authorization for production writes.

## Incident response

If a credential, machine or runtime is suspected compromised: activate the relevant kill switch, revoke/rotate credentials and sessions, preserve privacy-minimized evidence, validate adjacent identities/tenants, reconcile provider state, restore if needed, fix the root cause and rerun security/regression tests before re-enable. A credential committed to Git is considered compromised even if quickly removed.