"""Dry-run planning tool handlers for Phase 5."""

from __future__ import annotations

from pathlib import Path

from .deploy_plan import build_local_manifest, compare_manifest, remote_entries_from_metadata
from .envelope import ToolEnvelope, error, ok


def build_manifest(source_root: str) -> ToolEnvelope:
    try:
        entries = build_local_manifest(Path(source_root))
        return ok([entry.__dict__ for entry in entries], mode="plan_only")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="plan_only")
    except Exception:
        return error("provider_error", "Local manifest generation failed.", mode="plan_only")


def compare_plan(source_root: str, target_root: str, allowed_roots: tuple[str, ...], remote_metadata: list[dict]) -> ToolEnvelope:
    try:
        local_entries = build_local_manifest(Path(source_root))
        remote_entries = remote_entries_from_metadata(remote_metadata)
        plan = compare_manifest(
            local_entries,
            remote_entries,
            target_root=target_root,
            allowed_roots=allowed_roots,
            source_root=source_root,
        )
        return ok({"summary": plan.summary(), "plan": plan.__dict__}, mode="plan_only")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="plan_only")
    except Exception:
        return error("provider_error", "Plan comparison failed.", mode="plan_only")
