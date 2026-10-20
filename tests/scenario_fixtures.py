"""Scenario fixtures: the rich_world characterization world (PLAN step 1.2).

``rich_world(root)`` layers the rich world onto an existing mini repository
(built by ``conftest.build_mini_repo``): the curriculum builders first, then
raw YAML only for families no builder covers. Every record validates, and
two builds are byte-identical: no clock or random values anywhere.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import materials_manifest
import yaml
from migrations.route_identity_v13 import plan_migration
from repo_builders import (
    add_manifest_fixtures,
    rich_fixture,
    seed_goal_ledger,
    write_minimal_pdf,
    write_yaml,
)

from learning_os.derive.abilities import ability_fingerprint
from learning_os.derive.semantics.lineage import (
    LEDGER_RELATIVE,
    dump_ledger,
    emit_route_covers,
)
from learning_os.domain.material_inventory import render_manifest
from learning_os.domain.material_refs import MATERIAL_FIELDS, unit_routes
from learning_os.store.loader import load_repo
from learning_os.store.materials.resolution import (
    project_material_resource,
    resolve_route_material_files,
)
from learning_os.store.warning_baseline import write_baseline

PENDING_STAGE_ID = "stage-demo-pending"
SECOND_WORKSPACE_ID = "workspace-second"
ANALYSIS_NOTE_ID = "note-demo-analysis"
ABILITY_ID = "ability-demo-derive"
SECOND_ABILITY_ID = "ability-demo-variance"
LEGACY_UNIT_ID = "unit-demo-l02"
FIXED_DAY = "2026-09-20"

#: Amendment (ag) item 1: the measured initial warning counter, stored as
#: fixture data. Never collected during the build: validation creates a
#: path-dependent generated receipt cache. A separate test collects on a
#: fresh completed fixture and requires exact equality.
INITIAL_WARNING_SIGNATURES: Counter = Counter({
    ("ROUTE-ID-MISSING",
     "curriculum/modules/module-demo/source-map.yaml"): 1,
    ("SELECTION-ROUTE-ID-MISSING",
     "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml"): 1,
    ("RUNTIME-REVIEW-MISSING",
     "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"): 1,
    ("URI-PROJECT", "projects/registry/project-demo.yaml"): 1,
    ("LOCATOR-VAGUE",
     "curriculum/modules/module-demo/source-map.yaml"): 2,
    ("ROUTE-ANGLE-DETAIL-MISSING",
     "curriculum/modules/module-demo/source-map.yaml"): 2,
    ("STAGE-NODE-UNLINKED",
     "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"): 1,
    # The scope rule reports stage resources the module's source map does
    # not declare at route level: the three demo-stage rows plus the
    # pending stage's own row.
    ("RESOURCE-SCOPE-UNBOUND",
     "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"): 4,
})

#: Amendment (ag) item 1: the fixture coverage-audit evidence, filed under
#: the workspace outputs/ so hygiene never flags it.
COVERAGE_AUDIT_RELATIVE = "work/active/workspace-demo/outputs/demo-coverage-audit.md"
COVERAGE_AUDIT_TEXT = (
    "# Demo coverage audit\n"
    "\n"
    "## Local\n"
    "The fixture route material is present.\n"
    "\n"
    "## Linked\n"
    "The registered Demo Book owns the selected route.\n"
    "\n"
    "## Completeness\n"
    "All fixture units and selected routes were reviewed.\n"
)


def _repair_manifest_fixtures(root: Path) -> None:
    # add_manifest_fixtures serves the shadow suites, which never validate:
    # its path row lacks two required keys, and four of its extra rows are
    # schema-invalid. Repair the required path; drop the invalid extras,
    # none of which is a §5.1 family.
    path_file = root / "work/active/workspace-demo/paths/path-demo.yaml"
    data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    data["type"] = "learning-path"
    data["area"] = "university"
    write_yaml(path_file, data)
    for rel in ("sources/collections/shelf.yaml",
                "curriculum/thematic-groups.yaml",
                "projects/aliases.yaml",
                "sources/topics.yaml"):
        (root / rel).unlink()


def _add_pending_stage(root: Path) -> None:
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    note_rel = ("curriculum/modules/module-demo/units/unit-demo-l01/stages/"
                f"{PENDING_STAGE_ID}/notes.md")
    (root / note_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / note_rel).write_text("", encoding="utf-8")
    data["stages"].append({
        "id": PENDING_STAGE_ID,
        "knowledge_node_id": "knowledge-demo-expectation",
        "title": "Apply expected value",
        "status": "pending",
        "objective": "Apply expected value to a worked example.",
        "done_when": ["Work the example."],
        "scope_triage": "required-now",
        "resources": [{"kind": "read", "label": "Demo Book §2",
                       "source_id": "source-demo-book", "locator": "§2"}],
        "working_note": note_rel,
        "attachments": [],
        "source_feedback": [],
    })
    write_yaml(map_path, data)


def _add_second_workspace(root: Path) -> None:
    ws = root / "work/active" / SECOND_WORKSPACE_ID
    ws.mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(
        "---\n"
        f"id: {SECOND_WORKSPACE_ID}\n"
        "type: workspace\n"
        "title: Second workspace\n"
        "created: 2026-07-17\n"
        "status: active\n"
        "concepts: [concept-expected-value]\n"
        "notes: [note-demo]\n"
        "---\n"
        "\n"
        "## Objective\n"
        "\n"
        "Second.\n"
        "\n"
        "## Current Scope\n"
        "\n"
        "Small.\n"
        "\n"
        "## Open Questions\n"
        "\n"
        "None.\n"
        "\n"
        "## Next Action\n"
        "\n"
        "Do the second thing.\n",
        encoding="utf-8")


def _add_inbox_drops(root: Path) -> None:
    (root / "work/inbox/note-drop.md").write_text(
        "# Dropped note\n\nUnrouted.\n", encoding="utf-8")
    pack = root / "work/inbox/pack"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "one.md").write_text("one\n", encoding="utf-8")
    (pack / "two.md").write_text("two\n", encoding="utf-8")


def _add_fixture_book(root: Path) -> Path:
    book = root.parent / "materials/source-demo-book/book.pdf"
    write_minimal_pdf(book, ["Fixture book for source-demo-book"])
    return book


def _add_analysis_note(root: Path, book: Path) -> None:
    digest = hashlib.sha256(book.read_bytes()).hexdigest()
    body = ("# Expected value — analysis of Demo Book §1\n"
            "\n"
            "The derivation weights every outcome by its probability.\n")
    body_bytes = body.encode("utf-8")
    meta = {
        "id": ANALYSIS_NOTE_ID,
        "type": "note",
        "role": "reference",
        "title": "Expected value — analysis of Demo Book §1",
        "created": "2026-09-21",
        "concepts": ["concept-expected-value"],
        "sources": ["source-demo-book"],
        "material_analysis": {
            "resolution": "resolved",
            "material": "source-demo-book/book.pdf",
            "recorded_source_digest": digest,
            "live_source_digest": digest,
            "inspected_range": {"start": 1, "end": 1},
            "frozen_input_sha256": hashlib.sha256(body_bytes).hexdigest(),
            "frozen_input_bytes": len(body_bytes),
            "source_id": "source-demo-book",
        },
    }
    path = root / "knowledge/notes/mathematics" / f"{ANALYSIS_NOTE_ID}.md"
    path.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip()
                    + "\n---\n\n" + body, encoding="utf-8")


def _add_path_stage_note(root: Path) -> None:
    # Amendment (w): the path stage carries a notes_path naming an existing,
    # non-empty note, so path.note.write has a success case. The note stays
    # inside the owning workspace (rules/curriculum.py PATH-NOTE-OWNER).
    path_file = root / "work/active/workspace-demo/paths/path-demo.yaml"
    data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    note_rel = "work/active/workspace-demo/paths/stage-demo-path-notes.md"
    for stage in data["stages"]:
        if stage.get("id") == "stage-demo-path":
            stage["notes_path"] = note_rel
    write_yaml(path_file, data)
    (root / note_rel).write_text(
        "# First step — path notes\n\nBegun.\n", encoding="utf-8")


def _add_second_path_stage(root: Path) -> None:
    # Amendment (w), second stage: the same learning path keeps a pending
    # stage with no notes_path, so the path.py:43 refusal stays reachable.
    # current_stage still names the active stage-demo-path.
    path_file = root / "work/active/workspace-demo/paths/path-demo.yaml"
    data = yaml.safe_load(path_file.read_text(encoding="utf-8"))
    data["stages"].append({
        "id": "stage-demo-path-next",
        "title": "Second step",
        "status": "pending",
        "objective": "Continue the path.",
        "done_when": ["Continued."],
    })
    write_yaml(path_file, data)


def _add_runtime_target(root: Path) -> None:
    # Amendment (w): the active stage of the unit's current study map
    # carries a runtime_target, so collect_requirements returns one
    # requirement (req-demo-l01-demo) and the observation operations have
    # success cases. The stage has no `concepts`, so the concept is a
    # knowledge-node id of the unit, as the amendment allows.
    map_path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    for stage in data["stages"]:
        if stage.get("id") == "stage-demo":
            stage["runtime_target"] = {
                "concept": "knowledge-demo-expectation",
                "capability": {"kind": "explain", "operands": ["expectation"]},
                "conditions": ["unfamiliar-example"],
                "evidence_spec": ["explain-reason"],
            }
    write_yaml(map_path, data)


def _add_ability(root: Path) -> None:
    ability = {
        "id": ABILITY_ID,
        "title": "Derive expected value",
        "claim": "Derive expectation from stated outcomes.",
        "conditions": ["finite discrete outcomes", "probabilities sum to one"],
        "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-expected-value"],
        "module_ids": ["module-demo"],
        "preparation_routes": [],
        "review": {"state": "reviewed", "reviewed_by": "fixture",
                   "reviewed_on": "2026-09-23"},
    }
    write_yaml(root / "knowledge/abilities.yaml",
               {"abilities": [ability], "bridges": []})
    row = {
        "id": "ability-observation-1",
        "ability_id": ABILITY_ID,
        "ability_sha256": ability_fingerprint(ability),
        "claim": "I derived this from the stated problem.",
        "work_ref": "conversation://fixture/work-1",
        "confirmation_ref": "conversation://fixture/confirmation-1",
        "activity": "worked derivation",
        "result": "correct",
        "timestamp": "2026-09-23T10:01:00Z",
        "conditions": list(ability["conditions"]),
        "evidence_tags": list(ability["evidence_spec"]),
        "assistance": "none",
        "confirmed_by": "learner",
    }
    (root / "work/active/workspace-demo/ability-observations.jsonl").write_text(
        json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")


def _add_goal_ledger(root: Path) -> dict[str, str]:
    decisions = {"goal-demo-deferred": "deferred", "goal-demo-rejected": "rejected"}
    path = seed_goal_ledger(root, decisions)
    # seed_goal_ledger stamps today; pin the clock for determinism.
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in data["decisions"].values():
        entry["decided_at"] = FIXED_DAY
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return decisions


def _apply_route_migration(root: Path) -> None:
    # Amendment (y) item 1(a): the fixture is pre-Data-Contract-v13, so
    # every planned route-id insertion is written, exactly as the
    # migration test drives plan_migration. Ids are never hand-written.
    plan = plan_migration(root)
    if not plan.ready:
        raise RuntimeError(
            "route migration is not ready on the scenario fixture: "
            + "; ".join(f"{p.code} {p.path}: {p.detail}"
                        for p in plan.problems))
    for change in plan.changes:
        change.path.write_text(change.after, encoding="utf-8")


def _add_legacy_unit(root: Path) -> None:
    # Amendment (y) item 1(b): a second unit in module-demo with one
    # route and no id, added after step (a) so the migration never sees
    # it. It keeps material_synthesis.py:159 reachable. No study map:
    # a unit without one and without current_study_map validates.
    unit_dir = root / "curriculum/modules/module-demo/units" / LEGACY_UNIT_ID
    write_yaml(unit_dir / "unit.yaml", {
        "id": LEGACY_UNIT_ID, "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2,
        "scope": "The follow-up lecture as taught.", "status": "active",
        "scope_sources": [{"source_id": "source-demo-book",
                           "authority": "slides", "locator": "Lecture 2"}],
        "source_selections": [{"source_id": "source-demo-book",
                               "locator": "lecture-02.pdf",
                               "purpose": "Follow-up derivation"}],
        "artifacts": {"ultimate_reference": "note-demo"},
        "workspace_ids": ["workspace-demo"],
        "knowledge_map": {
            "summary": "Variance measures the spread around the expected value.",
            "nodes": [{
                "id": "knowledge-demo-variance",
                "title": "Spread around the mean",
                "summary": "Variance weights squared deviations by probability.",
                "concept_ids": ["concept-variance"],
            }],
        },
    })
    module_path = root / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append(LEGACY_UNIT_ID)
    write_yaml(module_path, module)
    smap_path = root / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    smap["sources"][0]["unit_routes"].append({
        "unit_id": LEGACY_UNIT_ID,
        "title": "Demo book — variance derivation",
        "format": "book",
        "angle": "Derives variance and works a discrete example.",
        "covers": ["knowledge-demo-variance"],
        "depth": "derivation",
        "scope": "current",
        "locator": "lecture-02.pdf",
    })
    write_yaml(smap_path, smap)


def _add_second_ability(root: Path) -> None:
    # Amendment (y) item 1(c): ability.candidate.append needs two
    # distinct active abilities (abilities.py:208-213). No lifecycle key
    # means active, as for the first ability.
    path = root / "knowledge/abilities.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["abilities"].append({
        "id": SECOND_ABILITY_ID,
        "title": "Derive variance",
        "claim": "Derive variance from stated outcomes.",
        "conditions": ["finite discrete outcomes",
                       "probabilities sum to one"],
        "evidence_spec": ["correct derivation"],
        "concept_ids": ["concept-variance"],
        "module_ids": ["module-demo"],
        "preparation_routes": [],
        "review": {"state": "reviewed", "reviewed_by": "fixture",
                   "reviewed_on": "2026-09-23"},
    })
    write_yaml(path, data)


def _add_lineage_claim(root: Path) -> str:
    # Amendment (y) item 1(d): one route-covers claim lineage.restamp can
    # apply to. seed_live_goal_ids only emits scope-authority claims,
    # which analyze() excludes, so the claim is a judged old-shape
    # covers claim with its judging receipt, mirroring
    # tests/test_lineage_restamp.py:_judged_repo. Runs last: the receipt
    # pins the final source-map and unit bytes.
    smap_path = root / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    route_id = smap["sources"][0]["unit_routes"][0]["id"]
    claim = emit_route_covers(
        route_id=route_id,
        covers=["knowledge-demo-expectation", "knowledge-demo-outcomes"],
        read_revisions={"module-demo": 1, "unit-demo-l01": 1},
        judged_by="operator/operator-approval",
        admitted_by={"request_id": "request-demo",
                     "idempotency_key": "demo-key"},
        evidence=[],
    )
    ledger_path = root / LEDGER_RELATIVE
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(dump_ledger({claim.claim_id: claim}),
                           encoding="utf-8")
    smap_rel = "curriculum/modules/module-demo/source-map.yaml"
    unit_rel = "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    intent = "sha256:" + "1" * 64
    receipt_id = "transaction-20200102-000000-001"
    write_yaml(root / "operations" / "transactions" / f"{receipt_id}.yaml", {
        "schema_version": 2, "id": receipt_id,
        "type": "transaction-receipt",
        "status": "committed", "capability": "module.plan.import",
        "committed_at": "2020-01-02T03:04:05+00:00",
        "snapshot_before": intent, "snapshot_after": intent,
        "expected_revisions": {"module-demo": 0, "unit-demo-l01": 0},
        "artifact_revisions": {
            "module-demo": {"before": 0, "after": 1},
            "unit-demo-l01": {"before": 0, "after": 1}},
        "request": {"channel": "operator", "request_id": "request-demo",
                    "idempotency_key": "demo-key",
                    "intent_sha256": intent,
                    "approval": {"kind": "operator-approval",
                                 "subject_sha256": intent}},
        "authority": {"capability_contract_version": 2, "enforced": True,
                      "grants": [{"capability": "module.plan.import",
                                  "declared_writes":
                                      ["curriculum/modules/**"]}]},
        "metadata": {},
        "writes": [
            {"path": smap_rel, "sha256_before": None, "created": False,
             "sha256_after": hashlib.sha256(
                 (root / smap_rel).read_bytes()).hexdigest()},
            {"path": unit_rel, "sha256_before": None, "created": False,
             "sha256_after": hashlib.sha256(
                 (root / unit_rel).read_bytes()).hexdigest()},
        ],
    })
    return claim.claim_id


#: Distinct extractable lines for the l01 route material (amendment (z)
#: item 2): a 20-page lecture plus a 4-page worked example the default
#: first pass leaves unread. Plain ASCII, parentheses-safe, one per page.
ROUTE_MATERIAL_TEXTS = [
    "Expected value, page 1 of 24: an outcome is a value a variable can take",
    "Expected value, page 2 of 24: probability weights every outcome",
    "Expected value, page 3 of 24: weights are nonnegative and sum to one",
    "Expected value, page 4 of 24: expectation is the weighted sum",
    "Expected value, page 5 of 24: E of X brackets the variable",
    "Expected value, page 6 of 24: a fair die expects three and a half",
    "Expected value, page 7 of 24: linearity splits sums of variables",
    "Expected value, page 8 of 24: constants factor out of expectation",
    "Expected value, page 9 of 24: independence factors products",
    "Expected value, page 10 of 24: variance squares the deviations",
    "Expected value, page 11 of 24: standard deviation restores the units",
    "Expected value, page 12 of 24: conditioning partitions the sample space",
    "Expected value, page 13 of 24: the tower rule nests the conditioning",
    "Expected value, page 14 of 24: indicator variables count events",
    "Expected value, page 15 of 24: the collector sums harmonic waits",
    "Expected value, page 16 of 24: symmetry argues without summing",
    "Expected value, page 17 of 24: Jensen bends convex transforms upward",
    "Expected value, page 18 of 24: Markov bounds the tail by the mean",
    "Expected value, page 19 of 24: Chebyshev squares the deviation bound",
    "Expected value, page 20 of 24: the first pass ends here, example unread",
    "Worked example part 1 of 4: a biased coin pays two on heads",
    "Worked example part 2 of 4: heads lands with probability three quarters",
    "Worked example part 3 of 4: expectation is one and three quarters",
    "Worked example part 4 of 4: check by enumerating both outcomes",
]


def _add_route_material(root: Path) -> Path:
    # Amendment (z) item 2: the material file unit-demo-l01's route
    # locator resolves to. The exact materials path comes from
    # project_material_resource, never guessed: the locator is a strict
    # safe path, so material_path is published even before the file
    # exists. Runs after the migration so the route carries its id, and
    # before the lineage claim so that step stays last.
    repo = load_repo(root)
    (route,) = unit_routes(repo.module_source_maps["module-demo"],
                           "module-demo", "unit-demo-l01")
    projected = project_material_resource(repo, route)
    target = repo.learningos_root / projected["material_path"]
    write_minimal_pdf(target, ROUTE_MATERIAL_TEXTS)
    resolved = resolve_route_material_files(repo, route)
    assert len(resolved) == 1 \
        and resolved[0].path.resolve() == target.resolve(), \
        f"route material did not resolve to the written file: {resolved}"
    return target


def _add_shelf(root: Path) -> None:
    # Amendment (ag) item 1: a schema-valid catalogue over the registered
    # Demo Book. Never restores the invalid `id` key the repair dropped.
    write_yaml(root / "sources/collections/shelf.yaml", {
        "title": "Scenario shelf", "collection_kind": "catalogue",
        "entries": [{"source": "source-demo-book", "group": "Demo",
                     "why": "The main demo reading."}],
    })


def _add_coverage_audit(root: Path) -> None:
    # Amendment (ag) item 1: fixture evidence only. Filed under
    # outputs/ so the hygiene sweep never flags it.
    path = root / COVERAGE_AUDIT_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(COVERAGE_AUDIT_TEXT, encoding="utf-8")


def _add_route_mirror(root: Path) -> None:
    # Amendment (ag) item 1: one uncompacted resource on the active
    # stage-demo, appended after the existing resources so their indices
    # hold. Every MATERIAL_FIELDS value present on the l01 route is
    # copied into its resource spelling; the mirror compacts losslessly.
    repo = load_repo(root)
    (route,) = unit_routes(repo.module_source_maps["module-demo"],
                           "module-demo", "unit-demo-l01")
    map_path = root / ("curriculum/modules/module-demo/units/unit-demo-l01"
                       "/study-map.yaml")
    data = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    (stage,) = [row for row in data["stages"]
                if row.get("id") == "stage-demo"]
    stage["resources"].append({
        "id": "resource-demo-route-mirror", "kind": "read",
        **{field: route[owner]
           for field, owner in MATERIAL_FIELDS.items()
           if owner in route},
    })
    assert stage["resources"][-1]["source_id"] == "source-demo-book"
    write_yaml(map_path, data)


def _add_attached_material(root: Path) -> Path:
    # Amendment (ag) item 1: the intake-create then attach journey's
    # target bytes. `nope.pdf` stays absent.
    book = root.parent / "materials/source-demo-book/book.pdf"
    target = root.parent / "materials/source-scenario-bare/attached.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(book.read_bytes())
    return target


def _add_materials_manifest(root: Path) -> None:
    # Amendment (ag) item 1: the existing inventory producer and
    # renderer; only `captured` is fixed for determinism.
    manifest = materials_manifest.build(root.parent / "materials")
    manifest["captured"] = FIXED_DAY
    (root / "records/materials-manifest.yaml").write_text(
        render_manifest(manifest), encoding="utf-8")


def _add_warning_baseline(root: Path) -> None:
    # Amendment (ag) item 1: the production serializer over the stored
    # measured counter. Only the date observation is fixed, inside this
    # call; the patch restores the function on exit.
    fixed = datetime.date(2026, 9, 20)
    with patch("learning_os.store.warning_baseline.observations.today",
               return_value=fixed):
        write_baseline(
            root, INITIAL_WARNING_SIGNATURES,
            "Measured initial rich_world content; "
            "no candidate writes included.")


def rich_world(root: Path) -> dict:
    """Layer the rich characterization world onto a mini repository.

    ``root`` is a ``build_mini_repo`` product. Returns the world's named
    ids for test use.
    """
    route_id, _route = rich_fixture(root)
    add_manifest_fixtures(root)
    _repair_manifest_fixtures(root)
    _add_pending_stage(root)
    _add_runtime_target(root)
    _add_path_stage_note(root)
    _add_second_path_stage(root)
    _add_second_workspace(root)
    _add_inbox_drops(root)
    book = _add_fixture_book(root)
    _add_analysis_note(root, book)
    _add_ability(root)
    _add_goal_ledger(root)
    _apply_route_migration(root)
    _add_legacy_unit(root)
    _add_second_ability(root)
    _add_route_material(root)
    claim_id = _add_lineage_claim(root)
    _add_shelf(root)
    _add_coverage_audit(root)
    _add_route_mirror(root)
    _add_attached_material(root)
    _add_materials_manifest(root)
    _add_warning_baseline(root)
    return {
        "module": "module-demo",
        "unit": "unit-demo-l01",
        "unit_legacy": LEGACY_UNIT_ID,
        "study_map": "study-map-demo-l01",
        "stage_active": "stage-demo",
        "stage_pending": PENDING_STAGE_ID,
        "route": route_id,
        "source": "source-demo-book",
        "workspace": "workspace-demo",
        "workspace_second": SECOND_WORKSPACE_ID,
        "path": "path-demo",
        "project": "project-demo",
        "ability": ABILITY_ID,
        "ability_second": SECOND_ABILITY_ID,
        "lineage_claim": claim_id,
        "note_synthesis": "note-demo",
        "note_analysis": ANALYSIS_NOTE_ID,
        "concept": "concept-expected-value",
        "goal_deferred": "goal-demo-deferred",
        "goal_rejected": "goal-demo-rejected",
        "ai_request": "ai-request-demo",
        "material": "material://source-demo-book/book.pdf",
    }
