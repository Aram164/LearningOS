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

import pytest

pytestmark = pytest.mark.full_repo


@pytest.fixture(scope="module")
def manifest(real_manifest) -> dict:
    """The real repository's projection — the authored data is the point here."""
    return real_manifest


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
    derived = {"type", "path", "domain", "domain_bucket", "summary"}
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


def test_published_lifecycle_verdicts_cover_modules_stages_resources_and_workspaces(manifest):
    from learning_os.domain.curriculum.lifecycle import is_retired, is_settled, workspace_is_open
    from learning_os.domain.curriculum.stages import entry_resource, stage_is_open

    assert manifest["modules"]
    for module in manifest["modules"]:
        assert module["is_settled"] is is_settled(module)
        assert module["is_retired"] is is_retired(module)

    assert manifest["stages"]
    for stage in manifest["stages"]:
        assert stage["is_open"] is stage_is_open(stage)
        expected_entry = entry_resource(stage)
        entry_flags = [res["is_entry"] for res in stage["resources"]]
        assert all(isinstance(flag, bool) for flag in entry_flags)
        assert sum(1 for flag in entry_flags if flag) <= 1
        for res in stage["resources"]:
            assert res["is_entry"] is (res is expected_entry)

    workspaces = [r for r in manifest["records"] if r.get("type") == "workspace"]
    assert workspaces
    for ws in workspaces:
        assert ws["is_open"] is workspace_is_open(ws.get("archived"), ws.get("status"))
    open_ids = {ws["id"] for ws in workspaces if ws["is_open"]}
    assert set(manifest["indexes"]["workspace_to_modules"]) <= open_ids
    assert set(manifest["indexes"]["workspace_to_units"]) <= open_ids
