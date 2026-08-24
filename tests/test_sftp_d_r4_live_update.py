from pathlib import Path

SCRIPT = Path("scripts/sftp_d_r4_live_update.py").read_text(encoding="utf-8")
WRAPPER = Path("scripts/Invoke-DomeneshopD-R4SftpLiveUpdate.ps1").read_text(encoding="utf-8")


def test_update_gate_binds_exact_release_target_and_hashes():
    assert 'D-R4-SFTP-UPDATE-20260824-001' in SCRIPT
    assert '/www/.mcp-d-r4-validation.txt' in SCRIPT
    assert '9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a' in SCRIPT
    assert '482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203' in SCRIPT


def test_update_gate_requires_exact_before_state_and_readback():
    assert 'before_state_mismatch_hold' in SCRIPT
    assert 'independent_readback_verified' in SCRIPT
    assert 'read_text_file(TARGET)' in SCRIPT


def test_update_gate_has_no_delete_or_rename_calls():
    lowered = SCRIPT.lower()
    assert '.remove(' not in lowered
    assert '.unlink(' not in lowered
    assert '.rename(' not in lowered
    assert 'sftp_delete_authorized' in lowered
    assert 'sftp_rename_authorized' in lowered


def test_wrapper_preserves_global_write_lock_and_no_broader_overwrite():
    assert "$env:WRITE_TOOLS_ENABLED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_DELETE_AUTHORIZED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_RENAME_AUTHORIZED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED='false'" in WRAPPER
