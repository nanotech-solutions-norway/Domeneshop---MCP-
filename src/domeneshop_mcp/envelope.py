"""Normalized response envelopes for MCP tool output."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class ToolEnvelope(TypedDict, total=False):
    success: bool
    status: Literal["ok", "error"]
    mode: str
    write_paused: bool
    data: Any
    warnings: list[str]
    error_class: str
    message: str


def ok(data: Any, *, mode: str = "read_only", warnings: list[str] | None = None) -> ToolEnvelope:
    return {
        "success": True,
        "status": "ok",
        "mode": mode,
        "write_paused": True,
        "data": data,
        "warnings": warnings or [],
    }


def error(error_class: str, message: str, *, mode: str = "read_only") -> ToolEnvelope:
    return {
        "success": False,
        "status": "error",
        "mode": mode,
        "write_paused": True,
        "error_class": error_class,
        "message": message,
        "warnings": [],
    }
