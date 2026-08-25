"""GET-only recovery verification for the D-R4B HTTP-forward CREATE.

This module exists specifically for the case where the provider accepted the
CREATE but the immediate post-write readback failed. It never issues POST, PUT,
DELETE, DNS, SFTP, or SQL mutations. It uses bounded retries and accepts success
only when the exact authorized forward state is observed through a GET endpoint.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .client import DomeneshopReadClient
from .config import DomeneshopConfig
from .errors import DomeneshopApiError
from .http_forward_create_dry_run import (
    DOMAIN_NAME,
    EXPECTED_PAYLOAD_SHA256,
    EXPECTED_TARGET_SHA256,
    FORWARD_HOST,
    FORWARD_URL,
    RELEASE_ID,
)


class HttpForwardPostWriteVerifyError(RuntimeError):
    """Sanitized fail-closed recovery-verification error."""

    def __init__(self, error_class: str) -> None:
        super().__init__(error_class)
        self.error_class = error_class


def _resolve_domain_id(read_client: DomeneshopReadClient) -> int:
    try:
        domains = read_client.list_domains(domain=DOMAIN_NAME)
    except DomeneshopApiError as exc:
        raise HttpForwardPostWriteVerifyError(exc.error_class) from exc
    except Exception as exc:
        raise HttpForwardPostWriteVerifyError("provider_read_failed") from exc

    if not isinstance(domains, list):
        raise HttpForwardPostWriteVerifyError("unexpected_domain_shape")
    matches = [
        item
        for item in domains
        if isinstance(item, dict)
        and str(item.get("domain", "")).strip().lower().rstrip(".") == DOMAIN_NAME
    ]
    if len(matches) != 1:
        raise HttpForwardPostWriteVerifyError("exact_domain_resolution_failed")
    item = matches[0]
    services = item.get("services")
    if not isinstance(services, dict) or services.get("dns") is not True:
        raise HttpForwardPostWriteVerifyError("dns_service_inactive")
    try:
        return int(item["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HttpForwardPostWriteVerifyError("unexpected_domain_shape") from exc


def _exact_match(item: Any) -> bool:
    return (
        isinstance(item, dict)
        and str(item.get("host", "")).strip() == FORWARD_HOST
        and str(item.get("url", "")).strip() == FORWARD_URL
        and item.get("frame") is False
    )


def _matching_host(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise HttpForwardPostWriteVerifyError("unexpected_forward_list_shape")
    return [
        item
        for item in items
        if isinstance(item, dict) and str(item.get("host", "")).strip() == FORWARD_HOST
    ]


def verify_exact_http_forward_post_write_state(
    config: DomeneshopConfig,
    *,
    attempts: int = 6,
    delay_seconds: float = 5.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    client_factory: Callable[[DomeneshopConfig], DomeneshopReadClient] = DomeneshopReadClient,
) -> dict[str, Any]:
    """Verify the exact CREATE state using GET-only bounded retries."""

    if config.write_tools_enabled or not config.dry_run_default:
        raise HttpForwardPostWriteVerifyError("unsafe_runtime_configuration")
    try:
        config.require_auth()
    except ValueError as exc:
        raise HttpForwardPostWriteVerifyError("credential_missing") from exc
    if attempts < 1 or attempts > 12:
        raise HttpForwardPostWriteVerifyError("invalid_retry_configuration")
    if delay_seconds < 0 or delay_seconds > 30:
        raise HttpForwardPostWriteVerifyError("invalid_retry_configuration")

    last_read_error = "not_visible"
    for attempt in range(1, attempts + 1):
        client = client_factory(config)
        try:
            domain_id = _resolve_domain_id(client)

            direct_result: Any = None
            direct_error: str | None = None
            try:
                direct_result = client.get_http_forward(domain_id, FORWARD_HOST)
            except DomeneshopApiError as exc:
                direct_error = exc.error_class
            except Exception:
                direct_error = "provider_read_failed"

            if _exact_match(direct_result):
                return {
                    "evidence_type": "http_forward_post_write_recovery_verification",
                    "release_id": RELEASE_ID,
                    "success": True,
                    "status": "exact_create_state_verified",
                    "verification_method": "get_by_host",
                    "attempts_used": attempt,
                    "target_sha256": EXPECTED_TARGET_SHA256,
                    "payload_sha256": EXPECTED_PAYLOAD_SHA256,
                    "exact_state_verified": True,
                    "provider_mutation_performed": False,
                    "http_forward_create_authorized": False,
                    "http_forward_update_authorized": False,
                    "http_forward_delete_authorized": False,
                    "broader_overwrite_authorized": False,
                    "write_tools_enabled": False,
                    "dry_run_default": True,
                }
            if direct_result is not None and isinstance(direct_result, dict):
                raise HttpForwardPostWriteVerifyError("post_write_state_mismatch")

            try:
                forwards = client.list_http_forwards(domain_id)
            except DomeneshopApiError as exc:
                last_read_error = exc.error_class
                forwards = None
            except Exception:
                last_read_error = "provider_read_failed"
                forwards = None

            if forwards is not None:
                matches = _matching_host(forwards)
                if len(matches) > 1:
                    raise HttpForwardPostWriteVerifyError("duplicate_forward_state")
                if len(matches) == 1:
                    if _exact_match(matches[0]):
                        return {
                            "evidence_type": "http_forward_post_write_recovery_verification",
                            "release_id": RELEASE_ID,
                            "success": True,
                            "status": "exact_create_state_verified",
                            "verification_method": "list_forwards",
                            "attempts_used": attempt,
                            "target_sha256": EXPECTED_TARGET_SHA256,
                            "payload_sha256": EXPECTED_PAYLOAD_SHA256,
                            "exact_state_verified": True,
                            "provider_mutation_performed": False,
                            "http_forward_create_authorized": False,
                            "http_forward_update_authorized": False,
                            "http_forward_delete_authorized": False,
                            "broader_overwrite_authorized": False,
                            "write_tools_enabled": False,
                            "dry_run_default": True,
                        }
                    raise HttpForwardPostWriteVerifyError("post_write_state_mismatch")

            last_read_error = direct_error or last_read_error
        finally:
            client.close()

        if attempt < attempts:
            sleep_fn(delay_seconds)

    raise HttpForwardPostWriteVerifyError(f"post_write_state_not_verified:{last_read_error}")
