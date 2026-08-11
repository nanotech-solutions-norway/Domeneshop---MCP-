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
- CI tests for placeholder and runtime-value behavior;
- explicit local MCP transport contract: `stdio` through `FastMCP.run(transport="stdio")`;
- MCP SDK compatibility constrained to the supported 1.x line because MCP 2.x removes the imported `mcp.server.fastmcp` module.
- provider and SFTP smoke evidence reduced to pass/fail metadata and aggregate counts, without provider payloads or remote paths.

Transport boundary:

- `domeneshop-mcp-server` and `python -m domeneshop_mcp.server` are stdio MCP processes for an operator-controlled MCP client;
- `https://ds.atlas-ai.no/` is the separate PHP health/configuration status surface, not an MCP transport endpoint;
- no remote Streamable HTTP or SSE MCP endpoint is declared by this release train.

Accepted protected evidence on 10.08.2026:

- authenticated Domeneshop domain-list GET;
- MCP initialize and read-only tools-list validation over stdio;
- SFTP allowed-root and directory-list reads inside the configured root;
- bounded public status-surface GET with HTTP 200, no authentication, and no retained payload;
- payload-free evidence and preserved controlled-write hold.

Runs `31384070264` and `31403862923` provide the accepted D-R1 closure evidence. Additional read surfaces remain capability-specific and do not expand this closure into write authorization.

See `docs/PROTECTED_READONLY_VALIDATION_20260810.md`.

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

Current blocker:

- on 11.08.2026 the operator confirmed that no isolated non-production domain is available;
- attempted GET-only target resolution failed closed without mutation;
- unapproved pilot selector secrets were removed from the protected environment;
- D-R3 remains held until an isolated domain is provisioned or explicitly approved.

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

```text
HOLD_NO_ISOLATED_TARGET
NO_PROVIDER_MUTATION_AUTHORIZED
```
