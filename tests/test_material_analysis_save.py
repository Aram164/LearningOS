"""Durable source-analysis notes: exact bytes, honest bindings, safe replay.

The handler owns authorship/review defaults, preserves body bytes verbatim
(including leading whitespace, CRLF, and Unicode), replays identical
requests, and refuses id collisions, frozen-hash mismatches, resolved
bindings to unregistered sources, and resolved bindings whose material is
unobservable or unrelated to its source.
"""

from __future__ import annotations

import hashlib
import json

import pytest
import yaml
from gateway_helpers import (
    approved_v2_cli,
    approved_v2_envelope,
    file_sha256,
    run_v2_capability,
)

from learning_os.loader import load_repo
from learning_os.material_analysis import binding_consistent, observe_local_material

NOTE_ID = "note-analysis-demo-pp1-3"
NOTE_PATH = "knowledge/notes/mathematics/note-analysis-demo-pp1-3.md"
BODY = "  \n# Demo analysis — Schmælzung\n\nLine one.\r\nLine two without final newline"


def _binding(**overrides):
    binding = {
        "resolution": "unresolved",
        "material": "demo/deck.pdf",
        "recorded_source_digest": "ab" * 32,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(BODY.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(BODY.encode("utf-8")),
    }
    binding.update(overrides)
    return binding


def _save(mini_repo, body: bytes, binding: dict, key: str, note_id: str = NOTE_ID,
          path: str = NOTE_PATH, title: str = "Demo analysis"):
    body_file = mini_repo / f"body-{key}.bin"
    body_file.write_bytes(body)
    return approved_v2_cli(
        mini_repo, "note-analysis-save",
        "--analysis", json.dumps({"id": note_id, "title": title,
                                  "path": path, "binding": binding}),
        "--body-file", str(body_file),
        "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[note_id], idempotency_key=key,
    )


def _note_bytes(mini_repo, path: str = NOTE_PATH) -> bytes:
    return (mini_repo / path).read_bytes()


def test_binding_rules_keep_resolutions_honest():
    base = {"material": "demo/deck.pdf", "recorded_source_digest": "ab" * 32,
            "inspected_range": {"start": 1, "end": 3},
            "frozen_input_sha256": "cd" * 32}
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x",
                               "live_source_digest": "ab" * 32}) is None
    assert binding_consistent({**base, "resolution": "resolved",
                               "live_source_digest": "ab" * 32}) is not None
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x"}) is not None
    assert binding_consistent({**base, "resolution": "resolved",
                               "source_id": "source-x",
                               "live_source_digest": "ef" * 32}) is not None
    assert binding_consistent({**base, "resolution": "stale",
                               "live_source_digest": "ef" * 32}) is None
    assert binding_consistent({**base, "resolution": "stale"}) is not None
    assert binding_consistent({**base, "resolution": "unavailable"}) is None
    assert binding_consistent({**base, "resolution": "unavailable",
                               "live_source_digest": "ab" * 32}) is not None
    assert binding_consistent({**base, "resolution": "unresolved"}) is None
    assert binding_consistent({**base, "resolution": "nope"}) is not None


def test_observe_local_material_reports_current_stale_missing(tmp_path):
    root = tmp_path / "materials"
    root.mkdir()
    target = root / "deck.pdf"
    target.write_bytes(b"v1")
    digest = hashlib.sha256(b"v1").hexdigest()
    assert observe_local_material(root, "deck.pdf", digest)["status"] == "current"
    target.write_bytes(b"v2")
    stale = observe_local_material(root, "deck.pdf", digest)
    assert stale["status"] == "stale"
    assert stale["live_digest"] == hashlib.sha256(b"v2").hexdigest()
    assert observe_local_material(root, "gone.pdf", digest)["status"] == "missing"
    assert observe_local_material(root, "../escape.pdf", digest)["status"] == "outside-boundary"
    assert observe_local_material(root, "/abs.pdf", digest)["status"] == "outside-boundary"


