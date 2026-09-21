#!/usr/bin/env python3
"""Prototype: bundle a manifest JSON Schema with its transitive closure.

    python tools/contract_bundle.py build --schema system/contracts/manifest-v14.schema.json --out /tmp/cb
    python tools/contract_bundle.py check --schema system/contracts/manifest-v14.schema.json --dir /tmp/cb

``build`` writes ``<stem>.bundle.json`` (canonical bytes) plus ``<stem>.meta.json``
(version, root hash, closure digest, resource inventory, generator identity).
``check`` rebuilds into a temporary directory and byte-compares, exiting 1 on
any difference. Nothing here touches canonical data, stamped fields, or gates.
"""

from __future__ import annotations

import argparse
import filecmp
import sys
import tempfile
from pathlib import Path

from learning_os.contracts.bundle import (  # noqa: E402
    BundleError,
    build_bundle,
    build_meta,
    canonical_bytes,
    digest_of,
    resolve_closure,
)
from learning_os.contracts.manifest_contract import load_contract  # noqa: E402


def _emit(root: Path, schema_rel: str, schema_dir_rel: str, out_dir: Path) -> list[Path]:
    schema_path = root / schema_rel
    schema_dir = root / schema_dir_rel
    bundle = build_bundle(schema_path, schema_dir)
    closure = resolve_closure(schema_path, schema_dir)
    meta = build_meta(
        contract=load_contract(root),
        schema_label=schema_rel,
        closure_digest=digest_of(bundle),
        resources=closure["resources"],
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = schema_path.stem.replace(".schema", "")
    bundle_path = out_dir / f"{stem}.bundle.json"
    meta_path = out_dir / f"{stem}.meta.json"
    bundle_path.write_bytes(bundle)
    meta_path.write_bytes(canonical_bytes(meta))
    return [bundle_path, meta_path]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--schema-dir", default="system/schema",
                        help="schema directory, repository-relative")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="write bundle + meta to --out")
    build.add_argument("--schema", required=True, help="root schema, repository-relative")
    build.add_argument("--out", required=True, help="output directory")
    check = sub.add_parser("check", help="rebuild and byte-compare against --dir")
    check.add_argument("--schema", required=True, help="root schema, repository-relative")
    check.add_argument("--dir", required=True, help="directory holding a previous build")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    try:
        if args.command == "build":
            written = _emit(root, args.schema, args.schema_dir, Path(args.out))
            print("wrote " + ", ".join(str(path) for path in written))
            return 0
        with tempfile.TemporaryDirectory(prefix="contract-bundle-check-") as tmp:
            fresh = _emit(root, args.schema, args.schema_dir, Path(tmp))
            failures = [
                path.name for path in fresh
                if not (Path(args.dir) / path.name).is_file()
                or not filecmp.cmp(path, Path(args.dir) / path.name, shallow=False)
            ]
        if failures:
            print(f"contract bundle drifted: {', '.join(failures)}", file=sys.stderr)
            return 1
        print("contract bundle matches")
        return 0
    except BundleError as exc:
        print(f"contract bundle error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
