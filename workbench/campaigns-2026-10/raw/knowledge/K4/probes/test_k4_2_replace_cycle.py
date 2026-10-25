"""K4 probe 2 — a prerequisite cycle introduced by a replace, not an add.

C1-C read the cycle refusal; K1 proved the validator's determinism directly.
This probe drives the cycle through the real V2 gateway so the staged
canonical validation rollback is witnessed end to end: the replace that
completes a strict cycle must refuse, leave the registry byte-identical,
and name a deterministic cycle path. The semantic control proves the
refusal is specific to the strict subgraph (ADR-016 decision 4).
"""
import json

import yaml
from gateway_helpers import approved_v2_call

REGISTRY = "registry-concept-relations"
C = "concept-cycle-c"


def _change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def _rows(root):
    return yaml.safe_load(
        (root / "knowledge/concept-relations.yaml").read_text())["relations"]


def _seed_third_concept(root):
    import yaml as _yaml
    path = root / "knowledge/concepts.yaml"
    data = _yaml.safe_load(path.read_text())
    data["concepts"].append({"id": C, "label": "Cycle C"})
    path.write_text(_yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def _seed_open_chain(root):
    """variance builds-on expected-value; expected-value requires C; C motivates variance."""
    _seed_third_concept(root)
    path = root / "knowledge/concept-relations.yaml"
    path.write_text(yaml.safe_dump({"relations": [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "requires", "to": C},
        {"from": C, "type": "motivates", "to": "concept-variance"},
    ]}, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_replace_that_closes_a_strict_cycle_refuses_and_rolls_back(mini_repo):
    _seed_open_chain(mini_repo)
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()

    strict = {"from": C, "type": "requires", "to": "concept-variance"}
    old = {"from": C, "type": "motivates", "to": "concept-variance"}
    result = _change(mini_repo, [{"action": "replace", "old": old, "new": strict}], "cycle-replace")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        {"from": "concept-expected-value", "type": "requires", "to": C},
        {"from": C, "type": "motivates", "to": "concept-variance"},
    ]


def test_cycle_refusal_names_the_cycle_deterministically(mini_repo):
    _seed_open_chain(mini_repo)
    old = {"from": C, "type": "motivates", "to": "concept-variance"}
    strict = {"from": C, "type": "requires", "to": "concept-variance"}
    first = _change(mini_repo, [{"action": "replace", "old": old, "new": strict}], "cycle-msg-1")
    assert first.returncode != 0
    first_body = json.loads(first.stdout)
    assert first_body["error"]["code"] == "VALIDATION_FAILED"
    message = first_body["error"]["message"]
    assert "cycle" in message.lower()
    second = _change(mini_repo, [{"action": "replace", "old": old, "new": strict}], "cycle-msg-2")
    assert second.returncode != 0
    assert json.loads(second.stdout)["error"]["message"] == message, (
        first.stdout, second.stdout)


def test_semantic_replacement_that_would_cycle_still_commits(mini_repo):
    """Control: the same replace shape with a semantic type commits (ADR-016 d4)."""
    _seed_open_chain(mini_repo)
    old = {"from": C, "type": "motivates", "to": "concept-variance"}
    semantic = {"from": C, "type": "contrasts-with", "to": "concept-variance"}
    result = _change(mini_repo, [{"action": "replace", "old": old, "new": semantic}], "semantic-replace")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _rows(mini_repo)[-1] == semantic


def test_add_that_closes_the_same_cycle_refuses_too(mini_repo):
    """The add shape of the same cycle is refused as well (the batch already
    covers unknown-endpoint adds; this pins the cycle code for the add shape)."""
    _seed_third_concept(mini_repo)
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _change(mini_repo, [
        {"action": "add", "new": {"from": "concept-expected-value", "type": "requires", "to": C}},
        {"action": "add", "new": {"from": C, "type": "requires", "to": "concept-variance"}},
    ], "cycle-add")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
