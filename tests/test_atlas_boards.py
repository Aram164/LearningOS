"""P2 board templates: deterministic, scoped, active-only (synthetic repo)."""
import hashlib
import json

from learning_os.derive.projection.atlas_boards import build_atlas_boards
from learning_os.store.loader import load_repo


def _boards(mini_repo):
    repo = load_repo(mini_repo)
    indexes = {
        "module_to_concepts": {"module-demo": ["concept-expected-value", "concept-variance"]},
        "unit_to_concepts": {},
    }
    return build_atlas_boards(repo, indexes)


def test_board_catalog_and_template_are_deterministic(mini_repo):
    catalog, files = _boards(mini_repo)
    catalog2, files2 = _boards(mini_repo)
    assert catalog == catalog2
    assert files == files2
    module = [c for c in catalog if c["kind"] == "module"]
    assert len(module) == 1
    entry = module[0]
    assert entry["working_path"] == "boards/atlas/module/module-demo.canvas"
    assert entry["concept_count"] == 2
    assert entry["relation_count"] == 1
    template = files[entry["template_path"]]
    assert hashlib.sha256(template.encode()).hexdigest() == entry["sha256"]
    canvas = json.loads(template)
    ids = [n["id"] for n in canvas["nodes"]]
    assert ids == sorted(ids)
    assert "los-concept-concept-variance" in ids
    assert canvas["edges"][0]["id"] == (
        "los-rel-concept-variance--builds-on--concept-expected-value")


def test_concept_cards_carry_no_answer_text(mini_repo):
    _catalog, files = _boards(mini_repo)
    card = files["generated/atlas/cards/concept-variance.md"]
    assert "GENERATED file" in card
    assert "Evidence: missing" in card


def test_retracted_relation_leaves_the_template(mini_repo):
    path = mini_repo / "knowledge/concept-relations.yaml"
    path.write_text(
        "relations:\n"
        "- from: concept-variance\n  type: builds-on\n  to: concept-expected-value\n"
        "  status: retracted\n  status_reason: superseded\n")
    catalog, files = _boards(mini_repo)
    entry = [c for c in catalog if c["kind"] == "module"][0]
    assert entry["relation_count"] == 0
    assert json.loads(files[entry["template_path"]])["edges"] == []


def test_semester_and_exam_use_declared_membership_and_checked_items(mini_repo):
    from test_practice_verification import BANK_SOLUTION, _base_record, _binding, _note, _record

    from learning_os.domain.snapshot import Note, Program, Unit

    _note(mini_repo, "note-practice-bank", "exercise-bank", BANK_SOLUTION)
    assert _record(mini_repo, _base_record(_binding(mini_repo)), "board-proof").returncode == 0
    repo = load_repo(mini_repo)
    repo.programs["program-a"] = Program("program-a", mini_repo, {"semesters": [
        {"id": "semester-sose-2026"}, {"id": "semester-wise-2026"},
    ]})
    repo.modules["module-demo"] = {"area_id": "program-a", "semester": "sose-2026"}
    repo.modules["module-other"] = {"area_id": "program-a", "semester": "wise-2026"}
    exam_id = "note-synthetic-mock"
    repo.notes[exam_id] = Note(exam_id, mini_repo, {
        "role": "mock-exam", "concepts": ["concept-variance"],
    }, "")
    repo.units["unit-demo"] = Unit("unit-demo", mini_repo, {
        "artifacts": {"mock_exam": exam_id},
    }, "module-demo")
    catalog, cards = build_atlas_boards(repo, {"module_to_concepts": {
        "module-demo": ["concept-expected-value"], "module-other": ["concept-variance"],
    }})
    entries = {entry["id"]: entry for entry in catalog}
    assert entries["module-demo"]["parent_id"] == "program-a--semester-sose-2026"
    assert entries["module-other"]["parent_id"] == "program-a--semester-wise-2026"
    for semester in ("sose", "wise"):
        assert entries[f"program-a--semester-{semester}-2026"]["concept_count"] == 1
    assert entries[exam_id]["parent_id"] == "module-demo"
    expected = cards["generated/atlas/cards/concept-expected-value.md"]
    assert "Verified practice: 1" in expected
    assert "What is 2+2" not in expected
