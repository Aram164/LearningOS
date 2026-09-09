"""Small material edits and lossless reference compaction through Gateway V2."""

from __future__ import annotations

import copy
import hashlib
import json

from learning_os.loader import load_repo
from learning_os.material_refs import (
    MATERIAL_FIELDS,
    PATCH_FIELDS,
    MaterialReferenceError,
    compact_map,
    expand_map,
    matching_routes,
    persist_route_ids,
    unit_routes,
)
from learning_os.transactions import artifact_revision

from .module import _module_plan_validation_errors
from .reads import _print_stable, _snapshot
from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
)


def _loaded(root):
    repo = load_repo(root)
    if repo.parse_failures:
        raise WriteRefused("material operation refuses unreadable canonical records")
    return repo


def _unit(repo, unit_id):
    unit = repo.units.get(unit_id)
    if unit is None:
        raise WriteRefused(f"unit not found: {unit_id}")
    if unit.module_id not in repo.module_source_maps:
        raise WriteRefused(f"unit {unit_id} has no module source map")
    return unit


def _route(routes, route_id):
    matches = [r for r in routes if r["id"] == route_id]
    if len(matches) != 1:
        raise WriteRefused(f"route {route_id} is missing or ambiguous in this unit")
    return matches[0]


def _guard_rows(root, artifacts):
    return {rid: artifact_revision(root, rid) for rid in sorted(set(artifacts))}


def _map_for_unit(repo, unit_id):
    maps = [sm for sm in repo.study_maps.values() if sm.unit_id == unit_id]
    if len(maps) > 1:
        raise WriteRefused(f"unit {unit_id} has ambiguous study maps")
    return maps[0] if maps else None


#: Batch reads serve at most this many routes: one snapshot, one load,
#: and a payload an operator can still review. Mirrors inspect's batch cap.
MAX_BATCH_ROUTES = 20


def _route_entry(routes, study_map, source_map, unit, route_id):
    """One exact route plus its stage uses: the scalar and batch shape.

    Both selectors build on this so their per-route fields cannot drift.
    Raises WriteRefused for a missing, cross-unit or ambiguous route id.
    """
    route = _route(routes, route_id)
    uses = []
    if study_map:
        raw_stages = {s["id"]: s for s in (study_map.authored_data or study_map.data)["stages"]}
        for stage in study_map.data.get("stages", []):
            for i, resource in enumerate(stage.get("resources", [])):
                if not isinstance(resource, dict):
                    continue
                raw = raw_stages[stage["id"]]["resources"][i]
                ref = raw.get("material_ref", {}) if isinstance(raw, dict) else {}
                matches = matching_routes(resource, routes)
                if ref.get("route_id") == route["id"] or (
                    len(matches) == 1 and matches[0]["id"] == route["id"]
                ):
                    uses.append({"stage_id": stage["id"], "resource_index": i,
                                 "scope_triage": resource.get("scope_triage"),
                                 "overrides": {k: v for k, v in resource.items()
                                               if k in MATERIAL_FIELDS
                                               and (k in raw if ref else
                                                    v != route.get(MATERIAL_FIELDS[k]))}})
    return {"route": route, "uses": uses,
            "patch_fields": sorted(PATCH_FIELDS),
            "patch_capability": "route.patch"}


def _batch_entries(routes, study_map, source_map, unit, route_ids):
    """Ordered route entries for 1-20 distinct routes of one unit.

    Every id is resolved before any entry is built, so a missing,
    cross-unit, duplicate or out-of-bounds request refuses the whole
    batch — never a partial payload.
    """
    ids = list(route_ids or [])
    if not ids:
        raise WriteRefused("plan-edit-context batch needs at least one route id")
    if len(ids) > MAX_BATCH_ROUTES:
        raise WriteRefused(
            f"plan-edit-context accepts at most {MAX_BATCH_ROUTES} routes per batch")
    if len(set(ids)) != len(ids):
        raise WriteRefused("plan-edit-context batch route ids are distinct")
    for route_id in ids:
        _route(routes, route_id)
    return [_route_entry(routes, study_map, source_map, unit, route_id)
            for route_id in ids]


