# D-R3 Protected DNS TXT Controlled-Write Dry Run

## Purpose

The manual `validate-dns-txt-pilot-dry-run.yml` workflow validates the exact isolated target, proposed TXT payload hash, protected signing-secret readiness, file-backed state layout, release allowlist, and mandatory control requirements without issuing an approval token or performing a provider mutation.

The workflow runs only in the protected `domeneshop-readonly-validation` environment and retains the existing safety posture:

```text
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
LIVE_EXECUTION_ENABLED=false
NO APPROVAL TOKEN ISSUED
NO IDEMPOTENCY RESERVATION
NO AUDIT EVENT CREATED
NO PROVIDER MUTATION
HOLD_LIVE_CHANGE_ACTIVATION
```

## Protected inputs

- existing secrets `DS_AUTH_USER`, `DS_AUTH_VALUE`, and `DS_PILOT_DOMAIN_NAME`;
- new secret `APPROVAL_SIGNING_SECRET`, at least 32 bytes and unique to this pilot;
- fixed variable `DS_PILOT_TXT_HOST=_mcp-validation`;
- fixed variables `WRITE_TOOLS_ENABLED=false`, `DRY_RUN_DEFAULT=true`, and `REQUIRE_OPERATOR_APPROVAL=true`.

Secret values, domain names, provider IDs, target strings, host names, proposed TXT values, and provider payloads are excluded from workflow output and artifacts.

## What the workflow proves

1. one exact DNS-enabled domain resolves through an authenticated GET;
2. the fixed TXT host remains collision-free;
3. the exact action, target, and payload are allowed by a disabled-live foundation manifest;
4. all four mandatory controls remain required: approval token, idempotency, append-only audit, and readback;
5. the protected signing secret passes the minimum runtime policy;
6. the nonce, idempotency, and audit paths can be initialized;
7. no approval token, idempotency reservation, audit event, provider write, or payload disclosure occurs.

## Evidence acceptance

Accept only a successful protected run from the intended `main` commit whose sanitized report contains:

```text
mode=controlled_write_preview
allowed_by_manifest=true
live_execution_enabled=false
write_tools_enabled=false
state_directories_ready=true
approval_signing_secret_validated=true
approval_token_issued=false
idempotency_reservation_created=false
audit_event_created=false
provider_mutation_performed=false
payload_included=false
target_included=false
```

Passing this dry run does not authorize a live manifest, an approval token, write-tool registration, or a DNS mutation. Those remain separate operator gates.
