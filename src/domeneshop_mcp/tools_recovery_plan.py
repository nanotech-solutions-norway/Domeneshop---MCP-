"""Recovery planning handlers for Phase 6."""

from __future__ import annotations

from .deploy_plan import compare_manifest, remote_entries_from_metadata, LocalManifestEntry
from .envelope import ToolEnvelope, error, ok
from .recovery_plan import build_backup_evidence_manifest, build_restore_preview, BackupEvidenceManifest


def build_backup_manifest_from_plan(plan_payload: dict, remote_metadata: list[dict], backup_root: str, allowed_roots: list[str]) -> ToolEnvelope:
    try:
        remote_entries = remote_entries_from_metadata(remote_metadata)
        plan_data = plan_payload.get("plan", plan_payload)
        plan = _plan_from_payload(plan_data)
        manifest = build_backup_evidence_manifest(plan, remote_entries, backup_root=backup_root, allowed_roots=tuple(allowed_roots))
        return ok({"summary": manifest.summary(), "manifest": manifest.__dict__}, mode="recovery_plan_only")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="recovery_plan_only")
    except Exception:
        return error("provider_error", "Backup evidence planning failed.", mode="recovery_plan_only")


def build_restore_preview_from_manifest(manifest_payload: dict, allowed_roots: list[str]) -> ToolEnvelope:
    try:
        manifest_data = manifest_payload.get("manifest", manifest_payload)
        manifest = BackupEvidenceManifest(
            mode=str(manifest_data["mode"]),
            created_utc=str(manifest_data["created_utc"]),
            backup_root=str(manifest_data["backup_root"]),
            target_root=str(manifest_data["target_root"]),
            entries=list(manifest_data.get("entries", [])),
        )
        preview = build_restore_preview(manifest, allowed_roots=tuple(allowed_roots))
        return ok({"summary": preview.summary(), "preview": preview.__dict__}, mode="recovery_plan_only")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="recovery_plan_only")
    except Exception:
        return error("provider_error", "Restore preview planning failed.", mode="recovery_plan_only")


def _plan_from_payload(data: dict):
    from .deploy_plan import DeploymentPlan
    return DeploymentPlan(
        mode=str(data["mode"]),
        source_root=str(data["source_root"]),
        target_root=str(data["target_root"]),
        new_files=list(data.get("new_files", [])),
        changed_files=list(data.get("changed_files", [])),
        unchanged_files=list(data.get("unchanged_files", [])),
        blocked_files=list(data.get("blocked_files", [])),
    )
