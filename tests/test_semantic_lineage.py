"""Semantic lineage: every belief carries its basis, and staleness is exact.

A claim read under older revisions is stale; a claim whose reads never
moved is supported no matter what else changed; disagreement needs a
reviewer, never a recompute. The sidecar ledger round-trips through its
schema, and a missing ledger is an empty one — backfill is lazy.
"""

from __future__ import annotations

import dataclasses

import pytest
import yaml

from learning_os.semantics import (
    CONTRACT_VERSION,
    LineageError,
    contest,
    dump_ledger,
    effective_statuses,
    emit_dossier_freshness,
    emit_route_covers,
    emit_scope_authority,
    endorse,
    impacted,
    load_ledger,
    record_claim,
    refresh,
    retraction_impact,
    supersede,
    withdraw,
)
from learning_os.semantics.lineage import (
    LEDGER_RELATIVE,
    from_dict,
    to_dict,
)


def _admission():
    return {"request_id": "request-demo", "idempotency_key": "demo-key"}


def _covers(revisions=None, hashes=None):
    return emit_route_covers(
        route_id="route-abc",
        covers=["knowledge-x", "knowledge-y"],
        read_revisions=revisions if revisions is not None else {"unit-aml-l01": 4},
        judged_by="Muse 2026-09-07",
        admitted_by=_admission(),
        evidence=["material://demo/deck.pdf"],
    )


def test_a_recorded_claim_is_supported_with_its_reads():
    lineage = _covers()
    assert lineage.status == "supported"
    assert lineage.claim_kind == "route-covers"
    assert lineage.claim_id == "covers:route-abc"
    assert lineage.derived_from.contract_version == CONTRACT_VERSION


def test_only_high_value_kinds_earn_lineage():
    with pytest.raises(LineageError):
        record_claim(
            claim_id="x", claim_kind="vibes",
            statement="s", judged_by="j", admitted_by=_admission(),
        )


def test_constructors_need_their_fields():
    with pytest.raises(LineageError):
        record_claim(
            claim_id=" ", claim_kind="route-covers",
            statement="s", judged_by="j", admitted_by=_admission(),
        )
    with pytest.raises(LineageError):
        record_claim(
            claim_id="x", claim_kind="route-covers",
            statement="s", judged_by="", admitted_by=_admission(),
        )


def test_records_need_their_admission():
    with pytest.raises(LineageError):
        record_claim(
            claim_id="x", claim_kind="route-covers",
            statement="s", judged_by="j", admitted_by={},
        )
    with pytest.raises(LineageError):
        record_claim(
            claim_id="x", claim_kind="route-covers",
            statement="s", judged_by="j",
            admitted_by={"request_id": "r", "idempotency_key": " "},
        )


def test_admission_binding_round_trips():
    lineage = _covers()
    assert lineage.admitted_by.request_id == "request-demo"
    assert lineage.admitted_by.idempotency_key == "demo-key"
    rebuilt = from_dict(to_dict(lineage))
    assert rebuilt == lineage


def test_supersede_preserves_the_prior_record():
    first = _covers()
    second = supersede(
        first,
        statement="route-abc covers knowledge-x",
        revisions={"unit-aml-l01": 5},
        judged_by="Aram",
        admitted_by={"request_id": "request-two", "idempotency_key": "two"},
        evidence=["material://demo/errata.pdf"],
    )
    assert second.claim_id == first.claim_id
    assert second.status == "supported"
    assert second.supersedes is not None
    assert second.supersedes["statement"] == first.statement
    assert second.supersedes["admitted_by"]["request_id"] == "request-demo"
    assert to_dict(second)["supersedes"]["claim_id"] == first.claim_id
    rebuilt = from_dict(to_dict(second))
    assert rebuilt == second


def test_a_fixture_mutation_stales_exactly_its_dependents():
    """The Phase 2 validation: one revision moves, only its readers stale."""
    reader = _covers(revisions={"unit-aml-l01": 4})
    other = dataclasses.replace(
        _covers(revisions={"unit-aml-l02": 2}), claim_id="covers:route-def",
    )
    current = {"unit-aml-l01": 5, "unit-aml-l02": 2}
    assert refresh(reader, CONTRACT_VERSION, current).status == "stale"
    assert refresh(other, CONTRACT_VERSION, current).status == "supported"
    assert impacted(
        [reader, other], CONTRACT_VERSION, current,
    ) == ("covers:route-abc",)


