"""The declared tree matches disk, and ARCHITECTURE §3.2 is its projection.

`test_render_is_idempotent` is first because it is the assumption everything
else rests on. A renderer that is not stable turns `make check` into a coin
toss: the block is regenerated, the checker compares, and the comparison fails
for reasons nobody can see in a diff.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learning_os.contracts import tree_contract as tc

ROOT = Path(__file__).resolve().parents[1]


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


def _repo(tmp_path: Path, *, directories: list[dict], hidden: dict | None = None,
          tree: list[str] = (), architecture: bool = True) -> Path:
    """A throwaway repository whose declared tree is exactly ``directories``."""
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    # The anchors that tell the checker this is a real repository rather than a
    # fixture that copied system/contracts/. Without them every test below
    # would pass vacuously.
    (tmp_path / "system" / "adr").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tools" / "learning_os").mkdir(parents=True, exist_ok=True)
    for relative in tree:
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)

    (tmp_path / tc.TREE_RELATIVE).write_text(
        yaml.safe_dump({
            "tree_version": 1,
            "applies_when_present": [
                "system/ARCHITECTURE.md", "system/adr", "tools/learning_os"],
            "directories": directories,
            "hidden": hidden or {},
            "residue": ["__pycache__"],
            "residue_suffixes": [".egg-info"],
        }, sort_keys=False),
        encoding="utf-8",
    )
    if architecture:
        (tmp_path / tc.ARCHITECTURE_RELATIVE).write_text(
            "# Architecture\n\n### 3.2 Tree\n\n"
            "<!-- tree:begin -->\n\n```text\nstale\n```\n\n<!-- tree:end -->\n\n"
            "### 3.3 Next\n",
            encoding="utf-8",
        )
    return tmp_path


def _simple() -> list[dict]:
    return [
        {"path": "system", "owner": "system", "purpose": "prose and contracts",
         "children": [
             {"path": "system/contracts", "purpose": "declarations"},
             {"path": "system/adr", "purpose": "decision records"},
         ]},
        {"path": "tools", "owner": "tools", "purpose": "the CLI"},
    ]


# ---- the assumption everything rests on -------------------------------------

def test_render_is_idempotent(tmp_path):
    root = _repo(tmp_path, directories=_simple(), tree=["tools"])
    contract = tc.load(root)
    first = tc.render(root, contract)
    assert tc.render(root, contract) == first

    assert tc.write_block(root, contract) is True
    assert tc.write_block(root, contract) is False, "a second write changed the file"
    assert tc.block_is_current(root, contract)


def test_the_rendered_block_is_what_the_checker_compares(tmp_path):
    root = _repo(tmp_path, directories=_simple(), tree=["tools"])
    contract = tc.load(root)
    tc.write_block(root, contract)
    assert "STALE-BLOCK" not in _codes(tc.check(root))


def test_a_hand_edited_block_is_stale(tmp_path):
    """The block is derived. Editing it is the one thing that must not work."""
    root = _repo(tmp_path, directories=_simple(), tree=["tools"])
    contract = tc.load(root)
    tc.write_block(root, contract)
    path = root / tc.ARCHITECTURE_RELATIVE
    path.write_text(
        path.read_text(encoding="utf-8").replace("the CLI", "something else"),
        encoding="utf-8")
    assert "STALE-BLOCK" in _codes(tc.check(root))


def test_a_missing_marker_is_reported_not_ignored(tmp_path):
    root = _repo(tmp_path, directories=_simple(), tree=["tools"], architecture=False)
    (root / tc.ARCHITECTURE_RELATIVE).write_text("# Architecture\n\nNo markers.\n",
                                                 encoding="utf-8")
    issues = tc.check(root)
    assert "STALE-BLOCK" in _codes(issues)
    assert any("tree:begin" in i.message for i in issues)


# ---- deny by default --------------------------------------------------------

def test_an_undeclared_directory_is_an_error(tmp_path):
    root = _repo(tmp_path, directories=_simple(), tree=["tools", "operations"])
    issues = tc.check(root)
    assert "UNDECLARED" in _codes(issues)
    assert any(i.path == "operations" for i in issues if i.code == "UNDECLARED")


def test_a_declared_directory_that_is_absent_is_an_error(tmp_path):
    directories = _simple() + [{"path": "records", "owner": "records",
                                "purpose": "registries"}]
    root = _repo(tmp_path, directories=directories, tree=["tools"])
    issues = tc.check(root)
    assert "MISSING" in _codes(issues)
    assert any("records" in i.message for i in issues if i.code == "MISSING")


def test_a_declared_directory_with_no_purpose_is_an_error(tmp_path):
    directories = _simple() + [{"path": "mystery", "owner": "nobody"}]
    root = _repo(tmp_path, directories=directories, tree=["tools", "mystery"])
    issues = tc.check(root)
    assert "UNDOCUMENTED" in _codes(issues)
    assert any(i.path == "mystery" for i in issues if i.code == "UNDOCUMENTED")


def test_depth_is_per_entry_so_an_undeclared_interior_is_not_checked(tmp_path):
    """`knowledge/notes/<domain>/` grows with authoring and answers to its own
    rules. A contract that policed every level would either forbid ordinary
    work or be edited into meaninglessness."""
    root = _repo(tmp_path, directories=_simple(),
                 tree=["tools", "tools/hooks", "tools/hooks/deeper"])
    assert "UNDECLARED" not in _codes(tc.check(root))


def test_residue_is_never_undeclared(tmp_path):
    root = _repo(tmp_path, directories=_simple(),
                 tree=["tools", "__pycache__", "thing.egg-info"])
    assert "UNDECLARED" not in _codes(tc.check(root))


# ---- hidden entries ---------------------------------------------------------

def test_an_undeclared_hidden_directory_is_an_error(tmp_path):
    root = _repo(tmp_path, directories=_simple(), tree=["tools", ".secret"])
    issues = tc.check(root)
    assert any(i.path == ".secret" for i in issues if i.code == "UNDECLARED")


def test_a_declared_hidden_directory_is_accepted(tmp_path):
    root = _repo(
        tmp_path, directories=_simple(), tree=["tools", ".github"],
        hidden={"tracked": [{"path": ".github", "purpose": "CI"}]},
    )
    assert "UNDECLARED" not in _codes(tc.check(root))


def test_an_ephemeral_entry_git_does_not_ignore_is_an_error(tmp_path):
    """A cache that stops being ignored is a cache about to be committed."""
    root = _repo(
        tmp_path, directories=_simple(), tree=["tools", ".cache"],
        hidden={"ephemeral": [{"path": ".cache", "purpose": "a cache"}]},
    )
    assert "UNIGNORED" in _codes(tc.check(root))


def test_a_self_ignoring_cache_is_accepted(tmp_path):
    """pytest and ruff each write a nested .gitignore of `*`, so the directory
    itself is not ignored while everything in it is. Probing only the directory
    would report both caches as about to be committed, on every run, forever."""
    import subprocess

    root = _repo(
        tmp_path, directories=_simple(), tree=["tools", ".pytest_cache"],
        hidden={"ephemeral": [{"path": ".pytest_cache", "purpose": "pytest cache"}]},
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".pytest_cache" / ".gitignore").write_text("*\n", encoding="utf-8")
    assert "UNIGNORED" not in _codes(tc.check(root))


# ---- no declaration at all --------------------------------------------------

def test_a_repository_with_no_contract_is_not_a_violation(tmp_path):
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    assert tc.check(tmp_path) == []


def test_the_check_is_silent_where_an_anchor_is_missing(tmp_path):
    """The gate that stops a fixture from being audited as if it were the system.

    Getting this wrong is not a small bug: `mini_repo` copies system/contracts/
    wholesale, so the contract is present while nearly nothing it declares is,
    and the first version of this checker failed 112 tests at once.
    """
    root = _repo(tmp_path, directories=_simple(), tree=["tools"])
    (root / "tools" / "learning_os").rmdir()
    assert tc.check(root) == []


def test_the_tree_check_is_silent_in_a_synthetic_repo(mini_repo):
    """`mini_repo` copies the real system/contracts/, so the declaration is
    present while almost nothing it declares is. The same trap the perimeter
    checker had; here the empty-contract guard is what avoids it."""
    assert tc.check(mini_repo) == []


# ---- the live half ----------------------------------------------------------

@pytest.mark.full_repo
def test_the_live_tree_matches_its_contract():
    issues = tc.check(ROOT)
    assert issues == [], "\n".join(str(i) for i in issues)


@pytest.mark.full_repo
def test_every_top_level_directory_on_disk_is_declared():
    declared = {e.path for e in tc.load(ROOT).directories if e.path}
    contract = tc.load(ROOT)
    hidden = contract.hidden_names()
    on_disk = {
        p.name for p in ROOT.iterdir()
        if p.is_dir() and not tc._is_residue(p.name, contract)
    } - hidden
    assert on_disk == declared, (
        f"undeclared: {sorted(on_disk - declared)}; "
        f"declared but absent: {sorted(declared - on_disk)}"
    )


@pytest.mark.full_repo
def test_the_architecture_block_regenerates_byte_identically():
    """The acceptance criterion, stated as a test: the prose is a projection."""
    contract = tc.load(ROOT)
    assert tc.block_is_current(ROOT, contract), (
        "run `python tools/tree_contract.py --write`"
    )


@pytest.mark.full_repo
def test_the_block_names_contracts_instead_of_listing_their_files():
    """R3. The old block hand-listed system/*.md and generated/*, which is why
    it rotted; the projection names the contract that owns each index."""
    block = tc.current_block(ROOT)
    assert "normative-corpus.yaml" in block
    assert "manifest-contract.yaml" in block
    for document in ("PHILOSOPHY.md", "WORKFLOWS.md", "ACCEPTANCE-TESTS.md"):
        assert document not in block, (
            f"{document} is enumerated in the tree block; the corpus indexes it"
        )
