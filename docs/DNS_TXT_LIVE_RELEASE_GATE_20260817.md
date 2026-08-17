# D-R3 DNS TXT Live Release Gate — 17.08.2026

## Purpose

Prepare the first bounded Domeneshop DNS TXT CREATE release after accepted protected dry-run evidence. This document is a release gate only. It does not activate live execution, issue an approval token, register a write tool, or perform a provider mutation.

## Accepted preconditions

- isolated non-production target resolved through authenticated Domeneshop API;
- fixed TXT host `_mcp-validation` verified collision-free;
- protected GET-only preflight accepted in run `31966109707`;
- protected controlled-write dry run accepted in run `32016205573`;
- accepted target SHA-256: `5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e`;
- accepted payload SHA-256: `6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c`;
- signing-secret policy validated;
- nonce, idempotency, and audit storage readiness validated;
- all mandatory controls required.

## Exact release scope

Only the first TXT CREATE operation may be considered by the next authorization step.

```text
provider=Domeneshop
record_type=TXT
host=_mcp-validation
action=domeneshop_create_dns_txt
accepted_target_sha256=5f8f8997f3af1c38f8b53dd2fba6ea95dc156aadce62d583a88db37f53a9fc2e
accepted_payload_sha256=6b480c6e249ef995ed40057c6dc33dca169728c5421e46f58ab33b8b3193710c
```

The protected runtime must resolve the target again immediately before approval issuance and must fail closed if the resolved target hash or deterministic payload hash differs from the accepted values above.

## Required controls before any provider call

1. Fresh authenticated pre-read confirms the exact target remains active and collision-free.
2. Runtime recomputes and matches the accepted target and payload hashes.
3. A live release manifest is generated outside Git with exactly one approved tool and exact target prefix.
4. `live_execution_enabled=true` may exist only inside that separately approved runtime manifest.
5. `WRITE_TOOLS_ENABLED` remains `false` until the final operator authorization step.
6. One-time approval token is bound to operator, action, exact target, accepted payload hash, approval ID, and expiry.
7. One idempotency key is reserved only after the approval token is successfully verified and consumed by the executor.
8. Append-only audit and independent readback remain mandatory.
9. The operator must explicitly authorize the provider mutation after reviewing the exact release evidence.

## Explicitly not authorized

```text
NO DNS MUTATION YET
NO TXT UPDATE
NO TXT DELETE
NO MX CHANGE
NO NS CHANGE
NO GENERAL DNS DELETE
NO HTTP FORWARD CHANGE
NO FILE WRITE
NO SQL WRITE
NO GLOBAL WRITE ACTIVATION
```

TXT UPDATE and rollback/delete require separate later approvals and release scopes after the CREATE readback is accepted.

## Operator authorization boundary

The next approval request must present only non-secret evidence sufficient to confirm:

- accepted run IDs and commit;
- target and payload hashes;
- exact tool/action;
- exact fixed host;
- release ID;
- approval expiry;
- idempotency key identifier or hash;
- confirmation that readback, audit, and rollback controls are active;
- confirmation that no broader target prefix or tool is enabled.

Until the operator explicitly approves the first provider mutation, the controlling state remains:

```text
CONTROLLED_WRITE_DRY_RUN_ACCEPTED
LIVE_RELEASE_GATE_PREPARED
WRITE_TOOLS_ENABLED=false
PROVIDER_MUTATION_PERFORMED=false
HOLD_LIVE_CHANGE_ACTIVATION
```
