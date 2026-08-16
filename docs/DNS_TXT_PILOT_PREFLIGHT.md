# D-R3 Isolated DNS TXT Pilot Preflight

## Purpose

This manual protected workflow prepares, but does not authorize or perform, the first DNS TXT pilot. It resolves an operator-selected domain name to its Domeneshop API ID, verifies active DNS service, then performs an authenticated GET for the exact `_mcp-validation` TXT host. It fails if the domain cannot be resolved exactly or if that host already contains a TXT record.

## Provisioning gate

On 11.08.2026 the isolated non-production domain was confirmed as active in the authenticated Domeneshop control panel. On 16.08.2026 protected run `31966109707` independently resolved one exact active target through the authenticated API and completed the fixed-host GET-only preflight. The domain name remains intentionally outside the repository.

Do not run the protected preflight until all of the following are true:

1. the domain has been registered in the intended Domeneshop account;
2. DNS service is active and the domain appears in the authenticated API domain list;
3. the domain has no production mail, web, forwarding, nameserver, or customer-data dependency;
4. the operator has approved it exclusively for the D-R3 TXT pilot.

Server-side file placement and configuration are defined in `docs/DNS_TXT_PILOT_SERVER_CONFIGURATION.md`.

## Protected configuration

The existing `domeneshop-readonly-validation` environment supplies:

```text
DS_AUTH_USER=<existing environment secret>
DS_AUTH_VALUE=<existing environment secret>
DS_PILOT_DOMAIN_NAME=<operator-selected isolated domain name secret>
DS_PILOT_TXT_HOST=_mcp-validation
WRITE_TOOLS_ENABLED=false
DRY_RUN_DEFAULT=true
REQUIRE_OPERATOR_APPROVAL=true
```

The domain name and resolved API ID remain outside the repository and workflow logs. The resolver accepts one exact domain match with active DNS service; partial or ambiguous matches fail closed. The host is fixed rather than operator-variable.

## Sanitized evidence

The workflow emits only:

- a one-way target hash;
- a deterministic payload hash;
- zero-record/collision state;
- manifest-allowlist and disabled-live-execution state;
- explicit no-mutation and no-payload markers.

It never prints the domain name, resolved domain ID, host, proposed TXT value, provider response, authorization header, or credentials.
Provider failures retain only the repository's bounded error class, such as `unauthorized` or `not_found`; provider messages and response bodies remain excluded.

## Accepted protected run — 16.08.2026

Protected workflow run `31966109707`, on accepted `main` commit `8248e7f8577f10e9a8afa5c4fd1e756ece71bb8b`, passed with the following sanitized evidence:

```text
exact_active_target_resolved=true
existing_txt_record_count=0
collision_detected=false
allowed_by_manifest=true
live_execution_enabled=false
write_tools_enabled=false
provider_mutation_performed=false
payload_included=false
```

The result validates only target discovery and collision-free GET-only preparation. It does not issue an approval token, reserve an idempotency key, create a live audit release, enable a write tool, or authorize a DNS change.

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
