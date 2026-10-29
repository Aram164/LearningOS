"""Captured-world identity tools (SPEC §6, PLAN step 1.4).

Every case captures a ``rich_world`` fixture only; the live tree is never
captured. Comparisons run the committed ``tools/compare_world.py`` against
scratch worktrees, scratch materials copies, and scratch clones.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
CAPTURE = REPO_ROOT / "tools" / "capture_world.py"

FIXTURE_NOW = "2026-10-01T09:00:00+02:00"


@pytest.fixture(autouse=True)
def _berlin_clock(monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    yield
    time.tzset()


def _child_env() -> dict:
    env = dict(os.environ)
    env["TZ"] = "Europe/Berlin"
    return env


def _git(root: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True,
        timeout=300, env=env or _child_env(),
    )
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr[-2000:]}"
    return proc


def _build_committed_world(container: Path) -> Path:
    from conftest import build_mini_repo
    from scenario_fixtures import rich_world

    root = build_mini_repo(container)
    rich_world(root)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@local")
    _git(root, "add", "-A")
    dated = dict(_child_env(), GIT_AUTHOR_DATE=FIXTURE_NOW,
                 GIT_COMMITTER_DATE=FIXTURE_NOW)
    _git(root, "commit", "-qm", "fixture", env=dated)
    return root


def _capture(root: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CAPTURE), "--root", str(root), "--out", str(out)],
        capture_output=True, text=True, timeout=300, env=_child_env(), cwd=REPO_ROOT,
    )


def _compare(cwd: Path, world: Path, baseline: str, candidate: str,
             materials: Path, work_dir: Path) -> subprocess.CompletedProcess:
    tool = cwd / "tools" / "compare_world.py"
    assert tool.is_file(), f"compare tool is missing from {cwd}"
    return subprocess.run(
        [sys.executable, str(tool), "--world", str(world),
         "--baseline", baseline, "--candidate", candidate,
         "--materials", str(materials), "--work-dir", str(work_dir)],
        capture_output=True, text=True, timeout=600, env=_child_env(), cwd=cwd,
    )


def _report(proc: subprocess.CompletedProcess) -> dict:
    assert proc.returncode in (0, 1), proc.stderr[-2000:]
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """One captured rich_world, shared read-only by every case in this file."""
    container = tmp_path_factory.mktemp("world-container")
    root = _build_committed_world(container)
    out = tmp_path_factory.mktemp("world") / "world"
    proc = _capture(root, out)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert not (out / "probe").exists()
    assert not (out / "materials").exists() and not (out / "materials").is_symlink()
    return {"root": root, "dir": out,
            "materials": root.parent / "materials"}


def _materials_copy(world: dict, dest: Path) -> Path:
    target = dest / "materials"
    shutil.copytree(world["materials"], target, symlinks=True)
    return target


def test_self_compare_exits_zero(world: dict, tmp_path: Path):
    proc = _compare(REPO_ROOT, world["dir"], "HEAD", "HEAD",
                    _materials_copy(world, tmp_path), tmp_path / "runs")
    assert proc.returncode == 0, proc.stderr[-2000:]
    report = json.loads(proc.stdout)
    assert report["identical"] is True
    assert report["differences"] == []
    assert report["semantic"]["equal"] is True
    assert report["contract"]["accepted"] is True
    assert report["baseline"]["checks"] == report["candidate"]["checks"]


def test_tampered_world_data_exits_two(world: dict, tmp_path: Path):
    tampered = tmp_path / "world"
    shutil.copytree(world["dir"], tampered, symlinks=True)
    target = tampered / "data" / "knowledge" / "concepts.yaml"
    blob = bytearray(target.read_bytes())
    blob[0] ^= 0x01
    target.write_bytes(bytes(blob))
    proc = _compare(REPO_ROOT, tampered, "HEAD", "HEAD",
                    _materials_copy(world, tmp_path), tmp_path / "runs")
    assert proc.returncode == 2
    assert "world corrupted" in proc.stderr


def _scratch_clone(dest: Path) -> Path:
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--local", str(REPO_ROOT), str(dest)],
        capture_output=True, text=True, timeout=300, env=_child_env(), cwd=parent,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    _git(dest, "config", "user.name", "S07 Test")
    _git(dest, "config", "user.email", "s07-test@local")
    return dest


def test_candidate_projection_change_names_manifest_path(world: dict, tmp_path: Path):
    clone = _scratch_clone(tmp_path / "clone")
    baseline = _git(clone, "rev-parse", "HEAD").stdout.strip()
    tallies = clone / "tools" / "learning_os" / "derive" / "projection" / "projection" / "tallies.py"
    text = tallies.read_text(encoding="utf-8")
    old = '"inbox_items": inbox_items,'
    assert text.count(old) == 1
    tallies.write_text(text.replace(old, '"inbox_items": inbox_items + 1,'),
                       encoding="utf-8")
    _git(clone, "commit", "-qam", "S07 test: shift the projected inbox count")
    candidate = _git(clone, "rev-parse", "HEAD").stdout.strip()
    proc = _compare(clone, world["dir"], baseline, candidate,
                    _materials_copy(world, tmp_path), tmp_path / "runs")
    assert proc.returncode == 1, proc.stderr[-2000:]
    report = json.loads(proc.stdout)
    assert report["identical"] is False
    assert "manifest:counts.inbox_items" in report["differences"]
    (row,) = [row for row in report["semantic"]["differences"]
              if row["path"] == "counts.inbox_items"]
    assert row["candidate"] == row["baseline"] + 1


def test_materials_inventory_has_a_present_entry(world: dict):
    entries = json.loads((world["dir"] / "materials.json").read_text(encoding="utf-8"))
    assert any(entry.get("exists") is True for entry in entries), entries


def _first_present_material(world: dict) -> str:
    entries = json.loads((world["dir"] / "materials.json").read_text(encoding="utf-8"))
    for entry in entries:
        full = world["materials"] / entry["path"]
        if entry.get("exists") is True and full.is_file() and not full.is_symlink():
            return entry["path"]
    raise AssertionError(f"no present regular material in {entries}")


def test_changed_material_exits_two(world: dict, tmp_path: Path):
    rel = _first_present_material(world)
    materials = _materials_copy(world, tmp_path)
    target = materials / rel
    blob = bytearray(target.read_bytes())
    blob[len(blob) // 2] ^= 0x01
    target.write_bytes(bytes(blob))
    proc = _compare(REPO_ROOT, world["dir"], "HEAD", "HEAD",
                    materials, tmp_path / "runs")
    assert proc.returncode == 2, proc.stdout[-2000:]
    assert rel in proc.stderr


def test_deleted_material_exits_two(world: dict, tmp_path: Path):
    rel = _first_present_material(world)
    materials = _materials_copy(world, tmp_path)
    (materials / rel).unlink()
    proc = _compare(REPO_ROOT, world["dir"], "HEAD", "HEAD",
                    materials, tmp_path / "runs")
    assert proc.returncode == 2, proc.stdout[-2000:]
    assert rel in proc.stderr


def _default_materials_dir() -> Path:
    """The materials tree ``compare_world`` uses when ``--materials`` is omitted."""
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=60, env=_child_env(),
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    toplevel = Path(proc.stdout.strip()).resolve()
    return (toplevel.parent / "materials").resolve()


def test_default_materials_compare_of_fixture_world_exits_two(
        world: dict, tmp_path: Path):
    """ND1 resolution: the verbatim default-``--materials`` run exits 2.

    A ``rich_world`` references synthetic fixture bytes that the pair's real
    materials tree cannot contain, so SPEC §6 step 3 aborts with
    "materials differ". That exit 2 is correct tool behavior, not a failure;
    the identity claim is proven by the own-materials variant below.
    """
    if not _default_materials_dir().is_dir():
        pytest.skip("this checkout has no default <toplevel>/../materials tree")
    tool = REPO_ROOT / "tools" / "compare_world.py"
    # ``--materials`` is deliberately omitted (the default under test); only
    # the work directory is pinned under tmp so pytest leaves no residue in
    # the pair scratch.
    proc = subprocess.run(
        [sys.executable, str(tool), "--world", str(world["dir"]),
         "--baseline", "HEAD", "--candidate", "HEAD",
         "--work-dir", str(tmp_path / "runs")],
        capture_output=True, text=True, timeout=600, env=_child_env(),
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 2, proc.stdout[-2000:]
    assert "materials differ" in proc.stderr


def test_own_materials_tool_only_change_compare_exits_zero(
        world: dict, tmp_path: Path):
    """ND1 resolution: a tool-only change is identical under the world's own materials.

    Topology-independent: the baseline and candidate are SHAs pinned by this
    test itself (parent and child of one scratch commit with a tool-only
    diff), never the floating ``main``/``HEAD`` refs, so the identity claim
    holds on any checkout containing S07 no matter where ``main`` points.
    """
    clone = _scratch_clone(tmp_path / "clone")
    baseline = _git(clone, "rev-parse", "HEAD").stdout.strip()
    tool = clone / "tools" / "capture_world.py"
    assert tool.is_file(), "S07 content is missing from this checkout"
    with tool.open("a", encoding="utf-8") as handle:
        handle.write("# S07 test: a tool-only comment carries no projection.\n")
    _git(clone, "commit", "-qam", "S07 test: tool-only comment change")
    candidate = _git(clone, "rev-parse", "HEAD").stdout.strip()
    # Two different commits with two different trees; the projection must
    # still be identical, as with the S07 delta itself (tools/tests only).
    assert baseline != candidate
    proc = _compare(clone, world["dir"], baseline, candidate,
                    _materials_copy(world, tmp_path), tmp_path / "runs")
    assert proc.returncode == 0, proc.stderr[-2000:]
    report = json.loads(proc.stdout)
    assert report["identical"] is True
    assert report["differences"] == []
    assert report["baseline"]["revision"] == baseline
    assert report["candidate"]["revision"] == candidate


def test_contract_version_bump_without_transition_exits_one(world: dict, tmp_path: Path):
    clone = _scratch_clone(tmp_path / "clone")
    baseline = _git(clone, "rev-parse", "HEAD").stdout.strip()
    assert not (REPO_ROOT / "tests" / "architecture"
                / "contract-transitions.yaml").exists()
    old_schema = clone / "system" / "contracts" / "manifest-v16.schema.json"
    text = old_schema.read_text(encoding="utf-8")
    text = text.replace("manifest-v16.schema.json", "manifest-v17.schema.json")
    text = text.replace("atomic manifest v16", "atomic manifest v17")
    old_const = '"contract_version": {\n          "const": 16\n        }'
    assert text.count(old_const) == 1
    text = text.replace(old_const, '"contract_version": {\n          "const": 17\n        }')
    (clone / "system" / "contracts" / "manifest-v17.schema.json").write_text(
        text, encoding="utf-8")
    bumped = subprocess.run(
        [sys.executable, str(clone / "tools" / "manifest_contract.py"),
         "--bump", "--note", "S07 test: contract version bump"],
        capture_output=True, text=True, timeout=300, env=_child_env(), cwd=clone,
    )
    assert bumped.returncode == 0, bumped.stderr[-2000:]
    _git(clone, "add", "-A")
    _git(clone, "commit", "-qm", "S07 test: bump the manifest contract to v17")
    candidate = _git(clone, "rev-parse", "HEAD").stdout.strip()
    proc = _compare(clone, world["dir"], baseline, candidate,
                    _materials_copy(world, tmp_path), tmp_path / "runs")
    assert proc.returncode == 1, proc.stderr[-2000:]
    report = json.loads(proc.stdout)
    assert report["identical"] is False
    assert "contract:contract_version" in report["differences"]
    assert report["contract"]["baseline_version"] == 16
    # The candidate's own contract bytes survived tree construction: its
    # stamped version is the bumped one, and its metadata is self-consistent.
    assert report["candidate"]["contract_version"] == 17
    assert report["candidate"]["checks"] == {
        "contract_version": True, "schema_sha256": True, "snapshot_id": True}
    assert report["semantic"]["equal"] is True


def _comparison_tool():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "phase6_world_comparison", REPO_ROOT / "tools/compare_world.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("layout", ["legacy", "store"])
def test_each_revision_uses_its_own_fingerprint_module(tmp_path, layout):
    """A historical tree need not contain the candidate's package layout."""
    package = tmp_path / "tools/learning_os"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    if layout == "store":
        package = package / "store"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
    expected = "1" * 64
    (package / "fingerprint.py").write_text(
        f"def canonical_fingerprint(root):\n    return {expected!r}\n", encoding="utf-8")
    assert _comparison_tool()._side_fingerprint(tmp_path) == expected


def test_broken_current_fingerprint_does_not_fall_back_to_a_legacy_owner(tmp_path):
    """A present broken current owner fails closed even if a legacy one works."""
    package = tmp_path / "tools/learning_os"
    store = package / "store"
    store.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (store / "__init__.py").write_text("", encoding="utf-8")
    (package / "fingerprint.py").write_text(
        "def canonical_fingerprint(root):\n    return '1' * 64\n", encoding="utf-8")
    (store / "fingerprint.py").write_text(
        "raise ModuleNotFoundError('broken dependency')\n", encoding="utf-8")
    assert _comparison_tool()._side_fingerprint(tmp_path) is None
