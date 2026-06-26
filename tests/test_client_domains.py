import httpx

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.tools_read import list_domains


def test_list_domains_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v0/domains"
        return httpx.Response(200, json=[{"id": 1, "domain": "example.com", "status": "active"}])

    transport = httpx.MockTransport(handler)
    config = DomeneshopConfig.from_env({"DS_AUTH_USER": "u", "DS_AUTH_VALUE": "v"})
    client = DomeneshopReadClient(config, transport=transport)
    result = list_domains(client)
    assert result["success"] is True
    assert result["data"][0]["domain"] == "example.com"
