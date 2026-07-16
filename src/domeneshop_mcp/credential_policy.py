"""Credential placeholder detection shared by API and SFTP configuration.

The project uses redacted runtime templates during review. Those markers must
never be treated as credentials and sent to an external provider.
"""
from __future__ import annotations

import re

_EXACT_PLACEHOLDERS = {
    "",
    "__SET_IN_SECRET_STORE__",
    "CHANGE_ME",
    "CHANGEME",
    "PLACEHOLDER",
    "INSERT_TOKEN_HERE",
    "INSERT_SECRET_HERE",
    "INSERT_PASSWORD_HERE",
    "INSERT_USERNAME_HERE",
    "I'VE_ENTERED_THE_TOKEN_HERE",
    "I'VE_ENTERED_THE_SECRET_HERE",
    "I'VE_ENTERED_THE_PASSWORD_HERE",
    "I'VE_ENTERED_THE_USERNAME_HERE",
    "TOKEN_HERE",
    "SECRET_HERE",
    "PASSWORD_HERE",
    "USERNAME_HERE",
}

_TEMPLATE_WRAPPERS = (
    ("${", "}"),
    ("<", ">"),
    ("{{", "}}"),
)


def _canonical(value: str | None) -> str:
    if value is None:
        return ""
    normalized = str(value).strip().replace("’", "'")
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    return normalized.upper()


def is_placeholder_value(value: str | None) -> bool:
    """Return True for empty values and known review/template markers.

    Detection is deliberately explicit to avoid rejecting legitimate secrets
    merely because they contain words such as ``token`` or ``secret``.
    """

    raw = "" if value is None else str(value).strip()
    canonical = _canonical(raw)

    if canonical in _EXACT_PLACEHOLDERS:
        return True

    if raw.startswith("__") and raw.endswith("__") and len(raw) > 4:
        return True

    for start, end in _TEMPLATE_WRAPPERS:
        if raw.startswith(start) and raw.endswith(end) and len(raw) > len(start) + len(end):
            return True

    if canonical.startswith("YOUR_") and any(
        marker in canonical for marker in ("TOKEN", "SECRET", "PASSWORD", "USERNAME", "KEY")
    ):
        return True

    if canonical.startswith("INSERT_") and canonical.endswith("_HERE"):
        return True

    if canonical.startswith("I'VE_ENTERED_THE_") and canonical.endswith("_HERE"):
        return True

    return False


def has_runtime_value(value: str | None) -> bool:
    """Return True only when a value is non-empty and not a template marker."""

    return not is_placeholder_value(value)
