from __future__ import annotations

import pytest

from domeneshop_mcp.config import DomeneshopConfig
import domeneshop_mcp.http_forward_post_write_verify as verify


class FakeReadClient:
    def __init__(self, *, direct=None, forwards=None, direct_error=None):
        self.direct = direct
        self.forwards = [] if forwards is None else forwards
        self.direct_error = direct_error
        self.closed = False

    def list_domains(self, domain=None):
        assert domain == verify.DOMAIN_NAME
        return [{"id": 12345, "domain": verify.DOMAIN_NAME, "services": {"dns": True}}]

    def get_http_forward(self, domain_id, host):
        assert domain_id == 12345
        assert host == verify.FORWARD_HOST
        if self.direct_error:
            from domeneshop_mcp.errors import DomeneshopApiError
            raise DomeneshopApiError(self.direct_error, "sanitized")
        return self.direct

    def list_http_forwards(self, domain_id):
        assert domain_id == 12345
        return self.forwards

    def close(self):
        self.closed = True


def safe_config() -> DomeneshopConfig:
    return DomeneshopConfig(
        auth_user="runtime-token",
        auth_value="runtime-secret",
        write_tools_enabled=False,
        dry_run_default=True,
    )


def exact_forward():
    return {"host": verify.FORWARD_HOST, "frame": False, "url": verify.FORWARD_URL}


def test_direct_get_exact_state_passes_without_mutation():
    client = FakeReadClient(direct=exact_forward())
    evidence = verify.verify_exact_http_forward_post_write_state(
        safe_config(), attempts=1, delay_seconds=0, client_factory=lambda config: client
    )
    assert evidence["success"] is True
    assert evidence["verification_method"] == "get_by_host"
    assert evidence["provider_mutation_performed"] is False
    assert evidence["http_forward_create_authorized"] is False
    assert evidence["http_forward_update_authorized"] is False
    assert evidence["http_forward_delete_authorized"] is False
    assert client.closed is True


def test_list_fallback_accepts_exact_state_when_direct_get_errors():
    client = FakeReadClient(direct_error="not_found", forwards=[exact_forward()])
    evidence = verify.verify_exact_http_forward_post_write_state(
        safe_config(), attempts=1, delay_seconds=0, client_factory=lambda config: client
    )
    assert evidence["success"] is True
    assert evidence["verification_method"] == "list_forwards"
    assert evidence["exact_state_verified"] is True


def test_mismatched_existing_state_fails_closed():
    client = FakeReadClient(
        direct_error="not_found",
        forwards=[{"host": verify.FORWARD_HOST, "frame": False, "url": "https://example.invalid/"}],
    )
    with pytest.raises(verify.HttpForwardPostWriteVerifyError, match="post_write_state_mismatch"):
        verify.verify_exact_http_forward_post_write_state(
            safe_config(), attempts=1, delay_seconds=0, client_factory=lambda config: client
        )


def test_retries_get_only_until_exact_state_visible():
    clients = [
        FakeReadClient(direct_error="not_found", forwards=[]),
        FakeReadClient(direct=exact_forward()),
    ]
    sleeps = []
    evidence = verify.verify_exact_http_forward_post_write_state(
        safe_config(),
        attempts=2,
        delay_seconds=0.01,
        sleep_fn=lambda seconds: sleeps.append(seconds),
        client_factory=lambda config: clients.pop(0),
    )
    assert evidence["success"] is True
    assert evidence["attempts_used"] == 2
    assert sleeps == [0.01]
    assert clients == []


def test_never_verified_returns_sanitized_hold():
    with pytest.raises(verify.HttpForwardPostWriteVerifyError, match="post_write_state_not_verified"):
        verify.verify_exact_http_forward_post_write_state(
            safe_config(),
            attempts=2,
            delay_seconds=0,
            sleep_fn=lambda seconds: None,
            client_factory=lambda config: FakeReadClient(direct_error="not_found", forwards=[]),
        )


def test_unsafe_runtime_configuration_is_rejected():
    unsafe = DomeneshopConfig(
        auth_user="runtime-token",
        auth_value="runtime-secret",
        write_tools_enabled=True,
        dry_run_default=True,
    )
    with pytest.raises(verify.HttpForwardPostWriteVerifyError, match="unsafe_runtime_configuration"):
        verify.verify_exact_http_forward_post_write_state(unsafe, attempts=1, delay_seconds=0)
