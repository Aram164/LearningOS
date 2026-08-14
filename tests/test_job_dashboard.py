"""The Job UI is an explicit, bounded read — never a projection leak."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml


LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), *args],
        capture_output=True,
        text=True,
        timeout=120,
    )


def write_job(mini_repo: Path, *, workspace_path: str = "workspace-job-deem/CONTEXT.md") -> Path:
    job = mini_repo.parent.parent / "Job"
    (job / "notes" / "stratum").mkdir(parents=True)
    (job / "workspace-job-deem" / "inputs").mkdir(parents=True)
    (job / "papers").mkdir(parents=True)
    (job / "workspace-job-deem" / "CONTEXT.md").write_text(textwrap.dedent("""\
        ---
        id: workspace-job-deem
        type: workspace
        title: Job workspace
        status: active
        standing: true
        ---

        ## Objective

        Build the system.

        ## Current Scope

        *Required now* — Current ticket.

        *Helpful now* — Read one chapter.

        ## Open Questions

        - What should be promoted later?

        ## Next Action

        Read the system map.
        """), encoding="utf-8")
    (job / "notes" / "note-skrub.md").write_text(textwrap.dedent("""\
        ---
        id: note-skrub
        type: note
        title: Skrub DAG
        state: evolving
        ---

        # Skrub DAG

        > The upstream graph Stratum intercepts.
        """), encoding="utf-8")
    (job / "notes" / "stratum" / "note-system.md").write_text(textwrap.dedent("""\
        ---
        id: note-system
        type: note
        title: Logical IR
        component: stratum/optimizer/ir.py
        verified_against: abc123 (2026-01-01)
        status: current
        ---

        # Logical IR

        > The system's operator representation.
        """), encoding="utf-8")
    (job / "workspace-job-deem" / "inputs" / "Polars-Learning-Plan.md").write_text(textwrap.dedent("""\
        # Polars Learning Plan

        ### Session 1 — Expressions
        - **Concept:** expression contexts.
        - **Source:** Polars guide.
        - **Stratum anchor:** compare both backends.
        - **Rebuild/stretch:** implement one expression.

        ## Definition of "there"
        Implement a backend from scratch.
        """), encoding="utf-8")
    (job / "papers" / "paper.pdf").write_bytes(b"%PDF-fixture")
    (job / "dashboard.yaml").write_text(yaml.safe_dump({
        "type": "job-dashboard",
        "schema_version": 1,
        "id": "job-dashboard",
        "title": "Job",
        "subtitle": "Bounded",
        "workspace": {"path": workspace_path},
        "notes": {"roots": ["notes"]},
        "learning_tracks": [{
            "id": "polars",
            "title": "Polars",
            "path": "workspace-job-deem/inputs/Polars-Learning-Plan.md",
        }],
        "papers": [{
            "id": "paper",
            "title": "Paper",
            "path": "papers/paper.pdf",
            "angle": "System context.",
        }],
        "canonical_shelf": [{
            "source_id": "source-demo-book",
            "horizon": "later",
            "why": "Reusable knowledge.",
        }],
    }, sort_keys=False), encoding="utf-8")
    return job


def test_job_dashboard_requires_explicit_confirmation(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-dashboard")
    assert proc.returncode == 2
    assert "explicit" in json.loads(proc.stdout)["error"]


def test_job_dashboard_is_bounded_and_not_projected(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "job-dashboard-v1"
    assert payload["access"] == {
        "scope": "job-dashboard",
        "read_only": True,
        "ephemeral": True,
        "excluded_from_manifest": True,
        "excluded_from_search": True,
        "excluded_from_ai": True,
    }
    dashboard = payload["dashboard"]
    assert dashboard["counts"] == {
        "notes": 2,
        "skrub_notes": 1,
        "system_notes": 1,
        "learning_sessions": 1,
        "papers": 1,
        "canonical_sources": 1,
    }
    assert dashboard["learning_tracks"][0]["sessions"][0]["title"] == "Expressions"
    assert dashboard["canonical_shelf"][0]["title"] == "Demo Book"
    assert all(not item["path"].startswith("/") for item in (
        dashboard["notes"]["skrub"]
        + dashboard["notes"]["stratum"]
        + dashboard["papers"]
        + dashboard["learning_tracks"]
    ))

    search = run_los(mini_repo, "search", "Skrub DAG")
    assert search.returncode == 0
    assert json.loads(search.stdout) == []


def test_notes_are_placed_on_the_stratum_pipeline(mini_repo):
    """The layer roster is the map — empty layers are the finding, not noise."""
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 0, proc.stderr
    notes = json.loads(proc.stdout)["dashboard"]["notes"]

    layers = {layer["id"]: layer for layer in notes["layers"]}
    assert list(layers) == [
        "capture", "logical", "rewrites", "physical", "runtime", "cross-cutting",
    ]
    # The upstream skrub note describes what Stratum intercepts, so it sits at capture.
    assert layers["capture"]["note_ids"] == ["note-skrub"]
    # component: stratum/optimizer/ir.py
    assert layers["logical"]["note_ids"] == ["note-system"]
    for empty in ("rewrites", "physical", "runtime", "cross-cutting"):
        assert layers[empty]["note_ids"] == []
    assert notes["stratum"][0]["layer"] == "logical"


def test_layer_derivation_prefers_the_specific_prefix(mini_repo):
    """`optimizer/ir/` and `optimizer/physical/` must beat the bare `optimizer/`."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from learning_os.commands.job import _layer_for

    cases = {
        "stratum/optimizer/ir/_join_ops.py": "logical",
        # The single-module form must not fall through to the rewrites bucket.
        "stratum/optimizer/ir.py": "logical",
        "stratum/optimizer/physical/_lowering.py": "physical",
        "stratum/optimizer/_algebraic_rewrites.py": "rewrites",
        "stratum/runtime/_scheduler.py": "runtime",
        "stratum/_rust_backend.py": "runtime",
        "stratum/_api.py": "capture",
        "stratum/patching/_patching.py": "capture",
        "stratum/_config.py": "cross-cutting",
        "": "",
    }
    for component, expected in cases.items():
        assert _layer_for(component, "stratum") == expected, component
    assert _layer_for("", "skrub") == "capture"


