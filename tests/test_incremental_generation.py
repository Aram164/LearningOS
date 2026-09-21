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
import yaml
from conftest import build_mini_repo
from repo_builders import add_curriculum, write_yaml

import learning_os.genout.derived_generation as shadow_module
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
from learning_os.genout.derived_generation import (
    BACKLINKS_PRODUCERS,
    BACKLINKS_SEMANTIC_ID,
    CONCEPT_MAP_BODY_ID,
    CONCEPT_MAP_PRODUCERS,
    DEPENDENCY_REPORT_BODY_ID,
    DEPENDENCY_REPORT_PRODUCERS,
    compare_shadow_generation,
    generation_input_digests,
    generation_registry,
)
from learning_os.loader import load_repo
from learning_os.loading import parse_frontmatter

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


# ---------------------------------------------------------------------------
# B. Generation inputs, registry, cold/warm shadow runs.
# ---------------------------------------------------------------------------

ALL_INPUTS = (
    "gen.notes",
    "gen.concepts",
    "gen.relations",
    "gen.workspaces",
    "gen.modules",
    "gen.units",
    "gen.study_maps",
)


def _curriculum_mini(tmp_path: Path, name: str = "mini") -> Path:
    mini = build_mini_repo(tmp_path / name)
    add_curriculum(mini)
    return mini


def _stage_shadow_producers(root: Path) -> None:
    """Copy the real shadow producer bytes under a mini root."""
    for rel in dict.fromkeys([
        *BACKLINKS_PRODUCERS, *CONCEPT_MAP_PRODUCERS, *DEPENDENCY_REPORT_PRODUCERS
    ]):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / rel).read_bytes())


def _trace_summary(trace) -> dict[str, tuple[str, str]]:
    return {event.node: (event.status, event.reason) for event in trace}


