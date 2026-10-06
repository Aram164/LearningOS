#!/usr/bin/env python3
"""Capture one world for captured-world identity (PLAN 1.4, SPEC §6).

``capture_world.py --root ROOT --out DIR`` copies the authored and
operational data (``DATA_ROOTS`` plus ``operations/``) out of ROOT's working
tree, pins every copied byte, records the Git and clock observations the
projection reads, and builds the reference material inventory. Revision-owned
contracts (``system/``) are deliberately not captured: each compared revision
keeps its own bytes. Never writes inside ROOT.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.fingerprint import DATA_ROOTS  # noqa: E402

WORLD_DATA_ROOTS = tuple(DATA_ROOTS) + ("operations",)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="repository root to capture")
    parser.add_argument("--out", required=True, help="directory to write the world to")
    return parser


def _fail(note: str) -> int:
    print(f"capture_world: {note}", file=sys.stderr)
    return 2


def _digest_tree(data_dir: Path) -> dict[str, str]:
    """Map POSIX relative path to sha256 hex for every file under data_dir.

    A symlink hashes its link target string, so the pin is self-contained:
    retargeting the link breaks the pin without reading outside the world.
    """
    found: dict[str, str] = {}
    for path in sorted(data_dir.rglob("*")):
        if path.is_symlink():
            rel = path.relative_to(data_dir).as_posix()
            found[rel] = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        elif path.is_file():
            rel = path.relative_to(data_dir).as_posix()
            found[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=120, env=env,
    )


def _capture_observations(root: Path) -> dict:
    """The §4 observation object, read live with any override disabled."""
    from learning_os import githistory, observations

    saved = os.environ.pop(observations.OVERRIDE_ENV, None)
    try:
        head = githistory.read_history(root, "-1", "--format=%H").strip() or None
        head_time = githistory.read_history(root, "-1", "--format=%cI").strip() or None
        dates = githistory._walk(os.path.abspath(root), "%cs")
        timestamps = githistory._walk(os.path.abspath(root), "%ct")
        now = observations.now().isoformat()
    finally:
        if saved is not None:
            os.environ[observations.OVERRIDE_ENV] = saved
    return {
        "now": now,
        "git": {
            "head": head, "head_time": head_time,
            "dates": dates, "timestamps": timestamps,
        },
    }


def _capture_meta(root: Path) -> dict:
    """ROOT's HEAD, a hash of its dirty status, and the dirty system/ paths."""
    head_proc = _git(root, "rev-parse", "--verify", "--quiet", "HEAD")
    head = head_proc.stdout.strip() or None
    status_proc = _git(root, "status", "--porcelain")
    porcelain = status_proc.stdout if status_proc.returncode == 0 else ""
    dirty_system: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        arrow = path.rfind(" -> ")
        if arrow >= 0:
            path = path[arrow + 4:]
        if path == "system" or path.startswith("system/"):
            dirty_system.append(path)
    return {
        "root_head": head,
        "dirty_status_sha256": "sha256:" + hashlib.sha256(
            porcelain.encode("utf-8")).hexdigest(),
        "dirty_system_paths": sorted(dirty_system),
    }


def _archive_head(root: Path, probe: Path) -> str | None:
    """Extract HEAD's tools/ and system/ into the probe; None on success."""
    listed = _git(root, "ls-tree", "--name-only", "HEAD")
    if listed.returncode != 0:
        return f"cannot list HEAD: {listed.stderr.strip()}"
    names = set(listed.stdout.split())
    wanted = [name for name in ("tools", "system") if name in names]
    if not wanted:
        return "HEAD contains neither tools/ nor system/"
    archived = subprocess.run(
        ["git", "-C", str(root), "archive", "HEAD", *wanted],
        capture_output=True, timeout=300,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if archived.returncode != 0:
        return f"cannot archive HEAD: {archived.stderr.decode('utf-8', 'replace').strip()}"
    with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as tar:
        tar.extractall(path=probe, filter="data")
    return None


def _all_routes(repo) -> list[dict]:
    """Every route in every module source map, built as unit_routes builds."""
    from learning_os.route_identity import route_with_identity

    rows: list[dict] = []
    for module_id in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[module_id]
        sources = source_map.get("sources", [])
        if not isinstance(sources, list):
            continue
        for entry in sources:
            if not isinstance(entry, dict):
                continue
            routes = entry.get("unit_routes", [])
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, dict):
                    continue
                rows.append({
                    **route_with_identity(
                        module_id, str(entry.get("source_id") or ""), route),
                    "source_id": entry.get("source_id"),
                })
    return rows


