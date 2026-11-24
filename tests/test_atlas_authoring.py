"""Actual V2 transactions against synthetic records, never the learner's graph."""
import json
from pathlib import Path

import jsonschema
import pytest
import yaml
from gateway_helpers import approved_v2_call, approved_v2_envelope, run_v2_capability
from repo_builders import run_los

from learning_os.store.contracts.gateway import intent_sha256

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


def test_atlas_question_payload_schema_types_its_fields(repo_root: Path):
    schema = json.loads((repo_root / "system/schema/capabilities/atlas.question.save.schema.json").read_text())
    question = schema["properties"]["question"]
    assert set(question["properties"]) == {"id", "title", "text", "target", "state", "answer_notes"}
    assert question["required"] == ["id"]
    assert question["additionalProperties"] is False
    validator = jsonschema.Draft202012Validator(schema)
    validator.validate({"question": {"id": "note-atlas-x"}})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"question": {"id": "note-atlas-x", "bogus": 1}})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({"question": {"title": "no id"}})


def test_pinned_row_only_unpins_and_decorated_remove_refused(mini_repo):
    pinned = {**OLD, "pinned": True}
    result = change(mini_repo, [{"action": "replace", "old": OLD, "new": pinned}], "pin")
    assert result.returncode == 0, result.stdout + result.stderr
    # Any other edit to a pinned row is refused.
    result = change(mini_repo, [{"action": "replace", "old": pinned,
                                 "new": {**pinned, "context": "sneaky"}}], "pinned-edit")
    assert result.returncode != 0
    # Hard deletion of a decorated row is refused.
    result = change(mini_repo, [{"action": "remove", "old": pinned}], "pinned-remove")
    assert result.returncode != 0
    # The exact unpin toggle is the one allowed change.
    result = change(mini_repo, [{"action": "replace", "old": pinned,
                                 "new": {**pinned, "pinned": False}}], "unpin")
    assert result.returncode == 0, result.stdout + result.stderr
    data = yaml.safe_load((mini_repo / "knowledge/concept-relations.yaml").read_text())
    assert data["relations"] == [{**OLD, "pinned": False}]
    # Decoration is decided by value, as the app decides it: an unpinned row
    # is removable, so the Remove the app offers after unpinning is admitted.
    result = change(mini_repo, [{"action": "remove", "old": {**OLD, "pinned": False}}], "unpinned-remove")
    assert result.returncode == 0, result.stdout + result.stderr


def test_retract_requires_reason_and_keeps_history(mini_repo):
    result = change(mini_repo, [{"action": "replace", "old": OLD,
                                 "new": {**OLD, "status": "retracted"}}], "retract-noreason")
    assert result.returncode != 0
    retracted = {**OLD, "status": "retracted", "status_reason": "superseded by review"}
    result = change(mini_repo, [{"action": "replace", "old": OLD, "new": retracted}], "retract")
    assert result.returncode == 0, result.stdout + result.stderr
    data = yaml.safe_load((mini_repo / "knowledge/concept-relations.yaml").read_text())
    assert data["relations"] == [retracted]


def test_evidence_state_precedence():
    from learning_os.domain.relations import enriched_relation, evidence_state
    assert evidence_state({}) == "missing"
    assert evidence_state({"evidence": [{"source_id": "source-x"}]}) == "verified"
    assert evidence_state({"evidence": [{"source_id": "source-x"}]}, ["stale"]) == "stale"
    assert evidence_state({"evidence_disputed": True,
                           "evidence": [{"source_id": "source-x"}]}, ["stale"]) == "disputed"
    old = {"from": "concept-a", "type": "requires", "to": "concept-b"}
    assert enriched_relation(old)["status"] == "active"
    assert "status" not in old  # stored rows are not rewritten by projection


def test_atlas_question_save_refuses_a_non_object_target(mini_repo):
    result = run_los(mini_repo, "atlas-question-save", "--question",
                     json.dumps({"id": "note-atlas-new", "title": "T",
                                 "text": "Why?", "target": "concept-expected-value"}))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "question target must be an object" in result.stderr


# ---- origin and the Atlas keeper (ADR-024 amendment, 2026-11-23) -------------