def test_save_preserves_bytes_and_sets_unreviewed_defaults(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, _binding(), "save-new")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True and payload["replayed"] is False
    raw = _note_bytes(mini_repo)
    assert raw.endswith(body)
    assert b"operator-drafted" in raw and b"unreviewed" in raw
    repo = load_repo(mini_repo)
    note = repo.notes[NOTE_ID]
    assert note.meta["role"] == "reference"
    assert note.meta["state"] == "rough"
    assert note.meta["authorship"] == "operator-drafted"
    assert note.meta["semantic_review"] == "unreviewed"
    # The loader strips leading whitespace and normalizes CRLF on read
    # (shared frontmatter behavior); the file bytes above are the
    # authoritative preserved body.
    assert note.body == BODY.replace("\r\n", "\n").lstrip()
    stored = note.meta["material_analysis"]["frozen_input_bytes"]
    assert raw[-stored:] == body


def test_identical_request_replays_without_a_second_write(mini_repo):
    body = BODY.encode("utf-8")
    first = _save(mini_repo, body, _binding(), "replay-first")
    assert first.returncode == 0, first.stdout + first.stderr
    before = _note_bytes(mini_repo)
    second = _save(mini_repo, body, _binding(), "replay-second")
    assert second.returncode == 0, second.stdout + second.stderr
    assert json.loads(second.stdout)["replayed"] is True
    assert _note_bytes(mini_repo) == before


def test_collision_with_different_analysis_refuses(mini_repo):
    body = BODY.encode("utf-8")
    first = _save(mini_repo, body, _binding(), "collision-first")
    assert first.returncode == 0, first.stdout + first.stderr
    before = _note_bytes(mini_repo)
    other = _save(mini_repo, body + b"\nchanged", _binding(), "collision-body")
    assert other.returncode != 0
    assert _note_bytes(mini_repo) == before
    retitled = _save(mini_repo, body, _binding(), "collision-title", title="Other")
    assert retitled.returncode != 0
    rebound = _save(mini_repo, body, _binding(resolution="stale",
                                              live_source_digest="ef" * 32),
                     "collision-binding")
    assert rebound.returncode != 0
    assert _note_bytes(mini_repo) == before


def test_existing_non_analysis_note_id_refuses(mini_repo):
    body = BODY.encode("utf-8")
    result = _save(mini_repo, body, _binding(), "collision-user-note",
                    note_id="note-demo",
                    path="knowledge/notes/mathematics/note-demo.md")
    assert result.returncode != 0


def test_frozen_hash_mismatch_and_self_promotion_refuse(mini_repo):
    body = BODY.encode("utf-8")
    tampered = _save(mini_repo, body, _binding(frozen_input_sha256="00" * 32),
                      "frozen-mismatch")
    assert tampered.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    shortened = _save(mini_repo, body, _binding(frozen_input_bytes=len(body) - 1),
                       "frozen-length")
    assert shortened.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()
    promoted_binding = {"id": NOTE_ID, "title": "Demo", "path": NOTE_PATH,
                        "binding": _binding(), "authorship": "user"}
    body_file = mini_repo / "body-promoted.bin"
    body_file.write_bytes(body)
    refused = approved_v2_cli(
        mini_repo, "note-analysis-save",
        "--analysis", json.dumps(promoted_binding),
        "--body-file", str(body_file),
        "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[NOTE_ID], idempotency_key="self-promotion",
    )
    assert refused.returncode != 0
    assert not (mini_repo / NOTE_PATH).exists()


def _register_material(mini_repo, uri: str):
    path = mini_repo / "sources" / "sources.yaml"
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = uri
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")


def test_resolved_binding_requires_a_registered_source(mini_repo):
    body = BODY.encode("utf-8")
    digest = "ab" * 32
    unknown = _save(mini_repo, body,
                     _binding(resolution="resolved", source_id="source-nope",
                              live_source_digest=digest), "resolved-unknown")
    assert unknown.returncode != 0
    assert "not registered" in unknown.stdout
    assert not (mini_repo / NOTE_PATH).exists()


