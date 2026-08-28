#!/usr/bin/env python3
"""Deep, repeatable LearningOS checks beyond the routine release gate.

The Makefile composes this with ``make system-check`` and the unified online
validator.  This script owns only deterministic local load tests: production
resource targets, repeated generation, atomic publication, concurrent CLI
reads, and repeated sibling-UI interaction suites.  It never edits canonical
data; only disposable ``generated/`` outputs are republished.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo


def _assert_manifest(data: dict) -> None:
    generated = data.get("_generated", {})
    assert generated.get("contract_version") == 5
    assert generated.get("snapshot_id") == (
        "sha256:" + generated.get("source_fingerprint", "")
    )
    for key in ("records", "stages", "units"):
        assert isinstance(data.get(key), list), key


def _is_file_shaped(value) -> bool:
    if not isinstance(value, str):
        return False
    clean = value.strip().split("?", 1)[0].split("#", 1)[0]
    name = clean.replace("\\", "/").rsplit("/", 1)[-1]
    return bool(name and not name.startswith(".") and "." in name.rstrip("."))


def _safe_web_url(value) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _audit_production_targets(root: Path, manifest: dict) -> tuple[int, int]:
    unique: dict[str, dict] = {}
    for stage in manifest.get("stages", []):
        if not isinstance(stage, dict):
            continue
        for resource in stage.get("resources", []) or []:
            if not isinstance(resource, dict):
                continue
            identity = json.dumps([
                resource.get("label"),
                resource.get("source_id"),
                resource.get("material_path"),
                resource.get("vault_path"),
                resource.get("url"),
            ], ensure_ascii=False)
            unique[identity] = resource

    openable = 0
    for resource in unique.values():
        material_path = resource.get("material_path")
        vault_path = resource.get("vault_path")
        url = resource.get("url")
        if material_path:
            assert _is_file_shaped(material_path), resource
            assert resource.get("material_exists") is True, resource
            assert (root.parent / material_path).is_file(), resource
            openable += 1
        elif isinstance(vault_path, str) \
                and not vault_path.lower().startswith("material://") \
                and _is_file_shaped(vault_path):
            assert (root / vault_path).is_file(), resource
            openable += 1
        elif url:
            assert _safe_web_url(url), resource
            openable += 1
    return len(unique), openable


def _generation_stress(root: Path, generations: int, readers: int,
                       reads_per_reader: int) -> tuple[str, int]:
    first_outputs = None
    first_hash = ""
    for _ in range(generations):
        outputs = generate_all(load_repo(root))
        current_hash = hashlib.sha256(
            outputs["manifest.json"].encode("utf-8")
        ).hexdigest()
        if not first_hash:
            first_hash = current_hash
            first_outputs = outputs
        else:
            assert current_hash == first_hash
    assert first_outputs is not None
    write_outputs(load_repo(root), first_outputs)

    start = threading.Event()

    def read_manifest() -> int:
        start.wait()
        for _ in range(reads_per_reader):
            data = json.loads(
                (root / "generated/manifest.json").read_text(encoding="utf-8")
            )
            _assert_manifest(data)
        return reads_per_reader

    def publish_manifest() -> None:
        start.wait()
        repo = load_repo(root)
        for _ in range(generations):
            write_outputs(repo, first_outputs)

    with ThreadPoolExecutor(max_workers=readers + 1) as pool:
        read_futures = [pool.submit(read_manifest) for _ in range(readers)]
        writer = pool.submit(publish_manifest)
        start.set()
        writer.result()
        reads = sum(future.result() for future in read_futures)
    return first_hash, reads


def _cli_stress(root: Path, reads: int) -> int:
    command = [
        sys.executable,
        str(root / "tools/los.py"),
        "--root",
        str(root),
        "status",
    ]

    def invoke() -> None:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr or result.stdout

    with ThreadPoolExecutor(max_workers=min(8, reads)) as pool:
        list(pool.map(lambda _index: invoke(), range(reads)))
    return reads


def _ui_stress(root: Path, rounds: int) -> int:
    ui_root = root.parent / "obsidian-ui"
    npm = shutil.which("npm")
    assert npm, "npm is required for the sibling UI stress rounds"
    assert (ui_root / "package.json").is_file(), "sibling obsidian-ui is missing"
    for _ in range(rounds):
        for script in ("test:modules", "test:ui"):
            result = subprocess.run(
                [npm, "run", script],
                cwd=ui_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, result.stderr or result.stdout
    return rounds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--readers", type=int, default=8)
    parser.add_argument("--reads-per-reader", type=int, default=100)
    parser.add_argument("--cli-reads", type=int, default=32)
    parser.add_argument("--ui-rounds", type=int, default=5)
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent

    outputs = generate_all(load_repo(root))
    manifest = json.loads(outputs["manifest.json"])
    resources, openable = _audit_production_targets(root, manifest)
    print(f"stress: production resources {resources}, openable {openable}, broken 0")

    digest, atomic_reads = _generation_stress(
        root, args.generations, args.readers, args.reads_per_reader
    )
    print(
        f"stress: deterministic generations {args.generations}/{args.generations} "
        f"({digest[:12]}); atomic reads {atomic_reads}/{atomic_reads}"
    )

    cli_reads = _cli_stress(root, args.cli_reads)
    print(f"stress: concurrent CLI reads {cli_reads}/{cli_reads}")
    ui_rounds = _ui_stress(root, args.ui_rounds)
    print(f"stress: repeated UI rounds {ui_rounds}/{ui_rounds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
