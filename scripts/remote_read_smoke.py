"""Manual hosted-file read smoke check for Phase 3."""

from __future__ import annotations

import json

from domeneshop_mcp.evidence_summary import summarize_collection_result
from domeneshop_mcp.sftp_read import SftpReadClient, SftpReadConfig
from domeneshop_mcp.tools_sftp_read import sftp_list_allowed_roots, sftp_list_files


def main() -> int:
    config = SftpReadConfig.from_env()
    client = SftpReadClient(config)
    try:
        roots_result = sftp_list_allowed_roots(client)
        print(
            json.dumps(
                summarize_collection_result(roots_result, evidence_type="sftp_allowed_roots"),
                indent=2,
                ensure_ascii=False,
            )
        )
        result = sftp_list_files(client, config.remote_root)
        print(
            json.dumps(
                summarize_collection_result(result, evidence_type="sftp_directory_list"),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if result.get("success") else 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
