from pathlib import Path

SCRIPT = Path('scripts/sftp_d_r4_live_restore.py').read_text(encoding='utf-8')
WRAPPER = Path('scripts/Invoke-DomeneshopD-R4SftpLiveRestore.ps1').read_text(encoding='utf-8')


def test_restore_exact_bindings_present() -> None:
    assert 'D-R4-SFTP-RESTORE-20260824-001' in SCRIPT
    assert '/www/.mcp-d-r4-validation.txt' in SCRIPT
    assert '482c668063d3b849337b82d5c04dcbcb7fb65a8ccfdae3226a61c5c7e4527203' in SCRIPT
    assert '9e37287a5e29a0d911589ac470ce83c5cabfeba6f0672c24935b6c2df96aa21a' in SCRIPT
    assert 'mcp-validation=D-R4-SFTP-CREATE-20260824\\n' in SCRIPT


def test_restore_requires_exact_before_state() -> None:
    assert 'before_state_mismatch_hold' in SCRIPT
    assert 'before.get("sha256") != BEFORE_SHA256' in SCRIPT
    assert '_write_exact(config)' in SCRIPT


def test_restore_has_independent_readback() -> None:
    assert 'restored_and_readback_verified' in SCRIPT
    assert 'independent_readback_verified=True' in SCRIPT
    assert 'restore_returns_to_accepted_create_state=True' in SCRIPT


def test_restore_does_not_authorize_delete_rename_or_broader_overwrite() -> None:
    assert 'SFTP_D_R4_DELETE_AUTHORIZED' in SCRIPT
    assert 'SFTP_D_R4_RENAME_AUTHORIZED' in SCRIPT
    assert 'SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED' in SCRIPT
    assert '.remove(' not in SCRIPT
    assert '.rename(' not in SCRIPT
    assert 'automatic_delete_performed=False' in SCRIPT


def test_wrapper_restores_global_safe_state() -> None:
    assert "$env:WRITE_TOOLS_ENABLED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_DELETE_AUTHORIZED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_RENAME_AUTHORIZED='false'" in WRAPPER
    assert "$env:SFTP_D_R4_BROADER_OVERWRITE_AUTHORIZED='false'" in WRAPPER
    assert 'D_R4_SFTP_LIVE_RESTORE_EXIT_CODE' in WRAPPER
