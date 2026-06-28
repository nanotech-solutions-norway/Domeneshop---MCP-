"""Validate the Phase 42 production use validation gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DOC = "docs/PHASE42_PRODUCTION_USE_VALIDATION.md"
REPORT = "phase42-production-use-validation-report.json"
REQUIRED_MARKERS = [
    "HOLD_PHASE42_PRODUCTION_USE_VALIDATION_ONLY",
    "WRITE_READINESS_SEQUENCE_COMPLETE",
    "READY_FOR_EXTERNAL_CONTROLLED_VALIDATION",
    "NO_AUTONOMOUS_LIVE_CHANGE",
    "RUNTIME_VALUES_OUTSIDE_REPOSITORY",
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "FINAL_OPERATOR_SIGNOFF_REF",
    "VERIFY_FINAL_OPERATOR_SIGNOFF_REQUIRED",
]
ENV_DEFAULTS = {
    "WRITE_TOOLS_ENABLED": "false",
    "DRY_RUN_DEFAULT": "true",
    "REQUIRE_OPERATOR_APPROVAL": "true",
    "REQUIRE_BACKUP_EVIDENCE": "true",
    "REQUIRE_PREFLIGHT_REPORT": "true",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Phase 42 production use validation gate.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default=REPORT)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    checks = validate(root)
    passed = all(item["passed"] for item in checks)
    payload = {
        "summary": {
            "mode": "phase42_production_use_validation",
            "phase42_production_use": "PRODUCTION_USE_VALIDATION_ONLY" if passed else "CHECK_FAILED",
            "release_decision": "READY_FOR_EXTERNAL_CONTROLLED_VALIDATION" if passed else "HOLD_FOR_FIX",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for item in checks if not item["passed"]),
        },
        "checks": checks,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def validate(root: Path) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for rel in [DOC, "README.md", "config/domeneshop-mcp.env.example", ".github/workflows/validate-domeneshop-mcp.yml"]:
        checks.append(check(f"file:{rel}", (root / rel).exists(), rel))

    env = parse_env(read(root / "config/domeneshop-mcp.env.example"))
    for key, expected in ENV_DEFAULTS.items():
        checks.append(check(f"env:{key}", env.get(key) == expected, f"expected={expected} observed={env.get(key)!r}"))

    combined = read(root / DOC) + "\n" + read(root / "README.md")
    for marker in REQUIRED_MARKERS:
        checks.append(check(f"marker:{marker}", marker in combined, marker))

    workflow = read(root / ".github/workflows/validate-domeneshop-mcp.yml")
    checks.append(check("report:phase42", REPORT in workflow, REPORT))
    checks.append(check("report:manifest", "read-only-release-manifest-validation-report.json" in workflow, "manifest report"))
    return checks


def check(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "passed": passed, "detail": detail}


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"\'').lower()
    return values


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
