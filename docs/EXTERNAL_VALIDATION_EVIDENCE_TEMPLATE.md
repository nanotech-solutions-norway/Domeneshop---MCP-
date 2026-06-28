# External Validation Evidence Template — 01:42, 28.06.2026

Use this template outside the repository to collect controlled validation evidence.

Do not paste runtime values, credentials, account identifiers, or private evidence into the repository.

## Validation summary

```text
validation_run_id:
approved_domain_ref:
operation_id:
operator_ref:
validation_started_utc:
validation_completed_utc:
final_status:
```

## Required references

```text
write_scope_ref:
credential_readiness_ref:
recovery_evidence_ref:
preflight_report_ref:
dry_run_report_ref:
operator_approval_ref:
staged_gate_ref:
post_change_verification_ref:
audit_log_ref:
final_operator_signoff_ref:
```

## Final checks

```text
scope_approved: yes/no
credential_references_external: yes/no
recovery_evidence_linked: yes/no
preflight_and_dry_run_linked: yes/no
operator_approval_linked: yes/no
staged_gate_linked: yes/no
post_change_verification_completed: yes/no
audit_log_defined: yes/no
final_operator_signoff_completed: yes/no
no_autonomous_change: yes/no
```

## Decision

```text
external_controlled_validation_status:
ready_for_controlled_use: yes/no
requires_fix_before_use: yes/no
notes:
```
