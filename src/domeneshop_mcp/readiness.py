"""Production readiness preflight for Phase 8."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

from .change_control import ChangeGateConfig
from .config import DomeneshopConfig
from .sftp_read import SftpReadConfig


@dataclass(frozen=True)
class ReadinessDecision:
    mode: str
    ready_for_read_only_runtime: bool
    ready_for_live_change_runtime: bool
    checks: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        failed = [item for item in self.checks if not item["passed"]]
        return {
            "mode": self.mode,
            "ready_for_read_only_runtime": self.ready_for_read_only_runtime,
            "ready_for_live_change_runtime": self.ready_for_live_change_runtime,
            "check_count": len(self.checks),
            "failed_count": len(failed),
        }


def evaluate_readiness(env: Mapping[str, str] | None = None) -> ReadinessDecision:
    source = os.environ if env is None else env
    api_config = DomeneshopConfig.from_env(source)
    sftp_config = SftpReadConfig.from_env(dict(source))
    gate_config = ChangeGateConfig.from_env(source)

    checks: list[dict[str, Any]] = []
    checks.append(_check("api_base_url_configured", bool(api_config.api_base_url)))
    checks.append(_check("api_auth_configured", api_config.has_auth))
    checks.append(_check("sftp_host_configured", bool(sftp_config.host)))
    checks.append(_check("sftp_auth_configured", sftp_config.has_auth))
    checks.append(_check("remote_root_is_allowed", sftp_config.remote_root in sftp_config.allowed_roots))
    checks.append(_check("max_read_file_bytes_positive", sftp_config.max_read_file_bytes > 0))
    checks.append(_check("change_tools_disabled", not gate_config.change_tools_enabled))
    checks.append(_check("dry_run_default_enabled", gate_config.dry_run_default))
    checks.append(_check("operator_approval_required", gate_config.require_operator_approval))
    checks.append(_check("live_action_not_registered", not gate_config.live_action_registered))

    read_only_required = {
        "api_base_url_configured",
        "api_auth_configured",
        "sftp_host_configured",
        "sftp_auth_configured",
        "remote_root_is_allowed",
        "max_read_file_bytes_positive",
        "change_tools_disabled",
        "dry_run_default_enabled",
        "operator_approval_required",
        "live_action_not_registered",
    }
    ready_read_only = all(item["passed"] for item in checks if item["name"] in read_only_required)

    return ReadinessDecision(
        mode="phase8_readiness_preflight",
        ready_for_read_only_runtime=ready_read_only,
        ready_for_live_change_runtime=False,
        checks=checks,
    )


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed)}
