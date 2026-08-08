import json

import httpx
import pytest

from domeneshop_mcp.approval_token import ApprovalTokenError, ApprovalTokenManager, UsedNonceStore
from domeneshop_mcp.audit_store import AppendOnlyAuditStore
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.controlled_write import (
    ControlledWriteError,
    ControlledWriteExecutor,
    ControlledWriteRequest,
    canonical_payload_sha256,
)
from domeneshop_mcp.credential_policy import has_runtime_value, is_placeholder_value
from domeneshop_mcp.errors import DomeneshopApiError
from domeneshop_mcp.idempotency import FileIdempotencyStore, IdempotencyError
from domeneshop_mcp.write_client import DomeneshopWriteClient
from domeneshop_mcp.write_release import ControlledWriteRelease, ReleaseManifestError


def _foundation_manifest():
    return {
        "release_id": "D-R2",
        "environment": "test",
        "decision": "APPROVE_CONTROLLED_WRITE_FOUNDATION",
        "approved_tools": ["domeneshop_create_dns_txt"],
        "approved_target_prefixes": ["domain:1:dns:_mcp-validation"],
        "live_execution_enabled": False,
        "controls": {
            "require_approval_token": True,
            "require_idempotency": True,
            "require_audit": True,
            "require_readback": True,
        },
    }


def _release(live=True):
    payload = _foundation_manifest()
    payload["release_id"] = "D-R3-PILOT" if live else "D-R2"
    payload["decision"] = "APPROVE_CONTROLLED_WRITE_PILOT" if live else "APPROVE_CONTROLLED_WRITE_FOUNDATION"
    payload["live_execution_enabled"] = live
    return ControlledWriteRelease.from_dict(payload)


def _enabled_config():
    return DomeneshopConfig(
        auth_user="token",
        auth_value="secret",
        write_tools_enabled=True,
        dry_run_default=False,
    )


def _txt_record(data="validation=1"):
    return {"host": "_mcp-validation", "data": data, "ttl": 300, "type": "TXT"}


class FakeAdapter:
    def __init__(self):
        self.state = None

    def pre_read(self, target):
        return self.state

    def execute(self, action, target, payload):
        self.state = dict(payload)
        return {"record_id": 7}

    def read_back(self, target, result):
        return self.state

    def rollback(self, action, target, before, result):
        self.state = before
        return {"status": "rolled_back"}


class MissingReadbackAdapter(FakeAdapter):
    def read_back(self, target, result):
        return None


def test_review_markers_are_rejected():
    values = [
        "__SET_IN_SECRET_STORE__",
        "CHANGE_ME",
        "INSERT_TOKEN_HERE",
        "I'VE_ENTERED_THE_SECRET_HERE",
        "${DOMENESHOP_TOKEN}",
        "<TOKEN>",
        "{{ secret }}",
        "YOUR_API_KEY",
    ]
    assert all(is_placeholder_value(value) for value in values)
    assert all(not has_runtime_value(value) for value in values)


def test_runtime_values_remain_valid():
    assert has_runtime_value("runtime-user")
    assert has_runtime_value("v1.random-looking-runtime-value")


def test_config_rejects_sanitized_runtime_review_values():
    config = DomeneshopConfig.from_env(
        {
            "DS_AUTH_USER": "I'VE_ENTERED_THE_TOKEN_HERE",
            "DS_AUTH_VALUE": "I'VE_ENTERED_THE_SECRET_HERE",
        }
    )
    assert config.has_auth is False


def test_foundation_manifest_allows_preview_scope_only():
    release = ControlledWriteRelease.from_dict(_foundation_manifest())
    assert release.live_execution_enabled is False
    assert release.allows("domeneshop_create_dns_txt", "domain:1:dns:_mcp-validation")
    assert not release.allows("domeneshop_create_dns_txt", "domain:2:dns:_mcp-validation")


def test_live_manifest_requires_pilot_decision():
    payload = _foundation_manifest()
    payload["live_execution_enabled"] = True
    with pytest.raises(ReleaseManifestError):
        ControlledWriteRelease.from_dict(payload)


