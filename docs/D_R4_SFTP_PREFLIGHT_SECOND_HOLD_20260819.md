# D-R4 SFTP preflight second fail-closed hold — 19.08.2026

The Office-PC retry after the Paramiko dependency correction still exited non-zero.

Confirmed retained footer evidence:

```text
D_R4_SFTP_PREFLIGHT_EXIT_CODE=1
WRITE_TOOLS_ENABLED=false
SFTP_CREATE_AUTHORIZED=false
SFTP_OVERWRITE_AUTHORIZED=false
SFTP_DELETE_AUTHORIZED=false
```

No SFTP mutation is authorized or inferred. The operator excerpt did not include the preflight script's sanitized `bounded_error_class` JSON line, so the exact read-only failure class is not yet established.

Next action is a direct GET/read-only diagnostic using the existing `sftp_d_r4_preflight.py` against the same fixed target. No alternative `/www` path may be selected manually.
