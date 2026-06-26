import pytest

from domeneshop_mcp.path_jail import PathGuard, is_text_extension


def test_path_guard_allows_known_root():
    guard = PathGuard.from_csv("/www,/www/atlas_control")
    assert guard.normalize("/www/index.php") == "/www/index.php"
    assert guard.normalize("/www/atlas_control/login.php") == "/www/atlas_control/login.php"


def test_path_guard_rejects_relative_path():
    guard = PathGuard.from_csv("/www")
    with pytest.raises(ValueError):
        guard.normalize("www/index.php")


def test_path_guard_rejects_parent_traversal():
    guard = PathGuard.from_csv("/www")
    with pytest.raises(ValueError):
        guard.normalize("/www/../private/file.php")


def test_path_guard_rejects_outside_root():
    guard = PathGuard.from_csv("/www")
    with pytest.raises(ValueError):
        guard.normalize("/private/file.php")


def test_text_extension_allowlist():
    assert is_text_extension("/www/index.php", {".php"}) is True
    assert is_text_extension("/www/image.png", {".php"}) is False
