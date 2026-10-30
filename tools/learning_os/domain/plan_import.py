"""Pure plan-package construction for module.plan.import / unit.plan.revise.

Moved verbatim from commands/module.py (PLAN 4.1, Task 82), re-derived
against the current tip. Every function here is pure over its inputs:
no repository reads, no gateway context, no orchestration. Handlers in
ops/handlers/plan.py own intake, gates, proposals and rendering.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from learning_os.domain.material_refs import MaterialReferenceError, expand_map
from learning_os.domain.route_identity import route_with_identity
from learning_os.domain.suggest import not_found

_COMPACT_STAGE_FIELDS = frozenset({
    "title", "objective", "done_when", "exam_critical", "concepts",
    "scope_triage", "resources", "runtime_target", "runtime_review",
})

_SOURCE_MAP_ROLES = frozenset({
    "course-material", "spine", "first-exposure", "intuition", "derivation",
    "implementation", "practice", "exam-preparation", "optional-depth",
    "reference", "candidate",
})

_COMPACT_JOIN_FIELDS = frozenset({"source_id", "role", "why", "priority", "when"})

UNIT_ROUTE_UPDATE_FIELDS = frozenset({
    "title", "format", "angle", "angle_detail", "covers", "depth", "scope",
    "locator", "url", "vault_path", "exposes_solutions_for", "requires_assets",
})

_INVENTORY_FENCE = "```inventory-v1"

INVENTORY_ROW_DISPOSITIONS = ("routed", "linked", "out-of-scope", "duplicate")


def source_map_routes(source_map: Any) -> dict[str, dict[str, Any]]:
    routes: dict[str, dict[str, Any]] = {}
    if not isinstance(source_map, dict):
        return routes
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        for route in source.get("unit_routes") or []:
            if isinstance(route, dict):
                identified = route_with_identity(str(source_map.get("module_id") or ""),
                                                 str(source.get("source_id") or ""), route)
                routes[str(identified["id"])] = identified
    return routes


def source_map_routes_with_source(
        source_map: Any) -> dict[str, tuple[str, dict[str, Any]]]:
    """Route id to (owning source id, row), for content-digest reads."""
    routes: dict[str, tuple[str, dict[str, Any]]] = {}
    if not isinstance(source_map, dict):
        return routes
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id") or "")
        for route in source.get("unit_routes") or []:
            if isinstance(route, dict):
                identified = route_with_identity(str(source_map.get("module_id") or ""), source_id, route)
                routes[str(identified["id"])] = (source_id, identified)
    return routes


def knowledge_node_rows(unit_data: Any) -> dict[str, dict[str, Any]]:
    """Knowledge node id to row for one unit mapping, or {} when absent."""
    if not isinstance(unit_data, dict):
        return {}
    knowledge = unit_data.get("knowledge_map")
    nodes = knowledge.get("nodes") if isinstance(knowledge, dict) else None
    if not isinstance(nodes, list):
        return {}
    rows = {}
    for node in nodes:
        if isinstance(node, dict) and str(node.get("id") or "").strip():
            rows[str(node["id"])] = node
    return rows


def inventory_block(audit_text: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse the structured inventory block, or (None, []) when absent."""
    opens = [i for i in range(len(audit_text))
             if audit_text.startswith(_INVENTORY_FENCE, i)]
    if not opens:
        return None, []
    if len(opens) > 1:
        return None, ["coverage audit carries more than one inventory-v1 block"]
    start = opens[0] + len(_INVENTORY_FENCE)
    close = audit_text.find("```", start)
    if close < 0:
        return None, ["coverage audit inventory-v1 block is never closed"]
    try:
        block = yaml.safe_load(audit_text[start:close])
    except yaml.YAMLError as exc:
        return None, [f"coverage audit inventory-v1 block is not YAML: {exc}"]
    if not isinstance(block, dict):
        return None, ["coverage audit inventory-v1 block must be a mapping"]
    return block, []