def test_resolved_binding_verifies_observed_registered_bytes(mini_repo):
    body = BODY.encode("utf-8")
    target = mini_repo.parent / "materials" / "demo" / "deck.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"observed deck bytes")
    digest = hashlib.sha256(b"observed deck bytes").hexdigest()

    def attempt(key: str, **overrides):
        return _save(mini_repo, body,
                      _binding(resolution="resolved", source_id="source-demo-book",
                               material="demo/deck.pdf",
                               recorded_source_digest=digest,
                               live_source_digest=digest, **overrides), key)

    # No registered material on the source: relationship unverifiable.
    refused = attempt("resolved-unregistered-material")
    assert refused.returncode != 0
    assert "registers no local material" in refused.stdout
    # Registered elsewhere: the bytes are real but not this source's.
    _register_material(mini_repo, "material://other/")
    refused = attempt("resolved-unrelated-material")
    assert refused.returncode != 0
    assert "not the source's registered file" in refused.stdout
    # Claimed digest differs from the observed bytes.
    _register_material(mini_repo, "material://demo/")
    refused = _save(mini_repo, body,
                     _binding(resolution="resolved", source_id="source-demo-book",
                              material="demo/deck.pdf",
                              recorded_source_digest="ab" * 32,
                              live_source_digest="ab" * 32), "resolved-drifted")
    assert refused.returncode != 0
    assert "not observable at its claimed live digest" in refused.stdout
    # Missing file with coherent digests: the false-resolved repro.
    target.unlink()
    refused = attempt("resolved-missing-file")
    assert refused.returncode != 0
    assert "not observable at its claimed live digest" in refused.stdout
    assert not (mini_repo / NOTE_PATH).exists()
    # Observed bytes under the registered root: accepted.
    target.write_bytes(b"observed deck bytes")
    known = attempt("resolved-known")
    assert known.returncode == 0, known.stdout + known.stderr
    assert load_repo(mini_repo).notes[NOTE_ID].meta[
        "material_analysis"]["source_id"] == "source-demo-book"


def test_dishonest_bindings_refuse(mini_repo):
    body = BODY.encode("utf-8")
    for key, binding in (
        ("stale-equal", _binding(resolution="stale", live_source_digest="ab" * 32)),
        ("unavailable-live", _binding(resolution="unavailable",
                                      live_source_digest="ab" * 32)),
        ("resolved-noid", _binding(resolution="resolved",
                                   live_source_digest="ab" * 32)),
    ):
        result = _save(mini_repo, body, binding, key)
        assert result.returncode != 0, key
    assert not (mini_repo / NOTE_PATH).exists()


# --------------------------------------------------------------------------
# Atomic batch saves: one snapshot, every item validated first, one receipt.
# --------------------------------------------------------------------------

def _binding_for(body: bytes, **overrides):
    binding = {
        "resolution": "unresolved",
        "material": "demo/deck.pdf",
        "recorded_source_digest": "ab" * 32,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body).hexdigest(),
        "frozen_input_bytes": len(body),
    }
    binding.update(overrides)
    return binding


def _batch_entry(tag: str, text: str, **overrides):
    body = text.encode("utf-8")
    note_id = f"note-analysis-batch-{tag}"
    entry = {
        "body": body,
        "binding": _binding_for(body),
        "note_id": note_id,
        "path": f"knowledge/notes/mathematics/{note_id}.md",
        "title": f"Batch analysis {tag}",
    }
    entry.update(overrides)
    return entry


def _batch_notes(mini_repo, entries, key):
    notes = []
    for index, entry in enumerate(entries):
        body_file = mini_repo / f"batch-body-{key}-{index}.bin"
        body_file.write_bytes(entry["body"])
        notes.append({
            "analysis": {"id": entry["note_id"], "title": entry["title"],
                         "path": entry["path"], "binding": entry["binding"]},
            "body_file": str(body_file),
            "body_file_sha256": file_sha256(body_file),
        })
    return notes


def _save_batch(mini_repo, entries, key):
    notes = _batch_notes(mini_repo, entries, key)
    return approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({"notes": notes}),
        artifact_ids=[entry["note_id"] for entry in entries],
        idempotency_key=key,
    )


def _transactions(mini_repo):
    tx_dir = mini_repo / "operations" / "transactions"
    return sorted(tx_dir.glob("transaction-*.yaml")) if tx_dir.is_dir() else []


