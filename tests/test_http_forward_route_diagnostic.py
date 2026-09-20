from __future__ import annotations

import importlib.util
from pathlib import Path

import httpx
import pytest

from domeneshop_mcp.http_forward_create_dry_run import DOMAIN_NAME, FORWARD_HOST, candidate_payload


def _load_diag_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "http_forward_route_diagnostic.py"
    spec = importlib.util.spec_from_file_location("http_forward_route_diagnostic", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diag = _load_diag_module()


class FakeConfig:
    api_base_url = "https://api.domeneshop.no/v0"
    auth_user = "token"
    auth_value = "secret"
    timeout_seconds = 20.0

    def require_auth(self):
        return None


def test_read_only_gate_rejects_any_mutation_authorization(monkeypatch):
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    for name in (
        "HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED",
    ):
        monkeypatch.setenv(name, "true")
        with pytest.raises(RuntimeError, match="mutation_authorization_forbidden"):
            diag._require_read_only()
        monkeypatch.setenv(name, "false")


def test_diagnostic_uses_get_only_and_reports_variants(monkeypatch):
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED", "false")
    monkeypatch.setattr(diag.DomeneshopConfig, "from_env", classmethod(lambda cls: FakeConfig()))

    domain_id = 12345
    import hashlib
    target = f"domain:{domain_id}:forward:{FORWARD_HOST}"
    monkeypatch.setattr(diag, "EXPECTED_TARGET_SHA256", hashlib.sha256(target.encode()).hexdigest())

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        assert request.method == "GET"
        if request.url.path.endswith("/domains"):
            return httpx.Response(200, json=[{"id": domain_id, "domain": DOMAIN_NAME}], request=request)
        if request.url.path.endswith(f"/domains/{domain_id}/forwards/"):
            return httpx.Response(200, json=[candidate_payload()], request=request)
        return httpx.Response(404, json={"error": "not_found"}, request=request)

    real_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(diag.httpx, "Client", client_factory)

    result = diag.run()
    assert result["provider_mutation_performed"] is False
    assert result["accepted_create_state_verified_by_list"] is True
    assert len(result["route_results"]) == 4
    assert all(method == "GET" for method, _ in seen)
