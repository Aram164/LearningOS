"""The Job UI is an explicit, bounded read — never a projection leak."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

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


def test_job_dashboard_rejects_a_catalogue_path_escape(mini_repo):
    write_job(mini_repo, workspace_path="../outside.md")
    proc = run_los(mini_repo, "job-dashboard", "--confirm-job-access")
    assert proc.returncode == 2
    assert "escapes the quarantine" in json.loads(proc.stdout)["error"]
