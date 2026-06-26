# Phase 3 SFTP Read Connector Implementation — 11:25, 26.06.2026

## Scope

Phase 3 implements read-only hosted-file inspection through SFTP-compatible access.

Included operations:

```text
sftp_list_allowed_roots
sftp_list_files
sftp_get_file_metadata
sftp_read_text_file
```

## Deliberate exclusions

The following operations are not implemented in Phase 3:

```text
sftp_upload_file
sftp_upload_folder
sftp_delete_file
sftp_restore_backup
ssh_run_command
chmod
chown
recursive delete
```

## Safety model

The read connector uses a path guard with explicit allowed roots:

```text
/www
/www/solarex_forms
/www/atlas_control
/www/atlas_pip2
```

A requested remote path must be absolute and remain inside the configured allowed roots. Parent traversal is rejected.

## Text-read limits

Text reads are limited by:

```text
MAX_READ_FILE_BYTES=262144
ALLOWED_TEXT_EXTENSIONS=.txt,.md,.json,.csv,.html,.htm,.css,.js,.php,.xml,.yml,.yaml,.log
```

Binary files can be listed and have metadata fetched, but are not read as text unless explicitly approved by extension configuration.

## Runtime configuration

```text
DOMENESHOP_SFTP_HOST=sftp.domeneshop.no
DOMENESHOP_SFTP_PORT=22
DS_SFTP_USER=runtime value only
DS_SFTP_VALUE=runtime value only
DOMENESHOP_REMOTE_ROOT=/www
```

Runtime access values must not be committed to the repository.

## Validation

Run:

```bash
python -m pip install -e ".[test]"
pytest -q
python scripts/validate_repository_structure.py
```

Manual smoke check, with runtime values configured outside the repository:

```bash
python scripts/remote_read_smoke.py
```

## Current MCP registration status

The SFTP read handlers are implemented in:

```text
src/domeneshop_mcp/tools_sftp_read.py
```

The server registration update was blocked by the GitHub connector safety layer during this session. Therefore, Phase 3 code and tests are implemented, while direct MCP server registration remains pending a local patch or a connector-approved update.

## Status

```text
PHASE_3_IMPLEMENTED_PENDING_CI_VALIDATION_AND_SERVER_REGISTRATION
```
