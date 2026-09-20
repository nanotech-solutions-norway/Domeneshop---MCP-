"""GET-only endpoint compatibility diagnostic for the D-R4B HTTP-forward pilot.

No mutation methods are used. The diagnostic first verifies the exact accepted
CREATE state through the forward list, then probes documented host-addressing
GET variants and reports only status classes.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import DomeneshopConfig
from .http_forward_create_dry_run import DOMAIN_NAME, FORWARD_HOST
from .http_forward_post_write_verify import _resolve_domain_id

EXPECTED_URL = "https://atlas-mcp-sandbox.no/"


class HttpForwardHostGetDiagnosticError(RuntimeError):
    pass


def run_host_get_diagnostic(config: DomeneshopConfig) -> dict[str, Any]:
    if config.write_tools_enabled or not config.dry_run_default:
        raise HttpForwardHostGetDiagnosticError("unsafe_runtime_configuration")
    config.require_auth()

    from .client import DomeneshopReadClient

    reader = DomeneshopReadClient(config)
    try:
        domain_id = _resolve_domain_id(reader)
        forwards = reader.list_http_forwards(domain_id)
    finally:
        reader.close()

    matches = [
        item for item in forwards
        if isinstance(item, dict)
        and str(item.get("host", "")).strip() == FORWARD_HOST
    ]
    if len(matches) != 1:
        raise HttpForwardHostGetDiagnosticError("exact_list_state_missing_or_duplicate")
    current = matches[0]
    if (
        str(current.get("url", "")).strip() != EXPECTED_URL
        or current.get("frame") is not False
    ):
        raise HttpForwardHostGetDiagnosticError("exact_list_state_mismatch")

    fqdn = f"{FORWARD_HOST}.{DOMAIN_NAME}"
    variants = {
        "host": f"/domains/{domain_id}/forwards/{FORWARD_HOST}",
        "host_trailing_slash": f"/domains/{domain_id}/forwards/{FORWARD_HOST}/",
        "fqdn": f"/domains/{domain_id}/forwards/{fqdn}",
        "fqdn_trailing_slash": f"/domains/{domain_id}/forwards/{fqdn}/",
    }

    results: dict[str, Any] = {}
    with httpx.Client(
        base_url=config.api_base_url,
        auth=(config.auth_user, config.auth_value),
        timeout=config.timeout_seconds,
        headers={"Accept": "application/json", "User-Agent": "domeneshop-mcp/0.9.0"},
        follow_redirects=False,
    ) as client:
        for name, path in variants.items():
            try:
                response = client.get(path)
            except httpx.HTTPError:
                results[name] = {"status": "request_failed"}
                continue
            entry: dict[str, Any] = {"status_code": response.status_code}
            if response.status_code in (301, 302, 307, 308):
                entry["redirect_present"] = bool(response.headers.get("location"))
            if response.status_code == 200:
                try:
                    body = response.json()
                except ValueError:
                    entry["body_shape"] = "non_json"
                else:
                    entry["exact_match"] = (
                        isinstance(body, dict)
                        and str(body.get("host", "")).strip() == FORWARD_HOST
                        and str(body.get("url", "")).strip() == EXPECTED_URL
                        and body.get("frame") is False
                    )
            results[name] = entry

    return {
        "evidence_type": "http_forward_host_get_compatibility_diagnostic",
        "success": True,
        "provider_state_verified_by_list": True,
        "provider_mutation_performed": False,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": False,
        "results": results,
    }
