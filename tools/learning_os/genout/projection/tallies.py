"""Per-module progress and the repository-wide counts.

Both are summaries of the projection rather than facts of their own: nothing
here may be true unless the records shipped alongside say so.
"""

from __future__ import annotations

from ...loader import Repo


def build_progress(modules_v2: list[dict], units_v2: list[dict],
                   study_maps_v2: list[dict]) -> dict:
    progress = {}
    study_map_by_unit = {sm["unit_id"]: sm for sm in study_maps_v2}
    unit_by_id = {u["id"]: u for u in units_v2}
    for module in modules_v2:
        module_units = [unit_by_id[uid] for uid in module.get("unit_order", [])
                        if uid in unit_by_id]
        stage_rows = [stage for unit in module_units
                      for stage in (study_map_by_unit.get(unit["id"], {}).get("stages", []) or [])]
        progress[module["id"]] = {
            "units_total": len(module_units),
            "units_complete": sum(1 for unit in module_units if unit.get("status") == "complete"),
            "units_needing_map": sum(1 for unit in module_units if unit.get("needs_study_map")),
            "stages_total": len(stage_rows),
            "stages_complete": sum(1 for stage in stage_rows if stage.get("status") == "complete"),
        }
    return progress


def build_counts(repo: Repo, *, thematic_groups: list[dict], topics_v2: list[dict],
                 topic_packs_v2: list[dict], projects_v2: list[dict],
                 programs_v2: list[dict], modules_v2: list[dict], units_v2: list[dict],
                 stages_v2: list[dict], inbox_items: int,
                 garden_entries: list, ai_requests: list, adoption: dict) -> dict:
    return {
        "notes": len(repo.notes), "concepts": len(repo.concepts),
        "sources": len(repo.sources), "collections": len(repo.collections),
        "topic_packs": len(topic_packs_v2),
        "thematic_groups": len(thematic_groups),
        "topics": len(topics_v2),
        "sources_with_topics": sum(
            1 for s in repo.sources.values() if s.get("topics")),
        "projects": len(projects_v2),
        "modules": len(modules_v2),
        "workspaces_active": len(repo.active_workspaces()),
        "workspaces_archived": len(repo.archived_workspaces()),
        "learning_paths": len(repo.learning_paths),
        "learning_paths_active": sum(
            1 for p in repo.active_learning_paths() if p.status == "active"),
        "programs": len(programs_v2),
        "units": len(repo.units),
        "study_maps": len(repo.study_maps),
        "stages": len(stages_v2),
        "stages_complete": sum(1 for stage in stages_v2 if stage.get("status") == "complete"),
        "source_feedback_records": sum(
            len(stage.get("source_feedback", []) or []) for stage in stages_v2),
        "units_needing_map": sum(1 for unit in units_v2 if unit.get("needs_study_map")),
        "inbox_items": inbox_items,
        "garden_entries": len(garden_entries),
        "ai_action_requests": len(ai_requests),
        "relations": len(repo.relations),
        "notes_reviewed": adoption["notes_reviewed"],
        "notes_with_evidence": adoption["notes_with_evidence"],
    }
