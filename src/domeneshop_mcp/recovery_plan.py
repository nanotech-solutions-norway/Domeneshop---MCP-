"""Backup and rollback planning for Phase 6.

This module creates evidence manifests and restore previews only.
It does not upload, overwrite, delete, or restore remote files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from .deploy_plan import DeploymentPlan, RemoteManifestEntry
from .path_jail import PathGuard


@dataclass(frozen=True)
class BackupEvidenceEntry:
    remote_path: str
    backup_path: str
    size: int
    remote_sha256: str | None
    reason: str


@dataclass(frozen=True)
class BackupEvidenceManifest:
    mode: str
    created_utc: str
    backup_root: str
    target_root: str
    entries: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "backup_root": self.backup_root,
            "target_root": self.target_root,
            "entry_count": len(self.entries),
            "will_write": False,
            "live_restore": False,
        }


@dataclass(frozen=True)
class RestorePreview:
    mode: str
    backup_root: str
    restore_targets: list[dict[str, Any]]
    blocked_targets: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "restore_target_count": len(self.restore_targets),
            "blocked_target_count": len(self.blocked_targets),
            "will_write": False,
            "live_restore": False,
        }


def build_backup_evidence_manifest(
    plan: DeploymentPlan,
    remote_entries: dict[str, RemoteManifestEntry],
    *,
    backup_root: str,
    allowed_roots: tuple[str, ...],
    timestamp: str | None = None,
) -> BackupEvidenceManifest:
    guard = PathGuard(allowed_roots)
    backup_root = guard.normalize(backup_root)
    created_utc = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    entries: list[dict[str, Any]] = []
    candidates = list(plan.changed_files)
    for item in candidates:
        remote_path = guard.normalize(str(item["remote_path"]))
        remote = remote_entries.get(remote_path)
        if remote is None:
            continue
        rel = _relative_to_root(remote_path, plan.target_root)
        backup_path = guard.normalize(str(PurePosixPath(backup_root) / rel))
        entry = BackupEvidenceEntry(
            remote_path=remote_path,
            backup_path=backup_path,
            size=remote.size,
            remote_sha256=remote.sha256,
            reason="changed_file_requires_backup_before_future_write",
        )
        entries.append(entry.__dict__)

    return BackupEvidenceManifest(
        mode="backup_evidence_dry_run",
        created_utc=created_utc,
        backup_root=backup_root,
        target_root=plan.target_root,
        entries=entries,
    )


def build_restore_preview(
    manifest: BackupEvidenceManifest,
    *,
    allowed_roots: tuple[str, ...],
) -> RestorePreview:
    guard = PathGuard(allowed_roots)
    restore_targets: list[dict[str, Any]] = []
    blocked_targets: list[dict[str, Any]] = []

    for item in manifest.entries:
        remote_path = str(item.get("remote_path", ""))
        backup_path = str(item.get("backup_path", ""))
        try:
            guard.normalize(remote_path)
            guard.normalize(backup_path)
        except ValueError as exc:
            blocked_targets.append({"remote_path": remote_path, "backup_path": backup_path, "reason": str(exc)})
            continue
        restore_targets.append(
            {
                "from_backup_path": backup_path,
                "to_remote_path": remote_path,
                "size": int(item.get("size", 0)),
                "remote_sha256": item.get("remote_sha256"),
                "will_write": False,
            }
        )

    return RestorePreview(
        mode="restore_preview_only",
        backup_root=manifest.backup_root,
        restore_targets=restore_targets,
        blocked_targets=blocked_targets,
    )


def _relative_to_root(remote_path: str, target_root: str) -> str:
    prefix = target_root.rstrip("/") + "/"
    if remote_path.startswith(prefix):
        return remote_path[len(prefix):]
    return remote_path.lstrip("/")
