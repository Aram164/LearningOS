"""Intelligence scan: observe the live world, interpret, propose.

Pure assembly tests run on synthetic observations (fast); CLI tests run
against the synthetic mini repo (no history, no ledger, no curriculum
units — the scan observes nothing and says so) plus one full-repo run
proving the command works on the checked-in state.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.semantics import ScanInput, intelligence_scan, scan_observations

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def _input(**overrides):
    fields = {
        "route_covers": (),
        "route_digest_pins": (),
        "live_route_digests": (),
        "route_revision_pins": (),
        "current_revisions": (),
        "node_digest_pins": (),
        "live_node_digests": (),
        "claim_statuses": (),
        "stale_claims": (),
        "obligations": (),
        "known_ids": (),
    }
    fields.update(overrides)
    return ScanInput(**fields)


def test_empty_observations_propose_nothing():
    assert scan_observations(_input()) == ()


def test_moved_node_digests_reach_covering_routes():
    goals = scan_observations(_input(
        route_covers=(("route-1", ("knowledge-a", "knowledge-b")),),
        node_digest_pins=(("route-1", (("knowledge-a", "sha256:old"),
                                       ("knowledge-b", "sha256:kept"))),),
        live_node_digests=(("knowledge-a", "sha256:new"),
                            ("knowledge-b", "sha256:kept")),
        claim_statuses=(("covers:route-1", "supported"),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("covering-routes-stale:route-1", "covering-routes-stale")]
    assert goals[0].state == "detected"


def test_covering_routes_evidence_names_the_moved_unit():
    goals = scan_observations(_input(
        route_covers=(("route-1", ("knowledge-a",)),),
        node_digest_pins=(("route-1", (("knowledge-a", "sha256:old"),)),),
        live_node_digests=(("knowledge-a", "sha256:new"),),
        claim_statuses=(("covers:route-1", "supported"),),
        node_units=(("knowledge-a", "unit-x"),),
    ))
    (goal,) = goals
    assert goal.evidence == (
        "route:route-1", "node:knowledge-a", "unit:unit-x")


def test_covering_routes_emit_without_a_unit_map():
    goals = scan_observations(_input(
        route_covers=(("route-1", ("knowledge-a",)),),
        node_digest_pins=(("route-1", (("knowledge-a", "sha256:old"),)),),
        live_node_digests=(("knowledge-a", "sha256:new"),),
        claim_statuses=(("covers:route-1", "supported"),),
    ))
    (goal,) = goals
    assert goal.evidence == ("route:route-1", "node:knowledge-a")


def test_moved_route_rows_reach_their_claim():
    goals = scan_observations(_input(
        route_digest_pins=(("route-1", "sha256:old"),),
        live_route_digests=(("route-1", "sha256:new"),),
        claim_statuses=(("covers:route-1", "supported"),),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("source-changed-under-claim:covers:route-1",
         "source-changed-under-claim")]


def test_moved_revisions_reach_old_shape_claims():
    goals = scan_observations(_input(
        route_revision_pins=(("route-1", (("module-x", 2),)),),
        current_revisions=(("module-x", 3),),
        claim_statuses=(("covers:route-1", "supported"),),
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


def test_claim_reviews_reach_the_review_detector():
    goals = scan_observations(_input(
        claim_reviews=(("covers:route-1", "", "supported"),
                       ("covers:route-2", "aram", "supported"),
                       ("covers:route-3", "aram", "contested")),
    ))
    assert [(goal.goal_id, goal.detector) for goal in goals] == [
        ("claims-needing-review:covers:route-1", "claims-needing-review"),
        ("claims-needing-review:covers:route-3", "claims-needing-review"),
    ]


def test_known_ids_dedup_every_detector():
    known = ("covering-routes-stale:route-1",
             "source-changed-under-claim:covers:route-2",
             "lineage-stale:covers:route-9",
             "study-map-obligation:unit-needs-map",
             "claims-needing-review:covers:route-1")
    goals = scan_observations(_input(
        route_covers=(("route-1", ("knowledge-a",)),),
        node_digest_pins=(("route-1", (("knowledge-a", "sha256:old"),)),),
        live_node_digests=(("knowledge-a", "sha256:new"),),
        route_digest_pins=(("route-2", "sha256:old"),),
        live_route_digests=(("route-2", "sha256:new"),),
        claim_statuses=(("covers:route-1", "supported"),
                        ("covers:route-2", "supported")),
        stale_claims=(("covers:route-9", ("unit-x",)),),
        obligations=("unit-needs-map",),
        claim_reviews=(("covers:route-1", "", "supported"),),
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


def test_scan_compares_stored_digests_not_file_membership(mini_repo, monkeypatch):
    """Row edits flag exactly their own claim; sibling rows stay silent.

    A quiet world — every row matching its pins — emits no
    covering-routes or changed-source goals at all. A route-row edit
    then flags exactly that claim, a node edit exactly the routes
    covering that node, and a revision bump exactly the old-shape claim
    pinning it. No Git history is read at any point: staleness is a
    digest comparison, so even a poisoned GIT_DIR changes nothing.
    """
    from learning_os.semantics.lineage import (
        dump_ledger,
        emit_route_covers,
        load_ledger,
    )
    from learning_os.semantics.scan import collect_observations, scan_observations

    route_a, route_b = _two_unit_scoped_world(mini_repo)
    admission = {"request_id": "scan-fixture", "idempotency_key": "scan-fixture"}
    legacy = emit_route_covers(
        route_id="route-legacy", covers=["knowledge-demo-alpha"],
        read_revisions={"module-demo": 3},
        judged_by="fixture", admitted_by=admission)
    ledger_path = mini_repo / "operations/transactions/lineage.yaml"
    records = load_ledger(mini_repo)
    records[legacy.claim_id] = legacy
    ledger_path.write_text(dump_ledger(records), encoding="utf-8")

    def row_goals():
        goals = scan_observations(collect_observations(mini_repo, days=30))
        return (
            sorted(goal.goal_id for goal in goals
                   if goal.detector == "source-changed-under-claim"),
            sorted(goal.goal_id for goal in goals
                   if goal.detector == "covering-routes-stale"),
        )

    obs = collect_observations(mini_repo, days=30)
    assert set(dict(obs.route_digest_pins)) == {route_a, route_b}
    assert dict(obs.route_revision_pins) == {
        "route-legacy": (("module-demo", 3),)}
    assert dict(obs.claim_units) == {
        f"covers:{route_a}": "unit-demo-l01",
        f"covers:{route_b}": "unit-demo-l02"}
    assert row_goals() == ([], [])

    monkeypatch.setenv("GIT_DIR", "/dev/null")
    assert row_goals() == ([], [])
    monkeypatch.delenv("GIT_DIR", raising=False)

    _rewrite_route(mini_repo, route_b, angle="Beta angle, revised.")
    assert row_goals() == (
        [f"source-changed-under-claim:covers:{route_b}"], [])
    _rewrite_route(mini_repo, route_b, angle="Beta angle.")

    _rewrite_node(mini_repo, "unit-demo-l01", "knowledge-demo-alpha",
                  title="Alpha, reframed")
    assert row_goals() == ([], [f"covering-routes-stale:{route_a}"])
    _rewrite_node(mini_repo, "unit-demo-l01", "knowledge-demo-alpha",
                  title="Alpha")

    _rewrite_revision(mini_repo, "module-demo", 4)
    assert row_goals() == (
        ["source-changed-under-claim:covers:route-legacy"], [])

    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    payload_ids = {goal["goal_id"] for goal in json.loads(proc.stdout)["goals"]}
    assert "source-changed-under-claim:covers:route-legacy" in payload_ids
    assert not any(
        goal_id.startswith("covering-routes-stale:")
        for goal_id in payload_ids
    )


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

    def counting(root, key, manifest, **kwargs):
        calls.append(key)
        return real_digest(root, key, manifest, **kwargs)

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


def test_missing_evidence_resolves_once_for_all_claims_sharing_it(
    mini_repo, monkeypatch,
):
    """Examination finding 3: three claims pinning one missing key attempt
    the resolver once per collection — and all three still go stale, so
    the collection stays fail-closed."""
    from learning_os.semantics import scan as scan_module
    from learning_os.semantics.lineage import dump_ledger, record_claim
    from learning_os.semantics.scan import collect_observations

    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    admission = {"request_id": "missing", "idempotency_key": "missing"}
    made = {}
    for n in range(3):
        claim = record_claim(
            claim_id=f"scope:proof:ghost-{n}", claim_kind="scope-authority",
            statement="Ghost holds.",
            source_hashes={"file:work/gone.md": "sha256:" + "0" * 64},
            judged_by="fixture", admitted_by=admission)
        made[claim.claim_id] = claim
    ledger = mini_repo / "operations/transactions/lineage.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(dump_ledger(made), encoding="utf-8")

    calls: list[str] = []
    real_digest = scan_module.live_evidence_digest

    def counting(root, key, manifest, **kwargs):
        calls.append(key)
        return real_digest(root, key, manifest, **kwargs)

    monkeypatch.setattr(scan_module, "live_evidence_digest", counting)
    obs = collect_observations(mini_repo, days=0)
    assert calls == ["file:work/gone.md"]
    assert sorted(claim for claim, _keys in obs.stale_claims) == sorted(made)


def test_brief_json_on_a_quiet_repo_is_empty_but_totalled(mini_repo):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini_repo),
         "intelligence-scan", "--brief", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {
        "contract": "intelligence-scan-brief", "groups": [],
        "omitted_goals": 0, "omitted_groups": 0,
        "total_goals": 0, "total_groups": 0,
        "full_result": "intelligence-scan --json",
    }


@pytest.mark.full_repo
def test_brief_json_caps_the_checked_in_queue_at_five():
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root),
         "intelligence-scan", "--brief", "--json"],
        capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "intelligence-scan-brief"
    groups = payload["groups"]
    assert len(groups) <= 5
    assert payload["total_groups"] == len(groups) + payload["omitted_groups"]
    assert payload["total_goals"] == (
        sum(group["member_count"] for group in groups) + payload["omitted_goals"])
    assert payload["full_result"] == "intelligence-scan --json"
    for rank, group in enumerate(groups, start=1):
        assert group["rank"] == rank
        assert {"cluster_id", "detector", "title", "tier", "tier_label",
               "nearest_sitting", "days_until", "member_count",
               "sample_goal_ids", "omitted_members"} <= set(group)
        assert len(group["sample_goal_ids"]) <= 6
        assert (len(group["sample_goal_ids"]) + group["omitted_members"]
                == group["member_count"])
    # Ranks follow the full queue's order.
    full = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "intelligence-scan"],
        capture_output=True, text=True, timeout=300)
    assert full.returncode == 0, full.stderr
    titles = [line.split("] ", 1)[1] for line in full.stdout.splitlines()
              if re.match(r"^\d+\. \[", line)]
    assert [group["title"] for group in groups] == titles[:len(groups)]


@pytest.mark.full_repo
def test_brief_human_page_shows_five_groups_then_the_omitted_tail():
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(root),
         "intelligence-scan", "--brief"],
        capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr
    rows = [line for line in proc.stdout.splitlines()
            if re.match(r"^\d+\. \[", line)]
    assert len(rows) <= 5
    total = int(re.search(r"in (\d+) group", proc.stdout.splitlines()[0]).group(1))
    if total > 5:
        assert "omitted -- rerun without --brief for the full queue" in proc.stdout


def _two_unit_scoped_world(mini_repo):
    """Two units judged in one batch, one route claim each, new-style reads.

    Returns (route_a, route_b): the judged route ids. Each claim pins its
    own route row plus its own covered node and no artifact revision —
    exactly what a batch import now records.
    """
    import yaml
    from repo_builders import add_curriculum, write_yaml

    from learning_os.revisions import dump_revisions
    from learning_os.route_identity import route_with_identity
    from learning_os.semantics.lineage import (
        dump_ledger,
        emit_route_covers,
        node_content_digest,
        route_content_digest,
    )

    add_curriculum(mini_repo)
    module_dir = mini_repo / "curriculum/modules/module-demo"
    smap_path = module_dir / "source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    smap["sources"][0]["unit_routes"] = [
        route_with_identity("module-demo", "source-demo-book", {
            "unit_id": unit_id, "title": title, "format": "paper",
            "angle": angle, "covers": [node], "depth": "derivation",
            "scope": "current", "locator": locator})
        for unit_id, title, angle, node, locator in (
            ("unit-demo-l01", "Alpha route", "Alpha angle.",
             "knowledge-demo-alpha", "paper-a.pdf"),
            ("unit-demo-l02", "Beta route", "Beta angle.",
             "knowledge-demo-beta", "paper-b.pdf"),
        )
    ]
    write_yaml(smap_path, smap)
    live_rows = {row["id"]: row
                 for row in smap["sources"][0]["unit_routes"]}
    route_a, route_b = (row["id"] for row in smap["sources"][0]["unit_routes"])
    node_rows = {
        "knowledge-demo-alpha": {"id": "knowledge-demo-alpha",
                                 "title": "Alpha", "summary": "First."},
        "knowledge-demo-beta": {"id": "knowledge-demo-beta",
                                "title": "Beta", "summary": "Second."},
    }
    unit1_path = module_dir / "units/unit-demo-l01/unit.yaml"
    unit1 = yaml.safe_load(unit1_path.read_text(encoding="utf-8"))
    unit1["knowledge_map"] = {
        "summary": "Alpha nodes.", "nodes": [node_rows["knowledge-demo-alpha"]]}
    write_yaml(unit1_path, unit1)
    write_yaml(module_dir / "units/unit-demo-l02/unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Second lecture", "order": 2,
        "scope": "The lecture as taught.", "status": "active",
        "knowledge_map": {
            "summary": "Beta nodes.",
            "nodes": [node_rows["knowledge-demo-beta"]]},
    })
    transactions = mini_repo / "operations/transactions"
    transactions.mkdir(parents=True, exist_ok=True)
    revisions = {"module-demo": 3, "unit-demo-l01": 2, "unit-demo-l02": 5}
    (transactions / "revisions.yaml").write_text(
        dump_revisions(revisions), encoding="utf-8")
    admission = {"request_id": "scan-fixture", "idempotency_key": "scan-fixture"}
    claims = {}
    for rid, node in ((route_a, "knowledge-demo-alpha"),
                      (route_b, "knowledge-demo-beta")):
        claim = emit_route_covers(
            route_id=rid, covers=[node], read_revisions={},
            judged_by="fixture", admitted_by=admission,
            source_hashes={
                f"route-content:{rid}": route_content_digest(
                    module_id="module-demo", source_id="source-demo-book",
                    route=live_rows[rid]),
                f"node-content:{node}": node_content_digest(node_rows[node]),
            })
        claims[claim.claim_id] = claim
    (transactions / "lineage.yaml").write_text(
        dump_ledger(claims), encoding="utf-8")
    return route_a, route_b


def _rewrite_revision(mini_repo, artifact, revision):
    from learning_os.revisions import dump_revisions, load_revisions

    current = load_revisions(mini_repo)
    current[artifact] = revision
    path = mini_repo / "operations/transactions/revisions.yaml"
    path.write_text(dump_revisions(current), encoding="utf-8")


def _rewrite_route(mini_repo, route_id, **fields):
    import yaml
    from repo_builders import write_yaml

    smap_path = (mini_repo / "curriculum/modules/module-demo/source-map.yaml")
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    for row in smap["sources"][0]["unit_routes"]:
        if row["id"] == route_id:
            row.update(fields)
    write_yaml(smap_path, smap)


def _rewrite_node(mini_repo, unit_id, node_id, **fields):
    import yaml
    from repo_builders import write_yaml

    unit_path = (mini_repo / "curriculum/modules/module-demo/units"
                 / unit_id / "unit.yaml")
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    for row in unit["knowledge_map"]["nodes"]:
        if row["id"] == node_id:
            row.update(fields)
    write_yaml(unit_path, unit)


def test_scoped_batch_claims_start_supported(mini_repo):
    from learning_os.semantics.scan import collect_observations

    route_a, route_b = _two_unit_scoped_world(mini_repo)
    assert dict(collect_observations(mini_repo, days=0).stale_claims) == {}


def test_withdrawn_claims_stay_out_of_row_detectors(mini_repo):
    """A withdrawn claim needs a fresh judgment: even when its own
    route row and covered node both move, no re-examination or
    revalidation goal fires for it."""
    from learning_os.semantics.lineage import dump_ledger, load_ledger, withdraw
    from learning_os.semantics.scan import collect_observations, scan_observations

    route_a, _route_b = _two_unit_scoped_world(mini_repo)
    ledger_path = mini_repo / "operations/transactions/lineage.yaml"
    records = load_ledger(mini_repo)
    ledger_path.write_text(
        dump_ledger({lineage.claim_id: lineage
                     for lineage in withdraw(
                         list(records.values()), f"covers:{route_a}")}),
        encoding="utf-8")
    _rewrite_route(mini_repo, route_a, angle="Alpha angle, revised.")
    _rewrite_node(mini_repo, "unit-demo-l01", "knowledge-demo-alpha",
                  title="Alpha, reframed")
    goals = scan_observations(collect_observations(mini_repo, days=0))
    assert [goal.goal_id for goal in goals
            if goal.detector in ("source-changed-under-claim",
                                 "covering-routes-stale")] == []


def test_route_patch_in_sibling_unit_stales_only_that_routes_claim(mini_repo):
    """A route.patch bumps module + owning unit: with scoped reads only the
    patched route's claim stales, never the batch sibling's."""
    from learning_os.semantics.scan import collect_observations

    route_a, route_b = _two_unit_scoped_world(mini_repo)
    _rewrite_route(mini_repo, route_b, angle="Beta angle, revised.")
    _rewrite_revision(mini_repo, "module-demo", 4)
    _rewrite_revision(mini_repo, "unit-demo-l02", 6)
    stale = dict(collect_observations(mini_repo, days=0).stale_claims)
    assert set(stale) == {f"covers:{route_b}"}
    assert stale[f"covers:{route_b}"] == (f"route-content:{route_b}",)


def test_progress_write_in_own_unit_leaves_route_claim_supported(mini_repo):
    """stage.progress.update bumps the unit revision: learner state is not a
    coverage read, so the unit's route claims stay supported."""
    from learning_os.semantics.scan import collect_observations

    _two_unit_scoped_world(mini_repo)
    _rewrite_revision(mini_repo, "unit-demo-l01", 3)
    _rewrite_revision(mini_repo, "study-map:unit-demo-l01", 1)
    assert dict(collect_observations(mini_repo, days=0).stale_claims) == {}


def test_own_route_row_edit_stales_exactly_that_claim(mini_repo):
    from learning_os.semantics.scan import collect_observations

    route_a, _route_b = _two_unit_scoped_world(mini_repo)
    _rewrite_route(mini_repo, route_a, angle="Alpha angle, revised.")
    stale = dict(collect_observations(mini_repo, days=0).stale_claims)
    assert set(stale) == {f"covers:{route_a}"}


def test_covered_node_edit_stales_exactly_the_covering_claim(mini_repo):
    from learning_os.semantics.scan import collect_observations

    route_a, _route_b = _two_unit_scoped_world(mini_repo)
    _rewrite_node(mini_repo, "unit-demo-l01", "knowledge-demo-alpha",
                  title="Alpha, reframed")
    stale = dict(collect_observations(mini_repo, days=0).stale_claims)
    assert set(stale) == {f"covers:{route_a}"}
    assert stale[f"covers:{route_a}"] == ("node-content:knowledge-demo-alpha",)
