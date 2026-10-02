"""Governed lineage re-stamp: narrow old coarse reads without re-judging (#94).

A route-covers claim judged under the old read shape pins its module
revision plus every co-imported unit, so any unrelated edit marks it
stale. The re-stamp narrows one claim's reads to the per-route shape new
judgments use — the route row plus each covered node, by content digest —
keeping evidence, judge and admission untouched and attributing the
narrowing itself. It refuses anything but a supported old-shape claim.
"""

from __future__ import annotations

import hashlib
import subprocess

import pytest
import yaml
from conftest import build_mini_repo
from repo_builders import rich_fixture, write_yaml

from learning_os import githistory
from learning_os.semantics import (
    LineageError,
    emit_route_covers,
    emit_scope_authority,
    parse_covers_statement,
    restamp_claim,
    withdraw,
)
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
    SCHEMA_RELATIVE,
    dump_ledger,
    from_dict,
    to_dict,
)
from learning_os.semantics.restamp import (
    _attribute_bundled_patch as attribute_bundled_patch,
)
from learning_os.semantics.restamp import (
    analyze,
    claims_list_sha256,
)


def _admission():
    return {"request_id": "request-demo", "idempotency_key": "demo-key"}


def _old_covers(**overrides):
    kwargs = {
        "route_id": "route-abc",
        "covers": ["knowledge-x", "knowledge-y"],
        "read_revisions": {"module-demo": 7, "unit-demo-l01": 4},
        "judged_by": "operator/operator-approval",
        "admitted_by": _admission(),
        "evidence": ["route-locator:00:00-04:16"],
        "source_hashes": {"file:work/evidence.md": "sha256:abc"},
    }
    kwargs.update(overrides)
    return emit_route_covers(**kwargs)


def _narrowed():
    return {
        "route-content:route-abc": "sha256:route",
        "node-content:knowledge-x": "sha256:x",
        "node-content:knowledge-y": "sha256:y",
    }


def test_parse_covers_statement_names_route_and_nodes():
    assert parse_covers_statement(
        "covers:route-abc", "route-abc covers knowledge-x, knowledge-y") == (
        "route-abc", ("knowledge-x", "knowledge-y"))
    assert parse_covers_statement(
        "covers:route-abc", "route-abc covers nothing") == ("route-abc", ())


def test_parse_covers_statement_refuses_a_foreign_statement():
    with pytest.raises(LineageError):
        parse_covers_statement("covers:route-abc", "route-other covers knowledge-x")
    with pytest.raises(LineageError):
        parse_covers_statement("covers:route-abc", "route-abc covers knowledge-x,")
    with pytest.raises(LineageError):
        parse_covers_statement("scope:proof:a", "proof is owned by a")


def test_restamp_narrows_reads_and_keeps_the_judgment():
    prior = _old_covers()
    stamped = restamp_claim(
        prior, source_hashes=_narrowed(),
        restamped_by="operator/operator-approval", restamped_on="2026-10-02")
    assert dict(stamped.derived_from.revisions) == {}
    assert dict(stamped.derived_from.source_hashes) == {
        "file:work/evidence.md": "sha256:abc", **_narrowed()}
    assert list(stamped.derived_from.evidence) == list(prior.derived_from.evidence)
    assert stamped.judged_by == prior.judged_by
    assert stamped.admitted_by == prior.admitted_by
    assert stamped.derived_from.contract_version == prior.derived_from.contract_version
    assert stamped.status == "supported"
    assert stamped.reviewed_by == ""
    assert stamped.restamped_by == "operator/operator-approval"
    assert stamped.restamped_on == "2026-10-02"
    assert stamped.supersedes == to_dict(prior)


def test_restamp_round_trips_through_the_sidecar_shape():
    stamped = restamp_claim(
        _old_covers(), source_hashes=_narrowed(),
        restamped_by="operator/operator-approval", restamped_on="2026-10-02")
    assert from_dict(to_dict(stamped)) == stamped


