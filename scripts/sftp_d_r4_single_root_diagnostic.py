"""Strict GET/read-only diagnostic for a dedicated D-R4 sandbox webhotel account.

This helper assumes the operator has loaded credentials for the newly provisioned
atlas-mcp-sandbox.no webhotel. It inspects only /www, requires exactly one entry,
and reports only bounded metadata for that sole entry. If the entry is a directory,
it may inspect exactly one level beneath it and reports only counts plus bounded
name/type summaries. It never mutates SFTP state and never selects a write target.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import PurePosixPath

from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig

SEARCH_ROOT = "/www"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _basename(path: str) -> str:
    return PurePosixPath(path).name


def _bounded_entry_summary(entry: dict[str, object]) -> dict[str, object]:
    path = str(entry.get("path", ""))
    name = _basename(path)
    mode = int(entry.get("mode", 0))
    return {
        "name": name,
        "path_sha256": _sha(path),
        "is_directory": stat.S_ISDIR(mode),
        "is_regular_file": stat.S_ISREG(mode),
    }


def main() -> int:
    client = None
    try:
        if os.environ.get("WRITE_TOOLS_ENABLED", "false").strip().lower() != "false":
            raise RuntimeError("write_tools_must_remain_disabled")
        if os.environ.get("DRY_RUN_DEFAULT", "true").strip().lower() != "true":
            raise RuntimeError("dry_run_default_must_remain_enabled")

        config = SftpReadConfig.from_env()
        if not config.has_auth:
            raise RuntimeError("sftp_credentials_missing")
        if SEARCH_ROOT not in config.allowed_roots:
            raise RuntimeError("www_root_not_allowed")

        client = SftpReadClient(config)
        root_entries = client.list_files(SEARCH_ROOT)
        if not isinstance(root_entries, list):
            raise RuntimeError("www_listing_unexpected_shape")
        if len(root_entries) != 1:
            raise RuntimeError(f"expected_exactly_one_root_entry_got_{len(root_entries)}")

        sole = _bounded_entry_summary(root_entries[0])
        child_summaries: list[dict[str, object]] = []
        child_count = None

        if sole["is_directory"]:
            sole_path = str(root_entries[0].get("path", ""))
            children = client.list_files(sole_path)
            if not isinstance(children, list):
                raise RuntimeError("sole_directory_listing_unexpected_shape")
            child_count = len(children)
            # Dedicated sandbox account only; still cap emitted metadata to avoid broad disclosure.
            child_summaries = [_bounded_entry_summary(entry) for entry in children[:10]]

        print(json.dumps({
            "success": True,
            "status": "single_root_diagnostic_ok",
            "search_root": SEARCH_ROOT,
            "search_root_sha256": _sha(SEARCH_ROOT),
            "root_entry_count": 1,
            "sole_root_entry": sole,
            "sole_root_directory_child_count": child_count,
            "sole_root_directory_child_summaries": child_summaries,
            "child_summary_cap": 10,
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "sftp_create_authorized": False,
            "sftp_overwrite_authorized": False,
            "sftp_delete_authorized": False,
            "write_target_selected": False,
        }, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "status": "hold_for_review",
            "bounded_error_class": str(exc),
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "sftp_create_authorized": False,
            "sftp_overwrite_authorized": False,
            "sftp_delete_authorized": False,
            "write_target_selected": False,
        }, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
