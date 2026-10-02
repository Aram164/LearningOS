"""Ephemeral session counts feed the three caller-fed detectors.

SessionCounts holds one live session's observations in memory only —
no file IO exists on it, so it cannot become a telemetry log. parse_feed
validates a caller-supplied feed mapping fail-closed, and the scan
serves the question/inspection/correction detectors from it. An empty
feed behaves exactly like no feed.
"""

from __future__ import annotations

import datetime as _dt
import json

import pytest
from repo_builders import run_los

from learning_os.semantics import ScanInput, scan_observations
from learning_os.semantics.goals import (
    DETECTOR_PRECEDENCE,
    GoalCluster,
    rank_clusters,
)
from learning_os.semantics.session_counts import (
    FeedError,
    SessionCounts,
    feed_is_empty,
    feed_scan_kwargs,
    parse_feed,
)

# ---- counters: in-memory, order-insensitive, validated ------------------------


def test_fresh_session_counts_snapshot_empty():
    assert SessionCounts().snapshot() == {
        "question_counts": {},
        "inspection_counts": [],
        "correction_counts": {},
        "voq_classes": [],
        "dossier_sets": [],
    }


def test_counts_accumulate_and_snapshot_sorts():
    counts = SessionCounts()
    counts.note_question("scope-authority")
    counts.note_question("scope-authority")
    counts.note_question("is-clean")
    counts.note_correction("route-repair")
    counts.note_inspection(["b.yaml", "a.yaml"])
    counts.note_inspection(["a.yaml", "b.yaml"])
    assert SessionCounts().snapshot()["question_counts"] == {}
    assert counts.snapshot() == {
        "question_counts": {"is-clean": 1, "scope-authority": 2},
        "inspection_counts": [{"files": ["a.yaml", "b.yaml"], "count": 2}],
        "correction_counts": {"route-repair": 1},
        "voq_classes": [],
        "dossier_sets": [],
    }


def test_blank_classes_and_empty_sets_refuse():
    counts = SessionCounts()
    with pytest.raises(FeedError):
        counts.note_question("  ")
    with pytest.raises(FeedError):
        counts.note_correction("")
    with pytest.raises(FeedError):
        counts.note_inspection([])
    with pytest.raises(FeedError):
        counts.note_inspection("a.yaml")
    with pytest.raises(FeedError):
        counts.note_inspection(["ok.yaml", " "])


def test_note_inspection_dedupes_files_within_one_set():
    counts = SessionCounts()
    counts.note_inspection(["b.yaml", "a.yaml", "b.yaml"])
    assert counts.snapshot()["inspection_counts"] == [
        {"files": ["a.yaml", "b.yaml"], "count": 1}]


def test_counters_hold_no_persistence_surface():
    counts = SessionCounts()
    counts.note_question("scope-authority")
    assert [name for name in dir(counts) if "save" in name or "write" in name
            or "persist" in name or "dump" in name or "store" in name] == []


# ---- feed validation: strict in, shaped out ------------------------------------


def test_parse_feed_defaults_every_section():
    assert parse_feed({}) == {
        "question_counts": {},
        "inspection_counts": [],
        "correction_counts": {},
        "voq_classes": [],
        "dossier_sets": [],
    }


def test_parse_feed_accepts_a_full_feed():
    feed = parse_feed({
        "question_counts": {"scope-authority": 5},
        "inspection_counts": [{"files": ["b.yaml", "a.yaml"], "count": 4}],
        "correction_counts": {"route-repair": 3},
        "voq_classes": ["is-clean"],
        "dossier_sets": [["x.yaml"]],
    })
    assert feed["question_counts"] == {"scope-authority": 5}
    assert feed["inspection_counts"] == [
        {"files": ["b.yaml", "a.yaml"], "count": 4}]
    assert feed["correction_counts"] == {"route-repair": 3}
    assert feed["voq_classes"] == ["is-clean"]
    assert feed["dossier_sets"] == [["x.yaml"]]


