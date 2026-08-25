from __future__ import annotations

import hashlib
import json

import httpx
import pytest

from domeneshop_mcp.config import DomeneshopConfig
import domeneshop_mcp.http_forward_live_update as live


class FakeReadClient:
    def __init__(self, *, state: dict | None = None) -> None:
        self.state = state or live.accepted_create_payload()
        self.closed = False

    def list_domains(self, domain=None):
        assert domain == live.DOMAIN_NAME
        return [{"id": 12345, "domain": live.DOMAIN_NAME, "services": {"dns": True}}]

    def list_http_forwards(self, domain_id):
        assert domain_id == 12345
        return [dict(self.state)]

    def close(self):
        self.closed = True


def safe_config() -> DomeneshopConfig:
    return DomeneshopConfig(
        auth_user="runtime-token",
        auth_value="runtime-secret",
        write_tools_enabled=False,
        dry_run_default=True,
    )


def target_hash() -> str:
    return hashlib.sha256(
        f"domain:12345:forward:{live.FORWARD_HOST}".encode("utf-8")
    ).hexdigest()


def authorize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(live, "EXPECTED_TARGET_SHA256", target_hash())
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED", "true")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED", "false")
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_RELEASE_ID", live.RELEASE_ID)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_TARGET_SHA256", target_hash())
    monkeypatch.setenv(
        "HTTP_FORWARD_D_R4B_REQUIRED_BEFORE_PAYLOAD_SHA256",
        live.REQUIRED_BEFORE_PAYLOAD_SHA256,
    )
    monkeypatch.setenv(
        "HTTP_FORWARD_D_R4B_UPDATE_PAYLOAD_SHA256",
        live.EXPECTED_UPDATE_PAYLOAD_SHA256,
    )
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_DOMAIN_NAME", live.DOMAIN_NAME)
    monkeypatch.setenv("HTTP_FORWARD_D_R4B_HOST", live.FORWARD_HOST)


def test_live_update_fails_closed_without_explicit_authorization(monkeypatch):
    monkeypatch.delenv("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED", raising=False)
    monkeypatch.setenv("WRITE_TOOLS_ENABLED", "false")
    monkeypatch.setenv("DRY_RUN_DEFAULT", "true")
    with pytest.raises(live.HttpForwardLiveUpdateError, match="update_not_authorized"):
        live.execute_exact_http_forward_update(safe_config())


def test_live_update_rejects_create_delete_or_broader_authorization(monkeypatch):
    authorize(monkeypatch)
    for name in (
        "HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED",
    ):
        monkeypatch.setenv(name, "true")
        with pytest.raises(live.HttpForwardLiveUpdateError):
            live.execute_exact_http_forward_update(safe_config())
        monkeypatch.setenv(name, "false")


def test_before_state_mismatch_stops_before_put(monkeypatch):
    authorize(monkeypatch)
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, request=request, json=live.candidate_update_payload())

    reader = FakeReadClient(
        state={"host": live.FORWARD_HOST, "frame": False, "url": "https://unexpected.invalid/"}
    )
    with pytest.raises(live.HttpForwardLiveUpdateError, match="required_before_state_mismatch"):
        live.execute_exact_http_forward_update(
            safe_config(),
            transport=httpx.MockTransport(handler),
            read_client_factory=lambda config: reader,
            sleep_fn=lambda seconds: None,
        )
    assert called is False


def test_exact_live_update_puts_once_and_verifies_by_list(monkeypatch):
    authorize(monkeypatch)
    readers = [
        FakeReadClient(state=live.accepted_create_payload()),
        FakeReadClient(state=live.candidate_update_payload()),
    ]

    def reader_factory(config):
        assert config.has_auth
        return readers.pop(0)

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, json.loads(request.content.decode("utf-8"))))
        assert request.method == "PUT"
        assert request.url.path == f"/v0/domains/12345/forwards/{live.FORWARD_HOST}"
        return httpx.Response(200, request=request, json=live.candidate_update_payload())

    evidence = live.execute_exact_http_forward_update(
        safe_config(),
        transport=httpx.MockTransport(handler),
        read_client_factory=reader_factory,
        sleep_fn=lambda seconds: None,
    )

    assert len(seen) == 1
    assert seen[0][2] == live.candidate_update_payload()
    assert evidence["success"] is True
    assert evidence["status"] == "updated_and_readback_verified"
    assert evidence["provider_mutation_performed"] is True
    assert evidence["independent_readback_verified"] is True
    assert evidence["readback_method"] == "list_forwards"
    assert evidence["readback_attempts_used"] == 1
    assert evidence["host_change_performed"] is False
    assert evidence["automatic_delete_performed"] is False
    assert evidence["automatic_rollback_performed"] is False
    assert evidence["http_forward_create_authorized"] is False
    assert evidence["http_forward_update_authorized"] is True
    assert evidence["http_forward_delete_authorized"] is False
    assert evidence["broader_overwrite_authorized"] is False
    assert readers == []


def test_post_write_readback_retries_then_succeeds(monkeypatch):
    authorize(monkeypatch)
    readers = [
        FakeReadClient(state=live.accepted_create_payload()),
        FakeReadClient(state=live.accepted_create_payload()),
        FakeReadClient(state=live.candidate_update_payload()),
    ]
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json=live.candidate_update_payload())

    evidence = live.execute_exact_http_forward_update(
        safe_config(),
        transport=httpx.MockTransport(handler),
        read_client_factory=lambda config: readers.pop(0),
        sleep_fn=lambda seconds: sleeps.append(seconds),
        readback_attempts=2,
        readback_delay_seconds=0.01,
    )

    assert evidence["readback_attempts_used"] == 2
    assert sleeps == [0.01]


def test_put_response_mismatch_fails_without_rollback(monkeypatch):
    authorize(monkeypatch)
    readers = [FakeReadClient(state=live.accepted_create_payload())]

    def handler(request: httpx.Request) -> httpx.Response:
        bad = dict(live.candidate_update_payload())
        bad["url"] = "https://unexpected.invalid/"
        return httpx.Response(200, request=request, json=bad)

    with pytest.raises(live.HttpForwardLiveUpdateError, match="update_response_mismatch") as exc:
        live.execute_exact_http_forward_update(
            safe_config(),
            transport=httpx.MockTransport(handler),
            read_client_factory=lambda config: readers.pop(0),
            sleep_fn=lambda seconds: None,
        )
    assert exc.value.provider_mutation_attempted is True
    assert exc.value.provider_mutation_performed is True
