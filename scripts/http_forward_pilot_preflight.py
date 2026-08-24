"""Run the isolated HTTP-forward pilot preflight and print sanitized evidence."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_preflight import (
    HttpForwardPreflightError,
    PILOT_FORWARD_HOST,
    validate_http_forward_pilot_preflight,
)


def main() -> int:
    try:
        evidence = validate_http_forward_pilot_preflight(
            DomeneshopConfig.from_env(),
            os.environ.get("DS_PILOT_DOMAIN_NAME", ""),
            host=os.environ.get("DS_PILOT_FORWARD_HOST", PILOT_FORWARD_HOST),
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except HttpForwardPreflightError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "http_forward_pilot_preflight",
                    "success": False,
                    "status": "error",
                    "mode": "read_only_dry_run",
                    "error_class": exc.error_class,
                    "http_forward_create_authorized": False,
                    "http_forward_update_authorized": False,
                    "http_forward_delete_authorized": False,
                    "provider_mutation_performed": False,
                    "domain_id_included": False,
                    "domain_name_included": False,
                    "host_included": False,
                    "payload_included": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
