# D-R3 DNS TXT Pilot — Final Acceptance

Date: 19.08.2026
Decision: `DNS_WRITE_ACCEPTED`
Environment: isolated non-production
Domain: `atlas-mcp-sandbox.no`
Host: `_mcp-validation`
Record type: TXT

## Result

The D-R3 controlled-write pilot completed successfully across the full bounded lifecycle:

1. authenticated GET-only pre-read and collision check;
2. deterministic controlled-write dry run;
3. explicitly authorized one-shot TXT CREATE;
4. independent CREATE readback and audit validation;
5. separately authorized one-shot TXT UPDATE;
6. independent UPDATE readback and audit validation;
7. separately authorized one-shot TXT RESTORE implemented as UPDATE back to the original accepted CREATE payload;
8. independent RESTORE readback and audit validation;
9. write capability reset to false after each live attempt.

No TXT DELETE was performed. No MX, NS, general DNS, HTTP forwarding, file, SQL, or global-write changes were authorized or performed.

## Fixed hashes

Target SHA-256:
`5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e`

Original CREATE / final RESTORE payload SHA-256:
`6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c`

UPDATE payload SHA-256:
`58e12db0a79ff0dbfe25015592fad85325eaba3a2a46ea56c01c11e26db8b087`

## Live release identities

- CREATE: `D-R3-TXT-CREATE-20260819-001`
- UPDATE: `D-R3-TXT-UPDATE-20260819-001`
- RESTORE: `D-R3-TXT-RESTORE-20260819-001`

## Accepted sanitized execution evidence

### CREATE

- `success=true`
- `status=created_and_readback_verified`
- `provider_create_returned=true`
- `independent_readback_verified=true`
- `audit_chain_valid=true`
- `LIVE_CREATE_EXIT_CODE=0`
- `WRITE_TOOLS_ENABLED=false`

### UPDATE

- `success=true`
- `status=updated_and_readback_verified`
- `provider_update_returned=true`
- `independent_readback_verified=true`
- `audit_chain_valid=true`
- `LIVE_UPDATE_EXIT_CODE=0`
- `WRITE_TOOLS_ENABLED=false`

### RESTORE

- `success=true`
- `status=restored_and_readback_verified`
- `provider_restore_returned=true`
- `independent_readback_verified=true`
- `audit_chain_valid=true`
- `restore_returns_to_original_create_state=true`
- `LIVE_RESTORE_EXIT_CODE=0`
- `WRITE_TOOLS_ENABLED=false`
- `TXT_DELETE_AUTHORIZED=false`

## Control conclusions

D-R3 demonstrates that the controlled-write framework can execute a narrowly scoped provider DNS mutation with:

- explicit per-mutation operator authorization;
- deterministic target/payload hashing;
- one-use approval tokens;
- persistent idempotency state;
- append-only chained audit evidence;
- exact pre-read verification;
- independent provider readback;
- fail-closed behavior;
- process-local write activation only;
- automatic return to `WRITE_TOOLS_ENABLED=false` after each attempt.

The isolated pilot TXT record is left in the original accepted CREATE state.

## Final decision

`DNS_WRITE_ACCEPTED`

D-R3 is complete. Any broader DNS write surface, TXT DELETE capability, HTTP forwarding, SFTP write, SQL write, or production-domain rollout remains outside this acceptance and requires its own release gate and authorization.