def test_live_manifest_requires_every_control():
    payload = _foundation_manifest()
    payload["decision"] = "APPROVE_CONTROLLED_WRITE_PILOT"
    payload["live_execution_enabled"] = True
    payload["controls"]["require_approval_token"] = False
    with pytest.raises(ReleaseManifestError, match="every mandatory control"):
        ControlledWriteRelease.from_dict(payload)


def test_manifest_rejects_string_boolean_values():
    payload = _foundation_manifest()
    payload["live_execution_enabled"] = "false"
    with pytest.raises(ReleaseManifestError, match="must be a boolean"):
        ControlledWriteRelease.from_dict(payload)


def test_wildcard_target_is_rejected():
    payload = _foundation_manifest()
    payload["approved_target_prefixes"] = ["*"]
    with pytest.raises(ReleaseManifestError):
        ControlledWriteRelease.from_dict(payload)


def test_token_is_payload_bound_and_one_time(tmp_path):
    manager = ApprovalTokenManager("x" * 48, UsedNonceStore(tmp_path / "used"))
    token = manager.issue(
        approval_id="APP-1",
        operator="operator",
        action="domeneshop_create_dns_txt",
        target="domain:1:dns:_mcp-validation",
        payload_sha256="a" * 64,
    )
    claims = manager.verify_and_consume(
        token,
        action="domeneshop_create_dns_txt",
        target="domain:1:dns:_mcp-validation",
        payload_sha256="a" * 64,
        operator="operator",
    )
    assert claims.approval_id == "APP-1"
    with pytest.raises(ApprovalTokenError):
        manager.verify_and_consume(
            token,
            action="domeneshop_create_dns_txt",
            target="domain:1:dns:_mcp-validation",
            payload_sha256="a" * 64,
            operator="operator",
        )


def test_token_rejects_payload_mismatch(tmp_path):
    manager = ApprovalTokenManager("x" * 48, UsedNonceStore(tmp_path / "used"))
    token = manager.issue(
        approval_id="APP-1",
        operator="operator",
        action="domeneshop_create_dns_txt",
        target="domain:1:dns:_mcp-validation",
        payload_sha256="a" * 64,
    )
    with pytest.raises(ApprovalTokenError):
        manager.verify_and_consume(
            token,
            action="domeneshop_create_dns_txt",
            target="domain:1:dns:_mcp-validation",
            payload_sha256="b" * 64,
            operator="operator",
        )


def test_idempotency_reservation_completion_and_replay(tmp_path):
    store = FileIdempotencyStore(tmp_path)
    reserved = store.reserve("operation-1", "a" * 64)
    assert reserved.status == "reserved"
    completed = store.complete("operation-1", {"record_id": 7})
    assert completed.status == "completed"
    replay = store.reserve("operation-1", "a" * 64)
    assert replay.status == "completed"
    assert replay.result == {"record_id": 7}


def test_idempotency_conflicting_payload_is_blocked(tmp_path):
    store = FileIdempotencyStore(tmp_path)
    store.reserve("operation-1", "a" * 64)
    with pytest.raises(IdempotencyError):
        store.reserve("operation-1", "b" * 64)


def test_audit_store_redacts_and_verifies_chain(tmp_path):
    path = tmp_path / "audit.jsonl"
    store = AppendOnlyAuditStore(path)
    first = store.append("preflight", "operator", "target", {"token": "secret-value", "value": 1})
    second = store.append("completed", "operator", "target", {"authorization": "Basic abc", "value": 2})
    assert first["details"]["token"] == "[REDACTED]"
    assert second["previous_hash"] == first["event_hash"]
    assert store.verify_chain() is True
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert lines[1]["details"]["authorization"] == "[REDACTED]"


def test_audit_store_redacts_common_key_variants(tmp_path):
    store = AppendOnlyAuditStore(tmp_path / "audit.jsonl")
    event = store.append(
        "preflight",
        "operator",
        "target",
        {
            "apiKey": "sensitive",
            "access_token": "sensitive",
            "nested": {"clientSecret": "sensitive", "database_password": "sensitive", "safe": "value"},
        },
    )
    assert event["details"] == {
        "apiKey": "[REDACTED]",
        "access_token": "[REDACTED]",
        "nested": {"clientSecret": "[REDACTED]", "database_password": "[REDACTED]", "safe": "value"},
    }


