# Domeneshop MCP Protected Read-Only Validation — 10.08.2026

## Classification

```text
PROTECTED_READONLY_VALIDATION_PASSED=true
AUTHENTICATED_DOMENESHOP_API_READ_VALIDATED=true
AUTHENTICATED_SFTP_READ_VALIDATED=true
MCP_STDIO_READONLY_DISCOVERY_VALIDATED=true
PUBLIC_STATUS_SURFACE_GET_OBSERVED=true
STATUS_SURFACE_WORKFLOW_VALIDATED=true
PROVIDER_MUTATION_PERFORMED=false
WRITE_TOOLS_ENABLED=false
HOLD_LIVE_CHANGE_ACTIVATION
```

## Accepted evidence

The manually approved protected GitHub Actions workflow completed successfully against accepted `main` commit:

```text
commit=5beb51ccce1a07eb22e083432ee9e0ad439a1e41
run_id=31384070264
run_url=https://github.com/nanotech-solutions-norway/Domeneshop---MCP-/actions/runs/31384070264
completed_utc=2026-08-10T11:35:04Z
```

The run passed:

- credential-presence and fail-closed configuration gates;
- repository structure and controlled-write hold validation;
- MCP stdio initialization and read-only tool discovery;
- an authenticated Domeneshop domain-list GET;
- authenticated SFTP allowed-root and directory-list reads.

Only sanitized aggregates were retained:

```text
domeneshop_domain_list_item_count=38
sftp_allowed_root_count=1
sftp_directory_item_count=11
warnings_count=0
payload_included=false
```

No provider payload, remote path, credential, authorization header, DNS value, or customer-specific identifier was included in the evidence.

## Status-surface observation and workflow closure

The successful workflow did not include the separate PHP status surface at `https://ds.atlas-ai.no/`. That endpoint is not the MCP transport.

An unauthenticated GET from the Office PC on 10.08.2026 returned:

```text
http_status=200
content_type=application/json; charset=utf-8
www_authenticate_header=absent
response_body_retained=false
```

This evidence supersedes the earlier assumption that separate Basic Auth credentials were required. No `DS_STATUS_AUTH_USER` or `DS_STATUS_AUTH_VALUE` exists or is required by the prepared workflow.

The repository now prepares a bounded unauthenticated GET-only validation using:

```text
DS_STATUS_URL=https://ds.atlas-ai.no/
```

The validator allows only HTTPS to `ds.atlas-ai.no`, sends no authentication, follows no redirects, bounds the response, requires a JSON object, and emits payload-free evidence.

## Accepted status-surface workflow evidence

The manually approved protected workflow subsequently completed successfully against merged `main` commit:

```text
commit=8ea925cc00dccd0177832077ef6b0c2e02d7d9b5
run_id=31403862923
run_url=https://github.com/nanotech-solutions-norway/Domeneshop---MCP-/actions/runs/31403862923
completed_utc=2026-08-10T15:46:35Z
```

The run repeated the credential and fail-closed configuration gates, repository and controlled-write validation, MCP read-only discovery, authenticated Domeneshop API read, and authenticated SFTP reads. It also produced the following sanitized status evidence:

```text
evidence_type=status_surface_get
success=true
mode=read_only_http_get
http_status=200
authentication_sent=false
json_object=true
json_key_count=5
payload_included=false
```

The controlled-write foundation reported `live_execution_enabled=false`. No response payload, credential, authorization header, provider record, remote path, DNS value, or customer-specific identifier was retained.

## D-R3 isolated-target hold — 11.08.2026

The operator confirmed that no isolated non-production Domeneshop domain is available for the TXT pilot. Protected GET-only preparation runs failed closed during target selection and performed no provider mutation. The temporary `DS_PILOT_DOMAIN_ID` and `DS_PILOT_DOMAIN_NAME` selector secrets were removed from the protected environment after this decision; validated API and SFTP read credentials remain unchanged.

```text
ISOLATED_NON_PRODUCTION_DOMAIN_AVAILABLE=false
DNS_TXT_PILOT_PREFLIGHT_ACCEPTED=false
PROVIDER_MUTATION_PERFORMED=false
WRITE_TOOLS_ENABLED=false
HOLD_NO_ISOLATED_TARGET
HOLD_LIVE_CHANGE_ACTIVATION
```

## Progress continuity

```text
completion_target=CONTROLLED_DNS_TXT_CHANGE_CAPABILITY
operator_status_progress_carried_forward=82%
progress_recalculated=false
scope_changed=false
current_process=D_R3_BLOCKED_NO_ISOLATED_TARGET
next_gate=PROVISION_OR_APPROVE_ISOLATED_NON_PRODUCTION_DOMAIN
```

