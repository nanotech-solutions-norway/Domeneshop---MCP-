from __future__ import annotations

import hashlib
from pathlib import Path


SCRIPT = Path("scripts/sftp_d_r4_live_create.py")
WRAPPER = Path("scripts/Invoke-DomeneshopD-R4SftpLiveCreate.ps1")
TARGET = "/www/.mcp-d-r4-validation.txt"
PAYLOAD = b"mcp-validation=D-R4-SFTP-CREATE-20260824\n"
TARGET_SHA256 = "0619d5e786da50c431b090667936a2076b7bbd1054bda5758c30d74eec7f2f2a"
PAYLOAD_SHA256 = "9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a"


def test_exact_bindings_are_deterministic() -> None:
    assert hashlib.sha256(TARGET.encode()).hexdigest() == TARGET_SHA256
    assert hashlib.sha256(PAYLOAD).hexdigest() == PAYLOAD_SHA256


def test_live_gate_contains_no_delete_or_overwrite_operations() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = (".remove(", ".unlink(", ".rename(", ".truncate(", "\"w\"", "'w'")
    for token in forbidden:
        assert token not in text
    assert 'sftp.open(TARGET, "x")' in text
    assert 'SFTP_D_R4_OVERWRITE_AUTHORIZED' in text
    assert 'SFTP_D_R4_DELETE_AUTHORIZED' in text


def test_wrapper_keeps_global_write_tools_disabled() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "$env:WRITE_TOOLS_ENABLED='false'" in text
    assert "$env:SFTP_D_R4_CREATE_AUTHORIZED='true'" in text
    assert "$env:SFTP_D_R4_OVERWRITE_AUTHORIZED='false'" in text
    assert "$env:SFTP_D_R4_DELETE_AUTHORIZED='false'" in text