def test_create_dns_txt_uses_post_and_location_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v0/domains/123/dns"
        assert json.loads(request.content) == _txt_record()
        return httpx.Response(201, headers={"Location": "/v0/domains/123/dns/456"})

    client = DomeneshopWriteClient(_enabled_config(), transport=httpx.MockTransport(handler))
    assert client.create_dns_record(123, _txt_record()) == 456


def test_write_client_is_txt_only_by_default():
    client = DomeneshopWriteClient(_enabled_config(), transport=httpx.MockTransport(lambda request: httpx.Response(204)))
    with pytest.raises(ValueError):
        client.create_dns_record(123, {"host": "www", "data": "192.0.2.1", "ttl": 300, "type": "A"})


def test_write_client_respects_global_pause():
    config = DomeneshopConfig(auth_user="token", auth_value="secret", write_tools_enabled=False)
    client = DomeneshopWriteClient(config, transport=httpx.MockTransport(lambda request: httpx.Response(201)))
    with pytest.raises(DomeneshopApiError) as exc:
        client.create_dns_record(123, _txt_record())
    assert exc.value.error_class == "write_paused"


def test_delete_is_separately_disabled():
    client = DomeneshopWriteClient(_enabled_config(), transport=httpx.MockTransport(lambda request: httpx.Response(204)))
    with pytest.raises(DomeneshopApiError) as exc:
        client.delete_dns_record(123, 456)
    assert exc.value.error_class == "manual_review_required"


def test_foundation_manifest_blocks_execution(tmp_path):
    manager = ApprovalTokenManager("x" * 48, UsedNonceStore(tmp_path / "used"))
    executor = ControlledWriteExecutor(
        _release(False), manager, FileIdempotencyStore(tmp_path / "idem"), AppendOnlyAuditStore(tmp_path / "audit.jsonl")
    )
    with pytest.raises(ControlledWriteError):
        executor.execute(
            ControlledWriteRequest(
                "domeneshop_create_dns_txt",
                "domain:1:dns:_mcp-validation",
                {},
                "operator",
                "bad",
                "key",
                preflight_reference="preflight",
            ),
            FakeAdapter(),
        )


def test_live_pilot_executes_once_and_replays_result(tmp_path):
    payload = _txt_record()
    target = "domain:1:dns:_mcp-validation"
    action = "domeneshop_create_dns_txt"
    manager = ApprovalTokenManager("x" * 48, UsedNonceStore(tmp_path / "used"))
    token = manager.issue(
        approval_id="APP-1",
        operator="operator",
        action=action,
        target=target,
        payload_sha256=canonical_payload_sha256(payload),
    )
    executor = ControlledWriteExecutor(
        _release(True), manager, FileIdempotencyStore(tmp_path / "idem"), AppendOnlyAuditStore(tmp_path / "audit.jsonl")
    )
    adapter = FakeAdapter()
    request = ControlledWriteRequest(action, target, payload, "operator", token, "operation-1", preflight_reference="preflight-1")
    first = executor.execute(request, adapter)
    assert first["replayed"] is False
    second = executor.execute(request, adapter)
    assert second["replayed"] is True


def test_required_readback_failure_is_rolled_back_and_not_completed(tmp_path):
    payload = _txt_record()
    target = "domain:1:dns:_mcp-validation"
    action = "domeneshop_create_dns_txt"
    manager = ApprovalTokenManager("x" * 48, UsedNonceStore(tmp_path / "used"))
    token = manager.issue(
        approval_id="APP-2",
        operator="operator",
        action=action,
        target=target,
        payload_sha256=canonical_payload_sha256(payload),
    )
    idempotency = FileIdempotencyStore(tmp_path / "idem")
    audit_path = tmp_path / "audit.jsonl"
    executor = ControlledWriteExecutor(_release(True), manager, idempotency, AppendOnlyAuditStore(audit_path))
    adapter = MissingReadbackAdapter()
    request = ControlledWriteRequest(action, target, payload, "operator", token, "operation-2", preflight_reference="preflight-2")

    with pytest.raises(ControlledWriteError, match="audit and rollback handling"):
        executor.execute(request, adapter)

    assert adapter.state is None
    assert idempotency.get("operation-2").status == "reserved"
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event_type"] == "controlled_write_failed"
    assert events[-1]["details"]["rollback"] == {"status": "rolled_back"}
