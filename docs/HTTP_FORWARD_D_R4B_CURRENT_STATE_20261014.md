# D-R4B HTTP-forward Current State — 2026-10-14

## Result

D-R4B is partially validated and must remain fail-closed for host-addressed UPDATE/DELETE operations involving the isolated hyphenated validation host.

Accepted evidence establishes:

- isolated HTTP-forward CREATE succeeded;
- list-forwards GET independently verified the exact accepted CREATE state;
- an exact separately authorized UPDATE attempt returned HTTP 404;
- GET-only recovery verification proved the accepted CREATE state remained unchanged;
- single-host GET route diagnostics also returned HTTP 404 while the list endpoint continued to return the forward;
- Domeneshop support confirmed the provider-side validator defect for hyphenated host elements;
- no retry of UPDATE and no DELETE is authorized.

## Current classification

```text
D_R4B_HTTP_FORWARD_CREATE=OPERATOR_ACCEPTED
D_R4B_LIST_READBACK=VALIDATED
D_R4B_SINGLE_HOST_READ_HYPHENATED=BLOCKED_PROVIDER_DEFECT
D_R4B_UPDATE_HYPHENATED=BLOCKED_PROVIDER_DEFECT
D_R4B_DELETE_HYPHENATED=BLOCKED_PROVIDER_DEFECT
GENERAL_HTTP_FORWARD_MUTATION=BLOCKED
WRITE_TOOLS_ENABLED=false
HOLD_LIVE_CHANGE_ACTIVATION=true
NO_AUTONOMOUS_LIVE_CHANGE=true
```

## Safe next step

Do not retry the existing hyphenated target.

Resume D-R4B mutation testing only if one of these conditions is met:

1. Domeneshop confirms the defect is fixed and a GET-only diagnostic verifies the documented single-host route first; or
2. a new isolated **non-hyphenated** validation host is selected through collision-safe GET-only preflight, followed by deterministic dry-run evidence and a new exact one-use authorization for each mutation.

Either path is a new work unit. Existing authorization material must not be reused.

## Non-blocking relationship to Conta MCP

The HTTP-forward defect does not block the current Conta MCP operational-v1 endpoint because that endpoint uses the existing webhotel/virtualhost document-root topology rather than the defective D-R4B single-host UPDATE path.

## Status

```text
PROVIDER_DEFECT=CONFIRMED
RETRY_EXISTING_UPDATE=false
DELETE_AUTHORIZED=false
NEW_TARGET_AUTHORIZED=false
NEXT_GATE=GET_ONLY_PROVIDER_FIX_VERIFICATION_OR_NEW_NON_HYPHENATED_TARGET_PREFLIGHT
```
