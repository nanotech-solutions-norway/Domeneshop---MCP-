# Domeneshop MCP Tool Catalog — 00:10, 27.06.2026

## Tool registration model

Tools must be registered in tiers.

```text
Tier 1: Safe read tools
Tier 2: Controlled diagnostics
Tier 3: Read-only hosted-file inspection and dry-run planning
Tier 4: Recovery planning tools
Tier 5: Control-plane approval and audit tools
Tier 6: Approval-gated future change tools
```

## Tier 1 — Domeneshop API read tools

| Tool | Purpose | Change risk |
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

| Tool | Purpose | Change risk |
|---|---|---:|
| `http_check_endpoint` | HTTP status check | None |
| `http_check_json_health` | JSON health endpoint check | None |
| `http_check_tls` | TLS availability check | None |

## Tier 3 — Hosted-file read and dry-run planning tools

| Tool | Purpose | Change risk |
|---|---|---:|
| `sftp_list_allowed_roots` | List configured remote roots | None |
| `sftp_list_files` | List files inside allowed root | None |
| `sftp_get_file_metadata` | Size, modified time, hash | None |
| `sftp_read_text_file` | Read limited text files | None |
| `deployment_build_local_manifest` | Build local file manifest | None |
| `deployment_compare_manifest` | Compare local manifest with supplied remote metadata | None |

## Tier 4 — Recovery planning tools

| Tool | Purpose | Change risk |
|---|---|---:|
| `recovery_build_backup_manifest` | Build backup evidence manifest from a dry-run plan | None |
| `recovery_build_restore_preview` | Build recovery preview from backup evidence manifest | None |

## Tier 5 — Control-plane approval and audit tools

| Tool | Purpose | Change risk |
|---|---|---:|
| `control_evaluate_change_preflight` | Evaluate approval, evidence, and risk controls | None |
| `control_build_audit_event` | Build hashed audit-event model | None |

## Tier 6 — Approval-gated future change tools

These tools must not be registered while change mode is paused.

| Tool | Purpose | Required controls |
|---|---|---|
| `domeneshop_create_dns_record` | Add DNS record | approval + audit |
| `domeneshop_update_dns_record` | Update DNS record | pre-read + approval + audit |
| `domeneshop_delete_dns_record` | Remove DNS record | pre-read + approval + audit |
| `domeneshop_create_http_forward` | Add forwarding | approval + audit |
| `domeneshop_update_http_forward` | Update forwarding | pre-read + approval + audit |
| `domeneshop_delete_http_forward` | Remove forwarding | pre-read + approval + audit |
| `sftp_upload_file` | Transfer one file | backup + hash + approval + audit |
| `sftp_upload_folder` | Transfer folder | manifest + backup + approval + audit |
| `sftp_restore_backup` | Apply backup copy | approval + audit |

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
