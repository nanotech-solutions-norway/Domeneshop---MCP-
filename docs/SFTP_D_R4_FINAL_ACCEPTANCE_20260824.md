# D-R4 SFTP Final Acceptance — 2026-08-24

## Decision

`SFTP_WRITE_ACCEPTED`

D-R4 controlled SFTP validation completed against the isolated `atlas-mcp-sandbox.no` webhotel using the exact validation target:

`/www/.mcp-d-r4-validation.txt`

Target SHA-256:

`0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a`

## Accepted sequence

### CREATE

Initial CREATE release:

`D-R4-SFTP-CREATE-20260824-001`

Accepted CREATE-state payload:

`mcp-validation=D-R4-SFTP-CREATE-20260824\n`

Accepted CREATE-state SHA-256:

`9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a`

The first live CREATE attempt exposed a bounded Paramiko mode defect: exclusive mode `x` created the target but did not include a write flag, leaving a zero-byte artifact. The provider artifact was independently verified as SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` and size 0. No delete or broader overwrite was performed.

A separately operator-authorized bounded repair/update (`D-R4-SFTP-REPAIR-UPDATE-20260824-001`) changed only the exact zero-byte target to the accepted CREATE-state payload. Independent readback verified the accepted CREATE-state SHA-256.

### UPDATE

Release:

`D-R4-SFTP-UPDATE-20260824-001`

Required before SHA-256:

`9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a`

Accepted UPDATE-state SHA-256:

`482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203`

Result:

- `status=updated_and_readback_verified`
- `success=true`
- `provider_mutation_performed=true`
- `independent_readback_verified=true`
- `WRITE_TOOLS_ENABLED=false`
- delete, rename, and broader overwrite remained unauthorized.

### RESTORE

Release:

`D-R4-SFTP-RESTORE-20260824-001`

Required before SHA-256:

`482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203`

Restored SHA-256:

`9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a`

Result:

- `status=restored_and_readback_verified`
- `success=true`
- `provider_mutation_performed=true`
- `independent_readback_verified=true`
- `restore_returns_to_accepted_create_state=true`
- `automatic_delete_performed=false`
- `WRITE_TOOLS_ENABLED=false`
- delete, rename, and broader overwrite remained unauthorized.

## Final provider state

`FINAL_RECORD_STATE=ACCEPTED_CREATE_STATE`

The validation file remains present at `/www/.mcp-d-r4-validation.txt` with SHA-256:

`9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a`

## Scope exclusions retained

This acceptance does **not** authorize any of the following:

- SFTP delete
- SFTP rename
- arbitrary or broader file overwrite
- production file deployment
- DNS changes
- HTTP forwarding changes
- SQL writes
- global write activation

`WRITE_TOOLS_ENABLED=false` remains the default and accepted global state.

## Final acceptance

`D_R4_COMPLETE=true`

`SFTP_WRITE_ACCEPTED=true`

`SFTP_CREATE_ACCEPTED=true`

`SFTP_UPDATE_ACCEPTED=true`

`SFTP_RESTORE_ACCEPTED=true`

`SFTP_DELETE_AUTHORIZED=false`

`SFTP_RENAME_AUTHORIZED=false`

`BROADER_OVERWRITE_AUTHORIZED=false`

`WRITE_TOOLS_ENABLED=false`
