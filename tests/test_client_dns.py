import httpx

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.tools_read import list_dns_records


def test_list_dns_records_filters_type_uppercase():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v0/domains/1/dns"
        assert request.url.params["type"] == "A"
        assert request.url.params["host"] == "www"
        return httpx.Response(200, json=[{"id": 2, "host": "www", "ttl": 3600, "type": "A", "data": "192.0.2.10"}])

    transport = httpx.MockTransport(handler)
    config = DomeneshopConfig(auth_user="u", auth_value="v")
    client = DomeneshopReadClient(config, transport=transport)
    result = list_dns_records(client, 1, host="www", record_type="a")
    assert result["success"] is True
    assert result["data"][0]["type"] == "A"
