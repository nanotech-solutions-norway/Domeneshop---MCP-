"""Validate the repository's minimum security and workflow controls."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


REQUIRED_CONTROLS = (
    "SECURITY.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/dependabot.yml",
)
ALLOWED_ENV_FILES = {".env.example", ".env.sample", ".env.template"}
BLOCKED_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".kdbx"}
BLOCKED_NAMES = {"id_rsa", "id_ed25519", "service-account.json"}
BLOCKED_DIRECTORIES = {"secrets", "credentials", "private"}


def _tracked_paths() -> list[str]:
    base = os.getenv("BASE_SHA", "").strip()
    head = os.getenv("HEAD_SHA", "").strip()
    command = ["git", "diff", "--name-only", base, head] if base and head else ["git", "ls-files"]
    return subprocess.check_output(command, text=True).splitlines()


def validate() -> list[str]:
    violations = [f"missing required control: {path}" for path in REQUIRED_CONTROLS if not Path(path).is_file()]

    for raw in _tracked_paths():
        path = Path(raw)
        name = path.name.lower()
        parent_parts = {part.lower() for part in path.parts[:-1]}

        if name.startswith(".env") and name not in ALLOWED_ENV_FILES:
            violations.append(f"prohibited environment file: {raw}")
        if path.suffix.lower() in BLOCKED_SUFFIXES or name in BLOCKED_NAMES:
            violations.append(f"prohibited credential/key file: {raw}")
        if parent_parts.intersection(BLOCKED_DIRECTORIES):
            violations.append(f"prohibited sensitive directory: {raw}")

        if raw.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"} and path.is_file():
            text = path.read_text(encoding="utf-8")
            if not re.search(r"(?m)^permissions:\s*(?:$|\n)", text):
                violations.append(f"workflow lacks top-level permissions: {raw}")
            if re.search(r"(?m)^\s*pull_request_target\s*:", text):
                violations.append(f"pull_request_target prohibited: {raw}")
            if re.search(r"persist-credentials\s*:\s*true", text, re.IGNORECASE):
                violations.append(f"workflow persists checkout credentials: {raw}")
            for match in re.finditer(r"(?m)^\s*uses:\s*([^\s#]+)", text):
                target = match.group(1)
                if target.startswith("./") or target.startswith("docker://"):
                    continue
                if "@" not in target or not re.fullmatch(r"[0-9a-fA-F]{40}", target.rsplit("@", 1)[1]):
                    violations.append(f"external action is not pinned to a full SHA in {raw}: {target}")

    return sorted(set(violations))


def main() -> int:
    violations = validate()
    if violations:
        print("Repository security baseline failed:")
        for item in violations:
            print(f"- {item}")
        return 1
    print("Repository security baseline passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
