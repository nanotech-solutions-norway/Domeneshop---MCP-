"""Sanitized GET-only diagnostic for the authorized D-R3 TXT CREATE precheck.

This script performs no provider mutation, issues no approval token, creates no
idempotency reservation, and writes no audit event. It exists only to expose
the bounded PilotPreflightError class that the live wrapper intentionally hid.
"""
from __future__ import annotations

import json
import os

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.pilot_preflight import (
    PILOT_HOST,
    PilotPreflightError,
    _normalize_domain_name,
    _resolve_exact_domain_id,
)


def main() -> int:
    client: DomeneshopReadClient | None = None
    try:
        domain_name = _normalize_domain_name(os.environ.get("DS_PILOT_DOMAIN_NAME", ""))
        config = DomeneshopConfig.from_env(
            {
                **os.environ,
                "WRITE_TOOLS_ENABLED": "false",
                "DRY_RUN_DEFAULT": "true",
                "REQUIRE_OPERATOR_APPROVAL": "true",
            }
        )
        if not config.has_auth:
            raise PilotPreflightError("credential_missing")

        client = DomeneshopReadClient(config)
        domain_id = _resolve_exact_domain_id(client, domain_name)
        records = client.list_dns_records(domain_id, host=PILOT_HOST, record_type="TXT")
        if not isinstance(records, list):
            raise PilotPreflightError("unexpected_shape")
        if records:
            raise PilotPreflightError("target_not_isolated")

        print(
            json.dumps(
                {
                    "success": True,
                    "status": "read_only_precheck_ok",
                    "existing_txt_record_count": 0,
                    "collision_detected": False,
                    "provider_mutation_performed": False,
                    "write_tools_enabled": False,
                    "domain_id_included": False,
                    "domain_name_included": False,
                    "host_included": False,
                    "provider_payload_included": False,
                },
                sort_keys=True,
            )
        )
        return 0
    except PilotPreflightError as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "status": "hold_for_review",
                    "bounded_error_class": exc.error_class,
                    "provider_mutation_performed": False,
                    "write_tools_enabled": False,
                    "domain_id_included": False,
                    "domain_name_included": False,
                    "host_included": False,
                    "provider_payload_included": False,
                },
                sort_keys=True,
            )
        )
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
