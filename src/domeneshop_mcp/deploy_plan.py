"""Dry-run deployment planning for Phase 5.

This module builds local manifests and compares them with remote metadata.
It never writes to a remote host.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .path_jail import PathGuard


SKIP_DIRS = {".git", ".github", "__pycache__", ".pytest_cache", ".venv", "venv", "audit", "backups"}


@dataclass(frozen=True)
class LocalManifestEntry:
    relative_path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class RemoteManifestEntry:
    remote_path: str
    size: int
    sha256: str | None = None


@dataclass(frozen=True)
class DeploymentPlan:
    mode: str
    source_root: str
    target_root: str
    new_files: list[dict[str, Any]]
    changed_files: list[dict[str, Any]]
    unchanged_files: list[dict[str, Any]]
    blocked_files: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source_root": self.source_root,
            "target_root": self.target_root,
            "new_count": len(self.new_files),
            "changed_count": len(self.changed_files),
            "unchanged_count": len(self.unchanged_files),
            "blocked_count": len(self.blocked_files),
            "will_write": False,
        }


def build_local_manifest(source_root: str | Path) -> list[LocalManifestEntry]:
    root = Path(source_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("Source root must be an existing directory.")

    entries: list[LocalManifestEntry] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        relative_path = "/".join(rel_parts)
        raw = path.read_bytes()
        entries.append(
            LocalManifestEntry(
                relative_path=relative_path,
                size=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    return entries


def compare_manifest(
    local_entries: list[LocalManifestEntry],
    remote_entries: dict[str, RemoteManifestEntry],
    *,
    target_root: str,
    allowed_roots: tuple[str, ...],
    source_root: str = ".",
) -> DeploymentPlan:
    guard = PathGuard(allowed_roots)
    target_root = guard.normalize(target_root)

    new_files: list[dict[str, Any]] = []
    changed_files: list[dict[str, Any]] = []
    unchanged_files: list[dict[str, Any]] = []
    blocked_files: list[dict[str, Any]] = []

    for entry in local_entries:
        remote_path = str(PurePosixPath(target_root) / entry.relative_path)
        try:
            guard.normalize(remote_path)
        except ValueError as exc:
            blocked_files.append({"relative_path": entry.relative_path, "remote_path": remote_path, "reason": str(exc)})
            continue

        remote = remote_entries.get(remote_path)
        local_info = {"relative_path": entry.relative_path, "remote_path": remote_path, "size": entry.size, "sha256": entry.sha256}
        if remote is None:
            new_files.append(local_info)
        elif remote.sha256 and remote.sha256 == entry.sha256:
            unchanged_files.append(local_info)
        elif remote.size == entry.size and remote.sha256 is None:
            changed_files.append({**local_info, "reason": "remote_hash_missing_size_matches"})
        else:
            changed_files.append({**local_info, "remote_size": remote.size, "remote_sha256": remote.sha256})

    return DeploymentPlan(
        mode="dry_run",
        source_root=str(source_root),
        target_root=target_root,
        new_files=new_files,
        changed_files=changed_files,
        unchanged_files=unchanged_files,
        blocked_files=blocked_files,
    )


def remote_entries_from_metadata(items: list[dict[str, Any]]) -> dict[str, RemoteManifestEntry]:
    result: dict[str, RemoteManifestEntry] = {}
    for item in items:
        path = str(item.get("path", ""))
        if not path:
            continue
        result[path] = RemoteManifestEntry(
            remote_path=path,
            size=int(item.get("size", 0)),
            sha256=item.get("sha256"),
        )
    return result