def test_unread_artifacts_cannot_stale_a_claim():
    lineage = _covers(revisions={"unit-aml-l01": 4})
    current = {"unit-aml-l01": 4, "unit-aml-l09": 9}
    assert refresh(lineage, CONTRACT_VERSION, current).status == "supported"
    assert impacted([lineage], CONTRACT_VERSION, current) == ()


def test_a_moved_contract_stales_everything():
    lineage = _covers()
    assert refresh(
        lineage, CONTRACT_VERSION + 1, {"unit-aml-l01": 4},
    ).status == "stale"


def test_a_vanished_read_stales_the_claim():
    lineage = _covers(revisions={"unit-aml-l01": 4})
    assert refresh(lineage, CONTRACT_VERSION, {}).status == "stale"


def test_source_hash_moves_stale_dossier_claims():
    lineage = emit_dossier_freshness(
        dossier_key="context://unit-aml-l01/semantic-dossier",
        hashes={"unit": "h1", "menu": "h2"},
        judged_by="Muse 2026-09-07",
        admitted_by=_admission(),
    )
    assert refresh(
        lineage, CONTRACT_VERSION, {}, {"unit": "h1", "menu": "h2"},
    ).status == "supported"
    assert refresh(
        lineage, CONTRACT_VERSION, {}, {"unit": "h1", "menu": "h3"},
    ).status == "stale"


def test_contested_claims_need_a_reviewer_not_a_recompute():
    lineage = _covers()
    disputed = contest(
        lineage, contested_by="Aram", reason="covers the wrong nodes")
    assert disputed.status == "contested"
    assert disputed.contested_by == "Aram"
    # Even a fresh world does not clear disagreement.
    assert refresh(
        disputed, CONTRACT_VERSION, {"unit-aml-l01": 4},
    ).status == "contested"
    assert impacted(
        [disputed], CONTRACT_VERSION, {"unit-aml-l01": 4},
    ) == ("covers:route-abc",)
    endorsed = endorse(disputed, reviewer="Aram")
    assert endorsed.status == "supported"
    assert endorsed.reviewed_by == "Aram"
    assert endorsed.contested_by == ""


def test_contests_and_endorsements_need_their_fields():
    lineage = _covers()
    with pytest.raises(LineageError):
        contest(lineage, contested_by="", reason="r")
    with pytest.raises(LineageError):
        contest(lineage, contested_by="A", reason=" ")
    with pytest.raises(LineageError):
        endorse(lineage, reviewer="")


def test_scope_authority_emission():
    lineage = emit_scope_authority(
        fact_kind="exam_date",
        owner="curriculum/modules/module-hu-aml/module.yaml",
        read_revisions={"module-hu-aml": 7},
        judged_by="Muse 2026-09-07",
        admitted_by=_admission(),
    )
    assert lineage.claim_kind == "scope-authority"
    assert lineage.claim_id == (
        "scope:exam_date:curriculum/modules/module-hu-aml/module.yaml")


def test_the_sidecar_round_trips_through_its_schema(tmp_path):
    lineage = contest(
        _covers(), contested_by="Aram", reason="reread the deck")
    records = {lineage.claim_id: lineage}
    ledger_file = tmp_path / LEDGER_RELATIVE
    ledger_file.parent.mkdir(parents=True)
    ledger_file.write_text(dump_ledger(records), encoding="utf-8")
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "contracts" / "semantic-lineage-ledger.schema.json").write_text(
        _live_schema_text(),
        encoding="utf-8",
    )
    loaded = load_ledger(tmp_path)
    assert loaded == records


def _live_schema_text() -> str:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    return (root / "system" / "contracts"
            / "semantic-lineage-ledger.schema.json").read_text(encoding="utf-8")


def test_a_missing_ledger_is_an_empty_one(tmp_path):
    assert load_ledger(tmp_path) == {}


