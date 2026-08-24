from __future__ import annotations

import pytest

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_preflight import (
    HttpForwardPreflightError,
    PILOT_FORWARD_HOST,
    validate_http_forward_pilot_preflight,
)


class FakeReadClient:
    def __init__(self, *, forwards=None, dns_records=None) -> None:
        self.forwards = [] if forwards is None else forwards
        self.dns_records = [] if dns_records is None else dns_records
        self.calls: list[tuple] = []

    def list_domains(self, domain=None):
        self.calls.append(("list_domains", domain))
        return [
            {
                "id": 12345,
                "domain": "atlas-mcp-sandbox.no",
                "services": {"dns": True},
            }
        ]

    def list_http_forwards(self, domain_id):
        self.calls.append(("list_http_forwards", domain_id))
        return self.forwards

    def list_dns_records(self, domain_id, host=None, record_type=None):
        self.calls.append(("list_dns_records", domain_id, host, record_type))
        return self.dns_records


@pytest.fixture
def safe_config() -> DomeneshopConfig:
    return DomeneshopConfig(
        auth_user="runtime-token-value",
        auth_value="runtime-secret-value",
        write_tools_enabled=False,
        dry_run_default=True,
    )


def test_preflight_accepts_isolated_target_without_mutation(safe_config):
    client = FakeReadClient()
    evidence = validate_http_forward_pilot_preflight(
        safe_config,
        "atlas-mcp-sandbox.no",
        client=client,
    )

    assert evidence["success"] is True
    assert evidence["status"] == "isolated_target_available"
    assert evidence["collision_detected"] is False
    assert evidence["existing_forward_count"] == 0
    assert evidence["blocking_dns_record_count"] == 0
    assert evidence["provider_mutation_performed"] is False
    assert evidence["http_forward_create_authorized"] is False
    assert evidence["http_forward_update_authorized"] is False
    assert evidence["http_forward_delete_authorized"] is False
    assert evidence["write_tools_enabled"] is False
    assert evidence["domain_id_included"] is False
    assert evidence["host_included"] is False
    assert ("list_dns_records", 12345, PILOT_FORWARD_HOST, None) in client.calls


def test_preflight_rejects_existing_forward(safe_config):
    client = FakeReadClient(forwards=[{"host": PILOT_FORWARD_HOST, "frame": False, "url": "https://example.com"}])
    with pytest.raises(HttpForwardPreflightError, match="target_not_isolated"):
        validate_http_forward_pilot_preflight(safe_config, "atlas-mcp-sandbox.no", client=client)


def test_preflight_rejects_blocking_dns_collision(safe_config):
    client = FakeReadClient(dns_records=[{"host": PILOT_FORWARD_HOST, "type": "CNAME", "data": "example.com"}])
    with pytest.raises(HttpForwardPreflightError, match="target_not_isolated"):
        validate_http_forward_pilot_preflight(safe_config, "atlas-mcp-sandbox.no", client=client)


def test_preflight_ignores_nonblocking_txt_record(safe_config):
    client = FakeReadClient(dns_records=[{"host": PILOT_FORWARD_HOST, "type": "TXT", "data": "validation"}])
    evidence = validate_http_forward_pilot_preflight(safe_config, "atlas-mcp-sandbox.no", client=client)
    assert evidence["success"] is True
    assert evidence["blocking_dns_record_count"] == 0


def test_preflight_fails_closed_when_write_tools_enabled(safe_config):
    unsafe = DomeneshopConfig(
        auth_user=safe_config.auth_user,
        auth_value=safe_config.auth_value,
        write_tools_enabled=True,
        dry_run_default=True,
    )
    with pytest.raises(HttpForwardPreflightError, match="unsafe_runtime_configuration"):
        validate_http_forward_pilot_preflight(unsafe, "atlas-mcp-sandbox.no", client=FakeReadClient())
