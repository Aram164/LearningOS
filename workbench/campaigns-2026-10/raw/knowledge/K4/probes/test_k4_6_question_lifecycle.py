"""K4 probe 6 — atlas.question.save lifecycle around a vanishing target.

C1-C never probed this capability (its finding 1 only witnessed the
retarget refusal). Driven here through the real V2 gateway:

- a question on an authored relation saves, and atlas.context lists it from
  BOTH endpoints;
- removing the relation commits (ADR-017 consequences: removal deletes an
  assertion, never the question) and the question keeps its recorded target;
- a NEW question on the now-removed relation refuses;
- the same wording saved twice is one note under replay and under a same-id
  update, and two notes under two ids (a question's identity is its note id,
  ADR-017 decision 4);
- a mixed target shape and an alias target are refused by the note schema
  before any handler target logic runs.
"""
import json

import yaml
from gateway_helpers import approved_v2_call, approved_v2_envelope, run_v2_capability
from repo_builders import run_los

R1 = {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}
WORDING = {"title": "Why does dispersion need the mean?",
           "text": "My own wording:\ncan variance exist without a mean?"}


def _change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=["registry-concept-relations"],
                            idempotency_key=key)


def _save_question(root, question, key, note_id):
    return approved_v2_call(root, capability="atlas.question.save",
                            payload={"question": question},
                            artifact_ids=[note_id], idempotency_key=key)


def test_question_on_a_relation_lists_from_both_endpoints(mini_repo):
    note_id = "note-atlas-k4-relation-q"
    question = {"id": note_id, **WORDING, "target": R1}
    result = _save_question(mini_repo, question, "k4-q-save", note_id)
    assert result.returncode == 0, result.stdout + result.stderr
    body = json.loads(result.stdout)["result"]
    assert body["note_path"] == f"knowledge/notes/questions/{note_id}.md"
    for concept in (R1["from"], R1["to"]):
        listing = json.loads(run_los(mini_repo, "atlas-context", concept).stdout)
        assert listing["relations"] == [R1]
        assert [q["id"] for q in listing["questions"]] == [note_id]
        assert listing["questions"][0]["target"] == R1


def test_removing_the_target_relation_keeps_the_question_and_the_wording(mini_repo):
    note_id = "note-atlas-k4-removed-target"
    result = _save_question(mini_repo, {"id": note_id, **WORDING, "target": R1},
                            "k4-r-save", note_id)
    assert result.returncode == 0, result.stdout + result.stderr
    result = _change(mini_repo, [{"action": "remove", "old": R1}], "k4-r-remove")
    assert result.returncode == 0, result.stdout + result.stderr

    note_text = (mini_repo / f"knowledge/notes/questions/{note_id}.md").read_text()
    assert WORDING["text"] in note_text
    for concept in (R1["from"], R1["to"]):
        listing = json.loads(run_los(mini_repo, "atlas-context", concept).stdout)
        assert listing["relations"] == []
        assert [q["id"] for q in listing["questions"]] == [note_id]
        assert listing["questions"][0]["target"] == R1
        assert listing["questions"][0]["state"] == "open"

    # A NEW question on the now-removed relation refuses.
    second = "note-atlas-k4-second-on-removed"
    result = _save_question(
        mini_repo, {"id": second, **WORDING, "target": R1}, "k4-r-second", second)
    assert result.returncode != 0, result.stdout + result.stderr
    assert not (mini_repo / f"knowledge/notes/questions/{second}.md").exists()


def test_same_wording_saved_twice_is_one_note_under_replay_and_update(mini_repo):
    note_id = "note-atlas-k4-twice"
    question = {"id": note_id, **WORDING, "target": {"concepts": ["concept-variance"]}}
    first_envelope = approved_v2_envelope(
        mini_repo, capability="atlas.question.save", payload={"question": question},
        artifact_ids=[note_id], idempotency_key="k4-twice-1")
    first = run_v2_capability(mini_repo, first_envelope)
    assert first.returncode == 0, first.stdout + first.stderr
    before = (mini_repo / f"knowledge/notes/questions/{note_id}.md").read_bytes()

    replay = run_v2_capability(mini_repo, first_envelope)  # the exact envelope, resubmitted
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout).get("replayed") is True

    update = _save_question(mini_repo, question, "k4-twice-2", note_id)
    assert update.returncode == 0, update.stdout + update.stderr
    assert json.loads(update.stdout)["result"]["replayed"] is False
    assert (mini_repo / f"knowledge/notes/questions/{note_id}.md").read_bytes() == before
    saved = yaml.safe_load(
        (mini_repo / f"knowledge/notes/questions/{note_id}.md").read_text().split("---")[1])
    assert saved["atlas_question"]["target"] == {"concepts": ["concept-variance"]}
    notes_on_disk = list((mini_repo / "knowledge/notes/questions").glob("*.md"))
    assert [p.stem for p in notes_on_disk] == [note_id]


def test_same_wording_under_two_ids_creates_two_question_notes(mini_repo):
    first_id = "note-atlas-k4-wording-a"
    second_id = "note-atlas-k4-wording-b"
    target = {"concepts": ["concept-expected-value"]}
    for note_id, key in ((first_id, "k4-w-a"), (second_id, "k4-w-b")):
        result = _save_question(mini_repo, {"id": note_id, **WORDING, "target": target},
                                key, note_id)
        assert result.returncode == 0, result.stdout + result.stderr
    listing = json.loads(run_los(mini_repo, "atlas-context", "concept-expected-value").stdout)
    assert [q["id"] for q in listing["questions"]] == [first_id, second_id]
    assert all(q["title"] == WORDING["title"] for q in listing["questions"])


def test_mixed_and_alias_targets_are_schema_refused(mini_repo):
    questions_dir = mini_repo / "knowledge/notes/questions"
    before = sorted(p.name for p in questions_dir.glob("*.md")) if questions_dir.exists() else []
    mixed = {"id": "note-atlas-k4-mixed", **WORDING,
             "target": {"concepts": ["concept-variance"],
                        "from": "concept-variance", "type": "requires",
                        "to": "concept-expected-value"}}
    result = _save_question(mini_repo, mixed, "k4-mixed", "note-atlas-k4-mixed")
    assert result.returncode != 0, result.stdout + result.stderr
    alias = {"id": "note-atlas-k4-alias", **WORDING,
             "target": {"concepts": ["Erwartungswert"]}}
    result = _save_question(mini_repo, alias, "k4-alias", "note-atlas-k4-alias")
    assert result.returncode != 0, result.stdout + result.stderr
    after = sorted(p.name for p in questions_dir.glob("*.md")) if questions_dir.exists() else []
    assert after == before