def test_restamp_refuses_anything_but_a_supported_old_shape_claim():
    narrowed = _narrowed()
    with pytest.raises(LineageError):
        restamp_claim(
            emit_scope_authority(
                fact_kind="proof", owner="a",
                read_revisions={"module-demo": 1},
                judged_by="j", admitted_by=_admission()),
            source_hashes=narrowed,
            restamped_by="b", restamped_on="2026-10-02")
    [gone] = withdraw([_old_covers()], "covers:route-abc")
    with pytest.raises(LineageError):
        restamp_claim(
            gone, source_hashes=narrowed,
            restamped_by="b", restamped_on="2026-10-02")
    stamped = restamp_claim(
        _old_covers(), source_hashes=narrowed,
        restamped_by="b", restamped_on="2026-10-02")
    with pytest.raises(LineageError):
        restamp_claim(
            stamped, source_hashes=narrowed,
            restamped_by="b", restamped_on="2026-10-03")


def test_restamp_needs_complete_narrowed_reads_and_attribution():
    prior = _old_covers()
    partial = dict(_narrowed())
    del partial["node-content:knowledge-y"]
    with pytest.raises(LineageError):
        restamp_claim(
            prior, source_hashes=partial,
            restamped_by="b", restamped_on="2026-10-02")
    with pytest.raises(LineageError):
        restamp_claim(
            prior, source_hashes=_narrowed(),
            restamped_by=" ", restamped_on="2026-10-02")
    with pytest.raises(LineageError):
        restamp_claim(
            prior, source_hashes=_narrowed(),
            restamped_by="b", restamped_on="")


def test_claim_list_binding_is_order_free_but_exact():
    one = claims_list_sha256(["covers:b", "covers:a"])
    assert one == claims_list_sha256(["covers:a", "covers:b"])
    assert one == "sha256:" + hashlib.sha256(
        b"covers:a\ncovers:b\n").hexdigest()
    with pytest.raises(LineageError):
        claims_list_sha256(["covers:a", "covers:a"])
    with pytest.raises(LineageError):
        claims_list_sha256(["covers:a", ""])


def test_bundled_patch_attribution_needs_one_named_route():
    routes = {"unit-m2-analysis-ch06": [
        "route-an-ch06-henningdierks", "route-an-ch06-wrathofmath"]}
    assert attribute_bundled_patch(
        request_id="request-kleine-beweise-20260912-ch06-dierks",
        units={"unit-m2-analysis-ch06"},
        routes_by_unit=routes) == "route-an-ch06-henningdierks"
    # A trailing counter names no route.
    assert attribute_bundled_patch(
        request_id="op-20260909-harv-l08-001",
        units={"unit-m2-sad-l08"},
        routes_by_unit={"unit-m2-sad-l08": ["route-x-001"]}) is None
    # A hint matching two routes names none.
    assert attribute_bundled_patch(
        request_id="request-demo-20260912-ch06-route",
        units={"unit-m2-analysis-ch06"},
        routes_by_unit=routes) is None
    # A unit hint outside the bumped unit names none.
    assert attribute_bundled_patch(
        request_id="request-kleine-beweise-20260912-ch07-dierks",
        units={"unit-m2-analysis-ch06"},
        routes_by_unit=routes) is None
    # An unscoped patch names none.
    assert attribute_bundled_patch(
        request_id="request-kleine-beweise-20260912-ch06-dierks",
        units=set(), routes_by_unit=routes) is None


