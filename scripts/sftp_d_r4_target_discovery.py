"""Bounded GET/read-only discovery for the D-R4 isolated SFTP target.

This helper never selects or mutates a remote path. It inspects only /www and at
most one directory level beneath candidate names related to the known isolated
sandbox. Output is sanitized and does not include general remote listings.
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
DOMAIN_NAME = "atlas-mcp-sandbox.no"
DOMAIN_STEM = "atlas-mcp-sandbox"
PILOT_FILE = ".mcp-d-r4-validation.txt"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _basename(path: str) -> str:
    return PurePosixPath(path).name


def _is_candidate_name(name: str) -> bool:
    normalized = name.strip().lower()
    return normalized == DOMAIN_NAME or DOMAIN_STEM in normalized or ("atlas" in normalized and "sandbox" in normalized)


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

        top_candidates: list[dict[str, object]] = []
        exact_top_matches = 0
        for entry in root_entries:
            path = str(entry.get("path", ""))
            name = _basename(path)
            if not _is_candidate_name(name):
                continue
            mode = int(entry.get("mode", 0))
            is_dir = stat.S_ISDIR(mode)
            if name.lower() == DOMAIN_NAME:
                exact_top_matches += 1
            top_candidates.append({
                "name": name,
                "path_sha256": _sha(path),
                "is_directory": is_dir,
                "exact_domain_name": name.lower() == DOMAIN_NAME,
            })

        nested_candidates: list[dict[str, object]] = []
        # Descend only into already matched candidate directories; never scan arbitrary /www subtrees.
        for candidate in top_candidates:
            if not candidate["is_directory"]:
                continue
            candidate_name = str(candidate["name"])
            candidate_path = str(PurePosixPath(SEARCH_ROOT) / candidate_name)
            try:
                children = client.list_files(candidate_path)
            except Exception:
                continue
            for child in children:
                child_path = str(child.get("path", ""))
                child_name = _basename(child_path)
                if not _is_candidate_name(child_name):
                    continue
                nested_candidates.append({
                    "parent_name": candidate_name,
                    "name": child_name,
                    "path_sha256": _sha(child_path),
                    "is_directory": stat.S_ISDIR(int(child.get("mode", 0))),
                    "exact_domain_name": child_name.lower() == DOMAIN_NAME,
                })

        exact_nested_matches = sum(1 for item in nested_candidates if item["exact_domain_name"] and item["is_directory"])
        exact_directory_matches = sum(1 for item in top_candidates if item["exact_domain_name"] and item["is_directory"]) + exact_nested_matches

        status = "unique_exact_candidate_found" if exact_directory_matches == 1 else ("no_exact_candidate_found" if exact_directory_matches == 0 else "ambiguous_exact_candidates")
        success = exact_directory_matches == 1

        print(json.dumps({
            "success": success,
            "status": status,
            "search_root_sha256": _sha(SEARCH_ROOT),
            "root_entry_count": len(root_entries),
            "candidate_entry_count": len(top_candidates) + len(nested_candidates),
            "exact_directory_match_count": exact_directory_matches,
            "top_candidate_summaries": top_candidates,
            "nested_candidate_summaries": nested_candidates,
            "pilot_filename_sha256": _sha(PILOT_FILE),
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "sftp_create_authorized": False,
            "sftp_overwrite_authorized": False,
            "sftp_delete_authorized": False,
            "general_remote_listing_included": False,
        }, sort_keys=True))
        return 0 if success else 2
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "status": "hold_for_review",
            "bounded_error_class": exc.__class__.__name__,
            "provider_mutation_performed": False,
            "write_tools_enabled": False,
            "general_remote_listing_included": False,
        }, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
