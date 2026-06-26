import httpx

from domeneshop_mcp.health import HealthDiagnostics
from domeneshop_mcp.tools_health import http_check_endpoint, http_check_json_health, http_check_tls


def test_endpoint_healthy_and_query_removed():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith("https://example.invalid/health")
        return httpx.Response(200, json={"ok": True})

    client = HealthDiagnostics(transport=httpx.MockTransport(handler))
    result = http_check_endpoint(client, "https://example.invalid/health?x=1")
    assert result["success"] is True
    assert result["data"]["status"] == "healthy"
    assert result["data"]["url"] == "https://example.invalid/health"


def test_endpoint_protected_status_is_successful_diagnostic():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = HealthDiagnostics(transport=httpx.MockTransport(handler))
    result = http_check_endpoint(client, "https://example.invalid/private")
    assert result["success"] is True
    assert result["data"]["status"] == "protected"


def test_json_health_summarizes_keys():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "database": "connected"})

    client = HealthDiagnostics(transport=httpx.MockTransport(handler))
    result = http_check_json_health(client, "https://example.invalid/health")
    assert result["success"] is True
    assert result["data"]["json_summary"]["database"] == "connected"


def test_tls_check_requires_https():
    client = HealthDiagnostics(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    result = http_check_tls(client, "http://example.invalid")
    assert result["success"] is True
    assert result["data"]["success"] is False
    assert result["data"]["status"] == "not_https"


def test_invalid_url_is_controlled_error():
    client = HealthDiagnostics()
    result = http_check_endpoint(client, "not-a-url")
    assert result["success"] is False
    assert result["error_class"] == "validation_failed"
