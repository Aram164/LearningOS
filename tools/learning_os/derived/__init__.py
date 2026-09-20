"""Derived state: a disposable incremental-computation substrate.

Derived values are never authoritative — deleting generated/derived-state/
only costs recomputation. See model.py (vocabulary), identity.py (content
digests), store.py (content-addressed persistence), engine.py (evaluation).
"""

from __future__ import annotations

from .engine import (
    BuildContext,
    Evaluation,
    TraceEvent,
    evaluate,
)
from .identity import (
    digest_bytes,
    digest_file,
    digest_paths,
    digest_producer_files,
    digest_tree,
)
from .model import (
    ENGINE_VERSION,
    DerivedError,
    InputRef,
    NodeSpec,
    NodeState,
    node_key,
)
from .store import (
    DERIVED_TOP_DIR,
    STATE_SCHEMA_VERSION,
    canonical_bytes,
    derived_dir,
    lookup,
    read_state,
    state_path,
    store_node,
)

__all__ = [
    "DERIVED_TOP_DIR",
    "ENGINE_VERSION",
    "STATE_SCHEMA_VERSION",
    "BuildContext",
    "DerivedError",
    "Evaluation",
    "InputRef",
    "NodeSpec",
    "NodeState",
    "TraceEvent",
    "canonical_bytes",
    "derived_dir",
    "digest_bytes",
    "digest_file",
    "digest_paths",
    "digest_producer_files",
    "digest_tree",
    "evaluate",
    "lookup",
    "node_key",
    "read_state",
    "state_path",
    "store_node",
]
