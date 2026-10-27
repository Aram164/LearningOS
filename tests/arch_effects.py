"""Oracle helpers for the one-writer check (SPEC §3.2a)."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable
from pathlib import Path

import yaml

from learning_os.store.fingerprint import CANONICAL_ROOTS


def capture_tree(root: Path) -> dict[str, str]:
    """Map POSIX relative path to sha256 hex for every canonical file.

    Covers every regular file under ``CANONICAL_ROOTS``. Does not follow
    symlinks: symlinked files and directories are skipped.
    """
    result: dict[str, str] = {}
    root = Path(root)
    for rel_root in CANONICAL_ROOTS:
        base = root / rel_root
        if base.is_symlink() or not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = sorted(
                d for d in dirnames
                if not Path(dirpath, d).is_symlink()
            )
            for name in sorted(filenames):
                full = Path(dirpath, name)
                if full.is_symlink() or not full.is_file():
                    continue
                rel = full.relative_to(root).as_posix()
                result[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
    return result


def new_receipts(before_root_listing, root: Path) -> list[dict]:
    """Parsed receipt YAMLs added under ``operations/transactions/``.

    ``before_root_listing`` is the receipt listing observed before: an
    iterable of names or paths. Anything matching
    ``transaction-*.yaml`` now that was not listed before is parsed and
    returned, sorted by file name.
    """
    before_names = {Path(str(entry)).name for entry in before_root_listing}
    directory = Path(root) / "operations" / "transactions"
    if not directory.is_dir():
        return []
    current = sorted(
        p for p in directory.glob("transaction-*.yaml")
        if p.is_file() and not p.is_symlink())
    added = []
    for path in current:
        if path.name not in before_names:
            added.append(
                yaml.safe_load(path.read_text(encoding="utf-8")))
    return added


def reconcile(before: dict[str, str], after: dict[str, str],
              receipts: Iterable[dict],
              restored_from: dict[str, str] | None = None) -> list[str]:
    """Violation strings for canonical changes no receipt or restore owns.

    Every changed, added or deleted canonical path must satisfy one of:
    1. some receipt ``writes[]`` entry has ``path`` equal to the path and
       ``sha256_after`` equal to ``after[path]`` (a deletion matches an
       entry whose ``sha256_after`` is null);
    2. ``restored_from`` has ``restored_from[path] == after[path]``, or the
       path is absent in both.
    """
    receipts = list(receipts)
    entries: list[tuple[str, object]] = []
    for receipt in receipts:
        writes = receipt.get("writes") if isinstance(receipt, dict) else None
        if not isinstance(writes, list):
            continue
        for row in writes:
            if isinstance(row, dict):
                entries.append((row.get("path"), row.get("sha256_after")))
    violations: list[str] = []
    missing = object()
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        owned = False
        if path in after:
            for entry_path, sha_after in entries:
                if entry_path == path and sha_after == after[path]:
                    owned = True
                    break
        else:
            for entry_path, sha_after in entries:
                if entry_path == path and sha_after is None:
                    owned = True
                    break
        if not owned and restored_from is not None:
            if restored_from.get(path, missing) == after.get(path, missing):
                owned = True
        if not owned:
            violations.append(f"unaccounted canonical change: {path}")
    return violations