@pytest.fixture(autouse=True)
def isolated_history(monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    for name in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
        monkeypatch.setenv(name, "2020-01-02T03:04:05+00:00")
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()
    yield
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()


def _git(root, *args):
    return subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _judged_repo(tmp_path, *, evidence=(), receipt_id="transaction-20200102-000000-001"):
    """A synthetic clone with one judged old-shape covers claim committed."""
    root = build_mini_repo(tmp_path)
    route_id, _route = rich_fixture(root)
    smap_path = root / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    smap["sources"][0]["unit_routes"][0]["id"] = route_id
    write_yaml(smap_path, smap)
    claim = emit_route_covers(
        route_id=route_id,
        covers=["knowledge-demo-expectation", "knowledge-demo-outcomes"],
        read_revisions={"module-demo": 1, "unit-demo-l01": 1},
        judged_by="operator/operator-approval",
        admitted_by={"request_id": "request-demo",
                     "idempotency_key": "demo-key"},
        evidence=list(evidence),
    )
    ledger_path = root / LEDGER_RELATIVE
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        dump_ledger({claim.claim_id: claim}), encoding="utf-8")
    schema_src = root / SCHEMA_RELATIVE
    assert schema_src.is_file()
    smap_rel = "curriculum/modules/module-demo/source-map.yaml"
    unit_rel = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    write_yaml(root / "operations" / "transactions" / f"{receipt_id}.yaml", {
        "schema_version": 2, "id": receipt_id, "type": "transaction-receipt",
        "status": "committed", "capability": "module.plan.import",
        "request": {"request_id": "request-demo",
                    "idempotency_key": "demo-key"},
        "writes": [
            {"path": smap_rel,
             "sha256_after": hashlib.sha256(
                 (root / smap_rel).read_bytes()).hexdigest()},
            {"path": unit_rel,
             "sha256_after": hashlib.sha256(
                 (root / unit_rel).read_bytes()).hexdigest()},
        ],
    })
    _git(root, "init")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "judge one covers claim")
    return root, claim.claim_id, route_id


def test_analyze_marks_an_unchanged_claim_eligible(tmp_path):
    root, claim_id, route_id = _judged_repo(tmp_path)
    out = analyze(root)
    assert out["totals"] == {
        "eligible": 1, "needs-rejudgment": 0, "needs-review": 0}
    row = out["claims"][claim_id]
    assert row["verdict"] == "eligible"
    assert row["basis"] == "exact"
    assert row["reasons"] == []
    assert sorted(row["new_reads"]) == [
        "node-content:knowledge-demo-expectation",
        "node-content:knowledge-demo-outcomes",
        f"route-content:{route_id}",
    ]


def test_analyze_refuses_a_claim_whose_route_row_changed(tmp_path):
    root, claim_id, _route_id = _judged_repo(tmp_path)
    smap_path = root / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    smap["sources"][0]["unit_routes"][0]["angle"] = "A rewritten angle."
    write_yaml(smap_path, smap)
    _git(root, "commit", "-am", "descriptive route edit")
    out = analyze(root)
    row = out["claims"][claim_id]
    assert row["verdict"] == "needs-rejudgment"
    assert row["reasons"] == ["route-changed"]
    assert row["new_reads"] is None


def test_analyze_holds_a_claim_whose_evidence_moved(tmp_path):
    root, claim_id, _route_id = _judged_repo(tmp_path)
    ledger_path = root / LEDGER_RELATIVE
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    record = ledger["records"][claim_id]
    evidence_path = root / "work/evidence.md"
    evidence_path.write_text("judged bytes", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(b"judged bytes").hexdigest()
    record["derived_from"]["source_hashes"] = {"file:work/evidence.md": digest}
    record["derived_from"]["evidence"] = ["repo-file:work/evidence.md"]
    ledger_path.write_text(
        yaml.safe_dump(ledger, sort_keys=False, allow_unicode=True),
        encoding="utf-8")
    _git(root, "commit", "-am", "cite file evidence")
    evidence_path.write_text("republished bytes", encoding="utf-8")
    out = analyze(root)
    row = out["claims"][claim_id]
    assert row["verdict"] == "needs-review"
    assert row["reasons"] == ["evidence-unverifiable:file:work/evidence.md"]
