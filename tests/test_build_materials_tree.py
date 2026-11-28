"""The materials tree builder plans by default and acts only with --apply (#113).

The builder reorganizes the external materials tree — the one tree with no
git history — so the bare command prints the plan and writes nothing. Every
test here runs against a fixture tree; the real materials tree is never
touched.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "build_materials_tree.py"

#: Two real PLACEMENT slugs with distinct parents, plus one already placed.
MOVED = {
    "abbott-understanding-analysis": "mathematics/analysis",
    "progit": "software/tooling",
}
PLACED = {"grieser-analysis1": "mathematics/analysis"}


def _fixture(tmp_path: Path) -> Path:
    materials = tmp_path / "materials"
    for slug in MOVED:
        folder = materials / slug
        folder.mkdir(parents=True)
        (folder / "notes.txt").write_text(f"{slug}\n", encoding="utf-8")
    for slug, parent in PLACED.items():
        folder = materials / parent / slug
        folder.mkdir(parents=True)
        (folder / "notes.txt").write_text(f"{slug}\n", encoding="utf-8")
    (materials / "source-unmapped-stray").mkdir(parents=True)
    return materials


def _snapshot(tree: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(tree.rglob("*")):
        if path.is_symlink():
            out[str(path.relative_to(tree))] = f"link->{path.readlink()}"
        elif path.is_file():
            out[str(path.relative_to(tree))] = hashlib.sha256(
                path.read_bytes()).hexdigest()
    return out


def _run(*args: str, materials: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), "--materials-root", str(materials), *args],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180)


def test_dry_run_is_the_default_and_writes_nothing(tmp_path: Path):
    materials = _fixture(tmp_path)
    before = _snapshot(materials)
    proc = _run(materials=materials)
    assert proc.returncode == 0, f"--- stderr ---\n{proc.stderr}"
    assert _snapshot(materials) == before, "the default plan run wrote"
    for slug in MOVED:
        assert slug in proc.stdout, (
            f"the plan never mentions {slug}\n--- stdout ---\n{proc.stdout}")


def test_apply_moves_folders_rebuilds_flat_and_sources(tmp_path: Path):
    materials = _fixture(tmp_path)
    proc = _run("--apply", materials=materials)
    assert proc.returncode == 0, f"--- stderr ---\n{proc.stderr}"
    for slug, parent in MOVED.items():
        target = materials / parent / slug
        assert (target / "notes.txt").is_file(), f"{slug} was not moved"
        assert not (materials / slug).exists(), f"{slug} still at the root"
        link = materials / ".flat" / f"source-{slug}"
        assert link.is_symlink(), f".flat link missing for {slug}"
    for parent in {*MOVED.values(), *PLACED.values()}:
        assert (materials / parent / "SOURCES.md").is_file(), (
            f"SOURCES.md missing in {parent}")
    assert "unmapped-stray" in proc.stdout, (
        f"the stray drew no warning\n--- stdout ---\n{proc.stdout}")
    # Idempotent: a second apply is a clean no-op report, not a second move.
    again = _run("--apply", materials=materials)
    assert again.returncode == 0, f"--- stderr ---\n{again.stderr}"


# ---- 2D CL-11: a competing destination never absorbs a source -------------

def _builder():
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_materials_tree", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _with_prior_aliases(materials: Path) -> None:
    """The compat layer an earlier apply left, pointing at today's locations."""
    flat = materials / ".flat"
    flat.mkdir()
    for slug in MOVED:
        (flat / f"source-{slug}").symlink_to(Path("..") / slug)