def inventory_view(block: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """The human audit view, generated from the structured rows."""
    local, linked = [], []
    for row in block.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("kind", "local") == "linked":
            linked.append({"reference": row.get("reference"),
                           "disposition": row.get("disposition"),
                           "observed": row.get("observed")})
        else:
            digest = row.get("sha256") or ""
            local.append({"path": row.get("path"),
                          "disposition": row.get("disposition"),
                          "sha256": digest[:12]})
    local.sort(key=lambda row: str(row.get("path")))
    linked.sort(key=lambda row: str(row.get("reference")))
    return {"local": local, "linked": linked}


def ack_shape_problems(acknowledgments: Any) -> list[str]:
    problems: list[str] = []
    if acknowledgments is None:
        return problems
    if not isinstance(acknowledgments, list):
        return ["acknowledgments must be a list"]
    for index, ack in enumerate(acknowledgments):
        where = f"acknowledgments[{index}]"
        if not isinstance(ack, dict):
            problems.append(f"{where} must be a mapping")
            continue
        for key in ("kind", "target", "reason"):
            value = ack.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{where}.{key} must be a nonempty string")
    return problems


def _relative_order_changed(before: list[str], after: list[str]) -> bool:
    """Return whether records present in both sequences changed relative order.

    Adding a new unit or stage is not a reorder. Moving existing records around
    the insertion is. That distinction lets plan expansion stay convenient
    while making accidental reshuffles fail closed.
    """
    shared = set(before) & set(after)
    return (
        [record_id for record_id in before if record_id in shared]
        != [record_id for record_id in after if record_id in shared]
    )


def _declared_reorders(package: dict[str, Any]) -> set[tuple[str, str]]:
    contract = package.get("plan_contract") or {}
    declarations = contract.get("intentional_reorders", []) or []
    return {
        (str(row.get("target")), str(row.get("id")))
        for row in declarations
        if isinstance(row, dict)
    }


def module_plan_ordering_problems(repo: Any, module_id: str,
                                   package: dict[str, Any]) -> list[str]:
    """Reject silent reordering while allowing explicit reviewed changes."""
    declared = _declared_reorders(package)
    actual_changes: set[tuple[str, str]] = set()
    problems: list[str] = []

    module_patch = package.get("module_patch", {}) or {}
    proposed_units = module_patch.get("unit_order")
    if isinstance(proposed_units, list):
        before_units = list(repo.modules[module_id].get("unit_order", []) or [])
        after_units = [str(record_id) for record_id in proposed_units]
        key = ("module-unit-order", module_id)
        if _relative_order_changed(before_units, after_units):
            actual_changes.add(key)
            if key not in declared:
                problems.append(
                    f"{module_id} reorders existing units; preserve their relative order or "
                    "declare an intentional module-unit-order change with a reason"
                )

    for entry in package.get("units", []) or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("unit"), dict):
            continue
        uid = entry["unit"].get("id")
        proposed_map = entry.get("study_map")
        if not isinstance(uid, str) or not isinstance(proposed_map, dict):
            continue
        current_unit = repo.units.get(uid)
        current_id = (
            current_unit.data.get("current_study_map")
            if current_unit is not None
            else None
        )
        current_map = repo.study_maps.get(current_id) if current_id else None
        if current_map is None:
            continue
        before_stages = [
            str(stage.get("id"))
            for stage in current_map.data.get("stages", []) or []
            if isinstance(stage, dict) and stage.get("id")
        ]
        after_stages = [
            str(stage.get("id"))
            for stage in proposed_map.get("stages", []) or []
            if isinstance(stage, dict) and stage.get("id")
        ]
        key = ("study-map-stage-order", str(current_map.id))
        if _relative_order_changed(before_stages, after_stages):
            actual_changes.add(key)
            if key not in declared:
                problems.append(
                    f"{current_map.id} reorders existing stages; plan expansion must preserve "
                    "their relative order unless an intentional study-map-stage-order change "
                    "is declared with a reason"
                )

    for target, record_id in sorted(declared - actual_changes):
        problems.append(
            f"intentional reorder declared for {target} {record_id}, but the package does not "
            "reorder existing records"
        )
    return problems


def _unit_source_refs(unit_data: dict[str, Any],
                      map_data: dict[str, Any] | None) -> set[str]:
    refs: set[str] = set()
    for field in ("scope_sources", "source_selections"):
        for entry in unit_data.get(field, []) or []:
            sid = entry.get("source_id") if isinstance(entry, dict) else None
            if isinstance(sid, str):
                refs.add(sid)
    if isinstance(map_data, dict):
        for stage in map_data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for field in ("resources", "source_feedback"):
                for entry in stage.get(field, []) or []:
                    sid = entry.get("source_id") if isinstance(entry, dict) else None
                    if isinstance(sid, str):
                        refs.add(sid)
    return refs


def _route_unit_id(route: object) -> str | None:
    if isinstance(route, str):
        return route
    if isinstance(route, dict):
        unit_id = route.get("unit_id")
        if isinstance(unit_id, str):
            return unit_id
    return None


