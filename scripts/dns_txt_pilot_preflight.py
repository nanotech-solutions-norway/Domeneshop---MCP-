"""Run the isolated DNS TXT pilot preflight and print sanitized evidence."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.pilot_preflight import PILOT_HOST, PilotPreflightError, validate_dns_txt_pilot_preflight


def main() -> int:
    try:
        evidence = validate_dns_txt_pilot_preflight(
            DomeneshopConfig.from_env(),
            os.environ.get("DS_PILOT_DOMAIN_ID", ""),
            host=os.environ.get("DS_PILOT_TXT_HOST", PILOT_HOST),
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except PilotPreflightError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "dns_txt_pilot_preflight",
                    "success": False,
                    "status": "error",
                    "mode": "read_only_dry_run",
                    "error_class": exc.error_class,
                    "provider_mutation_performed": False,
                    "domain_id_included": False,
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
