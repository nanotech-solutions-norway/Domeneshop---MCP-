from domeneshop_mcp.sanitizers import redact_mapping, sanitize_invoice


def test_redact_mapping_redacts_auth_keys():
    payload = {
        "authorization": "abc",
        "nested": {"auth_value": "def"},
        "safe": "value",
    }
    assert redact_mapping(payload) == {
        "authorization": "[REDACTED]",
        "nested": {"auth_value": "[REDACTED]"},
        "safe": "value",
    }


def test_sanitize_invoice_removes_url_code_field():
    invoice = {
        "id": 1,
        "type": "invoice",
        "amount": 120,
        "currency": "NOK",
        "status": "paid",
        "url": "https://www.domeneshop.no/invoice?nr=1&code=value",
    }
    sanitized = sanitize_invoice(invoice)
    assert sanitized == {
        "id": 1,
        "type": "invoice",
        "amount": 120,
        "currency": "NOK",
        "status": "paid",
    }
