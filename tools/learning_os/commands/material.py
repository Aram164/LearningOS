"""Small material edits and lossless reference compaction through Gateway V2."""

from __future__ import annotations

import copy
import hashlib
import json

import yaml

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
from learning_os.material_synthesis import material_synthesis_freshness
from learning_os.transactions import artifact_revision

from .module import _module_plan_validation_errors
from .reads import (
    _analysis_notes,
    _approved_assessments,
    _freshness_label,
    _print_stable,
    _snapshot,
)
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


def _apply_hint(args, capability, snapshot_id, revisions):
    """Ready-to-submit apply values for a successful --check.

    Direct CLI application is disabled, so the hint echoes everything the
    GatewayEnvelopeV2 needs except the per-request fields (request_id,
    idempotency_key, channel, approval): capability, exact payload,
    expected snapshot, and expected revisions. Output layer only —
    validation, guards, and receipts are unchanged.
    """
    if capability != "route.patch":
        return None
    return {
        "apply_via": "GatewayEnvelopeV2",
        "capability": capability,
        "payload": {
            "unit_id": args.unit_id,
            "route_id": args.route_id,
            "changes": args.changes,
        },
        "expected_snapshot": snapshot_id,
        "expected_revisions": dict(revisions),
        "apply_how": ("direct CLI application is disabled; submit a "
                      "GatewayEnvelopeV2 with this capability, payload, "
                      "expected_snapshot and expected_revisions"),
    }


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


def _stage_entry(study_map, stage_id):
    """One stage's own flags and placements, without the whole map.

    Returns the stage row as stored (effective, expanded): identity,
    status, triage and exam flags, objective, concepts, runtime target,
    and resource placements. Raises WriteRefused for a missing stage or
    a unit with no study map — never a partial payload.
    """
    if study_map is None:
        raise WriteRefused("plan-edit-context --stage-id needs a unit with a study map")
    stages = [s for s in study_map.data.get("stages", []) if isinstance(s, dict)]
    matches = [s for s in stages if s.get("id") == stage_id]
    if len(matches) != 1:
        raise WriteRefused(f"stage {stage_id} is missing or ambiguous in this unit")
    return dict(matches[0])


def _unit_audit(root, repo, unit) -> dict:
    """Deterministic planning audit for one unit: counts and lists, no judgments.

    Reports what the catalogue contains and where it stands — depth, scope,
    triage, placements, synthesis freshness — without deciding what is useful.
    The operator still reads the material; this only makes the shape visible
    before that reading starts.
    """
    from learning_os.material_synthesis import (
        MaterialSynthesisError,
        synthesis_destination,
        validate_unit_material_synthesis,
    )

    from .module import _match_key

    source_map = repo.module_source_maps[unit.module_id]
    routes = unit_routes(source_map, unit.module_id, unit.id)
    study_map = _map_for_unit(repo, unit.id)
    stages = study_map.data.get("stages", []) if study_map else []
    placements = [r for s in stages if isinstance(s, dict)
                  for r in (s.get("resources", []) or []) if isinstance(r, dict)]
    placed_keys = {_match_key(r) for r in placements}

    def placed(route):
        return (("route", route.get("id")) in placed_keys
                or ("source", route.get("source_id"), route.get("locator")) in placed_keys)

    by_depth: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for route in routes:
        by_depth[route.get("depth", "unstated")] = by_depth.get(route.get("depth", "unstated"), 0) + 1
        by_scope[route.get("scope", "unstated")] = by_scope.get(route.get("scope", "unstated"), 0) + 1
    triage_by_stage: dict[str, dict] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        counts: dict[str, int] = {}
        for resource in stage.get("resources", []) or []:
            if not isinstance(resource, dict):
                continue
            key = resource.get("scope_triage", "untriaged")
            counts[key] = counts.get(key, 0) + 1
        triage_by_stage[stage.get("id", "?")] = counts
    advanced_required = sorted(
        route["id"] for route in routes
        if route.get("depth") == "advanced-reference"
        and any(r.get("scope_triage") in {"required-now", "helpful-now"}
                for r in placements
                if _match_key(r) in (("route", route.get("id")),
                                     ("source", route.get("source_id"),
                                      route.get("locator")))))
    current_unplaced = sorted(
        route["id"] for route in routes
        if route.get("scope") in {"current", "prerequisite"} and not placed(route))
    legacy: dict[str, list] = {}
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        strings = [r for r in source.get("unit_routes", []) or []
                   if isinstance(r, str)]
        if strings:
            legacy[str(source.get("source_id"))] = strings
    legacy_sources = set(legacy)
    exact_with_unresolved = sorted(
        route["id"] for route in routes
        if route.get("source_id") in legacy_sources)
    unplaced = sorted(route["id"] for route in routes if not placed(route))
    try:
        destination = synthesis_destination(root, unit.id)
    except MaterialSynthesisError:
        destination = None
    synthesis: dict = {"present": bool(destination and destination.is_file()),
                       "fresh": False, "detail": None,
                       "deep_reviewed": 0, "screened": 0,
                       "unevaluated": 0, "unavailable": 0}
    if synthesis["present"]:
        try:
            dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
            validate_unit_material_synthesis(root, unit.id, dossier)
            synthesis["fresh"] = True
        except Exception as exc:  # noqa: BLE001 - freshness is best-effort reporting
            synthesis["detail"] = str(exc)
        try:
            for row in (dossier.get("route_assessments", []) or []):
                status = row.get("review_status")
                if status == "deep-reviewed":
                    synthesis["deep_reviewed"] += 1
                elif status == "screened":
                    synthesis["screened"] += 1
                elif status == "unevaluated":
                    synthesis["unevaluated"] += 1
                elif status == "unavailable":
                    synthesis["unavailable"] += 1
        except Exception:  # noqa: BLE001 - counts stay zero on unreadable dossiers
            pass
    adjacent: dict[str, list] = {}
    unit_source_ids = {r.get("source_id") for r in routes}
    for other_id, other in sorted(repo.units.items()):
        if other_id == unit.id or other.module_id != unit.module_id:
            continue
        try:
            other_routes = unit_routes(
                repo.module_source_maps[other.module_id], other.module_id, other_id)
        except Exception:  # noqa: BLE001 - one unreadable neighbour skips, never blocks
            continue
        shared = sorted(unit_source_ids & {r.get("source_id") for r in other_routes})
        if shared:
            adjacent[other_id] = shared
    return {
        "unit_id": unit.id,
        "module_id": unit.module_id,
        "source_records": len(unit_source_ids),
        "routes": len(routes),
        "placements": len(placements),
        "routes_by_depth": by_depth,
        "routes_by_scope": by_scope,
        "triage_by_stage": triage_by_stage,
        "advanced_reference_placed_required_or_helpful": advanced_required,
        "current_or_prerequisite_unplaced": current_unplaced,
        "legacy_string_routes_by_source": legacy,
        "exact_routes_with_unresolved_siblings": exact_with_unresolved,
        "unplaced_routes": unplaced,
        "synthesis": synthesis,
        "adjacent_unit_source_reuse": adjacent,
        "scope_authority": unit.data.get("scope_sources", []),
        "prior_year_boundary": sorted(
            route["id"] for route in routes if route.get("scope") == "prior-year"),
        "out_of_scope_present": sorted(
            route["id"] for route in routes if route.get("scope") == "out-of-scope"),
    }


