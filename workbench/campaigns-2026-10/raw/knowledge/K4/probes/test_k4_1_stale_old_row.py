"""K4 probe 1 — concept.relations.change with a stale exact-previous row.

C1-C read this handler without probing it. The attack: a row that WAS the
unique previous row at some earlier point but is no longer, offered as the
exact old row of a replace or remove after another change committed. The
handler must refuse (old-not-found), and the registry must be untouched.
"""
import json

import yaml
from gateway_helpers import approved_v2_call

REGISTRY = "registry-concept-relations"
OLD = {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}
REPLACED = {**OLD, "context": "replaced by session one"}


def _change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def _rows(root):
    return yaml.safe_load(
        (root / "knowledge/concept-relations.yaml").read_text())["relations"]


def test_remove_with_row_staled_by_an_earlier_replace_refuses(mini_repo):
    result = _change(mini_repo, [{"action": "replace", "old": OLD, "new": REPLACED}], "s1")
    assert result.returncode == 0, result.stdout + result.stderr
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()

    result = _change(mini_repo, [{"action": "remove", "old": OLD}], "stale-remove")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [REPLACED]


def test_replace_with_row_staled_by_an_earlier_replace_refuses(mini_repo):
    result = _change(mini_repo, [{"action": "replace", "old": OLD, "new": REPLACED}], "s1")
    assert result.returncode == 0, result.stdout + result.stderr
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()

    newer = {**OLD, "context": "replaced by session two"}
    result = _change(mini_repo, [{"action": "replace", "old": OLD, "new": newer}], "stale-replace")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [REPLACED]


def test_stale_old_refusal_is_the_exact_previous_row_refusal(mini_repo):
    result = _change(mini_repo, [{"action": "replace", "old": OLD, "new": REPLACED}], "s1")
    assert result.returncode == 0, result.stdout + result.stderr
    combined = ""
    result = _change(mini_repo, [{"action": "remove", "old": OLD}], "stale-msg")
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "no longer exists uniquely" in combined
