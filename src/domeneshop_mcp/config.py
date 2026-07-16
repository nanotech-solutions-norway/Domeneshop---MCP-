"""Configuration helpers for the Domeneshop MCP bridge."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .credential_policy import has_runtime_value


@dataclass(frozen=True)
class DomeneshopConfig:
    api_base_url: str = "https://api.domeneshop.no/v0"
    auth_user: str = ""
    auth_value: str = ""
    write_tools_enabled: bool = False
    dry_run_default: bool = True
    require_operator_approval: bool = True
    timeout_seconds: float = 20.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "DomeneshopConfig":
        source = os.environ if env is None else env

        def as_bool(name: str, default: bool) -> bool:
            raw = str(source.get(name, str(default))).strip().lower()
            return raw in {"1", "true", "yes", "on"}

        return cls(
            api_base_url=str(source.get("DOMENESHOP_API_BASE_URL", cls.api_base_url)).rstrip("/"),
            auth_user=str(source.get("DS_AUTH_USER", "")),
            auth_value=str(source.get("DS_AUTH_VALUE", "")),
            write_tools_enabled=as_bool("WRITE_TOOLS_ENABLED", False),
            dry_run_default=as_bool("DRY_RUN_DEFAULT", True),
            require_operator_approval=as_bool("REQUIRE_OPERATOR_APPROVAL", True),
            timeout_seconds=float(source.get("DOMENESHOP_TIMEOUT_SECONDS", "20")),
        )

    @property
    def has_auth(self) -> bool:
        return has_runtime_value(self.auth_user) and has_runtime_value(self.auth_value)

    def require_auth(self) -> None:
        if not self.has_auth:
            raise ValueError("Domeneshop API authentication values are missing or placeholders.")
