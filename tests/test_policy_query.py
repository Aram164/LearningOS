"""Policy queries answer governance questions with verdicts and reasons.

Predicates own the judgments; this suite pins the query envelope on top:
the shared verdict vocabulary, the per-rule mapping, reasons that cite the
caller's own inputs plus the authority, and fail-closed behavior for
unknown rules and malformed queries.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import POLICY_RULES, PolicyDecision, query
from learning_os.semantics.predicates import CONTRACT_VERSION, PREDICATES


def test_the_rule_set_is_pinned():
    assert set(POLICY_RULES) == {
        "mutation_allowed", "shelving_apply", "critique_action",
        "mastery_check", "note_review", "write_path", "workspace_scope",
    }
    for name, entry in POLICY_RULES.items():
        assert entry["predicate"] in PREDICATES, name
        assert PREDICATES[entry["predicate"]].version == CONTRACT_VERSION
        assert entry["description"]


def test_unknown_rules_fail_closed():
    with pytest.raises(KeyError):
        query("whatever")


def test_malformed_queries_deny_rather_than_raise():
    decision = query("mutation_allowed", capability="route.patch")
    assert decision.verdict == "deny"
    assert decision.reasons


@pytest.mark.parametrize(
    ("rule", "inputs", "verdict"),
    [
        ("mutation_allowed",
         {"capability": "route.patch",
          "target_path": "curriculum/modules/module-hu-aml/source-map.yaml",
          "scopes": ("curriculum/modules/*/source-map.yaml",)},
         "allow"),
        ("mutation_allowed",
         {"capability": "route.patch",
          "target_path": "knowledge/notes/note-x.md",
          "scopes": ("curriculum/modules/*/source-map.yaml",)},
         "deny"),
        ("shelving_apply",
         {"applied_items": ("a",), "approved_items": ("a", "b")},
         "allow"),
        ("shelving_apply",
         {"applied_items": ("c",), "approved_items": ("a", "b")},
         "deny"),
        ("critique_action",
         {"status": "open", "authorized_in_session": True},
         "allow"),
        ("critique_action",
         {"status": "open", "authorized_in_session": False},
         "defer"),
        ("critique_action",
         {"status": "resolved", "authorized_in_session": True},
         "deny"),
        ("mastery_check", {"statement_kind": "resolved"}, "allow"),
        ("mastery_check", {"statement_kind": "exam-passed"}, "deny"),
        ("note_review", {"change_kind": "evidence-append"}, "allow"),
        ("note_review", {"change_kind": "deletion"}, "needs-review"),
        ("write_path", {"channel": "unit.map.import"}, "allow"),
        ("write_path", {"channel": "hand-edit"}, "deny"),
        ("workspace_scope", {"claim_kind": "module_ids"}, "allow"),
        ("workspace_scope", {"claim_kind": "study_map"}, "deny"),
    ],
)
def test_rules_map_to_the_shared_vocabulary(rule, inputs, verdict):
    assert query(rule, **inputs).verdict == verdict


def test_defer_is_not_deny():
    """A deferred point may come back with authorization; a denied mutation
    must not be retried unchanged. The vocabulary keeps that distinction."""
    deferred = query(
        "critique_action", status="open", authorized_in_session=False)
    assert deferred.verdict == "defer"
    assert any("deferred" in reason for reason in deferred.reasons)


def test_unapproved_items_are_named():
    decision = query(
        "shelving_apply", applied_items=("a", "c"), approved_items=("a", "b"))
    assert decision.verdict == "deny"
    assert any("c" in reason for reason in decision.reasons)


def test_every_decision_carries_reasons_predicate_and_authority():
    cases = [
        ("mutation_allowed",
         {"capability": "route.patch",
          "target_path": "curriculum/modules/module-hu-aml/source-map.yaml",
          "scopes": ("curriculum/modules/*/source-map.yaml",)}),
        ("shelving_apply",
         {"applied_items": ("a",), "approved_items": ("a",)}),
        ("critique_action",
         {"status": "open", "authorized_in_session": False}),
        ("mastery_check", {"statement_kind": "open"}),
        ("note_review", {"change_kind": "typo"}),
        ("write_path", {"channel": "route.patch"}),
        ("workspace_scope", {"claim_kind": "unit_ids"}),
    ]
    for rule, inputs in cases:
        decision = query(rule, **inputs)
        assert isinstance(decision, PolicyDecision)
        assert decision.rule == rule
        assert decision.verdict in ("allow", "deny", "defer", "needs-review")
        assert decision.reasons, rule
        assert decision.predicate == POLICY_RULES[rule]["predicate"]
        assert decision.authority, rule
