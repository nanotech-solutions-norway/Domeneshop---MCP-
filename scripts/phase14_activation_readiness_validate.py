"""Validate the Phase 14 activation-readiness gate.

Phase 14 is not an activation phase. This validator confirms that the repository
contains the approval/evidence gate while live change operations remain held and
write-capable tools remain unregistered by default.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

PHASE13_DOC = Path("docs/PHASE13_RISK_REGISTER_AND_SCOPE.md")
PHASE14_DOC = Path("docs/PHASE14_ACTIVATION_READINESS_GATE.md")
ENV_EXAMPLE = Path("config/domeneshop-mcp.env.example")
SERVER_ENTRYPOINT = Path("src/domeneshop_mcp/server.py")
WORKFLOW = Path(".github/workflows/validate-domeneshop-mcp.yml")

REQUIRED_ENV_DEFAULTS = {
    "WRITE_TOOLS_ENABLED": "false",
    "DRY_RUN_DEFAULT": "true",
    "REQUIRE_OPERATOR_APPROVAL": "true",
    "REQUIRE_BACKUP_EVIDENCE": "true",
    "REQUIRE_PREFLIGHT_REPORT": "true",
}

REQUIRED_PHASE14_MARKERS = (
    "READINESS_GATE_ONLY",
    "HOLD_LIVE_CHANGE_ACTIVATION",
    "HOLD_PHASE13_ACTIVATION",
    "HOLD_PHASE14_ACTIVATION_READINESS_ONLY",
    "PENDING_EXPLICIT_RELEASE_APPROVAL",
)

REQUIRED_WORKFLOW_MARKERS = (
    "phase13_disabled_default_validate.py",
    "phase14_activation_readiness_validate.py",
    "phase14-activation-readiness-validation-report.json",
)

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
    "tools_phase14",
)

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Phase 14 activation-readiness gate.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--output",
        default="phase14-activation-readiness-validation-report.json",
        help="JSON report path.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    checks = validate_phase14_activation_readiness(root)
    passed = all(check.passed for check in checks)

    payload = {
        "summary": {
            "mode": "phase14_activation_readiness_validation",
            "phase14_gate": "READINESS_ONLY" if passed else "CHECK_FAILED",
            "release_decision": "HOLD_LIVE_CHANGE_ACTIVATION" if passed else "HOLD_FOR_FIX",
            "passed": passed,
            "check_count": len(checks),
            "failed_count": sum(1 for check in checks if not check.passed),
        },
        "checks": [check.__dict__ for check in checks],
    }

    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    return 0 if passed else 1


def validate_phase14_activation_readiness(repo_root: Path) -> list[Check]:
    checks: list[Check] = []

    checks.append(_exists_check("phase13_doc_exists", repo_root / PHASE13_DOC))
    checks.append(_exists_check("phase14_doc_exists", repo_root / PHASE14_DOC))
    checks.append(_exists_check("phase14_validator_exists", repo_root / "scripts" / "phase14_activation_readiness_validate.py"))
    checks.append(_exists_check("env_example_exists", repo_root / ENV_EXAMPLE))
    checks.append(_exists_check("server_entrypoint_exists", repo_root / SERVER_ENTRYPOINT))
    checks.append(_exists_check("workflow_exists", repo_root / WORKFLOW))

    env_values = _parse_key_value_lines(_read_text(repo_root / ENV_EXAMPLE))
    for key, expected in REQUIRED_ENV_DEFAULTS.items():
        actual = env_values.get(key)
        checks.append(
            Check(
                f"env_default:{key}",
                actual == expected,
                f"Expected {key}={expected}; observed {key}={actual!r}.",
            )
        )

    phase13_text = _read_text(repo_root / PHASE13_DOC)
    checks.append(
        Check(
            "phase13_activation_still_held",
            "HOLD_PHASE13_ACTIVATION" in phase13_text,
            "Phase 13 hold marker must remain present.",
        )
    )

    phase14_text = _read_text(repo_root / PHASE14_DOC)
    for marker in REQUIRED_PHASE14_MARKERS:
        checks.append(
            Check(
                f"phase14_marker:{marker}",
                marker in phase14_text,
                f"Phase 14 document must contain {marker}.",
            )
        )

    workflow_text = _read_text(repo_root / WORKFLOW)
    for marker in REQUIRED_WORKFLOW_MARKERS:
        checks.append(
            Check(
                f"workflow_marker:{marker}",
                marker in workflow_text,
                f"Workflow must include {marker}.",
            )
        )

    server_text = _read_text(repo_root / SERVER_ENTRYPOINT)
    for marker in DISALLOWED_SERVER_MARKERS:
        checks.append(
            Check(
                f"server_marker_absent:{marker}",
                marker not in server_text,
                f"Server entrypoint must not register or import {marker} by default.",
            )
        )

    return checks


def _exists_check(name: str, path: Path) -> Check:
    return Check(name, path.exists(), f"Required path: {path}")


def _parse_key_value_lines(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'').lower()
    return values


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
