# Domeneshop MCP Phase Plan — 22:34, 25.06.2026

## 0. Operating principle

This plan creates a controlled Domeneshop MCP bridge. The bridge must start as read-only and move to write-capable operation only after validation, backup, path-jail, approval, and rollback controls are verified.

The implementation must not expose unrestricted FTP, SFTP, SCP, shell, or DNS write access to the AI layer.

---

## Phase 1 — Repository baseline and governance

### Objective

Create the GitHub repository baseline for the Domeneshop MCP implementation.

### Actions

1. Confirm target repository:
   - `nanotech-solutions-norway/Domeneshop---MCP-`
2. Add repository documentation:
   - `README.md`
   - `docs/DOMENESHOP_MCP_PHASE_PLAN_2234_25062026.md`
   - `docs/SECURITY_AND_WRITE_CONTROL.md`
   - `docs/TOOL_CATALOG.md`
   - `docs/VALIDATION_CHECKLIST.md`
3. Add environment template:
   - `config/domeneshop-mcp.env.example`
4. Add validation workflow:
   - `.github/workflows/validate-domeneshop-mcp.yml`
5. Protect sensitive material:
   - no API token
   - no API secret
   - no FTP/SFTP/SCP password
   - no SSH key
   - no customer/private accounting data
   - no production `.env`

### Acceptance criteria

- Repository contains documentation and validation scaffold.
- No secrets are committed.
- Write mode is explicitly paused.
- Repository can be cloned and validated locally.

---

## Phase 2 — Domeneshop API read connector

### Objective

Implement read-only Domeneshop API operations.

### Scope

Domeneshop API read functions:

1. List domains.
2. Find domain by ID.
3. List DNS records for domain.
4. Find DNS record by ID.
5. List HTTP forwards.
6. Find HTTP forward by host.
7. List invoices.
8. Find invoice by invoice number.

### Technical route

- API base URL: `https://api.domeneshop.no/v0`
- Authentication: HTTP Basic Auth
- Username: API token
- Password: API secret

### MCP tools

```text
domeneshop_list_domains
domeneshop_get_domain
domeneshop_list_dns_records
domeneshop_get_dns_record
domeneshop_list_http_forwards
domeneshop_get_http_forward
domeneshop_list_invoices
domeneshop_get_invoice
```

### Acceptance criteria

- Read calls return sanitized summaries.
- Raw credentials are never logged.
- Errors are returned as controlled MCP errors.
- No write endpoint is callable in this phase.

---

## Phase 3 — SFTP/SCP read connector

### Objective

Implement read-only website file inspection for Domeneshop hosting.

### Scope

Read-only file operations:

1. List allowed directories.
2. Fetch metadata for a file.
3. Download selected text files for review.
4. Compute file hashes.
5. Confirm deployment root paths.

### Allowed roots

```text
/www/
/www/solarex_forms/
/www/atlas_control/
/www/atlas_pip2/
```

### Disallowed operations

- upload
- overwrite
- delete
- chmod/chown
- recursive destructive actions
- shell command execution through file connector

### Acceptance criteria

- Path traversal is blocked.
- Symlink escape is blocked or reported as manual review.
- File reads are restricted to allowlisted extensions and size limits.
- Binary files are listed but not read unless explicitly supported.

---

## Phase 4 — Health and diagnostics endpoints

### Objective

Create controlled diagnostics for deployed Domeneshop-hosted PHP systems.

### Scope

Add read-only MCP tools for health URLs such as:

```text
https://forms.nanotech-solutions.com/solarex_forms/health.php
https://monitor.atlas-ai.no/login.php
https://pip.atlas-ai.no/health.php
```

### MCP tools

```text
http_check_endpoint
http_check_json_health
http_check_php_status
http_check_tls
```

### Acceptance criteria

- Endpoint checks redact secrets and tokens.
- Unauthorized responses are summarized without raw backend detail.
- Health checks classify status as:
  - `healthy`
  - `degraded`
  - `unauthorized_expected`
  - `not_found`
  - `manual_review_required`

---

## Phase 5 — GitHub Actions deploy lane, dry-run only

### Objective

Prepare a GitHub Actions deployment workflow without enabling production writes.

### Actions

1. Add deployment workflow template.
2. Add dry-run mode.
3. Add file manifest generation.
4. Add hash comparison.
5. Add planned-upload summary.
6. Block live upload unless explicit environment variable is set.

### Required secrets

