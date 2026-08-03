"""CLI gateway tests (ADR-006): los.py status/--json, capture, delegation,
and the reading-room / adoption additions to the generator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from learning_os.genout import adoption_counts, generate_all
from learning_os.loader import load_repo

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str, stdin: str | None = None):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        capture_output=True, text=True, input=stdin, timeout=120)


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
    proc = run_los(mini_repo, "capture", "--text", "a half-formed thought",
                   "--title", "Half formed")
    assert proc.returncode == 0, proc.stderr
    inbox = mini_repo / "work" / "inbox"
    files = [f for f in inbox.iterdir() if f.suffix == ".md"]
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert "a half-formed thought" in body
    assert "# Half formed" in body
    assert "operator" in proc.stdout  # routing explicitly not the CLI's job


def test_capture_empty_input_fails_cleanly(mini_repo):
    proc = run_los(mini_repo, "capture", "--text", "   ")
    assert proc.returncode == 2
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_capture_file_copy(mini_repo, tmp_path):
    src = tmp_path / "photo-notes.txt"
    src.write_text("scanned scribbles", encoding="utf-8")
    proc = run_los(mini_repo, "capture", "--file", str(src))
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
    [edge] = data["edges"]
    assert edge["fromNode"] == "concept-variance"
    assert edge["toNode"] == "concept-expected-value"
    assert edge["label"] == "builds-on"
    # prerequisite-depth layout: the dependent sits one layer right of its prereq
    xs = {n["id"]: n["x"] for n in data["nodes"]}
    assert xs["concept-variance"] > xs["concept-expected-value"]
    # note links rendered on the concept card
    ev = next(n for n in data["nodes"] if n["id"] == "concept-expected-value")
    assert "note-demo" in ev["text"]


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