def test_a_schema_violating_ledger_is_refused(tmp_path):
    (tmp_path / "operations" / "transactions").mkdir(parents=True)
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "contracts" / "semantic-lineage-ledger.schema.json").write_text(
        _live_schema_text(), encoding="utf-8")
    (tmp_path / LEDGER_RELATIVE).write_text(
        yaml.safe_dump({
            "schema_version": 2,
            "type": "semantic-lineage-ledger",
            "records": {
                "x": {"claim_id": "x"},
            },
        }),
        encoding="utf-8",
    )
    with pytest.raises(LineageError):
        load_ledger(tmp_path)


def test_a_renamed_claim_id_is_refused(tmp_path):
    (tmp_path / "operations" / "transactions").mkdir(parents=True)
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "contracts" / "semantic-lineage-ledger.schema.json").write_text(
        _live_schema_text(), encoding="utf-8")
    lineage = _covers()
    record = to_dict(lineage)
    record["claim_id"] = "covers:something-else"
    (tmp_path / LEDGER_RELATIVE).write_text(
        yaml.safe_dump({
            "schema_version": 2,
            "type": "semantic-lineage-ledger",
            "records": {lineage.claim_id: record},
        }),
        encoding="utf-8",
    )
    with pytest.raises(LineageError):
        load_ledger(tmp_path)


def test_from_dict_rejects_garbage():
    with pytest.raises(LineageError):
        from_dict({"claim_id": "x"})


def _write_ledger(tmp_path, records):
    (tmp_path / "operations" / "transactions").mkdir(parents=True)
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "contracts" / "semantic-lineage-ledger.schema.json").write_text(
        _live_schema_text(), encoding="utf-8")
    (tmp_path / LEDGER_RELATIVE).write_text(
        dump_ledger(records), encoding="utf-8")
    return tmp_path


def _judged(cid, *assumes):
    return record_claim(
        claim_id=cid, claim_kind="route-covers", statement=cid,
        judged_by="t", admitted_by=_admission(), assumes=list(assumes),
    )


def test_a_valid_assumption_chain_loads(tmp_path):
    records = {
        record.claim_id: record
        for record in (_judged("A"), _judged("X", "A"), _judged("Y", "X"))
    }
    loaded = load_ledger(_write_ledger(tmp_path, records))
    assert set(loaded) == {"A", "X", "Y"}
    assert loaded["Y"].derived_from.assumes == ("X",)


def test_dangling_assumptions_refuse_on_load(tmp_path):
    records = {"X": _judged("X", "ghost")}
    _write_ledger(tmp_path, records)
    with pytest.raises(LineageError, match="LINEAGE-ASSUMPTION-MISSING"):
        load_ledger(tmp_path)


def test_cyclic_assumptions_refuse_on_load(tmp_path):
    records = {"A": _judged("A", "B"), "B": _judged("B", "A")}
    _write_ledger(tmp_path, records)
    with pytest.raises(LineageError, match="LINEAGE-ASSUMPTION-CYCLE"):
        load_ledger(tmp_path)


def test_self_assumption_refuses_on_load(tmp_path):
    lineage = _judged("S")
    record = to_dict(lineage)
    record["derived_from"]["assumes"] = ["S"]
    (tmp_path / "operations" / "transactions").mkdir(parents=True)
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "contracts" / "semantic-lineage-ledger.schema.json").write_text(
        _live_schema_text(), encoding="utf-8")
    (tmp_path / LEDGER_RELATIVE).write_text(
        yaml.safe_dump({
            "schema_version": 2,
            "type": "semantic-lineage-ledger",
            "records": {"S": record},
        }),
        encoding="utf-8",
    )
    with pytest.raises(LineageError, match="LINEAGE-ASSUMPTION-CYCLE"):
        load_ledger(tmp_path)


def _chain():
    """A → X → Y → Z, plus an unrelated W. Forward-only assumptions."""
    def make(cid, *assumes):
        return record_claim(
            claim_id=cid, claim_kind="route-covers", statement=cid,
            judged_by="t", admitted_by=_admission(), assumes=list(assumes),
        )
    return (
        make("A"),
        make("X", "A"),
        make("Y", "X"),
        make("Z", "Y"),
        make("W"),
    )


def test_retraction_impact_reports_the_blast_radius_without_marking():
    chain = _chain()
    assert retraction_impact(chain, "A") == ("A", "X", "Y", "Z")
    assert retraction_impact(chain, "X") == ("X", "Y", "Z")
    assert retraction_impact(chain, "W") == ("W",)
    # Read-only: nothing was marked.
    assert all(lineage.status == "supported" for lineage in chain)
    with pytest.raises(LineageError):
        retraction_impact(chain, "ghost")


