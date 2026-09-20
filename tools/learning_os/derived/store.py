"""Disposable content-addressed persistence for derived state.

Layout (all beneath generated/, never authoritative — deleting the whole
directory only costs recomputation):

    generated/derived-state/state-v1.json
    generated/derived-state/blobs/<sha256 hex of the canonical bytes>

Blobs are immutable values under content hashes; the state file maps
logical node IDs to the key they were built under plus their output hash.
Publication is blobs-first, state-last, each file via tmp + os.replace,
so a crash can orphan a blob but never leaves state pointing at a
half-written one. Path safety mirrors genout/outputs.py: no symlinks, no
``..``, everything stays beneath generated/.

Single-writer assumption: one process publishes at a time (generation and
search maintenance both run under the operator lock / single CLI process).
Concurrent publishers could interleave read-modify-write cycles on the
state file; the damage is bounded to lost cache entries (every entry is
still hash-verified on read), but it is not done deliberately.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from ..errors import TransactionFailure
from .model import DerivedError, NodeState

#: Top-level generated/ directory owned by this store. genout/outputs.py
#: must keep it out of stale-file garbage collection (single source of
#: truth for that exemption lives here, next to the writer).
DERIVED_TOP_DIR = "derived-state"

STATE_FILENAME = "state-v1.json"
STATE_SCHEMA_VERSION = 1
BLOBS_DIRNAME = "blobs"

_BLOB_RE = re.compile(r"[0-9a-f]{64}")


def derived_dir(root: Path) -> Path:
    """The derived-state directory (not created as a side effect)."""
    return root / "generated" / DERIVED_TOP_DIR


def state_path(root: Path) -> Path:
    """The state index path (not created as a side effect)."""
    return derived_dir(root) / STATE_FILENAME


def canonical_bytes(value: Any) -> bytes:
    """Deterministic serialization for hashing and blob storage.

    Same shape as the machine projections (sorted keys, compact
    separators, trailing newline). Not JSON-serializable input is a
    programming bug and raises.
    """
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise DerivedError(f"derived value is not deterministically serializable: {exc}") from exc
    return (text + "\n").encode("utf-8")


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate key: {key!r}")
        seen[key] = value
    return seen


def read_state(root: Path) -> dict[str, NodeState]:
    """Parse persisted node states; any corruption reads as empty.

    A missing, unreadable, unparseable, wrong-version, or wrongly shaped
    state file — including a blob reference that is not exactly
    ``blobs/<the entry's own output hash>`` — is an ordinary cache miss,
    never an error.
    """
    try:
        raw = state_path(root).read_bytes()
    except OSError:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicates)
    except (ValueError, UnicodeError):
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != STATE_SCHEMA_VERSION:
        return {}
    nodes = data.get("nodes")
    if not isinstance(nodes, dict):
        return {}
    states: dict[str, NodeState] = {}
    for node_id, entry in nodes.items():
        if not isinstance(node_id, str) or not node_id or not isinstance(entry, dict):
            continue
        key = entry.get("node_key")
        output = entry.get("output_sha256")
        blob = entry.get("blob")
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(output, str)
            or not _BLOB_RE.fullmatch(output)
            or blob != f"{BLOBS_DIRNAME}/{output}"
        ):
            continue
        states[node_id] = NodeState(node_key=key, output_sha256=output, blob=blob)
    return states


def invalidate(root: Path, node_id: str) -> None:
    """Drop one node's state entry; its blob is left as a harmless orphan.

    Self-healing for hash-verified but wrongly shaped values (tampering):
    the next evaluation misses and rebuilds from current inputs. Blobs are
    never deleted here — identical values share one blob across nodes.
    """
    states = read_state(root)
    if node_id not in states:
        return
    del states[node_id]
    payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "nodes": {
            key: {"node_key": item.node_key, "output_sha256": item.output_sha256, "blob": item.blob}
            for key, item in states.items()
        },
    }
    _atomic_write(_checked_store_dir(root, DERIVED_TOP_DIR) / STATE_FILENAME, canonical_bytes(payload))


def lookup(root: Path, node_id: str) -> tuple[NodeState, Any] | None:
    """Verified reuse: entry plus an existing blob with a matching hash.

    Anything else — missing entry, missing or symlinked blob, hash
    mismatch, unparseable blob — is a cache miss (None). The blob path is
    derived from the verified output hash, never trusted from the entry.
    """
    state = read_state(root).get(node_id)
    if state is None:
        return None
    blob_path = derived_dir(root) / BLOBS_DIRNAME / state.output_sha256
    try:
        if blob_path.is_symlink():
            return None
        data = blob_path.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(data).hexdigest() != state.output_sha256:
        return None
    try:
        return state, json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None


def _checked_store_dir(root: Path, *parts: str) -> Path:
    gen = root / "generated"
    if gen.is_symlink():
        raise TransactionFailure("generated output root may not be a symbolic link")
    gen.mkdir(parents=True, exist_ok=True)
    try:
        gen.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise TransactionFailure("generated output root escapes the repository") from exc
    current = gen
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise TransactionFailure(f"derived-state path is a symbolic link: {part}")
        if current.exists() and not current.is_dir():
            raise TransactionFailure(f"derived-state parent is not a directory: {part}")
        current.mkdir(exist_ok=True)
    try:
        current.resolve().relative_to(gen.resolve())
    except ValueError as exc:
        raise TransactionFailure("derived-state path escapes generated/") from exc
    return current


def _atomic_write(target: Path, content: bytes) -> None:
    if target.is_symlink():
        raise TransactionFailure(f"derived-state path is a symbolic link: {target.name}")
    tmp = target.with_name(f".{target.name}.tmp")
    if tmp.is_symlink():
        raise TransactionFailure(f"derived-state path is a symbolic link: {tmp.name}")
    tmp.write_bytes(content)
    os.replace(tmp, target)


def store_node(root: Path, node_id: str, *, node_key: str, value: Any) -> NodeState:
    """Publish one node's value: blob first, state index last, atomically.

    Returns the persisted state. Overwrites any previous entry for the
    node. A corrupt existing state file is replaced, not merged.
    """
    if not node_id:
        raise DerivedError("derived node id must be nonempty")
    data = canonical_bytes(value)
    digest = hashlib.sha256(data).hexdigest()
    blobs = _checked_store_dir(root, DERIVED_TOP_DIR, BLOBS_DIRNAME)
    _atomic_write(blobs / digest, data)
    states = read_state(root)
    state = NodeState(node_key=node_key, output_sha256=digest, blob=f"{BLOBS_DIRNAME}/{digest}")
    states[node_id] = state
    payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "nodes": {
            key: {"node_key": item.node_key, "output_sha256": item.output_sha256, "blob": item.blob}
            for key, item in states.items()
        },
    }
    _atomic_write(_checked_store_dir(root, DERIVED_TOP_DIR) / STATE_FILENAME, canonical_bytes(payload))
    return state
