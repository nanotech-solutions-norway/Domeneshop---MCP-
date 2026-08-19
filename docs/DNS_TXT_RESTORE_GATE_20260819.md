# D-R3 DNS TXT Restore Gate — 19.08.2026

## Purpose

Prepare the separately gated restore phase after the successful D-R3 TXT UPDATE without authorizing or performing a provider mutation.

## Current accepted provider state

The isolated TXT record has been successfully updated and independently read back under release `D-R3-TXT-UPDATE-20260819-001`.

Accepted current UPDATE payload SHA-256:

`58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087`

Accepted target SHA-256:

`5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e`

## Proposed restore

The proposed restore returns the same TXT record to the original accepted CREATE payload. No record creation or deletion is involved.

Proposed restore payload:

```json
{
  "host": "_mcp-validation",
  "data": "mcp-validation=D-R3-TXT-PREFLIGHT-20260810",
  "ttl": 300,
  "type": "TXT"
}
```

Proposed restore payload SHA-256:

`6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c`

Proposed release identity:

`D-R3-TXT-RESTORE-20260819-001`

## Dry-run controls

The restore dry run is authenticated GET-only and must verify all of the following before any later authorization can be considered:

- `WRITE_TOOLS_ENABLED=false`;
- exact protected domain resolution;
- exact target hash matches the accepted target hash;
- exactly one TXT record exists at the pilot host;
- the existing record exactly matches the accepted UPDATE state;
- deterministic restore payload exactly matches the original accepted CREATE payload hash;
- no approval token is issued;
- no idempotency reservation is created;
- no audit mutation event is created;
- no provider mutation is performed;
- raw target, payload, record ID and credentials are not emitted.

## Authorization boundary

This document and the associated dry-run package **do not authorize restore or delete**.

A successful dry run may only advance the project to an explicit operator authorization gate for the exact restore described above.

Until that explicit authorization:

```text
TXT_RESTORE_AUTHORIZED=false
TXT_DELETE_AUTHORIZED=false
WRITE_TOOLS_ENABLED=false
NO_PROVIDER_MUTATION
```

Delete remains a distinct operation and is not required for the planned restore, which uses a bounded UPDATE of the existing record back to the original accepted value.
