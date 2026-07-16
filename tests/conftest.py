"""Shared fixtures: the real repository root and a synthetic-minimal repo builder."""

from __future__ import annotations

import shutil
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    """A minimal, valid synthetic repository (inside LearningOS-shaped parents)."""
    los = tmp_path / "LearningOS"
    root = los / "repository"
    for d in ("knowledge/notes/mathematics", "knowledge/attachments", "records",
              "sources/collections", "work/inbox", "work/active", "generated/reports",
              "archive/workspaces", "tools", "tests"):
        (root / d).mkdir(parents=True)
    (los / "materials").mkdir()
    (los / "projects").mkdir()
    shutil.copytree(REPO_ROOT / "system" / "schema", root / "system" / "schema")

    (root / "knowledge" / "concepts.yaml").write_text(yaml.safe_dump({
        "concepts": [
            {"id": "concept-expected-value", "label": "Expected value",
             "aliases": ["Erwartungswert"]},
            {"id": "concept-variance", "label": "Variance", "aliases": ["Varianz"]},
        ]}), encoding="utf-8")
    (root / "knowledge" / "concept-relations.yaml").write_text(yaml.safe_dump({
        "relations": [
            {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        ]}), encoding="utf-8")
    (root / "sources" / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [
            {"id": "source-demo-book", "title": "Demo Book", "type": "book",
             "authors": ["A. Author"],
             "evaluations": [{"concepts": ["concept-expected-value"],
                              "roles": ["first-learning"], "level": "introductory",
                              "strengths": ["clear intuition"]}]},
        ]}), encoding="utf-8")
    (root / "records" / "modules.yaml").write_text(yaml.safe_dump({
        "modules": [
            {"id": "module-demo", "institution": "HU Berlin", "title": "Demo Module",
             "status": "enrolled", "attempts": [
                 {"termin": 1, "date": "2026-07-27", "result": "withdrawn"},
                 {"termin": 2, "date": "2026-10-09", "result": "registered"},
             ]},
        ]}), encoding="utf-8")
    (root / "knowledge" / "notes" / "mathematics" / "note-demo.md").write_text(
        textwrap.dedent("""\
        ---
        id: note-demo
        type: note
        title: Demo note
        created: 2026-07-16
        role: synthesis
        concepts: [concept-expected-value]
        sources: [source-demo-book]
        ---

        Body prose.
        """), encoding="utf-8")
    ws = root / "work" / "active" / "workspace-demo"
    (ws / "scratch").mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(textwrap.dedent("""\
        ---
        id: workspace-demo
        type: workspace
        title: Demo workspace
        created: 2026-07-16
        status: active
        concepts: [concept-expected-value]
        notes: [note-demo]
        ---

        ## Objective

        Demo.

        ## Current Scope

        Small.

        ## Open Questions

        None.

        ## Next Action

        Do the demo thing.
        """), encoding="utf-8")
    (root / "work" / "COORDINATION.md").write_text(textwrap.dedent("""\
        ---
        id: coordination
        type: coordination
        ---

        # Coordination

        ## Commitments

        (none)

        ## Priorities

        (none)

        ## Dependencies

        (none)

        ## Deferrals

        - Demo module deferred to 2. Termin (date lives in records/modules.yaml)
        """), encoding="utf-8")
    (root / ".gitignore").write_text("generated/*\n!generated/.gitkeep\n", encoding="utf-8")
    return root
