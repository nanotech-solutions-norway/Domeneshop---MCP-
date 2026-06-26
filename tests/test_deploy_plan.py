from pathlib import Path

import pytest

from domeneshop_mcp.deploy_plan import (
    LocalManifestEntry,
    RemoteManifestEntry,
    build_local_manifest,
    compare_manifest,
)
from domeneshop_mcp.tools_dry_run import compare_plan


def test_build_local_manifest_hashes_files(tmp_path: Path):
    (tmp_path / "index.html").write_text("hello", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "ignored.txt").write_text("ignore", encoding="utf-8")

    manifest = build_local_manifest(tmp_path)
    assert len(manifest) == 1
    assert manifest[0].relative_path == "index.html"
    assert manifest[0].size == 5
    assert manifest[0].sha256


def test_compare_manifest_classifies_new_changed_unchanged():
    local_entries = [
        LocalManifestEntry("new.html", 3, "aaa"),
        LocalManifestEntry("same.html", 4, "bbb"),
        LocalManifestEntry("changed.html", 5, "ccc"),
    ]
    remote_entries = {
        "/www/same.html": RemoteManifestEntry("/www/same.html", 4, "bbb"),
        "/www/changed.html": RemoteManifestEntry("/www/changed.html", 5, "old"),
    }

    plan = compare_manifest(local_entries, remote_entries, target_root="/www", allowed_roots=("/www",))
    summary = plan.summary()
    assert summary["new_count"] == 1
    assert summary["changed_count"] == 1
    assert summary["unchanged_count"] == 1
    assert summary["will_write"] is False


def test_compare_manifest_rejects_outside_target_root():
    local_entries = [LocalManifestEntry("index.html", 3, "aaa")]
    with pytest.raises(ValueError):
        compare_manifest(local_entries, {}, target_root="/private", allowed_roots=("/www",))


def test_compare_plan_tool_returns_envelope(tmp_path: Path):
    (tmp_path / "index.html").write_text("hello", encoding="utf-8")
    result = compare_plan(str(tmp_path), "/www", ("/www",), [])
    assert result["success"] is True
    assert result["data"]["summary"]["will_write"] is False
    assert result["data"]["summary"]["new_count"] == 1
