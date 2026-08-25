from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from domeneshop_mcp.config import DomeneshopConfig
import domeneshop_mcp.http_forward_live_create as live


class FakeReadClient:
    def __init__(self, *, readback: bool = False) -> None:
        self.readback = readback
        self.closed = False

    def list_domains(self, domain=None):
        assert domain == live.DOMAIN_NAME
        return [{"id": 12345, "domain": live.DOMAIN_NAME, "services": {"dns": True}}]

    def list_http_forwards(self, domain_id):
        assert domain_id == 12345
        return []

    def list_dns_records(self, domain_id, host=None, record_type=None):
        assert domain_id == 12345
        assert host == live.FORWARD_HOST
        return []

    def get_http_forward(self, domain_id, host):
        assert self.readback is True
        assert domain_id == 12345
        assert host == live.FORWARD_HOST
        return {"host": live.FORWARD_HOST, "frame": False, "url": live.FORWARD_URL}

    def close(self):
        self.closed = True


def safe_config() -> DomeneshopConfig:
    return DomeneshopConfig(
        auth_user="runtime-token",
        auth_value="runtime-secret",
        write_tools_enabled=False,
        dry_run_default=True,
    )


def authorize(monkeypatch: pytest.MonkeyPatch, target_hash: str) -> None:
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED", "true")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_RELEASE_ID", live.RELEASE_ID)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_TARGET_SHA256", target_hash)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_PAYLOAD_SHA256", live.EXPECTED_PAYLOAD_SHA256)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_DOMAIN_NAME", live.DOMAIN_NAME)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_HOST", live.FORWARD_HOST)


def test_live_create_fails_closed_without_explicit_authorization(monkeypatch):
    monkeypatch.delenv("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED", raising=False)
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    with pytest.raises(live.HttpForwardLiveCreateError, match="create_not_authorized"):
        live.execute_exact_http_forward_create(safe_config())


def test_live_create_rejects_update_delete_or_broader_authorization(monkeypatch):
    target_hash = hashlib.sha256(
        f"domain:12345:forward:{live.FORWARD_HOST}".encode("utf-8")
    ).hexdigest()
    authorize(monkeypatch, target_hash)
    monkeypatch.setattr(live, "EXPECTED_TARGET_SHA256", target_hash)

    for name in (
        "HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED",
    ):
        monkeypatch.setenv(name, "true")
        with pytest.raises(live.HttpForwardLiveCreateError):
            live.execute_exact_http_forward_create(safe_config())
        monkeypatch.setenv(name, "false")


def test_exact_live_create_posts_once_and_independently_reads_back(monkeypatch):
    target_hash = hashlib.sha256(
        f"domain:12345:forward:{live.FORWARD_HOST}".encode("utf-8")
    ).hexdigest()
    monkeypatch.setattr(live, "EXPECTED_TARGET_SHA256", target_hash)
    authorize(monkeypatch, target_hash)

    readers = [FakeReadClient(readback=False), FakeReadClient(readback=True)]

    def reader_factory(config):
        assert config.has_auth
        return readers.pop(0)

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, json.loads(request.content.decode("utf-8"))))
        assert request.method == "POST"
        assert request.url.path == "/domains/12345/forwards/"
        return httpx.Response(204, request=request)

    evidence = live.execute_exact_http_forward_create(
        safe_config(),
        transport=httpx.MockTransport(handler),
        read_client_factory=reader_factory,
    )

    assert len(seen) == 1
    assert seen[0][2] == live.candidate_payload()
    assert evidence["success"] is True
    assert evidence["status"] == "created_and_readback_verified"
    assert evidence["provider_mutation_performed"] is True
    assert evidence["independent_readback_verified"] is True
    assert evidence["automatic_delete_performed"] is False
    assert evidence["automatic_rollback_performed"] is False
    assert evidence["http_forward_update_authorized"] is False
    assert evidence["http_forward_delete_authorized"] is False
    assert evidence["broader_overwrite_authorized"] is False
    assert readers == []


def test_collision_stops_before_post(monkeypatch):
    target_hash = hashlib.sha256(
        f"domain:12345:forward:{live.FORWARD_HOST}".encode("utf-8")
    ).hexdigest()
    monkeypatch.setattr(live, "EXPECTED_TARGET_SHA256", target_hash)
    authorize(monkeypatch, target_hash)

    class CollisionReader(FakeReadClient):
        def list_http_forwards(self, domain_id):
            return [{"host": live.FORWARD_HOST, "frame": False, "url": live.FORWARD_URL}]

    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(204, request=request)

    with pytest.raises(live.HttpForwardLiveCreateError, match="existing_forward_collision") as exc:
        live.execute_exact_http_forward_create(
            safe_config(),
            transport=httpx.MockTransport(handler),
            read_client_factory=lambda config: CollisionReader(),
        )
    assert called is False
    assert exc.value.provider_mutation_attempted is False
