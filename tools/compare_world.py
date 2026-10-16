#!/usr/bin/env python3
"""Compare two code revisions against one captured world (PLAN 1.4, SPEC §6).

``compare_world.py --world DIR --baseline SHA [--candidate SHA|WORKTREE]``
checks the world's integrity, builds each revision in a disposable worktree
with the world's data overlaid (each revision keeps its own ``system/``),
runs the projection under the world's observations, and compares the semantic
manifest bodies plus the publication metadata relationships. Exits 0 on
identity, 1 on any difference, 2 when the world, the materials, or the
invocation itself cannot be trusted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.store.fingerprint import DATA_ROOTS  # noqa: E402

WORLD_DATA_ROOTS = tuple(DATA_ROOTS) + ("operations",)

#: Timeout for one projection run, in seconds.
GENERATE_TIMEOUT = 600


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True, help="captured world directory")
    parser.add_argument("--baseline", required=True, help="baseline revision")
    parser.add_argument("--candidate", default="HEAD",
                        help="candidate revision, or WORKTREE for the working tree")
    parser.add_argument("--materials", default=None,
                        help="materials directory (default: <toplevel>/../materials)")
    parser.add_argument("--work-dir", default=None,
                        help="worktree parent (default: <toplevel>/../scratch/world-runs)")
    return parser


def _fail(note: str) -> int:
    print(f"compare_world: {note}", file=sys.stderr)
    return 2


def _digest_tree(data_dir: Path) -> dict[str, str]:
    """The capture-time pin function, mirrored from capture_world.py."""
    found: dict[str, str] = {}
    for path in sorted(data_dir.rglob("*")):
        if path.is_symlink():
            rel = path.relative_to(data_dir).as_posix()
            found[rel] = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        elif path.is_file():
            rel = path.relative_to(data_dir).as_posix()
            found[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=300, env=env,
    )


def _toplevel() -> Path | None:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.strip()).resolve()


def _verify_data(world: Path) -> str | None:
    """Recompute the world's pin; None means the bytes are intact."""
    data_dir = world / "data"
    digest_path = world / "data-digest.json"
    if not data_dir.is_dir():
        return "world has no data/"
    if not digest_path.is_file():
        return "world has no data-digest.json"
    try:
        pinned = json.loads(digest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"cannot read data-digest.json: {exc}"
    if not isinstance(pinned, dict):
        return "data-digest.json is not an object"
    live = _digest_tree(data_dir)
    for rel in sorted(set(pinned) | set(live)):
        if pinned.get(rel) != live.get(rel):
            if rel not in pinned:
                return f"unpinned file appeared: {rel}"
            if rel not in live:
                return f"pinned file is gone: {rel}"
            return f"pinned bytes changed: {rel}"
    return None


def _verify_materials(world: Path, link: Path) -> str | None:
    """Check every inventory entry under the materials link; None means match."""
    manifest_path = world / "materials.json"
    try:
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"cannot read materials.json: {exc}"
    if not isinstance(entries, list):
        return "materials.json is not a list"
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            return "materials.json holds a malformed entry"
        rel = entry["path"]
        full = link / rel
        actual_exists = full.exists()
        if actual_exists != (entry.get("exists") is True):
            return f"material {rel}: existence changed"
        actual_link = os.readlink(full) if full.is_symlink() else None
        if actual_link != entry.get("symlink"):
            return f"material {rel}: symlink target changed"
        actual_digest = None
        if full.is_file():
            actual_digest = hashlib.sha256(full.read_bytes()).hexdigest()
        if actual_digest != entry.get("sha256"):
            return f"material {rel}: bytes changed"
    return None


def _remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def _overlay_data(world: Path, tree: Path) -> None:
    """Replace the tree's data roots with the world's bytes (SPEC §6 step 2)."""
    data_dir = world / "data"
    for rel_root in WORLD_DATA_ROOTS:
        target = tree / rel_root
        if target.is_symlink() or target.exists():
            _remove_tree(target)
        source = data_dir / rel_root
        if source.is_symlink() or source.is_file():
            if source.is_symlink():
                target.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, target)
        elif source.is_dir():
            shutil.copytree(source, target, symlinks=True,
                            copy_function=shutil.copy2)


