"""A short maintained journey through two common operator writes.

The full synthetic campaign lives in tests/eval; this test is the focused
regression entry point to run after a plan or analysis repair.
"""

from __future__ import annotations

import hashlib
import json

from gateway_helpers import approved_v2_call, approved_v2_cli, file_sha256
from repo_builders import material_fixture, run_los

from learning_os.loader import load_repo


def test_route_review_then_source_analysis_preserves_stage_override(mini_repo):
    repo, route_id, study_map_id = material_fixture(mini_repo)
    unit_id = repo.study_maps[study_map_id].unit_id
    stages_before = repo.study_maps[study_map_id].data["stages"]
    override = stages_before[0]["resources"][1]["angle"]

    change = {"angle": "Read the exact source before accepting the shortcut."}
    review = run_los(mini_repo, "route-patch", unit_id, route_id,
                     "--changes", json.dumps(change), "--check")
    assert review.returncode == 0, review.stdout + review.stderr
    approved = approved_v2_call(
        mini_repo, capability="route.patch",
        payload={"unit_id": unit_id, "route_id": route_id, "changes": change},
        artifact_ids=["module-demo", unit_id, study_map_id],
        idempotency_key="journey-route",
    )
    assert approved.returncode == 0, approved.stdout + approved.stderr
    route_receipt = json.loads(approved.stdout)["receipt_path"]
    assert (mini_repo / route_receipt).is_file()

    source_bytes = b"Plan A has 12 rows.\nThe missing value case needs a separate check.\n"
    material = mini_repo.parent / "materials/source-demo-book/book.pdf"
    material.write_bytes(source_bytes)
    digest = hashlib.sha256(source_bytes).hexdigest()
    body = b"  \n# Source analysis\n\nThe 12-row claim is bounded by this file.\r\n"
    body_file = mini_repo.parent / "journey-body.bin"
    body_file.write_bytes(body)
    note_id = "note-journey-source-analysis"
    note_path = f"knowledge/notes/mathematics/{note_id}.md"
    binding = {
        "resolution": "resolved", "source_id": "source-demo-book",
        "material": "source-demo-book/book.pdf",
        "recorded_source_digest": digest, "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 2},
        "frozen_input_sha256": hashlib.sha256(body).hexdigest(),
        "frozen_input_bytes": len(body),
    }
    saved = approved_v2_cli(
        mini_repo, "note-analysis-save",
        "--analysis", json.dumps({"id": note_id, "title": "Bounded source analysis",
                                  "path": note_path, "binding": binding}),
        "--body-file", str(body_file), "--body-file-sha256", file_sha256(body_file),
        artifact_ids=[note_id], idempotency_key="journey-analysis",
    )
    assert saved.returncode == 0, saved.stdout + saved.stderr
    analysis_receipt = json.loads(saved.stdout)["receipt_path"]
    assert analysis_receipt != route_receipt
    assert (mini_repo / analysis_receipt).is_file()
    assert (mini_repo / note_path).read_bytes().endswith(body)

    current = load_repo(mini_repo)
    first, second = current.study_maps[study_map_id].data["stages"][0]["resources"][:2]
    assert first["angle"] == change["angle"]
    assert second["angle"] == override
    assert current.study_maps[study_map_id].data["stages"][0]["status"] == stages_before[0]["status"]
    assert current.notes[note_id].meta["authorship"] == "operator-drafted"
    assert current.notes[note_id].meta["semantic_review"] == "unreviewed"
    generated = run_los(mini_repo, "generate")
    assert generated.returncode == 0, generated.stdout + generated.stderr
