"""Run the exact separately authorized D-R4B HTTP-forward UPDATE gate."""

from __future__ import annotations

import json

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_live_update import (
    HttpForwardLiveUpdateError,
    execute_exact_http_forward_update,
)


def main() -> int:
    try:
        evidence = execute_exact_http_forward_update(DomeneshopConfig.from_env())
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except HttpForwardLiveUpdateError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "http_forward_live_update",
                    "success": False,
                    "status": "error",
                    "error_class": exc.error_class,
                    "provider_mutation_attempted": exc.provider_mutation_attempted,
                    "provider_mutation_performed": exc.provider_mutation_performed,
                    "automatic_delete_performed": False,
                    "automatic_rollback_performed": False,
                    "http_forward_create_authorized": False,
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
