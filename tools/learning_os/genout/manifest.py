"""The atomic v2 projection every interface reads.

The per-domain rules live in ``genout/projection``; what remains here is the
assembly — which projectors run, in what order their records appear, and the
exact shape published under the contract. That shape is the interface, so it is
worth being able to read it on one screen.
"""

from __future__ import annotations

from ..contracts.manifest_contract import (
    declared_schema_sha256,
    declared_version,
    enforce,
)
from ..errors import TransactionFailure, unreadable_refusal
from ..fingerprint import source_fingerprint
from ..garden import project_garden_entries
from ..loader import Repo
from ..revisions import load_revisions
from .common import _git_state, _json_header
from .coordination import adoption_counts
from .modules_view import _academic_deadlines
from .projection import (
    build_counts,
    build_indexes,
    build_module_concept_edges,
    build_progress,
    project_collections,
    project_concepts,
    project_coordination,
    project_learning_paths,
    project_module_source_maps,
    project_modules,
    project_notes,
    project_programs,
    project_project_aliases,
    project_project_relationships,
    project_projects,
    project_sources,
    project_study_maps,
    project_thematic_groups,
    project_topics,
    project_unit_material_syntheses,
    project_units,
    project_workspaces,
    unit_to_project_ids,
)
from .review import build_review_items


