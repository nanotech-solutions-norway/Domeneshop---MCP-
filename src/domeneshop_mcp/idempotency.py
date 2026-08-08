"""File-backed idempotency ledger for controlled writes."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class IdempotencyError(ValueError):
    """Raised for conflicting or in-progress idempotency keys."""


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    payload_sha256: str
    status: str
    created_utc: str
    updated_utc: str
    result: dict[str, Any] | None = None


class FileIdempotencyStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.directory / f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}.json"

    def get(self, key: str) -> IdempotencyRecord | None:
        path = self._path(key)
        if not path.exists():
            return None
        return IdempotencyRecord(**json.loads(path.read_text(encoding="utf-8")))

    def reserve(self, key: str, payload_sha256: str) -> IdempotencyRecord:
        if not key.strip():
            raise IdempotencyError("Idempotency key is required")
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        record = IdempotencyRecord(key, payload_sha256, "reserved", now, now)
        path = self._path(key)
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(asdict(record), handle, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            return record
        except FileExistsError:
            existing = self.get(key)
            if existing is None:
                raise IdempotencyError("Idempotency ledger could not be read")
            if existing.payload_sha256 != payload_sha256:
                raise IdempotencyError("Idempotency key conflicts with a different payload")
            if existing.status == "completed":
                return existing
            raise IdempotencyError("An operation with this idempotency key is already in progress")

    def complete(self, key: str, result: dict[str, Any]) -> IdempotencyRecord:
        existing = self.get(key)
        if existing is None:
            raise IdempotencyError("Idempotency key was not reserved")
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        completed = IdempotencyRecord(
            key=existing.key,
            payload_sha256=existing.payload_sha256,
            status="completed",
            created_utc=existing.created_utc,
            updated_utc=now,
            result=result,
        )
        path = self._path(key)
        temp = path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(asdict(completed), handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        return completed
