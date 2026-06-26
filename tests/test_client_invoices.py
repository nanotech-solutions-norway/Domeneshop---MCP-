import httpx

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.tools_read import get_invoice


def test_invoice_url_is_sanitized():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 10,
                "type": "invoice",
                "amount": 100,
                "currency": "NOK",
                "status": "paid",
                "url": "https://example.invalid/invoice?code=value",
            },
        )

    transport = httpx.MockTransport(handler)
    config = DomeneshopConfig(auth_user="u", auth_value="v")
    client = DomeneshopReadClient(config, transport=transport)
    result = get_invoice(client, 10)
    assert result["success"] is True
    assert "url" not in result["data"]