def build_manifest(repo: Repo, generated_at: str, backlinks: dict | None = None,
                   enforce_contract: bool = True) -> dict:
    """The COMPLETE machine-readable projection of the repository (ADR-001):
    every canonical record (notes incl. attachments/evidence/contexts, concepts,
    sources, modules incl. attempts, workspaces, coordination) plus all
    relations. A consumer needing repository state should read this file, not
    parse the tree.

    ADR-006 addendum (2026-08-03, fourth): this is also the INTERFACE contract.
    Every field an interface would otherwise re-derive by parsing Markdown or
    YAML is projected here — workspace `next_action`/`objective`, source
    `url`/`material`/`evaluations`, note `domain`/`summary`, and structured
    `academic_deadlines`. Usability lives in the interface; deriving meaning
    stays here, once. If a UI needs to regex a canonical file, that is a
    manifest bug.

    One fact, one shape: where a projection could be expressed two ways the
    manifest carries exactly one. `academic_deadlines` replaced the narrower
    `exam_spine` key (2026-08-03), and `stages` is the flat by-id index for
    stage lookup while `study_maps[].stages` stays the ordering authority —
    an index plus an ordered list, never two copies of the same access path."""
    if repo.parse_failures:
        raise TransactionFailure(unreadable_refusal(repo.root, repo.parse_failures, "publish the manifest"))

    all_artifact_revisions = load_revisions(repo.root)
    # The shared revision ledger also protects deliberately opened quarantine
    # transactions. Those tokens are gateway concurrency state, not normal
    # LearningOS projection data: exposing their candidate/catalog IDs here
    # would leak Future Master's Planning into the ordinary manifest even when
    # every authored quarantine file is correctly ignored by the loader.
    master_planning_revision_prefixes = (
        "candidate-module-",
        "candidate-source-",
        "candidate-comparison-",
        "master-planning-",
        "master-promotion-",
    )
    artifact_revisions = {
        artifact_id: revision
        for artifact_id, revision in all_artifact_revisions.items()
        if not artifact_id.startswith(master_planning_revision_prefixes)
    }

    def projected_revision(record_id: str, data: dict | None = None) -> int:
        embedded = (data or {}).get("revision", 0)
        return artifact_revisions.get(record_id, embedded if isinstance(embedded, int) else 0)

    thematic_groups = project_thematic_groups(repo)
    topics_v2 = project_topics(repo)
    unit_to_projects = unit_to_project_ids(repo)
    unit_material_syntheses_v2 = project_unit_material_syntheses(repo)
    source_maps_v2 = project_module_source_maps(repo, projected_revision)

    # Record order is part of the published file. Each projector owns one
    # domain's shape; this list owns the sequence they appear in.
    records: list[dict] = [
        *project_notes(repo),
        *project_concepts(repo),
        *project_sources(repo, projected_revision),
        *project_projects(repo, projected_revision),
        *project_project_relationships(repo),
        *project_project_aliases(repo),
        *project_modules(repo, projected_revision),
        *project_collections(repo, projected_revision),
        *project_workspaces(repo, projected_revision),
        *project_learning_paths(repo, projected_revision),
        *project_programs(repo, projected_revision),
        *project_units(repo, projected_revision, unit_to_projects),
        *project_study_maps(repo, projected_revision, source_maps_v2),
        *source_maps_v2,
        *unit_material_syntheses_v2,
        *project_coordination(repo),
    ]
    relations = [
        {"from": r.get("from"), "type": r.get("type"), "to": r.get("to"),
         "context": r.get("context"), "source": r.get("source")}
        for r in sorted(repo.relations,
                        key=lambda r: (str(r.get("from")), str(r.get("type")), str(r.get("to"))))
    ]
    ad = adoption_counts(repo)
    fingerprint = source_fingerprint(repo)
    revision, dirty = _git_state(repo.root)
    generated_meta = _json_header(generated_at)
    generated_meta.update({
        # Read from system/contracts/manifest-contract.yaml, never hardcoded:
        # the version announced and the shape declared must have one source.
        "contract_version": declared_version(repo.root),
        "schema_sha256": declared_schema_sha256(repo.root),
        "snapshot_id": f"sha256:{fingerprint}",
        "source_fingerprint": fingerprint,
        "source_revision": revision,
        "source_dirty": dirty,
    })
    programs_v2 = [r for r in records if r.get("type") == "program"]
    projects_v2 = [r for r in records if r.get("type") == "project"]
    project_relationships_v2 = [
        r for r in records if r.get("type") == "project-relationship"
    ]
    modules_v2 = [r for r in records if r.get("type") == "module"]
    units_v2 = [r for r in records if r.get("type") == "unit"]
    study_maps_v2 = [r for r in records if r.get("type") == "study-map"]
    source_maps_v2 = [r for r in records if r.get("type") == "module-source-map"]
    topic_packs_v2 = [r for r in records if r.get("type") == "topic-pack"]
    stages_v2 = [
        {**stage, "study_map_id": study_map["id"],
         "unit_id": study_map["unit_id"], "module_id": study_map["module_id"]}
        for study_map in study_maps_v2 for stage in study_map.get("stages", [])
    ]
    module_concept_edges = build_module_concept_edges(
        modules=modules_v2, units=units_v2, stages=stages_v2,
        concepts=repo.concepts,
    )
    indexes = build_indexes(
        repo, records,
        modules_v2=modules_v2, units_v2=units_v2, study_maps_v2=study_maps_v2,
        source_maps_v2=source_maps_v2, projects_v2=projects_v2,
        project_relationships_v2=project_relationships_v2,
        unit_material_syntheses_v2=unit_material_syntheses_v2,
        module_concept_edges=module_concept_edges,
    )
    progress = build_progress(modules_v2, units_v2, study_maps_v2)
    semesters_v2 = [
        {**semester, "program_id": program["id"]}
        for program in programs_v2 for semester in program.get("semesters", []) or []
    ]
    inbox_dir = repo.root / "work" / "inbox"
    inbox_items = len([
        item for item in inbox_dir.iterdir() if not item.name.startswith(".")
    ]) if inbox_dir.is_dir() else 0
    # Garden existence and basic metadata are Core facts. Optional AI state may
    # enrich these rows, but cannot own or erase them.
    garden_entries = project_garden_entries(repo)

    # Review membership is also a Core decision. Interfaces render these
    # records; they do not reconstruct queues from counts or filesystem walks.
    review_items = build_review_items(
        repo,
        units_v2,
        study_maps_v2,
    )

    # AI action state remains an optional additive subsystem.
    from learning_os.ai_actions.projection import project_ai_actions
    ai_projection = project_ai_actions(repo)
    payload = {
        "_generated": generated_meta,
        "records": records,
        "relations": relations,
        # Backlinks are part of the SAME atomic manifest snapshot. The legacy
        # backlinks.json remains as a compatibility view, but interfaces never
        # need to race two separately-written files again.
        "backlinks": {k: v for k, v in (backlinks or {}).items() if k != "_generated"},
        # Interface convenience: every academic date an interface can render
        # with no Python running at all — registered attempts, available
        # sittings that have no attempt yet, and grouped registration windows,
        # already ordered. `_academic_deadlines` correlates attempts with
        # `examination.sittings` here so no interface repeats that rule.
        #
        # There is deliberately no separate `exam_spine` key: it was a strict
        # subset of this list (registered attempts only) and a second shape for
        # the same facts. `exam_spine` survives as the helper behind
        # the Markdown views and `los.py status --json` (ADR-006, 2026-08-03).
        "academic_deadlines": _academic_deadlines(repo),
        "thematic_groups": thematic_groups,
        "topics": topics_v2,
        "topic_packs": topic_packs_v2,
        "projects": projects_v2,
        "project_relationships": project_relationships_v2,
        "project_aliases": dict(sorted(repo.project_aliases.items())),
        "artifact_revisions": dict(sorted(artifact_revisions.items())),
        "programs": programs_v2,
        "semesters": semesters_v2,
        "modules": modules_v2,
        "units": units_v2,
        "study_maps": study_maps_v2,
        "stages": stages_v2,
        "module_concept_edges": module_concept_edges,
        "module_source_maps": source_maps_v2,
        "unit_material_syntheses": unit_material_syntheses_v2,
        "resume_pointer": dict(repo.resume_pointer or {}),
        "garden_entries": garden_entries,
        "review_items": review_items,
        "ai_actions": ai_projection["ai_actions"],
        "indexes": indexes,
        "progress": progress,
        "counts": build_counts(
            repo,
            thematic_groups=thematic_groups, topics_v2=topics_v2,
            topic_packs_v2=topic_packs_v2, projects_v2=projects_v2,
            programs_v2=programs_v2, modules_v2=modules_v2,
            units_v2=units_v2, stages_v2=stages_v2,
            inbox_items=inbox_items, garden_entries=garden_entries,
            ai_requests=ai_projection["ai_actions"]["requests"], adoption=ad,
        ),
    }
    # The published shape is a versioned interface, so the producer proves it
    # still matches what it announced. Adding a top-level key while continuing
    # to call the projection v2 is what turned UI CI red on 2026-08-08; that
    # class of mistake now fails here, in Core's own test run, instead of in a
    # downstream repository after the push.
    if enforce_contract:
        enforce(payload, repo.root)
    return payload
