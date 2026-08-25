"""Run GET-only D-R4B HTTP-forward post-write recovery verification."""

from __future__ import annotations

import json

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_post_write_verify import (
    HttpForwardPostWriteVerifyError,
    verify_exact_http_forward_post_write_state,
)


def main() -> int:
    try:
        evidence = verify_exact_http_forward_post_write_state(DomeneshopConfig.from_env())
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except HttpForwardPostWriteVerifyError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "http_forward_post_write_recovery_verification",
                    "success": False,
                    "status": "hold",
                    "error_class": exc.error_class,
                    "provider_mutation_performed": False,
                    "http_forward_create_authorized": False,
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
