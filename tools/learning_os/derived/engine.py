"""Evaluation with early cutoff (change pruning).

A node reuses its cached value when the persisted node key equals the key
recomputed from current inputs, current producer bytes, and current
dependency *output* hashes. A dependency that was rebuilt but produced a
byte-identical output therefore does not invalidate its dependents: the
dependent key never sees the rebuild, only the unchanged output hash.

Misses are cheap and safe; stale hits are the only defect class. Unknown
nodes, undeclared inputs, dependency cycles, and unreadable producer
files fail closed (DerivedError) rather than guessing. Corrupt or absent
cached state is an ordinary miss. Trace events are diagnostic only and
never influence a reuse decision.

A snapshot-bound caller passes a Staging: rebuilt values accumulate in
memory and reach the store only through commit_staging(), after the
caller has proven its inputs stayed stable across the evaluation.
Without a staging, rebuilt values store immediately (the historical
behavior, kept for callers that own no snapshot).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .identity import digest_bytes, digest_code_tree, digest_producer_files, runtime_digest
from .model import DerivedError, InputRef, NodeSpec, NodeState, node_key
from .store import canonical_bytes, lookup, store_node


@dataclass(frozen=True)
class Evaluation:
    """One node's evaluated value plus the proof it was built under."""

    value: Any
    output_sha256: str
    status: str  # "hit" | "rebuilt"
    node_key: str


@dataclass(frozen=True)
class TraceEvent:
    """Diagnostic record of one reuse decision. Never read by the engine."""

    node: str
    status: str  # "hit" | "rebuilt"
    # identity-hit | cold-miss | stale-key with same output (pruned
    # upstream: dependents are unaffected) | stale-key with new output.
    reason: str  # "node-key-equal" | "cache-miss"
    #            | "node-key-changed-output-same" | "node-key-changed-output-changed"
    node_key: str
    output_sha256: str
    previous_output_sha256: str | None = None


@dataclass(frozen=True)
class BuildContext:
    """Everything a build function may depend on, already resolved."""

    root: Path
    spec: NodeSpec
    inputs: Mapping[str, str]
    dependencies: Mapping[str, Evaluation]


#: A build function receives its resolved context and returns a
#: JSON-serializable value. It must be deterministic in its context.
BuildFn = Callable[[BuildContext], Any]

#: node id -> (spec, build). The spec id must equal its registry key.
Registry = Mapping[str, tuple[NodeSpec, BuildFn]]


@dataclass
class Staging:
    """An uncommitted evaluation result: rebuilt values held in memory.

    A snapshot-bound caller evaluates with a staging, verifies its
    inputs did not move during the evaluation, and only then publishes
    via commit_staging(). If the inputs moved, the staging is dropped —
    nothing built under the torn snapshot ever reaches the store.
    """

    pending: dict[str, tuple[str, Any]] = field(default_factory=dict)
    # node id -> (node key, value)

    def discard(self) -> None:
        """Drop every staged value without touching the store."""
        self.pending.clear()


def commit_staging(root: Path, staging: Staging) -> None:
    """Publish every staged value to the store, then empty the staging.

    Blobs-first/state-last per node, exactly as an immediate store;
    committing twice publishes once (the second commit finds nothing).
    """
    for node_id in sorted(staging.pending):
        key, value = staging.pending[node_id]
        store_node(root, node_id, node_key=key, value=value)
    staging.pending.clear()