def test_batch_mixed_new_and_replayed_reports_one_receipt(mini_repo):
    replayed = _batch_entry("replay", "kept analysis")
    created = _batch_entry("created", "new analysis")
    first = _save(mini_repo, replayed["body"], replayed["binding"],
                   "batch-mixed-first", note_id=replayed["note_id"],
                   path=replayed["path"], title=replayed["title"])
    assert first.returncode == 0, first.stdout + first.stderr
    before = _transactions(mini_repo)
    result = _save_batch(mini_repo, [replayed, created], "batch-mixed")
    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["ok"] is True and response["replayed"] is False
    assert response["result"]["created_note_ids"] == [created["note_id"]]
    assert response["result"]["replayed_note_ids"] == [replayed["note_id"]]
    assert response["result"]["note_paths"] == {
        replayed["note_id"]: replayed["path"],
        created["note_id"]: created["path"],
    }
    assert response["transaction_id"]
    assert (mini_repo / response["receipt_path"]).is_file()
    assert len(_transactions(mini_repo)) == len(before) + 1
    raw = (mini_repo / created["path"]).read_bytes()
    assert raw.endswith(created["body"])
    assert b"operator-drafted" in raw and b"unreviewed" in raw
    repo = load_repo(mini_repo)
    assert repo.notes[created["note_id"]].meta["role"] == "reference"
    assert repo.notes[replayed["note_id"]].meta["role"] == "reference"


def test_batch_one_bad_item_saves_none(mini_repo):
    good = _batch_entry("good", "good analysis")
    bad_body = b"bad analysis"
    bad = _batch_entry("bad", "bad analysis", binding=_binding_for(
        bad_body, frozen_input_sha256="00" * 32))
    result = _save_batch(mini_repo, [good, bad], "batch-one-bad")
    assert result.returncode != 0
    assert "batch item 1" in result.stdout
    assert not (mini_repo / good["path"]).exists()
    assert not (mini_repo / bad["path"]).exists()
    assert _transactions(mini_repo) == []


def test_batch_stale_source_bytes_refuse_the_whole_batch(mini_repo):
    _register_material(mini_repo, "material://demo/")
    target = mini_repo.parent / "materials" / "demo" / "deck.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"current deck bytes")
    good = _batch_entry("fresh", "fresh analysis")
    drifted_body = b"drifted analysis"
    drifted = _batch_entry("drifted", "drifted analysis", binding=_binding_for(
        drifted_body, resolution="resolved", source_id="source-demo-book",
        material="demo/deck.pdf", recorded_source_digest="ab" * 32,
        live_source_digest="ab" * 32))
    result = _save_batch(mini_repo, [good, drifted], "batch-stale")
    assert result.returncode != 0
    assert "not observable at its claimed live digest" in result.stdout
    assert not (mini_repo / good["path"]).exists()
    assert not (mini_repo / drifted["path"]).exists()
    assert _transactions(mini_repo) == []


def test_batch_duplicate_ids_refuse(mini_repo):
    entry = _batch_entry("dup", "duplicated analysis")
    identical = _save_batch(mini_repo, [entry, dict(entry)], "batch-dup-same")
    assert identical.returncode != 0
    assert "twice" in identical.stdout
    other_body = b"conflicting analysis"
    conflicting = _batch_entry("dup", "conflicting analysis", binding=_binding_for(
        other_body))
    refused = _save_batch(mini_repo, [entry, conflicting], "batch-dup-other")
    assert refused.returncode != 0
    assert "twice" in refused.stdout
    assert not (mini_repo / entry["path"]).exists()
    assert _transactions(mini_repo) == []


