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
    material_synthesis_freshness,
    synthesis_destination,
    validate_unit_material_synthesis,
)

NOTE_ID = "note-ref-density"
ANCHOR = {"topic": "Density", "purpose": "intuition",
          "locator": "lecture-01.pdf p.1"}
RANGE = {"start": 1, "end": 1}
MATERIAL = "source-demo-book/lecture-01.pdf"


def _plant_note(root: Path, body: str = "Density prose.\n"):
    meta = {"id": NOTE_ID, "type": "note", "role": "reference",
            "title": "Density analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "user-reviewed",
            "material_analysis": {
                "resolution": "resolved",
                "material": MATERIAL,
                "source_id": "source-demo-book",
                "recorded_source_digest": "0" * 64,
                "live_source_digest": "0" * 64,
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


def test_malformed_ref_fails_schema(mini_repo):
    dossier = _seed(mini_repo, "valid")
    del _assessment_ref(dossier)["note_revision"]
    with pytest.raises(MaterialSynthesisError, match="note_revision"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", dossier)


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
