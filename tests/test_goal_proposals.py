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
    detect_claims_needing_review,
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
        route_covers={
            "route-1": ["knowledge-a", "knowledge-b"],
            "route-2": ["knowledge-c"],
        },
        node_digest_pins={
            "route-1": {"knowledge-a": "sha256:old-a",
                        "knowledge-b": "sha256:kept-b"},
            "route-2": {"knowledge-c": "sha256:kept-c"},
        },
        live_node_digests={
            "knowledge-a": "sha256:new-a",
            "knowledge-b": "sha256:kept-b",
            "knowledge-c": "sha256:kept-c",
        },
        claim_statuses={"covers:route-1": "supported",
                        "covers:route-2": "supported"},
    )
    assert [goal.goal_id for goal in goals] == [
        "covering-routes-stale:route-1"]
    goal = goals[0]
    assert goal.state == "detected"
    assert "knowledge-a" in goal.rationale
    assert "route:route-1" in goal.evidence


def test_covering_routes_stay_silent_when_digests_match():
    """The proxy-vs-fact pin: byte-identical rows never fire, however
    their files moved in the window the old file-membership trigger
    watched."""
    goals = detect_covering_routes_stale(
        route_covers={"route-1": ["knowledge-a"]},
        node_digest_pins={"route-1": {"knowledge-a": "sha256:same"}},
        live_node_digests={"knowledge-a": "sha256:same"},
        claim_statuses={"covers:route-1": "supported"},
    )
    assert goals == ()


def test_covering_routes_ignore_routes_without_pins():
    """No judged baseline, no verdict: an unclaimed route cannot be
    stale against pins it never recorded."""
    goals = detect_covering_routes_stale(
        route_covers={"route-1": ["knowledge-a"]},
        node_digest_pins={},
        live_node_digests={"knowledge-a": "sha256:anything"},
        claim_statuses={},
    )
    assert goals == ()


def test_covering_routes_fail_closed_on_missing_live_nodes():
    """A pinned node with no live digest (deleted, unreadable,
    ambiguously owned) counts as changed: without bytes to compare,
    the claim cannot stand."""
    (goal,) = detect_covering_routes_stale(
        route_covers={"route-1": ["knowledge-a"]},
        node_digest_pins={"route-1": {"knowledge-a": "sha256:pinned"}},
        live_node_digests={},
        claim_statuses={"covers:route-1": "supported"},
    )
    assert goal.goal_id == "covering-routes-stale:route-1"


def test_source_changes_fire_only_when_the_claims_own_row_moved():
    """New-shape claims compare their own route-content digest: a
    sibling row moving (or its source file) fires nothing here."""
    goals = detect_source_changed_under_claim(
        route_digest_pins={"route-1": "sha256:old-1",
                           "route-2": "sha256:kept-2"},
        live_route_digests={"route-1": "sha256:new-1",
                            "route-2": "sha256:kept-2"},
        route_revision_pins={},
        current_revisions={},
        claim_statuses={"covers:route-1": "supported",
                        "covers:route-2": "supported"},
    )
    assert [goal.goal_id for goal in goals] == [
        "source-changed-under-claim:covers:route-1"]
    assert goals[0].evidence == (
        "claim:covers:route-1", "route:route-1")


def test_source_changes_stay_silent_when_digests_match():
    goals = detect_source_changed_under_claim(
        route_digest_pins={"route-1": "sha256:same"},
        live_route_digests={"route-1": "sha256:same"},
        route_revision_pins={},
        current_revisions={},
        claim_statuses={"covers:route-1": "supported"},
    )
    assert goals == ()


def test_source_changes_old_shape_follows_pinned_revisions():
    """Old-shape claims judged before per-row digests fire only when
    their own pinned revisions moved — never on file membership."""
    pins = {"route-1": {"module-demo": 3}}
    statuses = {"covers:route-1": "supported"}
    silent = detect_source_changed_under_claim(
        route_digest_pins={},
        live_route_digests={},
        route_revision_pins=pins,
        current_revisions={"module-demo": 3},
        claim_statuses=statuses,
    )
    assert silent == ()
    (goal,) = detect_source_changed_under_claim(
        route_digest_pins={},
        live_route_digests={},
        route_revision_pins=pins,
        current_revisions={"module-demo": 4},
        claim_statuses=statuses,
    )
    assert goal.goal_id == "source-changed-under-claim:covers:route-1"
    assert goal.evidence == (
        "claim:covers:route-1", "revision:module-demo")


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


