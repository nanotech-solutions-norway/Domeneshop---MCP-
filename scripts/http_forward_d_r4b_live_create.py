"""Run the exact authorized D-R4B HTTP-forward CREATE gate and print sanitized evidence."""

from __future__ import annotations

import json

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_live_create import (
    HttpForwardLiveCreateError,
    execute_exact_http_forward_create,
)


def main() -> int:
    try:
        evidence = execute_exact_http_forward_create(DomeneshopConfig.from_env())
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except HttpForwardLiveCreateError as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "status": "hold",
                    "error_class": exc.error_class,
                    "provider_mutation_attempted": exc.provider_mutation_attempted,
                    "provider_mutation_performed": exc.provider_mutation_performed,
                    "automatic_delete_performed": False,
                    "automatic_rollback_performed": False,
                    "http_forward_update_authorized": False,
                    "http_forward_delete_authorized": False,
                    "broader_overwrite_authorized": False,
                    "write_tools_enabled": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
