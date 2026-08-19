"""The projection must carry every field the schema allows — and no others.

Both schemas are closed (`additionalProperties: false`), so the set of fields
an interface can ever receive is decidable from the schema alone. Before this
test the evaluation projection emitted six of the schema's nine fields plus one
the schema has never allowed, so 87 authored `level` judgments and 18
`audience` notes stopped at the repository boundary while every consumer read a
`verdict` that could only be null.

Field-by-field assertions would drift the moment a schema field is added, which
is exactly how the gap appeared. These compare the two sets instead.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from learning_os.genout import generate_all
from learning_os.loader import load_repo


pytestmark = pytest.mark.full_repo

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def manifest() -> dict:
    """The real repository's projection — the authored data is the point here."""
    return json.loads(generate_all(load_repo(ROOT), "T1")["manifest.json"])


def _schema(root, name):
    return json.loads((root / "system/schema" / name).read_text())


def _evaluation_schema_fields(root):
    schema = _schema(root, "sources.schema.json")
    node = schema["properties"]["sources"]["items"]["properties"]["evaluations"]["items"]
    assert node.get("additionalProperties") is False, (
        "this test is only sound while the evaluation schema is closed"
    )
    return set(node["properties"])


def _note_schema_fields(root):
    schema = _schema(root, "note.schema.json")
    assert schema.get("additionalProperties") is False, (
        "this test is only sound while the note schema is closed"
    )
    return set(schema["properties"])


def test_every_evaluation_field_reaches_the_projection(repo_root, manifest):
    """No pedagogical judgment may stop at the repository boundary."""
    allowed = _evaluation_schema_fields(repo_root)
    projected = {
        key
        for record in manifest["records"]
        if record.get("type") == "source"
        for evaluation in (record.get("evaluations") or [])
        for key in evaluation
    }
    assert projected, "no evaluations were projected at all"

    missing = allowed - projected
    assert not missing, (
        f"the schema allows {sorted(missing)} but the projection drops them; "
        "an interface cannot render a judgment it never receives"
    )

    invented = projected - allowed
    assert not invented, (
        f"the projection emits {sorted(invented)}, which the closed evaluation "
        "schema does not allow — it can only ever be null"
    )


def test_every_note_field_reaches_the_projection(repo_root, manifest):
    """Note life — provenance and semantic review — is part of the record."""
    allowed = _note_schema_fields(repo_root)
    notes = [r for r in manifest["records"] if r.get("type") == "note"]
    assert notes, "no notes were projected at all"
    projected = {key for note in notes for key in note}

    # The projection adds navigational keys the schema has no reason to carry.
    derived = {"type", "path", "domain", "summary"}
    missing = allowed - projected - {"created"}
    assert not missing, (
        f"the note schema allows {sorted(missing)} but the projection drops them"
    )

    invented = projected - allowed - derived
    assert not invented, (
        f"the projection emits {sorted(invented)}, which the closed note schema "
        "does not allow"
    )


def test_authored_level_judgments_survive_the_projection(repo_root, manifest):
    """A regression guard with teeth: the count must not silently fall to zero."""
    levels = [
        evaluation["level"]
        for record in manifest["records"]
        if record.get("type") == "source"
        for evaluation in (record.get("evaluations") or [])
        if evaluation.get("level")
    ]
    assert levels, (
        "no evaluation reached the projection carrying a level, but the "
        "registry authors them — the field is being dropped again"
    )
    assert set(levels) <= {"introductory", "intermediate", "advanced", "reference"}


def test_authored_note_provenance_survives_the_projection(manifest):
    carried = [
        note for note in manifest["records"]
        if note.get("type") == "note" and note.get("transcription") is not None
    ]
    assert carried, (
        "no note reached the projection carrying its transcription state, but "
        "handwritten notes author it — the field is being dropped again"
    )
