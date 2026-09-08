"""Intelligence scan: observe the live world, interpret, propose.

Pure assembly tests run on synthetic observations (fast); CLI tests run
against the synthetic mini repo (no history, no ledger, no curriculum
units — the scan observes nothing and says so) plus one full-repo run
proving the command works on the checked-in state.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.semantics import ScanInput, intelligence_scan, scan_observations

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def _input(**overrides):
    fields = {
        "changed_nodes": (),
        "route_covers": (),
        "changed_sources": (),
        "claim_sources": (),
        "stale_claims": (),
        "obligations": (),
        "known_ids": (),
    }
    fields.update(overrides)
    return ScanInput(**fields)


def test_empty_observations_propose_nothing():
    assert scan_observations(_input()) == ()


def test_changed_nodes_reach_covering_routes():
    goals = scan_observations(_input(
        changed_nodes=("knowledge-a",),
        route_covers=(("route-1", ("knowledge-a", "knowledge-b")),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("covering-routes-stale:route-1", "covering-routes-stale")]
    assert goals[0].state == "detected"


def test_changed_sources_reach_dependent_claims():
    goals = scan_observations(_input(
        changed_sources=("source-x",),
        claim_sources=(("covers:route-1", ("source-x",)),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("source-changed-under-claim:covers:route-1",
         "source-changed-under-claim")]


def test_stale_claims_and_obligations_emit_with_evidence():
    goals = scan_observations(_input(
        stale_claims=(("covers:route-9", ("unit-x",)),),
        obligations=("unit-needs-map",),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("lineage-stale:covers:route-9", "lineage-stale"),
        ("study-map-obligation:unit-needs-map", "study-map-obligation"),
    ]
    assert goals[0].evidence[0] == "claim:covers:route-9"
    assert goals[1].evidence == ("unit:unit-needs-map",)


def test_known_ids_dedup_every_detector():
    known = ("covering-routes-stale:route-1",
             "lineage-stale:covers:route-9",
             "study-map-obligation:unit-needs-map")
    goals = scan_observations(_input(
        changed_nodes=("knowledge-a",),
        route_covers=(("route-1", ("knowledge-a",)),),
        stale_claims=(("covers:route-9", ("unit-x",)),),
        obligations=("unit-needs-map",),
        known_ids=known,
    ))
    assert goals == ()


def test_goals_sort_deterministically():
    first = scan_observations(_input(obligations=("unit-b", "unit-a")))
    second = scan_observations(_input(obligations=("unit-a", "unit-b")))
    assert [goal.goal_id for goal in first] == [
        "study-map-obligation:unit-a", "study-map-obligation:unit-b"]
    assert first == second


def test_scan_on_a_quiet_repo_reports_nothing(mini_repo):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {"goals": []}


def test_scan_refuses_a_negative_window(mini_repo):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--days", "-1"],
        capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2


@pytest.mark.full_repo
def test_scan_runs_on_the_checked_in_state():
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert set(payload) == {"goals"}
    for goal in payload["goals"]:
        assert {"goal_id", "detector", "title", "rationale",
                "evidence", "state"} <= set(goal)
        assert goal["state"] == "detected"


def test_intelligence_scan_reads_a_quiet_repo_directly(mini_repo):
    assert intelligence_scan(mini_repo, days=30) == ()


def test_live_scan_detects_changed_missing_and_unknown_evidence(mini_repo):
    import hashlib

    from learning_os.semantics.lineage import dump_ledger, record_claim
    from learning_os.semantics.scan import collect_observations

    evidence = mini_repo / "work/evidence.md"
    evidence.write_text("reviewed version", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(evidence.read_bytes()).hexdigest()
    records = {}
    for name, hashes in (
        ("target", {"file:work/evidence.md": digest}),
        ("unrelated", {}),
        ("unknown", {"unresolved:source": "unverifiable"}),
    ):
        record = record_claim(
            claim_id=f"scope:proof:{name}", claim_kind="scope-authority",
            statement=f"Synthetic {name} observation.", source_hashes=hashes,
            judged_by="fixture", admitted_by={"request_id": name, "idempotency_key": name},
        )
        records[record.claim_id] = record
    ledger = mini_repo / "operations/transactions/lineage.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(dump_ledger(records), encoding="utf-8")
    unknown = "scope:proof:unknown"
    target = "scope:proof:target"
    assert dict(collect_observations(mini_repo, days=0).stale_claims) == {
        unknown: ("unresolved:source",),
    }
    evidence.write_text("different support", encoding="utf-8")
    expected = {unknown: ("unresolved:source",), target: ("file:work/evidence.md",)}
    assert dict(collect_observations(mini_repo, days=0).stale_claims) == expected
    evidence.unlink()
    assert dict(collect_observations(mini_repo, days=0).stale_claims) == expected


def test_normalize_timestamp_rejects_non_time_values():
    from learning_os.semantics.scan import _normalize_timestamp

    assert _normalize_timestamp("1577934245") == 1577934245.0
    assert _normalize_timestamp(1577934245) == 1577934245.0
    assert _normalize_timestamp(1577934245.5) == 1577934245.5
    assert _normalize_timestamp("  1577934245  ") == 1577934245.0
    assert _normalize_timestamp("") is None
    assert _normalize_timestamp("2020-01-02") is None
    assert _normalize_timestamp("not-a-time") is None
    assert _normalize_timestamp(None) is None
    assert _normalize_timestamp(True) is None
    assert _normalize_timestamp(False) is None
    assert _normalize_timestamp(float("inf")) is None
    assert _normalize_timestamp(float("nan")) is None
    assert _normalize_timestamp("inf") is None
    assert _normalize_timestamp("nan") is None


def test_scan_recency_and_source_join_use_real_git_history(mini_repo, monkeypatch):
    """Phase 1: real commits drive recency and the route/source join.

    Uses production Git history (old baseline commit plus a recent unit
    and source-map commit) through ``collect_observations`` and the real
    CLI — never hand-assembled normalized timestamps. A recent unit
    change reaches its covering route, a recent source-map change
    reaches its route-covers claim through exact route identity, an old
    file stays excluded, an unresolved route stays absent, and an
    unreadable history fails visibly instead of reading as no changes.
    """
    import os

    import yaml
    from test_curriculum_v2 import _add_material_overview, add_curriculum, write_yaml

    from learning_os import githistory
    from learning_os.githistory import GitHistoryError
    from learning_os.semantics.lineage import dump_ledger, emit_route_covers
    from learning_os.semantics.scan import (
        _changed_files,
        collect_observations,
        scan_observations,
    )

    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("GIT_AUTHOR_DATE", raising=False)
    monkeypatch.delenv("GIT_COMMITTER_DATE", raising=False)
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()
    try:
        from learning_os.routes import deterministic_route_id

        add_curriculum(mini_repo)
        _add_material_overview(mini_repo)
        smap_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
        smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
        route = smap["sources"][0]["unit_routes"][0]
        route_id = deterministic_route_id("module-demo", "source-demo-book", route)
        route["id"] = route_id
        write_yaml(smap_path, smap)

        def git(*args, env=None):
            full_env = dict(os.environ)
            if env:
                full_env.update(env)
            return subprocess.run(
                ["git", "-c", "user.name=Test User",
                 "-c", "user.email=test@example.com",
                 "-c", "commit.gpgsign=false", *args],
                cwd=mini_repo, check=True, capture_output=True,
                text=True, env=full_env,
            ).stdout.strip()

        old_env = {"GIT_AUTHOR_DATE": "2020-01-02T03:04:05+00:00",
                   "GIT_COMMITTER_DATE": "2020-01-02T03:04:05+00:00"}
        git("init")
        git("add", "-A")
        git("commit", "-m", "old baseline", env=old_env)

        unit_path = (
            mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
        )
        unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
        unit["title"] = "Expected value (recent edit)"
        write_yaml(unit_path, unit)
        smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
        smap["sources"][0]["unit_routes"][0]["angle"] = "Recent angle edit."
        write_yaml(smap_path, smap)
        git("add",
            "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml",
            "curriculum/modules/module-demo/source-map.yaml")
        git("commit", "-m", "recent unit and source-map edits")
        githistory.last_commit_dates.cache_clear()
        githistory.last_commit_timestamps.cache_clear()

        admission = {"request_id": "scan-fixture", "idempotency_key": "scan-fixture"}
        owned = emit_route_covers(
            route_id=route_id, covers=["knowledge-demo-outcomes"],
            read_revisions={}, judged_by="fixture", admitted_by=admission)
        stray = emit_route_covers(
            route_id="route-unrelated", covers=["knowledge-demo-outcomes"],
            read_revisions={}, judged_by="fixture", admitted_by=admission)
        ledger_path = mini_repo / "operations/transactions/lineage.yaml"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            dump_ledger({owned.claim_id: owned, stray.claim_id: stray}),
            encoding="utf-8")

        unit_rel = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
        smap_rel = "curriculum/modules/module-demo/source-map.yaml"
        old_only = "knowledge/notes/mathematics/note-demo.md"
        recent = _changed_files(mini_repo, days=30)
        assert unit_rel in recent
        assert smap_rel in recent
        assert old_only not in recent
        assert old_only in _changed_files(mini_repo, days=3650)

        obs = collect_observations(mini_repo, days=30)
        assert "knowledge-demo-outcomes" in obs.changed_nodes
        assert route_id in dict(obs.route_covers)
        assert "source-demo-book" in obs.changed_sources
        sources_by_claim = dict(obs.claim_sources)
        assert sources_by_claim.get(f"covers:{route_id}") == ("source-demo-book",)
        assert sources_by_claim.get("covers:route-unrelated") == ()

        goals = scan_observations(obs)
        goal_ids = {goal.goal_id for goal in goals}
        assert f"covering-routes-stale:{route_id}" in goal_ids
        assert f"source-changed-under-claim:covers:{route_id}" in goal_ids
        assert not any("route-unrelated" in goal_id for goal_id in goal_ids)

        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini_repo),
             "intelligence-scan", "--json"],
            capture_output=True, text=True, timeout=180)
        assert proc.returncode == 0, proc.stderr
        payload_ids = {goal["goal_id"] for goal in json.loads(proc.stdout)["goals"]}
        assert f"covering-routes-stale:{route_id}" in payload_ids
        assert f"source-changed-under-claim:covers:{route_id}" in payload_ids

        bad = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini_repo),
             "intelligence-scan", "--json"],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "GIT_DIR": "/dev/null"})
        assert bad.returncode == 2
        assert "Git history" in (bad.stdout + bad.stderr)

        monkeypatch.setenv("GIT_DIR", "/dev/null")
        githistory.last_commit_dates.cache_clear()
        githistory.last_commit_timestamps.cache_clear()
        try:
            with pytest.raises(GitHistoryError):
                collect_observations(mini_repo, days=30)
        finally:
            monkeypatch.delenv("GIT_DIR", raising=False)
            githistory.last_commit_dates.cache_clear()
            githistory.last_commit_timestamps.cache_clear()
    finally:
        githistory.last_commit_dates.cache_clear()
        githistory.last_commit_timestamps.cache_clear()


def test_scan_proposes_dependent_revalidation_after_evidence_moves(
    mini_repo, monkeypatch,
):
    """Phase 2: B assumes A; A's evidence moves; both are proposed.

    B's own reads never move, so its proposal proves transitive
    evaluation rather than direct staleness. Both claims pin evidence
    through the shared resolver exactly once per key.
    """
    import hashlib

    from learning_os.semantics import scan as scan_module
    from learning_os.semantics.lineage import dump_ledger, record_claim
    from learning_os.semantics.scan import collect_observations

    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    evidence = mini_repo / "work/evidence.md"
    stable = mini_repo / "work/stable.md"
    evidence.write_text("v1", encoding="utf-8")
    stable.write_text("constant", encoding="utf-8")

    def digest(path):
        return "sha256:" + hashlib.sha256(
            path.read_bytes()).hexdigest()

    admission = {"request_id": "dep", "idempotency_key": "dep"}
    moving = record_claim(
        claim_id="scope:proof:a", claim_kind="scope-authority",
        statement="A holds.", source_hashes={"file:work/evidence.md": digest(evidence)},
        judged_by="fixture", admitted_by=admission,
    )
    dependent = record_claim(
        claim_id="scope:proof:b", claim_kind="scope-authority",
        statement="B holds given A.",
        source_hashes={"file:work/stable.md": digest(stable)},
        judged_by="fixture", admitted_by=admission,
        assumes=["scope:proof:a"],
    )
    ledger = mini_repo / "operations/transactions/lineage.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(
        dump_ledger({moving.claim_id: moving, dependent.claim_id: dependent}),
        encoding="utf-8")
    assert collect_observations(mini_repo, days=0).stale_claims == ()

    calls: list[str] = []
    real_digest = scan_module.live_evidence_digest

    def counting(root, key, manifest):
        calls.append(key)
        return real_digest(root, key, manifest)

    monkeypatch.setattr(scan_module, "live_evidence_digest", counting)
    evidence.write_text("v2", encoding="utf-8")
    obs = collect_observations(mini_repo, days=0)
    assert sorted(calls) == ["file:work/evidence.md", "file:work/stable.md"]
    assert dict(obs.stale_claims) == {
        "scope:proof:a": ("file:work/evidence.md",),
        "scope:proof:b": ("scope:proof:a",),
    }
    assert {goal.goal_id for goal in scan_observations(obs)} == {
        "lineage-stale:scope:proof:a", "lineage-stale:scope:proof:b"}

    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert {goal["goal_id"] for goal in json.loads(proc.stdout)["goals"]} == {
        "lineage-stale:scope:proof:a", "lineage-stale:scope:proof:b"}
