"""K1 invariant 4 (ADR-016 decision 4): a cycle among requires/builds-on fails
validation with REL-PREREQ-CYCLE and one deterministic path; the same cycle
among semantic types passes. Check lives in
tools/learning_os/derive/validation/registries.py::_prerequisite_cycle."""

from __future__ import annotations

import yaml

from learning_os.derive.validation import Validator
from learning_os.store.loader import load_repo


def _with_relations(mini_repo, relations):
    (mini_repo / "knowledge/concept-relations.yaml").write_text(
        yaml.safe_dump({"relations": relations}, sort_keys=False), encoding="utf-8")
    return mini_repo


def _cycle_issues(root):
    issues = Validator(load_repo(root)).run()
    return [str(i.message) for i in issues if i.code == "REL-PREREQ-CYCLE"]


STRICT_CYCLE = [
    {"from": "concept-expected-value", "type": "requires", "to": "concept-variance"},
    {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
]


def test_strict_cycle_fails_with_one_deterministic_path(mini_repo):
    root = _with_relations(mini_repo, STRICT_CYCLE)
    first = _cycle_issues(root)
    assert len(first) == 1, first
    assert first[0].startswith("prerequisite cycle: ")
    # The reported path is a real closed walk over strict edges.
    path = first[0].removeprefix("prerequisite cycle: ").split(" -> ")
    assert path[0] == path[-1] and len(path) >= 2
    # Same repository, second validation: byte-identical report.
    assert _cycle_issues(root) == first


def test_strict_cycle_path_is_independent_of_relation_file_order(mini_repo):
    """Determinism survives the authored file order: the reversed list yields
    the identical message."""
    a = _with_relations(mini_repo, STRICT_CYCLE)
    message_a = _cycle_issues(a)
    import copy
    import tempfile
    from conftest import build_mini_repo
    with tempfile.TemporaryDirectory() as tmp:
        other = build_mini_repo(tmp_path=__import__("pathlib").Path(tmp))
        _with_relations(other, list(reversed(STRICT_CYCLE)))
        message_b = _cycle_issues(other)
    assert message_a == message_b


def test_three_concept_strict_cycle_names_the_whole_walk(mini_repo):
    root = _with_relations(mini_repo, [
        {"from": "concept-expected-value", "type": "requires", "to": "concept-variance"},
        {"from": "concept-variance", "type": "requires", "to": "concept-expected-value"},
    ][:1] + [
        {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
    ])
    # Keep the fixture honest: this is the 2-cycle in mixed strict types.
    assert _cycle_issues(root) == [
        "prerequisite cycle: concept-expected-value -> concept-variance "
        "-> concept-expected-value"]


def test_self_loop_is_a_cycle(mini_repo):
    root = _with_relations(mini_repo, [
        {"from": "concept-expected-value", "type": "requires",
         "to": "concept-expected-value"},
    ])
    assert _cycle_issues(root) == [
        "prerequisite cycle: concept-expected-value -> concept-expected-value"]


def test_semantic_cycle_passes_validation(mini_repo):
    """ADR-016 decision 4: semantic relations may cycle freely."""
    root = _with_relations(mini_repo, [
        {"from": "concept-expected-value", "type": "motivates", "to": "concept-variance"},
        {"from": "concept-variance", "type": "derives", "to": "concept-expected-value"},
    ])
    assert _cycle_issues(root) == []


def test_mixed_graph_catches_only_the_strict_subgraph(mini_repo):
    """A semantic 2-cycle between the same concepts plus a strict 2-cycle:
    exactly the strict one is reported."""
    root = _with_relations(mini_repo, [
        *STRICT_CYCLE,
        {"from": "concept-expected-value", "type": "contrasts-with", "to": "concept-variance"},
        {"from": "concept-variance", "type": "contrasts-with", "to": "concept-expected-value"},
    ])
    issues = _cycle_issues(root)
    assert len(issues) == 1
    assert "contrasts-with" not in issues[0]
