"""Proof-carrying change: admission is deterministic, refusal is exact.

The plan's highest-risk validation in executable form, hardened: the
envelope carries claims, never verdicts — authorization, lineage, and
evidence come from a trusted context the agent never touches. A good
envelope admits with exactly one decision; a stale read, unresolvable
evidence, or out-of-scope write is refused without mutation; two
conflicting writes cannot both succeed; one approval covers exactly its
scope; widened scopes fail against the capability contract. The gateway
still applies — this suite pins the preflight that stands in front of it.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import (
    ChangeError,
    admit,
    build_envelope,
    build_trusted_context,
    verify_postconditions,
)

SCOPES = ("curriculum/modules/*/units/*/study-map.yaml",)
CONTRACT_SCOPES = {
    "route.patch": list(SCOPES),
    "unit.map.import": ["curriculum/modules/*/units/*/study-map.yaml"],
}
REVISIONS = {"study-map-aml-l01": 6}
SNAPSHOT = "sha256:abc"
WRITE = {
    "capability": "route.patch",
    "target_path": "curriculum/modules/module-hu-aml/units/unit-aml-l01/study-map.yaml",
    "summary": "re-point one stage row",
    "scopes": list(SCOPES),
}


def _envelope(**overrides):
    fields = {
        "intent": "ground the L01 map on the current menu",
        "scope": ["study-map-aml-l01"],
        "read_revisions": dict(REVISIONS),
        "claims": ["covers:route-1"],
        "evidence": ["material://demo/deck.pdf"],
        "writes": [dict(WRITE)],
        "expected_snapshot": SNAPSHOT,
        "postconditions": [{
            "predicate": "StudyMapGrounded",
            "selector": "study-map:unit-aml-l01",
            "op": "is_true",
        }],
        "validation_plan": ["make check", "warning-baseline"],
    }
    fields.update(overrides)
    return build_envelope(**fields)


GROUNDED_MAP = {
    "template_version": 1,
    "resource_pairs": [["source-a", "ch 1"]],
    "menu_pairs": [["source-a", "ch 1"]],
}
CLEAN_REPO = {"error_count": 0, "new_or_grown_warnings": 0}


def _live(**overrides):
    world = {
        "study-map:unit-aml-l01": dict(GROUNDED_MAP),
        "validation": dict(CLEAN_REPO),
    }
    world.update(overrides)
    return world


def _context(**overrides):
    fields = {
        "approved_by": "Aram",
        "approved_capabilities": ["route.patch"],
        "capability_scopes": {key: list(value)
                              for key, value in CONTRACT_SCOPES.items()},
        "claim_statuses": {"covers:route-1": "supported"},
        "evidence_digests": {"material://demo/deck.pdf": "h1"},
        "current_contract_version": 2,
        "current_revisions": dict(REVISIONS),
        "current_snapshot": SNAPSHOT,
    }
    fields.update(overrides)
    return build_trusted_context(**fields)


def test_a_good_envelope_admits_with_one_receipt_worth_of_reasons():
    decision = admit(_envelope(), _context())
    assert decision.verdict == "admit"
    assert len(decision.reasons) == 1
    results = verify_postconditions(_envelope(), _live())
    assert [(result.predicate, result.passed) for result in results] == [
        ("StudyMapGrounded", True)]


def test_verdicts_are_structurally_unstatable_in_envelopes():
    """Smuggling trust has no field to ride in on."""
    with pytest.raises(TypeError):
        _envelope(approved_by="Aram")
    with pytest.raises(TypeError):
        _envelope(claim_statuses={"covers:route-1": "supported"})


def test_a_stale_read_never_commits():
    """Highest risk, first half: the world moved under the envelope."""
    context = _context(current_revisions={"study-map-aml-l01": 7})
    decision = admit(_envelope(), context)
    assert decision.verdict == "conflict"
    assert any("stale" in reason.lower() for reason in decision.reasons)


def test_a_moved_snapshot_is_a_conflict_not_an_overwrite():
    context = _context(current_snapshot="sha256:def")
    decision = admit(_envelope(), context)
    assert decision.verdict == "conflict"


def test_unresolvable_evidence_replans():
    context = _context(evidence_digests={"material://demo/deck.pdf": None})
    assert admit(_envelope(), context).verdict == "replan"
    context = _context(evidence_digests={})
    assert admit(_envelope(), context).verdict == "replan"


def test_an_out_of_scope_write_is_denied():
    envelope = _envelope(writes=[dict(
        WRITE,
        target_path="knowledge/notes/note-x.md",
    )])
    decision = admit(envelope, _context())
    assert decision.verdict == "deny"


def test_scopes_wider_than_the_contract_are_denied():
    """The envelope cannot widen its own scopes past the contract."""
    envelope = _envelope(writes=[dict(
        WRITE,
        target_path="knowledge/notes/note-x.md",
        scopes=["knowledge/**"],
    )])
    decision = admit(envelope, _context())
    assert decision.verdict == "deny"
    assert any("capability contract" in reason for reason in decision.reasons)


def test_a_concrete_path_inside_the_contract_admits():
    """Narrower is fine: a concrete path the contract covers."""
    envelope = _envelope(writes=[dict(
        WRITE,
        scopes=["curriculum/modules/module-hu-aml/units/unit-aml-l01/study-map.yaml"],
    )])
    assert admit(envelope, _context()).verdict == "admit"


def test_one_approval_covers_one_scope():
    """An approval for route.patch never admits a unit.map.import write."""
    write = dict(
        WRITE,
        capability="unit.map.import",
    )
    envelope = _envelope(writes=[write])
    assert admit(envelope, _context()).verdict == "deny"


def test_anything_but_aram_is_not_approval():
    """The envelope is well-formed; the session did not approve."""
    context = _context(approved_by="Muse")
    decision = admit(_envelope(), context)
    assert decision.verdict == "deny"


def test_conflicting_writes_cannot_both_succeed():
    """Highest risk, second half: sequential admission, one snapshot each.

    The first envelope applies (the gateway moves the snapshot); the
    second, read under the old snapshot, conflicts instead of overwriting.
    """
    first, second = _envelope(), _envelope()
    assert admit(first, _context()).verdict == "admit"
    applied = _context(current_snapshot="sha256:applied")
    assert admit(second, applied).verdict == "conflict"


def test_ledger_lineage_decides_not_envelope_claims():
    """A claim the live ledger stopped supporting conflicts."""
    context = _context(claim_statuses={"covers:route-1": "stale"})
    assert admit(_envelope(), context).verdict == "conflict"
    context = _context(claim_statuses={})
    assert admit(_envelope(), context).verdict == "conflict"


def test_uncheckable_postconditions_replan():
    envelope = _envelope(postconditions=[{
        "predicate": "Nope", "selector": "validation", "op": "is_true",
    }])
    decision = admit(envelope, _context())
    assert decision.verdict == "replan"
    envelope = _envelope(postconditions=[{
        "predicate": "RepoClean", "selector": "validation", "op": "eventually",
    }])
    assert admit(envelope, _context()).verdict == "replan"


def test_postconditions_read_the_live_world_not_the_promise():
    """The reviewer's scenario: a promised RepoClean fails on a dirty repo.

    The envelope fixes nothing — the same envelope passes against a
    clean post-apply world and fails against a dirty one. Predetermined
    inputs cannot fake it because there are no predetermined inputs.
    """
    envelope = _envelope(postconditions=[
        {"predicate": "StudyMapGrounded",
         "selector": "study-map:unit-aml-l01", "op": "is_true"},
        {"predicate": "RepoClean",
         "selector": "validation", "op": "is_true"},
    ])
    assert admit(envelope, _context()).verdict == "admit"
    assert [(result.predicate, result.passed)
            for result in verify_postconditions(envelope, _live())] == [
        ("StudyMapGrounded", True), ("RepoClean", True)]
    dirty = _live(validation={"error_count": 3, "new_or_grown_warnings": 0})
    assert [(result.predicate, result.passed)
            for result in verify_postconditions(envelope, dirty)] == [
        ("StudyMapGrounded", True), ("RepoClean", False)]


def test_unobserved_selectors_raise_instead_of_passing():
    """A promised observation the harness never made is a harness bug."""
    envelope = _envelope()
    with pytest.raises(ChangeError):
        verify_postconditions(envelope, {})


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
        _envelope(evidence="material://demo/deck.pdf")
    with pytest.raises(ChangeError):
        _envelope(postconditions=[{"predicate": "RepoClean"}])
    with pytest.raises(ChangeError):
        _envelope(postconditions=[{
            "predicate": "RepoClean", "selector": "  ", "op": "is_true",
        }])


def test_malformed_contexts_refuse_at_construction():
    with pytest.raises(ChangeError):
        _context(approved_by="")
    with pytest.raises(ChangeError):
        _context(current_snapshot="")
    with pytest.raises(ChangeError):
        _context(current_contract_version="2")
    with pytest.raises(ChangeError):
        _context(current_revisions={"study-map-aml-l01": "six"})
