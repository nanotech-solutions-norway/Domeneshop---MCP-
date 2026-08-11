# D-R3 Isolated DNS TXT Pilot Preflight

## Purpose

This manual protected workflow prepares, but does not authorize or perform, the first DNS TXT pilot. It resolves an operator-selected domain name to its Domeneshop API ID, verifies active DNS service, then performs an authenticated GET for the exact `_mcp-validation` TXT host. It fails if the domain cannot be resolved exactly or if that host already contains a TXT record.

## Provisioning gate

On 11.08.2026 an isolated non-production candidate was confirmed available through Domeneshop's public registration search. The candidate name is intentionally kept outside the repository. Registration is still pending explicit purchase confirmation and successful account checkout.

Do not add `DS_PILOT_DOMAIN_NAME` until all of the following are true:

1. the candidate has been registered in the intended Domeneshop account;
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
