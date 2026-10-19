"""Exact drift occurrences, bounded reads and immutable audit lifecycles."""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from repo_builders import run_los, write_yaml

from learning_os.derive.semantics.claim_audits import (
    ALGORITHM,
    AuditAuthorization,
    AuditError,
    AuditRecord,
    AuditResult,
    ClaimBasis,
    audit_id,
    audit_records,
    authorization_from_mapping,
    memberships,
    pool_digest,
    sample_pool,
)
from learning_os.derive.semantics.claim_status import (
    interpret_claims,
    judgment_basis,
    observe_claims,
    observe_claims_with_audits,
    read_audits,
)
from learning_os.derive.semantics.goals import (
    cluster_goals,
    detect_claim_findings,
    detect_claims_audit,
    detector_metrics,
)
from learning_os.derive.semantics.lineage import (
    dump_ledger,
    record_claim,
    to_dict,
)
from learning_os.derive.semantics.scan import intelligence_scan, observe_goal_ledger


def claim(cid="covers:route-one", **kwargs):
    return record_claim(claim_id=cid, claim_kind="route-covers", statement="This source teaches the node.",
                        judged_by="judging-session", admitted_by={"request_id": "req-one", "idempotency_key": "key-one"}, **kwargs)


def test_occurrence_changes_for_different_current_drift_but_identical_drift_reuses_it():
    row = claim(revisions={"unit-a": 1})
    records = {row.claim_id: row}
    a = interpret_claims(records, {"unit-a": 2}, {})[row.claim_id]
    assert a.status == "stale" and len(a.occurrence) == 64
    assert interpret_claims(records, {"unit-a": 1}, {})[row.claim_id].status == "supported"
    b = interpret_claims(records, {"unit-a": 3}, {})[row.claim_id]
    assert b.goal_id != a.goal_id
    assert interpret_claims(records, {"unit-a": 2, "unrelated": 999}, {})[row.claim_id] == a
    assert detect_claim_findings(claims=[a], known_ids=[a.goal_id]) == ()
    assert len(detect_claim_findings(claims=[b], known_ids=[a.goal_id])) == 1


def test_evidence_values_and_blocking_assumptions_bind_occurrences():
    a = claim(source_hashes={"file:work/a": "sha256:old"})
    b = claim("covers:route-two", assumes=[a.claim_id])
    records = {a.claim_id: a, b.claim_id: b}
    x = interpret_claims(records, {}, {"file:work/a": "sha256:new"})
    y = interpret_claims(records, {}, {"file:work/a": "sha256:another"})
    assert x[b.claim_id].status == "stale"
    assert x[b.claim_id].causes == ("assumption-blocked", "coarse-pin")
    assert x[b.claim_id].goal_id != y[b.claim_id].goal_id


def test_restamp_read_shape_does_not_change_judgment_basis():
    row = claim(revisions={"unit-a": 1})
    stamped = replace(row, derived_from=replace(row.derived_from, revisions=(),
                       source_hashes=(("route-content:route-one", "sha256:pin"),)),
                       restamped_by="restamper", restamped_on="2026-10-18")
    assert judgment_basis(stamped) == judgment_basis(row)
    assert judgment_basis(replace(row, statement="A different judgment.")) != judgment_basis(row)


@pytest.mark.parametrize(("key", "cause"), [("route-content:route-one", "route-edited"),
    ("node-content:knowledge-one", "node-changed"), ("manifest:source/a.pdf", "evidence-changed")])
def test_one_staleness_finding_per_claim_and_root_cause(key, cause):
    row = claim(source_hashes={"route-content:route-one": "same", key: "old"})
    status = interpret_claims({row.claim_id: row}, {}, {"route-content:route-one": "same", key: "new"},
                              units={row.claim_id: "unit-a"})[row.claim_id]
    assert cause in status.causes
    goals = detect_claim_findings(claims=[status])
    assert len(goals) == 1 and goals[0].detector == "lineage-stale"
    assert goals[0].goal_id == status.goal_id


