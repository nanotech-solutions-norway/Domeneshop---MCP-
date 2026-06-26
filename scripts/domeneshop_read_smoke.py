"""Manual read smoke test for Domeneshop Phase 2."""

from __future__ import annotations

import json

from domeneshop_mcp.client import DomeneshopReadClient
from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.tools_read import list_domains


def main() -> int:
    config = DomeneshopConfig.from_env()
    client = DomeneshopReadClient(config)
    try:
        result = list_domains(client)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("success") else 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
