from __future__ import annotations

import httpx

from domeneshop_mcp.config import DomeneshopConfig
import domeneshop_mcp.http_forward_host_get_diagnostic as diag


class FakeReadClient:
    def __init__(self, config):
        pass

    def list_domains(self, domain=None):
        return [{"id": 12345, "domain": diag.DOMAIN_NAME, "services": {"dns": True}}]

    def list_http_forwards(self, domain_id):
        return [{"host": diag.FORWARD_HOST, "frame": False, "url": diag.EXPECTED_URL}]

    def close(self):
        pass


def test_diagnostic_is_get_only(monkeypatch):
    monkeypatch.setattr("domeneshop_mcp.client.DomeneshopReadClient", FakeReadClient)

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.method)
        return httpx.Response(404, request=request)

    original = httpx.Client

    class PatchedClient(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(diag.httpx, "Client", PatchedClient)
    cfg = DomeneshopConfig(
        auth_user="token",
        auth_value="secret",
        write_tools_enabled=False,
        dry_run_default=True,
    )
    evidence = diag.run_host_get_diagnostic(cfg)
    assert evidence["provider_mutation_performed"] is False
    assert evidence["http_forward_update_authorized"] is False
    assert seen and set(seen) == {"GET"}
