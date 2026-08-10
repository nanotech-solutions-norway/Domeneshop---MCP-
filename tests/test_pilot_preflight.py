import json

import pytest

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.pilot_preflight import PilotPreflightError, validate_dns_txt_pilot_preflight


class FakeReadClient:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def list_dns_records(self, domain_id, host=None, record_type=None):
        self.calls.append((domain_id, host, record_type))
        return self.records


def _safe_config():
    return DomeneshopConfig(
        auth_user="runtime-token",
        auth_value="runtime-secret",
        write_tools_enabled=False,
        dry_run_default=True,
    )


def test_preflight_is_get_only_target_bound_and_payload_free():
    client = FakeReadClient([])
    evidence = validate_dns_txt_pilot_preflight(_safe_config(), "123", client=client)
    serialized = json.dumps(evidence)

    assert client.calls == [(123, "_mcp-validation", "TXT")]
    assert evidence["success"] is True
    assert evidence["allowed_by_manifest"] is True
    assert evidence["live_execution_enabled"] is False
    assert evidence["write_tools_enabled"] is False
    assert evidence["provider_mutation_performed"] is False
    assert evidence["domain_id_included"] is False
    assert evidence["host_included"] is False
    assert evidence["payload_included"] is False
    assert "_mcp-validation" not in serialized
    assert "mcp-validation=" not in serialized


def test_preflight_rejects_existing_txt_collision():
    with pytest.raises(PilotPreflightError, match="target_not_isolated"):
        validate_dns_txt_pilot_preflight(_safe_config(), "123", client=FakeReadClient([{"id": 7}]))


@pytest.mark.parametrize("value", ["", "not-an-id", "0", "-1"])
def test_preflight_rejects_invalid_domain_id(value):
    with pytest.raises(PilotPreflightError, match="invalid_target"):
        validate_dns_txt_pilot_preflight(_safe_config(), value, client=FakeReadClient([]))


def test_preflight_rejects_non_isolated_host_before_provider_read():
    client = FakeReadClient([])
    with pytest.raises(PilotPreflightError, match="invalid_target"):
        validate_dns_txt_pilot_preflight(_safe_config(), "123", host="www", client=client)
    assert client.calls == []


@pytest.mark.parametrize(
    "config",
    [
        DomeneshopConfig(auth_user="token", auth_value="secret", write_tools_enabled=True, dry_run_default=True),
        DomeneshopConfig(auth_user="token", auth_value="secret", write_tools_enabled=False, dry_run_default=False),
    ],
)
def test_preflight_rejects_unsafe_runtime_configuration(config):
    with pytest.raises(PilotPreflightError, match="unsafe_runtime_configuration"):
        validate_dns_txt_pilot_preflight(config, "123", client=FakeReadClient([]))


def test_preflight_rejects_missing_credentials():
    with pytest.raises(PilotPreflightError, match="credential_missing"):
        validate_dns_txt_pilot_preflight(DomeneshopConfig(), "123", client=FakeReadClient([]))


def test_preflight_rejects_unexpected_provider_shape():
    with pytest.raises(PilotPreflightError, match="unexpected_shape"):
        validate_dns_txt_pilot_preflight(_safe_config(), "123", client=FakeReadClient({"records": []}))


def test_preflight_target_hash_is_bound_without_disclosing_target():
    first = validate_dns_txt_pilot_preflight(_safe_config(), "123", client=FakeReadClient([]))
    second = validate_dns_txt_pilot_preflight(_safe_config(), "124", client=FakeReadClient([]))
    assert first["target_sha256"] != second["target_sha256"]
    assert len(first["target_sha256"]) == 64
