# D-R3 Isolated DNS TXT Pilot Preflight

## Purpose

This manual protected workflow prepares, but does not authorize or perform, the first DNS TXT pilot. It performs one authenticated GET for the exact `_mcp-validation` TXT host on an operator-selected domain and fails if that host already contains a TXT record.

## Protected configuration

The existing `domeneshop-readonly-validation` environment supplies:

```text
DS_AUTH_USER=<existing environment secret>
DS_AUTH_VALUE=<existing environment secret>
DS_PILOT_DOMAIN_ID=<operator-selected isolated domain ID secret>
DS_PILOT_TXT_HOST=_mcp-validation
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
```

The domain ID remains outside the repository and workflow logs. The host is fixed rather than operator-variable.

## Sanitized evidence

The workflow emits only:

- a one-way target hash;
- a deterministic payload hash;
- zero-record/collision state;
- manifest-allowlist and disabled-live-execution state;
- explicit no-mutation and no-payload markers.

It never prints the domain ID, host, proposed TXT value, provider response, authorization header, or credentials.
Provider failures retain only the repository's bounded error class, such as `unauthorized` or `not_found`; provider messages and response bodies remain excluded.

## Preserved boundary

```text
GET_ONLY
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
LIVE_EXECUTION_ENABLED=false
NO APPROVAL TOKEN ISSUED
NO IDEMPOTENCY RESERVATION
NO AUDIT RELEASE CREATED
NO PROVIDER MUTATION
HOLD_LIVE_CHANGE_ACTIVATION
```

A successful preflight only confirms that the selected host is isolated and that a deterministic proposed payload is inside the prepared allowlist. It does not authorize create, update, delete, rollback, or any other provider mutation.
