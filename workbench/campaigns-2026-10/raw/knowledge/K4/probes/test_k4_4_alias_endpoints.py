"""K4 probe 4 — an operation that names an alias instead of a concept id.

ARCHITECTURE §6 makes aliases a read-surface resolution (material-context's
concept filter, concept search); the relation registry stores canonical ids
(ADR-015; the concept-relations schema pins a concept-id pattern). Probed
through the real gateway with two alias shapes:

- a free-form declared alias ("Erwartungswert") — refused by the row schema
  at the handler;
- a declared alias that is itself shaped like a concept id ("concept-ew") —
  passes the handler schema and must die at staged canonical validation as
  an unresolvable endpoint, atomically.
"""
import yaml
from gateway_helpers import approved_v2_call

REGISTRY = "registry-concept-relations"


def _change(root, operations, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": operations}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def _rows(root):
    return yaml.safe_load(
        (root / "knowledge/concept-relations.yaml").read_text())["relations"]


def _add_alias(root, alias):
    path = root / "knowledge/concepts.yaml"
    data = yaml.safe_load(path.read_text())
    data["concepts"][0]["aliases"].append(alias)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def test_free_form_alias_refused_by_the_row_schema(mini_repo):
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _change(mini_repo, [
        {"action": "add", "new": {"from": "Erwartungswert", "type": "requires",
                                  "to": "concept-variance"}}], "alias-free")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}]


def test_id_shaped_alias_refused_as_unresolvable_endpoint(mini_repo):
    """The alias 'concept-ew' passes the row pattern; only endpoint resolution
    can catch it. If this ever commits, the registry holds a non-canonical id
    that atlas.context cannot see — the failure this probe hunts."""
    _add_alias(mini_repo, "concept-ew")
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _change(mini_repo, [
        {"action": "add", "new": {"from": "concept-ew", "type": "requires",
                                  "to": "concept-variance"}}], "alias-shaped")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
    assert _rows(mini_repo) == [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}]


def test_id_shaped_alias_refused_for_replace_too(mini_repo):
    _add_alias(mini_repo, "concept-ew")
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    seeded = {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"}
    result = _change(mini_repo, [
        {"action": "replace", "old": seeded,
         "new": {"from": "concept-ew", "type": "builds-on", "to": "concept-expected-value"}}],
        "alias-shape-replace")
    assert result.returncode != 0, result.stdout + result.stderr
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before
