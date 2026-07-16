"""Controlled-write release-manifest model.

A release manifest is an allowlist, not an authorization by itself. Runtime
execution additionally requires the global write switch and a one-time
operation approval token.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ReleaseManifestError(ValueError):
    """Raised when a controlled-write manifest is invalid."""


@dataclass(frozen=True)
class ControlledWriteRelease:
    release_id: str
    environment: str
    decision: str
    approved_tools: frozenset[str]
    approved_target_prefixes: tuple[str, ...]
    live_execution_enabled: bool
    require_approval_token: bool
    require_idempotency: bool
    require_audit: bool
    require_readback: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ControlledWriteRelease":
        required = {
            "release_id",
            "environment",
            "decision",
            "approved_tools",
            "approved_target_prefixes",
            "live_execution_enabled",
            "controls",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ReleaseManifestError(f"Missing manifest fields: {', '.join(missing)}")

        controls = payload.get("controls")
        if not isinstance(controls, dict):
            raise ReleaseManifestError("controls must be an object")

        approved_tools = frozenset(str(item).strip() for item in payload["approved_tools"] if str(item).strip())
        prefixes = tuple(str(item).strip() for item in payload["approved_target_prefixes"] if str(item).strip())
        if not approved_tools:
            raise ReleaseManifestError("approved_tools must not be empty")
        if not prefixes:
            raise ReleaseManifestError("approved_target_prefixes must not be empty")
        if any(item in {"*", "/", ""} for item in prefixes):
            raise ReleaseManifestError("Broad or wildcard target prefixes are prohibited")

        decision = str(payload["decision"])
        live_enabled = bool(payload["live_execution_enabled"])
        if live_enabled and decision != "APPROVE_CONTROLLED_WRITE_PILOT":
            raise ReleaseManifestError("Live execution requires APPROVE_CONTROLLED_WRITE_PILOT")

        return cls(
            release_id=str(payload["release_id"]),
            environment=str(payload["environment"]),
            decision=decision,
            approved_tools=approved_tools,
            approved_target_prefixes=prefixes,
            live_execution_enabled=live_enabled,
            require_approval_token=bool(controls.get("require_approval_token", True)),
            require_idempotency=bool(controls.get("require_idempotency", True)),
            require_audit=bool(controls.get("require_audit", True)),
            require_readback=bool(controls.get("require_readback", True)),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "ControlledWriteRelease":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ReleaseManifestError("Manifest root must be an object")
        return cls.from_dict(data)

    def allows(self, tool: str, target: str) -> bool:
        return tool in self.approved_tools and any(
            target == prefix or target.startswith(prefix) for prefix in self.approved_target_prefixes
        )
