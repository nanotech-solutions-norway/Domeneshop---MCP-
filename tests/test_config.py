from domeneshop_mcp.config import DomeneshopConfig


def test_config_defaults_are_safe():
    config = DomeneshopConfig.from_env({})
    assert config.write_tools_enabled is False
    assert config.dry_run_default is True
    assert config.require_operator_approval is True
    assert config.has_auth is False


def test_placeholder_auth_is_not_valid():
    config = DomeneshopConfig.from_env(
        {
            "DS_AUTH_USER": "__SET_IN_SECRET_STORE__",
            "DS_AUTH_VALUE": "__SET_IN_SECRET_STORE__",
        }
    )
    assert config.has_auth is False


def test_config_accepts_runtime_auth_values():
    config = DomeneshopConfig.from_env(
        {
            "DS_AUTH_USER": "runtime-user",
            "DS_AUTH_VALUE": "runtime-value",
        }
    )
    assert config.has_auth is True