def _run_side(repo: Path, tree: Path, world: Path) -> tuple[dict | None, dict]:
    """Run the side's own projection; the manifest, plus the side's identity."""
    observations = str((world / "observations.json").resolve())
    env = dict(os.environ)
    env["LOS_OBSERVATIONS"] = observations
    env["TZ"] = "Europe/Berlin"
    generate = tree / "tools" / "generate.py"
    info: dict = {"generated": False, "generate_exit": None, "generate_tail": ""}
    if not generate.is_file():
        info["generate_tail"] = "tools/generate.py is missing"
        return None, info
    try:
        proc = subprocess.run(
            [sys.executable, str(generate), "--root", str(tree)],
            capture_output=True, text=True, timeout=GENERATE_TIMEOUT,
            env=env, cwd=tree,
        )
    except subprocess.TimeoutExpired:
        info["generate_tail"] = f"generation timed out after {GENERATE_TIMEOUT}s"
        return None, info
    info["generate_exit"] = proc.returncode
    tail = (proc.stderr.strip() + "\n" + proc.stdout.strip()).strip()
    info["generate_tail"] = "\n".join(tail.splitlines()[-5:])
    if proc.returncode != 0:
        return None, info
    info["generated"] = True
    manifest_path = tree / "generated" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        info["generated"] = False
        info["generate_tail"] = f"cannot read generated/manifest.json: {exc}"
        return None, info
    if not isinstance(manifest, dict):
        info["generated"] = False
        info["generate_tail"] = "generated/manifest.json is not an object"
        return None, info
    return manifest, info


_FINGERPRINT_SNIPPET = (
    "import sys",
    "sys.path.insert(0, sys.argv[1])",
    "from pathlib import Path",
    "from importlib import import_module",
    "owner = ('learning_os.store.fingerprint' if "
    "(Path(sys.argv[1]) / 'learning_os/store/fingerprint.py').is_file() "
    "else 'learning_os.fingerprint')",
    "canonical_fingerprint = import_module(owner).canonical_fingerprint",
    "print(canonical_fingerprint(Path(sys.argv[2])))",
)


def _side_fingerprint(tree: Path) -> str | None:
    """The side's own canonical fingerprint of its constructed tree."""
    env = dict(os.environ)
    env["TZ"] = "Europe/Berlin"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", "\n".join(_FINGERPRINT_SNIPPET),
             str(tree / "tools"), str(tree)],
            capture_output=True, text=True, timeout=300, env=env, cwd=tree,
        )
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _side_contract(tree: Path) -> tuple[dict | None, str | None]:
    """The side's own manifest-contract version and schema bytes identity."""
    import yaml

    contract_path = tree / "system" / "contracts" / "manifest-contract.yaml"
    try:
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"cannot read manifest-contract.yaml: {exc}"
    if not isinstance(contract, dict):
        return None, "manifest-contract.yaml is not a mapping"
    version = contract.get("contract_version")
    schema_rel = contract.get("schema_path")
    if not isinstance(version, int) or not isinstance(schema_rel, str):
        return None, "manifest-contract.yaml lacks contract_version/schema_path"
    schema_path = tree / schema_rel
    try:
        digest = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    except OSError as exc:
        return None, f"cannot read the manifest schema file: {exc}"
    return {"contract_version": version, "schema_sha256": f"sha256:{digest}"}, None


#: Marker for a value missing on one side of a semantic difference.
_ABSENT: dict = {"__absent__": True}


def _diff_paths(first, second, path: str, out: list[dict], cap: int = 10) -> None:
    """Collect up to cap semantic differences as path/baseline/candidate rows."""
    if len(out) >= cap:
        return
    here = path or "<root>"
    if type(first) is not type(second):
        out.append({"path": here, "baseline": first, "candidate": second})
        return
    if isinstance(first, dict):
        assert isinstance(second, dict)
        for key in sorted(set(first) | set(second)):
            step = f"{path}.{key}" if path else str(key)
            if key not in first:
                out.append({"path": step, "baseline": dict(_ABSENT),
                            "candidate": second[key]})
            elif key not in second:
                out.append({"path": step, "baseline": first[key],
                            "candidate": dict(_ABSENT)})
            else:
                _diff_paths(first[key], second[key], step, out, cap)
            if len(out) >= cap:
                return
        return
    if isinstance(first, list):
        assert isinstance(second, list)
        for index in range(max(len(first), len(second))):
            step = f"{path}[{index}]"
            if index >= len(first):
                out.append({"path": step, "baseline": dict(_ABSENT),
                            "candidate": second[index]})
            elif index >= len(second):
                out.append({"path": step, "baseline": first[index],
                            "candidate": dict(_ABSENT)})
            else:
                _diff_paths(first[index], second[index], step, out, cap)
            if len(out) >= cap:
                return
        return
    if first != second:
        out.append({"path": here, "baseline": first, "candidate": second})


