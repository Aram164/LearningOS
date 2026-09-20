"""Immutable descriptions of derived computations.

A node describes a deterministic value — current inputs plus the producer
implementation plus dependency outputs — not a task history record. The
evaluator (engine.py) decides reuse; this module only fixes the vocabulary
and the node-key construction every reuse decision rests on.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass


class DerivedError(ValueError):
    """A derived-state programming bug: unknown node, bad path, missing producer.

    Corrupt or missing cached state is never this error — that is an
    ordinary cache miss. Consumers treat this as "recompute without the
    cache" (or refuse, if no uncached path exists), never as a value.
    """


#: Bumped whenever evaluation, hashing, or state-shape semantics change.
#: Part of every node key, so an engine change invalidates all cached nodes
#: without requiring each producer to know about it.
#:
#: v2 (2026-09-20): the key additionally covers the whole-tree core code
#: digest and the runtime identity (F3/F4), so any pre-v2 cached entry is a
#: stale-key miss rather than a hit under weaker identity.
ENGINE_VERSION = 2

#: Implementation files every derived evaluation depends on. Consumers
#: include these in their node producer lists so substrate changes
#: invalidate cached values without a manual version bump.
DERIVED_SUBSTRATE_FILES = (
    "tools/learning_os/derived/engine.py",
    "tools/learning_os/derived/identity.py",
    "tools/learning_os/derived/model.py",
    "tools/learning_os/derived/store.py",
)


@dataclass(frozen=True)
class InputRef:
    """One resolved direct input: a stable identity plus its content digest."""

    id: str
    digest: str


@dataclass(frozen=True)
class NodeSpec:
    """Static description of one derived computation.

    ``direct_inputs`` names input identities resolved by the caller at
    evaluation time; ``dependencies`` names other nodes whose *output*
    digests feed this node's key (change pruning: a rebuilt dependency
    with an identical output does not invalidate its dependents).
    ``producer_files`` names the repo-relative implementation files whose
    bytes are part of the key, so a code change invalidates the cache.
    """

    id: str
    version: int
    producer_files: tuple[str, ...] = ()
    direct_inputs: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class NodeState:
    """Persisted reuse proof for one node: the key it was built under."""

    node_key: str
    output_sha256: str
    blob: str


def node_key(
    *,
    node_id: str,
    node_version: int,
    producer_digest: str,
    code_digest: str,
    runtime_digest: str,
    direct_inputs: tuple[InputRef, ...] = (),
    dependency_outputs: Mapping[str, str] | None = None,
) -> str:
    """Build the reuse key for one node evaluation.

    The key covers the engine version, the node identity and version, the
    declared producer implementation bytes, the whole-tree core code
    digest, the runtime identity, the direct input digests, and the
    dependency *output* digests — never repository HEAD, never the whole
    canonical state, and never whether a dependency was rebuilt. Inputs
    are ordered canonically so declaration order cannot fork the key.
    """
    parts = [
        f"derived-node-key-v{ENGINE_VERSION}",
        node_id,
        str(node_version),
        producer_digest,
        code_digest,
        runtime_digest,
    ]
    for ref in sorted(direct_inputs, key=lambda item: item.id):
        parts.append(ref.id)
        parts.append(ref.digest)
    for dep_id in sorted(dependency_outputs or {}):
        parts.append(dep_id)
        parts.append((dependency_outputs or {})[dep_id])
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