def test_parse_feed_refuses_unknown_keys_and_bad_counts():
    with pytest.raises(FeedError):
        parse_feed({"question_counts": {}, "surprise": 1})
    with pytest.raises(FeedError):
        parse_feed({"inspection_counts": [
            {"files": ["a.yaml"], "count": 3, "extra": 0}]})
    with pytest.raises(FeedError):
        parse_feed({"question_counts": {"q": True}})
    with pytest.raises(FeedError):
        parse_feed({"correction_counts": {"q": -1}})
    with pytest.raises(FeedError):
        parse_feed({"question_counts": {"q": "many"}})
    with pytest.raises(FeedError):
        parse_feed({"question_counts": [("q", 1)]})
    with pytest.raises(FeedError):
        parse_feed({"inspection_counts": [{"files": ["a.yaml"]}]})
    with pytest.raises(FeedError):
        parse_feed({"inspection_counts": [{"files": [], "count": 3}]})
    with pytest.raises(FeedError):
        parse_feed({"voq_classes": "is-clean"})
    with pytest.raises(FeedError):
        parse_feed(["not", "a", "mapping"])


def test_parse_feed_refuses_duplicate_inspection_sets():
    with pytest.raises(FeedError):
        parse_feed({"inspection_counts": [
            {"files": ["a.yaml"], "count": 5},
            {"files": ["a.yaml"], "count": 2}]})
    with pytest.raises(FeedError):
        parse_feed({"inspection_counts": [
            {"files": ["a.yaml", "b.yaml"], "count": 5},
            {"files": ["b.yaml", "a.yaml"], "count": 2}]})


def test_feed_scan_kwargs_renders_sorted_scan_tuples():
    kwargs = feed_scan_kwargs({
        "question_counts": {"b-class": 1, "a-class": 4},
        "inspection_counts": [{"files": ["b.yaml", "a.yaml"], "count": 4}],
        "correction_counts": {},
        "voq_classes": ["is-clean"],
        "dossier_sets": [["x.yaml", "w.yaml"]],
    })
    assert kwargs == {
        "question_counts": (("a-class", 4), ("b-class", 1)),
        "inspection_counts": ((("a.yaml", "b.yaml"), 4),),
        "correction_counts": (),
        "voq_classes": ("is-clean",),
        "dossier_sets": (("x.yaml", "w.yaml"),),
    }


def test_feed_scan_kwargs_revalidates_untrusted_input():
    with pytest.raises(FeedError):
        feed_scan_kwargs({"question_counts": {"q": "many"}})


def test_feed_is_empty_only_without_counts():
    assert feed_is_empty(parse_feed({})) is True
    assert feed_is_empty(parse_feed({"voq_classes": ["q"]})) is True
    assert feed_is_empty(parse_feed({"question_counts": {"q": 1}})) is False
    assert feed_is_empty(parse_feed(
        {"inspection_counts": [{"files": ["a.yaml"], "count": 1}]})) is False
    assert feed_is_empty(parse_feed({"correction_counts": {"q": 1}})) is False
    assert feed_is_empty({}) is True


def test_snapshot_round_trips_through_parse_feed():
    counts = SessionCounts()
    counts.note_question("scope-authority")
    counts.note_inspection(["a.yaml"])
    feed = parse_feed(counts.snapshot())
    assert feed["question_counts"] == {"scope-authority": 1}
    assert feed["inspection_counts"] == [{"files": ["a.yaml"], "count": 1}]


# ---- scan wiring: fed detectors fire, unfed stay silent ------------------------


def _fed(**overrides):
    base = {
        "question_counts": (),
        "inspection_counts": (),
        "correction_counts": (),
        "voq_classes": (),
        "dossier_sets": (),
    }
    base.update(overrides)
    return ScanInput(**base)


def test_fed_question_gap_fires_past_threshold_only():
    goals = scan_observations(_fed(
        question_counts=(("scope-authority", 5), ("is-clean", 2))))
    assert [goal.goal_id for goal in goals] == [
        "repeated-question-gap:scope-authority"]


def test_voq_coverage_suppresses_the_gap():
    goals = scan_observations(_fed(
        question_counts=(("scope-authority", 5),),
        voq_classes=("scope-authority",)))
    assert goals == ()


def test_fed_inspection_gap_fires_and_dossier_cover_suppresses():
    fed = _fed(inspection_counts=((("a.yaml", "b.yaml"), 4),))
    (goal,) = scan_observations(fed)
    assert goal.goal_id == "inspection-without-dossier:a.yaml|b.yaml"
    covered = scan_observations(_fed(
        inspection_counts=((("a.yaml", "b.yaml"), 4),),
        dossier_sets=(("a.yaml", "b.yaml", "c.yaml"),)))
    assert covered == ()


