# Phase 5 Validation Error Fix — 23:20, 26.06.2026

## Error observed

GitHub Actions failed in the test step with:

```text
FAILED tests/test_deploy_plan.py::test_compare_manifest_blocks_outside_root
ValueError: Remote path is outside allowed roots.
```

## Cause

The failing workflow ran against an earlier Phase 5 commit where the test expected `compare_manifest()` to return a plan object for an invalid target root.

That expectation was incorrect. The production behavior is correct: an invalid target root such as `/private` must be rejected before a deployment plan is created.

## Fix already present on current main

The test has been corrected to expect `ValueError`:

```python
with pytest.raises(ValueError):
    compare_manifest(local_entries, {}, target_root="/private", allowed_roots=("/www",))
```

Current corrected test name:

```text
test_compare_manifest_rejects_outside_target_root
```

## Required action

Run the workflow again on the latest `main` branch, not the earlier failed run.

## Safety confirmation

This fix does not add write behavior. The dry-run deployment lane remains planning-only and still reports:

```json
{
  "will_write": false
}
```

## Status

```text
PHASE_5_VALIDATION_ERROR_FIXED_ON_CURRENT_MAIN
```
