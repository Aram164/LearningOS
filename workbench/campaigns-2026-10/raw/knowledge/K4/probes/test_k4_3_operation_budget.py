"""K4 probe 3 — the 50-operation budget of concept.relations.change.

The capability payload declares 1..50 operations and the handler re-checks
it. Probed through the real gateway: exactly 50 explicit adds commit in one
transaction; 51 refuse before anything moves; a batch whose late operation
fails staged validation (a duplicate edge) commits nothing.
"""
import json

import yaml
from gateway_helpers import approved_v2_call

REGISTRY = "registry-concept-relations"
EXTRA = [f"concept-bulk-{i}" for i in range(3, 9)]  # six more concepts: 30 ordered pairs
TYPES = ["requires", "builds-on", "derives", "generalizes",
         "contrasts-with", "equivalent-to", "applies-in", "motivates"]


def _change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def _rows(root):
    return yaml.safe_load(
        (root / "knowledge/concept-relations.yaml").read_text())["relations"]


def _seed_bulk_concepts(root):
    path = root / "knowledge/concepts.yaml"
    data = yaml.safe_load(path.read_text())
    data["concepts"].extend({"id": cid, "label": f"Bulk {cid}"} for cid in EXTRA)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


SEMANTIC_TYPES = ["derives", "generalizes", "contrasts-with",
                  "equivalent-to", "applies-in", "motivates"]


def _fifty_distinct_adds():
    """50 distinct semantic rows over the six bulk concepts.

    Semantic types only: a strict edge plus its reverse would be a real
    prerequisite cycle, which validation correctly refuses regardless of
    the operation budget under test.
    """
    rows = []
    for frm in EXTRA:
        for to in EXTRA:
            if frm == to:
                continue
            for rtype in SEMANTIC_TYPES:
                rows.append({"from": frm, "type": rtype, "to": to})
                if len(rows) == 50:
                    return rows
    raise AssertionError("fixture could not produce 50 distinct rows")


def test_fifty_operations_commit_in_one_transaction(mini_repo):
    _seed_bulk_concepts(mini_repo)
    adds = [{"action": "add", "new": row} for row in _fifty_distinct_adds()]
    assert len(adds) == 50
    result = _change(mini_repo, adds, "bulk-50")
    assert result.returncode == 0, result.stdout + result.stderr
    body = json.loads(result.stdout)["result"]
    assert body["operation_count"] == 50
    assert len(_rows(mini_repo)) == 51  # the seeded variance edge plus fifty


def test_fifty_one_operations_refuse_and_commit_nothing(mini_repo):
    _seed_bulk_concepts(mini_repo)
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    adds = [{"action": "add", "new": row} for row in _fifty_distinct_adds()]
    adds.append({"action": "add", "new": {"from": EXTRA[0], "type": TYPES[0], "to": EXTRA[1]}})
    # the 51st must still be distinct to isolate the budget refusal
    adds[-1] = {"action": "add", "new": {"from": EXTRA[0], "type": TYPES[0], "to": EXTRA[2]}}
    assert len(adds) == 51
    result = _change(mini_repo, adds, "bulk-51")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}]


def test_late_duplicate_inside_one_batch_commits_nothing(mini_repo):
    """REL-DUP is caught by staged validation after the handler accepted the
    batch; the rollback must leave the registry byte-identical."""
    row = {"from": "concept-variance", "type": "requires", "to": "concept-expected-value"}
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _change(mini_repo, [
        {"action": "add", "new": row},
        {"action": "add", "new": {**row, "context": "innocent middle operation"}},
        {"action": "add", "new": row},
    ], "bulk-dup")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before


def test_empty_operations_refuse(mini_repo):
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _change(mini_repo, [], "bulk-empty")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
