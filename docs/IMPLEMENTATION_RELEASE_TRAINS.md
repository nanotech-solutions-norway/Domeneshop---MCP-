# Domeneshop MCP Implementation Release Trains — 16:07, 16.07.2026

## D-R0 — Baseline freeze

- Canonical capability registry created.
- Phase 35–48 artifacts retained as governance evidence and classified as reference/readiness material.
- Future work is organized by executable release train rather than additional planning-only phases.

## D-R1 — Read runtime closure

Implemented in this branch:

- centralized credential placeholder detection;
- rejection of sanitized operator markers before any provider call;
- API and SFTP configuration use the same credential policy;
- CI tests for placeholder and runtime-value behavior.

Still requires operator/runtime evidence:

- protected `ds.atlas-ai.no` status validation;
- authenticated Domeneshop read smoke;
- MCP initialize and tools-list validation using the selected transport;
- SFTP read smoke inside an approved non-sensitive root.

## D-R2 — Controlled-write foundation

Implemented in this branch:

- controlled-write release manifest and target/tool allowlists;
- HMAC-signed, expiring, one-time, payload-bound approval tokens;
- file-backed idempotency ledger;
- append-only redacted audit store with hash-chain verification;
- common controlled-write executor with pre-read, execute, readback, audit, and rollback handling;
- provider DNS mutation adapter with a default TXT-only pilot scope and deletion disabled.

Current boundary:

```text
FOUNDATION_ONLY
NO_WRITE_TOOL_REGISTRATION
NO_LIVE_EXECUTION_MANIFEST
NO_PROVIDER_MUTATION_AUTHORIZED
```

## D-R3 — DNS pilot acceptance

Required before activation:

1. approved test domain ID and isolated TXT host;
2. valid external runtime credentials;
3. release manifest decision `APPROVE_CONTROLLED_WRITE_PILOT`;
4. `WRITE_TOOLS_ENABLED=true` only in the isolated pilot runtime;
5. approval signing secret and protected approval ledger;
6. dry-run report, backup/compensation reference, and operator approval;
7. create/update/readback/rollback/audit evidence;
8. final operator sign-off.

MX, NS, general deletion, and broad target prefixes remain blocked.