def _brief_analysis_refs(root, repo, unit, routes) -> dict:
    """Reusable analysis references for one unit's sources: ids, never bodies.

    The same durable records material-context searches — analysis notes
    bound to this unit's source ids plus approved unit assessments — as
    identifiers with freshness, review, and resolution labels. Follow-up
    reads fetch bodies through the expand commands, never from here.
    """
    unit_source_ids = {r.get("source_id") for r in routes if r.get("source_id")}
    refs = []
    for note in _analysis_notes(repo):
        binding = note.meta["material_analysis"]
        if binding.get("source_id") not in unit_source_ids:
            continue
        refs.append({
            "note_id": note.id,
            "source_id": binding.get("source_id"),
            "resolution": binding.get("resolution"),
            "review": note.meta.get("semantic_review"),
            "inspected_range": binding.get("inspected_range") or {},
            "freshness": _freshness_label(root, binding),
            "path": note.path.relative_to(root).as_posix(),
        })
    assessed: list[str] = []
    stale: list[str] = []
    freshness_by_synthesis: dict[str, dict] = {}
    for synthesis_id, row_unit, assessment in _approved_assessments(repo):
        if row_unit != unit.id:
            continue
        route_id = assessment.get("route_id")
        if not isinstance(route_id, str):
            continue
        fresh = freshness_by_synthesis.get(synthesis_id)
        if fresh is None:
            dossier = repo.unit_material_syntheses.get(synthesis_id)
            fresh = material_synthesis_freshness(
                root, unit.id, dossier if isinstance(dossier, dict) else {},
                repo=repo)
            freshness_by_synthesis[synthesis_id] = fresh
        (assessed if fresh["status"] == "current" else stale).append(route_id)
    by_resolution: dict = {}
    for ref in refs:
        by_resolution[ref["resolution"]] = by_resolution.get(ref["resolution"], 0) + 1
    return {"analysis_notes": refs,
            "approved_assessment_routes": sorted(assessed),
            "stale_assessment_routes": sorted(stale),
            "analysis_by_resolution": by_resolution}