def _load_transitions(repo: Path) -> tuple[list[dict], str | None]:
    """The approved contract transitions, or an empty list when unlisted."""
    import yaml

    path = repo / "tests" / "architecture" / "contract-transitions.yaml"
    if not path.exists():
        return [], None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [], f"cannot read contract-transitions.yaml: {exc}"
    if data is None:
        return [], None
    if not isinstance(data, list):
        return [], "contract-transitions.yaml is not a list"
    rows: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            return [], "contract-transitions.yaml holds a malformed row"
        rows.append(row)
    return rows, None


def _resolve_revision(repo: Path, name: str) -> str | None:
    proc = _git(repo, "rev-parse", "--verify", f"{name}^{{commit}}")
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _cleanup(repo: Path, work_dir: Path, worktrees: list[Path],
             copies: list[Path]) -> None:
    for tree in worktrees:
        _git(repo, "worktree", "remove", "--force", str(tree))
        _remove_tree(tree)
    _git(repo, "worktree", "prune")
    for tree in copies:
        _remove_tree(tree)
    link = work_dir / "materials"
    if link.is_symlink():
        link.unlink()


def _check_metadata(side: str, manifest: dict | None, info: dict,
                    tree: Path) -> tuple[dict, list[str]]:
    """SPEC §6 step 5(ii): the side's publication metadata describes itself."""
    result: dict = {"contract_version": None, "schema_sha256": None,
                    "snapshot_id": None, "checks": {}}
    problems: list[str] = []
    if manifest is None:
        problems.append(f"metadata:{side}.generation")
        return result, problems
    generated = manifest.get("_generated")
    if not isinstance(generated, dict):
        problems.append(f"metadata:{side}.generation")
        return result, problems
    contract, note = _side_contract(tree)
    if contract is None:
        result["contract_note"] = note
        problems.append(f"metadata:{side}.contract_version")
        problems.append(f"metadata:{side}.schema_sha256")
    else:
        result["contract_version"] = contract["contract_version"]
        result["schema_sha256"] = contract["schema_sha256"]
        ok_version = generated.get("contract_version") == contract["contract_version"]
        ok_schema = generated.get("schema_sha256") == contract["schema_sha256"]
        result["checks"]["contract_version"] = ok_version
        result["checks"]["schema_sha256"] = ok_schema
        if not ok_version:
            problems.append(f"metadata:{side}.contract_version")
        if not ok_schema:
            problems.append(f"metadata:{side}.schema_sha256")
    digest = _side_fingerprint(tree)
    result["snapshot_id"] = generated.get("snapshot_id")
    ok_snapshot = digest is not None and generated.get("snapshot_id") == f"sha256:{digest}"
    result["checks"]["snapshot_id"] = ok_snapshot
    if not ok_snapshot:
        problems.append(f"metadata:{side}.snapshot_id")
    return result, problems


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = _toplevel()
    if repo is None:
        return _fail("cannot find the repository top level")
    world = Path(args.world).resolve()
    if not world.is_dir():
        return _fail(f"world is not a directory: {world}")
    materials_arg = Path(args.materials).resolve() if args.materials \
        else (repo.parent / "materials").resolve()
    work_dir = Path(args.work_dir).resolve() if args.work_dir \
        else (repo.parent / "scratch" / "world-runs").resolve()
    if work_dir == repo or repo in work_dir.parents:
        return _fail(f"refusing a work directory inside the repository: {work_dir}")
    if not materials_arg.is_dir():
        return _fail(f"materials is not a directory: {materials_arg}")

    # Step 0: the world's bytes are pinned and verified before anything else.
    broken = _verify_data(world)
    if broken is not None:
        return _fail(f"world corrupted: {broken}")

    baseline_sha = _resolve_revision(repo, args.baseline)
    if baseline_sha is None:
        return _fail(f"cannot resolve baseline revision: {args.baseline}")
    worktree_copy = args.candidate == "WORKTREE"
    candidate_sha = None
    if not worktree_copy:
        candidate_sha = _resolve_revision(repo, args.candidate)
        if candidate_sha is None:
            return _fail(f"cannot resolve candidate revision: {args.candidate}")
    assert worktree_copy or candidate_sha is not None

    work_dir.mkdir(parents=True, exist_ok=True)
    baseline_tree = work_dir / f"world-{baseline_sha}"
    if worktree_copy:
        candidate_tree = work_dir / "world-worktree"
    elif candidate_sha == baseline_sha:
        candidate_tree = baseline_tree
    else:
        assert candidate_sha is not None
        candidate_tree = work_dir / f"world-{candidate_sha}"

    # Step 1: one disposable worktree per distinct code revision.
    worktrees: list[Path] = []
    copies: list[Path] = []
    try:
        if worktree_copy:
            _remove_tree(candidate_tree)
            candidate_tree.mkdir(parents=True)
            listed = _git(repo, "ls-files", "-co", "--exclude-standard")
            if listed.returncode != 0:
                return _fail("cannot list the working tree")
            for rel in listed.stdout.splitlines():
                source = repo / rel
                target = candidate_tree / rel
                if source.is_symlink():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(os.readlink(source))
                elif source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            copies.append(candidate_tree)
        for tree, sha in ((baseline_tree, baseline_sha),
                          (candidate_tree, candidate_sha)):
            if tree == candidate_tree and worktree_copy:
                continue
            if tree in worktrees:
                continue
            assert sha is not None
            _git(repo, "worktree", "remove", "--force", str(tree))
            _remove_tree(tree)
            added = _git(repo, "worktree", "add", "--detach", str(tree), sha)
            if added.returncode != 0:
                return _fail(f"cannot build a worktree for {sha}: "
                             f"{added.stderr.strip()}")
            worktrees.append(tree)

        # Step 2: the world's data over each tree, and the shared materials link.
        _overlay_data(world, baseline_tree)
        _overlay_data(world, candidate_tree)
        link = work_dir / "materials"
        if link.is_symlink() or link.is_file():
            link.unlink()
        elif link.exists():
            return _fail(f"refusing to replace {link}")
        link.symlink_to(materials_arg)

        # Step 3: the world's material inventory against the current materials.
        mismatch = _verify_materials(world, link)
        if mismatch is not None:
            return _fail(f"materials differ: {mismatch}")

        # Step 4: each side's own projection under the world's observations.
        baseline_manifest, baseline_info = _run_side(repo, baseline_tree, world)
        if candidate_tree == baseline_tree:
            candidate_manifest, candidate_info = baseline_manifest, dict(baseline_info)
        else:
            candidate_manifest, candidate_info = _run_side(repo, candidate_tree, world)

        # Step 5(i): the semantic bodies must be identical.
        differences: list[str] = []
        semantic_rows: list[dict] = []
        semantic_equal = False
        if baseline_manifest is None or candidate_manifest is None:
            if baseline_manifest is None:
                differences.append("manifest:baseline.generation")
            if candidate_manifest is None:
                differences.append("manifest:candidate.generation")
        else:
            baseline_body = {k: v for k, v in baseline_manifest.items() if k != "_generated"}
            candidate_body = {k: v for k, v in candidate_manifest.items() if k != "_generated"}
            baseline_flat = json.dumps(baseline_body, sort_keys=True, ensure_ascii=True)
            candidate_flat = json.dumps(candidate_body, sort_keys=True, ensure_ascii=True)
            semantic_equal = baseline_flat == candidate_flat
            if not semantic_equal:
                _diff_paths(baseline_body, candidate_body, "", semantic_rows)
                differences.extend(f"manifest:{row['path']}" for row in semantic_rows)

        # Step 5(ii): each side's metadata describes its own bytes.
        baseline_meta, baseline_problems = _check_metadata(
            "baseline", baseline_manifest, baseline_info, baseline_tree)
        candidate_meta, candidate_problems = _check_metadata(
            "candidate", candidate_manifest, candidate_info, candidate_tree)
        differences.extend(baseline_problems)
        differences.extend(candidate_problems)

        # Step 5(iii): the contract versions agree, or a transition allows it.
        baseline_version = baseline_meta.get("contract_version")
        candidate_version = candidate_meta.get("contract_version")
        transition = None
        contract_ok = False
        if isinstance(baseline_version, int) and isinstance(candidate_version, int):
            if baseline_version == candidate_version:
                contract_ok = True
            else:
                rows, note = _load_transitions(repo)
                if note is not None:
                    return _fail(note)
                for row in rows:
                    if row.get("from") == baseline_version \
                            and row.get("to") == candidate_version:
                        transition = {k: row.get(k) for k in ("from", "to", "plan_ref")}
                        break
                contract_ok = transition is not None
                if not contract_ok:
                    differences.append("contract:contract_version")

        # Step 6: the JSON report.
        report = {
            "identical": not differences,
            "world": str(world),
            "baseline": {"revision": baseline_sha, **baseline_info, **baseline_meta},
            "candidate": {
                "revision": candidate_sha or "WORKTREE",
                **candidate_info, **candidate_meta,
            },
            "semantic": {"equal": semantic_equal, "differences": semantic_rows},
            "contract": {
                "baseline_version": baseline_version,
                "candidate_version": candidate_version,
                "transition": transition,
                "accepted": contract_ok,
            },
            "differences": differences,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if not differences else 1
    finally:
        # Step 7: nothing is left in the repository or under .git/worktrees.
        _cleanup(repo, work_dir, worktrees, copies)


if __name__ == "__main__":
    raise SystemExit(main())
