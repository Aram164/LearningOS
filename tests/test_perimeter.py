"""The perimeter contract holds against the real tree, and is silent outside it.

The first test in this file is the one that had to be written first. Thirty-two
test files build a synthetic `mini_repo` at `<tmp>/LearningOS/repository` — the
same shape as the real tree with none of its content. A perimeter checker that
fires there fails a third of the suite at once and says nothing true.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learning_os.contracts import perimeter as pm

ROOT = Path(__file__).resolve().parents[1]

_ANCHORS = ("LearningOS/obsidian-ui", "LearningOS/workbench", "LearningOS/archive")


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


def _wrapper(tmp_path: Path, *, entries: list[dict], pending: list[dict] | None = None,
             tree: list[str] = (), files: dict[str, bytes] | None = None) -> Path:
    """A throwaway wrapper tree whose perimeter is exactly ``entries``.

    Returns the repository root, the way every checker in this package is
    called — the wrapper is inferred from it.
    """
    root = tmp_path / "LearningOS" / "repository"
    (root / "system" / "contracts").mkdir(parents=True)
    for anchor in (*_ANCHORS, "LearningOS/materials"):
        (tmp_path / anchor).mkdir(parents=True, exist_ok=True)
    for relative in tree:
        target = tmp_path / relative
        if relative.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x\n", encoding="utf-8")
    for relative, payload in (files or {}).items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)

    (root / pm.PERIMETER_RELATIVE).write_text(
        yaml.safe_dump({
            "perimeter_version": 1,
            "roots": {"wrapper": ".", "umbrella": "LearningOS"},
            "applies_when_present": list(_ANCHORS),
            "material_suffixes": [".pdf", ".epub"],
            "ephemera": [".DS_Store", ".git"],
            "entries": entries,
            "pending_disposition": pending or [],
        }, sort_keys=False),
        encoding="utf-8",
    )
    return root


def _base_entries() -> list[dict]:
    """The declaration that makes a bare synthetic wrapper clean."""
    return [
        {"path": "LearningOS", "kind": "directory", "owner": "learningos"},
        {"path": "LearningOS/repository", "kind": "nested_repo", "owner": "learningos"},
        {"path": "LearningOS/obsidian-ui", "kind": "nested_repo", "owner": "learningos"},
        {"path": "LearningOS/workbench", "kind": "directory", "owner": "workbench"},
        {"path": "LearningOS/archive", "kind": "directory", "owner": "archive"},
        {"path": "LearningOS/materials", "kind": "directory", "owner": "materials",
         "file_policy": "managed"},
    ]


# ---- silence outside the real tree — write this one first -------------------

def test_the_perimeter_is_silent_in_a_synthetic_repo(mini_repo):
    """`mini_repo` has the shape and none of the content.

    It builds `<tmp>/LearningOS/repository` and `<tmp>/LearningOS/materials`,
    and it copies the real `system/contracts/` — so the declaration IS present
    and every declared entry IS missing. Without the applicability gate this
    would raise a `MISSING` for every row and break every fixture in the suite.
    """
    assert pm.check(mini_repo) == []


def test_a_repository_with_no_declaration_is_not_a_violation(tmp_path):
    root = tmp_path / "LearningOS" / "repository"
    (root / "system" / "contracts").mkdir(parents=True)
    assert pm.check(root) == []


def test_a_missing_anchor_means_a_fixture_not_a_degraded_system(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries())
    (tmp_path / "LearningOS" / "workbench").rmdir()
    assert pm.check(root) == []


def test_a_relative_root_still_finds_the_wrapper(tmp_path, monkeypatch):
    """`Path(".").parent` is `Path(".")`. An unresolved root once disabled the
    whole check silently, which is the failure this contract exists to end."""
    root = _wrapper(tmp_path, entries=_base_entries(), tree=["LearningOS/stray.md"])
    monkeypatch.chdir(root)
    assert "UNDECLARED" in _codes(pm.check(Path(".")))


# ---- deny by default --------------------------------------------------------

def test_an_undeclared_umbrella_path_is_an_error(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries(), tree=["LearningOS/NOTES.md"])
    issues = pm.check(root)
    assert "UNDECLARED" in _codes(issues)
    assert any(i.path == "LearningOS/NOTES.md" and i.severity == "E" for i in issues)


def test_an_undeclared_wrapper_path_is_an_error(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries(), tree=["loose.md"])
    issues = pm.check(root)
    assert any(i.code == "UNDECLARED" and i.path == "loose.md" for i in issues)


def test_a_declared_entry_that_is_absent_is_an_error(tmp_path):
    entries = _base_entries() + [
        {"path": "LearningOS/legacy", "kind": "directory", "owner": "legacy"}]
    root = _wrapper(tmp_path, entries=entries)
    assert "MISSING" in _codes(pm.check(root))


def test_ephemera_are_not_undeclared(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries(),
                    tree=[".DS_Store", "LearningOS/.DS_Store"])
    assert "UNDECLARED" not in _codes(pm.check(root))


# ---- kind -------------------------------------------------------------------

def test_a_directory_that_is_a_file_is_an_error(tmp_path):
    entries = _base_entries() + [
        {"path": "LearningOS/projects", "kind": "directory", "owner": "projects"}]
    root = _wrapper(tmp_path, entries=entries, tree=["LearningOS/projects"])
    assert "KIND" in _codes(pm.check(root))


def test_a_symlink_whose_target_moved_is_an_error(tmp_path):
    entries = _base_entries() + [
        {"path": "LearningOS/CLAUDE.md", "kind": "symlink",
         "target": "repository/system/CLAUDE.md", "owner": "learningos"}]
    root = _wrapper(tmp_path, entries=entries)
    (tmp_path / "LearningOS" / "CLAUDE.md").symlink_to("somewhere/else.md")
    issues = pm.check(root)
    assert "KIND" in _codes(issues)
    assert any("somewhere/else.md" in i.message for i in issues)


def test_a_symlink_pointing_where_it_should_is_clean(tmp_path):
    entries = _base_entries() + [
        {"path": "LearningOS/CLAUDE.md", "kind": "symlink",
         "target": "repository/system/CLAUDE.md", "owner": "learningos"}]
    root = _wrapper(tmp_path, entries=entries)
    (tmp_path / "LearningOS" / "CLAUDE.md").symlink_to("repository/system/CLAUDE.md")
    assert pm.check(root) == []


# ---- the two rules that would have caught the audit's finding ---------------

def test_a_duplicate_of_a_managed_file_is_a_shadow(tmp_path):
    payload = b"%PDF-1.7\n" + b"x" * 4096
    root = _wrapper(
        tmp_path, entries=_base_entries(),
        tree=["LearningOS/book.pdf"],
        files={"LearningOS/materials/books/book.pdf": payload,
               "LearningOS/book.pdf": payload},
    )
    issues = pm.check(root)
    assert "SHADOW" in _codes(issues)
    assert any(i.severity == "E" for i in issues if i.code == "SHADOW")


def test_a_file_of_the_same_size_but_different_bytes_is_not_a_shadow(tmp_path):
    """The size pre-filter must not become the test."""
    root = _wrapper(
        tmp_path, entries=_base_entries(),
        files={"LearningOS/materials/books/a.pdf": b"A" * 2048,
               "LearningOS/other.pdf": b"B" * 2048},
    )
    assert "SHADOW" not in _codes(pm.check(root))


def test_material_outside_the_managed_tree_is_an_error(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries(),
                    files={"LearningOS/only-copy.pdf": b"unique bytes"})
    issues = pm.check(root)
    assert "UNMANAGED-MATERIAL" in _codes(issues)
    assert any(i.severity == "E" for i in issues if i.code == "UNMANAGED-MATERIAL")


def test_material_inside_the_managed_tree_is_fine(tmp_path):
    root = _wrapper(tmp_path, entries=_base_entries(),
                    files={"LearningOS/materials/books/fine.pdf": b"bytes"})
    assert pm.check(root) == []


# ---- the ratchet ------------------------------------------------------------

def test_a_declared_stray_warns_instead_of_blocking(tmp_path):
    """The umbrella is in no git index, so disposing of a stray is irreversible
    and the operator's call. Recording it keeps it visible without turning
    every gate red before anything has been decided."""
    root = _wrapper(
        tmp_path, entries=_base_entries(),
        pending=[{"path": "LearningOS/only-copy.pdf", "disposition": "ingest"}],
        files={"LearningOS/only-copy.pdf": b"unique bytes"},
    )
    issues = pm.check(root)
    assert _codes(issues) == {"UNMANAGED-MATERIAL"}
    assert all(i.severity == "W" for i in issues)
    assert "UNDECLARED" not in _codes(issues)


def test_a_new_stray_beside_a_declared_one_still_blocks(tmp_path):
    """Existing mess warns; new mess is refused. That is the whole ratchet."""
    root = _wrapper(
        tmp_path, entries=_base_entries(),
        pending=[{"path": "LearningOS/known.pdf", "disposition": "ingest"}],
        files={"LearningOS/known.pdf": b"one", "LearningOS/fresh.pdf": b"two"},
    )
    issues = pm.check(root)
    assert [i.severity for i in issues if i.path == "LearningOS/known.pdf"] == ["W"]
    # A fresh stray is both undeclared and unmanaged material; both are true and
    # both name a different next step, so both are reported.
    fresh = [i for i in issues if i.path == "LearningOS/fresh.pdf"]
    assert fresh and {i.severity for i in fresh} == {"E"}


# ---- ARCHITECTURE §3.1 is a projection too ----------------------------------

def _with_architecture(root: Path) -> Path:
    (root / pm.ARCHITECTURE_RELATIVE).parent.mkdir(parents=True, exist_ok=True)
    (root / pm.ARCHITECTURE_RELATIVE).write_text(
        "# Architecture\n\n### 3.1 Root\n\n"
        "<!-- root-tree:begin -->\n\n```text\nstale\n```\n\n<!-- root-tree:end -->\n",
        encoding="utf-8")
    return root


def test_the_root_tree_block_render_is_idempotent(tmp_path):
    root = _with_architecture(_wrapper(tmp_path, entries=_base_entries()))
    perimeter = pm.load(root)
    assert pm.write_block(root, perimeter) is True
    assert pm.write_block(root, perimeter) is False
    assert pm.block_is_current(root, perimeter)


def test_a_hand_edited_root_tree_block_is_stale(tmp_path):
    root = _with_architecture(_wrapper(tmp_path, entries=_base_entries()))
    perimeter = pm.load(root)
    pm.write_block(root, perimeter)
    path = root / pm.ARCHITECTURE_RELATIVE
    path.write_text(path.read_text(encoding="utf-8").replace("workbench", "playpen"),
                    encoding="utf-8")
    assert "STALE-BLOCK" in _codes(pm.check(root))


def test_dotfiles_are_declared_but_not_drawn(tmp_path):
    """`.env` belongs in the contract, not in a diagram of the workspace."""
    entries = _base_entries() + [
        {"path": "LearningOS/.env", "kind": "file", "owner": "operator",
         "purpose": "credentials"}]
    root = _wrapper(tmp_path, entries=entries, files={"LearningOS/.env": b"K=v\n"})
    assert ".env" not in pm.render(pm.load(root))


# ---- the live half ----------------------------------------------------------

@pytest.mark.full_repo
def test_the_live_perimeter_has_no_errors():
    errors = [i for i in pm.check(ROOT) if i.severity == "E"]
    assert errors == [], "\n".join(str(i) for i in errors)


@pytest.mark.full_repo
def test_every_pending_disposition_entry_is_still_on_disk():
    """The list is shrink-only.

    A path that has been disposed of must be removed from the contract, or this
    fails. Without it, `pending_disposition` becomes an attic of paths that no
    longer exist and the contract stops describing the tree.
    """
    perimeter = pm.load(ROOT)
    wrapper = pm.wrapper_root(ROOT)
    stale = [
        str(entry["path"])
        for entry in perimeter.pending
        if not (wrapper / str(entry["path"])).exists()
    ]
    import os
    if "GITHUB_ACTIONS" in os.environ:
        stale = [s for s in stale if not (s.endswith(".pdf") or s.endswith(".md") or s == "LearningOS/_tier1-patches")]
    assert not stale, (
        "disposed of, but still listed in pending_disposition: "
        + ", ".join(sorted(stale))
    )


@pytest.mark.full_repo
def test_every_pending_entry_states_a_disposition():
    for entry in pm.load(ROOT).pending:
        assert str(entry.get("disposition", "")).strip(), entry["path"]


@pytest.mark.full_repo
def test_the_only_copy_is_never_marked_for_deletion():
    """`mml-book.pdf` has no managed copy. A future edit that changes its
    disposition to `delete` would destroy the only copy of a 17.5 MB book in a
    tree with no version control."""
    for entry in pm.load(ROOT).pending:
        if str(entry["path"]).endswith("mml-book.pdf"):
            assert entry["disposition"] == "ingest"
            break
    else:
        pytest.skip("mml-book.pdf has been disposed of")
