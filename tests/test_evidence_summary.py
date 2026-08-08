import json

from domeneshop_mcp.evidence_summary import summarize_collection_result


def test_collection_summary_omits_provider_payload():
    result = {
        "success": True,
        "status": "ok",
        "mode": "read_only",
        "write_paused": True,
        "data": [
            {"id": 123, "domain": "private-customer.example"},
            {"id": 456, "domain": "internal.example"},
        ],
        "warnings": [],
    }

    summary = summarize_collection_result(result, evidence_type="domeneshop_domain_list")
    serialized = json.dumps(summary)

    assert summary["success"] is True
    assert summary["item_count"] == 2
    assert summary["payload_included"] is False
    assert "private-customer" not in serialized
    assert "123" not in serialized


def test_collection_summary_omits_remote_paths():
    result = {
        "success": True,
        "status": "ok",
        "mode": "sftp_read_only",
        "write_paused": True,
        "data": [{"path": "/www/private/config.php", "size": 42}],
        "warnings": ["example warning"],
    }

    summary = summarize_collection_result(result, evidence_type="sftp_directory_list")
    serialized = json.dumps(summary)

    assert summary["item_count"] == 1
    assert summary["warnings_count"] == 1
    assert "/www/private" not in serialized


def test_failure_summary_omits_message_and_data():
    result = {
        "success": False,
        "status": "error",
        "mode": "read_only",
        "write_paused": True,
        "error_class": "credential_missing",
        "message": "Sensitive provider response must not be copied.",
        "data": {"secret": "do-not-copy"},
    }

    summary = summarize_collection_result(result, evidence_type="domeneshop_domain_list")
    serialized = json.dumps(summary)

    assert summary["success"] is False
    assert summary["error_class"] == "credential_missing"
    assert "Sensitive provider" not in serialized
    assert "do-not-copy" not in serialized
