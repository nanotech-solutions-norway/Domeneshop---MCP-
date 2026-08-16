import json
from pathlib import Path

import pytest

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.errors import DomeneshopApiError
from domeneshop_mcp.pilot_preflight import (
    PilotPreflightError,
    validate_dns_txt_pilot_controlled_write_dry_run,
    validate_dns_txt_pilot_preflight,
    validate_dns_txt_pilot_preflight_by_domain_name,
)


class FakeReadClient:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def list_dns_records(self, domain_id, host=None, record_type=None):
        self.calls.append((domain_id, host, record_type))
        return self.records


class FailingReadClient:
    def __init__(self, error):
        self.error = error

    def list_dns_records(self, domain_id, host=None, record_type=None):
        raise self.error


class DomainResolvingReadClient(FakeReadClient):
    def __init__(self, domains, records=None):
        super().__init__([] if records is None else records)
        self.domains = domains
        self.domain_calls = []

    def list_domains(self, domain=None):
        self.domain_calls.append(domain)
        if isinstance(self.domains, Exception):
            raise self.domains
        return self.domains


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
    assert evidence["domain_name_included"] is False
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


@pytest.mark.parametrize("error_class", ["unauthorized", "not_found", "validation_failed", "provider_error"])
def test_preflight_preserves_only_sanitized_provider_error_class(error_class):
    provider_error = DomeneshopApiError(error_class, "provider detail must not be surfaced", status_code=404)
    with pytest.raises(PilotPreflightError) as exc:
        validate_dns_txt_pilot_preflight(_safe_config(), "123", client=FailingReadClient(provider_error))
    assert exc.value.error_class == error_class
    assert str(exc.value) == error_class


def test_preflight_collapses_non_provider_exceptions():
    with pytest.raises(PilotPreflightError, match="provider_read_failed"):
        validate_dns_txt_pilot_preflight(_safe_config(), "123", client=FailingReadClient(RuntimeError("private")))


def test_domain_name_resolver_selects_exact_dns_enabled_match_without_disclosure():
    client = DomainResolvingReadClient(
        [
            {"id": 122, "domain": "other-example.no", "services": {"dns": True}},
            {"id": 123, "domain": "pilot-example.no", "services": {"dns": True}},
        ]
    )
    evidence = validate_dns_txt_pilot_preflight_by_domain_name(
        _safe_config(),
        "Pilot-Example.no.",
        client=client,
    )
    serialized = json.dumps(evidence)

    assert client.domain_calls == ["pilot-example.no"]
    assert client.calls == [(123, "_mcp-validation", "TXT")]
    assert evidence["success"] is True
    assert evidence["domain_name_included"] is False
    assert "pilot-example.no" not in serialized
    assert "123" not in {str(value) for key, value in evidence.items() if not key.endswith("sha256")}


def test_domain_name_resolver_rejects_no_exact_match():
    client = DomainResolvingReadClient(
        [{"id": 123, "domain": "not-pilot-example.no", "services": {"dns": True}}]
    )
    with pytest.raises(PilotPreflightError, match="target_not_found"):
        validate_dns_txt_pilot_preflight_by_domain_name(_safe_config(), "pilot-example.no", client=client)
    assert client.calls == []


def test_domain_name_resolver_rejects_ambiguous_exact_match():
    domains = [
        {"id": 123, "domain": "pilot-example.no", "services": {"dns": True}},
        {"id": 124, "domain": "pilot-example.no", "services": {"dns": True}},
    ]
    with pytest.raises(PilotPreflightError, match="ambiguous_target"):
        validate_dns_txt_pilot_preflight_by_domain_name(
            _safe_config(), "pilot-example.no", client=DomainResolvingReadClient(domains)
        )


def test_domain_name_resolver_requires_active_dns_service():
    domains = [{"id": 123, "domain": "pilot-example.no", "services": {"dns": False}}]
    with pytest.raises(PilotPreflightError, match="dns_service_inactive"):
        validate_dns_txt_pilot_preflight_by_domain_name(
            _safe_config(), "pilot-example.no", client=DomainResolvingReadClient(domains)
        )


@pytest.mark.parametrize("value", ["", "localhost", "https://example.no", "*.example.no", "-bad.example.no"])
def test_domain_name_resolver_rejects_invalid_names_before_provider_read(value):
    client = DomainResolvingReadClient([])
    with pytest.raises(PilotPreflightError, match="invalid_target"):
        validate_dns_txt_pilot_preflight_by_domain_name(_safe_config(), value, client=client)
    assert client.domain_calls == []


def test_domain_name_resolver_preserves_sanitized_list_error():
    provider_error = DomeneshopApiError("unauthorized", "private detail", status_code=403)
    with pytest.raises(PilotPreflightError, match="unauthorized"):
        validate_dns_txt_pilot_preflight_by_domain_name(
            _safe_config(),
            "pilot-example.no",
            client=DomainResolvingReadClient(provider_error),
        )


def test_controlled_write_dry_run_is_exact_target_bound_and_creates_no_authorization_artifacts(tmp_path):
    client = DomainResolvingReadClient(
        [{"id": 123, "domain": "pilot-example.no", "services": {"dns": True}}]
    )
    evidence = validate_dns_txt_pilot_controlled_write_dry_run(
        _safe_config(),
        "pilot-example.no",
        "x" * 48,
        tmp_path / "state",
        client=client,
    )
    serialized = json.dumps(evidence)

    assert client.domain_calls == ["pilot-example.no"]
    assert client.calls == [(123, "_mcp-validation", "TXT")]
    assert evidence["mode"] == "controlled_write_preview"
    assert evidence["allowed_by_manifest"] is True
    assert evidence["live_execution_enabled"] is False
    assert evidence["approval_signing_secret_validated"] is True
    assert evidence["approval_token_issued"] is False
    assert evidence["idempotency_reservation_created"] is False
    assert evidence["audit_event_created"] is False
    assert evidence["provider_mutation_performed"] is False
    assert evidence["mandatory_controls"] == {
        "approval_token": True,
        "idempotency": True,
        "audit": True,
        "readback": True,
    }
    assert list((tmp_path / "state" / "approval-nonces").iterdir()) == []
    assert list((tmp_path / "state" / "idempotency").iterdir()) == []
    assert not (tmp_path / "state" / "audit" / "controlled-write.jsonl").exists()
    assert "pilot-example.no" not in serialized
    assert "_mcp-validation" not in serialized


def test_controlled_write_dry_run_rejects_invalid_signing_secret(tmp_path):
    client = DomainResolvingReadClient(
        [{"id": 123, "domain": "pilot-example.no", "services": {"dns": True}}]
    )
    with pytest.raises(PilotPreflightError, match="approval_secret_invalid"):
        validate_dns_txt_pilot_controlled_write_dry_run(
            _safe_config(),
            "pilot-example.no",
            "too-short",
            tmp_path / "state",
            client=client,
        )


def test_controlled_write_dry_run_requires_absolute_state_root():
    with pytest.raises(PilotPreflightError, match="invalid_state_root"):
        validate_dns_txt_pilot_controlled_write_dry_run(
            _safe_config(),
            "pilot-example.no",
            "x" * 48,
            "relative-state",
            client=DomainResolvingReadClient([]),
        )


def test_controlled_write_dry_run_rejects_repository_state_root():
    with pytest.raises(PilotPreflightError, match="invalid_state_root"):
        validate_dns_txt_pilot_controlled_write_dry_run(
            _safe_config(),
            "pilot-example.no",
            "x" * 48,
            Path.cwd() / "runtime-state",
            client=DomainResolvingReadClient([]),
        )
