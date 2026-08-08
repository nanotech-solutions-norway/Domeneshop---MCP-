"""Append-only, redacted audit log with a SHA-256 integrity chain."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SENSITIVE_KEYS = {
    "authorization",
    "password",
    "secret",
    "token",
    "api_key",
    "private_key",
    "credential",
    "access_value",
    "auth_value",
    "access_token",
    "refresh_token",
    "client_secret",
}


def _normalized_key(value: Any) -> str:
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", str(value))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _is_sensitive_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    if normalized in _SENSITIVE_KEYS:
        return True
    return any(normalized.endswith(f"_{suffix}") for suffix in ("password", "secret", "token", "api_key", "private_key"))


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _is_sensitive_key(key) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


class AppendOnlyAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @staticmethod
    def _hash(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def append(self, event_type: str, actor: str, target: str, details: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            previous_hash = self._last_hash()
            event = {
                "event_type": event_type,
                "actor": actor,
                "target": target,
                "details": redact(details),
                "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "previous_hash": previous_hash,
            }
            event["event_hash"] = self._hash(event)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
            return event

    def _last_hash(self) -> str | None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        last = ""
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = line
        return json.loads(last)["event_hash"] if last else None

    def verify_chain(self) -> bool:
        if not self.path.exists():
            return True
        previous_hash: str | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                stored_hash = event.pop("event_hash", None)
                if event.get("previous_hash") != previous_hash:
                    return False
                calculated = self._hash(event)
                if stored_hash != calculated:
                    return False
                previous_hash = stored_hash
        return True