def module_plan_routing_problems(repo: Any, module_id: str,
                                  package: dict[str, Any]) -> list[str]:
    """Catch source omissions that ordinary referential validation cannot see."""
    source_map = package.get("source_map")
    if source_map is None:
        source_map = repo.module_source_maps.get(module_id, {})
    routes: dict[str, set[str]] = {}
    source_entries = source_map.get("sources", []) if isinstance(source_map, dict) else []
    for entry in source_entries or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("source_id"), str):
            continue
        routed_units = {
            uid for route in (entry.get("unit_routes", []) or [])
            if (uid := _route_unit_id(route))
        }
        routes.setdefault(entry["source_id"], set()).update(routed_units)

    units: dict[str, tuple[dict[str, Any], dict[str, Any] | None]] = {}
    for uid, unit in repo.units.items():
        if unit.module_id != module_id:
            continue
        study_map = repo.study_maps.get(unit.data.get("current_study_map"))
        units[uid] = (unit.data, study_map.data if study_map else None)
    for entry in package.get("units", []) or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("unit"), dict):
            continue
        uid = entry["unit"].get("id")
        if isinstance(uid, str):
            units[uid] = (entry["unit"], entry.get("study_map"))

    problems: list[str] = []
    for uid, (unit_data, map_data) in sorted(units.items()):
        if isinstance(map_data, dict):
            try:
                map_data = expand_map(map_data, source_map, module_id, uid)
            except MaterialReferenceError as exc:
                problems.append(f"{uid}: {exc}")
                continue
        for sid in sorted(_unit_source_refs(unit_data, map_data)):
            if sid not in routes:
                problems.append(f"{uid} uses {sid}, but the module source map omits it")
            elif uid not in routes[sid]:
                problems.append(f"{uid} uses {sid}, but its source-map unit_routes omit the unit")
    for update in package.get("workspace_updates", []) or []:
        if not isinstance(update, dict):
            continue
        workspace = repo.workspaces.get(update.get("id"))
        if workspace is None or set(workspace.meta.get("module_ids", []) or []) != {module_id}:
            continue
        for sid in update.get("sources", []) or []:
            if sid not in routes:
                problems.append(
                    f"workspace {update.get('id')} lists {sid}, but the module source map omits it"
                )
    return problems