def test_batch_fully_replayed_makes_no_write(mini_repo):
    first_entry = _batch_entry("first", "first analysis")
    second_entry = _batch_entry("second", "second analysis")
    for key, entry in (("batch-replay-first-a", first_entry),
                       ("batch-replay-first-b", second_entry)):
        saved = _save(mini_repo, entry["body"], entry["binding"], key,
                       note_id=entry["note_id"], path=entry["path"],
                       title=entry["title"])
        assert saved.returncode == 0, saved.stdout + saved.stderr
    before_files = _transactions(mini_repo)
    before_bytes = {
        entry["note_id"]: (mini_repo / entry["path"]).read_bytes()
        for entry in (first_entry, second_entry)
    }
    result = _save_batch(mini_repo, [first_entry, second_entry],
                          "batch-replay-all")
    assert result.returncode == 0, result.stdout + result.stderr
    response = json.loads(result.stdout)
    assert response["ok"] is True and response["replayed"] is True
    assert response["result"]["created_note_ids"] == []
    assert response["result"]["replayed_note_ids"] == [
        first_entry["note_id"], second_entry["note_id"]]
    assert response["transaction_id"] is None
    assert _transactions(mini_repo) == before_files
    for entry in (first_entry, second_entry):
        assert (mini_repo / entry["path"]).read_bytes() == before_bytes[
            entry["note_id"]]


def test_batch_failed_transaction_writes_nothing(mini_repo, monkeypatch):
    import los
    from learning_os.commands import analysis as analysis_commands
    from learning_os.commands.capability import _dispatch
    from learning_os.commands.support import WriteRefused
    from learning_os.contracts.capability_catalog import command_definitions

    entries = [_batch_entry("txa", "transaction analysis a"),
               _batch_entry("txb", "transaction analysis b")]
    notes = []
    for index, entry in enumerate(entries):
        body_file = mini_repo / f"batch-body-tx-{index}.bin"
        body_file.write_bytes(entry["body"])
        notes.append({
            "analysis": {"id": entry["note_id"], "title": entry["title"],
                         "path": entry["path"], "binding": entry["binding"]},
            "body_file": str(body_file),
            "body_file_sha256": file_sha256(body_file),
        })
    calls = []

    def failing_transaction(root, writes, **kwargs):
        calls.append((dict(writes), dict(kwargs)))
        return 2, ["simulated transaction failure"], {}

    monkeypatch.setattr(analysis_commands, "_write_transaction",
                        failing_transaction)
    definition = command_definitions(mini_repo)["note.analysis.save_batch"]
    with pytest.raises(WriteRefused, match="simulated transaction failure"):
        _dispatch(mini_repo, definition, {"schema_version": 2},
                  {"bundle": {"notes": notes}},
                  parser_factory=los.build_parser)
    assert len(calls) == 1
    assert len(calls[0][0]) == 2
    assert calls[0][1]["capability"] == "note.analysis.save_batch"
    assert sorted(calls[0][1]["artifact_ids"]) == sorted(
        entry["note_id"] for entry in entries)
    for entry in entries:
        assert not (mini_repo / entry["path"]).exists()


def test_batch_bounds_refuse(mini_repo):
    empty = approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({"notes": []}),
        artifact_ids=["note-analysis-batch-empty"],
        idempotency_key="batch-empty",
    )
    assert empty.returncode != 0
    assert "invalid payload" in empty.stdout
    many = [_batch_entry(f"n{index}", f"analysis {index}") for index in range(21)]
    oversized = approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({"notes": _batch_notes(mini_repo, many, "many")}),
        artifact_ids=[entry["note_id"] for entry in many],
        idempotency_key="batch-oversized",
    )
    assert oversized.returncode != 0
    assert "invalid payload" in oversized.stdout
    assert _transactions(mini_repo) == []


def test_batch_handler_bounds_refuse_directly():
    from learning_os.commands.analysis import _read_batch_items
    from learning_os.commands.support import WriteRefused

    with pytest.raises(WriteRefused, match="non-empty notes list"):
        _read_batch_items({"notes": []})
    with pytest.raises(WriteRefused, match="at most 20 per batch"):
        _read_batch_items({"notes": [{}] * 21})