def test_coarse_claims_share_one_group():
    rows = [claim("covers:route-" + str(i), revisions={"unit-" + str(i): 1}) for i in range(3)]
    states = interpret_claims({r.claim_id: r for r in rows}, {}, {})
    clusters = cluster_goals(detect_claim_findings(claims=list(states.values())))
    assert len(clusters) == 1 and len(clusters[0].member_ids) == 3


def test_unreviewed_supported_claims_do_not_generate_per_claim_review():
    row = claim()
    state = interpret_claims({row.claim_id: row}, {}, {})[row.claim_id]
    assert detect_claim_findings(claims=[state]) == ()
    for disputed in (replace(state, status="contested"), replace(state, audit="defective")):
        assert detect_claim_findings(claims=[disputed])[0].detector == "claims-needing-review"


def pool_world(root, n=32):
    records = {f"covers:route-{i:03}": claim(f"covers:route-{i:03}") for i in range(n)}
    target = root / "operations/transactions/lineage.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dump_ledger(records))
    pool = tuple(sorted(ClaimBasis(cid, judgment_basis(row)) for cid, row in records.items()))
    seed = "ab" * 32
    auth = {"pool": [p.payload() for p in pool], "pool_sha256": pool_digest(pool),
            "seed": seed, "algorithm": ALGORITHM, "sample": [p.payload() for p in sample_pool(pool, seed)] if len(pool) >= 30 else []}
    file = root.parent / "authorization.yaml"
    write_yaml(file, auth)
    return records, pool, auth, file


def decide(root, gid, action, file=None, note=None):
    args = ["goal", gid, action]
    if file is not None:
        args += ["--audit-file", str(file)]
    if note is not None:
        args += ["--note", note]
    preview = run_los(root, *args, "--check")
    assert preview.returncode == 0, preview.stderr + preview.stdout
    review = json.loads(preview.stdout)["reviewed_sha256"]
    result = run_los(root, *args, "--reviewed-sha256", review)
    assert result.returncode == 0, result.stderr + result.stdout
    return args, review


def test_pool_threshold_and_scan_never_draws(mini_repo, monkeypatch):
    import learning_os.derive.semantics.claim_audits as audits
    records, pool, auth, _ = pool_world(mini_repo, 29)
    states = observe_claims(mini_repo)
    assert detect_claims_audit(claims=list(states.values()), audits={}) == ()
    pool_world(mini_repo, 30)
    monkeypatch.setattr(audits, "sample_pool", lambda *_: pytest.fail("scan must not draw"))
    goals = intelligence_scan(mini_repo)
    assert len(goals) == 1 and goals[0].detector == "claims-audit"


