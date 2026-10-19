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