def _moved_only(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {name for name in before if before[name] != after[name]}


def test_input_digests_cover_seven_domains(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    digests = generation_input_digests(mini)
    assert sorted(digests) == sorted(ALL_INPUTS)
    assert digests == generation_input_digests(mini)


def test_each_domain_mutation_moves_exactly_its_digest(tmp_path: Path):
    cases = [
        ("gen.notes", "knowledge/notes/mathematics/note-demo.md"),
        ("gen.concepts", "knowledge/concepts.yaml"),
        ("gen.relations", "knowledge/concept-relations.yaml"),
        ("gen.workspaces", "work/active/workspace-demo/CONTEXT.md"),
        ("gen.modules", "curriculum/modules/module-demo/module.yaml"),
        ("gen.units", "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"),
        ("gen.study_maps", "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"),
    ]
    for index, (domain, rel) in enumerate(cases):
        mini = _curriculum_mini(tmp_path, f"mini-{index}")
        before = generation_input_digests(mini)
        target = mini / rel
        target.write_text(target.read_text(encoding="utf-8") + "\n# probe\n", encoding="utf-8")
        assert _moved_only(before, generation_input_digests(mini)) == {domain}


def test_source_map_and_legacy_snapshot_are_inputs(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = generation_input_digests(mini)
    source_map = mini / "curriculum" / "modules" / "module-demo" / "source-map.yaml"
    source_map.write_text(
        source_map.read_text(encoding="utf-8") + "\n# probe\n", encoding="utf-8")
    assert _moved_only(before, generation_input_digests(mini)) == {"gen.study_maps"}
    before = generation_input_digests(mini)
    legacy = mini / "records" / "modules.yaml"
    legacy.write_text(legacy.read_text(encoding="utf-8") + "\n# probe\n", encoding="utf-8")
    assert _moved_only(before, generation_input_digests(mini)) == {"gen.modules"}


def test_non_inputs_move_no_digest(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    before = generation_input_digests(mini)
    paths = mini / "work" / "active" / "workspace-demo" / "paths"
    paths.mkdir()
    (paths / "path-extra.yaml").write_text("id: path-extra\n", encoding="utf-8")
    (mini / "knowledge" / "notes" / "scratch.txt").write_text("not markdown\n", encoding="utf-8")
    (mini / "knowledge" / "concepts").mkdir()
    (mini / "knowledge" / "concepts" / "README.md").write_text("not yaml\n", encoding="utf-8")
    assert generation_input_digests(mini) == before


def test_registry_resolves_and_producers_exist(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    repo = load_repo(mini)
    registry = generation_registry(repo)
    assert sorted(registry) == sorted([
        BACKLINKS_SEMANTIC_ID, CONCEPT_MAP_BODY_ID, DEPENDENCY_REPORT_BODY_ID])
    inputs = generation_input_digests(mini)
    for node_id, (spec, _build) in registry.items():
        assert spec.id == node_id
        for name in spec.direct_inputs:
            assert name in inputs, f"{node_id} is missing input {name}"
        for dep in spec.dependencies:
            assert dep in registry, f"{node_id} is missing dependency {dep}"
    for rel in dict.fromkeys([
        *BACKLINKS_PRODUCERS, *CONCEPT_MAP_PRODUCERS, *DEPENDENCY_REPORT_PRODUCERS
    ]):
        assert (REPO_ROOT / rel).is_file(), f"renamed producer is untracked: {rel}"


def test_cold_shadow_rebuilds_and_matches(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    repo = _rich_repo(mini)
    trace: list = []
    comparison = compare_shadow_generation(repo, STAMP, trace=trace)
    assert comparison.equivalent, comparison.artifacts
    assert _trace_summary(trace) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "cache-miss"),
        CONCEPT_MAP_BODY_ID: ("rebuilt", "cache-miss"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "cache-miss"),
    }
    generated = mini / "generated"
    assert {path.name for path in generated.iterdir() if path.is_file()} == set()
    assert (generated / "derived-state" / "state-v1.json").is_file()


def test_warm_shadow_hits_and_matches(tmp_path: Path):
    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    repo = _rich_repo(mini)
    assert compare_shadow_generation(repo, STAMP).equivalent
    trace: list = []
    comparison = compare_shadow_generation(load_repo(mini), STAMP, trace=trace)
    assert comparison.equivalent
    assert _trace_summary(trace) == {
        BACKLINKS_SEMANTIC_ID: ("hit", "node-key-equal"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }


def test_compare_reports_mismatch_per_artifact(tmp_path: Path, monkeypatch):
    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    repo = _rich_repo(mini)
    monkeypatch.setattr(shadow_module, "build_concept_map_body", lambda repo: "TAMPERED")
    comparison = compare_shadow_generation(repo, STAMP)
    assert not comparison.equivalent
    assert comparison.artifacts == {
        "backlinks.json": True, "concept-map.md": False, "dependency-report.md": True}
    assert comparison.shadow["concept-map.md"] != comparison.legacy["concept-map.md"]


def test_cli_shadow_reports_exact(tmp_path: Path):
    import subprocess
    import sys

    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "generate.py"),
         "--root", str(mini), "--shadow-derived"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    assert "shadow generation: exact" in proc.stdout
    assert "3/3 artifacts byte-identical" in proc.stdout
    assert "semantic: rebuilt (cold)" in proc.stdout


def test_cli_shadow_json_reports_nodes(tmp_path: Path):
    import json
    import subprocess
    import sys

    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "generate.py"),
         "--root", str(mini), "--shadow-derived", "--json"],
        capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["equivalent"] is True
    assert payload["artifacts"] == {
        "backlinks.json": True, "concept-map.md": True, "dependency-report.md": True}
    assert payload["nodes"][BACKLINKS_SEMANTIC_ID]["status"] == "rebuilt"
    assert payload["nodes"][BACKLINKS_SEMANTIC_ID]["output_changed"] is True


def test_cli_json_requires_shadow_flag(tmp_path: Path):
    import subprocess
    import sys

    mini = _curriculum_mini(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "generate.py"),
         "--root", str(mini), "--json"],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2
    assert "--json requires --shadow-derived" in proc.stderr


# ---------------------------------------------------------------------------
# C. Mutation matrix: exact rebuild closures and pruning proofs.
# ---------------------------------------------------------------------------

NOTE_A_META = (
    "---\nid: note-a\ntitle: Note A\nconcepts: [c1, c2]\n"
    "sources: [source-demo-book]\ncontexts: [workspace-demo]\n"
    "supersedes: [note-old]\n---\n"
)


def _warmed_shadow(tmp_path: Path) -> Path:
    """Rich mini with producers staged and one shadow run banked."""
    mini = _curriculum_mini(tmp_path)
    _stage_shadow_producers(mini)
    assert compare_shadow_generation(_rich_repo(mini), STAMP).equivalent
    return mini


def _rerun(mini: Path) -> dict[str, tuple[str, str]]:
    trace: list = []
    comparison = compare_shadow_generation(load_repo(mini), STAMP, trace=trace)
    assert comparison.equivalent, comparison.artifacts
    return _trace_summary(trace)


def _rewrite_note_a(mini: Path, *, concepts="c1, c2", body="See note://note-b for details.\n"):
    (mini / "knowledge" / "notes" / "note-a.md").write_text(
        NOTE_A_META.replace("concepts: [c1, c2]", f"concepts: [{concepts}]")
        + "\n" + body,
        encoding="utf-8")


def _update_workspace_meta(mini: Path, path: str, **fields) -> None:
    target = mini / path
    meta, body = parse_frontmatter(target.read_text(encoding="utf-8"), target)
    meta.update(fields)
    target.write_text(
        "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n" + body.lstrip(),
        encoding="utf-8")


def _append_relation(mini: Path, relation: dict) -> None:
    target = mini / "knowledge" / "concept-relations.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["relations"].append(relation)
    write_yaml(target, data)


def test_note_prose_edit_prunes_backlinks_and_dependents(tmp_path: Path):
    mini = _warmed_shadow(tmp_path)
    _rewrite_note_a(mini, body="See note://note-b for further details and background.\n")
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }


