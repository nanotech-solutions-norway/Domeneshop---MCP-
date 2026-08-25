"""Print sanitized deterministic evidence for the D-R4B HTTP-forward UPDATE dry-run."""

from __future__ import annotations

import json
import os

from domeneshop_mcp.http_forward_update_dry_run import build_update_dry_run_evidence


def _enabled(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def main() -> int:
    try:
        evidence = build_update_dry_run_evidence(
            write_tools_enabled=_enabled("WRITE_TOOLS_ENABLED", "false"),
            dry_run_default=_enabled("DRY_RUN_DEFAULT", "true"),
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "evidence_type": "http_forward_update_dry_run",
                    "success": False,
                    "status": "error",
                    "error_class": exc.__class__.__name__,
                    "provider_mutation_performed": False,
                    "http_forward_create_authorized": False,
                    "http_forward_update_authorized": False,
                    "http_forward_delete_authorized": False,
                    "broader_overwrite_authorized": False,
                    "write_tools_enabled": _enabled("WRITE_TOOLS_ENABLED", "false"),
                    "dry_run_default": _enabled("DRY_RUN_DEFAULT", "true"),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