def test_withdraw_cascades_recursively_and_spares_the_unrelated():
    chain = _chain()
    marked = {lineage.claim_id: lineage.status
              for lineage in withdraw(chain, "A")}
    assert marked == {
        "A": "withdrawn", "X": "withdrawn", "Y": "withdrawn",
        "Z": "withdrawn", "W": "supported",
    }
    # Every other field survives the marking.
    after = {lineage.claim_id: lineage for lineage in withdraw(chain, "A")}
    assert after["Z"].statement == "Z"
    assert after["Z"].derived_from.assumes == ("Y",)
    assert after["Z"].judged_by == "t"


def test_withdraw_is_idempotent_and_monotonic():
    chain = _chain()
    once = withdraw(chain, "A")
    assert withdraw(once, "A") == once
    assert withdraw(withdraw(chain, "A"), "X") == once
    assert withdraw(withdraw(chain, "X"), "A") == once


def test_old_records_without_assumptions_cascade_only_to_themselves():
    legacy = to_dict(_chain()[0])
    del legacy["derived_from"]["assumes"]  # pre-Phase-10 sidecar shape
    loaded = from_dict(legacy)
    assert loaded.derived_from.assumes == ()
    assert retraction_impact((loaded,), loaded.claim_id) == (
        loaded.claim_id,)


def test_assumes_round_trip_through_the_sidecar_shape():
    lineage = record_claim(
        claim_id="Y", claim_kind="route-covers", statement="Y",
        judged_by="t", admitted_by=_admission(), assumes=["X"],
    )
    assert from_dict(to_dict(lineage)) == lineage


def test_withdrawn_claims_need_fresh_judgment():
    chain = _chain()
    (lost,) = [lineage for lineage in withdraw(chain, "A")
               if lineage.claim_id == "X"]
    assert lost.status == "withdrawn"
    # No recompute, endorsement, or contest lifts it.
    assert refresh(
        lost, CONTRACT_VERSION, {}, {},
    ).status == "withdrawn"
    with pytest.raises(LineageError):
        endorse(lost, reviewer="Aram")
    with pytest.raises(LineageError):
        contest(lost, contested_by="Aram", reason="r")
    # The impact query still reports it: it needs a human.
    assert "X" in impacted(
        withdraw(chain, "A"), CONTRACT_VERSION, {}, {},
    )


def test_assumptions_must_name_other_claims():
    with pytest.raises(LineageError):
        record_claim(
            claim_id="S", claim_kind="route-covers", statement="S",
            judged_by="t", admitted_by=_admission(), assumes=["S"],
        )
    with pytest.raises(LineageError):
        record_claim(
            claim_id="S", claim_kind="route-covers", statement="S",
            judged_by="t", admitted_by=_admission(), assumes=[" "],
        )
    with pytest.raises(LineageError):
        record_claim(
            claim_id="S", claim_kind="route-covers", statement="S",
            judged_by="t", admitted_by=_admission(), assumes="X",
        )


def _stale_chain():
    """A → B → C with A's revision moved, plus branching B → D and an
    unrelated E. Every claim's own reads are otherwise fresh."""
    def make(cid, rev, *assumes):
        return record_claim(
            claim_id=cid, claim_kind="route-covers", statement=cid,
            revisions={rev: 1}, judged_by="t",
            admitted_by=_admission(), assumes=list(assumes),
        )
    records = {
        lineage.claim_id: lineage for lineage in (
            make("A", "unit-a"),
            make("B", "unit-b", "A"),
            make("C", "unit-c", "B"),
            make("D", "unit-d", "B"),
            make("E", "unit-e"),
        )
    }
    current = {"unit-a": 2, "unit-b": 1, "unit-c": 1, "unit-d": 1,
               "unit-e": 1}
    return records, current


def test_effective_status_propagates_staleness_and_names_blockers():
    records, current = _stale_chain()
    verdicts = effective_statuses(records, CONTRACT_VERSION, current)
    assert verdicts["A"].status == "stale"
    assert verdicts["A"].blocked_by == ()
    assert verdicts["B"].status == "stale"
    assert verdicts["B"].blocked_by == ("A",)
    assert verdicts["C"].status == "stale"
    assert verdicts["C"].blocked_by == ("B",)
    assert verdicts["D"].status == "stale"
    assert verdicts["D"].blocked_by == ("B",)
    assert verdicts["E"].status == "supported"
    assert verdicts["E"].blocked_by == ()


