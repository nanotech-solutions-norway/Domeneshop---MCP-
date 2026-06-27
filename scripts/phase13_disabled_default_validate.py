"""Validate that Phase 13 remains disabled by default.

This guard is intentionally conservative. It validates that Phase 13 is documented
as a future-risk/scope phase while the repository continues to expose only the
read-only, diagnostic, planning, preflight, and recovery-preview surfaces already
approved by earlier phases.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PHASE13_DOC = Path("docs/PHASE13_RISK_REGISTER_AND_SCOPE.md")
ENV_EXAMPLE = Path("config/domeneshop-mcp.env.example")
SERVER_ENTRYPOINT = Path("src/domeneshop_mcp/server.py")

REQUIRED_DISABLED_DEFAULTS = {
    "WRITE_TOOLS_ENABLED": "false",
    "DRY_RUN_DEFAULT": "true",
    "REQUIRE_OPERATOR_APPROVAL": "true",
    "REQUIRE_BACKUP_EVIDENCE": "true",
    "REQUIRE_PREFLIGHT_REPORT": "true",
}

PHASE13_FLAG_NAMES = (
    "PHASE13_ENABLED",
    "DOMENESHOP_PHASE13_ENABLED",
    "ENABLE_PHASE13",
    "PHASE13_LIVE_CHANGE_ENABLED",
    "LIVE_CHANGE_TOOLS_ENABLED",
)

CAMEL_CASE_FLAG_NAMES = (
    "phase13Enabled",
    "domeneshopPhase13Enabled",
    "enablePhase13",
    "phase13LiveChangeEnabled",
    "liveChangeToolsEnabled",
)

ENABLE_VALUES = ("true", "1", "yes", "on", "enabled")

DISALLOWED_SERVER_MARKERS = (
    "domeneshop_create_dns_record",
    "domeneshop_update_dns_record",
    "domeneshop_delete_dns_record",
    "domeneshop_create_http_forward",
    "domeneshop_update_http_forward",
    "domeneshop_delete_http_forward",
    "domeneshop_update_ddns",
    "sftp_upload_file",
    "sftp_write_text_file",
    "sftp_delete_file",
    "ftp_upload_file",
    "scp_upload_file",
    "ssh_execute_command",
    "deployment_execute",
    "deployment_apply",
    "apply_change",
    "execute_change",
    "restore_backup",
    "tools_write",
    "tools_live_change",
    "tools_phase13",
)

OPERATIONAL_ROOTS = {"config", "src", "scripts", "deploy", ".github"}
OPERATIONAL_TOP_LEVEL_FILES = {"pyproject.toml"}
OPERATIONAL_SUFFIXES = {".py", ".toml", ".json", ".yml", ".yaml", ".env", ".example"}
EXCLUDED_OPERATIONAL_FILES = {Path("scripts/phase13_disabled_default_validate.py")}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that Phase 13 remains disabled by default.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--output",
        default="phase13-disabled-default-validation-report.json",
        help="JSON report path.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    checks = validate_phase13_disabled_default(root)
    passed = all(check.passed for check in checks)

    payload = {
        "summary": {
            "mode": "phase13_disabled_default_validation",
            "phase13_default": "DISABLED" if passed else "CHECK_FAILED",
            "release_decision": "HOLD_PHASE13_ACTIVATION" if passed else "HOLD_FOR_FIX",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for check in checks if not check.passed),
        },
        "checks": [check.__dict__ for check in checks],
    }

    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def validate_phase13_disabled_default(repo_root: Path) -> list[Check]:
    checks: list[Check] = []

    phase13_doc = repo_root / PHASE13_DOC
    env_example = repo_root / ENV_EXAMPLE
    server_entrypoint = repo_root / SERVER_ENTRYPOINT

    checks.append(_exists_check("phase13_doc_exists", phase13_doc))
    checks.append(_exists_check("phase13_validator_exists", repo_root / "scripts" / "phase13_disabled_default_validate.py"))
    checks.append(_exists_check("env_example_exists", env_example))
    checks.append(_exists_check("server_entrypoint_exists", server_entrypoint))

    env_text = _read_text(env_example)
    checks.extend(_check_required_disabled_defaults(env_text))

    doc_text = _read_text(phase13_doc)
    checks.append(
        Check(
            "phase13_doc_declares_disabled_default",
            "DISABLED_BY_DEFAULT" in doc_text and "HOLD_PHASE13_ACTIVATION" in doc_text,
            "Phase 13 document must explicitly hold activation and declare disabled-by-default status.",
        )
    )

    checks.extend(_check_no_enabled_phase13_flags(repo_root))
    checks.extend(_check_server_entrypoint(server_entrypoint))
    return checks


def _exists_check(name: str, path: Path) -> Check:
    return Check(name, path.exists(), f"Required path: {path}")


def _check_required_disabled_defaults(env_text: str) -> list[Check]:
    values = _parse_key_value_lines(env_text)
    checks: list[Check] = []
    for key, expected in REQUIRED_DISABLED_DEFAULTS.items():
        actual = values.get(key)
        checks.append(
            Check(
                f"default_marker:{key}",
                actual == expected,
                f"Expected {key}={expected}; observed {key}={actual!r}.",
            )
        )
    return checks


def _check_no_enabled_phase13_flags(repo_root: Path) -> list[Check]:
    matches: list[str] = []
    flag_pattern = _enabled_flag_pattern()

    for path in _iter_operational_files(repo_root):
        text = _read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if flag_pattern.search(line):
                matches.append(f"{path.relative_to(repo_root)}:{line_no}")

    return [
        Check(
            "no_phase13_enabled_defaults_in_operational_files",
            not matches,
            "Enabled Phase 13 default markers found: " + ", ".join(matches) if matches else "No enabled Phase 13 defaults found.",
        )
    ]


def _check_server_entrypoint(server_entrypoint: Path) -> list[Check]:
    server_text = _read_text(server_entrypoint)
    checks: list[Check] = []
    for marker in DISALLOWED_SERVER_MARKERS:
        checks.append(
            Check(
                f"server_marker_absent:{marker}",
                marker not in server_text,
                f"Server entrypoint must not register or import {marker} by default.",
            )
        )
    return checks


def _enabled_flag_pattern() -> re.Pattern[str]:
    names = [re.escape(name) for name in PHASE13_FLAG_NAMES + CAMEL_CASE_FLAG_NAMES]
    values = "|".join(re.escape(value) for value in ENABLE_VALUES)
    return re.compile(rf"^\s*(?:{'|'.join(names)})\s*[:=]\s*[\"']?(?:{values})[\"']?\s*(?:#.*)?$", re.IGNORECASE)


def _parse_key_value_lines(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'').lower()
    return values


def _iter_operational_files(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            continue
        if rel in EXCLUDED_OPERATIONAL_FILES:
            continue
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        if rel.as_posix() in OPERATIONAL_TOP_LEVEL_FILES:
            yield path
            continue
        if not rel.parts or rel.parts[0] not in OPERATIONAL_ROOTS:
            continue
        if path.suffix in OPERATIONAL_SUFFIXES or path.name in {"Dockerfile", "Dockerfile.example"}:
            yield path


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
