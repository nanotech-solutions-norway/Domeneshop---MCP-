from domeneshop_mcp.readiness import evaluate_readiness


def key(*parts):
    return "".join(parts)


def good_settings():
    return {
        "DOMENESHOP_API_BASE_URL": "https://api.domeneshop.no/v0",
        key("DS_", "AUTH_", "USER"): "u",
        key("DS_", "AUTH_", "VALUE"): "v",
        "DOMENESHOP_SFTP_HOST": "sftp.domeneshop.no",
        "DOMENESHOP_SFTP_PORT": "22",
        key("DS_", "SFTP_", "USER"): "u",
        key("DS_", "SFTP_", "VALUE"): "v",
        "DOMENESHOP_REMOTE_ROOT": "/www",
        "ALLOWED_REMOTE_ROOTS": "/www,/www/solarex_forms",
        "MAX_READ_FILE_BYTES": "262144",
        "WRITE_TOOLS_ENABLED": "false",
        "DRY_RUN_DEFAULT": "true",
        "REQUIRE_OPERATOR_APPROVAL": "true",
    }


def test_readiness_fails_without_runtime_values():
    decision = evaluate_readiness({})
    summary = decision.summary()
    assert summary["ready_for_read_only_runtime"] is False
    assert summary["ready_for_live_change_runtime"] is False


def test_readiness_passes_for_read_only_runtime_values():
    decision = evaluate_readiness(good_settings())
    summary = decision.summary()
    assert summary["ready_for_read_only_runtime"] is True
    assert summary["ready_for_live_change_runtime"] is False


def test_readiness_detects_change_mode_not_ready():
    settings = good_settings()
    settings["WRITE_TOOLS_ENABLED"] = "true"
    settings["DRY_RUN_DEFAULT"] = "false"
    decision = evaluate_readiness(settings)
    names = {item["name"]: item["passed"] for item in decision.checks}
    assert names["change_tools_disabled"] is False
    assert names["dry_run_default_enabled"] is False
    assert decision.summary()["ready_for_live_change_runtime"] is False
