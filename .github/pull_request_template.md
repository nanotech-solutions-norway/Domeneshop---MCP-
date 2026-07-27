## Domeneshop MCP security-controlled change

### Scope
- [ ] `HOLD_LIVE_CHANGE_ACTIVATION` and `NO_AUTONOMOUS_LIVE_CHANGE` remain controlling unless explicit approval evidence is included.
- [ ] Repository transfer, visibility change and live provider changes are excluded.
- [ ] No API credentials, runtime values, DNS secrets, provider payloads or sensitive data are included.

### Validation
- [ ] Python tests and relevant repository validators passed.
- [ ] New or modified Actions are pinned to full commit SHAs and use minimum permissions.
- [ ] Logs and artifacts were checked for credentials and provider/customer data.
- [ ] Rollback and fail-closed behavior were verified.

### Evidence
- [ ] Implementation log updated.
- [ ] Unverified settings remain `PENDING_REVIEW`.

Describe security impact, evidence, rollback and manual GitHub settings still required.
