"""The bounded Python split is exercised only in synthetic/disposable roots."""

from __future__ import annotations

import copy

import pytest
import yaml
from repo_builders import add_curriculum, write_yaml

from learning_os.app import python_sessions_migration as migration
from learning_os.derive.validation import validate
from learning_os.domain.failures import TransactionFailure, WriteRefused
from learning_os.store.loader import load_repo
from learning_os.store.warning_baseline import signatures_from_issues, write_baseline


@pytest.fixture
def python_plan(mini_repo):
    root = mini_repo
    add_curriculum(root)
    module = {"id": migration.MODULE, "type": "module", "kind": "skill",
              "area_id": "program-bachelors", "title": "Synthetic Python",
              "status": "active", "source_map": "source-map.yaml",
              "unit_order": [migration.UNIT]}
    stages, nodes, routes = [], [], []
    for number, topic in enumerate([*migration.TOPICS, *[f"optional-{i}" for i in range(10)]], 1):
        sid = f"stage-python-{topic}"
        required = number <= 16
        node_id = f"knowledge-python-{topic}" if required else "knowledge-python-optional"
        if required:
            nodes.append({"id": node_id, "title": topic, "summary": f"Read about {topic}."})
        note = f"{migration.UNIT_DIR}/stages/{sid}/notes.md"
        (root / note).parent.mkdir(parents=True)
        (root / note).write_text(f"Learner notes for {sid}.\n")
        resource = {"id": f"resource-python-{topic}", "kind": "read",
                    "label": topic, "source_id": "source-demo-book", "locator": f"Chapter 1, PDF pp. 1-2: {topic}",
                    "scope_triage": "required-now" if required else "deferred"}
        if required:
            resource["route_id"] = f"route-python-{topic}"
            routes.append({"id": resource["route_id"], "unit_id": migration.UNIT,
                           "title": topic, "format": "book", "angle": f"Explains {topic}.",
                           "angle_detail": "Read the named section and its example. This fixture checks ownership rather than source content.",
                           "covers": [node_id], "depth": "orientation", "scope": "current",
                           "locator": resource["locator"]})
        stages.append({"id": sid, "number": number, "title": topic, "status": "pending",
                       "objective": f"Read about {topic}.", "done_when": ["Read the material."],
                       "exam_critical": False, "concepts": [],
                       "scope_triage": "required-now" if required else "deferred",
                       "resources": [resource], "working_note": note, "attachments": [],
                       "source_feedback": [], "knowledge_node_id": node_id})
    nodes.append({"id": "knowledge-python-optional", "title": "Optional history",
                  "summary": "Former optional material, preserved."})
    unit_note = f"{migration.UNIT_DIR}/notes.md"
    (root / unit_note).write_text("Original unit notes stay on their original owner.\n")
    unit = {"id": migration.UNIT, "type": "unit", "module_id": migration.MODULE,
            "kind": "topic", "title": "All Python", "order": 1, "scope": "Synthetic path.",
            "status": "ready", "scope_sources": [{"source_id": "source-demo-book",
                                                       "authority": "reference"}],
            "source_selections": [], "artifacts": {}, "workspace_ids": [],
            "working_note": unit_note, "current_study_map": "study-map-job-python-fluency",
            "knowledge_map": {"summary": "Synthetic topics.", "nodes": nodes}}
    study = {"id": unit["current_study_map"], "type": "study-map", "plan_template_version": 1,
             "unit_id": migration.UNIT, "status": "ready", "current_stage": stages[0]["id"],
             "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                             "provenance": "operator"},
             "detours": [], "shelving": {"state": "none"}, "stages": stages}
    source_map = {"type": "module-source-map", "module_id": migration.MODULE,
                  "sources": [{"source_id": "source-demo-book", "role": "spine",
                               "why": "Synthetic source.", "priority": 0,
                               "unit_routes": [*routes, migration.UNIT]}]}
    for relative, value in ((migration.MODULE_PATH, module), (migration.UNIT_PATH, unit),
                            (migration.MAP_PATH, study), (migration.SOURCE_MAP_PATH, source_map)):
        write_yaml(root / relative, value)
    issues = validate(load_repo(root))
    signatures, errors = signatures_from_issues(issues)
    assert not errors, errors
    write_baseline(root, signatures, "Synthetic Python migration content debt.")
    return root