def test_a_destination_that_appears_after_the_preflight_is_refused(
        tmp_path: Path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    competitor = materials / MOVED["progit"] / "progit"
    original_mkdir = Path.mkdir

    def mkdir_then_compete(self, *args, **kwargs):
        original_mkdir(self, *args, **kwargs)
        if self == competitor.parent and not competitor.exists():
            original_mkdir(competitor)
            (competitor / "theirs.txt").write_text("competing\n", encoding="utf-8")

    monkeypatch.setattr(Path, "mkdir", mkdir_then_compete)
    before = {k: v for k, v in _snapshot(materials).items()
              if not k.startswith("software")}
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    monkeypatch.undo()
    err = capsys.readouterr().err
    assert "cannot apply materials layout" in err and str(competitor) in err
    # Nothing nested inside the competitor, and it kept its own bytes.
    assert sorted(p.name for p in competitor.iterdir()) == ["theirs.txt"]
    after = _snapshot(materials)
    assert {k: v for k, v in after.items() if not k.startswith("software")} == before
    for slug in MOVED:
        assert (materials / slug / "notes.txt").is_file(), slug
        assert (materials / ".flat" / f"source-{slug}").resolve() == (materials / slug).resolve()
    assert not any(materials.rglob("SOURCES.md"))


def _assert_occupied_destination_refused(materials: Path, competitor: Path,
                                         registered: Path, before: dict) -> None:
    for args in ((), ("--apply",)):
        proc = _run(*args, materials=materials)
        assert proc.returncode == 1, (args, proc.stdout, proc.stderr)
        assert "refusing an occupied destination" in proc.stderr, proc.stderr
        assert str(competitor) in proc.stderr and str(registered) in proc.stderr
        # Nothing moved, no alias changed, the occupant kept its bytes.
        assert _snapshot(materials) == before, args
    link = materials / ".flat" / "source-progit"
    assert link.resolve() == registered.resolve()
    assert sorted(p.name for p in competitor.iterdir()) == ["partial.part"]


def test_a_destination_occupied_before_apply_is_refused_and_keeps_the_alias(tmp_path: Path):
    """2D CL-11: an occupant already at the mapped place is never adopted.

    The registered folder is still at the root, its alias points there, and
    something else (an interrupted copy) already sits where PLACEMENT asks.
    """
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    competitor = materials / MOVED["progit"] / "progit"
    competitor.mkdir(parents=True)
    (competitor / "partial.part").write_text("half a copy\n", encoding="utf-8")
    _assert_occupied_destination_refused(
        materials, competitor, materials / "progit", _snapshot(materials))


def test_an_occupied_destination_after_a_placement_edit_keeps_the_registered_folder(
        tmp_path: Path):
    """The documented flow "edit PLACEMENT, re-run" with the new place occupied.

    The alias names the registered folder at its old nested place; the root
    holds no copy, so only the alias tells the two folders apart.
    """
    materials = tmp_path / "materials"
    registered = materials / "software" / "git-old" / "progit"
    registered.mkdir(parents=True)
    (registered / "progit.pdf").write_text("the book\n", encoding="utf-8")
    flat = materials / ".flat"
    flat.mkdir()
    (flat / "source-progit").symlink_to(Path("..") / "software" / "git-old" / "progit")
    competitor = materials / MOVED["progit"] / "progit"
    competitor.mkdir(parents=True)
    (competitor / "partial.part").write_text("half a copy\n", encoding="utf-8")
    _assert_occupied_destination_refused(materials, competitor, registered,
                                         _snapshot(materials))


def test_a_failed_move_puts_earlier_moves_back_and_keeps_the_aliases(
        tmp_path: Path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    before = _snapshot(materials)
    original_rename = builder.rename_noreplace
    calls = []

    def second_move_fails(src, dst):
        calls.append((Path(src), Path(dst)))
        if len(calls) == 2:
            raise OSError("simulated failure on the second move")
        return original_rename(src, dst)

    monkeypatch.setattr(builder, "rename_noreplace", second_move_fails)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    monkeypatch.undo()
    err = capsys.readouterr().err
    assert "simulated failure on the second move" in err
    assert "moved 1 folder(s) back" in err
    assert _snapshot(materials) == before
    for slug in MOVED:
        assert (materials / ".flat" / f"source-{slug}").resolve() == (materials / slug).resolve()


def test_an_empty_destination_created_at_rename_is_preserved(tmp_path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    before = _snapshot(materials)
    competitor = materials / MOVED["progit"] / "progit"
    original_rename = builder.rename_noreplace
    competitor_inode = None

    def compete_at_rename(source, destination):
        nonlocal competitor_inode
        if destination == competitor:
            destination.mkdir()
            competitor_inode = destination.stat().st_ino
        original_rename(source, destination)

    monkeypatch.setattr(builder, "rename_noreplace", compete_at_rename)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    assert competitor_inode is not None
    assert competitor.stat().st_ino == competitor_inode
    assert list(competitor.iterdir()) == []
    assert "moved 1 folder(s) back" in capsys.readouterr().err
    assert _snapshot(materials) == before


def test_a_later_parent_creation_failure_restores_the_existing_layout(tmp_path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    before = _snapshot(materials)
    original_mkdir = Path.mkdir

    def fail_later_parent(path, *args, **kwargs):
        if path == materials / MOVED["progit"]:
            raise PermissionError("simulated failure creating second destination parent")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_later_parent)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    err = capsys.readouterr().err
    assert "simulated failure creating second destination parent" in err
    assert "moved 1 folder(s) back" in err
    assert _snapshot(materials) == before


def test_alias_publication_failure_restores_moves_and_all_prior_links(tmp_path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    before = _snapshot(materials)
    late_alias = materials / ".flat" / "source-progit"
    replaced_alias = materials / ".flat" / "source-abbott-understanding-analysis"
    original_replace = builder.os.replace

    def fail_late_alias(source, destination):
        if destination == late_alias:
            assert replaced_alias.readlink() != Path("..") / "abbott-understanding-analysis"
            raise OSError("simulated failure publishing the last alias")
        original_replace(source, destination)

    monkeypatch.setattr(builder.os, "replace", fail_late_alias)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    err = capsys.readouterr().err
    assert "simulated failure publishing the last alias" in err
    assert "moved 2 folder(s) back" in err
    assert _snapshot(materials) == before
    for slug in MOVED:
        link = materials / ".flat" / f"source-{slug}"
        assert link.resolve(strict=True) == (materials / slug).resolve()


def test_failed_first_apply_does_not_publish_an_empty_alias_root(tmp_path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    before = _snapshot(materials)
    flat = materials / ".flat"
    original_rename = builder.rename_noreplace

    def fail_alias_root(source, destination):
        if destination == flat:
            assert list(source.glob("source-*"))
            raise OSError("simulated failure publishing the first alias root")
        return original_rename(source, destination)

    monkeypatch.setattr(builder, "rename_noreplace", fail_alias_root)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    assert "simulated failure publishing the first alias root" in capsys.readouterr().err
    assert not flat.exists()
    assert not list(materials.glob(".flat-tmp-*"))
    assert _snapshot(materials) == before
