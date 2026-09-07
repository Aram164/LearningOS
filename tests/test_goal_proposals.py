"""Candidate goals: detectors propose, the lifecycle disposes.

Detectors are read-only — they return records, never touch disk — and
thresholded, so a single event is signal, not spam. The lifecycle walks
one step at a time, and only Aram authorizes: anyone else's approval is
refused, and skipping PROPOSED on the way to AUTHORIZED is refused too.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import (
    GoalError,
    detect_covering_routes_stale,
    detect_inspection_without_dossier,
    detect_repeated_question_gap,
    detect_reviewer_correction_pattern,
    detect_source_changed_under_claim,
    goal_from_dict,
    goal_to_dict,
    transition,
)


def test_covering_routes_fire_only_for_their_nodes():
    goals = detect_covering_routes_stale(
        changed_nodes=["knowledge-a"],
        route_covers={
            "route-1": ["knowledge-a", "knowledge-b"],
            "route-2": ["knowledge-c"],
        },
    )
    assert [goal.goal_id for goal in goals] == [
        "covering-routes-stale:route-1"]
    goal = goals[0]
    assert goal.state == "detected"
    assert "knowledge-a" in goal.rationale
    assert "route:route-1" in goal.evidence


def test_source_changes_re_examine_only_pinned_claims():
    goals = detect_source_changed_under_claim(
        changed_sources=["source-a"],
        claim_sources={
            "covers:route-1": ["source-a"],
            "covers:route-2": ["source-b"],
        },
    )
    assert [goal.goal_id for goal in goals] == [
        "source-changed-under-claim:covers:route-1"]


def test_repeated_questions_need_threshold_and_a_gap():
    goals = detect_repeated_question_gap(
        question_counts={"scope": 5, "clean": 2, "mutation": 3},
        voq_classes=["scope", "mutation"],
        threshold=3,
    )
    assert goals == ()


def test_a_real_gap_proposes_a_voq():
    (goal,) = detect_repeated_question_gap(
        question_counts={"lineage": 4},
        voq_classes=["scope"],
        threshold=3,
    )
    assert goal.goal_id == "repeated-question-gap:lineage"
    assert "VOQ" in goal.title


def test_inspections_dedup_by_set_and_defer_to_dossiers():
    counts = {
        ("b.md", "a.md"): 4,
        ("c.md",): 4,
        ("d.md", "e.md"): 2,
    }
    goals = detect_inspection_without_dossier(
        inspection_counts=counts,
        dossier_sets=[["a.md", "b.md", "extra.md"]],
        threshold=3,
    )
    assert [goal.goal_id for goal in goals] == [
        "inspection-without-dossier:c.md"]


def test_reviewer_corrections_blame_the_contract():
    (goal,) = detect_reviewer_correction_pattern(
        correction_counts={"locators": 5, "typos": 1},
        threshold=3,
    )
    assert goal.goal_id == "reviewer-correction-pattern:locators"
    assert "contract" in goal.rationale


def test_known_goals_do_not_refire():
    goals = detect_reviewer_correction_pattern(
        correction_counts={"locators": 5},
        known_ids=["reviewer-correction-pattern:locators"],
    )
    assert goals == ()


def test_malformed_signals_fail_closed():
    with pytest.raises(GoalError):
        detect_repeated_question_gap(
            question_counts={"x": "many"}, voq_classes=[])
    with pytest.raises(GoalError):
        detect_covering_routes_stale(
            changed_nodes=["a"], route_covers={"r": "not-a-list"})


def test_detectors_write_nothing(tmp_path, monkeypatch):
    """Detectors return records; the only writes are the caller's."""
    monkeypatch.chdir(tmp_path)
    detect_covering_routes_stale(
        changed_nodes=["a"], route_covers={"r": ["a"]})
    detect_repeated_question_gap(
        question_counts={"x": 9}, voq_classes=[])
    assert list(tmp_path.iterdir()) == []


def _walk_to_proposed(detector_goals):
    (goal,) = detector_goals
    goal = transition(goal, "formulated")
    goal = transition(goal, "eligible")
    return transition(goal, "proposed")


def test_a_goal_walks_to_closed_only_through_aram():
    proposed = _walk_to_proposed(detect_reviewer_correction_pattern(
        correction_counts={"locators": 5}))
    with pytest.raises(GoalError):
        transition(proposed, "authorized", authorized_by="Muse")
    with pytest.raises(GoalError):
        transition(proposed, "authorized")
    goal = transition(proposed, "authorized", authorized_by="Aram")
    assert goal.authorized_by == "Aram"
    for state in ("planned", "executing", "verified", "closed"):
        goal = transition(goal, state)
    assert goal.state == "closed"
    with pytest.raises(GoalError):
        transition(goal, "detected")


def test_skipping_steps_is_refused():
    (goal,) = detect_repeated_question_gap(
        question_counts={"x": 9}, voq_classes=[])
    with pytest.raises(GoalError):
        transition(goal, "proposed")
    with pytest.raises(GoalError):
        transition(goal, "authorized", authorized_by="Aram")
    with pytest.raises(GoalError):
        transition(goal, "closed")


def test_deferral_rejection_and_supersession():
    (goal,) = detect_repeated_question_gap(
        question_counts={"x": 9}, voq_classes=[])
    goal = transition(goal, "formulated")
    goal = transition(goal, "eligible")
    deferred = transition(goal, "deferred")
    assert transition(deferred, "eligible").state == "eligible"
    with pytest.raises(GoalError):
        transition(goal, "superseded")
    replaced = transition(goal, "superseded", superseded_by="other:1")
    assert replaced.state == "superseded"
    assert replaced.superseded_by == "other:1"
    with pytest.raises(GoalError):
        transition(replaced, "eligible")


def test_stale_goals_re_enter_through_detection():
    (goal,) = detect_repeated_question_gap(
        question_counts={"x": 9}, voq_classes=[])
    stale = transition(goal, "stale")
    assert transition(stale, "detected").state == "detected"


def test_unknown_states_are_refused():
    (goal,) = detect_repeated_question_gap(
        question_counts={"x": 9}, voq_classes=[])
    with pytest.raises(GoalError):
        transition(goal, "shipped")


def test_queue_records_round_trip():
    proposed = _walk_to_proposed(detect_reviewer_correction_pattern(
        correction_counts={"locators": 5}))
    authorized = transition(proposed, "authorized", authorized_by="Aram")
    record = goal_to_dict(authorized)
    assert record["state"] == "authorized"
    assert goal_from_dict(record) == authorized


def test_queue_records_reject_garbage():
    with pytest.raises(GoalError):
        goal_from_dict({"goal_id": "x"})
    with pytest.raises(GoalError):
        goal_from_dict({
            "goal_id": "x", "detector": "d", "title": "t",
            "rationale": "r", "evidence": ["e"], "state": "shipped",
            "authorized_by": "", "superseded_by": "",
        })
