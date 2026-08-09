# Domeneshop MCP — GitHub Compromise and Source-Control Continuity — 02:41, 09.08.2026

Domeneshop MCP inherits the NTSN `GITHUB_COMPROMISE_CONTINUITY_STANDARD` maintained in `nanotech-solutions-norway/ntsn-mcp-integrations`.

## Domeneshop-specific fail-closed rule

A suspected GitHub account/repository/Actions compromise suspends trust in GitHub-originated deployment and write-capable automation. DNS, HTTP forward, SFTP/file and future SQL mutation capabilities remain paused unless their independent write-control release gates are satisfied after recovery verification.

## Recommended recovery architecture

- GitHub remains normal primary engineering/change-control while trusted.
- Preferred managed secondary: Azure DevOps Repos using independent Microsoft Entra identities/roles and branch policies.
- Optional provider-diverse secondary: isolated Forgejo/GitLab on a separately administered server/provider.
- Maintain signed full Git bundles and release/security manifests in immutable/WORM-capable storage plus an encrypted offline copy.
- Do not rely on a destructive real-time mirror as the only recovery mechanism.

## Using Domeneshop infrastructure as the backup Git host

Technically possible, but it creates common-mode risk when the same Domeneshop account or infrastructure also controls production DNS/hosting. Therefore:

- a Domeneshop server may be an additional or tertiary recovery location;
- it should use a separate hosting/admin account where possible;
- it should be reachable only through VPN/private access or strict IP allowlisting when feasible;
- use SSH keys, host firewall, encrypted storage, patching/monitoring and off-host immutable backup;
- do not store production DNS/API/SFTP/database credentials in the Git server;
- do not make this server the only independent recovery copy.

For higher security, place the secondary Git service on a different provider/account from production DNS/hosting and retain an immutable/offline copy in another trust domain.

## GitHub compromise incident sequence

1. Freeze GitHub-originated deployments and write activation.
2. Activate global/action kill switches.
3. Revoke/rotate affected GitHub Apps, tokens, deploy keys and workload trust.
4. Identify last known-good independently signed checkpoint.
5. Verify secondary Git history or immutable bundle against signed manifest.
6. Restore into an isolated clean repository/control plane.
7. Run Domeneshop repository security, dependency, CodeQL and project validation suites.
8. Revalidate path jail, backup/readback, approval and write-control gates before any mutation capability returns.
9. Record recovery evidence and explicit return-to-service approval.

DNS/routing failover may restore service availability, but it is not source-control security and must never automatically grant deployment authority to an unverified mirror.

This document defines architecture and incident behavior; it does not claim the secondary Git service or immutable/offline backup is already live.