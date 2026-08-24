from pathlib import Path


def test_repair_gate_is_exactly_bound_and_has_no_delete_or_rename() -> None:
    text = Path("scripts/sftp_d_r4_repair_update.py").read_text(encoding="utf-8")
    assert 'TARGET = "/www/.mcp-d-r4-validation.txt"' in text
    assert 'BEFORE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"' in text
    assert 'AFTER_SHA256 = "9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a"' in text
    assert 'PAYLOAD = b"mcp-validation=D-R4-SFTP-CREATE-20260824\\n"' in text
    assert ".remove(" not in text
    assert ".rename(" not in text
    assert ".unlink(" not in text


def test_repair_gate_requires_verified_empty_before_state() -> None:
    text = Path("scripts/sftp_d_r4_repair_update.py").read_text(encoding="utf-8")
    assert 'before.get("sha256") != BEFORE_SHA256' in text
    assert 'before.get("size") != 0' in text
    assert 'status="before_state_mismatch_hold"' in text
    assert 'with sftp.open(TARGET, "wb") as handle:' in text


def test_wrapper_keeps_global_write_and_destructive_actions_disabled() -> None:
    text = Path("scripts/Invoke-DomeneshopD-R4SftpRepairUpdate.ps1").read_text(encoding="utf-8")
    assert "$env:WRITE_TOOLS_ENABLED='false'" in text
    assert "$env:SFTP_D_R4_DELETE_AUTHORIZED='false'" in text
    assert "$env:SFTP_D_R4_RENAME_AUTHORIZED='false'" in text
