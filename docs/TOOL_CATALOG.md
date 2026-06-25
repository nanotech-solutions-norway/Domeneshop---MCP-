# Domeneshop MCP Tool Catalog — 22:34, 25.06.2026

## Tool registration model

Tools must be registered in tiers.

```text
Tier 1: Safe read tools
Tier 2: Controlled diagnostics
Tier 3: Dry-run deployment tools
Tier 4: Approval-gated write tools
Tier 5: Emergency rollback tools
```

## Tier 1 — Domeneshop API read tools

| Tool | Purpose | Write risk |
|---|---|---:|
| `domeneshop_list_domains` | List available domains | None |
| `domeneshop_get_domain` | Fetch one domain by ID | None |
| `domeneshop_list_dns_records` | List DNS records | None |
| `domeneshop_get_dns_record` | Fetch one DNS record | None |
| `domeneshop_list_http_forwards` | List HTTP forwards | None |
| `domeneshop_get_http_forward` | Fetch one forward | None |
| `domeneshop_list_invoices` | List invoices with sanitized output | None |
| `domeneshop_get_invoice` | Fetch invoice summary | None |

## Tier 2 — Diagnostics tools

| Tool | Purpose | Write risk |
|---|---|---:|
| `http_check_endpoint` | HTTP status check | None |
| `http_check_json_health` | JSON health endpoint check | None |
| `http_check_tls` | TLS availability check | None |
| `deployment_compare_manifest` | Compare intended files with remote metadata | None |

## Tier 3 — SFTP/SCP read and dry-run tools

| Tool | Purpose | Write risk |
|---|---|---:|
| `sftp_list_allowed_roots` | List configured remote roots | None |
| `sftp_list_files` | List files inside allowed root | None |
| `sftp_get_file_metadata` | Size, modified time, hash | None |
| `sftp_read_text_file` | Read limited text files | None |
| `sftp_prepare_deploy_manifest` | Prepare upload manifest | None |
| `sftp_deploy_dry_run` | Simulate upload | None |

## Tier 4 — Approval-gated write tools

These tools must not be registered while write mode is paused.

| Tool | Purpose | Required controls |
|---|---|---|
| `domeneshop_create_dns_record` | Add DNS record | approval + audit |
| `domeneshop_update_dns_record` | Update DNS record | pre-read + approval + audit |
| `domeneshop_delete_dns_record` | Delete DNS record | pre-read + approval + audit |
| `domeneshop_create_http_forward` | Add forwarding | approval + audit |
| `domeneshop_update_http_forward` | Update forwarding | pre-read + approval + audit |
| `domeneshop_delete_http_forward` | Delete forwarding | pre-read + approval + audit |
| `sftp_upload_file` | Upload one file | backup + hash + approval + audit |
| `sftp_upload_folder` | Upload folder | manifest + backup + approval + audit |

## Tier 5 — Rollback tools

| Tool | Purpose | Default mode |
|---|---|---|
| `sftp_list_backups` | List available backups | Read allowed |
| `sftp_restore_backup_dry_run` | Preview rollback | Read allowed |
| `sftp_restore_backup` | Restore backup | Approval-gated |

## Output rules

All tools must return normalized envelopes:

```json
{
  "success": true,
  "status": "ok",
  "mode": "read_only",
  "write_paused": true,
  "data": {},
  "warnings": [],
  "audit_id": "optional"
}
```

## Error classes

```text
configuration_missing
credential_missing
unauthorized
not_found
validation_failed
path_not_allowed
write_paused
backup_required
manual_review_required
provider_error
```