def cmd_plan_edit_context(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        snapshot = _snapshot(root, args.expected_snapshot)
        repo = _loaded(root)
        unit = _unit(repo, args.unit_id)
        source_map = repo.module_source_maps[unit.module_id]
        routes = unit_routes(source_map, unit.module_id, unit.id)
        study_map = _map_for_unit(repo, unit.id)
        artifacts = {unit.module_id, unit.id}
        if study_map:
            artifacts.add(study_map.id)
        payload = {"contract": "plan-edit-context", "unit_id": unit.id,
                   "module_id": unit.module_id,
                   "artifact_revisions": _guard_rows(root, artifacts),
                   "preflight": "route-patch UNIT_ID ROUTE_ID --changes JSON --check returns exact write guards"}
        if args.route_id and getattr(args, "route_ids", None):
            raise WriteRefused(
                "plan-edit-context takes --route-id or --route-ids, never both")
        if args.route_id:
            payload.update(_route_entry(
                routes, study_map, source_map, unit, args.route_id))
        elif getattr(args, "route_ids", None) is not None:
            entries = _batch_entries(
                routes, study_map, source_map, unit, args.route_ids)
            payload.update({"contract": "plan-edit-context-batch",
                            "requested_route_ids": list(args.route_ids),
                            "routes": entries})
        else:
            # Present the compact form even before an existing map is migrated.
            # Expansion inputs are included once, never separately per stage.
            compact = None
            if study_map:
                compact, _ = compact_map(study_map.authored_data or study_map.data,
                                         source_map, unit.module_id, unit.id)
            payload.update({"study_map": compact, "routes": routes,
                            "source_selections": unit.data.get("source_selections", [])})
        return _print_stable(root, snapshot, payload)


def _changed_write(writes, path, data):
    content = _dump_yaml(data)
    # Callers compare record values first; this second check also avoids a
    # write intent when the exact serialized bytes are already current.
    if path.read_bytes() != content.encode("utf-8"):
        writes[path] = content


def compaction_plan(repo, module_id):
    if module_id not in repo.module_source_maps:
        raise WriteRefused(f"module source map not found: {module_id}")
    source_map = repo.module_source_maps[module_id]
    writes, artifacts, used = {}, set(), set()
    saved = 0
    for sm in sorted(repo.study_maps.values(), key=lambda row: row.id):
        if sm.module_id != module_id:
            continue
        raw = sm.authored_data or sm.data
        compact, refs = compact_map(raw, source_map, module_id, sm.unit_id)
        if compact == raw:
            continue
        if expand_map(compact, source_map, module_id, sm.unit_id) != sm.data:
            raise WriteRefused(f"compaction changed {sm.id}")
        _changed_write(writes, sm.path, compact)
        used.update(refs)
        artifacts.update((module_id, sm.unit_id, sm.id))
        saved += len(sm.path.read_bytes()) - len(writes.get(sm.path, "").encode())
    pinned = persist_route_ids(source_map, module_id, used)
    if pinned != source_map:
        _changed_write(writes, repo.module_source_map_origins[module_id], pinned)
    return writes, artifacts, {"module_id": module_id, "map_bytes_saved": saved,
                               "referenced_routes": len(used)}


def route_patch_plan(repo, unit_id, route_id, changes):
    if not isinstance(changes, dict) or not changes or any(
        k not in PATCH_FIELDS or not isinstance(v, str) or not v.strip() or len(v) > 16000
        for k, v in changes.items()
    ):
        raise WriteRefused("changes must contain nonempty text for declared material fields only")
    unit = _unit(repo, unit_id)
    module_id = unit.module_id
    source_map = repo.module_source_maps[module_id]
    routes = unit_routes(source_map, module_id, unit_id)
    old = _route(routes, route_id)
    changes = {k: v for k, v in changes.items() if k not in old or old[k] != v}
    if not changes:
        return {}, set(), {"unit_id": unit_id, "route_id": route_id, "changes": {}}
    updated = persist_route_ids(source_map, module_id, {route_id})
    found = []
    for entry in updated["sources"]:
        for row in entry.get("unit_routes", []) or []:
            if isinstance(row, dict) and row.get("id") == route_id:
                found.append(row)
    if len(found) != 1:
        raise WriteRefused(f"route {route_id} is ambiguous in its module")
    found[0].update(changes)
    writes = {}
    _changed_write(writes, repo.module_source_map_origins[module_id], updated)
    artifacts = {module_id, unit_id}
    unit_data = copy.deepcopy(unit.data)
    for selection in unit_data.get("source_selections", []) or []:
        if not isinstance(selection, dict):
            continue
        same = selection.get("route_id") == route_id if selection.get("route_id") else (
            selection.get("source_id") == old["source_id"] and selection.get("locator") == old.get("locator")
        )
        if same and "locator" in changes:
            # A legacy selection must identify exactly one route, not just a
            # file reused for several pedagogical routes.
            if not selection.get("route_id") and len([r for r in routes if
                r.get("source_id") == selection.get("source_id") and r.get("locator") == selection.get("locator")
            ]) != 1:
                raise WriteRefused("legacy source selection is ambiguous; link its exact route first")
            selection["locator"] = changes["locator"]
    if unit_data != unit.data:
        _changed_write(writes, unit.path, unit_data)
    sm = _map_for_unit(repo, unit_id)
    if sm:
        raw = copy.deepcopy(sm.authored_data or sm.data)
        for stage, effective in zip(raw["stages"], sm.data["stages"], strict=True):
            for resource, expanded in zip(stage.get("resources", []), effective.get("resources", []), strict=True):
                if not isinstance(resource, dict):
                    continue
                ref = resource.get("material_ref")
                matches = matching_routes(expanded, routes)
                linked = ref is not None and ref["route_id"] == route_id
                if not linked and not (len(matches) == 1 and matches[0]["id"] == route_id):
                    continue
                if ref is not None:
                    # Once sharing is explicit, all remaining local values are
                    # deliberate overrides, even if they equal today's owner.
                    continue
                for field, owner in MATERIAL_FIELDS.items():
                    # Explicit stage overrides survive. Only identical legacy
                    # mirrors are synchronized; inherited fields expand later.
                    if owner in changes and field in resource and resource[field] == old.get(owner):
                        resource[field] = changes[owner]
        if raw != (sm.authored_data or sm.data):
            _changed_write(writes, sm.path, raw)
        # A map's effective material changes even when only its owner is written.
        if expand_map(raw, updated, module_id, unit_id) != sm.data:
            artifacts.add(sm.id)
    return writes, artifacts, {"unit_id": unit_id, "route_id": route_id,
                               "changes": {k: {"before": old.get(k), "after": v} for k, v in changes.items()}}


def _execute(args, capability, planner):
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        snapshot = _snapshot(root)
        repo = _loaded(root)
        try:
            writes, artifacts, detail = planner(repo)
        except MaterialReferenceError as exc:
            raise WriteRefused(str(exc)) from exc
        rows = {p.relative_to(root).as_posix(): hashlib.sha256(v.encode()).hexdigest()
                for p, v in sorted(writes.items())}
        plan_hash = "sha256:" + hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
        result = {"schema_version": 1, **detail, "plan_sha256": plan_hash,
                  "affected_files": list(rows), "artifact_ids": sorted(artifacts),
                  "expected_revisions": _guard_rows(root, artifacts)}
        if getattr(args, "plan_sha256", None) not in (None, plan_hash):
            raise WriteRefused("compaction plan changed; review the current plan")
        if not args.check and capability == "module.materials.compact" and args.plan_sha256 is None:
            raise WriteRefused("compaction requires the reviewed plan SHA-256")
        errors = _module_plan_validation_errors(root, writes) if writes else []
        if errors:
            raise WriteRefused("canonical validation failed: " + "; ".join(map(str, errors[:8])))
        if args.check:
            return _print_stable(root, snapshot, {
                **result, "ok": True, "check": True, "canonical_files_written": 0,
            })
        if not writes:
            raise WriteRefused("no material changes to apply")
        code, errors, confirmation = _write_transaction(
            root, writes, capability=capability, artifact_ids=sorted(artifacts),
            expected_revisions=_expected_revisions_from_args(args),
        )
        print(json.dumps({**result, "ok": code == 0, **confirmation,
                          **({"errors": list(map(str, errors))} if errors else {})},
                         ensure_ascii=False, separators=(",", ":")))
        return code


def cmd_route_patch(args) -> int:
    return _execute(args, "route.patch", lambda repo: route_patch_plan(
        repo, args.unit_id, args.route_id, args.changes,
    ))


def cmd_module_materials_compact(args) -> int:
    return _execute(args, "module.materials.compact", lambda repo: compaction_plan(repo, args.module_id))