def test_fed_correction_pattern_fires_past_threshold_only():
    goals = scan_observations(_fed(
        correction_counts=(("route-repair", 3), ("note-save", 1))))
    assert [goal.goal_id for goal in goals] == [
        "reviewer-correction-pattern:route-repair"]


def test_known_ids_dedup_fed_goals():
    goals = scan_observations(_fed(
        question_counts=(("scope-authority", 5),),
        correction_counts=(("route-repair", 3),),
        known_ids=("repeated-question-gap:scope-authority",)))
    assert [goal.goal_id for goal in goals] == [
        "reviewer-correction-pattern:route-repair"]


def test_empty_feed_matches_no_feed_exactly():
    bare = scan_observations(ScanInput(
        obligations=("unit-a",),
        stale_claims=(("claim-x", ("rev:y",)),),
    ))
    fed_empty = scan_observations(ScanInput(
        obligations=("unit-a",),
        stale_claims=(("claim-x", ("rev:y",)),),
        **feed_scan_kwargs(parse_feed({})),
    ))
    assert fed_empty == bare


# ---- ranking: precedence refines the proximity order ---------------------------


def _ranked_cluster(cluster_id: str, detector: str, *members: str) -> GoalCluster:
    return GoalCluster(cluster_id=cluster_id, detector=detector,
                       title=cluster_id, member_ids=tuple(members))


def test_belief_risk_outranks_fan_out_size_within_a_tier():
    contested = _ranked_cluster("c-contested", "claims-needing-review", "g1")
    obligations = _ranked_cluster(
        "c-obligations", "study-map-obligation", "g2", "g3", "g4")
    ranked = rank_clusters([obligations, contested],
                           today=_dt.date(2026, 9, 28),
                           deadlines=[], module_status={})
    assert [row.cluster.cluster_id for row in ranked] == [
        "c-contested", "c-obligations"]


def test_precedence_covers_every_known_detector():
    assert set(DETECTOR_PRECEDENCE) == {
        "claims-needing-review",
        "lineage-stale",
        "evidence-superseded",
        "source-changed-under-claim",
        "covering-routes-stale",
        "study-map-obligation",
        "reviewer-correction-pattern",
        "repeated-question-gap",
        "inspection-without-dossier",
    }


def test_precedence_orders_every_known_detector():
    detectors = ["inspection-without-dossier", "covering-routes-stale",
                 "lineage-stale", "claims-needing-review",
                 "study-map-obligation", "evidence-superseded",
                 "source-changed-under-claim", "repeated-question-gap",
                 "reviewer-correction-pattern"]
    clusters = [_ranked_cluster(f"c-{detector}", detector, f"g-{detector}")
                for detector in detectors]
    ranked = rank_clusters(clusters, today=_dt.date(2026, 9, 28),
                           deadlines=[], module_status={})
    assert [row.cluster.detector for row in ranked] == [
        "claims-needing-review",
        "lineage-stale",
        "evidence-superseded",
        "source-changed-under-claim",
        "covering-routes-stale",
        "study-map-obligation",
        "reviewer-correction-pattern",
        "repeated-question-gap",
        "inspection-without-dossier",
    ]


def test_unknown_detectors_sort_last_deterministically():
    known = _ranked_cluster("c-known", "lineage-stale", "g1")
    novel = _ranked_cluster("c-novel", "future-detector", "g2")
    ranked = rank_clusters([novel, known], today=_dt.date(2026, 9, 28),
                           deadlines=[], module_status={})
    assert [row.cluster.cluster_id for row in ranked] == ["c-known", "c-novel"]


def test_same_detector_still_breaks_ties_on_size_then_id():
    small = _ranked_cluster("c-a", "lineage-stale", "g1")
    big = _ranked_cluster("c-b", "lineage-stale", "g1", "g2")
    ranked = rank_clusters([small, big], today=_dt.date(2026, 9, 28),
                           deadlines=[], module_status={})
    assert [row.cluster.cluster_id for row in ranked] == ["c-b", "c-a"]