def commit(root, report=None):
    report = report or migration.prepare(root)
    return migration.apply(root, report, reviewed_sha256=migration.plan_sha256(report))


def original_files(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()
            and not path.relative_to(root).as_posix().startswith("generated/")}


def test_dry_run_and_split_preserve_material_and_note_bytes(python_plan):
    root = python_plan
    before = original_files(root)
    original = yaml.safe_load(before[migration.MAP_PATH])
    report = migration.prepare(root)
    assert original_files(root) == before
    assert len(report["sessions"]) == 16 and len(report["optional_stage_ids"]) == 10
    result = commit(root, report)
    assert not result["replayed"]
    repo = load_repo(root)
    assert [repo.units[row["unit_id"]].data["order"] for row in report["sessions"]] == list(range(1, 17))
    for prior, session in zip(original["stages"][:16], report["sessions"], strict=True):
        current = next(sm.data for sm in repo.study_maps.values() if sm.unit_id == session["unit_id"])
        stage = current["stages"][0]
        expected = dict(prior, number=1, working_note=session["note_after"])
        assert stage == expected
        assert (root / session["note_after"]).read_bytes() == before[session["note_before"]]
        assert not (root / session["note_before"]).exists()
    retained = yaml.safe_load((root / migration.MAP_PATH).read_text())
    assert retained["status"] == "paused"
    assert [row["id"] for row in retained["stages"]] == report["optional_stage_ids"]
    for prior, stage in zip(original["stages"][16:], retained["stages"], strict=True):
        assert stage == dict(prior, number=stage["number"])
        assert (root / stage["working_note"]).read_bytes() == before[stage["working_note"]]
    assert (root / f"{migration.UNIT_DIR}/notes.md").read_bytes() == before[f"{migration.UNIT_DIR}/notes.md"]
    for relative in set(report["deletes"]) | ({migration.MODULE_PATH, migration.UNIT_PATH,
                                               migration.MAP_PATH, migration.SOURCE_MAP_PATH}):
        assert (root / f"{migration.BASE}/before/{relative}").read_bytes() == before[relative]
    assert migration._validation_errors(root) == []


def test_resume_rehomes_the_same_stage_without_new_progress(python_plan):
    root = python_plan
    resume = {"type": "resume-pointer", "module_id": migration.MODULE,
              "unit_id": migration.UNIT, "study_map_id": "study-map-job-python-fluency",
              "stage_id": "stage-python-functions-scope", "updated": "2026-11-04"}
    write_yaml(root / migration.RESUME_PATH, resume)
    commit(root)
    current = yaml.safe_load((root / migration.RESUME_PATH).read_text())
    assert current == dict(resume, unit_id="unit-job-python-functions-scope",
                           study_map_id="study-map-job-python-functions-scope")


def test_shared_authored_reading_becomes_two_local_routes(python_plan):
    root = python_plan
    source_map = yaml.safe_load((root / migration.SOURCE_MAP_PATH).read_text())
    route = next(row for row in source_map["sources"][0]["unit_routes"]
                 if isinstance(row, dict) and row["id"] == "route-python-modules-imports")
    route.update(id=migration.SHARED_ROUTE,
                 covers=["knowledge-python-modules-imports", "knowledge-python-testing"])
    study = yaml.safe_load((root / migration.MAP_PATH).read_text())
    imports = next(row for row in study["stages"] if row["id"] == "stage-python-modules-imports")
    imports["resources"][0]["route_id"] = migration.SHARED_ROUTE
    tests = next(row for row in study["stages"] if row["id"] == "stage-python-testing")
    shared_resource = dict(imports["resources"][0], id="resource-python-shared-testing")
    tests["resources"].append(shared_resource)
    write_yaml(root / migration.SOURCE_MAP_PATH, source_map)
    write_yaml(root / migration.MAP_PATH, study)
    commit(root)
    final = yaml.safe_load((root / migration.SOURCE_MAP_PATH).read_text())
    routes = {row["id"]: row for row in final["sources"][0]["unit_routes"] if isinstance(row, dict)}
    assert routes[migration.SHARED_ROUTE]["covers"] == ["knowledge-python-modules-imports"]
    assert routes[migration.SHARED_TEST_ROUTE] == dict(
        routes[migration.SHARED_ROUTE], id=migration.SHARED_TEST_ROUTE,
        unit_id="unit-job-python-testing", covers=["knowledge-python-testing"])
    testing_map = yaml.safe_load((root / migration.MODULE_DIR / "units/unit-job-python-testing/study-map.yaml").read_text())
    assert testing_map["stages"][0]["resources"][-1] == dict(
        shared_resource, route_id=migration.SHARED_TEST_ROUTE)


