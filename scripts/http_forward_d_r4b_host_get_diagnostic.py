from __future__ import annotations

import json
import sys

from domeneshop_mcp.config import DomeneshopConfig
from domeneshop_mcp.http_forward_host_get_diagnostic import (
    HttpForwardHostGetDiagnosticError,
    run_host_get_diagnostic,
)


def main() -> int:
    try:
        evidence = run_host_get_diagnostic(DomeneshopConfig.from_env())
    except (HttpForwardHostGetDiagnosticError, ValueError) as exc:
        print(json.dumps({
            "evidence_type": "http_forward_host_get_compatibility_diagnostic",
            "success": False,
            "status": "error",
            "error_class": str(exc),
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
        }, indent=2, sort_keys=True))
        return 1
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
