from pathlib import Path

from domeneshop_mcp.operations_validation import validate_operations_docs


def test_operations_docs_exist():
    validation = validate_operations_docs(Path("."))
    names = {item["name"]: item["passed"] for item in validation.checks}
    assert names["file_exists:docs/OPERATIONAL_RUNBOOK.md"] is True
    assert names["file_exists:docs/INCIDENT_RESPONSE_PROCEDURES.md"] is True
    assert names["file_exists:docs/RELEASE_APPROVAL_CHECKLIST.md"] is True
    assert names["file_exists:docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md"] is True


def test_operations_docs_have_required_markers():
    validation = validate_operations_docs(Path("."))
    failed = [item for item in validation.checks if not item["passed"]]
    assert failed == []


def test_operations_validation_passes_current_repo():
    validation = validate_operations_docs(Path("."))
    assert validation.passed is True
    assert validation.summary()["failed_count"] == 0