ADDED = {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"}
DELEGATION = "system/contracts/delegations/atlas-keeper.yaml"


def change_as(root, channel, operations, key):
    """One envelope from `channel`: `ui` is Aram's click, `system-task` the keeper."""
    envelope = approved_v2_envelope(
        root, capability="concept.relations.change",
        payload={"change": {"operations": operations}},
        artifact_ids=[REGISTRY], idempotency_key=key)
    envelope["channel"] = channel
    if channel == "ui":
        envelope["approval"]["kind"] = "direct-user-gesture"
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return run_v2_capability(root, envelope)


def _delegate(root, **overrides):
    """A delegation that stays valid whenever the suite runs."""
    fields = {"schema_version": 1, "delegate": "atlas-keeper", "granted_by": "aram",
              "granted": "2026-01-01", "expires": "2099-12-31", "status": "active",
              "capability": "concept.relations.change", "channel": "system-task",
              "max_operations": 50, **overrides}
    lines = [f"{key}: {value}" for key, value in fields.items()]
    (root / DELEGATION).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _cited(root, row=ADDED):
    from test_practice_verification import _binding
    return {**row, "evidence": [_binding(root)]}


def _relations(root):
    return yaml.safe_load((root / "knowledge/concept-relations.yaml").read_text())["relations"]


def test_the_shipped_delegation_has_the_declared_shape(repo_root: Path):
    data = yaml.safe_load((repo_root / DELEGATION).read_text())
    assert data["status"] in {"active", "suspended"}
    assert data["channel"] == "system-task"
    assert data["capability"] == "concept.relations.change"
    assert 1 <= data["max_operations"] <= 50
    assert data["granted"] <= data["expires"]


def test_app_additions_are_recorded_as_arams(mini_repo):
    result = change_as(mini_repo, "ui", [{"action": "add", "new": ADDED}], "ui-add")
    assert result.returncode == 0, result.stdout + result.stderr
    assert {**ADDED, "origin": "aram"} in _relations(mini_repo)
    claimed = change_as(mini_repo, "ui", [{"action": "add", "new": {
        "from": "concept-variance", "type": "motivates", "to": "concept-expected-value",
        "origin": "pilot"}}], "ui-claims-pilot")
    assert claimed.returncode != 0 and "is recorded as origin aram" in claimed.stdout + claimed.stderr


def test_keeper_writes_only_under_an_active_delegation(mini_repo):
    cited = _cited(mini_repo)
    (mini_repo / DELEGATION).unlink()
    for state, key in ((None, "missing"), ({"status": "suspended"}, "suspended"),
                       ({"expires": "2020-01-01", "granted": "2019-01-01"}, "expired")):
        if state is not None:
            _delegate(mini_repo, **state)
        result = change_as(mini_repo, "system-task", [{"action": "add", "new": cited}], f"keeper-{key}")
        assert result.returncode != 0, key
        assert "has no active delegation" in result.stdout + result.stderr, key
    assert cited not in _relations(mini_repo)


def test_keeper_adds_cited_relations_as_pilot_with_a_receipt(mini_repo):
    _delegate(mini_repo)
    cited = _cited(mini_repo)
    uncited = change_as(mini_repo, "system-task", [{"action": "add", "new": ADDED}], "keeper-uncited")
    assert uncited.returncode != 0 and "must cite at least one verified quote" in uncited.stdout + uncited.stderr
    result = change_as(mini_repo, "system-task", [{"action": "add", "new": cited}], "keeper-add")
    assert result.returncode == 0, result.stdout + result.stderr
    assert {**cited, "origin": "pilot"} in _relations(mini_repo)
    receipt = json.loads(result.stdout)["receipt_path"]
    assert '"channel": "system-task"' in (mini_repo / receipt).read_text() \
        or "channel: system-task" in (mini_repo / receipt).read_text()


def test_keeper_leaves_arams_decisions_alone(mini_repo):
    _delegate(mini_repo)
    pinned = {**OLD, "pinned": True}
    assert change(mini_repo, [{"action": "replace", "old": OLD, "new": pinned}], "pin").returncode == 0
    mine = {**ADDED, "origin": "aram"}
    assert change_as(mini_repo, "ui", [{"action": "add", "new": ADDED}], "mine").returncode == 0
    cited_mine = {**mine, "evidence": _cited(mini_repo)["evidence"]}
    attempts = {
        "unpin": ([{"action": "replace", "old": pinned, "new": {**pinned, "pinned": False}}],
                  "Aram authored or pinned are his"),
        "remove": ([{"action": "remove", "old": pinned}], "never deletes one"),
        "edit-arams": ([{"action": "replace", "old": mine, "new": cited_mine}],
                       "Aram authored or pinned are his"),
        "claim-aram": ([{"action": "add", "new": {**_cited(mini_repo, {
            "from": "concept-variance", "type": "motivates", "to": "concept-expected-value"}),
            "origin": "aram"}}], "never changes a relation's origin"),
    }
    for key, (operations, reason) in attempts.items():
        result = change_as(mini_repo, "system-task", operations, f"keeper-{key}")
        assert result.returncode != 0, key
        assert reason in result.stdout + result.stderr, (key, result.stdout + result.stderr)
    assert pinned in _relations(mini_repo) and mine in _relations(mini_repo)


def test_keeper_may_ground_and_retract_unpinned_pilot_rows(mini_repo):
    _delegate(mini_repo)
    grounded = _cited(mini_repo, OLD)
    result = change_as(mini_repo, "system-task",
                       [{"action": "replace", "old": OLD, "new": grounded}], "keeper-ground")
    assert result.returncode == 0, result.stdout + result.stderr
    vetoed = {**grounded, "status": "vetoed", "status_reason": "not in the lecture"}
    refused = change_as(mini_repo, "system-task",
                        [{"action": "replace", "old": grounded, "new": vetoed}], "keeper-veto")
    assert refused.returncode != 0 and "are Aram's decisions" in refused.stdout + refused.stderr
    retracted = {**grounded, "status": "retracted", "status_reason": "superseded by a direct source"}
    result = change_as(mini_repo, "system-task",
                       [{"action": "replace", "old": grounded, "new": retracted}], "keeper-retract")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _relations(mini_repo) == [retracted]


def test_keeper_rejects_datetime_delegation_fields(mini_repo):
    for field in ("expires", "granted"):
        _delegate(mini_repo, **{field: "2099-12-31T00:00:00+00:00"})
        result = change_as(
            mini_repo, "system-task", [{"action": "add", "new": _cited(mini_repo)}],
            f"keeper-dt-{field}")
        assert result.returncode != 0
        assert "does not have the declared shape" in result.stdout + result.stderr


def test_keeper_cannot_revive_or_retract_vetoed_rows(mini_repo):
    _delegate(mini_repo)
    vetoed = {**OLD, "status": "vetoed", "status_reason": "contradicted by exam"}
    assert change_as(
        mini_repo, "ui", [{"action": "replace", "old": OLD, "new": vetoed}],
        "aram-veto").returncode == 0
    revive = change_as(
        mini_repo, "system-task",
        [{"action": "replace", "old": vetoed, "new": _cited(mini_repo, OLD)}],
        "keeper-revive-vetoed")
    assert revive.returncode != 0
    assert "vetoed relations are Aram's decision" in revive.stdout + revive.stderr
    retract = change_as(
        mini_repo, "system-task",
        [{"action": "replace", "old": vetoed,
          "new": {**_cited(mini_repo, OLD), "status": "retracted", "status_reason": "retry"}}],
        "keeper-retract-vetoed")
    assert retract.returncode != 0
    assert "vetoed relations are Aram's decision" in retract.stdout + retract.stderr
    assert _relations(mini_repo) == [vetoed]


def test_add_refuses_duplicate_identity_across_statuses(mini_repo):
    dup_active = change(mini_repo, [{"action": "add", "new": OLD}], "dup-active")
    assert dup_active.returncode != 0
    assert "already exists with status active" in dup_active.stdout + dup_active.stderr

    retracted = {**OLD, "status": "retracted", "status_reason": "superseded"}
    assert change(mini_repo, [{"action": "replace", "old": OLD, "new": retracted}],
                  "to-retracted").returncode == 0
    dup_retracted = change(mini_repo, [{"action": "add", "new": OLD}], "dup-retracted")
    assert dup_retracted.returncode != 0
    assert "already exists with status retracted" in dup_retracted.stdout + dup_retracted.stderr

    vetoed = {**OLD, "status": "vetoed", "status_reason": "contradicted by exam"}
    assert change(mini_repo, [{"action": "replace", "old": retracted, "new": vetoed}],
                  "to-vetoed").returncode == 0
    dup_vetoed = change(mini_repo, [{"action": "add", "new": OLD}], "dup-vetoed")
    assert dup_vetoed.returncode != 0
    out = dup_vetoed.stdout + dup_vetoed.stderr
    assert "already exists with status vetoed" in out and "fresh evidence" in out