def test_effective_status_preserves_contested_and_withdrawn_roots():
    records, current = _stale_chain()
    disputed = contest(
        records["A"], contested_by="Aram", reason="reread the deck")
    verdicts = effective_statuses(
        {**records, "A": disputed}, CONTRACT_VERSION, current)
    assert verdicts["A"].status == "contested"
    assert verdicts["B"].status == "stale"
    assert verdicts["B"].blocked_by == ("A",)
    # A dependent that is still supported itself goes stale on a
    # withdrawn assumption; an explicit cascade marking is preserved.
    lone = record_claim(
        claim_id="A", claim_kind="route-covers", statement="A",
        revisions={"unit-a": 2}, judged_by="t",
        admitted_by=_admission(),
    )
    (withdrawn_a,) = withdraw((lone,), "A")
    supported_b = record_claim(
        claim_id="B", claim_kind="route-covers", statement="B",
        revisions={"unit-b": 1}, judged_by="t",
        admitted_by=_admission(), assumes=["A"],
    )
    verdicts = effective_statuses(
        {"A": withdrawn_a, "B": supported_b}, CONTRACT_VERSION,
        {"unit-a": 2, "unit-b": 1})
    assert verdicts["A"].status == "withdrawn"
    assert verdicts["B"].status == "stale"
    assert verdicts["B"].blocked_by == ("A",)
    cascaded = {lineage.claim_id: lineage
                for lineage in withdraw(tuple(records.values()), "A")}
    verdicts = effective_statuses(cascaded, CONTRACT_VERSION, current)
    assert verdicts["A"].status == "withdrawn"
    assert verdicts["B"].status == "withdrawn"
    assert verdicts["E"].status == "supported"


def test_effective_status_recovers_when_the_root_is_fresh_again():
    records, _ = _stale_chain()
    fresh = {"unit-a": 1, "unit-b": 1, "unit-c": 1, "unit-d": 1,
             "unit-e": 1}
    verdicts = effective_statuses(records, CONTRACT_VERSION, fresh)
    assert all(v.status == "supported" for v in verdicts.values())
    # A recompute, not a sticky marking: withdrawing still needs judgment.
    assert verdicts["B"].blocked_by == ()


def test_effective_status_names_the_assumption_when_reads_also_moved():
    records, _ = _stale_chain()
    current = {"unit-a": 2, "unit-b": 2, "unit-c": 1, "unit-d": 1,
               "unit-e": 1}
    verdicts = effective_statuses(records, CONTRACT_VERSION, current)
    assert verdicts["B"].status == "stale"
    assert verdicts["B"].blocked_by == ("A",)


def test_effective_status_refuses_missing_and_cyclic_assumptions():
    records, current = _stale_chain()
    stray = record_claim(
        claim_id="S", claim_kind="route-covers", statement="S",
        judged_by="t", admitted_by=_admission(), assumes=["ghost"],
    )
    with pytest.raises(LineageError, match="LINEAGE-ASSUMPTION-MISSING"):
        effective_statuses(
            {**records, "S": stray}, CONTRACT_VERSION, current)
    loop = {
        lineage.claim_id: lineage
        for lineage in (_judged("X", "Y"), _judged("Y", "X"))
    }
    with pytest.raises(LineageError, match="LINEAGE-ASSUMPTION-CYCLE"):
        effective_statuses(loop, CONTRACT_VERSION, {})


def test_effective_status_is_deterministic_and_leaves_inputs_untouched():
    records, current = _stale_chain()
    before = {cid: to_dict(lineage) for cid, lineage in records.items()}
    first = effective_statuses(records, CONTRACT_VERSION, current)
    shuffled = dict(reversed(list(records.items())))
    second = effective_statuses(shuffled, CONTRACT_VERSION, current)
    assert first == second
    assert [v.claim_id for v in first.values()] == sorted(first)
    assert {cid: to_dict(lineage) for cid, lineage in records.items()} == before
    assert {cid: to_dict(lineage) for cid, lineage in shuffled.items()} == before
