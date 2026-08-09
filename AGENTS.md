# Domeneshop MCP agent instructions

## Governing records

- Treat `README.md`, `SECURITY.md`, `docs/SECURITY_AND_WRITE_CONTROL.md`, `docs/GITHUB_COMPROMISE_CONTINUITY.md`, `docs/` and the NTSN universal Atlas/MCP security standards as the repository guidance and evidence base.
- Preserve `HOLD_LIVE_CHANGE_ACTIVATION` unless an approved change explicitly supersedes it.
- Never commit or expose provider credentials, access/refresh tokens, passwords, private keys, customer data, private runtime values or production secrets.
- Never ask the operator to paste a production credential into ChatGPT/model context. Use the approved secret-manager/credential-broker or secure out-of-band entry path.

## Source-control continuity

- GitHub is normal primary engineering/change-control while trusted; it must not be the only independently recoverable source/governance copy.
- A suspected GitHub account/repository/App/Actions/platform compromise freezes GitHub-originated deployment and live/write activation.
- A destructive live mirror is replication, not sufficient backup or automatic source authority.
- Recovery requires an independently verified known-good signed checkpoint, immutable/offline recovery evidence, credential rotation as applicable, independent validation and explicit break-glass approval.
- DNS/routing failover restores availability only and never grants source/deployment/write authority.
- A Domeneshop/private server may be an additional hardened recovery node but should not be the sole independent copy when it shares production DNS/hosting account/provider blast radius.
- Azure DevOps Repos and isolated Forgejo/GitLab remain implementation candidates until explicitly selected and validated.

## Device configuration boundary

- Office PC and laptop PC use separate machine configurations/identities.
- Do not synchronize `.env`, credential files, private keys or secret-manager bootstrap material between machines through Drive or Git.
- Compromise/revocation of one device must be possible without exposing credentials from the other.

## Process progress reporting

- Follow `docs/PROCESS_PROGRESS_REPORTING_STANDARD.md` for every operator-facing process.
- Maintain evidence-weighted progress in canonical records, but do not automatically display a status bar after ordinary processes or responses.
- Display the status bar and short completed/ongoing/remaining summary only when the user's complete trimmed message is exactly `Status`, case-insensitively, with no other text, punctuation, mention or context.
- Messages such as `Status please`, `Project status`, `What's the status?`, or `Status @GitHub` do not trigger the special status block.
- Calculate progress from verified weighted milestones only.
- Failed or blocked processes do not increase the percentage.
- Recalculate explicitly when scope changes.
- Carry the current percentage into status records, transfer packs and continuation prompts.
- A progress percentage never authorizes deployment, provider calls, live changes or write enablement.

## Execution boundary

Do not activate live changes, alter production DNS or hosting state, enable write paths, or perform provider mutations without the applicable evidence and explicit operator authorization. Repository merge, source-control outage, mirror availability or recovery mode never relaxes this rule.

## State reporting

Report `DESIGNED`, `CONFIGURED`, `IMPLEMENTED`, `TESTED`, `VALIDATED`, `APPROVED`, `RELEASE_APPROVED` and `LIVE` separately. Security-policy adoption does not mean a secondary Git service, immutable backup, Credential Broker or production write path is live.