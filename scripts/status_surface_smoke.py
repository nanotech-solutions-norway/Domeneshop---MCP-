"""GET-only status-surface validation with payload-free evidence output."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.status_validation import DEFAULT_STATUS_URL, StatusValidationError, validate_status_surface


def main() -> int:
    try:
        evidence = validate_status_surface(os.environ.get("DS_STATUS_URL", DEFAULT_STATUS_URL))
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except StatusValidationError as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "status_surface_get",
                    "success": False,
                    "status": "error",
                    "mode": "read_only_http_get",
                    "authentication_sent": False,
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
