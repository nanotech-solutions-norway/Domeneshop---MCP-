import json

import httpx
import pytest

from domeneshop_mcp.status_validation import ProtectedStatusValidationError, validate_protected_status


def test_protected_status_get_returns_payload_free_evidence():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "ds.atlas-ai.no"
        assert request.headers.get("authorization", "").startswith("Basic ")
        return httpx.Response(200, json={"status": "ok", "write_tools_enabled": False})

    evidence = validate_protected_status(
        "https://ds.atlas-ai.no/",
        "runtime-user",
        "runtime-password",
        transport=httpx.MockTransport(handler),
    )

    serialized = json.dumps(evidence)
    assert evidence["success"] is True
    assert evidence["http_status"] == 200
    assert evidence["json_key_count"] == 2
    assert evidence["payload_included"] is False
    assert "write_tools_enabled" not in serialized
    assert "runtime-password" not in serialized


def test_protected_status_rejects_unauthorized_without_response_body():
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"private": "detail"}))

    with pytest.raises(ProtectedStatusValidationError, match="unauthorized"):
        validate_protected_status(
            "https://ds.atlas-ai.no/",
            "runtime-user",
            "runtime-password",
            transport=transport,
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://ds.atlas-ai.no/",
        "https://example.invalid/",
        "https://ds.atlas-ai.no/?token=value",
    ],
)
def test_protected_status_rejects_unapproved_targets(url):
    with pytest.raises(ProtectedStatusValidationError, match="invalid_target"):
        validate_protected_status(url, "runtime-user", "runtime-password")


def test_protected_status_rejects_placeholder_credentials_before_request():
    with pytest.raises(ProtectedStatusValidationError, match="credential_missing"):
        validate_protected_status("https://ds.atlas-ai.no/", "__SET_IN_SECRET_STORE__", "runtime-password")


def test_protected_status_rejects_non_object_json():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=["not", "an", "object"]))

    with pytest.raises(ProtectedStatusValidationError, match="unexpected_shape"):
        validate_protected_status(
            "https://ds.atlas-ai.no/",
            "runtime-user",
            "runtime-password",
            transport=transport,
        )
