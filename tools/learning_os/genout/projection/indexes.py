"""The lookup tables interfaces navigate by, derived from projected records.

Every table here answers a question an interface would otherwise answer by
scanning the whole record list. They are derived from the projection, never
from the tree — an index that read the repository directly could disagree with
the records shipped beside it.
"""

from __future__ import annotations

from ...loader import Repo


def build_indexes(repo: Repo, records: list[dict], *, modules_v2: list[dict],
                  units_v2: list[dict], study_maps_v2: list[dict],
                  source_maps_v2: list[dict], projects_v2: list[dict],
                  project_relationships_v2: list[dict]) -> dict:
    module_to_units = {
        module["id"]: [uid for uid in module.get("unit_order", []) if uid]
        for module in modules_v2
    }
    unit_to_study_map = {
        unit["id"]: unit.get("current_study_map")
        for unit in units_v2 if unit.get("current_study_map")
    }
    component_to_units: dict[str, list[str]] = {}
    source_to_modules: dict[str, list[str]] = {}
    source_to_units: dict[str, list[str]] = {}
    workspace_to_modules: dict[str, list[str]] = {}
    workspace_to_units: dict[str, list[str]] = {}
    project_to_units: dict[str, list[str]] = {
        project["id"]: list(project.get("unit_ids", []) or []) for project in projects_v2
    }
    project_to_workspaces: dict[str, list[str]] = {
        project["id"]: list(project.get("workspace_ids", []) or []) for project in projects_v2
    }
    project_to_relationships: dict[str, list[str]] = {
        project["id"]: [
            relation["id"] for relation in project_relationships_v2
            if relation.get("from_project_id") == project["id"]
        ]
        for project in projects_v2
    }
    for unit in units_v2:
        if unit.get("component_id"):
            component_to_units.setdefault(unit["component_id"], []).append(unit["id"])
        for scoped in unit.get("scope_sources", []) or []:
            if scoped.get("source_id"):
                source_to_units.setdefault(scoped["source_id"], []).append(unit["id"])
        for selection in unit.get("source_selections", []) or []:
            if selection.get("source_id"):
                source_to_units.setdefault(selection["source_id"], []).append(unit["id"])
    for source_map in source_maps_v2:
        mid = source_map.get("module_id")
        for entry in source_map.get("sources", []) or []:
            sid = entry.get("source_id")
            if sid:
                source_to_modules.setdefault(sid, []).append(mid)
            for uid in entry.get("unit_routes", []) or []:
                source_to_units.setdefault(sid, []).append(uid)
    for study_map in study_maps_v2:
        module_id = study_map.get("module_id")
        for stage in study_map.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id")
                if sid:
                    source_to_units.setdefault(sid, []).append(study_map["unit_id"])
                    # ADR-009 "Current use" means either the module source-map
                    # routes the source OR a stage actually uses it. library.py
                    # already follows that rule; the machine projection must
                    # publish the same fact instead of forcing the UI to recover
                    # module identity indirectly through source_to_units.
                    if module_id:
                        source_to_modules.setdefault(sid, []).append(module_id)
    for workspace in [r for r in records
                      if r.get("type") == "workspace" and not r.get("archived")]:
        workspace_to_modules[workspace["id"]] = list(workspace.get("module_ids", []) or [])
        workspace_to_units[workspace["id"]] = list(workspace.get("unit_ids", []) or [])
    for table in (component_to_units, source_to_modules, source_to_units,
                  workspace_to_modules, workspace_to_units, project_to_units,
                  project_to_workspaces, project_to_relationships):
        for key in table:
            table[key] = sorted(set(table[key]))
    return {
        "module_to_units": module_to_units,
        "unit_to_study_map": unit_to_study_map,
        "component_to_units": dict(sorted(component_to_units.items())),
        "source_to_modules": dict(sorted(source_to_modules.items())),
        "source_to_units": dict(sorted(source_to_units.items())),
        "workspace_to_modules": dict(sorted(workspace_to_modules.items())),
        "workspace_to_units": dict(sorted(workspace_to_units.items())),
        "project_to_units": dict(sorted(project_to_units.items())),
        "project_to_workspaces": dict(sorted(project_to_workspaces.items())),
        "project_to_relationships": dict(sorted(project_to_relationships.items())),
        "project_aliases": dict(sorted(repo.project_aliases.items())),
    }
