"""The loader's public surface (BUILD-SPEC Step 3).

The walk itself lives in ``learning_os.store.loading``: one module per domain over a
shared model, with the order between domains stated once in
``loading/__init__.py``. This module stays the import site every other tool
already uses — ``from learning_os.store.loader import load_repo`` — so where a record
is read from remains an internal detail of the loader, not a fact spread across
the callers.

See ``learning_os.store.loading`` for the registry layouts and for which module owns
which part of the tree.

Snapshot values are owned by ``learning_os.domain.snapshot``, vocabulary by
``learning_os.domain.vocabulary`` and ``md_section`` by
``learning_os.domain.markdown``; import them there.
"""

from __future__ import annotations

from learning_os.store.loading import (  # noqa: F401  (re-exported public surface)
    LoaderError,
    load_repo,
    parse_frontmatter,
)

__all__ = [
    "LoaderError",
    "load_repo", "parse_frontmatter",
]
