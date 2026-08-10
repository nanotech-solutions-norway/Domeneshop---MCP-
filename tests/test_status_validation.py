import json

import httpx
import pytest

from domeneshop_mcp.status_validation import StatusValidationError, validate_status_surface


def test_status_surface_get_returns_payload_free_evidence_without_authentication():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.host == "ds.atlas-ai.no"
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"status": "ok", "write_tools_enabled": False})

    evidence = validate_status_surface(
        "https://ds.atlas-ai.no/",
        transport=httpx.MockTransport(handler),
    )

    serialized = json.dumps(evidence)
    assert evidence["success"] is True
    assert evidence["http_status"] == 200
    assert evidence["json_key_count"] == 2
    assert evidence["authentication_sent"] is False
    assert evidence["payload_included"] is False
    assert "write_tools_enabled" not in serialized


def test_status_surface_rejects_unauthorized_without_response_body():
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"private": "detail"}))

    with pytest.raises(StatusValidationError, match="unauthorized"):
        validate_status_surface(
            "https://ds.atlas-ai.no/",
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
def test_status_surface_rejects_unapproved_targets(url):
    with pytest.raises(StatusValidationError, match="invalid_target"):
        validate_status_surface(url)


def test_status_surface_rejects_non_object_json():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=["not", "an", "object"]))

    with pytest.raises(StatusValidationError, match="unexpected_shape"):
        validate_status_surface(
            "https://ds.atlas-ai.no/",
            transport=transport,
        )
