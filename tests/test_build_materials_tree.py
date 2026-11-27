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
    assert "destination appeared after the preflight" in err
    # Nothing nested inside the competitor, and it kept its own bytes.
    assert sorted(p.name for p in competitor.iterdir()) == ["theirs.txt"]
    after = _snapshot(materials)
    assert {k: v for k, v in after.items() if not k.startswith("software")} == before
    for slug in MOVED:
        assert (materials / slug / "notes.txt").is_file(), slug
        assert (materials / ".flat" / f"source-{slug}").resolve() == (materials / slug).resolve()
    assert not any(materials.rglob("SOURCES.md"))


def test_a_failed_move_puts_earlier_moves_back_and_keeps_the_aliases(
        tmp_path: Path, monkeypatch, capsys):
    builder = _builder()
    materials = _fixture(tmp_path)
    _with_prior_aliases(materials)
    before = _snapshot(materials)
    original_rename = builder.os.rename
    calls = []

    def second_move_fails(src, dst):
        calls.append((Path(src), Path(dst)))
        if len(calls) == 2:
            raise OSError("simulated failure on the second move")
        return original_rename(src, dst)

    monkeypatch.setattr(builder.os, "rename", second_move_fails)
    assert builder.main(["--materials-root", str(materials), "--apply"]) == 1
    monkeypatch.undo()
    err = capsys.readouterr().err
    assert "simulated failure on the second move" in err
    assert "moved 1 folder(s) back, .flat is unchanged" in err
    assert _snapshot(materials) == before
    for slug in MOVED:
        assert (materials / ".flat" / f"source-{slug}").resolve() == (materials / slug).resolve()
