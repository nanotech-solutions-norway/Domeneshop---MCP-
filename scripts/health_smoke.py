"""Manual HTTP health smoke checks for Phase 4."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.health import HealthDiagnostics
from domeneshop_mcp.tools_health import http_check_endpoint, http_check_json_health, http_check_tls


def main() -> int:
    targets = [item.strip() for item in os.environ.get("HEALTH_TARGETS", "").split(",") if item.strip()]
    if not targets:
        print(json.dumps({"success": False, "message": "No HEALTH_TARGETS configured."}, indent=2))
        return 1

    client = HealthDiagnostics()
    try:
        results = []
        for target in targets:
            results.append(http_check_endpoint(client, target))
            results.append(http_check_tls(client, target))
            results.append(http_check_json_health(client, target))
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0 if all(item.get("success") for item in results) else 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
