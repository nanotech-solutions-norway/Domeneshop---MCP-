"""Audit event model for governed operations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor: str
    target: str
    decision_summary: dict[str, Any]
    created_utc: str
    event_hash: str


def build_audit_event(event_type: str, actor: str, target: str, decision_summary: dict[str, Any]) -> AuditEvent:
    created_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "event_type": event_type,
        "actor": actor,
        "target": target,
        "decision_summary": decision_summary,
        "created_utc": created_utc,
    }
    event_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return AuditEvent(
        event_type=event_type,
        actor=actor,
        target=target,
        decision_summary=decision_summary,
        created_utc=created_utc,
        event_hash=event_hash,
    )
