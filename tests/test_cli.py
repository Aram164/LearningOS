"""CLI gateway tests (ADR-006): los.py status/--json, capture, delegation,
and the reading-room / adoption additions to the generator."""

from __future__ import annotations

import json

import yaml
from gateway_helpers import approved_v2_call, file_sha256, request_artifact_id
from repo_builders import run_los

from learning_os.genout import adoption_counts, generate_all
from learning_os.loader import load_repo


# ----------------------------------------------------------------- status
def test_status_json_shape_and_counts(mini_repo):
    proc = run_los(mini_repo, "status", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert {"learning_os", "root", "counts", "adoption",
            "exam_spine", "validation"} <= set(payload)
    c = payload["counts"]
    assert c["notes"] == 1
    assert c["concepts"] == 2
    assert c["sources"] == 1
    assert c["active_workspaces"] == 1
    assert c["inbox_items"] == 0
    # the fixture registers a 2. Termin attempt — it must be on the spine
    assert payload["exam_spine"][0]["date"] == "2026-10-09"
    assert payload["exam_spine"][0]["termin"] == 2
    assert payload["adoption"] == {"notes_reviewed": 0, "notes_with_evidence": 0}


def test_status_human_output_mentions_validation(mini_repo):
    proc = run_los(mini_repo, "status")
    assert proc.returncode == 0, proc.stderr
    assert "validation:" in proc.stdout
    assert "notes 1" in proc.stdout


# ---------------------------------------------------------------- capture
def test_capture_text_lands_in_inbox_and_routing_stays_operator(mini_repo):
    key = "capture-half-formed-001"
    proc = approved_v2_call(
        mini_repo,
        capability="capture.create",
        payload={"text": "a half-formed thought", "title": "Half formed"},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    assert response["receipt_path"]
    inbox = mini_repo / "work" / "inbox"
    files = [f for f in inbox.iterdir() if f.suffix == ".md"]
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert "a half-formed thought" in body
    assert "# Half formed" in body
    assert response["result"]["captured"] == files[0].relative_to(mini_repo).as_posix()


def test_capture_direct_cli_write_is_refused(mini_repo):
    proc = run_los(mini_repo, "capture", "--text", "must use the gateway")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_capture_empty_input_fails_cleanly(mini_repo):
    proc = run_los(mini_repo, "capture", "--text", "   ")
    assert proc.returncode == 2
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_capture_file_copy(mini_repo, tmp_path):
    src = tmp_path / "photo-notes.txt"
    src.write_text("scanned scribbles", encoding="utf-8")
    key = "capture-photo-notes-001"
    proc = approved_v2_call(
        mini_repo,
        capability="capture.create",
        payload={"file": str(src), "file_sha256": file_sha256(src)},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    assert proc.returncode == 0, proc.stderr
    copied = mini_repo / "work" / "inbox" / "photo-notes.txt"
    assert copied.read_text(encoding="utf-8") == "scanned scribbles"
    assert src.exists()  # capture copies; it never destroys the original


# ------------------------------------------------------------- delegation
def test_validate_delegates_and_passes_on_clean_repo(mini_repo):
    proc = run_los(mini_repo, "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "0 error(s)" in proc.stdout


def test_generate_delegates_and_writes_reading_room(mini_repo):
    proc = run_los(mini_repo, "generate")
    assert proc.returncode == 0, proc.stderr
    room = mini_repo / "generated" / "reading-room.md"
    assert room.exists()
    assert "GENERATED" in room.read_text(encoding="utf-8")[:400]


# ------------------------------------------- reading room & adoption view
def test_reading_room_composes_the_views(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    room = outputs["reading-room.md"]
    assert "2026-10-09" in room                      # exam spine (registered)
    assert "workspace-demo" in room                  # active workspace + next
    assert "Do the demo thing." in room
    assert "note-demo.md" in room                    # recently changed notes
    assert "coordination-view.md" in room            # links into deeper views
    assert "reports/health.md" in room
    assert "reviewed: 0/1" in room                   # adoption line


def test_health_carries_adoption_section(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    health = outputs["reports/health.md"]
    assert "Review & evidence adoption" in health
    assert "`reviewed` date: 0/1" in health
    assert "`evidence` entries: 0/1" in health


# ---------------------------------------------------------- concept canvas
def test_concept_canvas_is_valid_json_canvas(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    data = json.loads(outputs["concept-canvas.canvas"])
    assert "_generated" in data
    node_ids = {n["id"] for n in data["nodes"]}
    assert node_ids == {"concept-expected-value", "concept-variance"}
    for n in data["nodes"]:
        assert {"id", "type", "text", "x", "y", "width", "height"} <= set(n)
    # Study order, not the canonical sentence (ADR-016 decision 3). The
    # relation reads "variance builds on expected value"; the arrow has to point
    # at what you learn second.
    [edge] = data["edges"]
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["fromSide"] == "right"
    assert edge["toNode"] == "concept-variance"
    assert edge["toSide"] == "left"
    assert edge["label"] == "prerequisite for (builds-on)"
    # Identity is canonical and unchanged, so this is a direction fix rather
    # than a rewrite of every edge in the file.
    assert edge["id"] == "concept-variance--builds-on--concept-expected-value"
    # prerequisite-depth layout: the dependent sits one layer right of its prereq
    xs = {n["id"]: n["x"] for n in data["nodes"]}
    assert xs["concept-variance"] > xs["concept-expected-value"]
    # note links rendered on the concept card
    ev = next(n for n in data["nodes"] if n["id"] == "concept-expected-value")
    assert "note-demo" in ev["text"]


def test_a_semantic_canvas_edge_keeps_its_canonical_direction(mini_repo):
    """Only the strict subgraph is a learning order, so only it is redrawn.

    A semantic arrow that flipped would assert an order the relation does not
    carry — the exact confusion ADR-016 decision 2 exists to prevent.
    """
    f = mini_repo / "knowledge" / "concept-relations.yaml"
    f.write_text(yaml.safe_dump({"relations": [
        {"from": "concept-variance", "type": "applies-in",
         "to": "concept-expected-value"},
    ]}))
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    [edge] = json.loads(outputs["concept-canvas.canvas"])["edges"]
    assert edge["fromNode"] == "concept-variance"
    assert edge["fromSide"] == "left"
    assert edge["toNode"] == "concept-expected-value"
    assert edge["toSide"] == "right"
    assert edge["label"] == "applies-in"


def test_the_canvas_and_the_mermaid_map_agree_on_study_direction(mini_repo):
    """Both are generated from one relation set. A test that asserts one and
    not the other proves nothing — and until 2026-09-04 they disagreed."""
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    [edge] = json.loads(outputs["concept-canvas.canvas"])["edges"]
    concept_map = outputs["concept-map.md"]

    # The map says so in its own header, and draws `requires` solid and
    # `builds-on` dotted. Either way the prerequisite is on the left.
    assert "Arrows point from prerequisite to dependent" in concept_map
    [arrow] = [ln for ln in concept_map.splitlines()
               if "-->" in ln or "-.->" in ln]
    left, right = arrow.split("->")
    assert "concept_expected_value" in left
    assert "concept_variance" in right

    # The canvas edge runs between the same two concepts in the same order.
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["toNode"] == "concept-variance"


def test_adoption_counts_flag_drift_past_review(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    text = note.read_text(encoding="utf-8")
    note.write_text(text.replace("created: 2026-07-16",
                                 "created: 2026-07-16\nreviewed: 2026-07-20"),
                    encoding="utf-8")
    ad = adoption_counts(load_repo(mini_repo))
    assert ad["notes_reviewed"] == 1
    # mini_repo has no Git history -> the note counts as changed-since-review
    assert ad["changed_since_review"] == ["note-demo"]
