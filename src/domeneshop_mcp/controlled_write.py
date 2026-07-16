"""Shared controlled-write execution pipeline."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Protocol

from .approval_token import ApprovalTokenManager
from .audit_store import AppendOnlyAuditStore
from .idempotency import FileIdempotencyStore
from .write_release import ControlledWriteRelease


class ControlledWriteError(RuntimeError):
    """Raised when a controlled mutation fails policy or execution."""


class MutationAdapter(Protocol):
    def pre_read(self, target: str) -> dict[str, Any] | None: ...
    def execute(self, action: str, target: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def read_back(self, target: str, result: dict[str, Any]) -> dict[str, Any] | None: ...
    def rollback(self, action: str, target: str, before: dict[str, Any] | None, result: dict[str, Any] | None) -> dict[str, Any] | None: ...


def canonical_payload_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ControlledWriteRequest:
    action: str
    target: str
    payload: dict[str, Any]
    operator: str
    approval_token: str
    idempotency_key: str
    backup_reference: str | None = None
    preflight_reference: str | None = None


class ControlledWriteExecutor:
    def __init__(
        self,
        release: ControlledWriteRelease,
        approval_manager: ApprovalTokenManager,
        idempotency_store: FileIdempotencyStore,
        audit_store: AppendOnlyAuditStore,
    ) -> None:
        self.release = release
        self.approval_manager = approval_manager
        self.idempotency_store = idempotency_store
        self.audit_store = audit_store

    def preview(self, action: str, target: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = self.release.allows(action, target)
        return {
            "release_id": self.release.release_id,
            "environment": self.release.environment,
            "action": action,
            "target": target,
            "payload_sha256": canonical_payload_sha256(payload),
            "allowed_by_manifest": allowed,
            "live_execution_enabled": self.release.live_execution_enabled,
            "requires": {
                "approval_token": self.release.require_approval_token,
                "idempotency": self.release.require_idempotency,
                "audit": self.release.require_audit,
                "readback": self.release.require_readback,
            },
        }

    def execute(self, request: ControlledWriteRequest, adapter: MutationAdapter) -> dict[str, Any]:
        payload_hash = canonical_payload_sha256(request.payload)
        if not self.release.live_execution_enabled:
            raise ControlledWriteError("Live execution is disabled by the controlled-write release manifest")
        if not self.release.allows(request.action, request.target):
            raise ControlledWriteError("Mutation is outside the active release allowlist")
        if not request.preflight_reference:
            raise ControlledWriteError("A preflight reference is required")
        if request.action.startswith(("sftp_", "dns_delete", "forward_delete")) and not request.backup_reference:
            raise ControlledWriteError("A backup or recovery reference is required for this mutation")

        existing = self.idempotency_store.get(request.idempotency_key)
        if existing is not None:
            if existing.payload_sha256 != payload_hash:
                raise ControlledWriteError("Idempotency key conflicts with a different payload")
            if existing.status == "completed":
                return {"replayed": True, "result": existing.result}
            raise ControlledWriteError("An operation with this idempotency key is already in progress")

        if self.release.require_approval_token:
            claims = self.approval_manager.verify_and_consume(
                request.approval_token,
                action=request.action,
                target=request.target,
                payload_sha256=payload_hash,
                operator=request.operator,
            )
        else:
            claims = None

        self.idempotency_store.reserve(request.idempotency_key, payload_hash)

        before: dict[str, Any] | None = None
        result: dict[str, Any] | None = None
        try:
            before = adapter.pre_read(request.target)
            result = adapter.execute(request.action, request.target, request.payload)
            after = adapter.read_back(request.target, result)
            event = self.audit_store.append(
                "controlled_write_completed",
                request.operator,
                request.target,
                {
                    "release_id": self.release.release_id,
                    "action": request.action,
                    "payload_sha256": payload_hash,
                    "approval_id": claims.approval_id if claims else None,
                    "preflight_reference": request.preflight_reference,
                    "backup_reference": request.backup_reference,
                    "before": before,
                    "result": result,
                    "after": after,
                },
            )
            completed = self.idempotency_store.complete(
                request.idempotency_key,
                {"provider_result": result, "readback": after, "audit_hash": event["event_hash"]},
            )
            return {"replayed": False, "result": completed.result}
        except Exception as exc:
            rollback = None
            try:
                rollback = adapter.rollback(request.action, request.target, before, result)
            except Exception:
                rollback = {"status": "rollback_failed"}
            self.audit_store.append(
                "controlled_write_failed",
                request.operator,
                request.target,
                {
                    "release_id": self.release.release_id,
                    "action": request.action,
                    "payload_sha256": payload_hash,
                    "error_class": exc.__class__.__name__,
                    "rollback": rollback,
                },
            )
            raise ControlledWriteError("Controlled mutation failed; audit and rollback handling were invoked") from exc
