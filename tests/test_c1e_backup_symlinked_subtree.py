"""C1-E: a symlinked subtree inside a declared backup tree must not vanish silently.

`backup.manifest` promises an inventory of exactly the producer-declared
roots (capabilities.yaml: "hashes only producer-declared allowlisted
roots"), and the module's own #25 principle (backup_manifest.py,
`_refuse_unreadable`) is that declared content must never "leave the
inventory without a trace". A symlinked subdirectory inside a declared
tree is neither followed (correct: "never follows symlinks") nor refused
nor recorded — the manifest completes green with the whole subtree
missing. This test is fix-agnostic: refuse, cover the subtree, or record
the skipped subtree in the manifest; any of the three passes.
"""

from __future__ import annotations

import json


def _build_ui(workspace):
    """The UI authority the default layout expects next to the repository.

    A synthetic fixture in the test's own tmp workspace, never the live
    sibling checkout (see test_pre_push_hook's live-UI-reader guard)."""
    ui = workspace / "obsidian-ui"
    (ui / "plugin").mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "styles.css", "manifest.json", "build-info.json"):
        (ui / "plugin" / name).write_text("void 0;\n", encoding="utf-8")
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1,
        "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "styles.css", "manifest.json", "build-info.json"],
        "vault_owned": ["data.json"],
    }), encoding="utf-8")
    return ui


def test_symlinked_subtree_is_refused_or_recorded(mini_repo):
    from repo_builders import run_los

    _build_ui(mini_repo.parent)
    stash = mini_repo.parent / "outside-stash"
    (stash / "deep").mkdir(parents=True)
    (stash / "deep" / "moved-notes.md").write_text(
        "archived to the external disk", encoding="utf-8")
    # The classic operator move: a declared tree's subtree now lives behind
    # a link (records/ moved to an external disk and linked back).
    (mini_repo / "records" / "archive").symlink_to(stash, target_is_directory=True)

    result = run_los(mini_repo, "backup-manifest", "--stdout")
    if result.returncode != 0:
        # Fix shape A: the inventory refuses rather than silently omitting.
        return
    manifest = json.loads(result.stdout)
    if "result" in manifest and isinstance(manifest["result"], dict):
        manifest = manifest["result"]
    rows = {(row["root"], row["path"]) for row in manifest["entries"]}
    covered = ("core", "records/archive/deep/moved-notes.md") in rows
    # Fix shape B: the subtree's real files are inventoried (only possible
    # when the link target is inside the authority, so B and C together
    # stay compatible with "never follows symlinks" for out-of-tree links).
    marked = "records/archive" in json.dumps(manifest)
    # Fix shape C: the skipped subtree is recorded in the manifest itself.
    assert covered or marked, (
        "backup-manifest completed green while the declared records tree's "
        "symlinked subtree left the inventory without a trace; entries cover "
        f"{len(rows)} files and the manifest records no skipped subtree")


def test_overnight_alias_restore_rejects_escapes_before_touching_files(tmp_path):
    from learning_os.app.backup_manifest import _rebuild_materials_alias_layer
    base = tmp_path / "restore"
    core = base / "repository"
    core.mkdir(parents=True)
    materials = base / "materials"
    (materials / "real").mkdir(parents=True)
    victim = base / "victim.txt"
    victim.write_text("keep")
    for aliases in ({"../../victim.txt": "real"}, {"safe": "../../outside"}, {"safe": "/tmp"}, {"..": "real"}):
        result = _rebuild_materials_alias_layer({"materials_aliases": aliases}, materials, core)
        assert not result["ok"]
        assert victim.read_text() == "keep" and not victim.is_symlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    (materials / ".flat").symlink_to(outside, target_is_directory=True)
    result = _rebuild_materials_alias_layer({"materials_aliases": {"safe": "real"}}, materials, core)
    assert not result["ok"] and list(outside.iterdir()) == []


# ---- generated/summaries is backed up; its generated siblings are not ----------
# Plan A step 4. The summary cache holds reviewed judgments nothing can rebuild;
# every other tree under generated/ is a disposable cache.

SUMMARY_SHA = "b" * 64


