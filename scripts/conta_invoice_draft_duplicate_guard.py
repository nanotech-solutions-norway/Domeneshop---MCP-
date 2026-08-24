"""Pure helpers for fail-closed invoice-draft duplicate classification."""
from __future__ import annotations

from typing import Any


class DuplicateGuardError(RuntimeError):
    pass


def extract_draft_entries(body: Any, expected_count: int) -> list[dict[str, Any]]:
    entries: Any = body if isinstance(body, list) else None
    if isinstance(body, dict):
        for key in ("hits", "items", "content", "data", "results", "invoiceDrafts"):
            if isinstance(body.get(key), list):
                entries = body[key]
                break
    if expected_count == 0 and entries is None:
        return []
    if not isinstance(entries, list):
        raise DuplicateGuardError("invoice_draft_entries_missing")
    if len(entries) != expected_count:
        raise DuplicateGuardError("invoice_draft_entries_incomplete")
    if not all(isinstance(entry, dict) for entry in entries):
        raise DuplicateGuardError("invoice_draft_entry_invalid")
    return entries


def extract_draft_identifier(entry: dict[str, Any]) -> str:
    for key in ("id", "invoiceDraftId", "invoice_draft_id"):
        value = entry.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    raise DuplicateGuardError("invoice_draft_identifier_missing")


def detail_contains_line_description(detail: Any, marker: str) -> bool:
    collections: list[list[Any]] = []

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("invoiceDraftLines", "lines"):
                    if not isinstance(value, list):
                        raise DuplicateGuardError("invoice_draft_lines_invalid")
                    collections.append(value)
                else:
                    collect(value)
        elif isinstance(node, list):
            for child in node:
                collect(child)

    collect(detail)
    if not collections:
        raise DuplicateGuardError("invoice_draft_lines_missing")
    descriptions: list[str] = []
    for lines in collections:
        for line in lines:
            if not isinstance(line, dict):
                raise DuplicateGuardError("invoice_draft_line_invalid")
            description = line.get("description")
            if not isinstance(description, str):
                raise DuplicateGuardError("invoice_draft_line_description_missing")
            descriptions.append(description)
    return marker in descriptions
