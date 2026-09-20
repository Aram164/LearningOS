"""Generation shadow execution: legacy-vs-derived equivalence proof.

Shadow phase (not production): selected generated artifacts are computed
both the old way and through the derived-state graph, and must agree
byte-for-byte while localized mutations execute only their declared
dependency closure. ``generate_all()`` stays authoritative throughout.

Section A pins the semantic/publication refactor itself; later sections
pin the shadow graph built on it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import build_mini_repo
from repo_builders import add_curriculum, write_yaml

from learning_os.genout.concepts import (
    build_backlinks,
    build_backlinks_semantic,
    build_concept_map,
    build_concept_map_body,
    build_dependency_report,
    build_dependency_report_body,
    publish_backlinks,
    publish_concept_map,
    publish_dependency_report,
)
from learning_os.loader import load_repo

REPO_ROOT = Path(__file__).resolve().parent.parent
STAMP = "2026-09-20T00:00:00+02:00"


def _backlinks_bytes(payload: dict) -> bytes:
    """Serialize exactly as outputs.py does for backlinks.json."""
    return (
        json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _write_workspace(path: Path, frontmatter: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")


def _rich_repo(root: Path):
    """Mini exercising every branch of the three builders."""
    write_yaml(root / "knowledge" / "concepts.yaml", {
        "concepts": [
            {"id": "c1", "label": "Concept One"},
            {"id": "c2", "label": "Concept Two"},
            {"id": "c3"},
            {"id": "c4", "label": "Isolated"},
            {"id": "c5", "label": "Cycle A"},
            {"id": "c6", "label": "Cycle B"},
        ]})
    write_yaml(root / "knowledge" / "concept-relations.yaml", {
        "relations": [
            {"from": "c2", "type": "requires", "to": "c1"},
            {"from": "c3", "type": "builds-on", "to": "c2"},
            {"from": "c1", "type": "motivates", "to": "c4"},
            {"from": "c5", "type": "requires", "to": "c6"},
            {"from": "c6", "type": "requires", "to": "c5"},
        ]})
    notes = root / "knowledge" / "notes"
    (notes / "note-a.md").write_text(
        "---\nid: note-a\ntitle: Note A\nconcepts: [c1, c2]\n"
        "sources: [source-demo-book]\ncontexts: [workspace-demo]\n"
        "supersedes: [note-old]\n---\n\nSee note://note-b for details.\n",
        encoding="utf-8")
    (notes / "note-b.md").write_text(
        "---\nid: note-b\ntitle: Note B\nconcepts: [c3]\n---\n\nPlain body.\n",
        encoding="utf-8")
    _write_workspace(
        root / "work" / "active" / "workspace-regex" / "CONTEXT.md",
        "id: workspace-regex\nstatus: active\nconcepts: [c1]",
        "Covers module-demo without declaring it.")
    _write_workspace(
        root / "work" / "active" / "workspace-dup" / "CONTEXT.md",
        "id: workspace-dup\nstatus: active\nnotes: [note-a, note-a]",
        "Duplicate note entry.")
    _write_workspace(
        root / "archive" / "workspaces" / "2026" / "ws-old" / "CONTEXT.md",
        "id: ws-old\nstatus: done\nmodule_ids: [module-demo]\nconcepts: [c2]",
        "Archived.")
    write_yaml(root / "curriculum" / "modules" / "module-lonely" / "module.yaml", {
        "id": "module-lonely", "type": "module", "title": "Lonely Module",
        "status": "enrolled"})
    return load_repo(root)


# ---------------------------------------------------------------------------
# A. Refactor equivalence: split builders reproduce the legacy bytes.
# ---------------------------------------------------------------------------

def test_backlinks_split_is_byte_identical(tmp_path: Path):
    mini = build_mini_repo(tmp_path / "mini")
    add_curriculum(mini)
    repo = _rich_repo(mini)
    old = build_backlinks(repo, STAMP)
    new = publish_backlinks(repo, build_backlinks_semantic(repo), STAMP)
    assert new == old
    assert _backlinks_bytes(new) == _backlinks_bytes(old)


def test_concept_map_split_is_byte_identical(tmp_path: Path):
    mini = build_mini_repo(tmp_path / "mini")
    add_curriculum(mini)
    repo = _rich_repo(mini)
    assert publish_concept_map(build_concept_map_body(repo), STAMP) == build_concept_map(
        repo, STAMP)


def test_dependency_report_split_is_byte_identical(tmp_path: Path):
    mini = build_mini_repo(tmp_path / "mini")
    add_curriculum(mini)
    repo = _rich_repo(mini)
    old = build_dependency_report(repo, build_backlinks(repo, STAMP), STAMP)
    assert publish_dependency_report(
        build_dependency_report_body(repo, build_backlinks(repo, STAMP)), STAMP) == old
    # The shadow feeds semantic (unstamped) backlinks: same bytes.
    assert publish_dependency_report(
        build_dependency_report_body(repo, build_backlinks_semantic(repo)), STAMP) == old


def test_rich_fixture_exercises_every_branch(tmp_path: Path):
    """Pin the fixture's branch coverage so it cannot silently rot."""
    mini = build_mini_repo(tmp_path / "mini")
    add_curriculum(mini)
    repo = _rich_repo(mini)
    backlinks = build_backlinks(repo, STAMP)
    assert backlinks["module_to_workspaces"]["module-demo"] == [
        "workspace-demo", "workspace-regex", "ws-old"]
    assert {"from": "note-a", "kind": "mentions"} in backlinks["note_incoming"]["note-b"]
    assert {"from": "note-a", "kind": "superseded-by"} in backlinks["note_incoming"]["note-old"]
    assert backlinks["workspace_to_notes"]["workspace-dup"] == ["note-a"]
    report = build_dependency_report(repo, backlinks, STAMP)
    assert "cycle detected among" in report
    assert "`ws-old` (archived)" in report
    assert "(no workspace references it)" in report
    assert "- **Isolated** (`c4`)" not in report
    assert '["c3"]' in build_concept_map(repo, STAMP)


def test_splits_are_byte_identical_without_prereqs(tmp_path: Path):
    mini = build_mini_repo(tmp_path / "mini")
    write_yaml(mini / "knowledge" / "concept-relations.yaml", {"relations": []})
    repo = load_repo(mini)
    assert publish_concept_map(build_concept_map_body(repo), STAMP) == build_concept_map(
        repo, STAMP)
    assert publish_dependency_report(
        build_dependency_report_body(repo, build_backlinks(repo, STAMP)), STAMP
    ) == build_dependency_report(repo, build_backlinks(repo, STAMP), STAMP)
    old = build_backlinks(repo, STAMP)
    assert publish_backlinks(repo, build_backlinks_semantic(repo), STAMP) == old


@pytest.mark.full_repo
def test_splits_are_byte_identical_on_real_repo():
    repo = load_repo(REPO_ROOT)
    old_backlinks = build_backlinks(repo, STAMP)
    assert publish_backlinks(repo, build_backlinks_semantic(repo), STAMP) == old_backlinks
    assert _backlinks_bytes(
        publish_backlinks(repo, build_backlinks_semantic(repo), STAMP)
    ) == _backlinks_bytes(old_backlinks)
    assert publish_concept_map(build_concept_map_body(repo), STAMP) == build_concept_map(
        repo, STAMP)
    assert publish_dependency_report(
        build_dependency_report_body(repo, old_backlinks), STAMP
    ) == build_dependency_report(repo, old_backlinks, STAMP)
