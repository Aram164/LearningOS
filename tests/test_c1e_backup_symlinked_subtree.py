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
