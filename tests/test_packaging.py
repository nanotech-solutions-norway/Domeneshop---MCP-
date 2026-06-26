import tomllib
from pathlib import Path


def test_console_entrypoint_is_declared():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert scripts["domeneshop-mcp-server"] == "domeneshop_mcp.server:main"


def test_server_extra_is_declared():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    extras = pyproject["project"]["optional-dependencies"]
    assert "server" in extras
    assert any(item.startswith("mcp") for item in extras["server"])
