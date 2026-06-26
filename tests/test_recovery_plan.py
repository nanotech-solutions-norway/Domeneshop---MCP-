from domeneshop_mcp.deploy_plan import DeploymentPlan, RemoteManifestEntry
from domeneshop_mcp.recovery_plan import build_backup_evidence_manifest, build_restore_preview
from domeneshop_mcp.tools_recovery_plan import build_backup_manifest_from_plan, build_restore_preview_from_manifest


def make_plan():
    return DeploymentPlan(
        mode="dry_run",
        source_root=".",
        target_root="/www",
        new_files=[{"relative_path": "new.html", "remote_path": "/www/new.html", "size": 3, "sha256": "new"}],
        changed_files=[{"relative_path": "changed.html", "remote_path": "/www/changed.html", "size": 5, "sha256": "local"}],
        unchanged_files=[],
        blocked_files=[],
    )


def test_backup_manifest_only_includes_changed_files():
    plan = make_plan()
    remote = {
        "/www/changed.html": RemoteManifestEntry("/www/changed.html", 4, "remote-old"),
        "/www/new.html": RemoteManifestEntry("/www/new.html", 3, "unexpected"),
    }
    manifest = build_backup_evidence_manifest(
        plan,
        remote,
        backup_root="/www/backups/dry-run",
        allowed_roots=("/www",),
        timestamp="2026-06-26T12:30:00+00:00",
    )
    assert manifest.summary()["entry_count"] == 1
    assert manifest.summary()["will_write"] is False
    assert manifest.entries[0]["remote_path"] == "/www/changed.html"
    assert manifest.entries[0]["backup_path"] == "/www/backups/dry-run/changed.html"


def test_restore_preview_is_plan_only():
    plan = make_plan()
    remote = {"/www/changed.html": RemoteManifestEntry("/www/changed.html", 4, "remote-old")}
    manifest = build_backup_evidence_manifest(plan, remote, backup_root="/www/backups/dry-run", allowed_roots=("/www",))
    preview = build_restore_preview(manifest, allowed_roots=("/www",))
    assert preview.summary()["restore_target_count"] == 1
    assert preview.summary()["will_write"] is False
    assert preview.restore_targets[0]["to_remote_path"] == "/www/changed.html"


def test_tool_build_backup_manifest_from_plan():
    plan = make_plan()
    remote_metadata = [{"path": "/www/changed.html", "size": 4, "sha256": "remote-old"}]
    result = build_backup_manifest_from_plan({"plan": plan.__dict__}, remote_metadata, "/www/backups/dry-run", ["/www"])
    assert result["success"] is True
    assert result["data"]["summary"]["entry_count"] == 1
    assert result["data"]["summary"]["will_write"] is False


def test_tool_build_restore_preview_from_manifest():
    plan = make_plan()
    remote = {"/www/changed.html": RemoteManifestEntry("/www/changed.html", 4, "remote-old")}
    manifest = build_backup_evidence_manifest(plan, remote, backup_root="/www/backups/dry-run", allowed_roots=("/www",))
    result = build_restore_preview_from_manifest({"manifest": manifest.__dict__}, ["/www"])
    assert result["success"] is True
    assert result["data"]["summary"]["restore_target_count"] == 1
    assert result["data"]["summary"]["live_restore"] is False
