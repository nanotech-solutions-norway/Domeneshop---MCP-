from pathlib import Path

from domeneshop_mcp.release_gate import validate_release_gate


def test_final_gate_passes_current_repo():
    result = validate_release_gate(Path("."))
    assert result.passed is True
    assert result.summary()["failed_count"] == 0


def test_final_gate_has_required_checks():
    result = validate_release_gate(Path("."))
    names = {item["name"]: item["passed"] for item in result.checks}
    assert names["control_doc_exists:docs/RELEASE_APPROVAL_CHECKLIST.md"] is True
    assert names["script_exists:scripts/estate_validate.py"] is True


def test_final_gate_fails_empty_folder(tmp_path: Path):
    result = validate_release_gate(tmp_path)
    assert result.passed is False
