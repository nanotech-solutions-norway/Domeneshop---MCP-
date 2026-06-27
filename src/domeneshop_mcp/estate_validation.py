"""Estate registry validation for Phase 11."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class EstateValidation:
    mode: str
    passed: bool
    service_count: int
    checks: list[dict[str, Any]]

    def summary(self) -> dict[str, Any]:
        failed = [item for item in self.checks if not item["passed"]]
        owners = sorted({item.get("owner") for item in self.checks if item.get("owner")})
        return {
            "mode": self.mode,
            "passed": self.passed,
            "service_count": self.service_count,
            "owner_count": len(owners),
            "check_count": len(self.checks),
            "failed_count": len(failed),
        }


def validate_estate_registry(registry_path: str | Path = "config/estate-targets.example.json") -> EstateValidation:
    path = Path(registry_path)
    checks: list[dict[str, Any]] = []
    if not path.exists():
        return EstateValidation("phase11_estate_validation", False, 0, [{"name": "registry_exists", "passed": False}])

    data = json.loads(path.read_text(encoding="utf-8"))
    services = list(data.get("services", []))
    allowed_roots = set(data.get("allowed_roots", []))
    checks.append({"name": "registry_mode_read_plan_only", "passed": data.get("mode") == "read_and_plan_only"})
    checks.append({"name": "allowed_roots_present", "passed": bool(allowed_roots)})
    checks.append({"name": "services_present", "passed": bool(services)})

    seen_names: set[str] = set()
    for service in services:
        name = str(service.get("name", ""))
        owner = str(service.get("owner", ""))
        domain = str(service.get("domain", ""))
        health_url = str(service.get("health_url", ""))
        remote_root = str(service.get("remote_root", ""))
        parsed = urlparse(health_url)
        checks.append({"name": f"service_name_present:{name}", "owner": owner, "passed": bool(name)})
        checks.append({"name": f"service_name_unique:{name}", "owner": owner, "passed": name not in seen_names})
        checks.append({"name": f"domain_present:{name}", "owner": owner, "passed": bool(domain)})
        checks.append({"name": f"health_url_https:{name}", "owner": owner, "passed": parsed.scheme == "https" and bool(parsed.netloc)})
        checks.append({"name": f"remote_root_allowed:{name}", "owner": owner, "passed": remote_root in allowed_roots})
        checks.append({"name": f"category_present:{name}", "owner": owner, "passed": bool(service.get("category"))})
        seen_names.add(name)

    return EstateValidation(
        mode="phase11_estate_validation",
        passed=all(item["passed"] for item in checks),
        service_count=len(services),
        checks=checks,
    )
