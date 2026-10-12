"""Read-only commands. Nothing here writes: the thin delegation to generate.py."""

from __future__ import annotations

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _publish,
)

from .support import (
    _root,
)


def cmd_generate(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        _publish(root)
    print("published generated/manifest.json (atomic contract snapshot)")
    return 0
