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
    return build_atlas_boards(repo, indexes, "T")


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
