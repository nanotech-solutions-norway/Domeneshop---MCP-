"""Run the exact-target controlled-write preview and print sanitized evidence."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.pilot_preflight import (
    PILOT_HOST,
    PilotPreflightError,
    validate_dns_txt_pilot_controlled_write_dry_run,
)


def main() -> int:
    try:
        evidence = validate_dns_txt_pilot_controlled_write_dry_run(
            DomeneshopConfig.from_env(),
            os.environ.get("DS_PILOT_DOMAIN_NAME", ""),
            os.environ.get("APPROVAL_SIGNING_SECRET", ""),
            os.environ.get("PILOT_STATE_ROOT", ""),
            host=os.environ.get("DS_PILOT_TXT_HOST", PILOT_HOST),
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except PilotPreflightError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "dns_txt_pilot_controlled_write_dry_run",
                    "success": False,
                    "status": "error",
                    "mode": "controlled_write_preview",
                    "error_class": exc.error_class,
                    "approval_token_issued": False,
                    "idempotency_reservation_created": False,
                    "audit_event_created": False,
                    "provider_mutation_performed": False,
                    "domain_id_included": False,
                    "domain_name_included": False,
                    "host_included": False,
                    "payload_included": False,
                    "target_included": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