def test_authorize_reject_defer_close_preserves_frozen_audit_and_exact_replay(mini_repo):
    records, pool, auth, file = pool_world(mini_repo)
    gid = audit_id(pool)
    args, review = decide(mini_repo, gid, "--authorize", file)
    ledger = mini_repo / "operations/goal-ledger.yaml"
    frozen = yaml.safe_load(ledger.read_text())["audits"][gid]["authorization"]
    replay_before = ledger.read_bytes()
    replay = run_los(mini_repo, *args, "--reviewed-sha256", review)
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["replayed"] is True and ledger.read_bytes() == replay_before
    changed_intent = run_los(mini_repo, *args, "--reviewed-sha256", review, "--note", "A different decision intent.")
    assert changed_intent.returncode == 3 and ledger.read_bytes() == replay_before
    changed_owner = run_los(mini_repo, *args, "--reviewed-sha256", review, "--session-id", "a-different-session")
    assert changed_owner.returncode == 3 and ledger.read_bytes() == replay_before

    assert any(g.goal_id == gid for g in intelligence_scan(mini_repo))  # authorized is intent, not suppression
    decide(mini_repo, gid, "--reject", note="Review later after the exam.")
    decide(mini_repo, gid, "--defer")
    assert yaml.safe_load(ledger.read_text())["audits"][gid]["authorization"] == frozen
    changed = {**auth, "seed": "cd" * 32, "sample": [p.payload() for p in sample_pool(pool, "cd" * 32)]}
    write_yaml(file, changed)
    refused = run_los(mini_repo, "goal", gid, "--authorize", "--audit-file", str(file), "--check")
    assert refused.returncode == 2 and "redraw" in refused.stderr
    report = mini_repo.parent / "report.md"
    report.write_text("Independent reviewer inspected the frozen sample; no overclaims found.")
    close = {"sample": auth["sample"], "defects": [], "reviewer": "independent-review-session",
             "report_path": str(report), "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
    write_yaml(file, close)
    args, review = decide(mini_repo, gid, "--close", file)
    data = yaml.safe_load(ledger.read_text())
    assert data["audits"][gid]["authorization"] == frozen
    certified, defective = memberships(audit_records(data["audits"]))
    assert certified == frozenset((p.claim_id, p.basis) for p in pool) and not defective
    assert intelligence_scan(mini_repo) == ()
    before = ledger.read_bytes()
    replay = run_los(mini_repo, *args, "--reviewed-sha256", review)
    assert replay.returncode == 0 and json.loads(replay.stdout)["replayed"] is True
    assert ledger.read_bytes() == before


def test_failed_audit_defects_match_exact_basis_and_require_repair_before_new_pool(mini_repo):
    records, pool, auth, file = pool_world(mini_repo)
    gid = audit_id(pool)
    decide(mini_repo, gid, "--authorize", file)
    report = mini_repo.parent / "report.md"
    report.write_text("One sampled route overclaims a node not taught at the locator.")
    close = {"sample": auth["sample"], "defects": [auth["sample"][0]], "reviewer": "review-session",
             "report_path": str(report), "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
    write_yaml(file, close)
    decide(mini_repo, gid, "--close", file)
    goals = intelligence_scan(mini_repo)
    assert len(goals) == 1 and goals[0].detector == "claims-needing-review"
    defective = auth["sample"][0]["claim_id"]
    old = records[defective]
    records[defective] = replace(old, statement="Reviewed repair teaches a narrower node.", supersedes=to_dict(old))
    (mini_repo / "operations/transactions/lineage.yaml").write_text(dump_ledger(records))
    assert observe_claims_with_audits(mini_repo)[defective].audit == "unaudited"
    goals = intelligence_scan(mini_repo)
    assert len(goals) == 1 and goals[0].detector == "claims-audit" and goals[0].goal_id != gid
    # Historical closure remains bound to the original pool after repair.
    decide(mini_repo, gid, "--close", file)
    close["defects"] = []
    write_yaml(file, close)
    refused = run_los(mini_repo, "goal", gid, "--close", "--audit-file", str(file), "--check")
    assert refused.returncode == 2 and "immutable result" in refused.stderr


def test_incomplete_pool_and_changed_report_refuse_before_writes(mini_repo):
    _, pool, auth, file = pool_world(mini_repo)
    shortened = pool[:-1]
    auth["pool"] = [p.payload() for p in shortened]
    auth["pool_sha256"] = pool_digest(shortened)
    auth["sample"] = [p.payload() for p in sample_pool(shortened, auth["seed"])]
    write_yaml(file, auth)
    result = run_los(mini_repo, "goal", audit_id(shortened), "--authorize", "--audit-file", str(file), "--check")
    assert result.returncode == 2 and "complete current" in result.stderr
    assert not (mini_repo / "operations/goal-ledger.yaml").exists()


def test_audit_parser_refuses_mutated_sample_duplicate_pairs_and_short_digests(mini_repo):
    _, _, auth, _ = pool_world(mini_repo)
    for field, value in (("seed", "ab"), ("sample", list(reversed(auth["sample"]))),
                         ("pool", [auth["pool"][0], *auth["pool"]])):
        bad = copy.deepcopy(auth)
        bad[field] = value
        with pytest.raises(AuditError):
            authorization_from_mapping(bad)


def test_wilson_rule_counts_each_occurrence_once_excludes_deferred_and_old():
    decisions = {f"lineage-stale:covers:route-{i}@{'a'*64}": {
        "state": "rejected" if i < 3 else "authorized", "decided_at": "2026-10-18"} for i in range(10)}
    metric = detector_metrics(decisions)["lineage-stale"]
    assert metric["decisions"] == 10 and metric["quiet"] is True
    key = next(iter(decisions))
    decisions[key] = {"state": "closed", "decided_at": "2026-10-18"}
    assert detector_metrics(decisions)["lineage-stale"]["decisions"] == 10
    for i in range(30):
        decisions[f"lineage-stale:old-{i}"] = {"state": "rejected", "decided_at": "2026-10-17"}
        decisions[f"lineage-stale:deferred-{i}"] = {"state": "deferred", "decided_at": "2026-10-18"}
    assert detector_metrics(decisions)["lineage-stale"]["decisions"] == 10


def test_focused_status_resolves_only_selected_evidence_and_its_assumptions(mini_repo, monkeypatch):
    import learning_os.derive.semantics.claim_status as owner
    a = claim("covers:route-a", source_hashes={"file:work/a.md": "sha256:old"})
    b = claim("covers:route-b", source_hashes={"file:work/b.md": "sha256:old"})
    records = {r.claim_id: r for r in [a, b]}
    (mini_repo / "work/a.md").write_text("a")
    (mini_repo / "work/b.md").write_text("b")
    calls = []
    original = owner.live_evidence_digest

    def observed(root, key, manifest, **kwargs):
        calls.append(key)
        return original(root, key, manifest, **kwargs)

    monkeypatch.setattr(owner, "live_evidence_digest", observed)
    result = observe_claims(mini_repo, records=records, route_ids=["route-a"])
    assert set(result) == {a.claim_id} and calls == ["file:work/a.md"]
    calls.clear()
    records[a.claim_id] = replace(a, derived_from=replace(a.derived_from, assumes=(b.claim_id,)))
    result = observe_claims(mini_repo, records=records, route_ids=["route-a"])
    assert set(result) == {a.claim_id} and calls == ["file:work/a.md", "file:work/b.md"]


def test_malformed_audit_state_cannot_silently_hide_disputes(mini_repo):
    path = mini_repo / "operations/goal-ledger.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("decisions: {}\naudits: [broken")
    basic = observe_claims(mini_repo, route_ids=["route-a"])
    assert basic["covers:route-a"].audit == "unavailable"
    assert observe_claims_with_audits(mini_repo, route_ids=["route-a"]) == basic
    with pytest.raises(AuditError, match="preserved audit state"):
        read_audits(mini_repo)
    with pytest.raises(AuditError, match="preserved audit state"):
        intelligence_scan(mini_repo)


def test_reject_requires_note_and_authorized_goal_stays_detectable(mini_repo):
    from repo_builders import seed_live_goal_ids
    gid, = seed_live_goal_ids(mini_repo, "authorize-me")
    refused = run_los(mini_repo, "goal", gid, "--reject", "--check")
    assert refused.returncode == 2 and "--note" in refused.stderr
    decide(mini_repo, gid, "--authorize")
    assert gid in {g.goal_id for g in intelligence_scan(mini_repo)}


def test_preflight_reports_real_claim_impact_without_blocking_descriptive_edits(mini_repo):
    from test_intelligence_scan import _two_unit_scoped_world

    from learning_os.app._plan_gate import module_plan_check_report

    first, _ = _two_unit_scoped_world(mini_repo)
    path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(path.read_text())
    for source in source_map["sources"]:
        for row in source.get("unit_routes", []):
            if row.get("id") == first:
                row["angle"] = "A revised, lecture-specific explanation."
    report = module_plan_check_report(mini_repo, "module-demo", {"source_map": source_map},
        {path: yaml.safe_dump(source_map)}, [], "sha256:" + "a"*64, {"unit-demo-l01"})
    entry = next(row for row in report["claims"] if row["claim_id"] == "covers:" + first)
    assert entry["before"] == "supported" and entry["after"] == "will-be-stale"
    assert first in entry["warning"] and "unit-plan-revise unit-demo-l01" in entry["next"]
    assert observe_claims(mini_repo)["covers:" + first].status == "supported"
    # The read-only scan fixture above deliberately omits full curriculum
    # metadata. Route-patch's complete preflight is covered with the valid
    # admitted material fixture in test_verbatim_anchor_admission.


def test_quieting_hides_only_attention_and_preserves_full_json(mini_repo):
    pool_world(mini_repo)
    write_yaml(mini_repo / "operations/goal-ledger.yaml", {
        "schema_version": 1, "type": "goal-ledger", "decisions": {
            "claims-audit:" + f"{i:064x}": {"state": "rejected", "note": "Not useful.", "decided_at": "2026-10-18"}
            for i in range(10)}})
    full = run_los(mini_repo, "intelligence-scan", "--json")
    assert full.returncode == 0, full.stderr
    goals = json.loads(full.stdout)["goals"]
    assert len(goals) == 1 and goals[0]["quiet"] is True
    brief = run_los(mini_repo, "intelligence-scan", "--brief", "--json")
    assert brief.returncode == 0, brief.stderr
    payload = json.loads(brief.stdout)
    assert payload["groups"] == [] and payload["detectors"]["claims-audit"]["quiet"] is True
    from learning_os.app.handlers.resume import _top_cluster
    assert _top_cluster(mini_repo) is None


@pytest.mark.parametrize("entry", ["scan", "ranked", "brief-handler", "full-handler"])
def test_entire_scan_uses_one_immutable_ledger_observation(mini_repo, monkeypatch, entry):
    from learning_os.app.handlers.reads import intelligence_scan as handle_scan
    from learning_os.app.ranking import ranked_scan

    pool_world(mini_repo, 30)
    path = mini_repo / "operations/goal-ledger.yaml"
    initial = {"schema_version": 1, "type": "goal-ledger", "decisions": {}}
    write_yaml(path, initial)
    changed = {**initial, "decisions": {
        f"claims-audit:{i:064x}": {"state": "rejected", "decided_at": "2026-10-18", "note": "Reviewed"}
        for i in range(10)}}
    reads = []
    original = Path.read_text

    def interposed_read(self, *args, **kwargs):
        value = original(self, *args, **kwargs)
        if self == path:
            reads.append(value)
            if len(reads) == 1:
                write_yaml(path, changed)
        return value

    monkeypatch.setattr(Path, "read_text", interposed_read)
    if entry == "scan":
        goals = intelligence_scan(mini_repo)
    elif entry == "ranked":
        goals, _, hidden = ranked_scan(mini_repo)
        assert hidden == 0
    else:
        result = handle_scan(SimpleNamespace(root=mini_repo), {"days": 30, "brief": entry == "brief-handler"})
        assert result.human_view["hidden_count"] == 0
        if entry == "brief-handler":
            assert result.payload["detectors"]["claims-audit"]["decisions"] == 0
            assert result.payload["total_groups"] == 1
        else:
            assert result.payload["goals"][0]["quiet"] is False
        goals = None
    assert len(reads) == 1
    if goals is not None:
        assert len(goals) == 1 and goals[0].quiet is False
    later = intelligence_scan(mini_repo)
    assert len(reads) == 2 and later[0].quiet is True


def test_observed_goal_metrics_cannot_be_mutated_or_refreshed_implicitly(mini_repo):
    path = mini_repo / "operations/goal-ledger.yaml"
    write_yaml(path, {"decisions": {}})
    observed = observe_goal_ledger(mini_repo)
    with pytest.raises(TypeError):
        observed.metrics["claims-audit"]["quiet"] = True
    with pytest.raises(TypeError):
        observed.metrics["unexpected"] = {}
    write_yaml(path, {"decisions": {"study-map-obligation:unit-x": {"state": "rejected"}}})
    assert observed.known_ids == ()
    assert observe_goal_ledger(mini_repo).known_ids == ("study-map-obligation:unit-x",)


@pytest.mark.parametrize("content", ["decisions: {}\naudits: []\n", "decisions: {}\naudits: [broken", b"\xff"])
@pytest.mark.parametrize("shape", ["route", "brief", "stage"])
def test_unavailable_optional_audit_does_not_disable_plan_inspection(mini_repo, content, shape):
    from repo_builders import _compact_setup

    _compact_setup(mini_repo)
    path = mini_repo / "operations/goal-ledger.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = content.encode() if isinstance(content, str) else content
    path.write_bytes(raw)
    suffix = {"route": ["--route-id", "route-demo-book"], "brief": ["--brief"], "stage": ["--stage-id", "stage-demo"]}[shape]
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", *suffix, "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    if shape == "route":
        assert data["claim"]["audit"] == "unavailable"
    elif shape == "brief":
        assert data["claims"]["audit_counts"]["unavailable"] > 0
    else:
        assert "claim" not in data and "claims" not in data
    assert path.read_bytes() == raw


def test_fresh_dispute_rejudgment_revalidates_audit_evidence_per_check(mini_repo):
    from test_verbatim_anchor_admission import _patch_world

    from learning_os.app.claim_admission import prepare_claim_admission
    from learning_os.store.loader import load_repo

    evidence = _patch_world(mini_repo)
    record = claim("covers:route-test")
    records = {record.claim_id: record, **{f"covers:other-{i}": claim(f"covers:other-{i}") for i in range(29)}}
    lineage = mini_repo / "operations/transactions/lineage.yaml"
    lineage.parent.mkdir(parents=True, exist_ok=True)
    lineage.write_text(dump_ledger(records))
    pool = tuple(sorted(ClaimBasis(cid, judgment_basis(row)) for cid, row in records.items()))
    seed = "ab" * 32
    authorization = AuditAuthorization(pool, seed, sample_pool(pool, seed))
    defect = ClaimBasis(record.claim_id, judgment_basis(record))
    result = AuditResult(authorization.sample, (defect,), "independent-reviewer", "report.md", "a" * 64)
    path = mini_repo / "operations/goal-ledger.yaml"
    write_yaml(path, {"decisions": {}, "audits": {audit_id(pool): AuditRecord(authorization, result).payload()}})
    observed = observe_goal_ledger(mini_repo)
    assert intelligence_scan(mini_repo, goal_ledger=observed)[0].detector == "claims-needing-review"
    package = {"claim_evidence": [evidence]}
    repo = load_repo(mini_repo)
    assert prepare_claim_admission(mini_repo, repo, "module-demo", package).problems == []
    before = lineage.read_bytes()
    path.write_text("decisions: {}\naudits: [broken")
    refused = prepare_claim_admission(mini_repo, repo, "module-demo", package)
    assert any("preserved audit state" in problem for problem in refused.problems)
    assert lineage.read_bytes() == before
    write_yaml(path, {"decisions": {}, "audits": {}})
    refused = prepare_claim_admission(mini_repo, repo, "module-demo", package)
    assert any("not stale or disputed" in problem for problem in refused.problems)
    assert intelligence_scan(mini_repo, goal_ledger=observed)[0].detector == "claims-needing-review"
    assert intelligence_scan(mini_repo)[0].detector == "claims-audit"


def test_basic_claim_evidence_never_reads_optional_audit_storage(mini_repo, monkeypatch):
    import learning_os.derive.semantics.claim_status as owner

    pool_world(mini_repo, 30)
    def unexpected(*args, **kwargs):
        pytest.fail("basic claim evidence must not access audit storage")
    monkeypatch.setattr(owner, "read_audits", unexpected)
    states = observe_claims(mini_repo)
    assert len(states) == 30
    assert all(row.status == "supported" and row.audit == "unavailable" for row in states.values())
