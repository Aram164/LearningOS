"""Shared fixtures: the real repository root and a synthetic-minimal repo builder."""

from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

import group_map
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Stamp embedded in the shared session snapshots below. No consumer asserts on
# its value (verified at introduction); it only needs to be stable so the
# snapshots are built once.
SHARED_GENERATED_AT = "shared-test-snapshot"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def pytest_collection_modifyitems(items):
    """Apply the area-group marker from tests/group_map.py; fail on drift."""
    errors = group_map.check_map(Path(__file__).resolve().parent)
    assert not errors, (
        "tests/group_map.py is out of step with tests/: "
        + "; ".join(errors))
    for item in items:
        name = Path(str(item.fspath)).name
        group = group_map.FILE_TO_GROUP.get(name)
        if group is not None:
            item.add_marker(getattr(pytest.mark, group))


@pytest.fixture(scope="session")
def real_repo():
    """The checked-in repository, loaded once.

    The suite never mutates the real tree (audited 2026-09-21: every write
    goes to tmp copies), and ``validate``/``generate_all``/``build_manifest``
    do not mutate the loaded object apart from idempotent memo caches — so
    every ``full_repo`` test can share one loaded snapshot instead of each
    paying ``load_repo`` again. Same assertions, one load.
    """
    from learning_os.loader import load_repo

    return load_repo(REPO_ROOT)


@pytest.fixture(scope="session")
def real_issues(real_repo):
    """``validate()`` over the checked-in repository, computed once."""
    from learning_os.rules import validate

    return validate(real_repo)


@pytest.fixture(scope="session")
def real_generated(real_repo):
    """``generate_all()`` over the checked-in repository, computed once."""
    from learning_os.genout import generate_all

    return generate_all(real_repo, generated_at=SHARED_GENERATED_AT)


@pytest.fixture(scope="session")
def real_manifest(real_generated):
    """The checked-in manifest, parsed from the shared ``generate_all``.

    ``generate_all(repo, at)["manifest.json"]`` parses to the same keys and
    values as ``build_manifest(repo, at, build_backlinks(repo, at))``
    (verified 2026-09-21) — key order follows production's sorted
    serialization, which is what every consumer reads. Same content the
    direct builders produce, without rebuilding it per test.
    """
    return json.loads(real_generated["manifest.json"])


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    """A minimal, valid synthetic repository (inside LearningOS-shaped parents)."""
    return build_mini_repo(tmp_path)


def build_mini_repo(tmp_path: Path) -> Path:
    """The builder behind the fixture.

    Exposed as a plain function because one test needs the same synthetic
    repository at module scope — a cross-process harness acts on a single
    repository across several scenarios. Reaching inside the fixture object to
    get at this was the alternative, and a second copy of the description was
    the worse one.
    """
    los = tmp_path / "LearningOS"
    root = los / "repository"
    for d in ("knowledge/notes/mathematics", "knowledge/attachments", "records",
              "sources/collections", "work/inbox", "work/active", "generated/reports",
              "archive/workspaces", "tools", "tests"):
        (root / d).mkdir(parents=True)
    (los / "materials").mkdir()
    shutil.copytree(REPO_ROOT / "system" / "schema", root / "system" / "schema")
    shutil.copytree(REPO_ROOT / "system" / "contracts", root / "system" / "contracts")

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
