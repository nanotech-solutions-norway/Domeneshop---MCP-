# Security Policy — 23:59, 27.07.2026

## Supported posture

This repository is the Domeneshop MCP bridge system of record. `HOLD_LIVE_CHANGE_ACTIVATION`, `NO_AUTONOMOUS_LIVE_CHANGE` and runtime-values-outside-repository controls must remain fail-closed unless separately approved and evidenced.

## Prohibited content

Do not commit Domeneshop API credentials, DNS/deployment secrets, passwords, private keys, runtime environment values, customer-confidential material, unredacted provider payloads or sensitive personal data.

## Reporting and response

Do not place credentials or confidential evidence in a public issue. Report privately to the repository owner. If exposure is suspected: stop affected workflows, revoke and rotate outside GitHub, preserve evidence, remove unsafe artifacts, inspect history/logs, assess contractual/privacy duties and re-enable only after validation.

Changes to live-change gates, provider routes, deployment workflows, authentication or evidence-generation controls require controlled pull-request review. Repository transfer remains on hold.
