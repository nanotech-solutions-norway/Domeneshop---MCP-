"""Data-minimizing summaries for operator-facing runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def summarize_collection_result(result: Mapping[str, Any], *, evidence_type: str) -> dict[str, Any]:
    """Return evidence metadata without copying provider or remote-file payloads."""
    data = result.get("data")
    if isinstance(data, (list, tuple, set, frozenset)):
        item_count = len(data)
    elif data is None:
        item_count = 0
    else:
        item_count = 1

    summary: dict[str, Any] = {
        "evidence_type": evidence_type,
        "success": result.get("success") is True,
        "status": result.get("status", "error"),
        "mode": result.get("mode", "read_only"),
        "write_paused": result.get("write_paused") is True,
        "item_count": item_count,
        "warnings_count": len(result.get("warnings", [])),
        "payload_included": False,
    }
    if not summary["success"]:
        summary["error_class"] = result.get("error_class", "unknown_error")
    return summary
