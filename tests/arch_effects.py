"""Oracle helpers for the one-writer check (SPEC §3.2a).

Only ``capture_tree`` exists for now; ``new_receipts`` and ``reconcile``
arrive with the oracle in Task 3.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from learning_os.fingerprint import CANONICAL_ROOTS


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
            dirnames[:] = [
                d for d in dirnames
                if not Path(dirpath, d).is_symlink()
            ]
            for name in filenames:
                full = Path(dirpath, name)
                if full.is_symlink() or not full.is_file():
                    continue
                rel = full.relative_to(root).as_posix()
                result[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
    return result