def test_note_concept_edit_propagates_then_prunes(tmp_path: Path):
    mini = _warmed_shadow(tmp_path)
    _rewrite_note_a(mini, concepts="c1, c2, c4")
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        # The report rebuilds (its backlinks output hash moved) but its own
        # output is unchanged: it reads only module_to_workspaces.
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-same"),
    }


def test_relation_edit_rebuilds_all_dependents(tmp_path: Path):
    mini = _warmed_shadow(tmp_path)
    _append_relation(mini, {"from": "c4", "type": "requires", "to": "c3"})
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
    }


def test_unrelated_source_edit_hits_everything(tmp_path: Path):
    from learning_os.genout.derived_generation import generation_input_digests as digests

    mini = _warmed_shadow(tmp_path)
    before = digests(mini)
    target = mini / "sources" / "sources.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    data["sources"][0]["title"] = "Renamed Demo Book"
    write_yaml(target, data)
    assert digests(mini) == before
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("hit", "node-key-equal"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }


def test_workspace_module_edit_rebuilds_backlinks_path(tmp_path: Path):
    mini = _warmed_shadow(tmp_path)
    _update_workspace_meta(
        mini, "work/active/workspace-demo/CONTEXT.md",
        module_ids=["module-demo", "module-lonely"])
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
    }


def test_workspace_concepts_edit_prunes_backlinks_only(tmp_path: Path):
    mini = _warmed_shadow(tmp_path)
    _update_workspace_meta(
        mini, "work/active/workspace-demo/CONTEXT.md",
        concepts=["concept-expected-value", "c1"])
    assert _rerun(mini) == {
        # Backlinks rereads workspaces but ignores their concept lists.
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        # The report prints workspace concept lists: genuinely changed.
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
    }


def test_producer_version_bump_rebuilds_only_its_node(tmp_path: Path):
    from dataclasses import replace

    from learning_os.genout.derived_generation import (
        generation_input_digests,
        legacy_shadow_artifacts,
    )

    mini = _warmed_shadow(tmp_path)
    repo = load_repo(mini)
    registry = dict(generation_registry(repo))
    spec, build = registry[BACKLINKS_SEMANTIC_ID]
    registry[BACKLINKS_SEMANTIC_ID] = (replace(spec, version=2), build)
    from learning_os.derived import evaluate_many

    trace: list = []
    results = evaluate_many(
        mini,
        [BACKLINKS_SEMANTIC_ID, CONCEPT_MAP_BODY_ID, DEPENDENCY_REPORT_BODY_ID],
        registry=registry,
        inputs=generation_input_digests(mini),
        trace=trace)
    assert _trace_summary(trace) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }
    assert set(results) == {
        BACKLINKS_SEMANTIC_ID, CONCEPT_MAP_BODY_ID, DEPENDENCY_REPORT_BODY_ID}
    assert legacy_shadow_artifacts(repo, STAMP)["backlinks.json"].startswith('{"_generated":')


