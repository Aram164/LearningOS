"""Proof-carrying change: admission is deterministic, refusal is exact.

The plan's highest-risk validation in executable form: a good envelope
admits with exactly one decision; a stale read, missing evidence, or
out-of-scope write is refused without mutation; two conflicting writes
cannot both succeed; one approval covers exactly its scope. The gateway
still applies — this suite pins the preflight that stands in front of it.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import (
    ChangeError,
    admit,
    build_envelope,
    verify_postconditions,
)

SCOPES = ("curriculum/modules/*/units/*/study-map.yaml",)
REVISIONS = {"study-map-aml-l01": 6}
SNAPSHOT = "sha256:abc"


def _envelope(**overrides):
    fields = {
        "intent": "ground the L01 map on the current menu",
        "scope": ["study-map-aml-l01"],
        "read_revisions": dict(REVISIONS),
        "claims": ["covers:route-1"],
        "claim_statuses": {"covers:route-1": "supported"},
        "evidence": {"material://demo/deck.pdf": "h1"},
        "writes": [{
            "capability": "route.patch",
            "target_path": "curriculum/modules/module-hu-aml/units/unit-aml-l01/study-map.yaml",
            "summary": "re-point one stage row",
            "scopes": list(SCOPES),
        }],
        "expected_snapshot": SNAPSHOT,
        "approved_by": "Aram",
        "approved_capabilities": ["route.patch"],
        "postconditions": [{
            "predicate": "StudyMapGrounded",
            "inputs": {
                "template_version": 1,
                "resource_pairs": [["source-a", "ch 1"]],
                "menu_pairs": [["source-a", "ch 1"]],
            },
            "op": "is_true",
        }],
        "validation_plan": ["make check", "warning-baseline"],
    }
    fields.update(overrides)
    return build_envelope(**fields)


def _world(revisions=None, snapshot=None):
    return {
        "current_contract_version": 2,
        "current_revisions": dict(REVISIONS if revisions is None else revisions),
        "current_snapshot": SNAPSHOT if snapshot is None else snapshot,
    }


def test_a_good_envelope_admits_with_one_receipt_worth_of_reasons():
    decision = admit(_envelope(), **_world())
    assert decision.verdict == "admit"
    assert len(decision.reasons) == 1
    results = verify_postconditions(_envelope())
    assert [(result.predicate, result.passed) for result in results] == [
        ("StudyMapGrounded", True)]


def test_a_stale_read_never_commits():
    """Highest risk, first half: the world moved under the envelope."""
    decision = admit(
        _envelope(), **_world(revisions={"study-map-aml-l01": 7}))
    assert decision.verdict == "conflict"
    assert any("stale" in reason.lower() for reason in decision.reasons)


def test_a_moved_snapshot_is_a_conflict_not_an_overwrite():
    decision = admit(_envelope(), **_world(snapshot="sha256:def"))
    assert decision.verdict == "conflict"


def test_missing_evidence_replans():
    decision = admit(
        _envelope(evidence={"material://demo/deck.pdf": None}), **_world())
    assert decision.verdict == "replan"


def test_an_out_of_scope_write_is_denied():
    envelope = _envelope(writes=[{
        "capability": "route.patch",
        "target_path": "knowledge/notes/note-x.md",
        "summary": "out of scope",
        "scopes": list(SCOPES),
    }])
    decision = admit(envelope, **_world())
    assert decision.verdict == "deny"


def test_one_approval_covers_one_scope():
    """An approval for route.patch never admits a unit.map.import write."""
    envelope = _envelope(
        approved_capabilities=["route.patch"],
        writes=[{
            "capability": "unit.map.import",
            "target_path": "curriculum/modules/module-hu-aml/units/unit-aml-l01/study-map.yaml",
            "summary": "wrong capability",
            "scopes": list(SCOPES),
        }],
    )
    assert admit(envelope, **_world()).verdict == "deny"


def test_anything_but_aram_is_not_approval():
    envelope = _envelope(approved_by="Muse")
    decision = admit(envelope, **_world())
    assert decision.verdict == "deny"


def test_conflicting_writes_cannot_both_succeed():
    """Highest risk, second half: sequential admission, one snapshot each.

    The first envelope applies (the gateway moves the snapshot); the
    second, read under the old snapshot, conflicts instead of overwriting.
    """
    first, second = _envelope(), _envelope()
    assert admit(first, **_world()).verdict == "admit"
    applied_snapshot = "sha256:applied"
    assert admit(second, **_world(snapshot=applied_snapshot)).verdict == "conflict"


def test_unsupported_lineage_conflicts():
    envelope = _envelope(claim_statuses={"covers:route-1": "stale"})
    assert admit(envelope, **_world()).verdict == "conflict"


def test_uncheckable_postconditions_replan():
    envelope = _envelope(postconditions=[{
        "predicate": "Nope", "inputs": {}, "op": "is_true",
    }])
    decision = admit(envelope, **_world())
    assert decision.verdict == "replan"
    envelope = _envelope(postconditions=[{
        "predicate": "RepoClean", "inputs": {}, "op": "eventually",
    }])
    assert admit(envelope, **_world()).verdict == "replan"


def test_failing_postconditions_report_per_check():
    envelope = _envelope(postconditions=[
        {
            "predicate": "StudyMapGrounded",
            "inputs": {
                "template_version": 1,
                "resource_pairs": [["source-a", "ch 1"]],
                "menu_pairs": [["source-a", "ch 1"]],
            },
            "op": "is_true",
        },
        {
            "predicate": "RepoClean",
            "inputs": {"error_count": 3, "new_or_grown_warnings": 0},
            "op": "is_true",
        },
    ])
    assert admit(envelope, **_world()).verdict == "admit"
    assert [(result.predicate, result.passed)
            for result in verify_postconditions(envelope)] == [
        ("StudyMapGrounded", True), ("RepoClean", False)]


def test_malformed_envelopes_refuse_at_construction():
    with pytest.raises(ChangeError):
        _envelope(intent="  ")
    with pytest.raises(ChangeError):
        _envelope(writes=[])
    with pytest.raises(ChangeError):
        _envelope(validation_plan=[])
    with pytest.raises(ChangeError):
        _envelope(expected_snapshot="")
    with pytest.raises(ChangeError):
        _envelope(postconditions=[{"predicate": "RepoClean"}])
