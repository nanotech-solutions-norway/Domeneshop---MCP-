"""Exact, separately authorized live UPDATE gate for the D-R4B HTTP-forward pilot.

This module can issue exactly one bound PUT after verifying the provider is in
accepted CREATE state. It requires independent bounded GET-only readback and
never performs CREATE, DELETE, rollback, DNS, SFTP, or SQL mutation.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable
from typing import Any

import httpx

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .controlled_write import canonical_payload_sha256
from .errors import DomeneshopApiError, classify_status
from .http_forward_update_dry_run import (
    DOMAIN_NAME,
    EXPECTED_TARGET_SHA256,
    EXPECTED_UPDATE_PAYLOAD_SHA256,
    FORWARD_HOST,
    RELEASE_ID,
    REQUIRED_BEFORE_PAYLOAD_SHA256,
    accepted_create_payload,
    candidate_update_payload,
)

READBACK_ATTEMPTS = 6
READBACK_DELAY_SECONDS = 5.0


class HttpForwardLiveUpdateError(RuntimeError):
    """Fail-closed live UPDATE error with mutation-state metadata."""

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


def _normalized_forward(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        "host": str(value.get("host", "")).strip(),
        "frame": value.get("frame"),
        "url": str(value.get("url", "")).strip(),
    }


def _require_exact_authorization() -> None:
    if _enabled("WRITE_TOOLS_ENABLED"):
        raise HttpForwardLiveUpdateError("global_write_enable_forbidden")
    if not _enabled("DRY_RUN_DEFAULT", "true"):
        raise HttpForwardLiveUpdateError("dry_run_default_must_remain_true")
    if _enabled("HTTP_FORWARD_D_R4B_CREATE_AUTHORIZED"):
        raise HttpForwardLiveUpdateError("create_authorization_forbidden")
    if not _enabled("HTTP_FORWARD_D_R4B_UPDATE_AUTHORIZED"):
        raise HttpForwardLiveUpdateError("update_not_authorized")
    if _enabled("HTTP_FORWARD_D_R4B_DELETE_AUTHORIZED"):
        raise HttpForwardLiveUpdateError("delete_authorization_forbidden")
    if _enabled("HTTP_FORWARD_D_R4B_BROADER_OVERWRITE_AUTHORIZED"):
        raise HttpForwardLiveUpdateError("broader_overwrite_authorization_forbidden")

    required = {
        "HTTP_FORWARD_D_R4B_RELEASE_ID": RELEASE_ID,
        "HTTP_FORWARD_D_R4B_TARGET_SHA256": EXPECTED_TARGET_SHA256,
        "HTTP_FORWARD_D_R4B_REQUIRED_BEFORE_PAYLOAD_SHA256": REQUIRED_BEFORE_PAYLOAD_SHA256,
        "HTTP_FORWARD_D_R4B_UPDATE_PAYLOAD_SHA256": EXPECTED_UPDATE_PAYLOAD_SHA256,
        "HTTP_FORWARD_D_R4B_DOMAIN_NAME": DOMAIN_NAME,
        "HTTP_FORWARD_D_R4B_HOST": FORWARD_HOST,
    }
    for name, expected in required.items():
        if os.environ.get(name, "") != expected:
            raise HttpForwardLiveUpdateError(f"authorization_binding_mismatch:{name}")


def _resolve_domain_id(read_client: DomeneshopReadClient) -> int:
    try:
        domains = read_client.list_domains(domain=DOMAIN_NAME)
    except DomeneshopApiError as exc:
        raise HttpForwardLiveUpdateError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardLiveUpdateError("provider_read_failed") from exc

    if not isinstance(domains, list):
        raise HttpForwardLiveUpdateError("unexpected_domain_shape")
    matches = [
        item
        for item in domains
        if isinstance(item, dict)
        and str(item.get("domain", "")).strip().lower().rstrip(".") == DOMAIN_NAME
    ]
    if len(matches) != 1:
        raise HttpForwardLiveUpdateError("exact_domain_resolution_failed")
    item = matches[0]
    services = item.get("services")
    if not isinstance(services, dict) or services.get("dns") is not True:
        raise HttpForwardLiveUpdateError("dns_service_inactive")
    try:
        return int(item["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HttpForwardLiveUpdateError("unexpected_domain_shape") from exc


def _find_unique_forward(read_client: DomeneshopReadClient, domain_id: int) -> dict[str, Any]:
    try:
        forwards = read_client.list_http_forwards(domain_id)
    except DomeneshopApiError as exc:
        raise HttpForwardLiveUpdateError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardLiveUpdateError("provider_read_failed") from exc

    if not isinstance(forwards, list):
        raise HttpForwardLiveUpdateError("unexpected_forward_list_shape")
    matches = [
        _normalized_forward(item)
        for item in forwards
        if isinstance(item, dict) and str(item.get("host", "")).strip() == FORWARD_HOST
    ]
    if len(matches) == 0:
        raise HttpForwardLiveUpdateError("required_before_forward_missing")
    if len(matches) != 1:
        raise HttpForwardLiveUpdateError("duplicate_forward_state")
    result = matches[0]
    if result is None:
        raise HttpForwardLiveUpdateError("unexpected_forward_shape")
    return result


def _verify_exact_before_state(read_client: DomeneshopReadClient, domain_id: int) -> None:
    if _sha256(_target(domain_id)) != EXPECTED_TARGET_SHA256:
        raise HttpForwardLiveUpdateError("target_binding_mismatch")

    current = _find_unique_forward(read_client, domain_id)
    expected = accepted_create_payload()
    if current != expected:
        raise HttpForwardLiveUpdateError("required_before_state_mismatch")
    if canonical_payload_sha256(current) != REQUIRED_BEFORE_PAYLOAD_SHA256:
        raise HttpForwardLiveUpdateError("required_before_hash_mismatch")


def _validate_put_response(response: httpx.Response) -> None:
    if response.status_code >= 400:
        raise HttpForwardLiveUpdateError(
            classify_status(response.status_code),
            provider_mutation_attempted=True,
            provider_mutation_performed=None,
        )
    if response.status_code != 200:
        raise HttpForwardLiveUpdateError(
            "unexpected_update_success_status",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        )
    try:
        body = _normalized_forward(response.json())
    except ValueError as exc:
        raise HttpForwardLiveUpdateError(
            "update_response_non_json",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        ) from exc
    if body != candidate_update_payload():
        raise HttpForwardLiveUpdateError(
            "update_response_mismatch",
            provider_mutation_attempted=True,
            provider_mutation_performed=True,
        )


def _verify_update_readback(
    config: DomeneshopConfig,
    domain_id: int,
    *,
    read_client_factory: Callable[[DomeneshopConfig], DomeneshopReadClient],
    sleep_fn: Callable[[float], None],
    attempts: int,
    delay_seconds: float,
) -> int:
    expected = candidate_update_payload()
    last_error: HttpForwardLiveUpdateError | None = None

    for attempt in range(1, attempts + 1):
        reader = read_client_factory(config)
        try:
            try:
                current = _find_unique_forward(reader, domain_id)
            except HttpForwardLiveUpdateError as exc:
                last_error = exc
            else:
                if current == expected and canonical_payload_sha256(current) == EXPECTED_UPDATE_PAYLOAD_SHA256:
                    return attempt
                last_error = HttpForwardLiveUpdateError(
                    "post_write_readback_mismatch",
                    provider_mutation_attempted=True,
                    provider_mutation_performed=True,
                )
        finally:
            reader.close()

        if attempt < attempts:
            sleep_fn(delay_seconds)

    error_class = last_error.error_class if last_error else "post_write_readback_failed"
    raise HttpForwardLiveUpdateError(
        error_class,
        provider_mutation_attempted=True,
        provider_mutation_performed=True,
    )


def execute_exact_http_forward_update(
    config: DomeneshopConfig,
    *,
    transport: httpx.BaseTransport | None = None,
    read_client_factory: Callable[[DomeneshopConfig], DomeneshopReadClient] = DomeneshopReadClient,
    sleep_fn: Callable[[float], None] = time.sleep,
    readback_attempts: int = READBACK_ATTEMPTS,
    readback_delay_seconds: float = READBACK_DELAY_SECONDS,
) -> dict[str, Any]:
    """Perform exactly one authorized UPDATE and bounded independent readback."""

    _require_exact_authorization()
    if config.write_tools_enabled or not config.dry_run_default:
        raise HttpForwardLiveUpdateError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise HttpForwardLiveUpdateError("credential_missing") from exc

    before_payload = accepted_create_payload()
    update_payload = candidate_update_payload()
    if canonical_payload_sha256(before_payload) != REQUIRED_BEFORE_PAYLOAD_SHA256:
        raise HttpForwardLiveUpdateError("required_before_binding_mismatch")
    if canonical_payload_sha256(update_payload) != EXPECTED_UPDATE_PAYLOAD_SHA256:
        raise HttpForwardLiveUpdateError("update_payload_binding_mismatch")
    if before_payload["host"] != update_payload["host"] or update_payload["host"] != FORWARD_HOST:
        raise HttpForwardLiveUpdateError("host_change_forbidden")

    pre_reader = read_client_factory(config)
    try:
        domain_id = _resolve_domain_id(pre_reader)
        _verify_exact_before_state(pre_reader, domain_id)
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
            response = mutation_client.put(
                f"/domains/{domain_id}/forwards/{FORWARD_HOST}",
                json=update_payload,
            )
    except httpx.HTTPError as exc:
        raise HttpForwardLiveUpdateError(
            "provider_mutation_request_failed",
            provider_mutation_attempted=mutation_attempted,
            provider_mutation_performed=None if mutation_attempted else False,
        ) from exc

    _validate_put_response(response)

    attempts_used = _verify_update_readback(
        config,
        domain_id,
        read_client_factory=read_client_factory,
        sleep_fn=sleep_fn,
        attempts=readback_attempts,
        delay_seconds=readback_delay_seconds,
    )

    return {
        "release_id": RELEASE_ID,
        "success": True,
        "status": "updated_and_readback_verified",
        "target_sha256": EXPECTED_TARGET_SHA256,
        "required_before_payload_sha256": REQUIRED_BEFORE_PAYLOAD_SHA256,
        "update_payload_sha256": EXPECTED_UPDATE_PAYLOAD_SHA256,
        "provider_mutation_attempted": True,
        "provider_mutation_performed": True,
        "independent_readback_verified": True,
        "readback_method": "list_forwards",
        "readback_attempts_used": attempts_used,
        "host_change_performed": False,
        "automatic_delete_performed": False,
        "automatic_rollback_performed": False,
        "http_forward_create_authorized": False,
        "http_forward_update_authorized": True,
        "http_forward_delete_authorized": False,
        "broader_overwrite_authorized": False,
        "write_tools_enabled": False,
        "dry_run_default": True,
    }
