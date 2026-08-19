# D-R3 TXT UPDATE Release Gate — 19.08.2026

## Purpose

Prepare the second controlled D-R3 provider mutation without authorizing it. This gate defines the exact TXT UPDATE payload and the read-only validation required before any PUT request may occur.

The already accepted CREATE state is the mandatory before-state.

## Existing accepted CREATE state

```text
Action: domeneshop_create_dns_txt
Domain: atlas-mcp-sandbox.no
Host: _mcp-validation
Type: TXT
Data: mcp-validation=D-R3-TXT-PREFLIGHT-20260810
TTL: 300
Target SHA-256: 5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e
Payload SHA-256: 6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c
```

CREATE execution has been accepted as `created_and_readback_verified`, with provider CREATE returned, independent readback verified, audit chain valid, and process write capability reset to false.

## Proposed exact UPDATE

```text
Action: domeneshop_update_dns_txt
Domain: atlas-mcp-sandbox.no
Host: _mcp-validation
Type: TXT
Data: mcp-validation=D-R3-TXT-UPDATE-20260819
TTL: 300
Target SHA-256: 5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e
Update payload SHA-256: 58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087
Proposed release identity: D-R3-TXT-UPDATE-20260819-001
```

Only the TXT `data` value changes. Host, record type, and TTL remain unchanged.

## Mandatory read-only dry run

The Office-PC dry run must:

1. run with `WRITE_TOOLS_ENABLED=false` and `DRY_RUN_DEFAULT=true`;
2. resolve the exact protected domain through authenticated GET;
3. require exactly one TXT record at `_mcp-validation`;
4. verify that record still matches the accepted CREATE payload;
5. derive the provider record ID but emit only its SHA-256 hash;
6. recompute and match the accepted target hash;
7. recompute and match the accepted CREATE payload hash;
8. recompute and match the proposed UPDATE payload hash;
9. create no approval token, idempotency reservation, audit event, or provider mutation.

Accepted dry-run status:

```text
success=true
status=update_dry_run_ok
existing_txt_record_count=1
existing_create_state_verified=true
provider_mutation_performed=false
write_tools_enabled=false
approval_token_issued=false
idempotency_reservation_created=false
audit_event_created=false
```

## Authorization boundary

This document and the dry-run package do **not** authorize the UPDATE.

A provider PUT may only be prepared for execution after a separate explicit operator instruction:

```text
Authorize D-R3 TXT UPDATE
```

The authorization, if given, is limited to the exact payload/hash above and one exact existing TXT record resolved from the accepted CREATE state.

## Explicit exclusions

```text
NO TXT DELETE
NO TXT RESTORE / ROLLBACK
NO SECOND TXT CREATE
NO MX CHANGE
NO NS CHANGE
NO GENERAL DNS CHANGE
NO HTTP FORWARD CHANGE
NO FILE WRITE
NO SQL WRITE
NO GLOBAL WRITE ACTIVATION
```

Rollback/restore remains a third, separately authorized mutation class.

## Decision after dry run

```text
UPDATE_DRY_RUN_ACCEPTED
or
HOLD_FOR_FIX
```

Provider UPDATE remains unauthorized until the operator gives the exact separate authorization after reviewing accepted dry-run evidence.