def _brief_payload(root, repo, unit, routes, study_map, artifacts) -> dict:
    """The brief preparation form: what the next command needs, nothing else.

    Identities, guards, id inventories, the audit's missing-evidence lists,
    reusable analysis references, required follow-up inputs, applicable
    preflight checks, and explicit expandable commands. Full route bodies,
    the study map, and analysis prose stay behind the expand references.
    """
    route_ids = sorted(r["id"] for r in routes if r.get("id"))
    stages = study_map.data.get("stages", []) if study_map else []
    stage_rows = [s for s in stages if isinstance(s, dict)]
    stage_ids = sorted(s["id"] for s in stage_rows if s.get("id"))
    batches = [
        f"los plan-edit-context {unit.id} --route-ids "
        + " ".join(route_ids[i:i + MAX_BATCH_ROUTES])
        for i in range(0, len(route_ids), MAX_BATCH_ROUTES)]
    return {
        "contract": "plan-edit-context-brief",
        "unit_id": unit.id,
        "module_id": unit.module_id,
        "artifact_revisions": _guard_rows(root, artifacts),
        "inventory": {
            "route_ids": route_ids,
            "stage_ids": stage_ids,
            "route_count": len(route_ids),
            "stage_count": len(stage_ids),
            "placement_count": sum(
                len(s.get("resources", []) or []) for s in stage_rows),
        },
        "unit_audit": _unit_audit(root, repo, unit),
        "analysis_refs": _brief_analysis_refs(root, repo, unit, routes),
        "required_inputs": {
            "route_patch": {
                "route_id": (f"one of the {len(route_ids)} inventoried route ids"),
                "changes": {
                    "fields": sorted(PATCH_FIELDS),
                    "rules": ("nonempty text per field, at most 16000 characters, "
                              "declared material fields only"),
                },
                "guards": ("artifact_revisions above; the gateway envelope "
                           "carries the snapshot"),
            },
            "plan_replace": {
                "file": ("reviewed package bytes for unit-plan-revise, "
                         "unit-map-import, or module-plan-import"),
                "round_trip": ("save the --check JSON, then apply with "
                               "--apply-reviewed-sha256 and --review-report"),
                "guards": ("artifact_revisions above; the saved report carries "
                           "the exact prepared envelope"),
            },
        },
        "preflight": [
            {"operation": "route-patch",
             "check": f"los route-patch {unit.id} ROUTE_ID --changes JSON --check"},
            {"operation": "unit-plan-revise",
             "check": f"los unit-plan-revise {unit.id} --file REVISION.yaml --check"},
            {"operation": "unit-map-import",
             "check": f"los unit-map-import {unit.id} --file MAP.yaml --check"},
            {"operation": "module-plan-import",
             "check": f"los module-plan-import {unit.module_id} --file PLAN.yaml --check"},
            {"operation": "verify",
             "check": (".venv/bin/python tools/verify_plan_receipt.py "
                       f"--report REPORT.json --unit {unit.id}")},
        ],
        "expand": {
            "full": f"los plan-edit-context {unit.id}",
            "full_audit": f"los plan-edit-context {unit.id} --audit",
            "route_batches": batches,
            "stages": {sid: f"los plan-edit-context {unit.id} --stage-id {sid}"
                       for sid in stage_ids},
            "analysis_search": f"los material-context QUERY --unit {unit.id}",
        },
    }


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
        selectors = [bool(args.route_id), getattr(args, "route_ids", None) is not None,
                     bool(getattr(args, "stage_id", None))]
        if sum(selectors) > 1:
            raise WriteRefused(
                "plan-edit-context takes one of --route-id, --route-ids, --stage-id")
        if getattr(args, "audit", False) and any(selectors):
            raise WriteRefused(
                "plan-edit-context --audit attaches to the full unit context, "
                "not to a route or stage selection")
        if getattr(args, "brief", False) and any(selectors):
            raise WriteRefused(
                "plan-edit-context --brief is the full-unit preparation form; "
                "expand one route or stage through its listed command instead")
        if getattr(args, "brief", False) and getattr(args, "audit", False):
            raise WriteRefused(
                "plan-edit-context --brief already carries the unit audit")
        if args.route_id:
            payload.update(_route_entry(
                routes, study_map, source_map, unit, args.route_id))
        elif getattr(args, "route_ids", None) is not None:
            entries = _batch_entries(
                routes, study_map, source_map, unit, args.route_ids)
            payload.update({"contract": "plan-edit-context-batch",
                            "requested_route_ids": list(args.route_ids),
                            "routes": entries})
        elif getattr(args, "stage_id", None):
            payload.update({"contract": "plan-edit-context-stage",
                            "requested_stage_id": args.stage_id,
                            "stage": _stage_entry(study_map, args.stage_id),
                            "scope": "one stage only — universe questions "
                                     "(e.g. no source covers X) need the full unit context"})
        elif getattr(args, "brief", False):
            payload = _brief_payload(root, repo, unit, routes, study_map, artifacts)
        else:
            # Present the compact form even before an existing map is migrated.
            # Expansion inputs are included once, never separately per stage.
            compact = None
            if study_map:
                compact, _ = compact_map(study_map.authored_data or study_map.data,
                                         source_map, unit.module_id, unit.id)
            payload.update({"study_map": compact, "routes": routes,
                            "source_selections": unit.data.get("source_selections", [])})
            if getattr(args, "audit", False):
                payload.update({"unit_audit": _unit_audit(root, repo, unit)})
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
            check_result = {
                **result, "ok": True, "check": True, "canonical_files_written": 0,
            }
            hint = _apply_hint(args, capability, snapshot, result["expected_revisions"])
            if hint is not None:
                check_result["next"] = hint
            return _print_stable(root, snapshot, check_result)
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