def test_stale_note_and_forged_report_refuse_before_writes(python_plan):
    root = python_plan
    report = migration.prepare(root)
    forged = copy.deepcopy(report)
    forged["writes"]["knowledge/notes/unauthorized.md"] = "escaped"
    with pytest.raises(WriteRefused, match="source, snapshot or revisions changed"):
        commit(root, forged)
    assert not (root / "knowledge/notes/unauthorized.md").exists()
    note = root / report["sessions"][0]["note_before"]
    note.write_text("New learner note after review.\n")
    with pytest.raises(WriteRefused, match="source, snapshot or revisions changed"):
        commit(root, report)
    assert not (root / report["sessions"][0]["note_after"]).exists()


def test_generation_and_existing_destination_refuse(python_plan):
    root = python_plan
    destination = root / f"{migration.MODULE_DIR}/units/unit-job-python-everyday-data"
    destination.mkdir()
    with pytest.raises(WriteRefused, match="destination already exists"):
        migration.prepare(root)
    contract_path = root / "system/contracts/data-contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["contract_version"] = 64
    write_yaml(contract_path, contract)
    with pytest.raises(WriteRefused, match="retired"):
        migration.prepare(root)


def test_symlinked_note_and_escaping_note_refuse_without_mutation(python_plan, tmp_path):
    root = python_plan
    study = yaml.safe_load((root / migration.MAP_PATH).read_text())
    note = root / study["stages"][0]["working_note"]
    external = tmp_path / "external-note.md"
    external.write_text("External bytes stay untouched.\n")
    note.unlink()
    note.symlink_to(external)
    with pytest.raises(WriteRefused, match="refuses symlink"):
        migration.prepare(root)
    assert external.read_text() == "External bytes stay untouched.\n"
    assert not (root / migration.MARKER).exists()
    note.unlink()
    note.write_text("Restored original note.\n")
    study["stages"][0]["working_note"] = "../external-note.md"
    write_yaml(root / migration.MAP_PATH, study)
    with pytest.raises(WriteRefused, match="outside the source unit"):
        migration.prepare(root)


def test_replay_does_not_overwrite_later_notes_and_requires_evidence(python_plan):
    root = python_plan
    report = migration.prepare(root)
    first = commit(root, report)
    note = root / report["sessions"][0]["note_after"]
    note.write_text("Later learning stays untouched.\n")
    replay = commit(root, report)
    assert replay["replayed"] and replay["transaction_id"] == first["transaction_id"]
    assert note.read_text() == "Later learning stays untouched.\n"
    (root / f"{migration.BASE}/evidence.json").write_text("{}")
    with pytest.raises(WriteRefused, match="evidence differs"):
        commit(root, report)


def test_validation_failure_rolls_back_the_entire_split(python_plan, monkeypatch):
    root = python_plan
    report = migration.prepare(root)
    before = original_files(root)
    real_validation = migration._validation_errors

    def refuse_post_state(candidate):
        if candidate == root and yaml.safe_load((root / migration.MAP_PATH).read_text())["status"] == "paused":
            return ["forced post-state validation failure"]
        return real_validation(candidate)

    monkeypatch.setattr(migration, "_validation_errors", refuse_post_state)
    with pytest.raises(TransactionFailure):
        commit(root, report)
    for relative, content in before.items():
        assert (root / relative).read_bytes() == content, relative
    assert not (root / migration.MARKER).exists()
    assert not (root / report["sessions"][0]["note_after"]).exists()
