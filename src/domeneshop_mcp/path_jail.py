"""Remote path guard for read-only hosted file access."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class PathGuard:
    allowed_roots: tuple[str, ...]

    @classmethod
    def from_csv(cls, csv_value: str) -> "PathGuard":
        roots = tuple(_normalize_root(part.strip()) for part in csv_value.split(",") if part.strip())
        if not roots:
            roots = ("/www",)
        return cls(allowed_roots=roots)

    def normalize(self, requested_path: str) -> str:
        if not requested_path or not requested_path.startswith("/"):
            raise ValueError("Remote path must be absolute.")

        path = PurePosixPath(requested_path)
        if ".." in path.parts:
            raise ValueError("Parent traversal is not allowed.")

        normalized = str(path)
        if normalized != "/" and normalized.endswith("/"):
            normalized = normalized.rstrip("/")

        if not self.is_allowed(normalized):
            raise ValueError("Remote path is outside allowed roots.")
        return normalized

    def is_allowed(self, normalized_path: str) -> bool:
        return any(
            normalized_path == root or normalized_path.startswith(root + "/")
            for root in self.allowed_roots
        )


def _normalize_root(root: str) -> str:
    if not root.startswith("/"):
        root = "/" + root
    normalized = str(PurePosixPath(root))
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


def is_text_extension(path: str, allowed_extensions: set[str]) -> bool:
    suffix = PurePosixPath(path).suffix.lower()
    return suffix in allowed_extensions
