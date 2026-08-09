# Domeneshop MCP Security Continuity Post-Merge Record — 02:56, 09.08.2026

## Classification

```text
RECORD_STATUS=AUTO_APPROVED
UNIVERSAL_SECURITY_POLICY=MERGED_PR_14
SOURCE_CONTINUITY_POLICY=MERGED_PR_14
LIVE_CHANGE_ACTIVATION=HOLD
SECONDARY_GIT=NOT_IMPLEMENTED
IMMUTABLE_OFFLINE_RECOVERY=NOT_IMPLEMENTED
```

## Governing outcome

Domeneshop MCP inherits the merged NTSN universal Atlas/MCP security baseline and GitHub-compromise/source-control continuity standard while preserving the existing read-first, path-jail, backup-before-write, readback, redaction and live-change hold.

## Permanent rules

- Never expose Domeneshop/API/SFTP/database/MCP credentials, tokens, passwords, private keys or runtime secrets to model context, Git, Drive evidence, logs, screenshots or transfer packs.
- GitHub is the normal engineering/change-control source while trusted but cannot be the only independently recoverable source/governance copy.
- A suspected GitHub compromise freezes GitHub-originated deployments and live/write activation.
- A live mirror alone is not sufficient recovery; verify an independently signed known-good checkpoint and immutable/offline recovery evidence before temporary recovery authority.
- DNS/routing failover can restore availability but cannot establish source integrity or grant mutation authority.
- DNS, HTTP-forward, SFTP/file and future SQL write paths remain independently gated and are never enabled because of a source-control outage/recovery event.

## Domeneshop/private-server boundary

A Domeneshop-hosted server can serve as an additional bare Git/Forgejo/GitLab recovery node only if it has separate administrator credentials where possible, SSH-key/strong authentication, restricted network access, host firewall, patching, monitoring, encrypted storage, no production secrets and an off-provider immutable backup. It should not be the sole independent recovery location when the same account/provider controls production DNS/hosting.

## Recovery backlog

| ID | Requirement | State |
|---|---|---|
| DOM-SC-01 | Select independent secondary Git provider/account boundary | `PENDING_REVIEW` |
| DOM-SC-02 | Signed Git bundle/checkpoint and integrity manifest | `NOT_IMPLEMENTED` |
| DOM-SC-03 | Immutable/WORM off-provider recovery storage | `NOT_IMPLEMENTED` |
| DOM-SC-04 | Encrypted offline recovery copy | `NOT_IMPLEMENTED` |
| DOM-SC-05 | GitHub compromise / ref tamper recovery exercise | `NOT_RUN` |
| DOM-SC-06 | Revalidate path jail, backup/readback and controlled-write gates after recovery | `NOT_RUN` |

## Platform candidates

Azure DevOps Repos remains the preferred managed candidate for independent secondary Git. Isolated Forgejo/GitLab on a separately administered provider is the provider-diverse candidate. Domeneshop-hosted Git is an optional additional node, not an automatic replacement for the independent secondary.

## Validation evidence

- Security adoption PR #14 merged 09.08.2026.
- Repository validation, security baseline, dependency review and CodeQL passed for the security-adoption head before merge.
- No source-continuity infrastructure, Credential Broker or production write path is claimed live by this record.

## Memory / continuation rule

Future Domeneshop MCP sessions must preserve `HOLD_LIVE_CHANGE_ACTIVATION`, the independent-source-recovery requirement, separate Office PC/laptop PC credential configurations and the no-secrets-in-model-context rule. Never ask the operator to paste production credentials into ChatGPT.