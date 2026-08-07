"""The external materials tree's durable inventory and its integrity checks.

materials/ is tracked by no Git repository, so the manifest is the only thing
standing between "the drive is unmounted" and silent, unnoticed data loss.
These tests are hermetic: they build synthetic materials trees under tmp_path
and never read the real 1.9 GB tree.
"""

from __future__ import annotations

import textwrap

import yaml

import materials_manifest as mm
from learning_os.loader import load_repo
from learning_os.rules import validate
from learning_os.rules.materials import _uris_in


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def make_tree(base, files: dict[str, str]):
    for rel, text in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return base


# ------------------------------------------------------------------ manifest
def test_build_records_every_durable_file(tmp_path):
    base = make_tree(tmp_path / "materials", {
        "Books/a.pdf": "alpha",
        "ML/course/b.pdf": "beta",
    })
    manifest = mm.build(base)
    assert manifest["totals"]["files"] == 2
    assert manifest["totals"]["bytes"] == len("alpha") + len("beta")
    assert set(manifest["files"]) == {"Books/a.pdf", "ML/course/b.pdf"}
    assert len(manifest["files"]["Books/a.pdf"]["sha256"]) == 64


def test_build_excludes_symlinks_noise_and_generated_catalogue(tmp_path):
    base = make_tree(tmp_path / "materials", {
        "Books/a.pdf": "alpha",
        "README.md": "generated catalogue",
        "FILES.txt": "generated listing",
        "INDEX.html": "generated page",
        "Books/.DS_Store": "junk",
        "ML/README.md": "a real nested readme, not the catalogue",
    })
    (base / ".flat").mkdir()
    (base / ".flat" / "source-a").symlink_to(base / "Books")

    keys = set(mm.build(base)["files"])
    assert keys == {"Books/a.pdf", "ML/README.md"}, keys


def test_verify_detects_deletion_change_and_new_files(tmp_path):
    base = make_tree(tmp_path / "materials", {
        "a.pdf": "alpha", "b.pdf": "beta", "c.pdf": "gamma",
    })
    manifest = mm.build(base)

    (base / "a.pdf").unlink()
    (base / "b.pdf").write_text("beta-but-longer", encoding="utf-8")
    (base / "d.pdf").write_text("delta", encoding="utf-8")

    result = mm.verify(manifest, base)
    assert result["missing"] == ["a.pdf"]
    assert result["changed"] == ["b.pdf"]
    assert result["unregistered"] == ["d.pdf"]


def test_deep_verify_catches_same_size_corruption(tmp_path):
    """The case a size check cannot see — a silently rewritten file."""
    base = make_tree(tmp_path / "materials", {"a.pdf": "alpha"})
    manifest = mm.build(base)
    (base / "a.pdf").write_text("ALPHA", encoding="utf-8")  # same length

    assert mm.verify(manifest, base, deep=False)["changed"] == []
    assert mm.verify(manifest, base, deep=True)["changed"] == ["a.pdf"]


def test_verify_proves_a_restored_copy_is_complete(tmp_path):
    """The restore path: a backup is trustworthy only if it can be checked."""
    original = make_tree(tmp_path / "materials", {"x/a.pdf": "alpha", "b.pdf": "beta"})
    manifest = mm.build(original)

    good = make_tree(tmp_path / "restored-good", {"x/a.pdf": "alpha", "b.pdf": "beta"})
    assert mm.verify(manifest, good, deep=True) == {
        "missing": [], "changed": [], "unregistered": []}

    truncated = make_tree(tmp_path / "restored-bad", {"b.pdf": "beta"})
    assert mm.verify(manifest, truncated, deep=True)["missing"] == ["x/a.pdf"]


# ----------------------------------------------------------------- URI sweep
def test_uri_sweep_handles_filenames_with_spaces():
    """Real filenames contain spaces; a whitespace-delimited scan truncates them."""
    text = textwrap.dedent("""\
        Scope authority: `material://Math/course/unser skript.pdf`
        A link: [the script](material://Math/course/Aufgabe 3 ist gut.pdf)
        Bare: material://Math/course/plain.pdf, and a sentence end
        material://Math/course/trailing.pdf.
    """)
    assert _uris_in(text) == {
        "Math/course/unser skript.pdf",
        "Math/course/Aufgabe 3 ist gut.pdf",
        "Math/course/plain.pdf",
        "Math/course/trailing.pdf",
    }


def test_uri_sweep_strips_fragments():
    assert _uris_in("`material://a/b.pdf#page=12`") == {"a/b.pdf"}


# ------------------------------------------------------------ validator tier
def _wire(mini_repo, *, uri: str, manifest_files: dict | None):
    """Point a canonical note at `uri`, optionally writing a manifest."""
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(note.read_text(encoding="utf-8") + f"\nSee `{uri}`.\n",
                    encoding="utf-8")
    if manifest_files is not None:
        (mini_repo / "records" / "materials-manifest.yaml").write_text(
            yaml.safe_dump({"schema_version": 1, "captured": "2026-08-07",
                            "totals": {"files": len(manifest_files), "bytes": 0},
                            "files": manifest_files}), encoding="utf-8")
    return validate(load_repo(mini_repo))


def test_missing_manifest_is_a_warning_not_an_error(mini_repo):
    issues = _wire(mini_repo, uri="material://a.pdf", manifest_files=None)
    assert "MATERIALS-MANIFEST" in codes(issues, "W")
    assert codes(issues, "E") == []


def test_referenced_file_gone_from_disk_is_an_error(mini_repo):
    materials = mini_repo.parent / "materials"
    (materials / "a.pdf").write_text("alpha", encoding="utf-8")
    manifest = {"a.pdf": {"size": 5, "sha256": "x"}}

    clean = _wire(mini_repo, uri="material://a.pdf", manifest_files=manifest)
    assert "MATERIAL-MISSING" not in codes(clean)

    (materials / "a.pdf").unlink()
    broken = validate(load_repo(mini_repo))
    assert "MATERIAL-MISSING" in codes(broken, "E")


def test_reference_absent_from_the_manifest_is_an_error(mini_repo):
    """Unrestorable: no backup was ever known to need this file."""
    (mini_repo.parent / "materials" / "a.pdf").write_text("alpha", encoding="utf-8")
    issues = _wire(mini_repo, uri="material://a.pdf", manifest_files={})
    assert "MATERIAL-UNREGISTERED" in codes(issues, "E")


def test_unreferenced_inventory_drift_only_warns(mini_repo):
    """Reorganising materials nags; it does not block a commit."""
    issues = _wire(mini_repo, uri="material://a.pdf",
                   manifest_files={"a.pdf": {"size": 5, "sha256": "x"},
                                   "gone.pdf": {"size": 9, "sha256": "y"}})
    (mini_repo.parent / "materials" / "a.pdf").write_text("alpha", encoding="utf-8")
    issues = validate(load_repo(mini_repo))
    assert "MATERIALS-DRIFT" in codes(issues, "W")
    assert "MATERIALS-DRIFT" not in codes(issues, "E")


def test_offline_tree_warns_once_instead_of_erroring_per_file(mini_repo):
    """An unmounted drive is not data loss and must not produce 1,141 errors."""
    (mini_repo.parent / "materials").rmdir()
    manifest = {f"f{i}.pdf": {"size": 1, "sha256": "z"} for i in range(50)}
    issues = _wire(mini_repo, uri="material://f0.pdf", manifest_files=manifest)
    assert codes(issues, "W").count("MATERIALS-OFFLINE") == 1
    assert "MATERIAL-MISSING" not in codes(issues, "E")
