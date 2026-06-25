# Domeneshop MCP Validation Checklist — 22:34, 25.06.2026

## Repository validation

- [ ] README exists.
- [ ] Phase plan exists.
- [ ] Security model exists.
- [ ] Tool catalog exists.
- [ ] Environment template exists.
- [ ] Workflow exists.
- [ ] No production `.env` exists.
- [ ] No private key exists.
- [ ] No token/secret/password literal exists.

## Domeneshop API validation

- [ ] API base URL configured.
- [ ] Token provided through environment only.
- [ ] Secret provided through environment only.
- [ ] Domain listing works.
- [ ] DNS listing works.
- [ ] HTTP forwards listing works.
- [ ] Invoice listing is sanitized.
- [ ] Failed authentication returns controlled error.

## SFTP/SCP validation

- [ ] Host configured.
- [ ] User configured.
- [ ] Password/key configured server-side only.
- [ ] Path jail active.
- [ ] Remote root exists.
- [ ] File listing works.
- [ ] Path traversal blocked.
- [ ] Symlink escape blocked or flagged.
- [ ] File read size limit enforced.

## Deployment dry-run validation

- [ ] Local manifest generated.
- [ ] Remote manifest generated.
- [ ] Hash comparison generated.
- [ ] Planned uploads listed.
- [ ] Planned overwrites listed.
- [ ] No live upload occurs.

## Backup validation

- [ ] Backup root configured.
- [ ] Backup manifest generated.
- [ ] Existing remote file backed up before overwrite.
- [ ] Backup hash recorded.
- [ ] Restore dry-run works.
- [ ] Restore live run remains approval-gated.

## Write activation validation

- [ ] `WRITE_TOOLS_ENABLED=false` by default.
- [ ] Write tools absent when paused.
- [ ] Write tools present only when enabled.
- [ ] Approval token/manual approval required.
- [ ] Audit log written.
- [ ] Rollback available.

## Production release decision

Final status must be one of:

```text
PENDING_REVIEW
APPROVED_FOR_READ_ONLY
APPROVED_FOR_DRY_RUN_DEPLOY
APPROVED_FOR_APPROVAL_GATED_WRITES
REJECTED
```

Current status:

```text
PENDING_REVIEW
```