@dataclass
class _Session:
    root: Path
    registry: Registry
    inputs: Mapping[str, str]
    trace: list[TraceEvent] | None
    code_digest: str
    runtime_digest: str
    staging: Staging | None = None
    memo: dict[str, Evaluation] = field(default_factory=dict)

    def evaluate(self, node_id: str, stack: tuple[str, ...] = ()) -> Evaluation:
        if node_id in self.memo:
            return self.memo[node_id]
        if node_id in stack:
            raise DerivedError(
                f"derived dependency cycle: {' -> '.join((*stack, node_id))}")
        try:
            spec, build = self.registry[node_id]
        except KeyError as exc:
            raise DerivedError(f"unknown derived node: {node_id}") from exc
        if spec.id != node_id:
            raise DerivedError(f"derived registry key {node_id!r} holds spec {spec.id!r}")
        child_stack = (*stack, node_id)
        dependencies = {dep: self.evaluate(dep, child_stack) for dep in spec.dependencies}
        try:
            resolved = {name: self.inputs[name] for name in spec.direct_inputs}
        except KeyError as exc:
            raise DerivedError(
                f"derived node {node_id!r} is missing input digest: {exc}") from exc
        key = node_key(
            node_id=spec.id,
            node_version=spec.version,
            producer_digest=digest_producer_files(self.root, spec.producer_files),
            code_digest=self.code_digest,
            runtime_digest=self.runtime_digest,
            direct_inputs=tuple(
                InputRef(id=name, digest=resolved[name]) for name in spec.direct_inputs),
            dependency_outputs={dep: item.output_sha256 for dep, item in dependencies.items()},
        )
        previous: NodeState | None = None
        cached = lookup(self.root, node_id)
        if cached is not None:
            previous, value = cached
            if previous.node_key == key:
                return self._finish(
                    node_id, value, previous.output_sha256, "hit",
                    "node-key-equal", key, previous.output_sha256)
        value = build(BuildContext(
            root=self.root, spec=spec, inputs=resolved, dependencies=dependencies))
        output = digest_bytes(canonical_bytes(value))
        if self.staging is not None:
            self.staging.pending[node_id] = (key, value)
        else:
            store_node(self.root, node_id, node_key=key, value=value)
        if previous is None:
            reason = "cache-miss"
        elif previous.output_sha256 == output:
            reason = "node-key-changed-output-same"
        else:
            reason = "node-key-changed-output-changed"
        return self._finish(
            node_id, value, output, "rebuilt", reason, key,
            previous.output_sha256 if previous is not None else None)

    def _finish(self, node_id: str, value: Any, output: str, status: str,
                reason: str, key: str, previous_output: str | None) -> Evaluation:
        evaluation = Evaluation(value=value, output_sha256=output, status=status, node_key=key)
        self.memo[node_id] = evaluation
        if self.trace is not None:
            self.trace.append(TraceEvent(
                node=node_id, status=status, reason=reason, node_key=key,
                output_sha256=output, previous_output_sha256=previous_output))
        return evaluation


def _session(
    root: Path,
    registry: Registry,
    inputs: Mapping[str, str],
    trace: list[TraceEvent] | None,
    staging: Staging | None,
) -> _Session:
    """One session: the code and runtime digests are fixed per session.

    Every node key in the session shares them, so a code or environment
    change between two node evaluations cannot fork the session's keys.
    """
    return _Session(
        root=root,
        registry=registry,
        inputs=inputs,
        trace=trace,
        code_digest=digest_code_tree(root),
        runtime_digest=runtime_digest(),
        staging=staging,
    )


def evaluate(
    root: Path,
    node_id: str,
    *,
    registry: Registry,
    inputs: Mapping[str, str],
    trace: list[TraceEvent] | None = None,
    staging: Staging | None = None,
) -> Evaluation:
    """Evaluate one node, reusing cached values whose keys still match.

    Dependencies evaluate depth-first with per-call memoisation, so a
    diamond evaluates each shared node once. ``inputs`` must resolve every
    direct input of every visited node. With a staging, rebuilt values
    accumulate in memory until the caller commits them.
    """
    return _session(root, registry, inputs, trace, staging).evaluate(node_id)


def evaluate_many(
    root: Path,
    node_ids: list[str],
    *,
    registry: Registry,
    inputs: Mapping[str, str],
    trace: list[TraceEvent] | None = None,
    staging: Staging | None = None,
) -> dict[str, Evaluation]:
    """Evaluate several roots sharing one memoisation session.

    Shared dependencies evaluate once across all roots, and the trace
    holds exactly one event per visited node — the shape node-execution
    assertions want. With a staging, rebuilt values accumulate in memory
    until the caller commits them.
    """
    session = _session(root, registry, inputs, trace, staging)
    return {node_id: session.evaluate(node_id) for node_id in node_ids}