def synthesis_entries(module_id: str,
                       package: dict[str, Any]) -> tuple[list[tuple[str, dict[str, Any]]], list[str]]:
    """Split the optional atomic synthesis replacements from the package.

    Returns ``([(unit_id, dossier)], [problems])``. Shape problems are
    contract failures; an empty list with no problems means the package
    carries no replacements.
    """
    raw = package.get("material_syntheses", [])
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], ["material_syntheses must be a list"]
    entries: list[tuple[str, dict[str, Any]]] = []
    problems: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(raw):
        where = f"material_syntheses[{index}]"
        if not isinstance(row, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unit_id = row.get("unit_id")
        dossier = row.get("dossier")
        if not isinstance(unit_id, str) or not unit_id.strip():
            problems.append(f"{where}.unit_id must name a unit")
            continue
        if unit_id in seen:
            problems.append(f"{where} repeats unit {unit_id}")
            continue
        seen.add(unit_id)
        if not isinstance(dossier, dict):
            problems.append(f"{where}.dossier must be a mapping")
            continue
        if dossier.get("unit_id", unit_id) != unit_id:
            problems.append(f"{where}.dossier.unit_id does not match {unit_id}")
            continue
        entries.append((unit_id, dossier))
    return entries, problems


def assemble_compact_module_revision(repo: Any, module_id: str,
                                      revision: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """Expand reviewed unit deltas against one live snapshot for the existing import gate."""
    problems: list[str] = []
    allowed = {"module_id", "plan_contract", "unit_revisions", "source_joins",
               "claim_evidence", "acknowledgments", "unit_additions", "unit_move"}
    if set(revision) - allowed:
        problems.append(f"compact module revision has unknown fields: {sorted(set(revision) - allowed)}")
    if module_id not in repo.modules:
        problems.append(not_found("module", module_id, repo.modules))
    revisions = revision.get("unit_revisions", [])
    if not isinstance(revisions, list) or not (revisions or revision.get("unit_additions") or revision.get("unit_move")):
        problems.append("give unit_revisions, unit_additions or unit_move")
        return None, problems
    if problems:
        return None, problems
    source_map = copy.deepcopy(repo.module_source_maps.get(module_id) or {})
    joins = revision.get("source_joins")
    if joins is None:
        joins = []
    if not isinstance(joins, list):
        return None, ["source_joins must be a list"]
    joined_ids = {entry.get("source_id") for entry in source_map.get("sources", [])
                  if isinstance(entry, dict)}
    seen_joins: set[str] = set()
    for position, join in enumerate(joins):
        where = f"source_joins[{position}]"
        if not isinstance(join, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unknown = set(join) - _COMPACT_JOIN_FIELDS
        if unknown:
            problems.append(f"{where} has unknown fields: {sorted(unknown)}")
            continue
        sid = join.get("source_id")
        if not isinstance(sid, str) or not sid:
            problems.append(f"{where} needs a source_id")
            continue
        if sid not in repo.sources:
            problems.append(f"{where} joins a source that is not registered: {sid}")
            continue
        if sid in joined_ids:
            problems.append(f"{where} joins a source already joined to {module_id}: {sid}")
            continue
        if sid in seen_joins:
            problems.append(f"{where} joins the same source twice: {sid}")
            continue
        role = join.get("role")
        if role not in _SOURCE_MAP_ROLES:
            problems.append(f"{where} role {role!r} is not a source-map role")
            continue
        why = join.get("why")
        if not isinstance(why, str) or not why.strip():
            problems.append(f"{where} needs a non-empty 'why'")
            continue
        priority = join.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool) or priority < 0:
            problems.append(f"{where} 'priority' must be an integer >= 0")
            continue
        when = join.get("when")
        if when is not None and not isinstance(when, str):
            problems.append(f"{where} 'when' must be a string")
            continue
        seen_joins.add(sid)
        entry: dict[str, Any] = {"source_id": sid, "role": role, "why": why,
                       "priority": priority, "unit_routes": []}
        if when is not None:
            entry["when"] = when
        source_map.setdefault("sources", []).append(entry)
    if problems:
        return None, problems
    entries: list[dict[str, Any]] = []
    syntheses: list[dict[str, Any]] = []
    seen_units: set[str] = set()
    for index, item in enumerate(revisions):
        where = f"unit_revisions[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{where} must be a mapping")
            continue
        unknown = set(item) - {"unit_id", "route_changes", "stage_patches",
                               "material_synthesis"}
        if unknown:
            problems.append(f"{where} has unknown fields: {sorted(unknown)}")
        uid = item.get("unit_id")
        if not isinstance(uid, str) or uid in seen_units:
            problems.append(f"{where} needs a distinct unit_id")
            continue
        seen_units.add(uid)
        unit = repo.units.get(uid)
        if unit is None or unit.module_id != module_id:
            problems.append(f"{where} targets a unit outside {module_id}: {uid}")
            continue
        changes = item.get("route_changes", {})
        if not isinstance(changes, dict) or set(changes) - {"add", "update", "remove"}:
            problems.append(f"{where}.route_changes allows only add, update, remove")
            continue
        for kind in ("add", "update", "remove"):
            if not isinstance(changes.get(kind, []), list):
                problems.append(f"{where}.route_changes.{kind} must be a list")
        if problems:
            continue
        source_map, _, route_problems = apply_unit_route_changes(
            source_map, module_id, uid, changes)
        problems.extend(f"{where}: {problem}" for problem in route_problems)
        patches = item.get("stage_patches", [])
        if not isinstance(patches, list):
            problems.append(f"{where}.stage_patches must be a list")
            continue
        current_id = unit.data.get("current_study_map")
        current_map = repo.study_maps.get(current_id) if current_id else None
        if patches and current_map is None:
            problems.append(f"{where} has no current study map to patch")
            continue
        base_data = None
        if patches and current_map is not None:
            # An append patch carries authored placements forward, so the whole
            # map starts from the authored form; legacy patches keep the
            # expanded base they were reviewed against.
            if any(isinstance(patch, dict) and "resources_append" in patch
                   for patch in patches):
                base_data = current_map.authored_data or current_map.data
            else:
                base_data = current_map.data
        study_map = copy.deepcopy(base_data) if base_data is not None else None
        stages = {stage.get("id"): stage for stage in study_map.get("stages", [])
                  if isinstance(stage, dict)} if study_map else {}
        existing_ids = {row.get("id") for stage in stages.values()
                        for row in (stage.get("resources") or [])
                        if isinstance(row, dict)}
        existing_ids = {rid for rid in existing_ids if isinstance(rid, str)}
        seen_stages: set[str] = set()
        for stage_index, patch in enumerate(patches):
            stage_where = f"{where}.stage_patches[{stage_index}]"
            if not isinstance(patch, dict) or "stage_id" not in patch \
                    or set(patch) - {"stage_id", "fields", "resources_append"}:
                problems.append(f"{stage_where} needs stage_id plus fields and/or resources_append")
                continue
            sid = patch["stage_id"]
            fields = patch.get("fields")
            append = patch.get("resources_append")
            if fields is None and append is None:
                problems.append(f"{stage_where} changes nothing; give fields and/or resources_append")
                continue
            if not isinstance(sid, str) or sid in seen_stages or sid not in stages:
                problems.append(f"{stage_where} names a missing or repeated stage: {sid}")
                continue
            seen_stages.add(sid)
            if fields is not None:
                if not isinstance(fields, dict) or not fields or set(fields) - _COMPACT_STAGE_FIELDS:
                    problems.append(f"{stage_where}.fields must be non-empty and limited to "
                                    f"{sorted(_COMPACT_STAGE_FIELDS)}")
                    continue
                if append is not None and "resources" in fields:
                    problems.append(f"{stage_where} cannot combine resources_append with fields.resources")
                    continue
            if append is not None:
                if not isinstance(append, list) or not append \
                        or any(not isinstance(row, dict) for row in append):
                    problems.append(f"{stage_where}.resources_append must be a non-empty list of resource objects")
                    continue
                new_ids = [row.get("id") for row in append]
                if any(not isinstance(rid, str) or not rid for rid in new_ids):
                    problems.append(f"{stage_where}.resources_append needs a fresh resource id on every row")
                    continue
                if len(set(new_ids)) != len(new_ids):
                    problems.append(f"{stage_where}.resources_append repeats a resource id")
                    continue
                collisions = [rid for rid in new_ids if rid in existing_ids]
                if collisions:
                    problems.append(f"{stage_where}.resources_append reuses an existing resource id: {collisions[0]}")
                    continue
            if fields is not None:
                stages[sid].update(copy.deepcopy(fields))
            if append is not None:
                stages[sid].setdefault("resources", []).extend(copy.deepcopy(append))
                existing_ids.update(row["id"] for row in append)
        dossier = item.get("material_synthesis")
        if dossier is not None:
            if not isinstance(dossier, dict) or dossier.get("unit_id", uid) != uid:
                problems.append(f"{where}.material_synthesis must belong to {uid}")
            else:
                syntheses.append({"unit_id": uid, "dossier": copy.deepcopy(dossier)})
        if not any(changes.get(kind) for kind in ("add", "update", "remove")) \
                and not patches and dossier is None:
            problems.append(f"{where} changes nothing")
        entries.append({"unit": copy.deepcopy(unit.data), "study_map": study_map})
    additions = revision.get("unit_additions", [])
    order = list(repo.modules[module_id].get("unit_order", []))
    if not isinstance(additions, list):
        problems.append("unit_additions must be a list")
        additions = []
    for addition in additions:
        if not isinstance(addition, dict) or set(addition) - {"unit", "study_map", "routes", "before_id", "after_id"}:
            problems.append("unit_additions allows unit, study_map, routes and relative placement")
            continue
        unit_data = copy.deepcopy(addition.get("unit"))
        map_data = copy.deepcopy(addition.get("study_map"))
        uid = unit_data.get("id") if isinstance(unit_data, dict) else None
        if not isinstance(uid, str) or not uid or uid in repo.units or uid in seen_units \
                or unit_data.get("module_id") != module_id:
            problems.append("unit_additions needs a fresh unit ID belonging to the requested module")
            continue
        if not isinstance(map_data, dict) or map_data.get("unit_id") != uid \
                or not isinstance(map_data.get("id"), str) or map_data["id"] in repo.study_maps:
            problems.append("unit_additions needs a new study map belonging to its new unit")
            continue
        routes = addition.get("routes", [])
        if not isinstance(routes, list):
            problems.append("unit_additions.routes must be a list of source_id/route objects")
            continue
        source_map, _, route_problems = apply_unit_route_changes(source_map, module_id, uid, {"add": routes})
        problems.extend(route_problems)
        seen_units.add(uid)
        unit_data["current_study_map"] = map_data.get("id")
        entries.append({"unit": unit_data, "study_map": map_data})
        placement = {key: addition[key] for key in ("before_id", "after_id") if key in addition}
        if placement:
            if len(placement) != 1 or next(iter(placement.values())) not in order:
                problems.append("unit_additions needs exactly one existing placement anchor")
                continue
            key, anchor = next(iter(placement.items()))
            order.insert(order.index(anchor) + (key == "after_id"), uid)
        else:
            order.append(uid)
    move = revision.get("unit_move")
    contract = copy.deepcopy(revision.get("plan_contract"))
    if move is not None:
        try:
            if not isinstance(move, dict) or set(move) - {"unit_id", "reason", "before_id", "after_id"}:
                raise ValueError("unit_move allows unit_id, reason and one relative placement")
            if not isinstance(move.get("reason"), str) or not move["reason"].strip():
                raise ValueError("unit_move needs a nonblank reason")
            if not isinstance(move.get("unit_id"), str) or move["unit_id"] not in repo.units or repo.units[move["unit_id"]].module_id != module_id:
                raise ValueError("unit_move targets an existing unit in this module")
            order = [row["id"] for row in relative_placement(
                [{"id": uid} for uid in order], move["unit_id"],
                {key: move[key] for key in ("before_id", "after_id") if key in move})]
            if not isinstance(contract, dict):
                raise ValueError("unit_move requires the existing plan contract")
            if not isinstance(contract.get("intentional_reorders", []), list):
                raise ValueError("intentional_reorders must be a list")
            contract.setdefault("intentional_reorders", []).append({
                "target": "module-unit-order", "id": module_id, "reason": move["reason"]})
        except ValueError as exc:
            problems.append(str(exc))
    if additions or move is not None:
        by_unit = {entry["unit"]["id"]: entry for entry in entries}
        for number, uid in enumerate(order, 1):
            if uid not in by_unit:
                if repo.units[uid].data.get("order") == number:
                    continue
                entry = {"unit": copy.deepcopy(repo.units[uid].data), "study_map": None}
                entries.append(entry)
                by_unit[uid] = entry
            by_unit[uid]["unit"]["order"] = number
    if problems:
        return None, problems
    package = {
        "module_id": module_id,
        "plan_contract": contract,
        "module_patch": {"unit_order": order} if additions or move is not None else {},
        "source_patches": [], "source_map": source_map,
        "units": entries, "material_syntheses": syntheses,
        "claim_evidence": copy.deepcopy(revision.get("claim_evidence", [])),
        "acknowledgments": copy.deepcopy(revision.get("acknowledgments", [])),
        "workspace_updates": [],
    }
    return package, []


def apply_unit_route_changes(source_map: dict[str, Any], module_id: str, unit_id: str,
                              changes: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]], list[str]]:
    """Apply add/update/remove ops to one unit's routes, fail closed.

    Returns ``(new_source_map, summary, problems)``. Unrelated routes are
    carried forward untouched internally; the caller never copies them.
    """
    problems: list[str] = []
    new_map = copy.deepcopy(source_map)
    sources = new_map.get("sources", []) or []
    by_id: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict):
                identified = route_with_identity(module_id, str(source.get("source_id") or ""), route)
                by_id.setdefault(str(identified["id"]), (source, route))

    def unit_of(route: dict[str, Any]) -> str | None:
        return route.get("unit_id") if isinstance(route, dict) else None

    summary: dict[str, list[str]] = {"added": [], "updated": [], "removed": []}
    operated: set[str] = set()
    for kind in ("add", "update", "remove"):
        for row in changes.get(kind, []) or []:
            if not isinstance(row, dict):
                continue
            allowed = {"source_id", "route"} if kind == "add" else \
                {"route_id", "fields"} if kind == "update" else {"route_id", "reason"}
            if set(row) - allowed:
                problems.append(f"route_changes.{kind} has unknown fields "
                                f"{sorted(set(row) - allowed)}; expected {sorted(allowed)}")
            route = row.get("route") if kind == "add" else row
            rid = route.get("id" if kind == "add" else "route_id") if isinstance(route, dict) else None
            if isinstance(rid, str):
                if rid in operated:
                    problems.append(f"ambiguous repeated route operation: {rid}")
                operated.add(rid)
    if problems:
        return new_map, summary, problems
    for row in (changes.get("add", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.add entries must be mappings")
            continue
        source_id = row.get("source_id")
        route = row.get("route")
        if not isinstance(source_id, str) or not isinstance(route, dict):
            problems.append("route_changes.add needs {source_id, route}")
            continue
        rid = route.get("id")
        if not isinstance(rid, str) or not rid.strip():
            problems.append("route_changes.add route needs a stable id")
            continue
        if rid in by_id:
            problems.append(f"route_changes.add duplicates existing route: {rid}")
            continue
        if route.get("unit_id") != unit_id:
            problems.append(f"route_changes.add {rid} must belong to {unit_id}")
            continue
        missing = [k for k in ("title", "format", "angle", "covers", "depth", "scope")
                   if k not in route]
        if missing:
            problems.append(f"route_changes.add {rid} lacks rich route fields: {missing}")
            continue
        targets = [s for s in sources
                   if isinstance(s, dict) and s.get("source_id") == source_id]
        if not targets:
            problems.append(f"route_changes.add {rid} names an unknown source: {source_id}")
            continue
        stored = {k: v for k, v in route.items() if k != "source_id"}
        targets[0].setdefault("unit_routes", []).append(stored)
        by_id[rid] = (targets[0], stored)
        summary["added"].append(rid)
    for row in (changes.get("update", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.update entries must be mappings")
            continue
        rid = row.get("route_id")
        fields = row.get("fields", {})
        if not isinstance(rid, str) or not isinstance(fields, dict):
            problems.append("route_changes.update needs {route_id, fields}")
            continue
        found = by_id.get(rid)
        if found is None:
            problems.append(f"route_changes.update names a missing route: {rid}")
            continue
        _, route = found
        if unit_of(route) != unit_id:
            problems.append(f"route_changes.update {rid} belongs to another unit")
            continue
        unknown = sorted(set(fields) - UNIT_ROUTE_UPDATE_FIELDS)
        if unknown:
            problems.append(
                f"route_changes.update {rid} touches identity/ownership fields: {unknown}")
            continue
        if not fields:
            problems.append(f"route_changes.update {rid} changes nothing")
            continue
        # Persist the public identity before changing the fields it derives from.
        route.setdefault("id", rid)
        route.update(copy.deepcopy(fields))
        summary["updated"].append(rid)
    for row in (changes.get("remove", []) or []):
        if not isinstance(row, dict):
            problems.append("route_changes.remove entries must be mappings")
            continue
        rid = row.get("route_id")
        reason = row.get("reason")
        if not isinstance(rid, str):
            problems.append("route_changes.remove needs a route_id")
            continue
        if not isinstance(reason, str) or not reason.strip():
            problems.append(f"route_changes.remove {rid} needs a disposition reason")
            continue
        found = by_id.get(rid)
        if found is None:
            problems.append(f"route_changes.remove names a missing route: {rid}")
            continue
        source, route = found
        if unit_of(route) != unit_id:
            problems.append(f"route_changes.remove {rid} belongs to another unit")
            continue
        source["unit_routes"].remove(route)
        del by_id[rid]
        summary["removed"].append(rid)
    for key in summary:
        summary[key] = sorted(summary[key])
    return new_map, summary, problems


def minimal_artifact_ids(root: Path, module_id: str, writes: dict[Path, str],
                          entries: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Semantic owners for exactly the files a unit revision changes."""
    ids: list[str] = []
    dossier_by_unit = {unit_id: dossier for unit_id, dossier in entries}
    for path in writes:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) >= 4 and parts[0] == "curriculum" and parts[1] == "modules" \
                and parts[3] == "source-map.yaml":
            if module_id not in ids:
                ids.append(module_id)
        elif "units" in parts:
            uid = parts[parts.index("units") + 1]
            if rel.name == "material-synthesis.yaml":
                dossier = dossier_by_unit.get(uid, {})
                did = dossier.get("id") if isinstance(dossier, dict) else None
                if isinstance(did, str) and did not in ids:
                    ids.append(did)
            elif uid not in ids:
                ids.append(uid)
    return ids


def relative_placement(rows: list[dict], record_id: str, placement: dict) -> list[dict]:
    """Move one unambiguous stable ID relative to another; never mutate input."""
    if set(placement) not in ({"before_id"}, {"after_id"}):
        raise ValueError("placement needs exactly one before_id or after_id")
    key, anchor = next(iter(placement.items()))
    ids = [row.get("id") for row in rows]
    if not isinstance(record_id, str) or ids.count(record_id) != 1:
        raise ValueError(f"missing or ambiguous stable ID: {record_id}")
    if not isinstance(anchor, str) or ids.count(anchor) != 1 or anchor == record_id:
        raise ValueError(f"missing, ambiguous or self placement anchor: {anchor}")
    result = copy.deepcopy(rows)
    moved = result.pop(ids.index(record_id))
    position = next(i for i, row in enumerate(result) if row.get("id") == anchor)
    result.insert(position + (key == "after_id"), moved)
    if result == rows:
        raise ValueError("placement changes nothing")
    return result


_STRUCTURAL_OPERATION_FIELDS = {
    "stage_move": {"stage_id", "before_id", "after_id"},
    "resource_move": {"stage_id", "resource_id", "before_id", "after_id"},
    "resource_insert": {"stage_id", "resource", "before_id", "after_id", "runtime_review"},
    "resource_append": {"stage_id", "resource", "runtime_review"},
}


def _renewed_runtime_review(stage: dict, review: object) -> dict:
    """A new row changes what a runtime review covered, so its edit may renew it.

    Carries no fingerprint: the import binds one to the stage it writes.
    """
    if "runtime_review" not in stage:
        raise ValueError("this stage has no runtime_review to renew")
    if not isinstance(review, dict) or set(review) != {"reviewed_by", "reviewed_on"} or not all(
            isinstance(value, str) and value.strip() for value in review.values()):
        raise ValueError("runtime_review needs exactly reviewed_by and reviewed_on")
    return dict(review)


def apply_structural_edit(current: dict, edit: dict) -> dict:
    """Expand one bounded intent against authored data; preserve all other state."""
    if not isinstance(edit, dict) or set(edit) - {"reason", *_STRUCTURAL_OPERATION_FIELDS}:
        raise ValueError("structural_edit allows reason and one stage_move, resource_move, resource_insert or resource_append")
    if not isinstance(edit.get("reason"), str) or not edit["reason"].strip():
        raise ValueError("structural_edit needs a nonblank reason")
    operations = set(edit) - {"reason"}
    if len(operations) != 1:
        raise ValueError("structural_edit needs exactly one operation")
    kind = next(iter(operations))
    op = edit[kind]
    if not isinstance(op, dict):
        raise ValueError("structural operation must be an object")
    if set(op) - _STRUCTURAL_OPERATION_FIELDS[kind] or "stage_id" not in op:
        raise ValueError("structural operation has unknown or missing fields")
    placement = {key: op[key] for key in ("before_id", "after_id") if key in op}
    result = copy.deepcopy(current)
    stages = result.get("stages", [])
    if kind == "stage_move":
        result["stages"] = relative_placement(stages, op["stage_id"], placement)
        for number, stage in enumerate(result["stages"], 1):
            stage["number"] = number
        return result
    matches = [stage for stage in stages if stage.get("id") == op["stage_id"]]
    if len(matches) != 1:
        raise ValueError("resource operation needs one existing stage ID")
    stage = matches[0]
    resources = stage.get("resources", [])
    if kind == "resource_move":
        stage["resources"] = relative_placement(resources, op.get("resource_id"), placement)
        return result
    resource = op.get("resource")
    if not isinstance(resource, dict) or not isinstance(resource.get("id"), str) or not resource["id"]:
        raise ValueError(f"{kind} needs a resource with a fresh stable ID")
    if any(row.get("id") == resource["id"] for s in stages for row in s.get("resources", [])):
        raise ValueError(f"{kind} reuses an existing resource ID")
    if kind == "resource_append":
        # No anchor: unidentified legacy rows stay as they are, ahead of it.
        stage["resources"] = [*resources, copy.deepcopy(resource)]
    else:
        # Insert via the same anchor rules, including ambiguity and self checks.
        augmented = [*resources, copy.deepcopy(resource)]
        if set(placement) not in ({"before_id"}, {"after_id"}):
            raise ValueError("placement needs exactly one before_id or after_id")
        anchor = next(iter(placement.values()))
        ids = [row.get("id") for row in resources]
        if not isinstance(anchor, str) or ids.count(anchor) != 1:
            raise ValueError("resource_insert needs one existing resource anchor")
        # Appending after the last resource is valid, even though the helper's
        # movement would be a no-op on the augmented list.
        position = ids.index(anchor) + ("after_id" in placement)
        augmented.pop()
        augmented.insert(position, copy.deepcopy(resource))
        stage["resources"] = augmented
    if "runtime_review" in op:
        stage["runtime_review"] = _renewed_runtime_review(stage, op["runtime_review"])
    return result
