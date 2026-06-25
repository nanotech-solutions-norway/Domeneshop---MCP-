# Domeneshop MCP Security and Write Control — 22:34, 25.06.2026

## Security posture

The Domeneshop MCP bridge must be read-first, least-privilege, auditable, and reversible.

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

Never commit:

- Domeneshop API token
- Domeneshop API secret
- FTP/SFTP/SCP password
- SSH private key
- production `.env`
- private customer/accounting data
- bank/account identifiers

Use only:

- GitHub Actions secrets
- server-side environment variables
- hosting-provider secret stores

### 3. Path jail

Allowed roots:

```text
/www/
/www/solarex_forms/
/www/atlas_control/
/www/atlas_pip2/
```

Block:

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

### 4. Backup-before-write

All overwrites require:

1. Remote read.
2. Hash before write.
3. Timestamped backup.
4. Upload.
5. Remote re-read.
6. Hash/content verification.
7. Audit log.

### 5. Approval-gated writes

A write operation must include:

- target path or domain
- exact operation
- dry-run preview
- backup manifest
- explicit approval
- audit entry

### 6. Logging and redaction

Logs may include:

- timestamp
- operation type
- relative path
- domain
- status
- file hash
- sanitized error class

Logs must not include:

- passwords
- API secrets
- tokens
- private keys
- full raw backend exceptions if sensitive

## Risk classification

| Operation | Risk | Default mode |
|---|---:|---|
| Domain listing | Low | Allowed |
| DNS listing | Low/medium | Allowed |
| Invoice listing | Medium | Sanitized read only |
| DNS create/update/delete | High | Paused |
| HTTP forward create/update/delete | High | Paused |
| SFTP file list | Medium | Allowed after path-jail validation |
| SFTP file read | Medium/high | Limited extensions and size |
| SFTP upload | High | Paused |
| SFTP delete | Very high | Disabled unless separately approved |
| SSH command | Very high | Not exposed as general MCP tool |

## Production release rule

Production write access may only be enabled after:

```text
validation_passed=true
backup_verified=true
rollback_verified=true
audit_log_verified=true
operator_approval=true
WRITE_TOOLS_ENABLED=true
```
