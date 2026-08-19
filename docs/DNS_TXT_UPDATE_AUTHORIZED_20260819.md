# D-R3 TXT UPDATE Authorization — 19.08.2026

## Authorization

Operator explicitly authorized:

```text
Authorize D-R3 TXT UPDATE
```

This authorization applies only to the deterministic UPDATE accepted by the successful GET-only dry run.

## Exact scope

```text
Action: domeneshop_update_dns_txt
Domain: atlas-mcp-sandbox.no
Host: _mcp-validation
Type: TXT
TTL: 300
Release / approval / idempotency identity: D-R3-TXT-UPDATE-20260819-001
Target SHA-256: 5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e
Before payload SHA-256: 6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c
Update payload SHA-256: 58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087
```

The authorized payload changes only the TXT data value from the accepted CREATE-state value to the deterministic D-R3 UPDATE validation value. Host, type, and TTL remain unchanged.

## Mandatory controls

- fresh authenticated target resolution;
- exact single-record CREATE-state pre-read;
- accepted target / before-state / UPDATE payload hash revalidation;
- one-time payload-bound approval token;
- fixed idempotency identity;
- persistent append-only audit;
- independent provider readback;
- process-local write switch only;
- write switch reset to false after execution;
- no raw credential, token, target, payload, record ID, or provider domain ID in sanitized output.

## Explicit exclusions

```text
NO TXT DELETE
NO TXT RESTORE / ROLLBACK
NO TXT CREATE
NO MX CHANGE
NO NS CHANGE
NO GENERAL DNS CHANGE
NO HTTP FORWARD CHANGE
NO FILE WRITE
NO SQL WRITE
NO GLOBAL WRITE ACTIVATION
```

## Failure rule

If `provider_update_returned=false`, stop and diagnose before any retry.

If `provider_update_returned=true` but the overall operation fails, treat the provider state as potentially updated. Do not retry the UPDATE and do not restore/delete automatically. Perform GET-only verification and require a separate explicit restore/delete authorization before compensation.