def test_corrupt_backlinks_blob_heals_without_cascade(tmp_path: Path):
    from learning_os.derived import read_state

    mini = _warmed_shadow(tmp_path)
    entry = read_state(mini)[BACKLINKS_SEMANTIC_ID]
    blob = mini / "generated" / "derived-state" / entry.blob
    blob.write_bytes(b"tampered")
    assert _rerun(mini) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "cache-miss"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }


# ---------------------------------------------------------------------------
# D. Real-repo replay: scenarios A-F on a disposable copy.
# ---------------------------------------------------------------------------

REPLAY_NOTE = "knowledge/notes/algorithms/note-algo2-amortized-analysis-exercise-bank.md"


def _copy_live_tree(tmp_path: Path) -> Path:
    import shutil

    copy = tmp_path / "live-copy"
    shutil.copytree(
        REPO_ROOT, copy,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "generated", "__pycache__", ".pytest_cache",
            ".ruff_cache", ".DS_Store"),
    )
    return copy


def _replay_rerun(copy: Path) -> dict[str, tuple[str, str]]:
    trace: list = []
    comparison = compare_shadow_generation(load_repo(copy), STAMP, trace=trace)
    assert comparison.equivalent, comparison.artifacts
    return _trace_summary(trace)


@pytest.mark.full_repo
def test_real_repo_replay_scenarios(tmp_path: Path):
    copy = _copy_live_tree(tmp_path)
    relations_file = copy / "knowledge" / "concept-relations.yaml"
    source_file = sorted((copy / "sources" / "registry").glob("*.yaml"))[0]
    workspace_file = sorted((copy / "work" / "active").glob("*/CONTEXT.md"))[0]
    note_file = copy / REPLAY_NOTE
    pristine = {
        path: path.read_bytes()
        for path in (note_file, relations_file, workspace_file, source_file)
    }

    def restore():
        for path, data in pristine.items():
            path.write_bytes(data)

    # Scenario A: cold then warm on the pristine copy.
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "cache-miss"),
        CONCEPT_MAP_BODY_ID: ("rebuilt", "cache-miss"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "cache-miss"),
    }
    all_hit = {
        BACKLINKS_SEMANTIC_ID: ("hit", "node-key-equal"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }
    assert _replay_rerun(copy) == all_hit

    # Scenario B: note prose append (no new links).
    note_file.write_text(
        note_file.read_text(encoding="utf-8") + "\nReplay probe sentence without links.\n",
        encoding="utf-8")
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }
    restore()
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("hit", "node-key-equal"),
    }

    # Scenario C: note concept metadata gains an entry.
    meta, body = parse_frontmatter(note_file.read_text(encoding="utf-8"), note_file)
    concepts = list(meta.get("concepts", []) or [])
    concepts.append("concept-replay-probe")
    meta["concepts"] = concepts
    note_file.write_text(
        "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n" + body.lstrip(),
        encoding="utf-8")
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-same"),
    }
    restore()
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-same"),
    }

    # Scenario D: a new requires edge between two real concepts.
    repo = load_repo(copy)
    first, second = sorted(repo.concepts)[:2]
    data = yaml.safe_load(relations_file.read_text(encoding="utf-8"))
    data["relations"].append({"from": first, "type": "requires", "to": second})
    write_yaml(relations_file, data)
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
    }
    restore()
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-changed"),
        CONCEPT_MAP_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-changed"),
    }

    # Scenario E: workspace body prose append.
    workspace_file.write_text(
        workspace_file.read_text(encoding="utf-8") + "\nReplay probe sentence.\n",
        encoding="utf-8")
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-same"),
    }
    restore()
    assert _replay_rerun(copy) == {
        BACKLINKS_SEMANTIC_ID: ("rebuilt", "node-key-changed-output-same"),
        CONCEPT_MAP_BODY_ID: ("hit", "node-key-equal"),
        DEPENDENCY_REPORT_BODY_ID: ("rebuilt", "node-key-changed-output-same"),
    }

    # Scenario F: an unrelated source title change.
    data = yaml.safe_load(source_file.read_text(encoding="utf-8"))
    data["sources"][0]["title"] = data["sources"][0]["title"] + " (replay probe)"
    write_yaml(source_file, data)
    assert _replay_rerun(copy) == all_hit
    restore()
    assert _replay_rerun(copy) == all_hit


@pytest.mark.full_repo
def test_splits_are_byte_identical_on_real_repo(real_repo):
    repo = real_repo
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
