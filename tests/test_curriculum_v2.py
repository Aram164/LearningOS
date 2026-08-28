"""Module-first curriculum contract, migration, and action-specific gateway tests."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from gateway_helpers import approved_v2_cli, file_sha256, request_artifact_id

from learning_os.contracts.manifest_contract import declared_version
from learning_os.fingerprint import source_fingerprint
from learning_os.genout import generate_all, write_outputs
from learning_os.loader import load_repo, parse_frontmatter
from learning_os.routes import deterministic_route_id
from learning_os.rules import validate

ROOT = Path(__file__).resolve().parent.parent
LOS = ROOT / "tools" / "los.py"
MIGRATE = ROOT / "tools" / "migrations" / "curriculum_v2.py"


def run_los(root: Path, *args: str):
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), *args],
                          capture_output=True, text=True, timeout=120)


def gateway_result(proc) -> dict:
    """Return the capability handler result from a GatewayResultV2 response."""
    return json.loads(proc.stdout)["result"]


def gateway_error(proc) -> str:
    """Return the stable human-readable detail from a typed gateway refusal."""
    return str(json.loads(proc.stdout).get("error", {}).get("message", ""))


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def add_curriculum(root: Path) -> None:
    write_yaml(root / "curriculum/programs/program-bachelors.yaml", {
        "id": "program-bachelors", "type": "program", "title": "Bachelor’s",
        "kind": "academic", "status": "active", "default": True,
        "semester_bound": True,
        "semesters": [{"id": "semester-sose-2026", "title": "SoSe 2026",
                       "status": "current", "order": 1}],
    })
    module_dir = root / "curriculum/modules/module-demo"
    write_yaml(module_dir / "module.yaml", {
        "id": "module-demo", "type": "module", "kind": "academic",
        "area_id": "program-bachelors", "institution": "HU Berlin",
        "title": "Demo Module", "semester": "sose-2026", "status": "enrolled",
        "unit_order": ["unit-demo-l01"], "source_map": "source-map.yaml",
        "examination": {
            "type": "klausur",
            "sittings": [
                {"termin": 3, "date": "2000-01-01", "label": "Elapsed unregistered sitting"},
                {"termin": 2, "date": "2026-10-09",
                 "time": "13:00-16:00", "label": "2. Termin"},
            ],
            "registration_windows": [{"opens": "2026-08-31", "closes": "2026-09-10",
                                      "label": "2.-PZ Anmeldung",
                                      "action": "Register via AGNES.", "termins": [2]}],
        },
        "attempts": [
            {"termin": 1, "date": "2026-07-27", "result": "withdrawn"},
            {"termin": 2, "date": "2026-10-09", "result": "registered"},
        ],
    })
    write_yaml(module_dir / "source-map.yaml", {
        "type": "module-source-map", "module_id": "module-demo",
        "sources": [{"source_id": "source-demo-book", "role": "spine",
                     "why": "Scoped demo reading.", "priority": 0,
                     "unit_routes": ["unit-demo-l01"]}],
    })
    unit_dir = module_dir / "units/unit-demo-l01"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l01", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Expected value", "order": 1,
        "scope": "The lecture as taught.", "status": "active",
        "scope_sources": [{"source_id": "source-demo-book", "authority": "slides",
                           "locator": "Lecture 1"}],
        "source_selections": [{"source_id": "source-demo-book", "locator": "§1 Erwartungswert",
                               "purpose": "Current derivation"}],
        "current_study_map": "study-map-demo-l01",
        "artifacts": {"ultimate_reference": "note-demo"},
        "workspace_ids": ["workspace-demo"],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    write_yaml(unit_dir / "study-map.yaml", {
        "id": "study-map-demo-l01", "type": "study-map", "unit_id": "unit-demo-l01",
        "status": "active", "current_stage": "stage-demo",
        "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                        "provenance": "operator"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": "stage-demo", "title": "Derive expected value", "status": "active",
            "objective": "Derive and explain expected value.",
            "done_when": ["Explain the derivation."], "scope_triage": "required-now",
            "resources": [
                {"id": "resource-demo-book-ch01", "kind": "read",
                 "label": "Demo Book §1", "source_id": "source-demo-book",
                 "locator": "§1"},
                {"id": "resource-demo-book-appendix", "kind": "read",
                 "label": "Demo Book Appendix", "source_id": "source-demo-book",
                 "locator": "Appendix A"},
                # no id: the pre-v3 shape must keep working
                {"kind": "watch", "label": "Demo companion video",
                 "source_id": "source-demo-book"},
            ],
            "working_note": note_rel, "attachments": [], "source_feedback": [],
        }],
    })
    write_yaml(root / "curriculum/resume.yaml", {
        "type": "resume-pointer", "module_id": "module-demo", "unit_id": "unit-demo-l01",
        "study_map_id": "study-map-demo-l01", "stage_id": "stage-demo",
        "updated": "2026-08-03",
    })
    ws_path = root / "work/active/workspace-demo/CONTEXT.md"
    meta, body = parse_frontmatter(ws_path.read_text(encoding="utf-8"), ws_path)
    meta.update({"program_ids": ["program-bachelors"], "module_ids": ["module-demo"],
                 "unit_ids": ["unit-demo-l01"]})
    ws_path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() +
                       "\n---\n\n" + body.lstrip(), encoding="utf-8")


def _set_workspace_status(root: Path, status: str, workspace: str = "workspace-demo") -> None:
    ws_path = root / f"work/active/{workspace}/CONTEXT.md"
    meta, body = parse_frontmatter(ws_path.read_text(encoding="utf-8"), ws_path)
    meta["status"] = status
    ws_path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() +
                       "\n---\n\n" + body.lstrip(), encoding="utf-8")


def _add_material_overview(root: Path, *, covers=None, builds_on=None) -> None:
    """Give the synthetic lecture one v5 knowledge map and rich source route."""
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcome values to their probabilities.",
        "nodes": [
            {
                "id": "knowledge-demo-outcomes",
                "title": "Outcome values",
                "summary": "A random variable assigns a number to each outcome.",
            },
            {
                "id": "knowledge-demo-expectation",
                "title": "Probability-weighted average",
                "summary": "Expectation weights every value by its probability.",
                "builds_on": builds_on or ["knowledge-demo-outcomes"],
            },
        ],
    }
    write_yaml(unit_path, unit)

    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "unit_id": "unit-demo-l01",
        "title": "Demo book — expected-value derivation",
        "format": "book",
        "angle": "Derives the weighted sum and works a discrete example.",
        "covers": covers or ["knowledge-demo-outcomes", "knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": "current",
        "locator": "lecture-01.pdf",
    }]
    write_yaml(source_map_path, source_map)

    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/book.pdf"
    write_yaml(registry_path, registry)


def test_rich_material_route_projects_semantics_and_resolved_local_file(mini_repo):
    from learning_os.genout import build_manifest

    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    local = mini_repo.parent / "materials/source-demo-book/lecture-01.pdf"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text("synthetic lecture", encoding="utf-8")

    repo = load_repo(mini_repo)
    assert [issue for issue in validate(repo) if issue.severity == "E"] == []
    manifest = build_manifest(repo, "2026-08-12T12:00:00+00:00")
    projected_map = next(row for row in manifest["module_source_maps"]
                         if row["module_id"] == "module-demo")
    route = projected_map["sources"][0]["unit_routes"][0]
    assert route["angle"] == "Derives the weighted sum and works a discrete example."
    assert route["covers"] == ["knowledge-demo-outcomes", "knowledge-demo-expectation"]
    assert route["material_uri"] == "material://source-demo-book/lecture-01.pdf"
    assert route["material_path"] == "materials/source-demo-book/lecture-01.pdf"
    assert route["material_exists"] is True
    projected_unit = next(row for row in manifest["units"] if row["id"] == "unit-demo-l01")
    assert projected_unit["knowledge_map"]["nodes"][1]["builds_on"] == ["knowledge-demo-outcomes"]


def test_material_route_cannot_claim_an_unknown_knowledge_node(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo, covers=["knowledge-demo-missing"])
    errors = [issue for issue in validate(load_repo(mini_repo)) if issue.severity == "E"]
    assert any(issue.code == "REF-KNOWLEDGE" for issue in errors)


def test_knowledge_map_dependency_must_resolve_inside_its_lecture(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo, builds_on=["knowledge-demo-missing"])
    errors = [issue for issue in validate(load_repo(mini_repo)) if issue.severity == "E"]
    assert any(issue.code == "KNOWLEDGE-EDGE" for issue in errors)


def test_learner_can_choose_and_remove_one_rich_material_option(mini_repo):
    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"] = []
    write_yaml(unit_path, unit)

    chosen = approved_v2_cli(
        mini_repo,
        "unit-source-selection",
        "unit-demo-l01",
        "source-demo-book",
        "lecture-01.pdf",
        "select",
        "--purpose",
        "Use the worked derivation.",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-source-selection-choose",
    )
    assert chosen.returncode == 0, chosen.stderr
    selection = load_repo(mini_repo).units["unit-demo-l01"].data["source_selections"]
    assert selection == [{
        "route_id": deterministic_route_id(
            "module-demo",
            "source-demo-book",
            load_repo(mini_repo).module_source_maps["module-demo"]["sources"][0][
                "unit_routes"
            ][0],
        ),
        "source_id": "source-demo-book",
        "locator": "lecture-01.pdf",
        "purpose": "Use the worked derivation.",
    }]

    removed = approved_v2_cli(
        mini_repo,
        "unit-source-selection",
        "unit-demo-l01",
        "source-demo-book",
        "lecture-01.pdf",
        "remove",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-source-selection-remove",
    )
    assert removed.returncode == 0, removed.stderr
    assert load_repo(mini_repo).units["unit-demo-l01"].data["source_selections"] == []

    invented = run_los(
        mini_repo,
        "unit-source-selection",
        "unit-demo-l01",
        "source-demo-book",
        "not-on-the-menu.pdf",
        "select",
    )
    assert invented.returncode == 2
    assert "must match one rich material route" in invented.stderr


def _lifecycle_errors(root: Path) -> set[str]:
    return {issue.code for issue in validate(load_repo(root))
            if issue.severity == "E" and issue.code.startswith("LIFECYCLE-")}


# Algo 2 was, on 2026-08-08, a blocked workspace ("no study, next action none")
# over a ready unit, a ready study map and a required-now stage. Every file was
# individually valid; nothing compared them, so the repository asserted "do
# nothing" and "do this now" at the same time (engineering audit, finding 3).

def test_a_blocked_sole_workspace_cannot_leave_its_unit_ready(mini_repo):
    add_curriculum(mini_repo)
    _set_workspace_status(mini_repo, "blocked")
    assert _lifecycle_errors(mini_repo) == {"LIFECYCLE-BLOCKED-UNIT", "LIFECYCLE-BLOCKED-MAP"}


def test_pausing_the_unit_and_map_with_the_workspace_is_coherent(mini_repo):
    add_curriculum(mini_repo)
    _set_workspace_status(mini_repo, "blocked")
    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    for name in ("unit.yaml", "study-map.yaml"):
        data = yaml.safe_load((unit_dir / name).read_text(encoding="utf-8"))
        data["status"] = "paused"
        write_yaml(unit_dir / name, data)
    assert _lifecycle_errors(mini_repo) == set()


def test_one_blocked_workspace_among_several_is_not_a_sole_context(mini_repo):
    """Scope check: only the *last* execution context pauses the work."""
    import shutil

    add_curriculum(mini_repo)
    _set_workspace_status(mini_repo, "blocked")
    second = mini_repo / "work/active/workspace-demo-two"
    shutil.copytree(mini_repo / "work/active/workspace-demo", second)
    meta, body = parse_frontmatter((second / "CONTEXT.md").read_text(encoding="utf-8"),
                                   second / "CONTEXT.md")
    meta.update({"id": "workspace-demo-two", "status": "active"})
    (second / "CONTEXT.md").write_text(
        "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n" + body.lstrip(),
        encoding="utf-8")
    assert _lifecycle_errors(mini_repo) == set()


def test_an_unblocked_workspace_leaves_a_ready_unit_alone(mini_repo):
    """The rule must not fire on the ordinary case it was written beside."""
    add_curriculum(mini_repo)
    assert _lifecycle_errors(mini_repo) == set()


def test_manifest_v2_exposes_full_curriculum_and_reverse_indexes(mini_repo):
    add_curriculum(mini_repo)
    repo = load_repo(mini_repo)
    assert not [issue for issue in validate(repo) if issue.severity == "E"]
    manifest = json.loads(generate_all(repo, "T1")["manifest.json"])
    # Read from the producer-owned declaration, never hardcoded: a literal
    # here has to be edited on every bump, which makes it a chore rather than
    # a check. What is worth asserting is that the manifest announces the
    # version the contract declares — the mismatch consumers fail closed on.
    assert manifest["_generated"]["contract_version"] == declared_version(mini_repo)
    assert manifest["programs"][0]["id"] == "program-bachelors"
    assert manifest["modules"][0]["id"] == "module-demo"
    assert manifest["units"][0]["source_selections"][0]["locator"] == "§1 Erwartungswert"
    assert manifest["study_maps"][0]["stages"][0]["notes_text"] == ""
    assert manifest["indexes"]["module_to_units"] == {"module-demo": ["unit-demo-l01"]}
    assert manifest["indexes"]["source_to_units"] == {"source-demo-book": ["unit-demo-l01"]}
    assert manifest["resume_pointer"]["stage_id"] == "stage-demo"
    assert manifest["progress"]["module-demo"]["stages_total"] == 1
    assert manifest["academic_deadlines"] == [
        {"kind": "registration-window", "start_date": "2026-08-31",
         "end_date": "2026-09-10", "label": "2.-PZ Anmeldung",
         "modules": [{"module_id": "module-demo", "title": "Demo Module",
                      "action": "Register via AGNES.", "termins": [2]}]},
        {"kind": "exam", "start_date": "2026-10-09", "end_date": "2026-10-09",
         "module_id": "module-demo", "title": "Demo Module", "termin": 2,
         "label": "2. Termin", "time": "13:00-16:00", "notes": None,
         "registration_state": "registered"},
    ]
    assert "Elapsed unregistered sitting" not in json.dumps(manifest["academic_deadlines"])


def test_non_academic_module_needs_no_institution_or_semester(mini_repo):
    add_curriculum(mini_repo)
    write_yaml(mini_repo / "curriculum/programs/program-skills.yaml", {
        "id": "program-skills", "type": "program", "title": "Skills", "kind": "skills",
        "status": "active", "default": False, "semester_bound": False, "semesters": [],
    })
    module = mini_repo / "curriculum/modules/module-skill-python"
    write_yaml(module / "module.yaml", {
        "id": "module-skill-python", "type": "module", "kind": "skill",
        "area_id": "program-skills", "title": "Python", "status": "active",
        "unit_order": ["unit-python-scope"], "source_map": "source-map.yaml",
    })
    write_yaml(module / "source-map.yaml", {"type": "module-source-map",
                                             "module_id": "module-skill-python", "sources": []})
    write_yaml(module / "units/unit-python-scope/unit.yaml", {
        "id": "unit-python-scope", "type": "unit", "module_id": "module-skill-python",
        "kind": "topic", "title": "Scope", "order": 1, "scope": "Python scope repair.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })
    issues = validate(load_repo(mini_repo))
    assert not [issue for issue in issues if issue.severity == "E"]


def test_stage_feedback_detour_and_progress_are_unit_scoped(mini_repo):
    add_curriculum(mini_repo)
    before = load_repo(mini_repo).sources["source-demo-book"]["evaluations"]
    feedback = approved_v2_cli(
        mini_repo, "source-feedback", "unit-demo-l01", "stage-demo",
        "source-demo-book", "too-advanced", "--note", "Return after the lecture.",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-feedback",
    )
    assert feedback.returncode == 0, feedback.stderr
    repo = load_repo(mini_repo)
    stage = repo.study_maps["study-map-demo-l01"].data["stages"][0]
    assert stage["source_feedback"][0]["feedback"] == "too-advanced"
    assert repo.sources["source-demo-book"]["evaluations"] == before

    detour = approved_v2_cli(
        mini_repo, "detour-create", "unit-demo-l01", "stage-demo",
        "--title", "Review finite sums", "--classification", "required-now",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-detour-create",
    )
    assert detour.returncode == 0, detour.stderr
    did = gateway_result(detour)["detour"]["id"]
    assert load_repo(mini_repo).study_maps["study-map-demo-l01"].data["status"] == "paused"
    resolved = approved_v2_cli(
        mini_repo, "detour-resolve", "unit-demo-l01", did,
        "--resolution", "Reviewed the needed identity.",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-detour-resolve",
    )
    assert resolved.returncode == 0, resolved.stderr
    completed = approved_v2_cli(
        mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-stage-complete",
    )
    assert completed.returncode == 0, completed.stderr
    repo = load_repo(mini_repo)
    assert repo.study_maps["study-map-demo-l01"].data["status"] == "ready-to-shelve"
    assert repo.units["unit-demo-l01"].data["status"] == "ready-to-shelve"


def test_stage_note_snapshot_guard_and_german_search(mini_repo):
    add_curriculum(mini_repo)
    write_outputs(load_repo(mini_repo), generate_all(load_repo(mini_repo), "T1"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]
    saved = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--replace",
        "--text", "Meine Herleitung.", artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-stage-note-save", expected_snapshot=snapshot,
    )
    assert saved.returncode == 0, saved.stderr
    stale = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--replace",
        "--text", "Would overwrite.", artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-stage-note-stale", expected_snapshot=snapshot,
    )
    assert stale.returncode == 3
    search = run_los(mini_repo, "search", "Erwartungswert")
    assert search.returncode == 0
    assert "concept-expected-value" in search.stdout


def test_stage_attachment_copies_the_exact_approved_bytes(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    source = tmp_path / "stage-handwriting.png"
    source.write_bytes(b"approved-stage-image")
    saved = approved_v2_cli(
        mini_repo, "stage-attach", "unit-demo-l01", "stage-demo",
        "--file", str(source),
        "--file-sha256", file_sha256(source),
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-stage-attachment-content-bound",
    )
    assert saved.returncode == 0, saved.stderr
    copied = mini_repo / gateway_result(saved)["attachment"]
    assert copied.read_bytes() == b"approved-stage-image"


def test_unit_map_import_creates_one_current_map(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    unit_dir = module_path.parent / "units/unit-demo-l02"
    write_yaml(unit_dir / "unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2, "scope": "Lecture 2.",
        "status": "needs-map", "scope_sources": [], "source_selections": [],
        "artifacts": {}, "workspace_ids": [],
    })
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md"
    incoming = tmp_path / "map.yaml"
    write_yaml(incoming, {
        "id": "study-map-demo-l02", "type": "study-map", "unit_id": "unit-demo-l02",
        "plan_template_version": 1,
        "status": "ready", "current_stage": "stage-variance",
        "source_plan": {"path": "proposal.json", "provenance": "ai-proposed"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{"id": "stage-variance", "number": 1,
                    "title": "Variance", "status": "pending",
                    "objective": "Derive variance.", "done_when": ["Derive it."],
                    "exam_critical": False, "concepts": [],
                    "scope_triage": "required-now", "resources": [],
                    "working_note": note_rel, "attachments": [], "source_feedback": []}],
    })
    proc = approved_v2_cli(
        mini_repo, "unit-map-import", "unit-demo-l02", "--file", str(incoming),
        "--file-sha256", file_sha256(incoming),
        artifact_ids=["unit-demo-l02", "study-map-demo-l02"],
        idempotency_key="curriculum-unit-map-import",
    )
    assert proc.returncode == 0, proc.stderr
    repo = load_repo(mini_repo)
    assert repo.units["unit-demo-l02"].data["current_study_map"] == "study-map-demo-l02"
    assert (mini_repo / note_rel).is_file()


def test_module_plan_import_adds_units_sources_and_workspace_join(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    note_rel = "curriculum/modules/module-demo/units/unit-demo-l02/stages/stage-variance/notes.md"
    audit_rel = "work/active/workspace-demo/outputs/demo-coverage-audit.md"
    audit = mini_repo / audit_rel
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Complete demo coverage audit\n\n## Local inventory\n\nDone.\n\n"
        "## Linked inventory\n\nDone.\n\n## Completeness sign-off\n\nDone.\n",
        encoding="utf-8",
    )
    package = tmp_path / "module-plan.yaml"
    shared_empty = []
    package_data = {
        "module_id": "module-demo",
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": audit_rel,
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "module_patch": {"title": "Standardized Demo Module",
                         "unit_order": ["unit-demo-l02", "unit-demo-l01"]},
        "source_patches": [{"id": "source-demo-book", "title": "Demo Book, verified"}],
        "source_map": {
            "type": "module-source-map", "module_id": "module-demo",
            "sources": [{"source_id": "source-demo-book", "role": "course-material",
                         "why": "Scope and drills.", "priority": 0,
                         "unit_routes": ["unit-demo-l01", "unit-demo-l02"]}],
        },
        "units": [{
            "unit": {"id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
                     "kind": "lecture", "title": "Variance", "order": 0,
                     "scope": "Lecture 2 as taught.", "status": "ready",
                     "scope_sources": [{"source_id": "source-demo-book", "authority": "slides"}],
                     "source_selections": [], "current_study_map": "study-map-demo-l02",
                     "artifacts": {}, "workspace_ids": ["workspace-demo"]},
            "study_map": {"id": "study-map-demo-l02", "type": "study-map",
                          "plan_template_version": 1,
                          "unit_id": "unit-demo-l02", "status": "ready",
                          "current_stage": "stage-variance",
                          "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                                          "provenance": "operator"},
                          "detours": [], "shelving": {"state": "none"},
                          "stages": [{"id": "stage-variance", "number": 1,
                                      "title": "Variance",
                                      "status": "pending", "objective": "Derive variance.",
                                      "done_when": ["Derive it."],
                                      "exam_critical": False, "concepts": [],
                                      "scope_triage": "required-now", "resources": [],
                                      "working_note": note_rel,
                                      "attachments": shared_empty,
                                      "source_feedback": shared_empty}]},
        }],
        "workspace_updates": [{"id": "workspace-demo",
                               "sources": ["source-demo-book"],
                               "unit_ids": ["unit-demo-l02", "unit-demo-l01"],
                               "sections": {"Next Action": "Start the standardized variance unit."}}],
    }
    write_yaml(package, package_data)
    assert "&id" in package.read_text(encoding="utf-8")

    broken = yaml.safe_load(package.read_text(encoding="utf-8"))
    broken["source_map"]["sources"][0]["unit_routes"] = ["unit-demo-l01"]
    broken_package = tmp_path / "broken-module-plan.yaml"
    write_yaml(broken_package, broken)
    rejected = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                       str(broken_package), "--check")
    assert rejected.returncode == 1
    assert "source-map unit_routes omit the unit" in rejected.stderr
    assert load_repo(mini_repo).modules["module-demo"]["title"] == "Demo Module"

    checked = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                      str(package), "--check")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["canonical_files_written"] == 0
    assert "unit-demo-l02" not in load_repo(mini_repo).units

    outside_audit = mini_repo / "outside-snapshot-coverage-audit.md"
    outside_audit.write_text(
        "## Local inventory\n\n## Linked inventory\n\n## Completeness sign-off\n",
        encoding="utf-8",
    )
    outside_package_data = copy.deepcopy(package_data)
    outside_package_data["plan_contract"]["coverage_audit"] = outside_audit.name
    outside_package = tmp_path / "outside-audit-module-plan.yaml"
    write_yaml(outside_package, outside_package_data)
    outside_refused = run_los(
        mini_repo, "module-plan-import", "module-demo", "--file",
        str(outside_package), "--check",
    )
    assert outside_refused.returncode == 2
    assert "snapshot-bound work/active" in outside_refused.stderr
    outside_audit.unlink()

    unguarded = run_los(mini_repo, "module-plan-import", "module-demo", "--file",
                        str(package))
    assert unguarded.returncode == 2
    snapshot = f"sha256:{source_fingerprint(load_repo(mini_repo))}"
    proc = approved_v2_cli(
        mini_repo, "module-plan-import", "module-demo", "--file", str(package),
        "--file-sha256", file_sha256(package),
        artifact_ids=["module-demo", "unit-demo-l02"],
        idempotency_key="curriculum-module-plan-import",
        expected_snapshot=snapshot,
    )
    assert proc.returncode == 0, proc.stderr
    repo = load_repo(mini_repo)
    assert repo.modules["module-demo"]["title"] == "Standardized Demo Module"
    assert repo.sources["source-demo-book"]["title"] == "Demo Book, verified"
    assert repo.modules["module-demo"]["unit_order"][0] == "unit-demo-l02"
    assert repo.workspaces["workspace-demo"].meta["unit_ids"][0] == "unit-demo-l02"
    assert "standardized variance" in repo.workspaces["workspace-demo"].section("Next Action")
    assert (mini_repo / note_rel).is_file()
    rendered_map = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02/study-map.yaml").read_text(encoding="utf-8")
    assert "&id" not in rendered_map and "*id" not in rendered_map

    # Expanding an existing plan may add stages, but it may not silently move
    # the stages already in use. A deliberate reorder needs a scoped reason in
    # the review contract, so the package cannot acquire one accidentally.
    map_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02/study-map.yaml"
    current_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    review_note = (
        "curriculum/modules/module-demo/units/unit-demo-l02/"
        "stages/stage-variance-review/notes.md"
    )
    current_map["stages"].append({
        "id": "stage-variance-review", "number": 2, "title": "Review variance",
        "status": "pending", "objective": "Review the derivation.",
        "done_when": ["Reproduce it cold."], "exam_critical": False,
        "concepts": [], "scope_triage": "required-now",
        "resources": [], "working_note": review_note, "attachments": [],
        "source_feedback": [],
    })
    write_yaml(map_path, current_map)
    (mini_repo / review_note).parent.mkdir(parents=True, exist_ok=True)
    (mini_repo / review_note).write_text("", encoding="utf-8")

    reordered_units = copy.deepcopy(package_data)
    reordered_units["module_patch"]["unit_order"].reverse()
    reordered_units["units"][0]["study_map"] = copy.deepcopy(current_map)
    reordered_units_package = tmp_path / "reordered-units-module-plan.yaml"
    write_yaml(reordered_units_package, reordered_units)
    rejected_unit_order = run_los(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(reordered_units_package), "--check",
    )
    assert rejected_unit_order.returncode == 1
    assert "reorders existing units" in rejected_unit_order.stderr

    reordered = copy.deepcopy(package_data)
    reordered["units"][0]["study_map"] = copy.deepcopy(current_map)
    reordered["units"][0]["study_map"]["stages"].reverse()
    for number, stage in enumerate(reordered["units"][0]["study_map"]["stages"], start=1):
        stage["number"] = number
    reordered_package = tmp_path / "reordered-module-plan.yaml"
    write_yaml(reordered_package, reordered)
    rejected_order = run_los(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(reordered_package), "--check",
    )
    assert rejected_order.returncode == 1
    assert "reorders existing stages" in rejected_order.stderr

    reordered["plan_contract"]["intentional_reorders"] = [{
        "target": "study-map-stage-order", "id": "study-map-demo-l02",
        "reason": "The review must precede the derivation after a curriculum change.",
    }]
    write_yaml(reordered_package, reordered)
    reviewed_order = run_los(
        mini_repo, "module-plan-import", "module-demo",
        "--file", str(reordered_package), "--check",
    )
    assert reviewed_order.returncode == 0, reviewed_order.stderr


def test_note_revise_is_approval_gated_and_preserves_identity_and_role(mini_repo, tmp_path):
    revised = tmp_path / "note-demo.md"
    revised.write_text("""---
