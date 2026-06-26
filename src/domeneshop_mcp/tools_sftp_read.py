"""Read-only SFTP tool handlers for Phase 3."""

from __future__ import annotations

from .envelope import ToolEnvelope, error, ok
from .sftp_read import SftpReadClient


def _controlled(operation) -> ToolEnvelope:
    try:
        return ok(operation(), mode="sftp_read_only")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="sftp_read_only")
    except PermissionError:
        return error("unauthorized", "SFTP operation was not authorized.", mode="sftp_read_only")
    except FileNotFoundError:
        return error("not_found", "Remote file or directory was not found.", mode="sftp_read_only")
    except Exception:
        return error("provider_error", "SFTP read operation failed.", mode="sftp_read_only")


def sftp_list_allowed_roots(client: SftpReadClient) -> ToolEnvelope:
    return _controlled(client.list_allowed_roots)


def sftp_list_files(client: SftpReadClient, remote_path: str) -> ToolEnvelope:
    return _controlled(lambda: client.list_files(remote_path))


def sftp_get_file_metadata(client: SftpReadClient, remote_path: str) -> ToolEnvelope:
    return _controlled(lambda: client.get_file_metadata(remote_path))


def sftp_read_text_file(client: SftpReadClient, remote_path: str) -> ToolEnvelope:
    return _controlled(lambda: client.read_text_file(remote_path))
