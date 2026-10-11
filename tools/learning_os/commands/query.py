"""Read-only commands. Nothing here writes: the thin delegations to validate.py /
generate.py."""

from __future__ import annotations

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _publish,
)

from .support import (
    _delegate,
    _root,
)


def cmd_validate(args) -> int:
    return _delegate("validate.py", ["--online"] if args.online else [], args)


def cmd_generate(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        _publish(root)
    print("published generated/manifest.json (atomic contract snapshot)")
    return 0
