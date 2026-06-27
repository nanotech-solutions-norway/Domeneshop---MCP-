from pathlib import Path

from domeneshop_mcp.release_manifest import validate_release_manifest


def test_release_manifest_passes_current_example():
    result = validate_release_manifest(Path("config/read-only-release-manifest.example.json"))
    assert result.passed is True
    assert result.summary()["failed_count"] == 0


def test_release_manifest_fails_missing_file(tmp_path: Path):
    result = validate_release_manifest(tmp_path / "missing.json")
    assert result.passed is False
    assert result.summary()["failed_count"] == 1


def test_release_manifest_contains_expected_checks():
    result = validate_release_manifest(Path("config/read-only-release-manifest.example.json"))
    names = {item["name"]: item["passed"] for item in result.checks}
    assert names["release_type_read_only"] is True
    assert names["decision_read_only"] is True
    assert names["all_expected_reports_present"] is True