def test_batch_malformed_bundles_are_invalid_payloads(mini_repo):
    missing_notes = approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({}),
        artifact_ids=["note-analysis-batch-malformed"],
        idempotency_key="batch-no-notes",
    )
    assert missing_notes.returncode != 0
    assert "invalid payload" in missing_notes.stdout
    entry = _batch_entry("unbound", "unbound analysis")
    notes = _batch_notes(mini_repo, [entry], "unbound")
    del notes[0]["body_file_sha256"]
    unbound = approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({"notes": notes}),
        artifact_ids=[entry["note_id"]],
        idempotency_key="batch-unbound",
    )
    assert unbound.returncode != 0
    assert "invalid payload" in unbound.stdout
    untitled = _batch_entry("untitled", "untitled analysis")
    notes = _batch_notes(mini_repo, [untitled], "untitled")
    del notes[0]["analysis"]["title"]
    refused = approved_v2_cli(
        mini_repo, "note-analysis-save-batch",
        "--bundle", json.dumps({"notes": notes}),
        artifact_ids=[untitled["note_id"]],
        idempotency_key="batch-untitled",
    )
    assert refused.returncode != 0
    assert "invalid payload" in refused.stdout
    assert _transactions(mini_repo) == []


def test_batch_retry_returns_the_same_breakdown(mini_repo):
    replayed = _batch_entry("retry-kept", "kept analysis")
    created = _batch_entry("retry-new", "new analysis")
    saved = _save(mini_repo, replayed["body"], replayed["binding"],
                   "batch-retry-first", note_id=replayed["note_id"],
                   path=replayed["path"], title=replayed["title"])
    assert saved.returncode == 0, saved.stdout + saved.stderr
    entries = [replayed, created]
    envelope = approved_v2_envelope(
        mini_repo,
        capability="note.analysis.save_batch",
        payload={"bundle": {"notes": _batch_notes(mini_repo, entries, "retry")}},
        artifact_ids=[entry["note_id"] for entry in entries],
        idempotency_key="batch-retry-001",
    )
    first = run_v2_capability(mini_repo, envelope)
    assert first.returncode == 0, first.stdout + first.stderr
    first_response = json.loads(first.stdout)
    assert first_response["ok"] is True
    assert first_response["replayed"] is False
    receipts_before = _transactions(mini_repo)
    # The identical envelope bytes: rebuilding would mint a new intent now
    # that the snapshot and revisions have moved.
    second = run_v2_capability(mini_repo, envelope)
    assert second.returncode == 0, second.stdout + second.stderr
    second_response = json.loads(second.stdout)
    assert second_response["ok"] is True
    assert second_response["replayed"] is True
    assert second_response["transaction_id"] == first_response["transaction_id"]
    assert second_response["receipt_path"] == first_response["receipt_path"]
    assert second_response["result"]["created_note_ids"] == (
        first_response["result"]["created_note_ids"])
    assert second_response["result"]["replayed_note_ids"] == (
        first_response["result"]["replayed_note_ids"])
    assert second_response["result"]["note_paths"] == (
        first_response["result"]["note_paths"])
    assert _transactions(mini_repo) == receipts_before


def test_batch_shape_has_one_source_of_truth(repo_root):
    import los
    from learning_os.commands import analysis as analysis_commands
    from learning_os.contracts import batch_notes
    from learning_os.contracts.payloads import payload_schema, subparsers

    fresh = payload_schema(
        "note.analysis.save_batch",
        subparsers(los.build_parser())["note-analysis-save-batch"])
    schema_path = (repo_root / "system/schema/capabilities"
                   / "note.analysis.save_batch.schema.json")
    on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
    assert on_disk == fresh
    assert on_disk["properties"]["bundle"] == batch_notes.bundle_schema()
    notes_schema = batch_notes.bundle_schema()["properties"]["notes"]
    assert notes_schema["minItems"] == batch_notes.BATCH_MIN_NOTES
    assert notes_schema["maxItems"] == batch_notes.BATCH_MAX_NOTES
    assert analysis_commands.ANALYSIS_FIELDS is batch_notes.ANALYSIS_FIELDS
    assert analysis_commands.BATCH_FIELDS is batch_notes.BATCH_FIELDS
    assert analysis_commands.BATCH_ITEM_FIELDS is batch_notes.BATCH_ITEM_FIELDS
    assert analysis_commands.BATCH_MIN_NOTES == batch_notes.BATCH_MIN_NOTES
    assert analysis_commands.BATCH_MAX_NOTES == batch_notes.BATCH_MAX_NOTES