def test_unreviewed_claims_fire_and_reviewed_ones_stay_silent():
    goals = detect_claims_needing_review(
        claims={
            "covers:route-1": {"reviewed_by": "", "status": "supported"},
            "covers:route-2": {"reviewed_by": "aram", "status": "supported"},
        },
    )
    assert [goal.goal_id for goal in goals] == [
        "claims-needing-review:covers:route-1"]
    assert goals[0].state == "detected"
    assert "claim:covers:route-1" in goals[0].evidence


def test_contested_claims_need_a_reviewer_not_a_recompute():
    (goal,) = detect_claims_needing_review(
        claims={"covers:route-1": {"reviewed_by": "aram",
                                   "status": "contested"}},
    )
    assert goal.goal_id == "claims-needing-review:covers:route-1"
    assert goal.title.startswith("Resolve ")
    assert "reviewer" in goal.rationale


def test_stale_and_withdrawn_claims_stay_out_of_review():
    assert detect_claims_needing_review(
        claims={
            "covers:route-1": {"reviewed_by": "", "status": "stale"},
            "covers:route-2": {"reviewed_by": "", "status": "withdrawn"},
        },
    ) == ()


def test_review_signals_fail_closed():
    with pytest.raises(GoalError):
        detect_claims_needing_review(
            claims={"covers:route-1": {"reviewed_by": "",
                                       "status": "judged"}})
    with pytest.raises(GoalError):
        detect_claims_needing_review(
            claims={"covers:route-1": "supported"})


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
            route_covers={"r": "not-a-list"},
            node_digest_pins={},
            live_node_digests={},
            claim_statuses={})
    with pytest.raises(GoalError):
        detect_covering_routes_stale(
            route_covers={"r": ["a"]},
            node_digest_pins={"r": {"a": ""}},
            live_node_digests={},
            claim_statuses={})
    with pytest.raises(GoalError):
        detect_source_changed_under_claim(
            route_digest_pins={},
            live_route_digests={},
            route_revision_pins={"r": {"module-x": True}},
            current_revisions={},
            claim_statuses={"covers:r": "supported"})
    with pytest.raises(GoalError):
        detect_source_changed_under_claim(
            route_digest_pins={"r": "sha256:pinned"},
            live_route_digests={},
            route_revision_pins={},
            current_revisions={},
            claim_statuses={})


def test_row_detectors_skip_contested_and_withdrawn_claims():
    """A moved row under a contested claim needs its reviewer, and
    under a withdrawn claim a fresh judgment — never a re-examination
    goal, however far the row moved."""
    for status in ("contested", "withdrawn"):
        assert detect_source_changed_under_claim(
            route_digest_pins={"route-1": "sha256:old"},
            live_route_digests={"route-1": "sha256:new"},
            route_revision_pins={},
            current_revisions={},
            claim_statuses={"covers:route-1": status},
        ) == ()
        assert detect_covering_routes_stale(
            route_covers={"route-1": ["knowledge-a"]},
            node_digest_pins={"route-1": {"knowledge-a": "sha256:old"}},
            live_node_digests={"knowledge-a": "sha256:new"},
            claim_statuses={"covers:route-1": status},
        ) == ()


def test_review_goals_carry_their_unit_for_clustering():
    goals = detect_claims_needing_review(
        claims={
            "covers:route-1": {"reviewed_by": "", "status": "supported"},
            "covers:route-2": {"reviewed_by": "", "status": "supported"},
            "scope:proof:x": {"reviewed_by": "", "status": "supported"},
        },
        claim_units={"covers:route-1": "unit-a",
                     "covers:route-2": "unit-a"},
    )
    assert [goal.goal_id for goal in goals] == [
        "claims-needing-review:covers:route-1",
        "claims-needing-review:covers:route-2",
        "claims-needing-review:scope:proof:x",
    ]
    assert goals[0].evidence == ("claim:covers:route-1", "unit:unit-a")
    assert goals[1].evidence == ("claim:covers:route-2", "unit:unit-a")
    # No resolvable unit: stands alone, never wrongly grouped.
    assert goals[2].evidence == ("claim:scope:proof:x",)


def test_detectors_write_nothing(tmp_path, monkeypatch):
    """Detectors return records; the only writes are the caller's."""
    monkeypatch.chdir(tmp_path)
    detect_covering_routes_stale(
        route_covers={"r": ["a"]},
        node_digest_pins={"r": {"a": "sha256:pinned"}},
        live_node_digests={"a": "sha256:pinned"},
        claim_statuses={"covers:r": "supported"})
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
