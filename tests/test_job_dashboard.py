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


def run_capability(root: Path, name: str, envelope: dict):
    return subprocess.run(
        [
            sys.executable, str(LOS), "--root", str(root),
            "capability", name, "--payload-file", "-",
        ],
        input=json.dumps(envelope),
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

        ### Session 2 — Lazy optimization
        - **Concept:** lazy plans.
        - **Source:** Lazy API.
        - **Stratum anchor:** compare explain output.
        - **Rebuild/stretch:** annotate one plan.

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
        "workspace": {
            "path": workspace_path,
            "id": "workspace-job-deem",
            "title": "Job workspace",
            "status": "active",
            "standing": True,
            "objective": "Build the system.",
            "current_scope": [
                {"label": "required-now", "text": "Current ticket."},
                {"label": "helpful-now", "text": "Read one chapter."},
            ],
            "open_questions": ["What should be promoted later?"],
            "next_action": "Read the system map.",
        },
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


def test_job_dashboard_fails_closed_when_its_producer_contract_drifts(mini_repo):
    job = write_job(mini_repo)
    path = job / "dashboard.yaml"
    dashboard = yaml.safe_load(path.read_text(encoding="utf-8"))
    dashboard["workspace"]["current_scope"][0]["label"] = "urgent-but-undeclared"
    path.write_text(yaml.safe_dump(dashboard, sort_keys=False), encoding="utf-8")

    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 2
    error = json.loads(proc.stdout)["error"]
    assert "job-dashboard-v2 contract violation" in error
    assert "urgent-but-undeclared" in error


def test_job_dashboard_is_bounded_and_not_projected(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "job-dashboard-v2"
    access = payload["access"]
    assert {key: access[key] for key in (
        "scope", "read_only", "ephemeral", "excluded_from_manifest",
        "excluded_from_search", "excluded_from_ai", "writes_through_gateway",
    )} == {
        "scope": "job-dashboard",
        "read_only": True,
        "ephemeral": True,
        "excluded_from_manifest": True,
        "excluded_from_search": True,
        "excluded_from_ai": True,
        "writes_through_gateway": True,
    }
    assert access["snapshot_id"].startswith("sha256:")
    assert set(access["allowed_roots"]) == {
        "legacy-plans", "notes", "papers", "plans", "workspace-job-deem",
    }
    dashboard = payload["dashboard"]
    assert dashboard["counts"] == {
        "notes": 2,
        "learning_notes": 0,
        "skrub_notes": 1,
        "system_notes": 1,
        "learning_tracks": 1,
        "learning_stages": 2,
        "open_tasks": 0,
        "completed_tasks": 0,
        "papers": 1,
        "canonical_sources": 1,
    }
    first_stage = dashboard["learning_tracks"][0]["stages"][0]
    assert first_stage["title"] == "Expressions"
    assert first_stage["objective"] == "expression contexts."
    assert first_stage["resources"][0]["kind"] == "read"
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

    reopened = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                       "--track", "polars", "--session", "2", "--state", "open")
    assert reopened.returncode == 0, reopened.stderr
    progress = yaml.safe_load((job / "operations" / "progress.yaml").read_text("utf-8"))
    assert progress["tracks"]["polars"]["completed_sessions"] == [1]


def test_job_track_progress_rejects_a_nonexistent_session(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                   "--track", "polars", "--session", "99")
    assert proc.returncode == 2
    assert "has no session 99" in proc.stderr


def test_job_note_save_creates_and_updates_a_learning_note(mini_repo):
    job = write_job(mini_repo)
    created = run_los(
        mini_repo, "job-note-save", "--confirm-job-access", "--approve",
        "--note", "Join order", "--title", "Join order", "--body", "First model.",
    )
    assert created.returncode == 0, created.stderr
    payload = json.loads(created.stdout)
    assert payload["note"] == "job-note-join-order"
    note = job / payload["path"]
    assert note.is_file()
    assert "First model." in note.read_text("utf-8")

    updated = run_los(
        mini_repo, "job-note-save", "--confirm-job-access", "--approve",
        "--note", "job-note-join-order", "--title", "Join ordering",
        "--body", "Revised model.",
    )
    assert updated.returncode == 0, updated.stderr
    text = note.read_text("utf-8")
    assert "title: Join ordering" in text
    assert "Revised model." in text and "First model." not in text

    dashboard = json.loads(run_los(
        mini_repo, "job-dashboard", "--confirm-job-access",
    ).stdout)["dashboard"]
    assert dashboard["notes"]["learning"][0]["id"] == "job-note-join-order"


def test_job_plan_save_shadows_legacy_without_rewriting_it(mini_repo):
    job = write_job(mini_repo)
    legacy = job / "workspace-job-deem" / "inputs" / "Polars-Learning-Plan.md"
    authored = legacy.read_bytes()
    plan = {
        "id": "polars",
        "title": "Polars production path",
        "horizon": "next",
        "cadence": "Two stages per month",
        "outcome": "Explain and implement a lazy optimizer.",
        "stages": [{
            "id": "stage-polars-logical-plans",
            "number": 1,
            "title": "Logical plans",
            "status": "pending",
            "objective": "Explain a logical plan and implement one transformation.",
            "done_when": ["A tested transformation preserves the declared schema."],
            "estimate_minutes": 90,
            "exam_critical": False,
            "concepts": ["concept-python"],
            "scope_triage": "required-now",
            "resources": [{
                "kind": "read",
                "label": "Polars lazy API",
                "url": "https://docs.pola.rs/user-guide/lazy/",
                "scope_triage": "required-now",
            }, {
                "kind": "practise",
                "label": "Implement and test one optimizer rewrite",
                "scope_triage": "required-now",
            }],
            "attachments": [],
            "source_feedback": [],
            "job_context": {
                "mental_models": [{"label": "Core model", "text": "IR before execution."}],
                "read_only_anchor": "Inspect Stratum's logical plan only; do not edit it.",
            },
        }],
    }
    proc = run_los(
        mini_repo, "job-plan-save", "--confirm-job-access", "--approve",
        "--plan", json.dumps(plan),
    )
    assert proc.returncode == 0, proc.stderr
    assert legacy.read_bytes() == authored
    dashboard = json.loads(run_los(
        mini_repo, "job-dashboard", "--confirm-job-access",
    ).stdout)["dashboard"]
    assert len(dashboard["learning_tracks"]) == 1
    assert dashboard["learning_tracks"][0]["source_kind"] == "structured"
    assert dashboard["learning_tracks"][0]["title"] == "Polars production path"
    stage = dashboard["learning_tracks"][0]["stages"][0]
    assert stage["objective"].startswith("Explain a logical plan")
    assert stage["resources"][0]["url"] == "https://docs.pola.rs/user-guide/lazy/"
    assert stage["job_context"]["mental_models"][0]["label"] == "Core model"
    stored = yaml.safe_load((job / "plans" / "polars.yaml").read_text("utf-8"))
    assert stored["schema_version"] == 2
    assert "stages" in stored and "sessions" not in stored


def test_job_plan_save_rejects_an_unstructured_stage(mini_repo):
    write_job(mini_repo)
    plan = {
        "id": "polars",
        "title": "Broken plan",
        "stages": [{
            "id": "stage-polars-broken",
            "number": 1,
            "title": "Broken",
            "objective": "This is not enough.",
            "done_when": [],
            "resources": [{"kind": "browse", "label": "Anything"}],
        }],
    }
    proc = run_los(
        mini_repo, "job-plan-save", "--confirm-job-access", "--approve",
        "--plan", json.dumps(plan),
    )
    assert proc.returncode == 2
    assert "done_when" in proc.stderr


def test_job_task_save_creates_and_updates_the_quarantined_list(mini_repo):
    write_job(mini_repo)
    task = {
        "title": "Trace the join planner",
        "details": "Write down one surprise.",
        "horizon": "now",
        "status": "open",
        "track_id": "polars",
    }
    created = run_los(
        mini_repo, "job-task-save", "--confirm-job-access", "--task", json.dumps(task),
    )
    assert created.returncode == 0, created.stderr
    task_id = json.loads(created.stdout)["task"]
    task.update({"id": task_id, "status": "done"})
    updated = run_los(
        mini_repo, "job-task-save", "--confirm-job-access", "--task", json.dumps(task),
    )
    assert updated.returncode == 0, updated.stderr
    dashboard = json.loads(run_los(
        mini_repo, "job-dashboard", "--confirm-job-access",
    ).stdout)["dashboard"]
    assert dashboard["tasks"][0]["id"] == task_id
    assert dashboard["tasks"][0]["status"] == "done"
    assert dashboard["counts"]["completed_tasks"] == 1


def test_job_capability_refuses_a_stale_snapshot_and_returns_its_receipt(mini_repo):
    write_job(mini_repo)
    payload = {
        "task": {"title": "Trace planner", "horizon": "now", "status": "open"},
        "confirm_job_access": True,
    }
    stale = run_capability(mini_repo, "job.task.save", {
        "request_id": "req-job-task-stale",
        "capability": "job.task.save",
        "expected_snapshot": "sha256:stale",
        "payload": payload,
    })
    assert stale.returncode == 3
    assert "changed since this view loaded" in json.loads(stale.stdout)["error"]

    dashboard = json.loads(run_los(
        mini_repo, "job-dashboard", "--confirm-job-access",
    ).stdout)
    saved = run_capability(mini_repo, "job.task.save", {
        "request_id": "req-job-task-current",
        "capability": "job.task.save",
        "expected_snapshot": dashboard["access"]["snapshot_id"],
        "payload": payload,
    })
    assert saved.returncode == 0, saved.stderr
    response = json.loads(saved.stdout)
    assert response["ok"] is True
    assert response["receipt_path"].startswith("operations/transactions/transaction-")
    assert response["result"]["receipt_path"] == response["receipt_path"]


def test_the_stratum_checkout_is_never_writable(mini_repo):
    """Aram's standing rule: Stratum changes in no shape or form.

    Pinned at the guard rather than trusted to the allowlist's silence, so a
    future edit that adds "stratum" to WRITABLE_ROOTS fails loudly here.
    """
    from learning_os.commands.job import JobDashboardError
    from learning_os.commands.job_write import (
        FORBIDDEN_ROOTS, WRITABLE_ROOTS, _writable_path,
    )

    assert "stratum" in FORBIDDEN_ROOTS
    assert not any(root.startswith("stratum") for root in WRITABLE_ROOTS)

    job = write_job(mini_repo)
    for attempt in (
        "stratum",
        "stratum/optimizer/ir/_join_ops.py",
        "notes/../stratum/setup.py",
    ):
        with pytest.raises(JobDashboardError) as caught:
            _writable_path(job, attempt)
        assert "read-only" in str(caught.value) or "escapes" in str(caught.value)


def test_drift_detection_leaves_no_trace_in_the_read_only_checkout(mini_repo):
    """Even the stat-cache refresh a plain `git diff` performs is a write."""
    source = (Path(__file__).resolve().parent.parent
              / "tools/learning_os/commands/job.py").read_text(encoding="utf-8")
    assert 'GIT_OPTIONAL_LOCKS": "0"' in source


def test_job_track_progress_rejects_an_undeclared_track(mini_repo):
    write_job(mini_repo)
    proc = run_los(mini_repo, "job-track-progress", "--confirm-job-access",
                   "--track", "not-a-track", "--session", "1")
    assert proc.returncode == 2
    assert "unknown learning track" in proc.stderr
