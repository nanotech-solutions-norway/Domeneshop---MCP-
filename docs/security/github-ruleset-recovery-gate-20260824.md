# GitHub Default-Branch Ruleset Recovery Gate — 2026-08-24

Status: `PROPOSED_NOT_APPLIED`

## Context

Issue #9 remains the only open canonical repository issue after D-R4 completion. Read-only settings validation on 2026-08-11 found no repository ruleset enforced. The existing importable `.github/rulesets/main-security.json` has no bypass actors while requiring one approving review, code-owner review, and last-push approval. For a single-operator repository, applying that configuration can create an unrecoverable merge lockout.

## Recommended recoverable design

Candidate file:

`.github/rulesets/main-security-recoverable-proposed.json`

The candidate retains the existing default-branch protections and adds exactly one recovery mechanism:

- actor type: `OrganizationAdmin`
- bypass mode: `pull_request`
- no direct-push/always bypass is proposed.

This means an organization owner/admin must still create a pull request, preserving the pull-request and audit trail, but may explicitly bypass otherwise impossible review requirements when no second reviewer is available.

## Protections retained

- default branch only
- branch deletion restriction
- non-fast-forward/force-push restriction
- linear history
- pull request required
- squash merge only
- stale-review dismissal
- code-owner review requirement
- approval of the most recent push by another actor
- one approving review
- review-thread resolution
- strict required `security-baseline` status check

## Operator gate

Do **not** import or activate this ruleset without explicit operator approval.

When approved, preferred UI path:

1. Repository `Settings` -> `Rules` -> `Rulesets`.
2. Import or create the recoverable ruleset targeting the default branch.
3. Confirm the bypass list contains only organization owners/admins and is set to **For pull requests only**.
4. Confirm there is no `Always allow` bypass.
5. Confirm deletion and force-push protections remain enabled.
6. Confirm pull requests, review-thread resolution, and `security-baseline` required status check remain enabled.
7. Save/activate.
8. Independently read back the active ruleset and capture evidence in Issue #9 before closing the gate.

## Remaining Issue #9 evidence after ruleset activation

The following are separate evidence items and are not proven by this artifact:

- account passkey/2FA and recovery review;
- repository visibility/full-history secret review;
- runtime credential/App/OAuth/key inventory;
- independent reviewer evidence where genuinely available.

Already recorded in Issue #9 from 2026-08-11:

- Actions default token permissions are read;
- workflows cannot approve pull-request reviews;
- `domeneshop-readonly-validation` has two protection rules;
- secret scanning and push protection were enabled and independently read back.

## Holds retained

`HOLD_LIVE_CHANGE_ACTIVATION`

`NO_AUTONOMOUS_LIVE_CHANGE`

`WRITE_TOOLS_ENABLED=false`

This proposal does not authorize repository ruleset activation, provider mutation, DNS change, SFTP change, HTTP forwarding change, SQL write, repository transfer, or any broader live-write scope.
