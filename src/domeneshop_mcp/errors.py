"""Controlled error mapping for Domeneshop API responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DomeneshopApiError(Exception):
    error_class: str
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        code = f" status={self.status_code}" if self.status_code is not None else ""
        return f"{self.error_class}:{code} {self.message}"


def classify_status(status_code: int) -> str:
    if status_code in {401, 403}:
        return "unauthorized"
    if status_code == 404:
        return "not_found"
    if status_code == 400:
        return "validation_failed"
    if status_code == 409:
        return "conflict"
    if status_code == 412:
        return "precondition_failed"
    if status_code >= 500:
        return "provider_error"
    return "unexpected_status"