def _summary_world(root):
    summary_dir = root / "generated" / "summaries" / SUMMARY_SHA / "pages-1-2"
    summary_dir.mkdir(parents=True)
    (summary_dir / "summary.md").write_text(
        "<!-- GENERATED file - do not edit; promoted by tools/material_summarize.py --promote -->\n"
        "A reviewed two-page summary.\n", encoding="utf-8")
    (summary_dir / "meta.json").write_text(json.dumps({
        "_generated": {"generator": "tools/material_summarize.py"},
        "sha256": SUMMARY_SHA, "pages": [1, 2]}), encoding="utf-8")
    sibling = root / "generated" / "text-cache" / SUMMARY_SHA
    sibling.mkdir(parents=True)
    (sibling / "index.json").write_text('{"_generated": {}}', encoding="utf-8")
    (root / "generated" / "manifest.json").write_text('{"_generated": {}}', encoding="utf-8")
    outside = root.parent / "outside-summary.md"
    outside.write_text("not part of any backup", encoding="utf-8")
    (summary_dir / "linked.md").symlink_to(outside)
    return summary_dir


def _core_generated(manifest):
    return {(row["path"], row["sha256"]) for row in manifest["entries"]
            if row["root"] == "core" and row["path"].startswith("generated/")}


def test_summary_tree_is_inventoried_exactly_and_restores_byte_for_byte(mini_repo, tmp_path):
    import hashlib
    import shutil

    from repo_builders import run_los

    ui = _build_ui(mini_repo.parent)
    summary_dir = _summary_world(mini_repo)
    result = run_los(mini_repo, "backup-manifest", "--stdout")
    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    if "result" in manifest and isinstance(manifest["result"], dict):
        manifest = manifest["result"]
    inventoried = _core_generated(manifest)
    expected = {
        (f"generated/summaries/{SUMMARY_SHA}/pages-1-2/{name}",
         "sha256:" + hashlib.sha256((summary_dir / name).read_bytes()).hexdigest())
        for name in ("summary.md", "meta.json")}
    # Exactly the two summary files: no text-cache sibling, no top-level
    # generated file, and the link inside the tree is not followed.
    assert inventoried == expected

    manifest_path = tmp_path / "backup" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    restored = tmp_path / "backup" / "restored"
    shutil.copytree(mini_repo, restored / "core", symlinks=True)
    shutil.copytree(mini_repo.parent / "materials", restored / "materials", symlinks=True)
    shutil.copytree(ui, restored / "ui", symlinks=True)
    args = ("backup-verify", "--manifest", str(manifest_path),
            "--restored-core", str(restored / "core"), "--restored-ui", str(restored / "ui"),
            "--restored-materials", str(restored / "materials"), "--checksums-only")
    verified = run_los(mini_repo, *args)
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert json.loads(verified.stdout)["ok"] is True
    after = {(path, "sha256:" + hashlib.sha256((restored / "core" / path).read_bytes()).hexdigest())
             for path, _digest in inventoried}
    assert after == inventoried

    # A summary lost in the restore is reported missing; one changed, a mismatch.
    lost = restored / "core" / "generated" / "summaries" / SUMMARY_SHA / "pages-1-2" / "meta.json"
    lost.unlink()
    (lost.parent / "summary.md").write_text("tampered", encoding="utf-8")
    broken = json.loads(run_los(mini_repo, *args).stdout)
    assert broken["ok"] is False
    assert {(row["path"].rsplit("/", 1)[-1], row["issue"]) for row in broken["issues"]} == {
        ("meta.json", "missing"), ("summary.md", "checksum-mismatch")}


def test_a_linked_directory_inside_the_summary_tree_refuses_the_inventory(mini_repo):
    from repo_builders import run_los

    _build_ui(mini_repo.parent)
    summary_dir = _summary_world(mini_repo)
    elsewhere = mini_repo.parent / "elsewhere"
    (elsewhere / "deep").mkdir(parents=True)
    (elsewhere / "deep" / "summary.md").write_text("moved away", encoding="utf-8")
    (summary_dir.parent / "pages-3-4").symlink_to(elsewhere, target_is_directory=True)
    result = run_los(mini_repo, "backup-manifest", "--stdout")
    assert result.returncode != 0
    assert "symlinked directory" in result.stderr