def test_job_dashboard_rejects_a_catalogue_path_escape(mini_repo):
    write_job(mini_repo, workspace_path="../outside.md")
    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 2
    assert "escapes the quarantine" in json.loads(proc.stdout)["error"]


# --------------------------------------------------------------------------
# Bounded Job writes (ADR-010). Every one is an explicit gesture, lands inside
# Job/, and leaves the canon byte-identical.
# --------------------------------------------------------------------------

WRITE_COMMANDS = (
    ("job-session-log", ("--text", "Read the join lowering path.")),
    ("job-note-stamp", ("--note", "note-system", "--commit", "beef123")),
    ("job-track-progress", ("--track", "polars", "--session", "1")),
)


def canonical_state(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


@pytest.mark.parametrize("command,extra", WRITE_COMMANDS)
def test_job_writes_require_explicit_confirmation(mini_repo, command, extra):
    write_job(mini_repo)
    proc = run_los(mini_repo, command, *extra)
    assert proc.returncode == 2
    assert "--confirm-job-access" in proc.stderr


@pytest.mark.parametrize("command,extra", WRITE_COMMANDS)
def test_job_writes_never_touch_the_canon(mini_repo, command, extra):
    write_job(mini_repo)
    before = canonical_state(mini_repo)
    proc = run_los(mini_repo, command, "--confirm-job-access", *extra)
    assert proc.returncode == 0, proc.stderr
    assert canonical_state(mini_repo) == before


def test_job_session_log_appends_and_receipts(mini_repo):
    job = write_job(mini_repo)
    first = run_los(mini_repo, "job-session-log", "--confirm-job-access",
                    "--text", "Traced the optimizer.")
    assert first.returncode == 0, first.stderr
    logged = json.loads(first.stdout)["logged"]
    assert logged.startswith("workspace-job-deem/scratch/")

    second = run_los(mini_repo, "job-session-log", "--confirm-job-access",
                     "--track", "polars", "--session", "2", "--text", "Lazy plans.")
    assert second.returncode == 0, second.stderr

    body = (job / logged).read_text(encoding="utf-8")
    assert "Traced the optimizer." in body
    assert "Lazy plans." in body
    assert "track `polars`" in body

    receipts = sorted((job / "operations" / "transactions").glob("transaction-*.yaml"))
    assert len(receipts) == 2
    receipt = yaml.safe_load(receipts[0].read_text(encoding="utf-8"))
    assert receipt["capability"] == "job.session.log"
    assert receipt["snapshot_before"] != receipt["snapshot_after"]


def test_job_note_stamp_rewrites_only_the_living_header(mini_repo):
    job = write_job(mini_repo)
    note = job / "notes" / "stratum" / "note-system.md"
    before = note.read_text(encoding="utf-8")

    proc = run_los(mini_repo, "job-note-stamp", "--confirm-job-access",
                   "--note", "note-system", "--commit", "beef123",
                   "--date", "2026-08-14")
    assert proc.returncode == 0, proc.stderr

    after = note.read_text(encoding="utf-8")
    assert "verified_against: beef123 (2026-08-14)" in after
    assert "status: current" in after
    # The body and every other frontmatter key are untouched: Aram writes the
    # notes, the operator only stamps them (notes/README.md).
    assert after.split("---")[2] == before.split("---")[2]
    assert "title: Logical IR" in after
    assert "component: stratum/optimizer/ir.py" in after


def test_job_note_stamp_refuses_a_note_without_the_living_header(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-note-stamp", "--confirm-job-access",
                   "--note", "note-skrub", "--commit", "beef123")
    assert proc.returncode == 2
    assert "not a living note" in proc.stderr


def test_job_track_progress_is_machine_owned_and_leaves_the_dashboard_alone(mini_repo):
    job = write_job(mini_repo)
    authored = (job / "dashboard.yaml").read_bytes()

    proc = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                   "--track", "polars", "--session", "2")
    assert proc.returncode == 0, proc.stderr
    again = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                    "--track", "polars", "--session", "1")
    assert again.returncode == 0, again.stderr

    progress = yaml.safe_load((job / "operations" / "progress.yaml").read_text("utf-8"))
    assert progress["tracks"]["polars"]["completed_sessions"] == [1, 2]
    assert (job / "dashboard.yaml").read_bytes() == authored


def test_job_track_progress_rejects_an_undeclared_track(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                   "--track", "not-a-track", "--session", "1")
    assert proc.returncode == 2
    assert "unknown learning track" in proc.stderr
