"""GET-only protected status validation with payload-free evidence output."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.status_validation import (
    DEFAULT_STATUS_URL,
    ProtectedStatusValidationError,
    validate_protected_status,
)


def main() -> int:
    try:
        evidence = validate_protected_status(
            os.environ.get("DS_STATUS_URL", DEFAULT_STATUS_URL),
            os.environ.get("DS_STATUS_AUTH_USER", ""),
            os.environ.get("DS_STATUS_AUTH_VALUE", ""),
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except ProtectedStatusValidationError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "protected_status_get",
                    "success": False,
                    "status": "error",
                    "mode": "read_only_http_get",
                    "error_class": exc.error_class,
                    "payload_included": False,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
