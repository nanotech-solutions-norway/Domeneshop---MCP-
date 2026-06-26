"""Runtime deployment validation for Phase 9."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_DEPLOYMENT_FILES = (
    "deploy/container/Dockerfile.example",
    "deploy/compose/compose.readonly.example.yml",
    "deploy/systemd/domeneshop-mcp.service.example",
    "docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md",
    "config/mcp-client.example.json",
)

REQUIRED_SAFE_MARKERS = (
    "WRITE_TOOLS_ENABLED=false",
    "DRY_RUN_DEFAULT=true",
    "REQUIRE_OPERATOR_APPROVAL=true",
)


@dataclass(frozen=True)
class RuntimeDeploymentValidation:
    mode: str
    passed: bool
    checks: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        failed = [item for item in self.checks if not item["passed"]]
        return {
            "mode": self.mode,
            "passed": self.passed,
            "check_count": len(self.checks),
            "failed_count": len(failed),
        }


def validate_runtime_deployment(repo_root: str | Path = ".") -> RuntimeDeploymentValidation:
    root = Path(repo_root)
    checks: list[dict[str, Any]] = []

    for rel in REQUIRED_DEPLOYMENT_FILES:
        checks.append({"name": f"file_exists:{rel}", "passed": (root / rel).exists()})

    env_template = root / "config" / "domeneshop-mcp.env.example"
    env_text = env_template.read_text(encoding="utf-8") if env_template.exists() else ""
    for marker in REQUIRED_SAFE_MARKERS:
        checks.append({"name": f"safe_marker:{marker}", "passed": marker in env_text})

    compose = root / "deploy" / "compose" / "compose.readonly.example.yml"
    compose_text = compose.read_text(encoding="utf-8") if compose.exists() else ""
    checks.append({"name": "compose_keeps_change_tools_disabled", "passed": "WRITE_TOOLS_ENABLED" in compose_text and "false" in compose_text})
    checks.append({"name": "compose_uses_server_command_indirectly", "passed": "domeneshop-mcp" in compose_text})

    passed = all(item["passed"] for item in checks)
    return RuntimeDeploymentValidation(mode="phase9_runtime_deployment_validation", passed=passed, checks=checks)
