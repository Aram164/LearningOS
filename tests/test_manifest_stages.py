"""Stage-1 manifest proof: the staged decomposition is behavior-preserving.

``build_manifest()`` is production-authoritative. These tests assemble the
same payload through the decomposed stage helpers directly and require
exact equality — dict-level and serialized-byte-level — with the
production path. No caching exists yet; this pins the refactor alone.
"""

from __future__ import annotations

import json
from functools import partial

from learning_os.garden import project_garden_entries
from learning_os.genout import generate_all
from learning_os.genout.concepts import build_backlinks
from learning_os.genout.coordination import adoption_counts
from learning_os.genout.manifest import (
    _projected_revision,
    assemble_manifest_semantic_payload,
    build_manifest,
    build_manifest_relations,
    build_manifest_semesters,
    build_manifest_stages,
    count_inbox_items,
    derive_manifest_collections,
    load_manifest_revisions,
    project_manifest_ai_actions,
    project_manifest_prerequisites,
    project_manifest_records,
    publish_manifest_metadata,
)
from learning_os.genout.modules_view import _academic_deadlines
from learning_os.genout.projection import (
    build_counts,
    build_indexes,
    build_module_concept_edges,
    build_progress,
)
from learning_os.genout.review import build_review_items
from learning_os.loader import load_repo


def _serialize_manifest(payload: dict) -> str:
    """Byte-exact manifest.json serialization, mirroring outputs.py."""
    return (
        json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def _assemble_via_stages(repo, generated_at, backlinks) -> dict:
    """Independent orchestration of the decomposed stage helpers."""
    artifact_revisions = load_manifest_revisions(repo.root)
    projected_revision = partial(_projected_revision, artifact_revisions)
    prerequisites = project_manifest_prerequisites(repo, projected_revision)
    records = project_manifest_records(
        repo,
        projected_revision,
        prerequisites["unit_to_projects"],
        prerequisites["source_maps"],
        prerequisites["unit_material_syntheses"],
    )
    relations = build_manifest_relations(repo)
    collections = derive_manifest_collections(records)
    stages = build_manifest_stages(collections["study_maps"])
    module_concept_edges = build_module_concept_edges(
        modules=collections["modules"],
        units=collections["units"],
        stages=stages,
        concepts=repo.concepts,
    )
    indexes = build_indexes(
        repo,
        records,
        modules_v2=collections["modules"],
        units_v2=collections["units"],
        study_maps_v2=collections["study_maps"],
        source_maps_v2=collections["module_source_maps"],
        projects_v2=collections["projects"],
        project_relationships_v2=collections["project_relationships"],
        unit_material_syntheses_v2=prerequisites["unit_material_syntheses"],
        module_concept_edges=module_concept_edges,
    )
    progress = build_progress(
        collections["modules"], collections["units"], collections["study_maps"]
    )
    ai_projection = project_manifest_ai_actions(repo)
    garden_entries = project_garden_entries(repo)
    counts = build_counts(
        repo,
        thematic_groups=prerequisites["thematic_groups"],
        topics_v2=prerequisites["topics"],
        topic_packs_v2=collections["topic_packs"],
        projects_v2=collections["projects"],
        programs_v2=collections["programs"],
        modules_v2=collections["modules"],
        units_v2=collections["units"],
        stages_v2=stages,
        inbox_items=count_inbox_items(repo.root),
        garden_entries=garden_entries,
        ai_requests=ai_projection["ai_actions"]["requests"],
        adoption=adoption_counts(repo),
    )
    semantic = assemble_manifest_semantic_payload(
        repo,
        backlinks,
        records=records,
        relations=relations,
        thematic_groups=prerequisites["thematic_groups"],
        topics_v2=prerequisites["topics"],
        artifact_revisions=artifact_revisions,
        collections=collections,
        stages_v2=stages,
        module_concept_edges=module_concept_edges,
        semesters_v2=build_manifest_semesters(collections["programs"]),
        unit_material_syntheses_v2=prerequisites["unit_material_syntheses"],
        garden_entries=garden_entries,
        review_items=build_review_items(
            repo, collections["units"], collections["study_maps"]
        ),
        ai_projection=ai_projection,
        indexes=indexes,
        progress=progress,
        counts=counts,
        project_aliases=repo.project_aliases,
        resume_pointer=repo.resume_pointer,
        academic_deadlines=_academic_deadlines(repo),
    )
    return {
        "_generated": publish_manifest_metadata(repo, generated_at),
        **semantic,
    }


def test_staged_assembly_matches_production_payload(mini_repo):
    repo = load_repo(mini_repo)
    backlinks = build_backlinks(repo, "T1")
    assert _assemble_via_stages(repo, "T1", backlinks) == build_manifest(
        repo, "T1", backlinks
    )


def test_staged_assembly_matches_production_bytes(mini_repo):
    repo = load_repo(mini_repo)
    backlinks = build_backlinks(repo, "T1")
    staged = _serialize_manifest(_assemble_via_stages(repo, "T1", backlinks))
    assert staged == generate_all(repo, "T1")["manifest.json"]


def test_metadata_covers_generated_and_nothing_else(mini_repo):
    repo = load_repo(mini_repo)
    payload = build_manifest(repo, "T1", build_backlinks(repo, "T1"))
    assert publish_manifest_metadata(repo, "T1") == payload["_generated"]


def test_semantic_payload_is_timestamp_independent(mini_repo):
    """Only _generated moves with the stamp; the semantic body is stable."""
    repo = load_repo(mini_repo)
    first = _assemble_via_stages(repo, "T1", build_backlinks(repo, "T1"))
    second = _assemble_via_stages(repo, "T2", build_backlinks(repo, "T2"))
    assert {k: v for k, v in first.items() if k != "_generated"} == {
        k: v for k, v in second.items() if k != "_generated"
    }
    assert first["_generated"] != second["_generated"]
