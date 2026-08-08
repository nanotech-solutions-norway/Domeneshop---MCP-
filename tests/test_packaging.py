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
    assert "mcp>=1.0.0,<2.0.0" in extras["server"]


def test_server_transport_is_explicitly_stdio():
    server_text = Path("src/domeneshop_mcp/server.py").read_text(encoding="utf-8")
    assert 'MCP_TRANSPORT = "stdio"' in server_text
    assert "mcp.run(transport=MCP_TRANSPORT)" in server_text
