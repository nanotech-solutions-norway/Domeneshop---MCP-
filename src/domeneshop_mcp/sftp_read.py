"""Read-only SFTP client for hosted file inspection."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Iterable

from .path_jail import PathGuard, is_text_extension


@dataclass(frozen=True)
class SftpReadConfig:
    host: str = "sftp.domeneshop.no"
    port: int = 22
    user: str = ""
    access_value: str = ""
    remote_root: str = "/www"
    allowed_roots: tuple[str, ...] = ("/www",)
    max_read_file_bytes: int = 262144
    allowed_text_extensions: frozenset[str] = frozenset(
        {".txt", ".md", ".json", ".csv", ".html", ".htm", ".css", ".js", ".php", ".xml", ".yml", ".yaml", ".log"}
    )

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "SftpReadConfig":
        source = os.environ if env is None else env
        roots = tuple(x.strip() for x in source.get("ALLOWED_REMOTE_ROOTS", "/www").split(",") if x.strip())
        extensions = frozenset(
            x.strip().lower() for x in source.get("ALLOWED_TEXT_EXTENSIONS", ".txt,.md,.json,.csv,.html,.htm,.css,.js,.php").split(",") if x.strip()
        )
        return cls(
            host=source.get("DOMENESHOP_SFTP_HOST", "sftp.domeneshop.no"),
            port=int(source.get("DOMENESHOP_SFTP_PORT", "22")),
            user=source.get("DS_SFTP_USER", ""),
            access_value=source.get("DS_SFTP_VALUE", ""),
            remote_root=source.get("DOMENESHOP_REMOTE_ROOT", "/www"),
            allowed_roots=roots or ("/www",),
            max_read_file_bytes=int(source.get("MAX_READ_FILE_BYTES", "262144")),
            allowed_text_extensions=extensions,
        )

    @property
    def has_auth(self) -> bool:
        return self.user not in {"", "__SET_IN_SECRET_STORE__"} and self.access_value not in {"", "__SET_IN_SECRET_STORE__"}


class SftpReadClient:
    def __init__(self, config: SftpReadConfig, sftp: Any | None = None) -> None:
        self.config = config
        self.guard = PathGuard(config.allowed_roots)
        self._sftp = sftp
        self._transport = None

    def connect(self) -> None:
        if self._sftp is not None:
            return
        if not self.config.has_auth:
            raise ValueError("SFTP access values are missing or placeholders.")
        import paramiko

        transport = paramiko.Transport((self.config.host, self.config.port))
        transport.connect(username=self.config.user, password=self.config.access_value)
        self._transport = transport
        self._sftp = paramiko.SFTPClient.from_transport(transport)

    def close(self) -> None:
        if self._sftp is not None and hasattr(self._sftp, "close"):
            self._sftp.close()
        if self._transport is not None and hasattr(self._transport, "close"):
            self._transport.close()

    def list_allowed_roots(self) -> list[str]:
        return list(self.config.allowed_roots)

    def list_files(self, remote_path: str) -> list[dict[str, Any]]:
        self.connect()
        path = self.guard.normalize(remote_path)
        items = self._sftp.listdir_attr(path)
        return [_metadata(path, item) for item in items]

    def get_file_metadata(self, remote_path: str) -> dict[str, Any]:
        self.connect()
        path = self.guard.normalize(remote_path)
        stat = self._sftp.stat(path)
        return _stat_metadata(path, stat)

    def read_text_file(self, remote_path: str) -> dict[str, Any]:
        self.connect()
        path = self.guard.normalize(remote_path)
        if not is_text_extension(path, set(self.config.allowed_text_extensions)):
            raise ValueError("File extension is not approved for text read.")
        stat = self._sftp.stat(path)
        size = int(getattr(stat, "st_size", 0))
        if size > self.config.max_read_file_bytes:
            raise ValueError("File exceeds configured read size limit.")
        with self._sftp.open(path, "rb") as handle:
            raw = handle.read()
        digest = hashlib.sha256(raw).hexdigest()
        return {
            "path": path,
            "size": len(raw),
            "sha256": digest,
            "content": raw.decode("utf-8", errors="replace"),
        }


def _metadata(parent_path: str, item: Any) -> dict[str, Any]:
    filename = getattr(item, "filename", "")
    path = str(PurePosixPath(parent_path) / filename)
    return _stat_metadata(path, item)


def _stat_metadata(path: str, stat: Any) -> dict[str, Any]:
    mtime = getattr(stat, "st_mtime", None)
    return {
        "path": path,
        "size": int(getattr(stat, "st_size", 0)),
        "mode": int(getattr(stat, "st_mode", 0)),
        "modified_utc": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat() if mtime else None,
    }
