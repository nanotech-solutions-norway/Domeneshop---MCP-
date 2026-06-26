"""HTTP health tool handlers for Phase 4."""

from __future__ import annotations

from .envelope import ToolEnvelope, error, ok
from .health import HealthDiagnostics


def _controlled(operation) -> ToolEnvelope:
    try:
        return ok(operation(), mode="http_diagnostics")
    except ValueError as exc:
        return error("validation_failed", str(exc), mode="http_diagnostics")
    except Exception:
        return error("provider_error", "HTTP diagnostic operation failed.", mode="http_diagnostics")


def http_check_endpoint(client: HealthDiagnostics, url: str) -> ToolEnvelope:
    return _controlled(lambda: client.check_endpoint(url))


def http_check_json_health(client: HealthDiagnostics, url: str) -> ToolEnvelope:
    return _controlled(lambda: client.check_json_health(url))


def http_check_tls(client: HealthDiagnostics, url: str) -> ToolEnvelope:
    return _controlled(lambda: client.check_tls(url))