def _material_entry(materials_root: Path, rel: str, exists: bool) -> dict:
    full = materials_root / rel
    link = os.readlink(full) if full.is_symlink() else None
    digest = None
    if exists and full.is_file():
        digest = hashlib.sha256(full.read_bytes()).hexdigest()
    return {"path": rel, "exists": exists, "symlink": link, "sha256": digest}


def _capture_materials(root: Path, out: Path) -> tuple[list[dict] | None, str | None]:
    """The reference inventory (SPEC §6, amendments (ah) and (n))."""
    from learning_os.loader import load_repo
    from learning_os.materials_resolution import (
        MATERIAL_SCHEME,
        material_location,
        resolve_route_material_files,
    )
    from learning_os.rules.materials import _uris_in

    data_dir = out / "data"
    probe = out / "probe"
    link = out / "materials"
    if link.exists() or link.is_symlink():
        return None, f"refusing to overwrite {link}"
    probe.mkdir(parents=True)
    try:
        for child in sorted(data_dir.iterdir()):
            target = probe / child.name
            if child.is_symlink() or child.is_file():
                if child.is_symlink():
                    target.symlink_to(os.readlink(child))
                else:
                    shutil.copy2(child, target)
            elif child.is_dir():
                shutil.copytree(child, target, symlinks=True, copy_function=shutil.copy2)
        problem = _archive_head(root, probe)
        if problem is not None:
            return None, problem
        link.symlink_to(root.parent / "materials")
        repo = load_repo(probe)
        # The link itself, unresolved: resolved inventory paths are joined
        # under learningos_root/"materials", which is this link exactly.
        materials_root = link

        payloads: set[str] = set()
        for rel_root in DATA_ROOTS:
            base = probe / rel_root
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                blob = path.read_bytes().decode("utf-8", errors="replace")
                if "material://" in blob:
                    payloads |= _uris_in(blob)
        payloads.discard("")

        entries: dict[str, dict] = {}
        for payload in sorted(payloads):
            location = material_location(repo, MATERIAL_SCHEME + payload)
            material_path = location.get("material_path")
            if not isinstance(material_path, str):
                continue
            prefix = "materials/"
            if not material_path.startswith(prefix):
                continue
            rel = material_path[len(prefix):]
            entries.setdefault(
                rel, _material_entry(
                    materials_root, rel,
                    location.get("material_exists") is True))
        for route in _all_routes(repo):
            for found in resolve_route_material_files(repo, route):
                try:
                    rel = found.path.relative_to(materials_root).as_posix()
                except ValueError:
                    continue
                entries.setdefault(rel, _material_entry(materials_root, rel, True))
        if payloads and not entries:
            return None, "the world references materials but the inventory is empty"
        return [entries[key] for key in sorted(entries)], None
    finally:
        shutil.rmtree(probe, ignore_errors=True)
        if link.is_symlink():
            link.unlink()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    if not root.is_dir():
        return _fail(f"root is not a directory: {root}")
    if out == root or root in out.parents:
        return _fail(f"refusing to write the world inside the root: {out}")
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        return _fail(f"refusing to write into a non-empty directory: {out}")

    data_dir = out / "data"
    data_dir.mkdir()
    for rel_root in WORLD_DATA_ROOTS:
        base = root / rel_root
        if base.is_symlink() or not base.is_dir():
            continue
        shutil.copytree(base, data_dir / rel_root, symlinks=True,
                        copy_function=shutil.copy2)
    (out / "data-digest.json").write_text(
        json.dumps(_digest_tree(data_dir), indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (out / "observations.json").write_text(
        json.dumps(_capture_observations(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    entries, problem = _capture_materials(root, out)
    if problem is not None:
        return _fail(problem)
    assert entries is not None
    (out / "materials.json").write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "meta.json").write_text(
        json.dumps(_capture_meta(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(f"captured world from {root} to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
