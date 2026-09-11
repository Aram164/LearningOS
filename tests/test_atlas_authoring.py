"""Actual V2 transactions against synthetic records, never the learner's graph."""
import json

import yaml
from gateway_helpers import approved_v2_call
from repo_builders import run_los

OLD = {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}
REGISTRY = "registry-concept-relations"


def change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def test_manual_edit_remove_add_and_replay(mini_repo):
    new = {**OLD, "context": "My own reasoning", "source": "note-demo"}
    result = change(mini_repo, [{"action": "replace", "old": OLD, "new": new}], "edit")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["snapshot_after"]
    result = change(mini_repo, [{"action": "remove", "old": new}], "remove")
    assert result.returncode == 0, result.stdout + result.stderr
    result = change(mini_repo, [{"action": "add", "new": OLD}], "add")
    assert result.returncode == 0, result.stdout + result.stderr
    data = yaml.safe_load((mini_repo / "knowledge/concept-relations.yaml").read_text())
    assert data["relations"] == [OLD]


def test_invalid_batch_rolls_back_and_exact_old_is_required(mini_repo):
    path = mini_repo / "knowledge/concept-relations.yaml"
    before = path.read_bytes()
    for index, row in enumerate((OLD, {"from": OLD["to"], "type": "requires", "to": OLD["from"]},
                                 {**OLD, "to": "concept-missing"}, {**OLD, "source": "note-missing"})):
        result = change(mini_repo, [{"action": "add", "new": row}], f"invalid-{index}")
        assert result.returncode != 0, result.stdout
        assert path.read_bytes() == before
    result = change(mini_repo, [{"action": "remove", "old": {**OLD, "context": "not the original"}}], "wrong-old")
    assert result.returncode != 0
    assert path.read_bytes() == before


def test_question_survives_relation_removal_and_can_reopen(mini_repo):
    note_id = "note-atlas-my-question"
    question = {"id": note_id, "title": "Why?", "text": "Why does this follow?\nMy wording.",
                "target": OLD}
    result = approved_v2_call(mini_repo, capability="atlas.question.save", payload={"question": question},
                              artifact_ids=[note_id], idempotency_key="question")
    assert result.returncode == 0, result.stdout + result.stderr
    result = change(mini_repo, [{"action": "remove", "old": OLD}], "question-edge-remove")
    assert result.returncode == 0, result.stdout + result.stderr
    for state in ("resolved", "open"):
        result = approved_v2_call(mini_repo, capability="atlas.question.save",
                                  payload={"question": {"id": note_id, "state": state, "answer_notes": ["note-demo"]}},
                                  artifact_ids=[note_id], idempotency_key=f"question-{state}")
        assert result.returncode == 0, result.stdout + result.stderr
    result = run_los(mini_repo, "atlas-context", OLD["from"])
    data = json.loads(result.stdout)
    assert data["relations"] == []
    assert data["questions"][0]["target"] == OLD
    assert data["questions"][0]["state"] == "open"
    assert "Why does this follow?\nMy wording." in (mini_repo / f"knowledge/notes/questions/{note_id}.md").read_text()


def test_no_direct_cli_bypass(mini_repo):
    result = run_los(mini_repo, "concept-relations-change", "--change",
                     json.dumps({"operations": [{"action": "remove", "old": OLD}]}))
    assert result.returncode != 0
    assert yaml.safe_load((mini_repo / "knowledge/concept-relations.yaml").read_text())["relations"] == [OLD]
