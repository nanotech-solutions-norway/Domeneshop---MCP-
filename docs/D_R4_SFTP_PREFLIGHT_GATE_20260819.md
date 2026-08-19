# D-R4 SFTP preflight gate — 19.08.2026

## Objective

Prepare the first isolated SFTP controlled-write pilot after D-R3 DNS acceptance.

## Exact proposed CREATE

```text
Host: sftp.domeneshop.no
Remote root: /www/atlas-mcp-sandbox.no
Pilot file: .mcp-d-r4-validation.txt
Target: /www/atlas-mcp-sandbox.no/.mcp-d-r4-validation.txt
Payload: mcp-validation=D-R4-SFTP-CREATE-20260819 + LF
Release preview: D-R4-SFTP-CREATE-PREFLIGHT-20260819
```

Hashes:

```text
target_sha256=930975e51425f91b5896dd80c5205902a6bd958988726ce40ea8910ee3dc371a
payload_sha256=ca313ff4049457d2565a4e3f3c4accfd657491bba654dcdb6a48bb2a90867b4c
```

## Preflight requirements

The GET/read-only Office-PC preflight must prove:

- authenticated SFTP connection succeeds;
- `/www/atlas-mcp-sandbox.no` exists;
- the candidate is a directory;
- the exact pilot file does not already exist;
- deterministic target/payload hashes match;
- no remote listing, remote path, file content, or credential is emitted;
- `WRITE_TOOLS_ENABLED=false` and `DRY_RUN_DEFAULT=true` throughout;
- no approval token, idempotency reservation, audit mutation event, or SFTP mutation occurs.

If the candidate root does not exist, hold D-R4 for target-resolution review. Do not fall back to another `/www` directory.

## Authorization boundary

This gate does not authorize SFTP CREATE, overwrite, rename, chmod, mkdir, delete, deployment, DNS, forwarding, SQL, or broader writes.

A later successful preflight/dry run must be followed by explicit operator authorization for one exact CREATE before a write-capable adapter is packaged.
