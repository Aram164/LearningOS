"""Write-payload clarity: named refusals, declared input shapes, seal guidance.

#100 names the unknown fields (and the accepted ones) in the note,
analysis and question refusals, with a dedicated message when the id is
missing. #93 declares every opaque ``json_object`` payload field's
accepted input shape so ``capabilities NAME --json`` shows it. #105
teaches ``seal_envelope.py --guards auto`` to tell a bad payload from
underivable guards, and adds id suggestions to the write handlers'
not-found refusals.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_cli, file_sha256
from repo_builders import (
    _compact_revision,
    add_curriculum,
    material_fixture,
    run_los,
    write_yaml,
)
from test_learning_paths import add_path

from learning_os.commands.note import NOTE_FIELDS
from learning_os.commands.support import WriteRefused
from learning_os.contracts.batch_notes import ANALYSIS_FIELDS

# ------------------------------------------------------------------ #100


def test_note_precheck_names_the_unknown_fields():
    from learning_os.commands.note import _precheck_note

    with pytest.raises(WriteRefused) as refused:
        _precheck_note(
            {"id": "note-x", "title": "T", "domain": "math", "role": "synthesis"},
            b"body",
        )
    message = str(refused.value)
    assert "note has unknown fields: domain" in message
    assert (
        "accepted: id, title, path, role, concepts, sources, contexts, "
        "supersedes" in message
    )
    assert "type/created/state/authorship/semantic_review are set by the handler" in message


def test_note_precheck_gives_a_missing_id_its_own_message():
    from learning_os.commands.note import _precheck_note

    with pytest.raises(WriteRefused, match="^note needs a string id$"):
        _precheck_note({"title": "T"}, b"body")
    # An unknown field still wins over a missing id: one refusal, the
    # actionable one.
    with pytest.raises(WriteRefused, match="unknown fields: domain"):
        _precheck_note({"title": "T", "domain": "math"}, b"body")


def test_analysis_precheck_names_the_unknown_fields():
    from learning_os.commands.analysis import _precheck_analysis

    with pytest.raises(WriteRefused) as refused:
        _precheck_analysis({"id": "note-x", "title": "T", "domain": "math"}, b"body")
    message = str(refused.value)
    assert "analysis has unknown fields: domain" in message
    assert "accepted: id, title, path, binding" in message
    assert "type/created/state/authorship/semantic_review are set by the handler" in message


def test_analysis_precheck_gives_a_missing_id_its_own_message():
    from learning_os.commands.analysis import _precheck_analysis

    with pytest.raises(WriteRefused, match="^analysis needs a string id$"):
        _precheck_analysis({"title": "T"}, b"body")


def test_question_save_names_the_unknown_fields(mini_repo):
    result = run_los(
        mini_repo, "atlas-question-save", "--question",
        json.dumps({"id": "note-q", "title": "T", "domain": "math"}),
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "question has unknown fields: domain" in result.stderr
    assert "accepted: id, title, text, target, state, answer_notes" in result.stderr
    assert "type/role/created/authorship are set by the handler" in result.stderr


def test_question_save_gives_a_missing_id_its_own_message(mini_repo):
    result = run_los(
        mini_repo, "atlas-question-save", "--question",
        json.dumps({"title": "T"}),
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "question needs a string id" in result.stderr


# ------------------------------------------------------------------- #93

SCHEMA_DIR = "system/schema/capabilities"


def _capability_schema(repo_root, name):
    return json.loads(
        (repo_root / SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def test_every_opaque_payload_field_declares_its_accepted_shape(repo_root):
    """A new ``json_object`` payload field without a declaration fails here.

    Declare it once: a ``payload_records`` entry in
    ``system/contracts/capabilities.yaml`` (inline accepted fields, a
    ``record_schema`` pointer, or documented ``freeform``), or a
    contract-module fragment in ``contracts/payloads._NESTED_SCHEMAS`` —
    then regenerate with ``tools/generate_capability_schemas.py``.
    """
    import los
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.contracts.payload_records import resolve_all
    from learning_os.contracts.payloads import (
        _NESTED_SCHEMAS,
        json_object_fields,
        subparsers,
    )

    commands = subparsers(los.build_parser())
    declared = set(resolve_all(repo_root)) | set(_NESTED_SCHEMAS)
    missing, dangling = [], []
    for name, definition in command_definitions(repo_root).items():
        command_parser = commands.get(definition.cli_command or "")
        if command_parser is None:
            continue
        for field in sorted(json_object_fields(command_parser)):
            if (name, field) not in declared:
                missing.append(f"{name}.{field}")
    for name, field in sorted(declared):
        definition = command_definitions(repo_root).get(name)
        command_parser = commands.get(definition.cli_command or "") \
            if definition is not None else None
        if command_parser is None or field not in json_object_fields(command_parser):
            dangling.append(f"{name}.{field}")
    assert not missing, (
        "opaque payload fields without a declared accepted shape: "
        + ", ".join(missing)
    )
    assert not dangling, (
        "declarations naming no json_object payload field: " + ", ".join(dangling)
    )


def test_no_payload_schema_is_a_bare_object_anymore(repo_root):
    for path in sorted((repo_root / SCHEMA_DIR).glob("*.schema.json")):
        properties = json.loads(path.read_text(encoding="utf-8"))["properties"]
        for field, fragment in properties.items():
            assert fragment != {"type": "object"}, (
                f"{path.stem}.{field} is still opaque"
            )


def test_note_and_analysis_shapes_mirror_their_handlers(repo_root):
    note = _capability_schema(repo_root, "note.create")["properties"]["note"]
    assert note["additionalProperties"] is False
    assert set(note["properties"]) == set(NOTE_FIELDS)
    assert set(note["required"]) == {"id", "title", "path"}
    analysis = _capability_schema(
        repo_root, "note.analysis.save")["properties"]["analysis"]
    assert analysis["additionalProperties"] is False
    assert set(analysis["properties"]) == set(ANALYSIS_FIELDS)
    assert set(analysis["required"]) == set(ANALYSIS_FIELDS)


def test_intake_revise_and_collection_shapes_mirror_their_handlers(repo_root):
    from learning_os.commands.collection_entry import REVISE_FIELDS as COLLECTION_FIELDS
    from learning_os.commands.source_catalog import (
        CORRECT_FIELDS,
        CREATE_FIELDS,
        REVISE_FIELDS,
    )

    intake = _capability_schema(
        repo_root, "source.intake.record")["properties"]["record"]
    assert set(intake["properties"]) == {"records"}
    items = intake["properties"]["records"]["items"]
    assert items["additionalProperties"] is False
    assert set(items["properties"]) == set(CREATE_FIELDS | CORRECT_FIELDS)
    assert set(items["required"]) == {"action", "id"}
    revise = _capability_schema(
        repo_root, "source.record.revise")["properties"]["record"]
    assert revise["additionalProperties"] is False
    assert set(revise["properties"]) == set(REVISE_FIELDS)
    assert set(revise["required"]) == {"id"}
    collection = _capability_schema(
        repo_root, "collection.entry.revise")["properties"]["record"]
    assert collection["additionalProperties"] is False
    assert set(collection["properties"]) == set(COLLECTION_FIELDS)
    assert set(collection["required"]) == set(COLLECTION_FIELDS)


def test_route_concept_review_and_unit_shapes_mirror_their_handlers(repo_root):
    from learning_os.material_refs import PATCH_FIELDS

    changes = _capability_schema(repo_root, "route.patch")["properties"]["changes"]
    assert changes["additionalProperties"] is False
    assert set(changes["properties"]) == set(PATCH_FIELDS)
    assert changes["minProperties"] == 1
    change = _capability_schema(
        repo_root, "concept.relations.change")["properties"]["change"]
    assert set(change["properties"]) == {"operations"}
    operations = change["properties"]["operations"]["items"]
    assert operations["additionalProperties"] is False
    assert set(operations["properties"]) == {"action", "old", "new"}
    review = _capability_schema(
        repo_root, "route.identity.migrate")["properties"]["review"]
    assert review["additionalProperties"] is False
    assert set(review["properties"]) == {
        "schema_version", "basis_plan_sha256", "basis_snapshot_sha256",
        "decisions",
    }
    assert set(review["required"]) == set(review["properties"])
    revision = _capability_schema(repo_root, "unit.plan.revise")["properties"]["record"]
    assert revision["additionalProperties"] is False
    assert set(revision["properties"]) == {
        "unit_id", "plan_contract", "route_changes", "study_map",
        "material_synthesis", "claim_evidence", "acknowledgments",
    }
    assert set(revision["required"]) == {"plan_contract"}


def _record_top_level(repo_root, path):
    """Top-level (properties, required) of a record schema, through $ref."""
    schema = json.loads((repo_root / path).read_text(encoding="utf-8"))
    target = schema
    while isinstance(target.get("$ref"), str):
        node = schema
        for part in target["$ref"][2:].split("/"):
            node = node[part]
        target = node
    return set(target["properties"]), set(target.get("required", []))


def test_full_record_shapes_derive_from_their_record_schemas(repo_root):
    cases = [
        ("project.create", "project", "system/schema/project.schema.json",
         {"schema_version"}),
        ("project.update", "project", "system/schema/project.schema.json",
         {"schema_version"}),
        ("module.plan.import", "promotion",
         "system/schema/master-planning-promotion.schema.json", set()),
        ("masters-planning.catalog.update", "record",
         "system/schema/master-planning-catalog.schema.json", set()),
        ("masters-planning.comparison.publish", "record",
         "system/schema/candidate-source-comparison.schema.json", set()),
        ("legacy.archive.lock.publish", "record",
         "system/schema/legacy-archive-lock.schema.json", set()),
        ("unit.material-synthesis.publish", "record",
         "system/schema/unit-material-synthesis.schema.json", set()),
    ]
    for name, field, record_path, defaulted in cases:
        fragment = _capability_schema(repo_root, name)["properties"][field]
        names, required = _record_top_level(repo_root, record_path)
        assert fragment["additionalProperties"] is False, name
        assert set(fragment["properties"]) == names, name
        # The handler defaults `defaulted` itself; everything else the
        # stored record requires is required inline too.
        assert set(fragment["required"]) == required - defaulted, name
        assert record_path in fragment["description"], name


def test_the_artifact_map_is_documented_as_free_form(repo_root):
    fragment = _capability_schema(
        repo_root, "ai-action.delivery.apply")["properties"]["artifact_sha256"]
    assert fragment["type"] == "object"
    assert "additionalProperties" not in fragment
    assert "Free-form map" in fragment["description"]


def test_capabilities_note_create_shows_the_accepted_note_fields(mini_repo):
    result = run_los(mini_repo, "capabilities", "note.create", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    note = payload["payload_schema"]["properties"]["note"]
    assert set(note["properties"]) == set(NOTE_FIELDS)
    assert note["additionalProperties"] is False
    assert "note.schema.json" in note["description"]


def _sealed_note(mini_repo, key, record):
    body_file = mini_repo / f"body-{key}.bin"
    body_file.write_bytes(b"clarity probe body")
    return approved_v2_cli(
        mini_repo, "note-create",
        "--note", json.dumps(record),
        "--body-file", str(body_file),
        "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[record.get("id", "note-missing")], idempotency_key=key,
    )


def test_an_unknown_note_field_refuses_at_payload_validation(mini_repo):
    path = "knowledge/notes/mathematics/note-clarity-unknown.md"
    result = _sealed_note(mini_repo, "clarity-unknown", {
        "id": "note-clarity-unknown", "title": "T", "path": path,
        "domain": "math",
    })
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "invalid payload" in combined
    assert "domain" in combined
    assert not (mini_repo / path).exists(), "refused before any transaction work"


def test_a_note_missing_a_required_field_refuses_at_payload_validation(mini_repo):
    result = _sealed_note(mini_repo, "clarity-no-title", {
        "id": "note-clarity-no-title",
        "path": "knowledge/notes/mathematics/note-clarity-no-title.md",
    })
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "invalid payload" in combined
    assert "title" in combined


# ------------------------------------------------------------------ #105

SEAL = Path(__file__).resolve().parent.parent / "tools" / "seal_envelope.py"


def _seal(root: Path, out: Path, *, capability: str, payload: dict, key: str):
    return subprocess.run(
        [sys.executable, str(SEAL), "--root", str(root),
         "--capability", capability, "--payload", json.dumps(payload),
         "--key", key, "--guards", "auto", "--out", str(out)],
        capture_output=True, text=True, timeout=120)


def test_stage_writes_suggest_the_units_stage_ids(mini_repo):
    add_curriculum(mini_repo)
    note = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-dem",
                   "--text", "x")
    assert note.returncode == 2
    assert "stage not found: stage-dem" in note.stderr
    assert "did you mean" in note.stderr
    assert "stage-demo" in note.stderr
    progress = run_los(mini_repo, "stage-progress", "unit-demo-l01", "stage-dem",
                       "active")
    assert progress.returncode == 2
    assert "stage-demo" in progress.stderr
    feedback = run_los(mini_repo, "source-feedback", "unit-demo-l01", "stage-dem",
                       "source-demo-book", "helpful")
    assert feedback.returncode == 2
    assert "stage-demo" in feedback.stderr
    detour = run_los(mini_repo, "detour-create", "unit-demo-l01", "stage-dem",
                     "--title", "Gap", "--classification", "deferred")
    assert detour.returncode == 2
    assert "stage-demo" in detour.stderr


def test_stage_writes_suggest_unit_ids(mini_repo):
    add_curriculum(mini_repo)
    result = run_los(mini_repo, "stage-note", "unit-demo-l1", "stage-demo",
                     "--text", "x")
    assert result.returncode == 2
    assert "unit not found: unit-demo-l1" in result.stderr
    assert "unit-demo-l01" in result.stderr


def test_path_writes_suggest_path_and_stage_ids(mini_repo):
    add_path(mini_repo)
    stage = run_los(mini_repo, "path-note", "path-demo-probability", "stage-on",
                    "--text", "x")
    assert stage.returncode == 2
    assert "stage not found: stage-on" in stage.stderr
    assert "stage-one" in stage.stderr
    path = run_los(mini_repo, "path-note", "path-demo-probabilit", "stage-one",
                   "--text", "x")
    assert path.returncode == 2
    assert "active learning path not found: path-demo-probabilit" in path.stderr
    assert "path-demo-probability" in path.stderr


def test_route_patch_suggests_the_units_route_ids(mini_repo):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    result = run_los(mini_repo, "route-patch", unit_id, rid[:-1],
                     "--changes", json.dumps({"angle": "Changed"}), "--check")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "missing or ambiguous" in result.stderr
    assert rid in result.stderr


def test_seal_with_a_bad_stage_id_says_fix_the_payload(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="stage.note.write",
                   payload={"unit_id": "unit-demo-l01",
                            "stage_id": "stage-dem-counting",
                            "text": "mistyped stage"},
                   key="clarity-seal-bad-stage-001")
    assert sealed.returncode == 2
    assert "stage not found: stage-dem-counting" in sealed.stderr
    assert "did you mean" in sealed.stderr
    assert "stage-demo" in sealed.stderr
    assert "fix the payload and seal again" in sealed.stderr
    assert "explicit --revision" not in sealed.stderr


def test_seal_without_a_transaction_keeps_the_explicit_revision_advice(
        mini_repo, tmp_path):
    repo, rid, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="route.patch",
                   payload={"unit_id": unit_id, "route_id": rid,
                            "changes": {"angle": "A checked change"},
                            "check": True},
                   key="clarity-seal-check-001")
    assert sealed.returncode == 2, sealed.stdout + sealed.stderr
    assert "explicit --revision" in sealed.stderr
    assert "fix the payload" not in sealed.stderr


# ------------------------------------------------------- #114 item 1: refusals
#
# The write handlers that still printed a bare id now suggest through
# the shared helper, like the #84/#105 reads and stage writes.


def test_unit_map_import_suggests_unit_ids(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    draft = tmp_path / "map.yaml"
    draft.write_text("unit_id: unit-demo-l1\n", encoding="utf-8")
    proc = run_los(mini_repo, "unit-map-import", "unit-demo-l1",
                   "--file", str(draft))
    assert proc.returncode == 2
    assert "unit not found: unit-demo-l1" in proc.stderr
    assert "unit-demo-l01" in proc.stderr


def test_unit_source_selection_suggests_unit_and_source_ids(mini_repo):
    add_curriculum(mini_repo)
    unit = run_los(mini_repo, "unit-source-selection", "unit-demo-l1",
                   "source-demo-book", "§1", "select")
    assert unit.returncode == 2
    assert "unit not found: unit-demo-l1" in unit.stderr
    assert "unit-demo-l01" in unit.stderr
    source = run_los(mini_repo, "unit-source-selection", "unit-demo-l01",
                     "source-dem", "§1", "select")
    assert source.returncode == 2
    assert "source not found: source-dem" in source.stderr
    assert "source-demo-book" in source.stderr


def test_detour_resolve_suggests_detour_ids(mini_repo):
    add_curriculum(mini_repo)
    study_map = (mini_repo / "curriculum/modules/module-demo/units"
                 / "unit-demo-l01/study-map.yaml")
    data = yaml.safe_load(study_map.read_text(encoding="utf-8"))
    data["detours"] = [{"id": "detour-expected-value-gap", "title": "Gap",
                        "spawned_by_stage": "stage-demo",
                        "classification": "deferred", "status": "open",
                        "return_to_stage": "stage-demo"}]
    write_yaml(study_map, data)
    proc = run_los(mini_repo, "detour-resolve", "unit-demo-l01",
                   "detour-expected-value")
    assert proc.returncode == 2
    assert "detour not found: detour-expected-value" in proc.stderr
    assert "detour-expected-value-gap" in proc.stderr


def test_source_feedback_suggests_source_and_resource_ids(mini_repo):
    add_curriculum(mini_repo)
    source = run_los(mini_repo, "source-feedback", "unit-demo-l01",
                     "stage-demo", "source-dem", "helpful")
    assert source.returncode == 2
    assert "source not found: source-dem" in source.stderr
    assert "source-demo-book" in source.stderr
    resource = run_los(mini_repo, "source-feedback", "unit-demo-l01",
                       "stage-demo", "source-demo-book", "helpful",
                       "--resource-id", "resource-demo-book-ch0")
    assert resource.returncode == 2
    assert "resource not found on stage stage-demo" in resource.stderr
    assert "resource-demo-book-ch01" in resource.stderr
    assert "known:" in resource.stderr


def test_note_writes_suggest_note_ids(mini_repo, tmp_path):
    revised = tmp_path / "revised.md"
    revised.write_text("---\nid: note-dem\n---\nbody\n", encoding="utf-8")
    revise = run_los(mini_repo, "note-revise", "note-dem",
                     "--file", str(revised), "--approve")
    assert revise.returncode == 2
    assert "note not found: note-dem" in revise.stderr
    assert "note-demo" in revise.stderr
    evidence = run_los(mini_repo, "note-evidence", "note-dem",
                       "derivation", "material://demo/x.pdf")
    assert evidence.returncode == 2
    assert "note not found: note-dem" in evidence.stderr
    assert "note-demo" in evidence.stderr


def test_module_attempt_suggests_module_ids(mini_repo):
    add_curriculum(mini_repo)
    proc = run_los(mini_repo, "module-attempt", "module-dem",
                   "--termin", "2", "--date", "2026-10-09",
                   "--result", "registered")
    assert proc.returncode == 2
    assert "module not found: module-dem" in proc.stderr
    assert "module-demo" in proc.stderr


def test_module_plan_import_suggests_module_ids(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    package = tmp_path / "compact.yaml"
    write_yaml(package, {"module_id": "module-dem",
                         "unit_revisions": [{"unit_id": "unit-demo-l01"}]})
    proc = run_los(mini_repo, "module-plan-import", "module-dem",
                   "--file", str(package), "--check")
    assert proc.returncode == 2
    assert "module not found: module-dem" in proc.stderr
    assert "module-demo" in proc.stderr


def test_unit_plan_revise_suggests_unit_ids(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    revision = tmp_path / "revision.yaml"
    write_yaml(revision, _compact_revision(mini_repo, unit_id="unit-demo-l1"))
    proc = run_los(mini_repo, "unit-plan-revise", "unit-demo-l1",
                   "--file", str(revision), "--check")
    assert proc.returncode == 2
    assert "unit not found: unit-demo-l1" in proc.stderr
    assert "unit-demo-l01" in proc.stderr
