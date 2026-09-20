"""Derived-state substrate: keys, identities, and the disposable store.

Commit 1 of the incremental-computation plan. Pins the node-key format
(inputs + producer + dependency *outputs*), the content-identity rules
(bytes, never mtimes), and the store's miss-on-anything-corrupt contract.
No production consumer exists yet; the only production edge is the
_keep-dir exemption that stops generation from garbage-collecting the
cache.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from learning_os.derived import (
    DERIVED_TOP_DIR,
    DerivedError,
    InputRef,
    NodeSpec,
    canonical_bytes,
    derived_dir,
    digest_bytes,
    digest_file,
    digest_paths,
    digest_producer_files,
    digest_tree,
    invalidate,
    lookup,
    node_key,
    read_state,
    state_path,
    store_node,
)
from learning_os.genout.outputs import _KEEP_TOP_DIRS, _remove_stale

PRODUCER = "p" * 64
INPUT = InputRef(id="knowledge.notes", digest="a" * 64)


def _key(**overrides):
    args = {
        "node_id": "search.note:x",
        "node_version": 1,
        "producer_digest": PRODUCER,
        "direct_inputs": (INPUT,),
        "dependency_outputs": {"up": "b" * 64},
    }
    args.update(overrides)
    return node_key(**args)


# ---------------------------------------------------------------------------
# Node keys.
# ---------------------------------------------------------------------------

def test_node_key_is_stable():
    assert _key() == _key()


def test_node_key_covers_every_component():
    base = _key()
    assert _key(node_id="other") != base
    assert _key(node_version=2) != base
    assert _key(producer_digest="q" * 64) != base
    assert _key(direct_inputs=(InputRef(id="knowledge.notes", digest="c" * 64),)) != base
    assert _key(direct_inputs=()) != base
    assert _key(dependency_outputs={"up": "d" * 64}) != base
    assert _key(dependency_outputs={}) != base


def test_node_key_ignores_declaration_order():
    first = (InputRef(id="a", digest="1" * 64), InputRef(id="b", digest="2" * 64))
    second = (InputRef(id="b", digest="2" * 64), InputRef(id="a", digest="1" * 64))
    assert _key(direct_inputs=first) == _key(direct_inputs=second)
    assert _key(dependency_outputs={"x": "1", "y": "2"}) == _key(
        dependency_outputs={"y": "2", "x": "1"})


def test_node_spec_defaults():
    spec = NodeSpec(id="n", version=1)
    assert spec.producer_files == () and spec.direct_inputs == () and spec.dependencies == ()


# ---------------------------------------------------------------------------
# Content identity.
# ---------------------------------------------------------------------------

def test_digest_bytes_pins_sha256():
    assert digest_bytes(b"abc") == hashlib.sha256(b"abc").hexdigest()
    assert digest_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


def test_digest_file_tracks_content(tmp_path: Path):
    target = tmp_path / "note.md"
    target.write_text("one", encoding="utf-8")
    before = digest_file(tmp_path, target)
    target.write_text("two", encoding="utf-8")
    assert digest_file(tmp_path, target) != before


def test_digest_file_distinguishes_missing_and_inadmissible(tmp_path: Path):
    missing = digest_file(tmp_path, tmp_path / "absent.md")
    assert missing == digest_file(tmp_path, tmp_path / "absent.md")
    present = tmp_path / "present.md"
    present.write_text("x", encoding="utf-8")
    assert digest_file(tmp_path, present) != missing
    # A link escaping the root contributes link identity, never target bytes.
    outside = tmp_path / "outside.txt"
    outside.write_text("target bytes", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()
    link = vault / "escape.md"
    link.symlink_to(outside)
    escape_digest = digest_file(vault, link)
    assert escape_digest != missing
    assert escape_digest != digest_bytes(b"target bytes\0")
    # ... and follows an in-root link to the target content.
    inner = vault / "inner.md"
    inner.write_text("target bytes", encoding="utf-8")
    alias = vault / "alias.md"
    alias.symlink_to(inner)
    assert digest_file(vault, alias) == digest_file(vault, inner)


def test_digest_tree_is_deterministic_and_content_sensitive(tmp_path: Path):
    notes = tmp_path / "knowledge" / "notes"
    notes.mkdir(parents=True)
    (notes / "b.md").write_text("b", encoding="utf-8")
    (notes / "a.md").write_text("a", encoding="utf-8")
    first = digest_tree(tmp_path, "knowledge/notes")
    assert digest_tree(tmp_path, "knowledge/notes") == first
    (notes / "a.md").write_text("changed", encoding="utf-8")
    assert digest_tree(tmp_path, "knowledge/notes") != first


def test_digest_tree_skips_dotfiles_and_tolerates_absence(tmp_path: Path):
    assert digest_tree(tmp_path, "knowledge/notes") == digest_tree(tmp_path, "knowledge/notes")
    notes = tmp_path / "knowledge" / "notes"
    notes.mkdir(parents=True)
    empty = digest_tree(tmp_path, "knowledge/notes")
    (notes / ".hidden.md").write_text("scratch", encoding="utf-8")
    assert digest_tree(tmp_path, "knowledge/notes") == empty


def test_digest_tree_rejects_escape(tmp_path: Path):
    with pytest.raises(DerivedError):
        digest_tree(tmp_path, "../outside")
    with pytest.raises(DerivedError):
        digest_tree(tmp_path, "/abs")


def test_digest_paths_is_order_independent_and_missing_aware(tmp_path: Path):
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    assert digest_paths(tmp_path, ["a.md", "b.md"]) == digest_paths(tmp_path, ["b.md", "a.md"])
    assert digest_paths(tmp_path, ["a.md", "gone.md"]) != digest_paths(tmp_path, ["a.md", "b.md"])


def test_digest_producer_files_fails_closed(tmp_path: Path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "producer.py").write_text("v1", encoding="utf-8")
    good = digest_producer_files(tmp_path, ["tools/producer.py"])
    (tmp_path / "tools" / "producer.py").write_text("v2", encoding="utf-8")
    assert digest_producer_files(tmp_path, ["tools/producer.py"]) != good
    with pytest.raises(DerivedError):
        digest_producer_files(tmp_path, ["tools/missing.py"])
    with pytest.raises(DerivedError):
        digest_producer_files(tmp_path, ["../escape.py"])
    with pytest.raises(DerivedError):
        digest_producer_files(tmp_path, ["/abs.py"])


# ---------------------------------------------------------------------------
# Canonical bytes.
# ---------------------------------------------------------------------------

def test_canonical_bytes_is_deterministic():
    assert canonical_bytes({"b": 1, "a": [1, 2]}) == b'{"a":[1,2],"b":1}\n'


def test_canonical_bytes_rejects_non_serializable():
    with pytest.raises(DerivedError):
        canonical_bytes({"now": object()})


# ---------------------------------------------------------------------------
# Store round-trips.
# ---------------------------------------------------------------------------

def test_store_and_lookup_round_trip(tmp_path: Path):
    state = store_node(tmp_path, "n", node_key="k1", value={"b": 1, "a": [1, 2]})
    assert state.blob == f"blobs/{state.output_sha256}"
    found = lookup(tmp_path, "n")
    assert found is not None
    assert found[0] == state
    assert found[1] == {"a": [1, 2], "b": 1}
    assert lookup(tmp_path, "other") is None


def test_lookup_on_empty_root_is_a_miss(tmp_path: Path):
    assert lookup(tmp_path, "n") is None
    assert read_state(tmp_path) == {}
    assert not derived_dir(tmp_path).exists()


def test_store_replaces_and_orphans_old_blob(tmp_path: Path):
    first = store_node(tmp_path, "n", node_key="k1", value={"v": 1})
    second = store_node(tmp_path, "n", node_key="k2", value={"v": 2})
    assert lookup(tmp_path, "n")[0] == second
    # The orphaned blob is harmless: nothing references it.
    assert (derived_dir(tmp_path) / first.blob).exists()
    assert not list(derived_dir(tmp_path).rglob("*.tmp"))


def test_store_replaces_corrupt_state(tmp_path: Path):
    state_path(tmp_path).parent.mkdir(parents=True)
    state_path(tmp_path).write_text("not json", encoding="utf-8")
    store_node(tmp_path, "n", node_key="k1", value={"v": 1})
    assert lookup(tmp_path, "n") is not None


def test_store_rejects_empty_node_id(tmp_path: Path):
    with pytest.raises(DerivedError):
        store_node(tmp_path, "", node_key="k", value={})


# ---------------------------------------------------------------------------
# Store corruption tolerance: every case is a miss, never an error.
# ---------------------------------------------------------------------------

def _hand_state(tmp_path: Path, payload: str):
    state_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    state_path(tmp_path).write_text(payload, encoding="utf-8")


def test_corrupt_state_file_is_a_miss(tmp_path: Path):
    _hand_state(tmp_path, "{oops")
    assert read_state(tmp_path) == {}
    assert lookup(tmp_path, "n") is None


def test_wrong_schema_version_is_a_miss(tmp_path: Path):
    _hand_state(tmp_path, json.dumps({"schema_version": 999, "nodes": {}}))
    assert read_state(tmp_path) == {}


def test_misshapen_state_is_a_miss(tmp_path: Path):
    _hand_state(tmp_path, json.dumps({"schema_version": 1, "nodes": ["n"]}))
    assert read_state(tmp_path) == {}
    _hand_state(tmp_path, json.dumps([1, 2]))
    assert read_state(tmp_path) == {}


def test_duplicate_state_keys_reject_the_file(tmp_path: Path):
    _hand_state(
        tmp_path,
        '{"schema_version": 1, "nodes": {"n": {"node_key": "a", "node_key": "b",'
        ' "output_sha256": "' + "0" * 64 + '", "blob": "blobs/' + "0" * 64 + '"}}}',
    )
    assert read_state(tmp_path) == {}


def test_misshapen_entries_are_skipped_selectively(tmp_path: Path):
    (derived_dir(tmp_path) / "blobs").mkdir(parents=True)
    value = canonical_bytes({"ok": True})
    digest = hashlib.sha256(value).hexdigest()
    (derived_dir(tmp_path) / "blobs" / digest).write_bytes(value)
    _hand_state(tmp_path, json.dumps({
        "schema_version": 1,
        "nodes": {
            "good": {"node_key": "k", "output_sha256": digest, "blob": f"blobs/{digest}"},
            "escape": {"node_key": "k", "output_sha256": digest, "blob": "blobs/../../x"},
            "nonhex": {"node_key": "k", "output_sha256": "zz", "blob": "blobs/zz"},
            "short": {"node_key": "k"},
            "nonstr": "nope",
        },
    }))
    assert set(read_state(tmp_path)) == {"good"}
    assert lookup(tmp_path, "good") is not None
    assert lookup(tmp_path, "escape") is None


def test_missing_blob_is_a_miss(tmp_path: Path):
    digest = hashlib.sha256(canonical_bytes({"v": 1})).hexdigest()
    _hand_state(tmp_path, json.dumps({
        "schema_version": 1,
        "nodes": {"n": {"node_key": "k", "output_sha256": digest, "blob": f"blobs/{digest}"}},
    }))
    assert lookup(tmp_path, "n") is None


def test_tampered_blob_is_a_miss(tmp_path: Path):
    store_node(tmp_path, "n", node_key="k", value={"v": 1})
    blob = derived_dir(tmp_path) / "blobs"
    target = next(blob.iterdir())
    target.write_bytes(b'{"v": 2}\n')
    assert lookup(tmp_path, "n") is None


def test_symlinked_blob_is_a_miss(tmp_path: Path):
    state = store_node(tmp_path, "n", node_key="k", value={"v": 1})
    blob_path = derived_dir(tmp_path) / state.blob
    data = blob_path.read_bytes()
    blob_path.unlink()
    real = derived_dir(tmp_path) / "real.json"
    real.write_bytes(data)
    blob_path.symlink_to(real)
    assert lookup(tmp_path, "n") is None


def test_unparseable_blob_with_matching_hash_is_a_miss(tmp_path: Path):
    raw = b"\xff\xfe not json \x00"
    digest = hashlib.sha256(raw).hexdigest()
    blobs = derived_dir(tmp_path) / "blobs"
    blobs.mkdir(parents=True)
    (blobs / digest).write_bytes(raw)
    _hand_state(tmp_path, json.dumps({
        "schema_version": 1,
        "nodes": {"n": {"node_key": "k", "output_sha256": digest, "blob": f"blobs/{digest}"}},
    }))
    assert lookup(tmp_path, "n") is None


# ---------------------------------------------------------------------------
# Invalidation (self-healing).
# ---------------------------------------------------------------------------

def test_invalidate_drops_the_entry_and_keeps_the_blob(tmp_path: Path):
    state = store_node(tmp_path, "n", node_key="k", value={"v": 1})
    store_node(tmp_path, "other", node_key="k", value={"v": 2})
    invalidate(tmp_path, "n")
    assert lookup(tmp_path, "n") is None
    assert lookup(tmp_path, "other") is not None
    assert (derived_dir(tmp_path) / state.blob).exists()


def test_invalidate_missing_entry_is_a_noop(tmp_path: Path):
    invalidate(tmp_path, "n")
    assert not state_path(tmp_path).exists()


# ---------------------------------------------------------------------------
# Coexistence with generation.
# ---------------------------------------------------------------------------

def test_derived_state_survives_stale_removal(tmp_path: Path):
    assert DERIVED_TOP_DIR == "derived-state"
    assert DERIVED_TOP_DIR in _KEEP_TOP_DIRS
    gen = tmp_path / "generated"
    (gen / "derived-state" / "blobs").mkdir(parents=True)
    keep = gen / "derived-state" / "state-v1.json"
    keep.write_text("{}", encoding="utf-8")
    stale = gen / "stale-view.md"
    stale.write_text("old", encoding="utf-8")
    live = gen / "manifest.json"
    live.write_text("{}", encoding="utf-8")
    _remove_stale(gen, {"manifest.json": "{}"})
    assert keep.exists()
    assert (gen / "derived-state" / "blobs").is_dir()
    assert not stale.exists()
    assert live.exists()
