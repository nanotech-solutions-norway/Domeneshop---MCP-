from pathlib import Path

from domeneshop_mcp.estate_validation import validate_estate_registry


def test_estate_registry_validates_current_example():
    validation = validate_estate_registry(Path("config/estate-targets.example.json"))
    assert validation.passed is True
    assert validation.summary()["service_count"] >= 4
    assert validation.summary()["failed_count"] == 0


def test_estate_registry_checks_https_and_allowed_roots():
    validation = validate_estate_registry(Path("config/estate-targets.example.json"))
    names = {item["name"]: item["passed"] for item in validation.checks}
    assert names["registry_mode_read_plan_only"] is True
    assert names["allowed_roots_present"] is True
    assert names["services_present"] is True


def test_estate_registry_missing_file_fails(tmp_path: Path):
    validation = validate_estate_registry(tmp_path / "missing.json")
    assert validation.passed is False
    assert validation.summary()["failed_count"] == 1
