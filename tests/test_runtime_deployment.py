from pathlib import Path

from domeneshop_mcp.runtime_validation import validate_runtime_deployment


def test_runtime_deployment_scaffold_files_exist():
    validation = validate_runtime_deployment(Path("."))
    names = {item["name"]: item["passed"] for item in validation.checks}
    assert names["file_exists:deploy/container/Dockerfile.example"] is True
    assert names["file_exists:deploy/compose/compose.readonly.example.yml"] is True
    assert names["file_exists:deploy/systemd/domeneshop-mcp.service.example"] is True
    assert names["file_exists:docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md"] is True
    assert names["file_exists:config/mcp-client.example.json"] is True


def test_runtime_deployment_guard_markers_exist():
    validation = validate_runtime_deployment(Path("."))
    failed = [item for item in validation.checks if not item["passed"]]
    assert failed == []


def test_runtime_deployment_validation_passes_current_repo():
    validation = validate_runtime_deployment(Path("."))
    assert validation.passed is True
    assert validation.summary()["failed_count"] == 0