```text
DOMENESHOP_SFTP_HOST
DOMENESHOP_SFTP_USER
DOMENESHOP_SFTP_PASSWORD
DOMENESHOP_SFTP_PORT
DOMENESHOP_REMOTE_ROOT
```

### Acceptance criteria

- Workflow runs validation without pushing to Domeneshop.
- Missing secrets do not fail documentation validation.
- Production upload is blocked by default.

---

## Phase 6 — Backup and rollback system

### Objective

Implement safe deployment backups before any file write.

### Backup logic

Before overwriting files, the bridge must:

1. Fetch existing remote file.
2. Compute hash.
3. Store timestamped backup.
4. Write local backup manifest.
5. Perform upload.
6. Re-fetch deployed file.
7. Verify hash or content signature.

### Backup path model

```text
/backups/YYYY/MM/DD/HHMMSS/{project}/{relative_path}.bak
```

### Acceptance criteria

- Overwrite without backup is impossible.
- Rollback command can restore the previous version.
- Backup manifests are retained as deployment evidence.

---

## Phase 7 — Approval-gated write activation

### Objective

Enable write-ready code while keeping runtime writes disabled until approval.

### Write activation controls

Write operations require all of the following:

1. `WRITE_TOOLS_ENABLED=true`
2. Approved target domain/path.
3. Valid backup manifest.
4. Explicit action type.
5. Explicit approval token or manual operator confirmation.
6. Audit log entry.

### Allowed write tools after approval

```text
domeneshop_create_dns_record
domeneshop_update_dns_record
domeneshop_delete_dns_record
domeneshop_create_http_forward
domeneshop_update_http_forward
domeneshop_delete_http_forward
sftp_upload_file
sftp_upload_folder
sftp_restore_backup
```

### Acceptance criteria

- Write tools are not registered when paused.
- Dry-run and live-run are visibly different.
- Every write operation produces an audit record.

---

## Phase 8 — MCP server implementation

### Objective

Build the MCP server that exposes only the approved tool set.

### Recommended stack

Either of the following is acceptable:

1. Node.js / TypeScript MCP server.
2. Python MCP server.

### Required modules

```text
src/config
src/security
src/domeneshop-api
src/sftp
src/http-health
src/audit
src/tools
src/server
```

### Acceptance criteria

- MCP server exposes a minimal tool catalog.
- Tools have strict schemas.
- Outputs are sanitized.
- Errors are structured.
- Tool registration respects write-pause mode.

---

## Phase 9 — Production deployment

### Objective

Deploy the MCP bridge to a controlled HTTPS endpoint.

### Deployment constraints

- HTTPS required.
- Server-side credentials only.
- No frontend token exposure.
- Rate limits enabled.
- Audit logging enabled.
- Admin endpoint not publicly exposed.

### Possible endpoint

```text
https://mcp.atlas-ai.no/domeneshop
```

### Acceptance criteria

- MCP server is reachable from approved clients.
- Health endpoint returns safe status.
- Write mode remains off unless explicitly approved.

---

## Phase 10 — Operational runbook

### Objective

Create a practical operating model for maintenance and incident response.

### Required runbooks

1. DNS read review.
2. DNS write approval.
3. SFTP dry-run deploy.
4. Production deploy.
5. Rollback.
6. Credential rotation.
7. Audit export.
8. Failed deployment recovery.

### Acceptance criteria

- Non-technical operator can follow the steps.
- All risky actions include pre-checks and rollback steps.
- All commands avoid exposing secrets.

---

## Phase 11 — Integration with existing Atlas/SolarEX/Domeneshop estate

### Objective

Connect the bridge to existing project paths and hosted endpoints.

### Known target areas

```text
/www/solarex_forms/
/www/atlas_control/
/www/atlas_pip2/
forms.nanotech-solutions.com
monitor.atlas-ai.no
pip.atlas-ai.no
```

### Acceptance criteria

- Existing paths are mapped before deployment.
- No old working files are overwritten without backup.
- Health checks are run after every deployment.

---

## Phase 12 — Final validation and release gate

### Objective

Approve or reject production readiness.

### Release gate checklist

1. Repository validation passes.
2. No secrets in repo.
3. API read tools pass.
4. SFTP read tools pass.
5. Health checks pass.
6. Dry-run deployment passes.
7. Backup/rollback tested.
8. Audit logs verified.
9. Write tools remain paused unless approved.
10. Production endpoint has HTTPS and authentication.

### Final classification

Until Phase 12 is passed, classify the implementation as:

```text
PENDING_REVIEW
```