def test_tiers_still_dominate_precedence():
    urgent_obligation = _ranked_cluster(
        "c-urgent", "study-map-obligation", "g1")
    idle_contested = _ranked_cluster(
        "c-idle", "claims-needing-review", "g2")
    ranked = rank_clusters(
        [idle_contested, urgent_obligation], today=_dt.date(2026, 9, 28),
        deadlines=[{"kind": "exam", "module_id": "m",
                    "start_date": "2026-10-05"}],
        module_status={"m": "enrolled"},
        cluster_modules={"c-urgent": {"m"}})
    assert [(row.cluster.cluster_id, row.tier) for row in ranked] == [
        ("c-urgent", 1), ("c-idle", 4)]


# ---- CLI: --feed is read-only input --------------------------------------------


def test_cli_feed_fires_the_count_detectors(mini_repo, tmp_path):
    feed_path = tmp_path / "session-feed.json"
    feed_path.write_text(json.dumps({
        "question_counts": {"scope-authority": 5, "is-clean": 1},
        "correction_counts": {"route-repair": 4},
    }), encoding="utf-8")
    before = feed_path.read_bytes()
    proc = run_los(mini_repo, "intelligence-scan", "--json", "--days", "0",
                   "--feed", str(feed_path))
    assert proc.returncode == 0, proc.stderr
    goal_ids = [goal["goal_id"] for goal in json.loads(proc.stdout)["goals"]]
    assert "repeated-question-gap:scope-authority" in goal_ids
    assert "reviewer-correction-pattern:route-repair" in goal_ids
    assert "repeated-question-gap:is-clean" not in goal_ids
    assert feed_path.read_bytes() == before


def _tree_snapshot(root):
    """Relpath to bytes for every file under root."""
    snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = path.read_bytes()
    return snapshot


def test_cli_fed_scan_writes_nothing_to_the_repo(mini_repo, tmp_path):
    feed_path = tmp_path / "session-feed.json"
    feed_path.write_text(json.dumps({
        "question_counts": {"scope-authority": 5},
        "inspection_counts": [{"files": ["a.yaml", "b.yaml"], "count": 4}],
        "correction_counts": {"route-repair": 3},
    }), encoding="utf-8")
    before = _tree_snapshot(mini_repo)
    proc = run_los(mini_repo, "intelligence-scan", "--days", "0",
                   "--feed", str(feed_path))
    assert proc.returncode == 0, proc.stderr
    assert _tree_snapshot(mini_repo) == before


def test_cli_feed_refuses_gracefully(mini_repo, tmp_path):
    missing = tmp_path / "absent.json"
    proc = run_los(mini_repo, "intelligence-scan", "--feed", str(missing))
    assert proc.returncode == 2
    assert "--feed" in proc.stderr
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    proc = run_los(mini_repo, "intelligence-scan", "--feed", str(broken))
    assert proc.returncode == 2
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"question_counts": {"q": "many"}}),
                         encoding="utf-8")
    proc = run_los(mini_repo, "intelligence-scan", "--feed", str(malformed))
    assert proc.returncode == 2
    assert "malformed feed" in proc.stderr


@pytest.mark.parametrize("value", [None, 1, False, "", "file.yaml", {}, {"x": []}])
def test_dossier_sets_requires_a_list_of_lists(value):
    with pytest.raises(FeedError, match="dossier_sets"):
        parse_feed({"dossier_sets": value})


@pytest.mark.parametrize("raw", [
    b'{"dossier_sets": null}',
    b'{"dossier_sets": {}}',
    b'{"question_counts": {"scope-authority": 5, "scope-authority": 0}}',
    b'{"question_counts": {"scope-authority": 5}, "question_counts": {}}',
    b'{"inspection_counts": [{"files": ["a.yaml"], "count": 4, "count": 0}]}',
    b'\xff',
    b'[' * 1500 + b']' * 1500,
])
def test_cli_feed_refuses_ambiguous_or_unreadable_input_without_writing(
    mini_repo, tmp_path, raw,
):
    feed_path = tmp_path / "untrusted-feed.json"
    feed_path.write_bytes(raw)
    before = _tree_snapshot(mini_repo)
    proc = run_los(mini_repo, "intelligence-scan", "--feed", str(feed_path))
    assert proc.returncode == 2
    assert "--feed" in proc.stderr or "malformed feed" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert _tree_snapshot(mini_repo) == before
    assert feed_path.read_bytes() == raw
