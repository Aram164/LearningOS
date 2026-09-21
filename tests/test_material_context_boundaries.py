"""Retrieval follows current routes and binds external assessment bytes."""

from __future__ import annotations

import json

import pytest
import yaml
from repo_builders import _compact_setup, run_los, write_minimal_pdf
from test_material_context import _binding, _context, _plant_note

from learning_os.material_synthesis import synthesis_destination


@pytest.mark.parametrize("change", ["unchanged", "changed", "removed", "restored"])
def test_assessment_continuation_binds_bytes_even_when_already_stale(mini_repo, change):
    _compact_setup(mini_repo)
    material = mini_repo.parent / "materials/source-demo-book/lecture-01.pdf"
    # This unrelated note supplies page one without observing the dossier's
    # source. Page two must bind that source through the assessment itself.
    body = "Weighted distributions example.\n"
    _plant_note(mini_repo, "note-unrelated-weighted", body,
                _binding("unavailable.pdf", "ab" * 32, body,
                         resolution="unavailable"))
    write_minimal_pdf(material, ["first changed version"])
    if change == "restored":
        material.unlink()
    first = _context(mini_repo, "weighted", "--limit", "1")
    assert first["total"] == 2 and first["next_offset"] == 1
    assert first["items"][0]["origin"] == "analysis-note"
    if change in {"changed", "restored"}:
        write_minimal_pdf(material, ["second changed version"])
    elif change == "removed":
        material.unlink()
    continued = run_los(
        mini_repo, "material-context", "weighted", "--limit", "1", "--offset", "1",
        "--expected-snapshot", first["snapshot_id"],
        "--expected-observations", first["observations_sha256"],
    )
    if change == "unchanged":
        assert continued.returncode == 0, continued.stderr
        second = json.loads(continued.stdout)
        assert second["items"][0]["origin"] == "unit-assessment"
        assert second["items"][0]["freshness"]["status"] == "stale"
    else:
        assert continued.returncode == 2, continued.stdout + continued.stderr
        assert "changed between pages" in continued.stderr
        restarted = _context(mini_repo, "weighted", "--limit", "1")
        assert restarted["observations_sha256"] != first["observations_sha256"]


@pytest.mark.parametrize("synthesis_state", ["absent", "draft"])
def test_unit_search_finds_routed_notes_before_synthesis_approval(mini_repo, synthesis_state):
    _compact_setup(mini_repo)
    destination = synthesis_destination(mini_repo, "unit-demo-l01")
    if synthesis_state == "absent":
        destination.unlink()
    else:
        dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
        dossier["status"] = "draft"
        destination.write_text(yaml.safe_dump(dossier), encoding="utf-8")
    body = "Independent density explanation.\n"
    _plant_note(mini_repo, "note-routed-density", body,
                _binding("source-demo-book/lecture-01.pdf", "ab" * 32, body))
    global_result = _context(mini_repo, "density")
    scoped = _context(mini_repo, "density", "--unit", "unit-demo-l01")
    assert [item["id"] for item in global_result["items"]] == ["note-routed-density"]
    assert [item["id"] for item in scoped["items"]] == ["note-routed-density"]
    assert scoped["pool"]["assessments"] == 0
    assert scoped["items"][0]["review"]["semantic_review"] == "unreviewed"
    brief = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--brief")
    assert brief.returncode == 0, brief.stderr
    assert [row["note_id"] for row in
            json.loads(brief.stdout)["analysis_refs"]["analysis_notes"]] == ["note-routed-density"]
