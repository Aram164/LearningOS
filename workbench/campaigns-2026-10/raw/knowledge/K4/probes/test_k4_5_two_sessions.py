"""K4 probe 5 — two sessions changing different rows under one snapshot.

Both envelopes are built from the same pre-state (same snapshot token, same
registry revision). Session A commits its replace. Session B then submits
its replace of a different row:

- with the stale snapshot token: refused as a snapshot conflict (STALE_SNAPSHOT);
- with the snapshot token omitted entirely: refused at admission — the V2
  envelope schema makes the token mandatory, so no token-less path reaches
  the transaction at all.

Neither session's change may land as a silent lost update, and the exact
replay of A's envelope answers replayed:true with no second write.
"""
import json

import yaml
from gateway_helpers import approved_v2_envelope, run_v2_capability
from learning_os.store.contracts.gateway import intent_sha256

REGISTRY = "registry-concept-relations"
R1 = {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}


def _seed_second_row(root):
    path = root / "knowledge/concept-relations.yaml"
    path.write_text(yaml.safe_dump({"relations": [
        R1,
        {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"},
    ]}, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _rows(root):
    return yaml.safe_load(
        (root / "knowledge/concept-relations.yaml").read_text())["relations"]


def test_second_session_on_a_stale_snapshot_refuses(mini_repo):
    _seed_second_row(mini_repo)
    r2 = {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"}
    envelope_a = approved_v2_envelope(
        mini_repo, capability="concept.relations.change",
        payload={"change": {"operations": [
            {"action": "replace", "old": R1, "new": {**R1, "context": "session A"}}]}},
        artifact_ids=[REGISTRY], idempotency_key="session-a")
    envelope_b = approved_v2_envelope(
        mini_repo, capability="concept.relations.change",
        payload={"change": {"operations": [
            {"action": "replace", "old": r2, "new": {**r2, "context": "session B"}}]}},
        artifact_ids=[REGISTRY], idempotency_key="session-b")

    result_a = run_v2_capability(mini_repo, envelope_a)
    assert result_a.returncode == 0, result_a.stdout + result_a.stderr
    result_b = run_v2_capability(mini_repo, envelope_b)
    assert result_b.returncode != 0, result_b.stdout + result_b.stderr
    combined = result_b.stdout + result_b.stderr
    assert "snapshot" in combined.lower() or "conflict" in combined.lower()
    rows = _rows(mini_repo)
    assert rows[0] == {**R1, "context": "session A"}
    assert rows[1] == r2  # B's change never landed


def test_envelope_without_a_snapshot_token_is_refused_at_admission(mini_repo):
    """The V2 envelope schema makes expected_snapshot mandatory: a session
    trying to skip the snapshot guard and rely on the registry-revision
    guard alone cannot even submit. (No token-less path exists for this
    capability, so the revision guard has no reachable lost-update race
    through the gateway — the snapshot guard answers the two-session case.)"""
    _seed_second_row(mini_repo)
    r2 = {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"}
    envelope_a = approved_v2_envelope(
        mini_repo, capability="concept.relations.change",
        payload={"change": {"operations": [
            {"action": "replace", "old": R1, "new": {**R1, "context": "session A"}}]}},
        artifact_ids=[REGISTRY], idempotency_key="session-a2")
    envelope_c = approved_v2_envelope(
        mini_repo, capability="concept.relations.change",
        payload={"change": {"operations": [
            {"action": "replace", "old": r2, "new": {**r2, "context": "session C"}}]}},
        artifact_ids=[REGISTRY], idempotency_key="session-c")
    del envelope_c["expected_snapshot"]  # omit the token entirely
    envelope_c["approval"]["subject_sha256"] = intent_sha256(envelope_c)

    result_a = run_v2_capability(mini_repo, envelope_a)
    assert result_a.returncode == 0, result_a.stdout + result_a.stderr
    result_c = run_v2_capability(mini_repo, envelope_c)
    assert result_c.returncode != 0, result_c.stdout + result_c.stderr
    body = json.loads(result_c.stdout)
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert "invalid capability envelope" in body["error"]["message"]
    rows = _rows(mini_repo)
    assert rows[0] == {**R1, "context": "session A"}
    assert rows[1] == r2


def test_exact_replay_of_the_committed_session_answers_replayed(mini_repo):
    _seed_second_row(mini_repo)
    envelope_a = approved_v2_envelope(
        mini_repo, capability="concept.relations.change",
        payload={"change": {"operations": [
            {"action": "replace", "old": R1, "new": {**R1, "context": "session A"}}]}},
        artifact_ids=[REGISTRY], idempotency_key="session-a3")
    first = run_v2_capability(mini_repo, envelope_a)
    assert first.returncode == 0, first.stdout + first.stderr
    second = run_v2_capability(mini_repo, envelope_a)
    assert second.returncode == 0, second.stdout + second.stderr
    body = json.loads(second.stdout)
    assert body.get("replayed") is True
    assert _rows(mini_repo)[0] == {**R1, "context": "session A"}
