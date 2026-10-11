"""Dossier analysis refs: reuse note prose without copying it.

A route assessment may reference durable source-analysis notes instead of
duplicating chapter analysis. Each ref pins the note revision the approver
saw plus the exact anchor and inspected material identity; a later note
edit, a retargeted anchor, or a changed inspected range stales the dossier
until re-review. Freshness derives the same verdict the validator enforces,
and the projection carries the refs to consumers.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml
from repo_builders import _compact_setup, _valid_dossier

from learning_os.material_synthesis import (
    ANALYSIS_REFS_STALE,
    MaterialSynthesisError,
    MaterialSynthesisUnitNotFound,
    current_unit_material_basis,
    material_synthesis_freshness,
    synthesis_destination,
    validate_unit_material_synthesis,
)

NOTE_ID = "note-ref-density"
ANCHOR = {"topic": "Density", "purpose": "intuition",
          "locator": "lecture-01.pdf p.1"}
RANGE = {"start": 1, "end": 1}
MATERIAL = "source-demo-book/lecture-01.pdf"


def _plant_note(root: Path, body: str = "Density prose.\n", material: str = MATERIAL):
    digest = hashlib.sha256((root.parent / "materials" / material).read_bytes()).hexdigest()
    meta = {"id": NOTE_ID, "type": "note", "role": "reference",
            "title": "Density analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "user-reviewed",
            "material_analysis": {
                "resolution": "resolved",
                "material": material,
                "source_id": "source-demo-book",
                "recorded_source_digest": digest,
                "live_source_digest": digest,
                "inspected_range": dict(RANGE),
                "anchors": [dict(ANCHOR)],
                "frozen_input_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "frozen_input_bytes": len(body.encode()),
            }}
    path = root / "knowledge/notes/mathematics" / f"{NOTE_ID}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))
    return path


def _digest_of(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _ref(note_digest: str, **overrides):
    ref = {"note_id": NOTE_ID, "note_revision": 0, "note_digest": note_digest,
           "anchor": dict(ANCHOR), "material": MATERIAL,
           "inspected_range": dict(RANGE)}
    ref.update(overrides)
    return ref


def _seed(root: Path, ref: str | dict | None = None):
    """Plant the note and dossier; "valid" binds the ref to live bytes."""
    _compact_setup(root)
    note_path = _plant_note(root)
    if ref == "valid":
        ref = _ref(_digest_of(note_path))
    dossier = _valid_dossier(root, "route-demo-book", "lecture-01.pdf")
    if ref is not None:
        dossier["route_assessments"][0]["analysis_refs"] = [ref]
    synthesis_destination(root, "unit-demo-l01").write_text(
        yaml.safe_dump(dossier, sort_keys=False), encoding="utf-8")
    return dossier


def _assessment_ref(dossier: dict) -> dict:
    return dossier["route_assessments"][0]["analysis_refs"][0]


def test_valid_ref_passes_validation_and_freshness(mini_repo):
    dossier = _seed(mini_repo, "valid")
    assert validate_unit_material_synthesis(
        mini_repo, "unit-demo-l01", dossier) is dossier
    assert material_synthesis_freshness(
        mini_repo, "unit-demo-l01", dossier) == {
            "status": "current", "reasons": []}


def test_note_edit_after_approval_stales_dossier(mini_repo, tmp_path):
    from gateway_helpers import approved_v2_cli, file_sha256

    dossier = _seed(mini_repo, "valid")
    assert validate_unit_material_synthesis(
        mini_repo, "unit-demo-l01", dossier) is dossier
    note_path = mini_repo / "knowledge/notes/mathematics" / f"{NOTE_ID}.md"
    revised = tmp_path / "revised.md"
    revised.write_bytes(note_path.read_bytes() + b"\nEdited after approval.\n")
    proc = approved_v2_cli(
        mini_repo, "note-revise", NOTE_ID,
        "--file", str(revised), "--approve",
        "--file-sha256", file_sha256(revised),
        artifact_ids=[NOTE_ID],
        idempotency_key="synthesis-ref-note-revise",
    )
    assert proc.returncode == 0, proc.stderr
    with pytest.raises(MaterialSynthesisError,
                       match="note was revised after approval"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)
    assert material_synthesis_freshness(
        mini_repo, "unit-demo-l01", dossier) == {
            "status": "stale", "reasons": [ANALYSIS_REFS_STALE]}
    assert ANALYSIS_REFS_STALE == "analysis-refs-stale"


def test_wrong_revision_refused(mini_repo):
    dossier = _seed(mini_repo, "valid")
    _assessment_ref(dossier)["note_revision"] = 999
    with pytest.raises(MaterialSynthesisError,
                       match="note was revised after approval"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)


def test_direct_body_edit_breaks_the_content_digest(mini_repo):
    dossier = _seed(mini_repo, "valid")
    assert validate_unit_material_synthesis(
        mini_repo, "unit-demo-l01", dossier) is dossier
    note_path = mini_repo / "knowledge/notes/mathematics" / f"{NOTE_ID}.md"
    with note_path.open("ab") as handle:
        handle.write(b"\nUngoverned body change.\n")
    with pytest.raises(MaterialSynthesisError,
                       match="note bytes differ from the approved content"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)
    assert material_synthesis_freshness(
        mini_repo, "unit-demo-l01", dossier) == {
            "status": "stale", "reasons": [ANALYSIS_REFS_STALE]}


def test_misbound_refs_refused(mini_repo):
    mutations = [
        ({"note_id": "note-missing"}, "note is missing"),
        ({"note_id": "note-demo"}, "note carries no material analysis"),
        ({"anchor": {**ANCHOR, "purpose": "other"}},
         "anchor is not among the note's recorded anchors"),
        ({"material": "other/deck.pdf"},
         "material identity differs from the note's binding"),
        ({"inspected_range": {"start": 1, "end": 9}},
         "inspected range differs from the note's binding"),
        ({"note_digest": "sha256:" + "ff" * 32},
         "note bytes differ from the approved content"),
    ]
    for fields, problem in mutations:
        dossier = _seed(mini_repo, "valid")
        _assessment_ref(dossier).update(fields)
        with pytest.raises(MaterialSynthesisError, match=problem):
            validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)


def test_uncoordinated_unit_mutation_refuses_at_the_binding_guard(mini_repo):
    """SPEC (cq) 5: the binding guard precedes the repository lookup."""
    dossier = _seed(mini_repo, None)
    assert dossier["unit_id"] == "unit-demo-l01"
    # A request for another unit against this dossier refuses at the
    # binding guard, even when the requested unit would also miss.
    for requested in ("unit-demo-l02", "unit-nope"):
        with pytest.raises(MaterialSynthesisError) as caught:
            validate_unit_material_synthesis(mini_repo, requested, dossier)
        assert type(caught.value) is MaterialSynthesisError
        assert str(caught.value) == (
            "dossier unit_id does not match the requested unit")


def test_malformed_dossier_schema_precedes_the_lookup(mini_repo):
    """SPEC (cq) 5: schema failures precede binding and lookup alike."""
    dossier = _seed(mini_repo, None)
    dossier["unit_id"] = "unit-nope"
    del dossier["comparisons"]
    with pytest.raises(MaterialSynthesisError) as caught:
        validate_unit_material_synthesis(mini_repo, "unit-nope", dossier)
    assert type(caught.value) is MaterialSynthesisError
    assert "unit not found" not in str(caught.value)

    bound = _seed(mini_repo, None)
    del bound["comparisons"]
    with pytest.raises(MaterialSynthesisError) as caught:
        validate_unit_material_synthesis(mini_repo, "unit-demo-l02", bound)
    assert type(caught.value) is MaterialSynthesisError
    assert "does not match the requested unit" not in str(caught.value)


def test_malformed_ref_fails_schema(mini_repo):
    dossier = _seed(mini_repo, "valid")
    del _assessment_ref(dossier)["note_revision"]
    with pytest.raises(MaterialSynthesisError, match="note_revision"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)


def test_unknown_unit_lookup_raises_the_structured_subclass(mini_repo):
    """SPEC (cq) 5: the genuine lookup carries id and actual candidates."""
    from learning_os.loader import load_repo

    dossier = _seed(mini_repo, None)
    dossier["unit_id"] = "unit-nope"
    with pytest.raises(MaterialSynthesisUnitNotFound) as caught:
        validate_unit_material_synthesis(mini_repo, "unit-nope", dossier)
    exc = caught.value
    assert type(exc) is MaterialSynthesisUnitNotFound
    assert str(exc) == "unit not found: unit-nope"
    assert exc.unit_id == "unit-nope"
    assert list(exc.candidates) == list(load_repo(mini_repo).units)
    # ValueError compatibility for every other caller.
    assert isinstance(exc, MaterialSynthesisError)
    with pytest.raises(ValueError, match="unit not found: unit-nope"):
        validate_unit_material_synthesis(mini_repo, "unit-nope", dossier)


def test_publication_helper_types_only_the_subclass(mini_repo, monkeypatch):
    """SPEC (cq) 5: NotFound for the lookup; other errors pass through."""
    import learning_os.material_synthesis as synthesis_mod
    from learning_os.domain import suggest as suggest_mod
    from learning_os.domain.failures import NotFound
    from learning_os.loader import load_repo
    from learning_os.ops.handlers.plan import _validate_publication_synthesis

    dossier = _seed(mini_repo, None)
    miss = "unit-nope"
    dossier["unit_id"] = miss
    repo = load_repo(mini_repo)
    with pytest.raises(NotFound) as caught:
        _validate_publication_synthesis(mini_repo, miss, dossier)
    exc = caught.value
    assert type(exc) is NotFound
    assert str(exc) == "unit not found: unit-nope"
    assert exc.site == "unit.material-synthesis.publish.unknown-unit"
    assert exc.gateway_message == "unit not found: unit-nope"
    assert exc.exit_code == 2
    assert exc.reason == "NOT_FOUND"
    assert exc.suggestions == suggest_mod.suggestions(miss, repo.units)

    # A non-lookup dossier failure propagates unwrapped, exact type.
    stale = _seed(mini_repo, None)
    stale["basis"]["policy"] = "tiered-v1"
    with pytest.raises(MaterialSynthesisError) as caught:
        _validate_publication_synthesis(mini_repo, "unit-demo-l01", stale)
    assert type(caught.value) is MaterialSynthesisError

    # The helper adds no repository read of its own: the validator's
    # single load supplies the carried candidates.
    loads = []
    real_load = synthesis_mod.load_repo

    def counting(root):
        loads.append(root)
        return real_load(root)

    monkeypatch.setattr(synthesis_mod, "load_repo", counting)
    with pytest.raises(NotFound):
        _validate_publication_synthesis(mini_repo, miss, dossier)
    assert loads == [mini_repo]


def test_publication_validations_route_through_the_helper(mini_repo, monkeypatch):
    """SPEC (cq) 5: both publication validations translate the lookup."""
    from learning_os.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
    )
    from learning_os.domain.failures import NotFound
    from learning_os.ops.context import OpContext
    from learning_os.ops.handlers import plan as plan_handlers

    dossier = _seed(mini_repo, None)
    miss = "unit-nope"
    dossier["unit_id"] = miss
    ctx = OpContext(root=mini_repo, operation="unit.material-synthesis.publish",
                    channel="operator", invocation="command", gateway=None)
    # First validation: the fast-feedback call translates the lookup.
    with pytest.raises(NotFound) as caught:
        plan_handlers.unit_material_synthesis_publish(
            ctx, {"unit_id": miss, "record": dossier})
    assert type(caught.value) is NotFound
    assert caught.value.site == "unit.material-synthesis.publish.unknown-unit"

    # Second validation: the commit authority translates a unit lost
    # after feedback, with the real validator on both calls.
    raced = _seed(mini_repo, None)
    real_basis = plan_handlers.current_unit_material_basis

    def basis_then_vanish(root, unit_id, **kwargs):
        out = real_basis(root, unit_id, **kwargs)
        (root / "curriculum/modules/module-demo/units/unit-demo-l01"
         / "unit.yaml").unlink()
        return out

    monkeypatch.setattr(plan_handlers, "current_unit_material_basis",
                        basis_then_vanish)
    context = GatewayRequestContext(
        request_id="req-1", idempotency_key="key-1",
        capability="unit.material-synthesis.publish", channel="operator",
        intent_sha256="sha256:" + "0" * 64,
        approval_kind="direct-user-gesture",
        approval_subject_sha256="sha256:" + "0" * 64)
    ctx2 = OpContext(root=mini_repo, operation="unit.material-synthesis.publish",
                     channel="operator", invocation="command", gateway=context)
    with gateway_request_context(context):
        with pytest.raises(NotFound) as caught:
            plan_handlers.unit_material_synthesis_publish(
                ctx2, {"unit_id": "unit-demo-l01", "record": raced,
                       "approve": True})
    assert type(caught.value) is NotFound
    assert str(caught.value) == "unit not found: unit-demo-l01"
    assert caught.value.site == "unit.material-synthesis.publish.unknown-unit"


def test_ref_rides_projection(mini_repo):
    from learning_os.genout.projection.records_curriculum import (
        project_unit_material_syntheses,
    )
    from learning_os.loader import load_repo

    _seed(mini_repo, "valid")
    projected = project_unit_material_syntheses(load_repo(mini_repo))
    assert len(projected) == 1
    note_path = mini_repo / "knowledge/notes/mathematics" / f"{NOTE_ID}.md"
    assert projected[0]["route_assessments"][0]["analysis_refs"] == [
        _ref(_digest_of(note_path))]
    assert projected[0]["freshness"] == {"status": "current", "reasons": []}


def test_dossier_without_refs_is_unaffected(mini_repo):
    dossier = _seed(mini_repo, None)
    assert validate_unit_material_synthesis(
        mini_repo, "unit-demo-l01", dossier) is dossier
    assert material_synthesis_freshness(
        mini_repo, "unit-demo-l01", dossier) == {
            "status": "current", "reasons": []}


@pytest.mark.parametrize("change", ["changed", "removed"])
def test_refreshing_route_basis_cannot_reapprove_stale_analysis(mini_repo, change):
    dossier = _seed(mini_repo, "valid")
    source = mini_repo.parent / "materials" / MATERIAL
    if change == "changed":
        source.write_bytes(source.read_bytes() + b"\nnew edition\n")
    else:
        source.unlink()
    # A new review must not reuse the old interpretation merely by rebinding
    # the route's basis. The pinned note still describes the previous bytes.
    dossier["basis"].update(current_unit_material_basis(mini_repo, "unit-demo-l01"))
    for row in dossier["route_assessments"]:
        for evidence in row.get("evidence", []):
            evidence["checksum"] = dossier["basis"]["material_checksums"][row["route_id"]]
    with pytest.raises(MaterialSynthesisError, match="analysis source is not current"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)
    assert material_synthesis_freshness(mini_repo, "unit-demo-l01", dossier) == {
        "status": "stale", "reasons": [ANALYSIS_REFS_STALE]}


def test_referenced_material_outside_route_basis_binds_continuation(mini_repo):
    from repo_builders import run_los
    from test_material_context import _binding, _context
    from test_material_context import _plant_note as plant_search_note

    dossier = _seed(mini_repo, "valid")
    material = "source-demo-book/analysis-only.pdf"
    source = mini_repo.parent / "materials" / material
    source.write_bytes(b"original analysis material")
    note = _plant_note(mini_repo, material=material)
    dossier["route_assessments"][0]["analysis_refs"] = [
        _ref(_digest_of(note), material=material)]
    synthesis_destination(mini_repo, "unit-demo-l01").write_text(
        yaml.safe_dump(dossier, sort_keys=False), encoding="utf-8")
    body = "Weighted example from another source.\n"
    plant_search_note(mini_repo, "note-page-one", body,
                      _binding("unavailable.pdf", "ab" * 32, body,
                               resolution="unavailable"))
    first = _context(mini_repo, "weighted", "--limit", "1")
    assert first["total"] == 2
    source.write_bytes(b"first changed analysis material")
    stale = _context(mini_repo, "weighted", "--limit", "1")
    source.write_bytes(b"second changed analysis material")
    continued = run_los(
        mini_repo, "material-context", "weighted", "--offset", "1",
        "--expected-snapshot", stale["snapshot_id"],
        "--expected-observations", stale["observations_sha256"])
    # Observed bytes moved between pages: an optimistic-concurrency
    # conflict (exit 3), like a stale --expected-snapshot.
    assert continued.returncode == 3, continued.stdout + continued.stderr
    assert "changed between pages" in continued.stderr
    fresh = _context(mini_repo, "weighted")
    assessment = next(row for row in fresh["items"] if row["origin"] == "unit-assessment")
    assert assessment["freshness"] == {"status": "stale", "reasons": [ANALYSIS_REFS_STALE]}
