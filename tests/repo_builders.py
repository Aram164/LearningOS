"""Shared synthetic-repository builders for the test suite.

`add_curriculum`, `write_yaml`, `_add_material_overview` and `run_los` used to
live in `test_curriculum_v2.py`, which made fifteen other test modules import
from a test module — so renaming or splitting the biggest test file would have
broken the whole suite. They are pure builders/drivers with no assertions, so
they live here now; behaviour is unchanged. The unit-revision fixture stack
(`_sliced_unit`, `_valid_dossier`, `_audit`, `_plan_contract`,
`_compact_setup`, `_compact_revision`) moved here for the same reason when a
second suite needed the same fixtures.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from learning_os.loader import load_repo, parse_frontmatter
from learning_os.routes import deterministic_route_id
from learning_os.warning_baseline import collect, write_baseline

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def run_los(root: Path, *args: str, stdin: str | None = None):
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), *args],
                          capture_output=True, text=True, input=stdin, timeout=120)


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_minimal_pdf(path: Path, texts: list[str]) -> None:
    """A dependency-free multi-page PDF with one text line per page.

    Hand-built so fixtures need no PDF writer: pypdf reads the result and
    extracts each page's line back. ``texts[i]`` must be plain ASCII in
    parentheses-safe characters.
    """
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{3 + i * 3} 0 R" for i in range(len(texts)))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(texts)} >>".encode())
    for i, text in enumerate(texts):
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {4 + i * 3} 0 R "
            f"/Resources << /Font << /F1 {5 + i * 3} 0 R >> >> >>".encode()
        )
        stream = f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode()
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream
            + b"\nendstream"
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets[1:]:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF".encode()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


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


def rich_fixture(root):
    """Curriculum plus one rich route, with the selection wired to it.

    Returns the deterministic route id and the route dict. Public because
    several test modules share it; behaviour is unchanged from the helper
    that lived in `test_manifest_routes.py`.
    """
    add_curriculum(root)
    _add_material_overview(root)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    route = source_map["sources"][0]["unit_routes"][0]
    route_id = deterministic_route_id(
        "module-demo", "source-demo-book", route
    )
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["source_selections"][0]["locator"] = route["locator"]
    unit["knowledge_map"]["nodes"][1]["concept_ids"] = [
        "concept-expected-value"
    ]
    write_yaml(unit_path, unit)
    return route_id, route


def material_fixture(root):
    """Rich route plus a fully-specified first stage and baselined warnings.

    Public because two test modules share it; behaviour is unchanged from
    the helper that lived in `test_material_editing.py`. Returns the loaded
    repo, the route id, and the study-map id.
    """
    route_id, _ = rich_fixture(root)
    source_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    route = source_map["sources"][0]["unit_routes"][0]
    route["angle_detail"] = "Überprüfung: a fully preserved explanation. " * 30
    write_yaml(source_path, source_map)
    repo = load_repo(root)
    sm = next(iter(repo.study_maps.values()))
    sm.data["plan_template_version"] = 1
    for number, stage in enumerate(sm.data["stages"], 1):
        stage["number"] = number
        stage.setdefault("exam_critical", False)
        stage.setdefault("concepts", ["concept-expected-value"])
    row = {"kind": "read", "label": route["title"], "source_id": "source-demo-book",
           "locator": route["locator"], "angle": route["angle"],
           "angle_detail": route["angle_detail"], "scope_triage": "required-now"}
    sm.data["stages"][0]["resources"] = [
        row, {**row, "angle": "This stage needs a distinct treatment.", "scope_triage": "helpful-now"},
        {"kind": "read", "label": "An independent resource", "source_id": "source-demo-book",
         "locator": "Independent chapter", "scope_triage": "reference-only"},
    ]
    write_yaml(sm.path, sm.data)
    material = repo.materials_root / "source-demo-book/lecture-01.pdf"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_text("synthetic lecture")
    signatures, errors = collect(root)
    assert not errors, errors
    write_baseline(root, signatures, "Pre-existing warnings in this synthetic fixture")
    return load_repo(root), route_id, sm.id


def curriculum_mini(tmp_path: Path):
    """A mini repo plus partitioned curriculum. Shared by the manifest
    shadow suites so both pin the same fixture shape."""
    from conftest import build_mini_repo

    mini = build_mini_repo(tmp_path)
    add_curriculum(mini)
    return mini


def add_manifest_fixtures(root: Path) -> None:
    """Projects, paths, shelves, facets, garden, AI, ledger, resume.

    Schema-valid minimal rows for every manifest domain the plain mini
    lacks, so the shadow mutation matrix can touch each one. Behaviour
    matches the probe that derived the expected closures.
    """
    write_yaml(root / "projects/registry/project-demo.yaml", {
        "schema_version": 1, "id": "project-demo", "type": "project",
        "title": "Demo project", "project_type": "software",
        "status": "active", "root_uri": "project://demo",
        "objective": "Demonstrate the shadow graph.",
        "milestone_ids": [], "linked_module_ids": ["module-demo"],
        "unit_ids": ["unit-demo-l01"], "workspace_ids": ["workspace-demo"],
        "thematic_group_ids": [],
        "boundaries": {"confidentiality": "private",
                       "external_code_access": "approved"},
    })
    write_yaml(root / "projects/relations/project-relations.yaml", {
        "relations": [{"id": "relationship-demo",
                       "from_project_id": "project-demo",
                       "to_id": "module-demo", "to_type": "module",
                       "relation_type": "informs", "reason": "Demo.",
                       "contribution": "Demo shelf."}],
    })
    write_yaml(root / "projects/aliases.yaml",
               {"aliases": {"old-demo": "project-demo"}})
    write_yaml(root / "work/active/workspace-demo/paths/path-demo.yaml", {
        "id": "path-demo", "title": "Demo path", "status": "active",
        "workspace_id": "workspace-demo", "current_stage": "stage-demo-path",
        "created": "2026-09-01",
        "stages": [{"id": "stage-demo-path", "title": "First step",
                    "status": "active", "objective": "Begin.",
                    "done_when": ["Started."]}],
    })
    write_yaml(root / "sources/collections/shelf.yaml", {
        "id": "shelf", "collection_kind": "catalogue", "title": "Shelf",
        "entries": [{"source": "source-demo-book"}],
    })
    write_yaml(root / "curriculum/thematic-groups.yaml", {
        "thematic_groups": [{"id": "group-maths", "title": "Maths", "order": 1}],
    })
    write_yaml(root / "sources/topics.yaml", {
        "topics": [{"id": "topic-probability", "title": "Probability",
                    "domain": "mathematics"}],
    })
    garden = root / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)
    (garden / "seed.md").write_text("A thought. #idea\n", encoding="utf-8")
    bundle = root / "operations/ai-actions/requests/ai-request-demo"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "request.yaml").write_text(yaml.safe_dump({
        "id": "ai-request-demo", "action_id": "unit.compare-materials",
        "status": "prepared",
        "target": {"kind": "unit", "id": "unit-demo-l01"},
        "provider": {"preferred": "manual-bundle"},
        "created_at": "2026-09-20T00:00:00+00:00",
    }), encoding="utf-8")
    ledger = root / "operations/transactions/revisions.yaml"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(yaml.safe_dump({
        "schema_version": 1, "type": "artifact-revision-ledger",
        "revisions": {"unit-demo-l01": 3},
    }), encoding="utf-8")
    (root / "curriculum/resume.yaml").write_text(
        yaml.safe_dump({"type": "resume-pointer", "module_id": "module-demo",
                        "unit_id": "unit-demo-l01",
                        "study_map_id": "study-map-demo-l01",
                        "stage_id": "stage-demo", "updated": "2026-09-20"}),
        encoding="utf-8")


def stage_manifest_producers(root: Path, repo) -> None:
    """Copy the real Core implementation tree under a mini root.

    Producer identity is the whole ``tools/learning_os`` tree (F3), so
    the fixture mirrors the whole tree rather than the declared subset:
    a producer-mutation test edits the staged copy the way a production
    code change edits the real one.
    """
    # `repo` stays in the signature for the existing call sites; the tree
    # no longer depends on the registry's declarations.
    real_root = Path(__file__).resolve().parent.parent
    target = root / "tools" / "learning_os"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        real_root / "tools" / "learning_os",
        target,
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def trace_summary(trace) -> dict[str, tuple[str, str]]:
    """Node -> (status, reason) for exact closure assertions."""
    return {event.node: (event.status, event.reason) for event in trace}


def moved_only(before: dict[str, str], after: dict[str, str]) -> set[str]:
    return {name for name in before if before[name] != after[name]}


def rewrite_yaml_doc(path: Path, mutate) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _sliced_route(route_id: str, locator: str, scope: str = "current") -> dict:
    # Canonical shape: `source_id` lives on the parent source entry, never
    # inside `unit_routes` (the schema forbids it there).
    return {
        "id": route_id,
        "unit_id": "unit-demo-l01",
        "title": f"Route {route_id}",
        "format": "book",
        "angle": "A synthetic angle.",
        "angle_detail": "A synthetic angle in long form for this lecture.",
        "covers": ["knowledge-demo-expectation"],
        "depth": "derivation",
        "scope": scope,
        "locator": locator,
    }


def _sliced_unit(root: Path, routes: list[dict]) -> None:
    add_curriculum(root)
    unit_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["knowledge_map"] = {
        "summary": "Expected value connects outcomes to probability weights.",
        "nodes": [
            {"id": "knowledge-demo-outcomes", "title": "Outcomes",
             "summary": "A variable maps outcomes to values."},
            {"id": "knowledge-demo-expectation", "title": "Expectation",
             "summary": "Expectation is a probability-weighted average."},
        ],
    }
    write_yaml(unit_path, unit)
    source_map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = routes
    write_yaml(source_map_path, source_map)
    registry_path = root / "sources/sources.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["material"] = "material://source-demo-book/"
    write_yaml(registry_path, registry)
    write_minimal_pdf(root.parent / "materials/source-demo-book/lecture-01.pdf",
                      ["expected-value lecture"])


def _valid_dossier(root: Path, route_id: str, locator: str) -> dict:
    from learning_os.material_synthesis import current_unit_material_basis

    basis = current_unit_material_basis(root, "unit-demo-l01")
    basis = {**basis, "ai_provenance": {
        "request_id": "ai-request-slice-demo",
        "delivery_id": "ai-delivery-demo",
        "provider": "manual-bundle",
    }}
    checksum = basis["material_checksums"][route_id]
    return {
        "schema_version": 1,
        "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis",
        "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": basis,
        "route_assessments": [{
            "route_id": route_id,
            "source_id": "source-demo-book",
            "locator": locator,
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "A direct derivation of the weighted sum.",
            "assumptions": "Finite discrete outcomes are assumed.",
            "notation": "Uses uppercase X and lowercase outcome values.",
            "exercise_value": "Includes a small worked calculation.",
            "best_for": "Checking the lecture's core derivation.",
            "limitations": "Does not cover continuous variables.",
            "scope_of_absence": "lecture-01.pdf, PDF p. 1 of 1",
            "evidence": [{"locator": "lecture-01.pdf p.1",
                          "checksum": checksum}],
        }],
        "comparisons": [],
        "concept_groups": [
            {"concept_id": "concept-variance",
             "local_node_ids": ["knowledge-demo-outcomes"],
             "related_unit_ids": [],
             "bridge_note_ids": [],
             "narrative": "Outcomes feed later dispersion measures."},
            {"concept_id": "concept-expected-value",
             "local_node_ids": ["knowledge-demo-expectation"],
             "related_unit_ids": ["unit-demo-l01"],
             "bridge_note_ids": ["note-demo"],
             "narrative": "The local derivation is the canonical concept."},
        ],
    }


def _audit(mini_repo: Path) -> str:
    audit_rel = "work/active/workspace-demo/outputs/demo-coverage-audit.md"
    audit = mini_repo / audit_rel
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Complete demo coverage audit\n\n## Local inventory\n\nDone.\n\n"
        "## Linked inventory\n\nDone.\n\n## Completeness sign-off\n\nDone.\n",
        encoding="utf-8",
    )
    return audit_rel


def _plan_contract(audit_rel: str) -> dict:
    return {
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
    }


def _compact_revision(mini_repo: Path, **overrides) -> dict:
    revision = {
        "unit_id": "unit-demo-l01",
        "plan_contract": {
            "version": 1,
            "plan_template_version": 1,
            "coverage_audit": _audit(mini_repo),
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "route_changes": {"add": [], "update": [], "remove": []},
    }
    revision.update(overrides)
    return revision


def _compact_setup(mini_repo: Path):
    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    good = _valid_dossier(mini_repo, "route-demo-book", "lecture-01.pdf")
    from learning_os.material_synthesis import synthesis_destination
    synthesis_destination(mini_repo, "unit-demo-l01").write_text(
        yaml.safe_dump(good, sort_keys=False), encoding="utf-8")
    _audit(mini_repo)
    write_baseline(mini_repo, collect(mini_repo)[0], "unit revision fixture")
    return good
