"""Derived state: a disposable incremental-computation substrate.

Derived values are never authoritative — deleting generated/derived-state/
only costs recomputation. See model.py (vocabulary), identity.py (content
digests), store.py (content-addressed persistence), engine.py (evaluation).
"""

from __future__ import annotations

from .engine import (
    BuildContext,
    Evaluation,
    Staging,
    TraceEvent,
    commit_staging,
    evaluate,
    evaluate_many,
)
from .identity import (
    canonical_snapshot_digest,
    digest_bytes,
    digest_code_identity,
    digest_code_tree,
    digest_executing_code_tree,
    digest_file,
    digest_matching_files,
    digest_paths,
    digest_producer_files,
    digest_tree,
    runtime_digest,
    validator_runtime_digest,
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
    invalidate,
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
    "Staging",
    "TraceEvent",
    "canonical_bytes",
    "canonical_snapshot_digest",
    "commit_staging",
    "derived_dir",
    "digest_bytes",
    "digest_code_identity",
    "digest_code_tree",
    "digest_executing_code_tree",
    "digest_file",
    "digest_matching_files",
    "digest_paths",
    "digest_producer_files",
    "digest_tree",
    "evaluate",
    "evaluate_many",
    "invalidate",
    "lookup",
    "node_key",
    "read_state",
    "runtime_digest",
    "state_path",
    "store_node",
    "validator_runtime_digest",
]