The carried percentage is not activation authority. It remains evidence-weighted by the existing project status and is not increased by this preparation-only change.

## Preserved execution boundary

```text
NO DNS MUTATION
NO FILE WRITE
NO SQL WRITE
NO PROVIDER MUTATION
NO WRITE TOOL REGISTRATION
NO AUTONOMOUS LIVE CHANGE
HOLD_LIVE_CHANGE_ACTIVATION
```

D-R3 still requires an explicitly approved isolated domain ID and TXT host, protected signing/audit/idempotency runtime storage, deterministic dry-run evidence, and a separate operator authorization before any mutation.

## D-R3 isolated-domain provisioning preparation — 11.08.2026

The operator subsequently requested creation of an isolated non-production domain. On 11.08.2026 the domain was confirmed active in the authenticated Domeneshop control panel. Its name is intentionally retained outside the repository and protected evidence. Authenticated API discovery and DNS-service validation have not yet been completed.

```text
ISOLATED_DOMAIN_CANDIDATE_AVAILABLE=true
ISOLATED_DOMAIN_REGISTERED=true
AUTHENTICATED_API_DISCOVERY_PENDING=true
DS_PILOT_DOMAIN_NAME_CONFIGURED=false
PROVIDER_MUTATION_PERFORMED=false
WRITE_TOOLS_ENABLED=false
HOLD_PENDING_AUTHENTICATED_API_DISCOVERY
HOLD_LIVE_CHANGE_ACTIVATION
```

The next gate is manual protected configuration of `DS_PILOT_DOMAIN_NAME`, followed by authenticated GET-only discovery and the protected TXT preflight. Progress remains carried at 82%; control-panel registration evidence alone does not close a runtime evidence gate.

## D-R3 protected isolated-target preflight — 16.08.2026

The operator configured `DS_PILOT_DOMAIN_NAME` in the protected `domeneshop-readonly-validation` environment. Protected workflow run `31966109707` executed from accepted `main` commit `8248e7f8577f10e9a8afa5c4fd1e756ece71bb8b` and completed successfully. Sanitized evidence confirmed one exact active API target, zero existing TXT records at the fixed validation host, no collision, manifest allowlisting, disabled live execution, disabled write tools, no provider mutation, and no retained payload.

```text
DS_PILOT_DOMAIN_NAME_CONFIGURED=true
AUTHENTICATED_API_DISCOVERY_PENDING=false
PROTECTED_GET_ONLY_PREFLIGHT_PASSED=true
EXISTING_TXT_RECORD_COUNT=0
COLLISION_DETECTED=false
ALLOWED_BY_MANIFEST=true
LIVE_EXECUTION_ENABLED=false
WRITE_TOOLS_ENABLED=false
PROVIDER_MUTATION_PERFORMED=false
PAYLOAD_INCLUDED=false
HOLD_PENDING_RUNTIME_STORAGE_AND_DRY_RUN
HOLD_LIVE_CHANGE_ACTIVATION
```

Progress remains carried at 82% because the approved rollout plan does not assign a separate weight to this substep. The current process is protected approval-signing, audit, and idempotency runtime-storage preparation; the next evidence gate is a deterministic controlled-write dry-run. A DNS mutation still requires separate operator authorization.

## D-R3 controlled-write dry-run preparation — 16.08.2026

An exact-target protected dry-run workflow and sanitized evidence contract were implemented. The workflow revalidates the active target and empty fixed TXT host, validates the protected signing secret and state-directory initialization, and builds a disabled-live controlled-write preview. It explicitly creates no approval token, idempotency reservation, audit event, or provider mutation.

The Office PC inert state root is prepared outside the repository with access restricted to the current operator, `SYSTEM`, and local administrators. No Domeneshop service identity is installed on that host, so this is preparation evidence only and must not be represented as production runtime storage.

```text
CONTROLLED_WRITE_DRY_RUN_WORKFLOW_IMPLEMENTED=true
PROTECTED_DRY_RUN_EXECUTION_PENDING=true
APPROVAL_TOKEN_ISSUED=false
IDEMPOTENCY_RESERVATION_CREATED=false
AUDIT_EVENT_CREATED=false
PROVIDER_MUTATION_PERFORMED=false
WRITE_TOOLS_ENABLED=false
HOLD_PENDING_PROTECTED_DRY_RUN
HOLD_LIVE_CHANGE_ACTIVATION
```

Progress remains carried at 82% pending protected execution evidence. The next operator-only input is the unique `APPROVAL_SIGNING_SECRET` value in the protected GitHub environment.