id: note-demo
type: note
title: Demo note revised
created: 2026-07-16
role: synthesis
concepts: [concept-expected-value]
sources: [source-demo-book]
---

Revised after explicit review.
""", encoding="utf-8")
    denied = run_los(mini_repo, "note-revise", "note-demo", "--file", str(revised))
    assert denied.returncode == 2
    applied = approved_v2_cli(
        mini_repo, "note-revise", "note-demo", "--file", str(revised), "--approve",
        "--file-sha256", file_sha256(revised),
        artifact_ids=["note-demo"],
        idempotency_key="curriculum-note-revise",
    )
    assert applied.returncode == 0, applied.stderr
    note = load_repo(mini_repo).notes["note-demo"]
    assert note.meta["title"] == "Demo note revised"
    assert note.meta["role"] == "synthesis"
    assert "explicit review" in note.body


def test_shelving_applies_only_selected_items_after_explicit_approval(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    items = tmp_path / "items.json"
    items.write_text(json.dumps({"items": [
        {"id": "proposal-keep", "kind": "garden", "title": "Keep",
         "destination": "knowledge/garden/kept-idea.md", "rationale": "Worth gestating.",
         "content": "# Kept idea\n\nOriginal wording."},
        {"id": "proposal-skip", "kind": "garden", "title": "Skip",
         "destination": "knowledge/garden/skipped-idea.md", "rationale": "Optional.",
         "content": "# Skipped idea"},
    ]}), encoding="utf-8")
    prepared = approved_v2_cli(
        mini_repo, "shelving-prepare", "unit-demo-l01", "--items-file", str(items),
        "--items-file-sha256", file_sha256(items),
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-shelving-prepare",
    )
    assert prepared.returncode == 0, prepared.stderr
    denied = run_los(mini_repo, "shelving-apply", "unit-demo-l01",
                     "--selected", "proposal-keep")
    assert denied.returncode == 2
    applied = approved_v2_cli(
        mini_repo, "shelving-apply", "unit-demo-l01", "--approve",
        "--selected", "proposal-keep",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01", "proposal-keep"],
        idempotency_key="curriculum-shelving-apply",
    )
    assert applied.returncode == 0, applied.stderr
    assert (mini_repo / "knowledge/garden/kept-idea.md").is_file()
    assert not (mini_repo / "knowledge/garden/skipped-idea.md").exists()


def test_quarantine_boundary_never_projects_quarantined_content(mini_repo):
    add_curriculum(mini_repo)
    write_yaml(mini_repo / "curriculum/programs/program-masters-planning.yaml", {
        "id": "program-masters-planning", "type": "program", "title": "Master’s Planning",
        "kind": "quarantine", "status": "quarantined", "default": False,
        "semester_bound": False, "boundary_action": "Open Master’s Planning", "semesters": [],
    })
    write_yaml(mini_repo / "curriculum/quarantine/index.yaml", {
        "type": "quarantine-index", "id": "quarantine-masters-planning",
        "workspace_ids": ["workspace-degree-planning"],
        "boundary_program_id": "program-masters-planning",
    })
    secret = mini_repo / "curriculum/quarantine/masters-planning/prospective.md"
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text("QUARANTINED-PROSPECTIVE-SECRET", encoding="utf-8")
    manifest = json.loads(generate_all(load_repo(mini_repo), "T1")["manifest.json"])
    encoded = json.dumps(manifest)
    assert "program-masters-planning" not in encoded
    assert "quarantine_boundaries" not in manifest
    assert manifest["counts"]["programs"] == len(manifest["programs"])
    assert "QUARANTINED-PROSPECTIVE-SECRET" not in encoded
    assert "workspace-degree-planning" not in encoded


def test_session_end_reports_canvas_as_unrelated_and_never_session_owned(mini_repo):
    add_curriculum(mini_repo)
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=mini_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=mini_repo, check=True)
    subprocess.run(["git", "add", "."], cwd=mini_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=mini_repo, check=True)
    saved = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
        "--replace", "--text", "Session-owned note.",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-session-owned-note",
    )
    assert saved.returncode == 0, saved.stderr
    (mini_repo / "Untitled 37.canvas").write_text("{}", encoding="utf-8")
    ended = run_los(mini_repo, "session-end")
    assert ended.returncode == 0, ended.stderr
    payload = json.loads(ended.stdout)
    assert any("stage-demo/notes.md" in path for path in payload["touched"])
    assert "Untitled 37.canvas" not in payload["touched"]
    assert any("Untitled 37.canvas" in line for line in payload["unrelated_changes"])
    # session-end gates on validation, and validate.py resolves its repository
    # from its own location unless given --root. Without that flag it validated
    # the repository the TOOLS live in, so an unrelated warning over there could
    # block closing a session here. The freshly written report proves the
    # validator ran against THIS root.
    report = mini_repo / "generated" / "reports" / "validation-report.md"
    assert report.is_file(), "session-end validated a different repository root"


# ------------------------------------------- write-path robustness (red-team)
NOTE_REL = "curriculum/modules/module-demo/units/unit-demo-l01/stages/stage-demo/notes.md"


def test_empty_note_text_is_refused_instead_of_truncating(mini_repo):
    add_curriculum(mini_repo)
    saved = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
        "--replace", "--text", "Real content worth keeping.",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-nonempty-note",
    )
    assert saved.returncode == 0, saved.stderr
    note = mini_repo / NOTE_REL
    before = note.read_text(encoding="utf-8")
    for empty in ("", "   \n\t "):
        wiped = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                        "--replace", "--text", empty)
        assert wiped.returncode == 2
        assert "empty note" in wiped.stderr
    assert note.read_text(encoding="utf-8") == before


def test_empty_snapshot_token_is_refused_not_read_as_unguarded(mini_repo):
    add_curriculum(mini_repo)
    probe = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                    "--text", "probe", "--expected-snapshot", "")
    assert probe.returncode == 3
    assert "expected-snapshot" in probe.stderr
    # Omitting the flag cannot bypass the V2 envelope authority.
    unguarded = run_los(mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
                        "--text", "probe")
    assert unguarded.returncode == 2
    assert "GatewayEnvelopeV2" in unguarded.stderr


def test_two_captures_with_one_title_in_one_second_keep_both(mini_repo):
    add_curriculum(mini_repo)
    first_key = "curriculum-capture-first"
    second_key = "curriculum-capture-second"
    first = approved_v2_cli(
        mini_repo, "capture", "--json", "--title", "race", "--text", "FIRST",
        artifact_ids=[request_artifact_id("capture.create", first_key)],
        idempotency_key=first_key,
    )
    second = approved_v2_cli(
        mini_repo, "capture", "--json", "--title", "race", "--text", "SECOND",
        artifact_ids=[request_artifact_id("capture.create", second_key)],
        idempotency_key=second_key,
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    one, two = gateway_result(first), gateway_result(second)
    assert one["ok"] and two["ok"]
    assert one["captured"] != two["captured"]
    bodies = [(mini_repo / payload["captured"]).read_text(encoding="utf-8")
              for payload in (one, two)]
    assert any("FIRST" in body for body in bodies)
    assert any("SECOND" in body for body in bodies)


def test_unwritable_note_target_refuses_cleanly_without_debris(mini_repo):
    add_curriculum(mini_repo)
    note = mini_repo / NOTE_REL
    note.unlink()
    note.mkdir()  # the target is now a directory: an ordinary filesystem mishap
    proc = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo", "--text", "probe",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-unwritable-note",
    )
    assert proc.returncode == 2
    assert "target is not a regular file" in gateway_error(proc)
    assert "Traceback" not in proc.stdout + proc.stderr
    assert not list(note.parent.glob(".*.tmp")), "a temp file was left behind"


def test_a_failed_write_rolls_the_whole_transaction_back(mini_repo):
    """stage-progress writes the study map AND the unit.

    When the second write failed the first stayed applied, and `validate` saw
    nothing wrong — a silent cross-file split-brain.
    """
    add_curriculum(mini_repo)
    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    study_map, unit = unit_dir / "study-map.yaml", unit_dir / "unit.yaml"
    before_map = study_map.read_text(encoding="utf-8")
    before_unit = unit.read_text(encoding="utf-8")
    (unit_dir / ".unit.yaml.tmp").mkdir()  # block the atomic temp name
    proc = approved_v2_cli(
        mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-rollback-failure",
    )
    assert proc.returncode == 2
    assert "Traceback" not in proc.stdout + proc.stderr
    assert study_map.read_text(encoding="utf-8") == before_map
    assert unit.read_text(encoding="utf-8") == before_unit
    (unit_dir / ".unit.yaml.tmp").rmdir()
    retry = approved_v2_cli(
        mini_repo, "stage-progress", "unit-demo-l01", "stage-demo", "complete",
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="curriculum-rollback-retry",
    )
    assert retry.returncode == 0, retry.stderr


def test_stage_ids_must_be_unique_across_study_maps(mini_repo):
    """`stages` is projected as a flat by-id index, so a stage id reused in
    another unit resolves to whichever map was generated last. Five stages in
    the curriculum-v2 import collided this way and only in-map uniqueness was
    checked."""
    import shutil

    add_curriculum(mini_repo)
    units = mini_repo / "curriculum/modules/module-demo/units"
    shutil.copytree(units / "unit-demo-l01", units / "unit-demo-l02")
    for name in ("unit.yaml", "study-map.yaml"):
        target = units / "unit-demo-l02" / name
        text = target.read_text(encoding="utf-8")
        # everything is re-identified except the stage id, which stays colliding
        text = text.replace("unit-demo-l01", "unit-demo-l02")
        text = text.replace("study-map-demo-l01", "study-map-demo-l02")
        target.write_text(text, encoding="utf-8")
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    codes = {issue.code for issue in validate(load_repo(mini_repo), online=False)}
    assert "MAP-STAGE-GLOBAL-DUP" in codes


def test_an_impossible_calendar_date_fails_validation(mini_repo):
    """`format: date` is declared in the schemas but was never enforced, so a
    transposed exam date validated clean."""
    registry = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["modules"][0]["attempts"][0]["date"] = "2026-13-45"
    write_yaml(registry, data)
    proc = run_los(mini_repo, "validate")
    assert proc.returncode != 0
    assert "2026-13-45" in proc.stdout
    assert "date" in proc.stdout


def test_session_end_reports_warnings_without_blocking(mini_repo):
    """Errors gate a session; by-design offline-material warnings must not."""
    add_curriculum(mini_repo)
    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=mini_repo, check=True)
    registry = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["sources"][0]["material"] = "material://source-demo-book-offline"
    write_yaml(registry, data)
    saved = approved_v2_cli(
        mini_repo, "stage-note", "unit-demo-l01", "stage-demo",
        "--replace", "--text", "Session-owned note.",
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-warning-session-note",
    )
    assert saved.returncode == 0, saved.stderr
    check = run_los(mini_repo, "validate")
    assert check.returncode == 0, check.stderr
    assert "0 warning(s)" not in check.stdout, "fixture did not produce a warning"
    ended = run_los(mini_repo, "session-end")
    assert ended.returncode == 0, ended.stderr
    payload = json.loads(ended.stdout)
    assert "warning(s)" in payload["validation"]



def test_unit_note_is_session_scoped_and_projected(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    write_outputs(load_repo(mini_repo), generate_all(load_repo(mini_repo), "T0"))
    manifest = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    snapshot = manifest["_generated"]["snapshot_id"]
    attachment = tmp_path / "handwritten.png"
    attachment.write_bytes(b"fixture-image")

    saved = approved_v2_cli(
        mini_repo, "unit-note", "unit-demo-l01",
        "--title", "Expected value session",
        "--text", "I connected linearity to the indicator-variable argument.",
        "--stage-id", "stage-demo",
        "--attachment", str(attachment),
        "--attachment-sha256", file_sha256(attachment),
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-unit-note",
        expected_snapshot=snapshot,
    )
    assert saved.returncode == 0, saved.stderr
    payload = gateway_result(saved)
    assert payload["stage_ids"] == ["stage-demo"]
    assert len(payload["attachments"]) == 1

    unit = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml")
        .read_text(encoding="utf-8")
    )
    assert unit["working_note"].endswith("/notes.md")
    note = mini_repo / unit["working_note"]
    text = note.read_text(encoding="utf-8")
    assert "learningos:unit-note" in text
    assert "Expected value session" in text
    assert "indicator-variable" in text

    projected = json.loads((mini_repo / "generated/manifest.json").read_text(encoding="utf-8"))
    unit_row = next(row for row in projected["units"] if row["id"] == "unit-demo-l01")
    assert unit_row["notes_text"] == text
    assert unit_row["note_sections"][0]["title"] == "Expected value session"
    assert unit_row["note_sections"][0]["stage_ids"] == ["stage-demo"]
    assert unit_row["note_sections"][0]["attachments"][0]["path"].endswith("handwritten.png")
    assert "indicator-variable" in unit_row["note_sections"][0]["summary"]
    # The legacy selected stage is not required by the command envelope.
    assert "stage_id" not in payload


def test_unit_note_requires_one_approved_hash_per_attachment(mini_repo, tmp_path):
    add_curriculum(mini_repo)
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    refused = approved_v2_cli(
        mini_repo, "unit-note", "unit-demo-l01",
        "--text", "Keep this draft outside the repository.",
        "--attachment", str(first),
        "--attachment", str(second),
        "--attachment-sha256", file_sha256(first),
        artifact_ids=["unit-demo-l01"],
        idempotency_key="curriculum-unit-note-incomplete-attachment-hashes",
    )
    assert refused.returncode == 2
    assert "once per --attachment" in gateway_error(refused)
    unit_dir = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
    assert not (unit_dir / "notes.md").exists()
    assert not (unit_dir / "attachments").exists()


def test_unit_note_rejects_foreign_stage_and_preserves_state(mini_repo):
    add_curriculum(mini_repo)
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    before = unit_path.read_text(encoding="utf-8")
    refused = run_los(
        mini_repo, "unit-note", "unit-demo-l01", "--text", "Do not write this",
        "--stage-id", "stage-foreign",
    )
    assert refused.returncode == 2
    assert "does not belong" in refused.stderr
    assert unit_path.read_text(encoding="utf-8") == before
    assert not (unit_path.parent / "notes.md").exists()


def test_unit_note_snapshot_guard_keeps_note_unchanged(mini_repo):
    add_curriculum(mini_repo)
    refused = run_los(
        mini_repo, "unit-note", "unit-demo-l01", "--text", "stale",
        "--expected-snapshot", "sha256:stale",
    )
    assert refused.returncode == 3
    assert not (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/notes.md").exists()

@pytest.mark.full_repo
def test_live_migration_is_idempotent_in_dry_run(repo_root):
    proc = subprocess.run([sys.executable, str(MIGRATE), "--root", str(repo_root), "--report"],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert "dry-run: 0 action(s)" in proc.stdout


# AMLS PAPER INVENTORY
#
# The reading list this inventory describes lives outside the authored tree,
# under ../materials/ (CLAUDE.md §11), so a CI checkout of this repository
# alone cannot see it. Splitting the old single test keeps every wiring
# assertion running everywhere:
#
#   * the wiring test reads the checked-in fixture — hermetic, runs in CI;
#   * the drift test proves the fixture still matches the external list —
#     local only, skipped where materials/ is not present.
#
# Regenerate the fixture with tools/refresh_amls_fixture.py.

AMLS_INVENTORY = Path(__file__).resolve().parent / "fixtures" / "amls-paper-inventory.yaml"
AMLS_READING_LIST = (
    ROOT.parent
    / "materials/.flat/source-amls-ss26-lectures/AMLS-Source-Papers-Reading-List.md"
)


def _amls_inventory() -> dict:
    return yaml.safe_load(AMLS_INVENTORY.read_text(encoding="utf-8"))


@pytest.mark.full_repo
def test_amls_complete_paper_inventory_is_wired_per_lecture(repo_root):
    inventory = _amls_inventory()
    assert inventory["totals"]["curated"] == 60
    assert inventory["totals"]["bibliography"] == 283

    repo = load_repo(repo_root)
    source = repo.sources["source-amls-ss26-lectures"]
    assert source["material"] == "material://source-amls-ss26-lectures"
    assert source["identifiers"]["paper-reading-list"].endswith(
        "/AMLS-Source-Papers-Reading-List.md")

    for lecture, expected in inventory["lectures"].items():
        study_map = repo.study_maps[f"study-map-amls-l{lecture}"].data
        stage = next(row for row in study_map["stages"]
                     if row["id"] == f"stage-amls-l{lecture}-integrate")
        selected = [row for row in stage["resources"]
                    if row.get("locator") ==
                    f"AMLS paper reading list, Part 1, Lecture {lecture}"]
        assert [row["label"].removeprefix("Primary paper — ")
                for row in selected] == expected["curated"]
        assert all(row.get("url") and row.get("vault_path") for row in selected)
        complete = [row for row in stage["resources"]
                    if row.get("locator") ==
                    f"AMLS paper reading list, Part 2, Lecture {lecture}; reference-only"]
        assert len(complete) == 1
        assert complete[0]["kind"] == "reference"
        assert f"({expected['bibliography']} entries)" in complete[0]["label"]

        # The inventory must be PRESERVED (asserted above: every curated paper is a
        # resource, and the full bibliography is a reference-only entry). It must not
        # be pushed onto the learner as a study task. Source-completeness is an
        # operator obligation discharged at plan-creation time (WORKFLOWS.md); a
        # done_when that says "disposition every curated paper" converts the
        # operator's bookkeeping into the learner's exam hours. Normalization pass,
        # 2026-08-08, item 4.
        assert not any("Every curated paper is marked" in item
                       for item in stage["done_when"]), (
            f"lecture {lecture}: the operator's source-completeness gate has leaked "
            "back into a learner done_when")
        assert any("primary paper" in item.lower() for item in stage["done_when"]), (
            f"lecture {lecture}: the learner gate must still name the primary paper")


@pytest.mark.full_repo
def test_amls_reading_list_still_matches_checked_in_inventory():
    if not AMLS_READING_LIST.exists():
        pytest.skip(f"materials/ not checked out: {AMLS_READING_LIST}")
    from refresh_amls_fixture import parse_reading_list

    assert parse_reading_list(AMLS_READING_LIST) == _amls_inventory()["lectures"], (
        "the external AMLS reading list has drifted from "
        "tests/fixtures/amls-paper-inventory.yaml — rerun "
        "tools/refresh_amls_fixture.py, then re-wire the affected study maps"
    )


@pytest.mark.full_repo
def test_live_migration_preserves_rollback_evidence(repo_root):
    original = repo_root / "records/modules.yaml"
    backup = repo_root / "migration/curriculum-v2/originals/records-modules.yaml"
    mapping = yaml.safe_load(
        (repo_root / "migration/curriculum-v2/old-to-new.yaml").read_text(encoding="utf-8"))
    report = (repo_root / "migration/curriculum-v2/report.md").read_text(encoding="utf-8")

    # Rollback evidence means the DATA has not drifted from the pre-migration
    # snapshot — not that the deprecated file is forbidden a deprecation banner.
    # `records/modules.yaml` is a frozen compatibility snapshot (CLAUDE.md hard
    # rule #2), so its records must stay byte-identical to the backup, while its
    # comment header is allowed to say loudly that it owns nothing. Byte-equality
    # on the whole file would forbid exactly that warning. Normalization pass,
    # 2026-08-08, item 1.
    def _records_only(path):
        return [ln for ln in path.read_text(encoding="utf-8").splitlines()
                if not ln.lstrip().startswith("#")]

    assert yaml.safe_load(original.read_text(encoding="utf-8")) == \
        yaml.safe_load(backup.read_text(encoding="utf-8")), \
        "records/modules.yaml data drifted from the rollback snapshot"
    assert _records_only(original) == _records_only(backup), \
        "records/modules.yaml changed outside its comment header"
    assert "FROZEN COMPATIBILITY SNAPSHOT" in original.read_text(encoding="utf-8"), \
        "the frozen-snapshot banner regressed; the file would again read as an owner"
    assert "single canonical owner" not in original.read_text(encoding="utf-8"), \
        "records/modules.yaml is claiming ownership again"
    pairs = {(row["old"], row["new"]) for row in mapping["mappings"]}
    assert ("work/active/workspace-degree-planning",
            "curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning") in pairs
    assert ("sources/collections/degree-module-anchors.yaml",
            "curriculum/quarantine/masters-planning/sources/degree-module-anchors.yaml") in pairs
    assert "codex/learning-path-app-v1" in report
    assert "revert" in report.casefold()


# MATERIAL RESOURCE PROJECTION REGRESSION MATRIX
#
# These tests define the core-owned interface contract for exact local stage
# resources. They intentionally precede the generator implementation.
#
# They use only mini_repo/tmp_path data and never inspect the real materials
# tree, real generated manifest, canary, or user vault.


def _material_projection_fixture(
        mini_repo,
        *,
        source_material,
        resources,
        existing_files=()):
    """Project one synthetic study-map resource set through the real core."""
    from learning_os.genout import build_manifest
    from learning_os.loader import load_repo

    add_curriculum(mini_repo)

    registry = mini_repo / "sources" / "sources.yaml"
    registry_data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    source = next(
        row for row in registry_data["sources"]
        if row["id"] == "source-demo-book"
    )
    source["material"] = source_material
    write_yaml(registry, registry_data)

    repo = load_repo(mini_repo)
    study_map = next(iter(repo.study_maps.values()))
    map_data = study_map.data

    assert map_data["stages"], "synthetic curriculum has no stage"
    stage = map_data["stages"][0]
    stage_id = stage["id"]
    stage["resources"] = [
        {"kind": "read", **resource}
        for resource in resources
    ]
    write_yaml(study_map.path, map_data)

    for relative in existing_files:
        target = repo.materials_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"fixture material: {relative}\n",
            encoding="utf-8",
        )

    repo = load_repo(mini_repo)
    manifest = build_manifest(
        repo,
        "2026-08-06T20:00:00+00:00",
    )

    nested_map = next(
        row for row in manifest["study_maps"]
        if row["id"] == study_map.id
    )
    nested_stage = next(
        row for row in nested_map["stages"]
        if row["id"] == stage_id
    )
    flat_stage = next(
        row for row in manifest["stages"]
        if row["id"] == stage_id
    )

    return repo, nested_stage["resources"], flat_stage["resources"]


def _expected_material_path(repo, material_uri):
    target = (
        repo.materials_root
        / material_uri.removeprefix("material://")
    )
    return str(
        target.resolve().relative_to(
            repo.learningos_root.resolve()
        )
    )


def _assert_projected_resource(
        repo,
        nested,
        flat,
        index,
        *,
        material_uri,
        exists):
    projected = nested[index]

    assert projected["material_uri"] == material_uri
    assert projected["material_path"] == _expected_material_path(
        repo,
        material_uri,
    )
    assert projected["material_exists"] is exists

    assert flat[index]["material_uri"] == projected["material_uri"]
    assert flat[index]["material_path"] == projected["material_path"]
    assert flat[index]["material_exists"] is projected["material_exists"]

    return projected


def test_material_resource_projection_preserves_authored_uri(mini_repo):
    material_uri = (
        "material://source-demo-book/"
        "lecture-slides/01_Introduction.pdf"
    )

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Lecture 01",
            "locator": "lecture-slides/01_Introduction.pdf",
            "vault_path": material_uri,
        }],
        existing_files=[
            "source-demo-book/lecture-slides/01_Introduction.pdf",
        ],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["vault_path"] == material_uri
    assert "lecture-slides/lecture-slides" not in projected[
        "material_path"
    ]


def test_material_resource_projection_handles_single_file_source(
        mini_repo):
    material_uri = "material://source-demo-book/demo-book.pdf"

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=material_uri,
        resources=[{
            "source_id": "source-demo-book",
            "label": "Complete book",
            "locator": "demo-book.pdf",
            "vault_path": material_uri,
        }],
        existing_files=["source-demo-book/demo-book.pdf"],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["material_path"].endswith(
        "source-demo-book/demo-book.pdf"
    )
    assert "demo-book.pdf/demo-book.pdf" not in projected[
        "material_path"
    ]


def test_material_resource_projection_derives_file_locators(
        mini_repo):
    locators = [
        "Primer_Linear_Algebra.pdf",
        "lecture-slides/02_Regression.pdf",
        "older-lecture-slides/08_Neural_Networks.pdf",
        "lecture-slides/VL 11-transformers.pdf (81 pages)",
    ]
    exact_locators = [
        "Primer_Linear_Algebra.pdf",
        "lecture-slides/02_Regression.pdf",
        "older-lecture-slides/08_Neural_Networks.pdf",
        "lecture-slides/VL 11-transformers.pdf",
    ]
    resources = [
        {
            "source_id": "source-demo-book",
            "label": locator,
            "locator": locator,
        }
        for locator in locators
    ]

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=resources,
        existing_files=[
            f"source-demo-book/{locator}"
            for locator in exact_locators
        ],
    )

    for index, (locator, exact_locator) in enumerate(
            zip(locators, exact_locators, strict=True)):
        material_uri = (
            f"material://source-demo-book/{exact_locator}"
        )
        projected = _assert_projected_resource(
            repo,
            nested,
            flat,
            index,
            material_uri=material_uri,
            exists=True,
        )
        assert projected["locator"] == locator
        assert "vault_path" not in projected


def test_material_resource_projection_ignores_descriptive_and_unsafe_locators(
        mini_repo):
    resources = [
        {
            "source_id": "source-demo-book",
            "label": "Reading guidance",
            "locator": "Chapter 9, selected sections",
        },
        {
            "source_id": "source-demo-book",
            "label": "Traversal attempt",
            "locator": "../../outside/secret.pdf",
        },
        {
            "source_id": "source-demo-book",
            "label": "Absolute path attempt",
            "locator": "/tmp/secret.pdf",
        },
        {
            "source_id": "source-demo-book",
            "label": "Lecture range",
            "locator": (
                "lecture-slides/VL 01.pdf through "
                "lecture-slides/VL 11.pdf"
            ),
        },
        {
            "source_id": "source-demo-book",
            "label": "Combined files",
            "locator": "exercise/UE 08.pdf + exercise/UE 09.pdf",
        },
    ]

    _repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=resources,
    )

    for index in range(len(resources)):
        assert nested[index].get("material_uri") is None
        assert nested[index].get("material_path") is None
        assert nested[index].get("material_exists") in {
            None,
            False,
        }

        assert flat[index].get("material_uri") is None
        assert flat[index].get("material_path") is None
        assert flat[index].get("material_exists") in {
            None,
            False,
        }


def test_material_resource_projection_keeps_missing_material_nonfatal(
        mini_repo):
    locator = "lecture-slides/offline.pdf"
    material_uri = f"material://source-demo-book/{locator}"

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-demo-book/lecture-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Offline lecture",
            "locator": locator,
        }],
    )

    _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=False,
    )


def test_material_resource_projection_uses_source_material_authority(
        mini_repo):
    """A source may intentionally delegate material identity to another ID."""
    material_uri = (
        "material://source-shared-slides/"
        "exercise-slides/UE4.pdf"
    )

    repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material=(
            "material://source-shared-slides/exercise-slides"
        ),
        resources=[{
            "source_id": "source-demo-book",
            "label": "Shared exercise deck",
            "locator": "exercise-slides/UE4.pdf",
        }],
        existing_files=[
            "source-shared-slides/exercise-slides/UE4.pdf",
        ],
    )

    projected = _assert_projected_resource(
        repo,
        nested,
        flat,
        0,
        material_uri=material_uri,
        exists=True,
    )

    assert projected["source_id"] == "source-demo-book"
    assert projected["material_uri"].startswith(
        "material://source-shared-slides/"
    )


def test_stage_resource_inherits_its_unique_exact_unit_route_target(mini_repo):
    """Descriptive stage prose must still open the lecture-specific target.

    Generated study maps append the route angle to ``locator``.  Re-parsing
    that prose as a path is unsafe and made AML L11 fall back to the source's
    lecture-slides directory.  The stable source-id + route-title pair already
    identifies the exact route, so the projection should reuse its target.
    """
    from learning_os.genout import build_manifest
    from learning_os.loader import load_repo

    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)

    registry = mini_repo / "sources" / "sources.yaml"
    registry_data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    source = next(
        row for row in registry_data["sources"]
        if row["id"] == "source-demo-book"
    )
    source["material"] = "material://source-demo-book/lecture-slides"
    write_yaml(registry, registry_data)

    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route.update({
        "title": "Current L11 Transformers lecture deck",
        "locator": "lecture-slides/VL 11-transformers.pdf",
    })
    write_yaml(source_map_path, source_map)

    repo = load_repo(mini_repo)
    study_map = next(iter(repo.study_maps.values()))
    map_data = study_map.data
    map_data["stages"][0]["resources"] = [{
        "kind": "read",
        "label": "Current L11 Transformers lecture deck",
        "source_id": "source-demo-book",
        "locator": (
            "lecture-slides/VL 11-transformers.pdf (81 pages) — "
            "the exact 2026 scope authority"
        ),
        "scope_triage": "required-now",
    }]
    write_yaml(study_map.path, map_data)

    target = (
        repo.materials_root
        / "source-demo-book/lecture-slides/VL 11-transformers.pdf"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("synthetic lecture\n", encoding="utf-8")

    manifest = build_manifest(
        load_repo(mini_repo),
        "2026-08-23T12:00:00+00:00",
    )
    projected = next(
        row for row in manifest["stages"]
        if row["id"] == map_data["stages"][0]["id"]
    )["resources"][0]

    assert projected["material_uri"] == (
        "material://source-demo-book/lecture-slides/VL 11-transformers.pdf"
    )
    assert projected["material_path"].endswith(
        "source-demo-book/lecture-slides/VL 11-transformers.pdf"
    )
    assert projected["material_exists"] is True


def test_stage_resource_does_not_inherit_an_ambiguous_or_missing_route(
        mini_repo):
    """A collection or range is not silently presented as one openable file."""
    from learning_os.genout import build_manifest
    from learning_os.loader import load_repo

    add_curriculum(mini_repo)
    _add_material_overview(mini_repo)

    registry = mini_repo / "sources" / "sources.yaml"
    registry_data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    source = next(
        row for row in registry_data["sources"]
        if row["id"] == "source-demo-book"
    )
    source["material"] = "material://source-demo-book/lecture-slides"
    write_yaml(registry, registry_data)

    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route.update({
        "title": "Current lecture range",
        "locator": "lecture-slides/VL 01.pdf through VL 11.pdf",
    })
    write_yaml(source_map_path, source_map)

    repo = load_repo(mini_repo)
    study_map = next(iter(repo.study_maps.values()))
    map_data = study_map.data
    map_data["stages"][0]["resources"] = [{
        "kind": "read",
        "label": "Current lecture range",
        "source_id": "source-demo-book",
        "locator": "open the exact slide, not the whole deck",
        "scope_triage": "required-now",
    }]
    write_yaml(study_map.path, map_data)

    manifest = build_manifest(
        load_repo(mini_repo),
        "2026-08-23T12:00:00+00:00",
    )
    projected = next(
        row for row in manifest["stages"]
        if row["id"] == map_data["stages"][0]["id"]
    )["resources"][0]

    assert projected.get("material_uri") is None
    assert projected.get("material_path") is None
    assert projected.get("material_exists") in {None, False}


def test_material_resource_projection_refuses_compound_and_unsafe_uris(
        mini_repo):
    resources = [
        {
            "source_id": "source-demo-book",
            "label": "Compound locator",
            "locator": "first.pdf; second.pdf",
        },
        {
            "source_id": "source-demo-book",
            "label": "Unsafe authored URI",
            "vault_path": (
                "material://source-demo-book/"
                "../../../repository/secret.pdf"
            ),
        },
    ]

    _repo, nested, flat = _material_projection_fixture(
        mini_repo,
        source_material="material://source-demo-book",
        resources=resources,
        existing_files=[
            "source-demo-book/first.pdf",
            "source-demo-book/second.pdf",
        ],
    )

    for collection in (nested, flat):
        for resource in collection:
            assert resource.get("material_uri") is None
            assert resource.get("material_path") is None
            assert resource.get("material_exists") in {
                None,
                False,
            }


# ORDERING REGRESSION


@pytest.mark.full_repo
def test_aml_units_and_exam_stages_keep_the_reviewed_sequence(repo_root):
    """Expanded material menus must not rearrange the AML learning surface."""
    repo = load_repo(repo_root)
    module = repo.modules["module-hu-aml"]
    expected_units = [
        *[f"unit-aml-l{lecture:02d}" for lecture in range(1, 12)],
        "unit-aml-exam-prep",
    ]
    assert module["unit_order"] == expected_units
    assert [
        unit.id
        for unit in sorted(
            (unit for unit in repo.units.values() if unit.module_id == "module-hu-aml"),
            key=lambda unit: unit.data["order"],
        )
    ] == expected_units

    study_map = repo.study_maps["study-map-aml-exam-prep"].data
    expected_stages = [
        "stage-aml-calibration",
        "stage-aml-foundations-repair",
        "stage-aml-linear-optimization-repair",
        "stage-aml-neural-transformer-loop",
        "stage-aml-integration-sheet",
        "stage-aml-mock-one",
        "stage-aml-mock-one-repair",
        "stage-aml-mock-two",
        "stage-aml-final-repair",
        "stage-aml-taper",
    ]
    assert [stage["id"] for stage in study_map["stages"]] == expected_stages
    assert study_map["current_stage"] == expected_stages[0]
    assert [stage["status"] for stage in study_map["stages"]] == [
        "active", *(["pending"] * 9),
    ]


# RESOURCE IDENTITY (ADR-009)


@pytest.mark.full_repo
def test_sad_lectures_are_knowledge_maps_with_complete_material_menus(repo_root):
    """SaD follows the same choose-a-source semantics as AML, lecture by lecture."""
    repo = load_repo(repo_root)
    module_dir = (
        repo_root
        / "curriculum/modules/module-hu-m2-statistik-analysis"
    )
    module = yaml.safe_load((module_dir / "module.yaml").read_text(encoding="utf-8"))
    lecture_ids = [f"unit-m2-sad-l{i:02d}" for i in range(1, 16)]
    unit_ids = [*lecture_ids, "unit-m2-sad-clustering"]

    assert all(uid in module["unit_order"] for uid in unit_ids)
    assert "unit-m2-sad-l06-l10" not in module["unit_order"]

    node_ids_by_unit = {}
    for uid in unit_ids:
        unit = repo.units[uid].data
        knowledge_map = unit.get("knowledge_map")
        assert knowledge_map and knowledge_map["nodes"], f"{uid} has no knowledge map"
        # Until 2026-08-22 these two lines asserted the opposite: that a
        # lecture carrying a knowledge map and a complete menu had *no* study
        # map. That was the policy, and it left sixteen SaD units with nothing
        # to work through. OPERATOR.md rule 6 now says a unit of an enrolled
        # module owes an ordered map, so the assertion inverts with it.
        assert unit.get("current_study_map"), f"{uid} owes a study map"
        assert (module_dir / f"units/{uid}/study-map.yaml").exists()
        node_ids_by_unit[uid] = {node["id"] for node in knowledge_map["nodes"]}

    source_map = yaml.safe_load(
        (module_dir / "source-map.yaml").read_text(encoding="utf-8")
    )
    routes_by_unit = {uid: [] for uid in unit_ids}
    required = {"unit_id", "title", "format", "angle", "covers", "depth", "scope", "locator"}
    for source in source_map["sources"]:
        for route in source.get("unit_routes", []):
            assert not (
                isinstance(route, str) and route.startswith("unit-m2-sad-")
            ), f"SaD route on {source['source_id']} is still an unannotated id"
            if not isinstance(route, dict) or route.get("unit_id") not in routes_by_unit:
                continue
            assert required <= route.keys()
            assert route["covers"]
            assert set(route["covers"]) <= node_ids_by_unit[route["unit_id"]]
            routes_by_unit[route["unit_id"]].append((source["source_id"], route))

    assert all(routes_by_unit.values()), "every SaD lecture/topic needs material choices"
    assert all(
        any(route["scope"] == "current" for _, route in routes)
        for routes in routes_by_unit.values()
    ), "every SaD lecture/topic needs a current course-scope option"
    formats = {
        route["format"]
        for routes in routes_by_unit.values()
        for _, route in routes
    }
    assert {"course-material", "exercise", "book", "video"} <= formats

    obsolete = [
        "work/active/workspace-m2-exam-prep/inputs/SaD_L01_Mini_Plan.md",
        "work/active/workspace-m2-exam-prep/outputs/SaD-L06-L15-module-plan.yaml",
        "work/active/workspace-m2-exam-prep/paths/path-sad-l04-probability-bayes.yaml",
    ]
    assert not [path for path in obsolete if (repo_root / path).exists()]


@pytest.mark.full_repo
def test_amls_bundle_resources_carry_stable_ids(repo_root):
    """A bundled source must be addressable item by item, not just as a bundle.

    `source-amls-ss26-lectures` backs ~96 stage resources. Without per-resource
    identity, every judgment about any of them files under one source id, so
    "SystemML was excellent" and "TASO was unnecessary" become the same record.
    """
    repo = load_repo(repo_root)
    ided, bare = [], []
    for study_map in repo.study_maps.values():
        if not str(study_map.data.get("id", "")).startswith("study-map-amls"):
            continue
        for stage in study_map.data.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                if resource.get("source_id") != "source-amls-ss26-lectures":
                    continue
                (ided if resource.get("id") else bare).append(resource["label"])

    assert len(ided) >= 90, f"only {len(ided)} AMLS bundle resources carry ids"
    for label in bare:
        # Restraint (ADR-009): activities are not teaching objects. An
        # explain-back drill is something you DO, not something to judge or
        # reuse, so it deliberately has no identity.
        assert "Explain-back" in label, (
            f"un-identified AMLS bundle resource that is not an activity: {label}")


@pytest.mark.full_repo
def test_a_paper_cited_by_two_lectures_shares_one_resource_id(repo_root):
    """Identity belongs to the paper, not to the citation.

    AMLS cites "Attention Is All You Need" from both L04 and L07, and the
    Hidden Technical Debt paper from both L01 and L02. If each citation minted
    its own id, feedback would scatter across the plans that happen to mention
    a paper instead of accumulating on the paper — which is the reuse ADR-009
    is for. This test fails if someone "fixes" the duplicate ids.
    """
    repo = load_repo(repo_root)
    by_id = {}
    for study_map in repo.study_maps.values():
        for stage in study_map.data.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                if resource.get("id"):
                    by_id.setdefault(resource["id"], []).append(resource)

    shared = {rid: rs for rid, rs in by_id.items() if len(rs) > 1}
    assert "resource-amls-attention-is-all-you-need" in shared, (
        "the paper cited by AMLS L04 and L07 no longer shares one resource id")

    for rid, uses in shared.items():
        urls = {r.get("url") for r in uses if r.get("url")}
        assert len(urls) <= 1, f"resource id {rid} spans different urls: {urls}"


# FACETED LIBRARY (ADR-009)


@pytest.mark.full_repo
def test_topics_are_a_closed_vocabulary(repo_root):
    """An unlisted topic must be an error, or the facet decays into tag soup.

    The whole reason `topics` is a controlled vocabulary rather than free tags is
    that free tags reliably produce deep-learning / DL / neural-networks / NN
    within a year. That only holds if the validator actually refuses unknown
    values.
    """
    from learning_os.rules import validate as _validate
    repo = load_repo(repo_root)
    assert repo.topics, "sources/topics.yaml did not load"
    for tid in repo.topics:
        assert tid.startswith("topic-")
    # every topic used by a source must exist in the vocabulary
    for source in repo.sources.values():
        for tid in source.get("topics", []) or []:
            assert tid in repo.topics, f"{source['id']} uses unknown topic {tid}"
    assert not [i for i in _validate(repo) if i.severity == "E"]


@pytest.mark.full_repo
def test_topics_are_independent_of_thematic_groups(repo_root):
    """One identity, many classifications — the point of the facet.

    If topics could only come from a source's own domain, the polyhierarchy
    would collapse back into the single-placement tree ADR-009 exists to escape.
    This asserts at least one source carries a topic whose display domain is not
    among that source's own thematic groups.
    """
    repo = load_repo(repo_root)
    crossing = []
    for source in repo.sources.values():
        groups = set(source.get("thematic_group_ids", []) or [])
        for tid in source.get("topics", []) or []:
            domain = repo.topics.get(tid, {}).get("domain")
            if domain and domain not in groups:
                crossing.append((source["id"], tid, domain))
    assert crossing, (
        "no source carries a topic outside its own domain — either the seed data "
        "regressed to one-domain-per-source, or the facet is being used as a "
        "second name for thematic_group_ids")


@pytest.mark.full_repo
def test_library_view_reports_unclassified_rather_than_hiding_it(repo_root):
    """Sparse is the honest state under on-use population, so it must be visible.

    A faceted browser that showed only classified sources would silently imply
    the Library is smaller than it is, and would create pressure to bulk-backfill
    topics — the exact judgment-inventing pass ADR-005 forbids.
    """
    from learning_os.genout import build_library
    repo = load_repo(repo_root)
    view = build_library(repo, "T1")
    assert "## By topic" in view and "## By domain" in view
    assert "## By purpose" in view and "## By form" in view
    assert "## By current use" in view
    assert "Not yet classified by topic" in view
    # enumerate, don't count: buckets must list their members
    assert "## Members" in view
    for sid in list(repo.sources)[:3]:
        assert f"`{sid}`" in view, f"{sid} appears in no bucket listing"


def test_source_feedback_can_name_a_resource(mini_repo):
    """The write path must reach the identity the records already carry.

    ADR-009 gave resources ids and feedback an optional resource_id, but until
    the CLI accepted one, four opinions about four papers in one bundled course
    still collapsed into an indistinguishable set — the model expressed the
    distinction and nothing could record it.

    Runs against `mini_repo`, never the live repository: a test that writes to
    the real tree leaves transaction receipts and bumped artifact revisions
    behind, which is state nobody asked for.
    """
    add_curriculum(mini_repo)
    unit, stage, src = "unit-demo-l01", "stage-demo", "source-demo-book"

    ok = approved_v2_cli(
        mini_repo, "source-feedback", unit, stage, src, "helpful",
        "--resource-id", "resource-demo-book-ch01",
        artifact_ids=[unit, "study-map-demo-l01"],
        idempotency_key="curriculum-resource-feedback-first",
    )
    assert ok.returncode == 0, ok.stderr
    assert gateway_result(ok)["feedback"]["resource_id"] \
        == "resource-demo-book-ch01"

    # a second, CONTRADICTORY judgment about a different resource in the SAME
    # source — the case that was inexpressible before v3
    other = approved_v2_cli(
        mini_repo, "source-feedback", unit, stage, src,
        "too-advanced", "--resource-id", "resource-demo-book-appendix",
        artifact_ids=[unit, "study-map-demo-l01"],
        idempotency_key="curriculum-resource-feedback-second",
    )
    assert other.returncode == 0, other.stderr

    # and a plain source-level judgment still works, unchanged
    plain = approved_v2_cli(
        mini_repo, "source-feedback", unit, stage, src, "useful-for-review",
        artifact_ids=[unit, "study-map-demo-l01"],
        idempotency_key="curriculum-resource-feedback-plain",
    )
    assert plain.returncode == 0, plain.stderr

    target = (mini_repo / "curriculum/modules/module-demo/units"
              / "unit-demo-l01/study-map.yaml")
    entries = [s for s in yaml.safe_load(target.read_text(encoding="utf-8"))
               ["stages"] if s["id"] == stage][0]["source_feedback"]
    by_resource = {e.get("resource_id"): e["feedback"] for e in entries}
    assert by_resource["resource-demo-book-ch01"] == "helpful"
    assert by_resource["resource-demo-book-appendix"] == "too-advanced"
    assert by_resource[None] == "useful-for-review"
    assert all(e["source_id"] == src for e in entries), \
        "source_id must survive on every entry — provenance is never traded away"


def test_source_feedback_rejects_a_resource_that_is_not_on_the_stage(mini_repo):
    """A dangling resource_id looks more precise than source-level feedback
    while actually saying less, so it must fail loudly and name the real ids."""
    add_curriculum(mini_repo)
    unit, stage = "unit-demo-l01", "stage-demo"

    bad = run_los(mini_repo, "source-feedback", unit, stage, "source-demo-book",
                  "helpful", "--resource-id", "resource-does-not-exist")
    assert bad.returncode == 2
    assert "resource not found" in bad.stderr
    assert "resource-demo-book-ch01" in bad.stderr, \
        "the error must list the ids that DO exist, or it is a dead end"

# --------------------------------------------------------------------------
# ADR-009 LIBRARY PROJECTION REGRESSIONS
#
# Domain/classification belongs to the source. Module/collection context is a
# separate projection. "Current use" includes both planned module routing and
# an actual stage citation.
# --------------------------------------------------------------------------

def test_manifest_current_use_includes_stage_only_source(mini_repo):
    """A stage citation is Current use even if the module source-map omitted it."""
    add_curriculum(mini_repo)

    source_map_path = (
        mini_repo
        / "curriculum/modules/module-demo/source-map.yaml"
    )
    source_map = yaml.safe_load(
        source_map_path.read_text(encoding="utf-8")
    )
    source_map["sources"] = []
    write_yaml(source_map_path, source_map)

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    assert manifest["indexes"]["source_to_modules"] == {
        "source-demo-book": ["module-demo"],
    }
    assert manifest["indexes"]["source_to_units"] == {
        "source-demo-book": ["unit-demo-l01"],
    }


def test_source_domain_does_not_inherit_module_or_collection_context(mini_repo):
    """Domain says what a source is about, never where it happens to be used."""
    add_curriculum(mini_repo)

    write_yaml(
        mini_repo / "curriculum/thematic-groups.yaml",
        {
            "thematic_groups": [
                {
                    "id": "thematic-group-source-domain",
                    "title": "Source domain",
                    "order": 10,
                },
                {
                    "id": "thematic-group-module-context",
                    "title": "Module context",
                    "order": 20,
                },
                {
                    "id": "thematic-group-collection-context",
                    "title": "Collection context",
                    "order": 30,
                },
            ],
        },
    )

    source_path = mini_repo / "sources/sources.yaml"
    source_doc = yaml.safe_load(
        source_path.read_text(encoding="utf-8")
    )
    source_doc["sources"][0]["thematic_group_ids"] = [
        "thematic-group-source-domain",
    ]
    write_yaml(source_path, source_doc)

    module_path = (
        mini_repo
        / "curriculum/modules/module-demo/module.yaml"
    )
    module_doc = yaml.safe_load(
        module_path.read_text(encoding="utf-8")
    )
    module_doc["thematic_group_ids"] = [
        "thematic-group-module-context",
    ]
    write_yaml(module_path, module_doc)

    write_yaml(
        mini_repo / "sources/collections/contextual-demo.yaml",
        {
            "title": "Contextual demo",
            "thematic_group_ids": [
                "thematic-group-collection-context",
            ],
            "entries": [
                {
                    "source": "source-demo-book",
                    "why": "Curated here for this context.",
                },
            ],
        },
    )

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    source = next(
        row
        for row in manifest["records"]
        if row.get("id") == "source-demo-book"
    )

    assert source["thematic_group_ids"] == [
        "thematic-group-source-domain",
    ]

    assert manifest["indexes"]["source_to_modules"][
        "source-demo-book"
    ] == ["module-demo"]

# --------------------------------------------------------------------------
# MANIFEST V4 — CONCRETE REVIEW DECISIONS
# --------------------------------------------------------------------------

def test_review_queue_projects_stable_inbox_decision(mini_repo):
    add_curriculum(mini_repo)

    capture = mini_repo / "work/inbox/question.md"
    capture.write_text(
        "# Where does this belong?\n\nUnrouted thought.\n",
        encoding="utf-8",
    )

    first = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )
    second = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T2",
        )["manifest.json"]
    )

    [item] = [
        row
        for row in first["review_items"]
        if row["category"] == "inbox"
    ]
    [again] = [
        row
        for row in second["review_items"]
        if row["category"] == "inbox"
    ]

    assert item["id"] == again["id"]
    assert item["title"] == "Where does this belong?"
    assert item["target"]["kind"] == "inbox-item"
    assert item["target"]["path"] == "work/inbox/question.md"
    assert item["target"]["revision"].startswith("sha256:")
    assert "human placement decision" in item["reason"]


def test_review_queue_projects_shelving_proposal_with_revision(mini_repo):
    add_curriculum(mini_repo)

    path = (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    )
    study_map = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )
    study_map["shelving"] = {
        "state": "proposed",
        "summary": "Two things are ready for human review.",
        "items": [
            {
                "id": "proposal-demo-note",
                "kind": "durable-note",
                "title": "Expected value synthesis",
                "destination": "knowledge/notes/mathematics/expected-value.md",
                "rationale": "The derivation is now stable.",
            },
        ],
    }
    write_yaml(path, study_map)

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    [item] = [
        row
        for row in manifest["review_items"]
        if row["category"] == "shelving"
    ]

    projected_map = next(
        row
        for row in manifest["study_maps"]
        if row["id"] == "study-map-demo-l01"
    )

    assert item["id"] == "review-shelving-study-map-demo-l01"
    assert item["target"]["id"] == "study-map-demo-l01"
    assert item["target"]["unit_id"] == "unit-demo-l01"
    assert item["target"]["proposal_ids"] == [
        "proposal-demo-note"
    ]
    assert item["target"]["revision"] == projected_map["revision"]


def test_review_queue_projects_needs_map_as_planning_decision(mini_repo):
    add_curriculum(mini_repo)

    path = (
        mini_repo
        / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    )
    unit = yaml.safe_load(
        path.read_text(encoding="utf-8")
    )
    unit["status"] = "needs-map"
    unit.pop("current_study_map", None)
    write_yaml(path, unit)

    manifest = json.loads(
        generate_all(
            load_repo(mini_repo),
            "T1",
        )["manifest.json"]
    )

    [item] = [
        row
        for row in manifest["review_items"]
        if row["category"] == "planning"
    ]

    assert item["id"] == "review-planning-unit-demo-l01"
    assert item["target"]["kind"] == "unit"
    assert item["target"]["id"] == "unit-demo-l01"
    assert item["target"]["module_id"] == "module-demo"
    assert "needs a study map" in item["reason"]
