"""Exact, separately authorized live CREATE gate for the D-R4B HTTP-forward pilot.

This module deliberately does not expose a general HTTP-forward write client.
It can issue exactly one bound POST after fresh GET-only collision checks and
requires independent readback. It never performs UPDATE, DELETE, rollback, DNS,
SFTP, or SQL mutation.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable
from typing import Any

import httpx

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .controlled_write import canonical_payload_sha256
from .errors import DomeneshopApiError, classify_status
from .http_forward_create_dry_run import (
    DOMAIN_NAME,
    EXPECTED_PAYLOAD_SHA256,
    EXPECTED_TARGET_SHA256,
    FORWARD_HOST,
    FORWARD_URL,
    RELEASE_ID,
    candidate_payload,
)

BLOCKING_DNS_TYPES = frozenset({"A", "AAAA", "ANAME", "CNAME"})


class HttpForwardLiveCreateError(RuntimeError):
    """Fail-closed live-gate error with mutation-state metadata."""

    def __init__(
        self,
        error_class: str,
        *,
        provider_mutation_attempted: bool = False,
        provider_mutation_performed: bool | None = False,
    ) -> None:
        super().__init__(error_class)
        self.error_class = error_class
        self.provider_mutation_attempted = provider_mutation_attempted
        self.provider_mutation_performed = provider_mutation_performed


def _enabled(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _target(domain_id: int) -> str:
    return f"domain:{domain_id}:forward:{FORWARD_HOST}"


def _require_exact_authorization() -> None:
    if _enabled("WRITE_TOOLS_ENABLED"):
        raise HttpForwardLiveCreateError("global_write_enable_forbidden")
    if not _enabled("DRY_RUN_DEFAULT", "true"):
        raise HttpForwardLiveCreateError("dry_run_default_must_remain_true")
    if not _enabled("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED"):
        raise HttpForwardLiveCreateError("create_not_authorized")
    if _enabled("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED"):
        raise HttpForwardLiveCreateError("update_authorization_forbidden")
    if _enabled("HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED"):
        raise HttpForwardLiveCreateError("delete_authorization_forbidden")
    if _enabled("HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED"):
        raise HttpForwardLiveCreateError("broader_overwrite_authorization_forbidden")

    required = {
        "HTTP_FORWARD_D_R4B_RELEASE_ID": RELEASE_ID,
        "HTTP_FORWARD_D_R4B_TARGET_SHA256": EXPECTED_TARGET_SHA256,
        "HTTP_FORWARD_D_R4B_PAYLOAD_SHA256": EXPECTED_PAYLOAD_SHA256,
        "HTTP_FORWARD_D_R4B_DOMAIN_NAME": DOMAIN_NAME,
        "HTTP_FORWARD_D_R4B_HOST": FORWARD_HOST,
    }
    for name, expected in required.items():
        if os.environ.get(name, "") != expected:
            raise HttpForwardLiveCreateError(f"authorization_binding_mismatch:{name}")


def _resolve_domain_id(read_client: DomeneshopReadClient) -> int:
    try:
        domains = read_client.list_domains(domain=DOMAIN_NAME)
    except DomeneshopApiError as exc:
        raise HttpForwardLiveCreateError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardLiveCreateError("provider_read_failed") from exc

    if not isinstance(domains, list):
        raise HttpForwardLiveCreateError("unexpected_domain_shape")
    matches = [
        item
        for item in domains
        if isinstance(item, dict)
        and str(item.get("domain", "")).strip().lower().rstrip(".") == DOMAIN_NAME
    ]
    if len(matches) != 1:
        raise HttpForwardLiveCreateError("exact_domain_resolution_failed")
    item = matches[0]
    services = item.get("services")
    if not isinstance(services, dict) or services.get("dns") is not True:
        raise HttpForwardLiveCreateError("dns_service_inactive")
    try:
        return int(item["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HttpForwardLiveCreateError("unexpected_domain_shape") from exc


def _fresh_preflight(read_client: DomeneshopReadClient, domain_id: int) -> None:
    target_sha256 = _sha256(_target(domain_id))
    if target_sha256 != EXPECTED_TARGET_SHA256:
        raise HttpForwardLiveCreateError("target_binding_mismatch")

    try:
        forwards = read_client.list_http_forwards(domain_id)
        dns_records = read_client.list_dns_records(domain_id, host=FORWARD_HOST)
    except DomeneshopApiError as exc:
        raise HttpForwardLiveCreateError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardLiveCreateError("provider_read_failed") from exc

    if not isinstance(forwards, list) or not isinstance(dns_records, list):
        raise HttpForwardLiveCreateError("unexpected_preflight_shape")

    if any(
        isinstance(item, dict) and str(item.get("host", "")).strip() == FORWARD_HOST
        for item in forwards
    ):
        raise HttpForwardLiveCreateError("existing_forward_collision")

    blocking_dns = [
        item
        for item in dns_records
        if isinstance(item, dict)
        and str(item.get("host", "")).strip() == FORWARD_HOST
        and str(item.get("type", "")).strip().upper() in BLOCKING_DNS_TYPES
    ]
    if blocking_dns:
        raise HttpForwardLiveCreateError("blocking_dns_collision")


def _verify_readback(read_client: DomeneshopReadClient, domain_id: int) -> None:
    try:
        result = read_client.get_http_forward(domain_id, FORWARD_HOST)
    except DomeneshopApiError as exc:
        raise HttpForwardLiveCreateError(
            "post_write_readback_failed",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        ) from exc
    except Exception as exc:
        raise HttpForwardLiveCreateError(
            "post_write_readback_failed",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        ) from exc

    if not isinstance(result, dict):
        raise HttpForwardLiveCreateError(
            "post_write_readback_shape_mismatch",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        )

    host_ok = str(result.get("host", "")).strip() == FORWARD_HOST
    url_ok = str(result.get("url", "")).strip() == FORWARD_URL
    frame_ok = result.get("frame") is False
    if not (host_ok and url_ok and frame_ok):
        raise HttpForwardLiveCreateError(
            "post_write_readback_mismatch",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        )


def execute_exact_http_forward_create(
    config: DomeneshopConfig,
    *,
    transport: httpx.BaseTransport | None = None,
    read_client_factory: Callable[[DomeneshopConfig], DomeneshopReadClient] = DomeneshopReadClient,
) -> dict[str, Any]:
    """Perform exactly one authorized CREATE and independent readback."""

    _require_exact_authorization()
    if config.write_tools_enabled or not config.dry_run_default:
        raise HttpForwardLiveCreateError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise HttpForwardLiveCreateError("credential_missing") from exc

    payload = candidate_payload()
    if canonical_payload_sha256(payload) != EXPECTED_PAYLOAD_SHA256:
        raise HttpForwardLiveCreateError("payload_binding_mismatch")

    pre_reader = read_client_factory(config)
    try:
        domain_id = _resolve_domain_id(pre_reader)
        _fresh_preflight(pre_reader, domain_id)
    finally:
        pre_reader.close()

    mutation_attempted = False
    try:
        with httpx.Client(
            base_url=config.api_base_url,
            auth=(config.auth_user, config.auth_value),
            timeout=config.timeout_seconds,
            transport=transport,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "domeneshop-mcp/0.9.0",
            },
        ) as mutation_client:
            mutation_attempted = True
            response = mutation_client.post(f"/domains/{domain_id}/forwards/", json=payload)
    except httpx.HTTPError as exc:
        raise HttpForwardLiveCreateError(
            "provider_mutation_request_failed",
            provider_mutation_attempted=mutation_attempted,
            provider_mutation_performed=None if mutation_attempted else False,
        ) from exc

    if response.status_code >= 400:
        raise HttpForwardLiveCreateError(
            classify_status(response.status_code),
            provider_mutation_attempted=True,
            provider_mutation_performed=None,
        )

    post_reader = read_client_factory(config)
    try:
        _verify_readback(post_reader, domain_id)
    finally:
        post_reader.close()

    return {
        "release_id": RELEASE_ID,
        "success": True,
        "status": "created_and_readback_verified",
        "target_sha256": EXPECTED_TARGET_SHA256,
        "payload_sha256": EXPECTED_PAYLOAD_SHA256,
        "provider_mutation_attempted": True,
        "provider_mutation_performed": True,
        "independent_readback_verified": True,
        "automatic_delete_performed": False,
        "automatic_rollback_performed": False,
        "http_forward_create_authorized": True,
        "http_forward_update_authorized": False,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": False,
        "dry_run_default": True,
    }
