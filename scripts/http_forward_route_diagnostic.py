"""GET-only diagnostic for Domeneshop HTTP-forward single-host routing.

No provider mutation methods are used. The diagnostic first proves the exact
accepted CREATE state through list-forwards, then probes documented single-host
GET route variants to isolate the provider 404 observed by GET/PUT.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.controlled_write import canonical_payload_sha256
from domeneshop_mcp.http_forward_create_dry_run import (
    DOMAIN_NAME,
    EXPECTED_PAYLOAD_SHA256,
    EXPECTED_TARGET_SHA256,
    FORWARD_HOST,
    candidate_payload,
)


def _enabled(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _require_read_only() -> None:
    if _enabled("WRITE_TOOLS_ENABLED"):
        raise RuntimeError("global_write_enable_forbidden")
    if not _enabled("DRY_RUN_DEFAULT", "true"):
        raise RuntimeError("dry_run_default_must_remain_true")
    for name in (
        "HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED",
        "HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED",
    ):
        if _enabled(name):
            raise RuntimeError(f"mutation_authorization_forbidden:{name}")


def _normalize(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "host": str(value.get("host", "")).strip(),
        "frame": value.get("frame"),
        "url": str(value.get("url", "")).strip(),
    }


def run() -> dict[str, Any]:
    _require_read_only()
    config = DomeneshopConfig.from_env()
    config.require_auth()

    expected = candidate_payload()
    if canonical_payload_sha256(expected) != EXPECTED_PAYLOAD_SHA256:
        raise RuntimeError("accepted_create_payload_binding_mismatch")

    with httpx.Client(
        base_url=config.api_base_url,
        auth=(config.auth_user, config.auth_value),
        timeout=config.timeout_seconds,
        headers={"Accept": "application/json", "User-Agent": "domeneshop-mcp/0.9.0"},
    ) as client:
        domains = client.get("/domains", params={"domain": DOMAIN_NAME})
        domains.raise_for_status()
        items = domains.json()
        matches = [
            item for item in items
            if isinstance(item, dict)
            and str(item.get("domain", "")).strip().lower().rstrip(".") == DOMAIN_NAME
        ]
        if len(matches) != 1:
            raise RuntimeError("exact_domain_resolution_failed")
        domain_id = int(matches[0]["id"])

        target = f"domain:{domain_id}:forward:{FORWARD_HOST}"
        import hashlib
        if hashlib.sha256(target.encode("utf-8")).hexdigest() != EXPECTED_TARGET_SHA256:
            raise RuntimeError("target_binding_mismatch")

        listed = client.get(f"/domains/{domain_id}/forwards/")
        listed.raise_for_status()
        forwards = listed.json()
        listed_matches = [
            _normalize(item)
            for item in forwards
            if isinstance(item, dict) and str(item.get("host", "")).strip() == FORWARD_HOST
        ]
        if listed_matches != [expected]:
            raise RuntimeError("accepted_create_state_not_present")

        fqdn = f"{FORWARD_HOST}.{DOMAIN_NAME}"
        variants = {
            "documented_host": f"/domains/{domain_id}/forwards/{FORWARD_HOST}",
            "documented_host_trailing_slash": f"/domains/{domain_id}/forwards/{FORWARD_HOST}/",
            "fqdn_host": f"/domains/{domain_id}/forwards/{fqdn}",
            "fqdn_host_trailing_slash": f"/domains/{domain_id}/forwards/{fqdn}/",
        }

        results: dict[str, Any] = {}
        for name, path in variants.items():
            response = client.get(path)
            exact_match = False
            if response.status_code == 200:
                try:
                    exact_match = _normalize(response.json()) == expected
                except ValueError:
                    exact_match = False
            results[name] = {
                "status_code": response.status_code,
                "exact_state_match": exact_match,
            }

    return {
        "evidence_type": "http_forward_single_host_route_diagnostic",
        "success": True,
        "mode": "get_only",
        "accepted_create_state_verified_by_list": True,
        "route_results": results,
        "provider_mutation_performed": False,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": False,
        "dry_run_default": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
