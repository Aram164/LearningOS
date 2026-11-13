"""Material reading for plan editing: edit context, source spans and material context."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

import yaml

from learning_os.app.context import OpContext
from learning_os.app.handlers._shared import guard_rows as _guard_rows
from learning_os.app.handlers._shared import map_for_unit as _map_for_unit
from learning_os.app.handlers._shared import window_values as _window_values
from learning_os.app.proposal import Result
from learning_os.app.registry import OperationEffects, register
from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    read_stage_results,
    stage_results_for,
)
from learning_os.derive.material_synthesis import material_synthesis_freshness
from learning_os.derive.semantics.claim_status import claims_summary, observe_claims_with_audits
from learning_os.derive.semantics.source_use import evidence_label as _evidence_label
from learning_os.derive.semantics.source_use import use_evidence as _use_evidence
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused, unreadable_refusal
from learning_os.domain.material_refs import (
    MATERIAL_FIELDS,
    PATCH_FIELDS,
    compact_map,
    matching_routes,
    unit_routes,
)
from learning_os.domain.suggest import MAX_SUGGESTIONS, expansion, suggest, with_suggestions
from learning_os.domain.vocabulary import FRONTMATTER_RE
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.fs import note_bytes as _note_bytes
from learning_os.store.material_analysis import observe_local_material
from learning_os.store.materials.reading_cards import (
    MAX_OPEN_ENTRIES,
    Read,
    ReadingStore,
    ReadingStoreError,
    SettleRefusal,
    adopt_command,
    entry_view,
    pages_label,
    settle_command,
    valid_session,
)
from learning_os.store.materials.resolution import (
    project_material_resource,
    resolve_route_material_files,
    sha256_file,
)
from learning_os.store.materials.slices import (
    SliceResolutionError,
    parse_locator_page_ranges,
    pdf_part_from_bytes,
)
from learning_os.store.materials.slices import read_part as _read_part
from learning_os.store.materials.slices import route_material_files as _route_material_files
from learning_os.store.materials.slices import unit_note_scope as _unit_note_scope

MAX_STAGE_RESULTS = 5

def _analysis_notes(repo):
    return sorted((note for note in repo.notes.values()
                   if isinstance(note.meta.get("material_analysis"), dict)),
                  key=lambda note: note.id)

def _approved_assessments(repo):
    found = []
    for synthesis_id in sorted(repo.unit_material_syntheses):
        data = repo.unit_material_syntheses[synthesis_id]
        if not isinstance(data, dict) or data.get("status") != "approved":
            continue
        unit_id = data.get("unit_id")
        assessments = data.get("route_assessments")
        if not isinstance(assessments, list):
            continue
        for assessment in assessments:
            if isinstance(assessment, dict):
                found.append((synthesis_id, unit_id, assessment))
    found.sort(key=lambda row: (row[1] or "", row[2].get("route_id") or ""))
    return found

def _freshness_label(root, binding, observations=None):
    """Live source freshness: current, stale, or unreadable. Never inferred.

    When `observations` is given, the observed bytes (or their absence)
    are recorded under the material relpath so a paged continuation can
    prove the external state it pages over did not move between pages.
    """
    material = str(binding.get("material") or "")
    observation = observe_local_material(
        root.parent / "materials", material,
        str(binding.get("recorded_source_digest") or ""))
    if observations is not None:
        live = observation.get("live_digest")
        observations[f"material:{material}"] = \
            live if live is not None else observation["status"]
    status = observation["status"]
    if status in ("current", "stale"):
        return status
    return "unreadable"


#: Batch reads serve at most this many routes: one snapshot, one load,
#: and a payload an operator can still review. Mirrors inspect's batch cap.
MAX_BATCH_ROUTES = 20

#: The span excerpt stays well under the old 8 KiB operator print.
MAX_EXCERPT = 6000


def _unit(ctx, repo, unit_id):
    """The unit, or an R6 refusal (SPEC (bi) item 7).

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is a ``NotFound`` with the byte-identical legacy
    complaint; the corrupt-catalogue guard stays a site-less plain
    refusal, exactly as it propagated.
    """
    unit = repo.units.get(unit_id)
    if unit is None:
        complaint = with_suggestions(
            f"unit not found: {unit_id}", unit_id, repo.units)
        raise NotFound("unit", unit_id, repo.units, message=complaint,
                       site=f"{ctx.operation}.unknown-unit")
    if unit.module_id not in repo.module_source_maps:
        raise WriteRefused(f"unit {unit_id} has no module source map")
    return unit


def _route(ctx, routes, route_id):
    """One exact route id, or an R6 refusal (SPEC (bi) item 7).

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is a ``NotFound`` with the byte-identical legacy
    complaint; the ambiguous match keeps the legacy plain refusal and
    its text, as ``_require_route`` does.
    """
    matches = [r for r in routes if r["id"] == route_id]
    if len(matches) != 1:
        complaint = with_suggestions(
            f"route {route_id} is missing or ambiguous in this unit",
            route_id, [row["id"] for row in routes])
        if not matches:
            raise NotFound("route", route_id,
                           [row["id"] for row in routes],
                           message=complaint,
                           site=f"{ctx.operation}.unknown-route")
        raise WriteRefused(complaint)
    return matches[0]


def _route_entry(ctx, routes, study_map, source_map, unit, route_id):
    """One exact route plus its stage uses: the scalar and batch shape.

    Both selectors build on this so their per-route fields cannot drift.
    Raises WriteRefused for a missing, cross-unit or ambiguous route id.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3); only the context threads through to the lookup.
    """
    route = _route(ctx, routes, route_id)
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


def _batch_entries(ctx, routes, study_map, source_map, unit, route_ids):
    """Ordered route entries for 1-20 distinct routes of one unit.

    Every id is resolved before any entry is built, so a missing,
    cross-unit, duplicate or out-of-bounds request refuses the whole
    batch — never a partial payload.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3); only the context threads through to the lookups.
    """
    ids = list(route_ids or [])
    if not ids:
        raise WriteRefused(
            "plan-edit-context batch needs at least one route id",
            site=f"{ctx.operation}.empty-batch")
    if len(ids) > MAX_BATCH_ROUTES:
        raise WriteRefused(
            f"plan-edit-context accepts at most {MAX_BATCH_ROUTES} routes per batch",
            site=f"{ctx.operation}.batch-too-many")
    if len(set(ids)) != len(ids):
        raise WriteRefused(
            "plan-edit-context batch route ids are distinct",
            site=f"{ctx.operation}.batch-duplicate")
    for route_id in ids:
        _route(ctx, routes, route_id)
    return [_route_entry(ctx, routes, study_map, source_map, unit, route_id)
            for route_id in ids]


def _stage_entry(ctx, study_map, stage_id):
    """One stage's own flags and placements, without the whole map.

    Returns the stage row as stored (effective, expanded): identity,
    status, triage and exam flags, objective, concepts, runtime target,
    and resource placements. Raises WriteRefused for a missing stage or
    a unit with no study map — never a partial payload.

    Moved from ``commands.material`` for the plan reads (SPEC (bs)
    item 3): the miss is an R6 ``NotFound`` with the byte-identical
    legacy complaint; the ambiguous match keeps the legacy plain
    refusal and its text.
    """
    if study_map is None:
        raise WriteRefused(
            "plan-edit-context --stage-id needs a unit with a study map",
            site=f"{ctx.operation}.stage-needs-map")
    stages = [s for s in study_map.data.get("stages", []) if isinstance(s, dict)]
    matches = [s for s in stages if s.get("id") == stage_id]
    if len(matches) != 1:
        complaint = f"stage {stage_id} is missing or ambiguous in this unit"
        if not matches:
            raise NotFound("stage", stage_id,
                           [s["id"] for s in stages if s.get("id")],
                           message=complaint,
                           site=f"{ctx.operation}.unknown-stage")
        raise WriteRefused(complaint)
    return dict(matches[0])


def _unit_audit(root, repo, unit) -> dict:
    """Deterministic planning audit for one unit: counts and lists, no judgments.

    Reports what the catalogue contains and where it stands — depth, scope,
    triage, placements, synthesis freshness — without deciding what is useful.
    The operator still reads the material; this only makes the shape visible
    before that reading starts.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    from learning_os.app._plan_gate import match_key as _match_key
    from learning_os.derive.material_synthesis import (
        MaterialSynthesisError,
        synthesis_destination,
        validate_unit_material_synthesis,
    )

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
        destination = synthesis_destination(root, unit.id, repo=repo)
    except MaterialSynthesisError:
        destination = None
    present = bool(destination and destination.is_file())
    synthesis: dict = {"present": present,
                       "replacement_required_if_evidential_routes_change": present,
                       "replacement_reason": (
                           "an existing dossier needs a staged replacement when evidential routes change"
                           if present else "no existing dossier requires replacement"),
                       "fresh": False, "detail": None,
                       "deep_reviewed": 0, "screened": 0,
                       "unevaluated": 0, "unavailable": 0}
    if synthesis["present"]:
        try:
            dossier = yaml.safe_load(destination.read_text(encoding="utf-8"))
            validate_unit_material_synthesis(root, unit.id, dossier, repo=repo)
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


def _brief_analysis_refs(root, repo, unit, routes, snapshot, *, include_related=False) -> dict:
    """Reusable analysis references for one unit's routes: ids, never bodies.

    The same durable records material-context searches — analysis notes
    standing direct against this unit's routes plus approved unit
    assessments — as identifiers with freshness, review, and resolution
    labels. Same-source-only notes are counted with an expansion hint,
    listed only through --include-related. Follow-up reads fetch bodies
    through the expand commands, never from here.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    pairs = [(route.get("source_id"), route) for route in routes
             if route.get("source_id")]
    refs = []
    related = []
    for note in _analysis_notes(repo):
        binding = note.meta["material_analysis"]
        standing = _unit_note_scope(repo, binding, pairs)
        if standing is None:
            continue
        (refs if standing == "direct" else related).append({
            "note_id": note.id,
            "source_id": binding.get("source_id"),
            "scope": standing,
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
    out = {"analysis_notes": refs,
           "related_count": len(related),
           "related_expand": expansion(
               "plan-edit-context", unit.id, "--brief", "--include-related",
               "--expected-snapshot", snapshot),
           "approved_assessment_routes": sorted(assessed),
           "stale_assessment_routes": sorted(stale),
           "analysis_by_resolution": by_resolution}
    if include_related:
        out["related_notes"] = related
    return out


def _brief_payload(root, repo, unit, routes, study_map, artifacts, snapshot,
                   *, include_related=False, include_neighbors=False) -> dict:
    """The brief preparation form: what the next command needs, nothing else.

    Identities, guards, id inventories, the audit's missing-evidence lists,
    reusable analysis references, required follow-up inputs, applicable
    preflight checks, and explicit expandable commands. Full route bodies,
    the study map, and analysis prose stay behind the expand references.
    The neighboring-unit source-reuse map is discovery information, not
    coverage: the brief carries its count, and the complete map lists only
    through the explicit expansion.

    Moved verbatim from ``commands.material`` for the plan reads (SPEC
    (bs) item 3).
    """
    route_ids = sorted(r["id"] for r in routes if r.get("id"))
    stages = study_map.data.get("stages", []) if study_map else []
    stage_rows = [s for s in stages if isinstance(s, dict)]
    stage_ids = sorted(s["id"] for s in stage_rows if s.get("id"))
    batches = [
        expansion("plan-edit-context", unit.id, "--route-ids",
                  *route_ids[i:i + MAX_BATCH_ROUTES],
                  "--expected-snapshot", snapshot)
        for i in range(0, len(route_ids), MAX_BATCH_ROUTES)]
    audit = _unit_audit(root, repo, unit)
    neighbors = audit["adjacent_unit_source_reuse"]
    brief_audit = {key: value for key, value in audit.items()
                   if key != "adjacent_unit_source_reuse"}
    brief_audit["adjacent_unit_source_reuse_count"] = len(neighbors)
    if include_neighbors:
        brief_audit["adjacent_unit_source_reuse"] = neighbors
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
        "unit_audit": brief_audit,
        "analysis_refs": _brief_analysis_refs(
            root, repo, unit, routes, snapshot,
            include_related=include_related),
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
             "check": expansion(
                 "route-patch", unit.id, "ROUTE_ID",
                 "--changes", "JSON", "--check")},
            {"operation": "unit-plan-revise",
             "check": expansion(
                 "unit-plan-revise", unit.id, "--file", "REVISION.yaml",
                 "--check")},
            {"operation": "unit-map-import",
             "check": expansion(
                 "unit-map-import", unit.id, "--file", "MAP.yaml", "--check")},
            {"operation": "module-plan-import",
             "check": expansion(
                 "module-plan-import", unit.module_id, "--file", "PLAN.yaml",
                 "--check")},
            {"operation": "verify",
             "check": (".venv/bin/python tools/verify_plan_receipt.py "
                       f"--report REPORT.json --unit {unit.id}")},
        ],
        "expand": {
            "full": expansion(
                "plan-edit-context", unit.id, "--expected-snapshot", snapshot),
            "full_audit": expansion(
                "plan-edit-context", unit.id, "--audit",
                "--expected-snapshot", snapshot),
            "adjacent_unit_source_reuse": expansion(
                "plan-edit-context", unit.id, "--brief", "--include-neighbors",
                "--expected-snapshot", snapshot),
            "route_batches": batches,
            "stages": {sid: expansion(
                "plan-edit-context", unit.id, "--stage-id", sid,
                "--expected-snapshot", snapshot)
                       for sid in stage_ids},
            "analysis_search": expansion(
                "material-context", "QUERY", "--unit", unit.id,
                "--expected-snapshot", snapshot),
        },
    }


@register("plan.edit-context", kind="query", effects=OperationEffects.READ)
def plan_edit_context(ctx: OpContext, req: dict) -> Result:
    """Assemble one unit's edit context: map, routes, selections, audit."""
    root = ctx.root
    snapshot = _snapshot(root, req.get("expected_snapshot"))
    repo = ctx.repo()
    if repo.parse_failures:
        raise WriteRefused(
            "material operation refuses unreadable canonical records")
    unit = _unit(ctx, repo, req["unit_id"])
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
    selectors = [bool(req.get("route_id")),
                 req.get("route_ids") is not None,
                 bool(req.get("stage_id"))]
    if sum(selectors) > 1:
        raise WriteRefused(
            "plan-edit-context takes one of --route-id, --route-ids, --stage-id",
            site=f"{ctx.operation}.one-selector")
    if req.get("audit") and any(selectors):
        raise WriteRefused(
            "plan-edit-context --audit attaches to the full unit context, "
            "not to a route or stage selection",
            site=f"{ctx.operation}.audit-needs-full")
    if req.get("brief") and any(selectors):
        raise WriteRefused(
            "plan-edit-context --brief is the full-unit preparation form; "
            "expand one route or stage through its listed command instead",
            site=f"{ctx.operation}.brief-needs-full")
    if req.get("brief") and req.get("audit"):
        raise WriteRefused(
            "plan-edit-context --brief already carries the unit audit",
            site=f"{ctx.operation}.brief-has-audit")
    if req.get("include_related") and not req.get("brief"):
        raise WriteRefused(
            "plan-edit-context --include-related needs --brief",
            site=f"{ctx.operation}.related-needs-brief")
    if req.get("include_neighbors") and not req.get("brief"):
        raise WriteRefused(
            "plan-edit-context --include-neighbors needs --brief",
            site=f"{ctx.operation}.neighbors-needs-brief")
    if req.get("route_id"):
        payload.update(_route_entry(
            ctx, routes, study_map, source_map, unit, req["route_id"]))
    elif req.get("route_ids") is not None:
        entries = _batch_entries(
            ctx, routes, study_map, source_map, unit, req["route_ids"])
        payload.update({"contract": "plan-edit-context-batch",
                        "requested_route_ids": list(req["route_ids"]),
                        "routes": entries})
    elif req.get("stage_id"):
        try:
            untargeted = stage_results_for(
                read_stage_results(repo), unit.id, req["stage_id"])
        except RuntimeInputError as exc:
            raise WriteRefused(
                str(exc), site=f"{ctx.operation}.bad-stage-results",
            ) from exc
        payload.update({"contract": "plan-edit-context-stage",
                        "requested_stage_id": req["stage_id"],
                        "stage": _stage_entry(ctx, study_map, req["stage_id"]),
                        "stage_results": {
                            "results": [
                                {"id": row.get("id"),
                                 "activity": row.get("activity"),
                                 "result": row.get("result"),
                                 "timestamp": row.get("timestamp"),
                                 "conditions": row.get("conditions", []),
                                 "assistance": row.get("assistance", ""),
                                 "note": row.get("note", "")}
                                for row in untargeted[:MAX_STAGE_RESULTS]
                            ],
                            "total": len(untargeted),
                            "credit": "none",
                        },
                        "scope": "one stage only — universe questions "
                                 "(e.g. no source covers X) need the full unit context"})
    elif req.get("brief"):
        payload = _brief_payload(
            root, repo, unit, routes, study_map, artifacts, snapshot,
            include_related=bool(req.get("include_related")),
            include_neighbors=bool(req.get("include_neighbors")))
    else:
        # Present the compact form even before an existing map is migrated.
        # Expansion inputs are included once, never separately per stage.
        compact = None
        if study_map:
            compact, _ = compact_map(study_map.authored_data or study_map.data,
                                     source_map, unit.module_id, unit.id)
        payload.update({"study_map": compact, "routes": routes,
                        "source_selections": unit.data.get("source_selections", [])})
        if req.get("audit"):
            payload.update({"unit_audit": _unit_audit(root, repo, unit)})
    if not req.get("stage_id"):
        selected = ([req["route_id"]] if req.get("route_id") else req["route_ids"]
                    if req.get("route_ids") is not None else [row["id"] for row in routes])
        try:
            claims = observe_claims_with_audits(root, repo=repo, route_ids=selected)
        except ValueError as exc:
            raise WriteRefused(f"cannot read claim status: {exc}") from exc
        if req.get("route_id"):
            payload["claim"] = claims["covers:" + req["route_id"]].payload()
        elif req.get("route_ids") is not None:
            for entry in payload["routes"]:
                entry["claim"] = claims["covers:" + entry["route"]["id"]].payload()
        elif req.get("brief"):
            payload["claims"] = claims_summary(claims)
        else:
            payload["claims"] = {cid.removeprefix("covers:"): row.payload() for cid, row in claims.items()}
    _snapshot(root, snapshot)
    return Result(
        {"schema_version": 1, "snapshot_id": snapshot, **payload},

    )


def _placement_route(ctx, repo, unit, source_map, routes, route, req):
    """Use only a snapshot-bound canonical placement, never caller-supplied paths.

    Moved from ``commands.material_span`` for the plan reads (SPEC
    (bs) item 3): only the context threads through to the lookup and
    the request replaces the namespace.
    """
    stage_id = req.get("stage_id")
    index = req.get("resource_index")
    if bool(stage_id) != (index is not None):
        raise WriteRefused(
            "--stage and --resource-index must be supplied together",
            site=f"{ctx.operation}.stage-needs-index")
    if not stage_id:
        return route, ""
    study_map = _map_for_unit(repo, unit.id)
    if study_map is None:
        raise WriteRefused("unit has no stage placement to inspect",
                           site=f"{ctx.operation}.placement-needs-map")
    stages = [row for row in study_map.data.get("stages", [])
              if isinstance(row, dict) and row.get("id") == stage_id]
    if not stages:
        raise NotFound("stage", stage_id,
                       [row["id"] for row in study_map.data.get("stages", [])
                        if isinstance(row, dict) and row.get("id")],
                       message="placement is missing or ambiguous in this unit",
                       site=f"{ctx.operation}.unknown-placement")
    if len(stages) != 1 or index < 0 or index >= len(stages[0].get("resources", [])):
        raise WriteRefused("placement is missing or ambiguous in this unit",
                           site=f"{ctx.operation}.unknown-placement")
    uses = _route_entry(
        ctx, routes, study_map, source_map, unit, route["id"])["uses"]
    if not any(use["stage_id"] == stage_id and use["resource_index"] == index
               for use in uses):
        raise WriteRefused(
            "placement is missing or does not belong to this route",
            site=f"{ctx.operation}.placement-foreign")
    resource = stages[0]["resources"][index]
    if resource.get("source_id") != route.get("source_id"):
        raise WriteRefused("placement source does not match its route",
                           site=f"{ctx.operation}.placement-source-mismatch")
    selected = {**route, **{key: resource[key] for key in ("locator", "vault_path", "url")
                           if key in resource}}
    return selected, f" --stage {stage_id} --resource-index {index}"


_SHA256_PIN_RE = re.compile(r"(?:sha256:)?([0-9a-f]{64})")

#: Registered route bindings listed for one material-form file.
MAX_MATERIAL_BINDINGS = 10

#: Analysis notes listed for one material-form file.
MAX_MATERIAL_NOTES = 20


def _form_refusal(ctx, message):
    return WriteRefused(message, site=f"{ctx.operation}.bad-form")


def _pinned_digest(ctx, raw):
    """``sha256:<hex>`` from ``--file-sha256``, or None when not given."""
    if raw is None:
        return None
    match = _SHA256_PIN_RE.fullmatch(raw) if isinstance(raw, str) else None
    if match is None:
        raise _form_refusal(
            ctx, "--file-sha256 must be a SHA-256 digest such as a search hit's "
                 "file_sha256 (sha256:<64 lowercase hex>)")
    return f"sha256:{match.group(1)}"


def _refuse_changed(ctx, where, pinned, observed):
    raise WriteRefused(
        f"{where} changed since the reference was made: expected {pinned}, "
        f"the file now hashes to {observed}; search again for a current reference",
        site=f"{ctx.operation}.file-changed", prefixed=True, exit_code=3)


def _read_material_pdf(ctx, materials_root: Path, relative) -> tuple[Path, bytes]:
    """One regular PDF below the resolved materials root, read through one descriptor.

    The configured root is resolved first, so a root that is itself a link
    (a copied trial world) keeps working. Below it every component is opened
    relative to its parent's descriptor without following links, so a
    symlink anywhere below the root refuses and no component can be swapped
    between the check and the read. The digest check and the extraction both
    use the bytes read here; nothing is reopened by path.
    """
    def bad(message):
        return WriteRefused(message, site=f"{ctx.operation}.bad-material")

    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative:
        raise bad(f"--material must be a materials-root-relative path: {relative!r}")
    pure = PurePosixPath(relative)
    if (pure.is_absolute() or pure.as_posix() != relative
            or any(part in {"", ".", ".."} for part in pure.parts)):
        raise bad("--material must be a canonical materials-root-relative path "
                  f"without traversal: {relative!r}")
    if ".flat" in pure.parts:
        raise bad("--material may not pass through the reserved .flat alias "
                  "directory; use the physical path a material-search hit names")
    if pure.suffix.lower() != ".pdf":
        raise bad(f"--material reads PDFs only: {relative!r}")
    try:
        base = materials_root.resolve(strict=True)
    except OSError as exc:
        raise WriteRefused(f"the materials root is unavailable: {materials_root}",
                           site=f"{ctx.operation}.material-missing") from exc
    directory = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptors: list[int] = []
    try:
        descriptors.append(os.open(base, directory))
        for part in pure.parts[:-1]:
            descriptors.append(os.open(part, directory | os.O_NOFOLLOW,
                                       dir_fd=descriptors[-1]))
        handle = os.open(pure.parts[-1], os.O_RDONLY | os.O_NOFOLLOW,
                         dir_fd=descriptors[-1])
        descriptors.append(handle)
        if not stat.S_ISREG(os.fstat(handle).st_mode):
            raise bad(f"--material is not a regular file: {relative!r}")
        chunks = []
        while chunk := os.read(handle, 1 << 20):
            chunks.append(chunk)
    except FileNotFoundError as exc:
        raise WriteRefused(f"no file at --material {relative!r} below the materials root",
                           site=f"{ctx.operation}.material-missing") from exc
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise bad(f"--material {relative!r} passes through a symlink or a "
                      "non-directory below the materials root") from exc
        raise
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    return base.joinpath(*pure.parts), b"".join(chunks)


def _material_route_bindings(repo, physical: Path) -> list[dict]:
    """Every (module, unit, route) whose resolved files include this exact file."""
    found, seen = [], set()
    for unit_id in sorted(repo.units):
        unit = repo.units[unit_id]
        source_map = repo.module_source_maps.get(unit.module_id)
        if not isinstance(source_map, dict):
            continue
        for route in unit_routes(source_map, unit.module_id, unit.id):
            route_id = route.get("id")
            if not route_id or (unit.id, route_id) in seen:
                continue
            for resolved in resolve_route_material_files(repo, route):
                try:
                    same = Path(resolved.path).resolve() == physical
                except OSError:
                    same = False
                if same:
                    seen.add((unit.id, route_id))
                    found.append({"module": unit.module_id, "unit": unit.id,
                                  "route": route_id, "source_id": route.get("source_id")})
                    break
    return found


def _material_analysis_refs(root, repo, relative) -> dict:
    """Analysis notes bound to this exact materials path: ids, never bodies."""
    refs = []
    for note in _analysis_notes(repo):
        binding = note.meta["material_analysis"]
        if binding.get("material") != relative:
            continue
        refs.append({
            "note_id": note.id,
            "source_id": binding.get("source_id"),
            "scope": "direct",
            "resolution": binding.get("resolution"),
            "review": note.meta.get("semantic_review"),
            "inspected_range": binding.get("inspected_range") or {},
            "freshness": _freshness_label(root, binding),
            "path": note.path.relative_to(root).as_posix(),
        })
    return {"analysis_notes": refs[:MAX_MATERIAL_NOTES],
            "analysis_notes_total": len(refs),
            "analysis_notes_truncated": len(refs) > MAX_MATERIAL_NOTES}


def _material_form_span(ctx, req) -> Result:
    """``material-span --material RELPATH --pages … --extract``: no unit, no route."""
    root = ctx.root
    snapshot = _snapshot(root, req.get("expected_snapshot"))
    if any(req.get(key) is not None for key in
           ("unit_id", "route_id", "stage_id", "resource_index")):
        raise _form_refusal(ctx, "--material replaces UNIT, ROUTE and the stage "
                                 "placement; pass one form, not both")
    pages_text = req.get("pages")
    parsed = (parse_locator_page_ranges(pages_text.strip())
              if isinstance(pages_text, str) else [])
    if not req.get("extract") or not parsed:
        raise _form_refusal(
            ctx, '--material needs --extract and --pages with explicit PDF pages '
                 'in the locator house style, e.g. "pdf p. 287" or "pdf pp. 287-289"')
    pinned = _pinned_digest(ctx, req.get("file_sha256"))
    repo = ctx.repo()
    relative = req["material"]
    physical, content = _read_material_pdf(
        ctx, repo.learningos_root / "materials", relative)
    digest = "sha256:" + hashlib.sha256(content).hexdigest()
    if pinned is not None and digest != pinned:
        _refuse_changed(ctx, f"--material {relative}", pinned, digest)
    bindings = _material_route_bindings(repo, physical)
    sources = {row["source_id"] for row in bindings if row.get("source_id")}
    source_id = next(iter(sources)) if len(sources) == 1 else None
    bare = digest.removeprefix("sha256:")
    entry = {"material_uri": None, "material": relative, "format": "pdf",
             "file_sha256": digest, "extraction": "not-requested",
             "binding": {"resolution": "resolved", "source_id": source_id,
                         "material": relative, "recorded_source_digest": bare,
                         "live_source_digest": bare}}
    try:
        part = pdf_part_from_bytes(relative, content, parsed)
        excerpt = part.text[:MAX_EXCERPT]
        entry.update({"extraction": part.status, "excerpt": excerpt,
                      "excerpt_truncated": len(part.text) > MAX_EXCERPT,
                      "pages": list(part.pages), "page_total": part.page_total})
    except SliceResolutionError as exc:
        entry.update({"extraction": "unreadable", "reason": exc.reason})
    next_action = None
    if entry.get("excerpt_truncated") or entry.get("extraction") == "range-truncated":
        next_action = ("This excerpt is cut off. Rerun material-span --material "
                       f"{relative!r} with fewer --pages, e.g. one page at a time.")
    payload = {
        "contract": "material-span-v1", "unit_id": None, "module_id": None,
        "route_id": None, "source_id": source_id, "material": relative,
        "locator": None, "url": None, "availability": "local-observed",
        "next_action": next_action,
        "bindings": bindings[:MAX_MATERIAL_BINDINGS],
        "bindings_total": len(bindings),
        "analysis_refs": _material_analysis_refs(root, repo, relative),
        "spans": [entry],
        "expansion": None,
    }
    _snapshot(root, snapshot)
    return Result({"schema_version": 1, "snapshot_id": snapshot, **payload})


@register("material.span", kind="query", effects=OperationEffects.READ)
def material_span(ctx: OpContext, req: dict) -> Result:
    """One common source-span description, with optional bounded local inspection.

    Two forms: an exact unit route (``UNIT ROUTE``), or a PDF named by its
    materials-root-relative path (``--material``), which needs no route.
    """
    root = ctx.root
    try:
        if req.get("material") is not None:
            return _material_form_span(ctx, req)
        if req.get("unit_id") is None or req.get("route_id") is None:
            raise _form_refusal(
                ctx, 'material-span needs UNIT ROUTE, or --material RELPATH '
                     '--pages "pdf p. N" --extract')
        pinned = _pinned_digest(ctx, req.get("file_sha256"))
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        repo = ctx.repo()
        unit = repo.units.get(req["unit_id"])
        if unit is None:
            complaint = with_suggestions(
                f"unknown unit {req['unit_id']}",
                req["unit_id"], repo.units)
            raise NotFound("unit", req["unit_id"], repo.units,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-unit")
        source_map = repo.module_source_maps.get(unit.module_id)
        if source_map is None:
            raise WriteRefused("unit has no module source map")
        routes = unit_routes(source_map, unit.module_id, unit.id)
        matches = [row for row in routes
                   if row["id"] == req["route_id"]]
        if len(matches) > 1:
            raise WriteRefused(
                f"route {req['route_id']} is ambiguous in {unit.id}: "
                f"{len(matches)} matches")
        if not matches:
            route_ids = sorted(row["id"] for row in routes if row.get("id"))
            base = f"route not found: {req['route_id']} in {unit.id}"
            if suggest(req["route_id"], route_ids):
                complaint = with_suggestions(
                    base, req["route_id"], route_ids)
            else:
                # No ranked near-miss: still name the unit's routes, bounded,
                # so the caller picks an existing one instead of guessing.
                listed = route_ids[:MAX_SUGGESTIONS]
                extra = len(route_ids) - len(listed)
                detail = ", ".join([*listed, f"+{extra} more"] if extra > 0
                                   else listed)
                complaint = f"{base} (routes: {detail})" if detail else base
            raise NotFound("route", req["route_id"], route_ids,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-route")
        route, placement_flags = _placement_route(
            ctx, repo, unit, source_map, routes, matches[0], req)
        explicit_pages: list[tuple[int, int]] | None = None
        pages_text = req.get("pages")
        if pages_text is not None:
            parsed = parse_locator_page_ranges(
                pages_text.strip()) if isinstance(pages_text, str) else []
            if not parsed:
                raise WriteRefused(
                    '--pages needs explicit PDF page ranges in the locator house '
                    'style, e.g. "pdf pp. 21-26"; it replaces the route locator\'s '
                    "page selection for this call")
            explicit_pages = parsed
        source = repo.sources.get(route.get("source_id"), {})
        projected = project_material_resource(repo, route)
        files = resolve_route_material_files(repo, route)
        status = ("local-observed" if files else
                  "local-unavailable" if projected.get("material_uri") else
                  "remote-unobserved" if route.get("url") or source.get("url") else
                  "unavailable")
        next_action = None
        if status == "remote-unobserved":
            next_action = (
                "Open the URL explicitly to read it. For local extraction, "
                "register an authorized local copy as material, run "
                "make inventory, then rerun material-span "
                f"{unit.id} {route['id']}{placement_flags} --extract. No remote bytes "
                "were observed here."
            )
        elif status == "local-unavailable":
            next_action = (
                "Restore the registered local file, run make inventory, "
                f"then rerun material-span {unit.id} {route['id']}{placement_flags} --extract."
            )
        analysis = _brief_analysis_refs(root, repo, unit, [route], snapshot)
        notes = analysis["analysis_notes"]
        analysis["analysis_notes_total"] = len(notes)
        analysis["analysis_notes_truncated"] = len(notes) > 20
        analysis["analysis_notes"] = notes[:20]
        analysis["expand"] = expansion(
            "plan-edit-context", unit.id, "--route-id", route["id"],
            "--expected-snapshot", snapshot)
        analysis["approved_assessment_routes"] = [
            item for item in analysis["approved_assessment_routes"] if item == route["id"]]
        analysis["stale_assessment_routes"] = [
            item for item in analysis["stale_assessment_routes"] if item == route["id"]]
        spans = []
        materials_real = (repo.learningos_root / "materials").resolve()
        if pinned is not None and len(files) != 1:
            raise _form_refusal(
                ctx, f"--file-sha256 pins one file; route {route['id']} resolves "
                     f"{len(files)} local file(s)")
        for resolved in files:
            path = Path(resolved.path)
            entry = {"material_uri": resolved.material_uri,
                     "format": path.suffix.lower().lstrip(".") or "unknown",
                     "file_sha256": sha256_file(path),
                     "extraction": "not-requested"}
            if pinned is not None and entry["file_sha256"] != pinned:
                _refuse_changed(ctx, f"route {route['id']}'s file", pinned,
                                entry["file_sha256"])
            # A ready analysis binding: exactly what the draft needs,
            # minus inspected_range, in the stored canonical form
            # (materials-relative path, bare hex). Additive only.
            bare_digest = entry["file_sha256"].removeprefix("sha256:")
            entry["binding"] = {
                "resolution": "resolved",
                "source_id": route.get("source_id"),
                "material": path.resolve().relative_to(
                    materials_real).as_posix(),
                "recorded_source_digest": bare_digest,
                "live_source_digest": bare_digest,
            }
            if req.get("extract"):
                try:
                    part = _read_part(route["id"], resolved, route.get("locator", ""),
                                      pages=explicit_pages)
                    if sha256_file(path) != entry["file_sha256"]:
                        raise SliceResolutionError(route["id"], "file changed during inspection")
                    excerpt = part.text[:MAX_EXCERPT]
                    entry.update({"extraction": part.status,
                                  "excerpt": excerpt,
                                  "excerpt_truncated": len(part.text) > MAX_EXCERPT,
                                  "pages": list(part.pages),
                                  "page_total": part.page_total})
                    if part.kind == "text" and excerpt:
                        # Text bindings cite physical, one-based file lines,
                        # including a partly displayed final line.
                        last_line = excerpt.count("\n") + (not excerpt.endswith("\n"))
                        entry["inspected_range_unit"] = "line"
                        entry["inspected_range"] = {"start": 1, "end": last_line}
                except (SliceResolutionError, OSError, UnicodeError) as exc:
                    entry.update({"extraction": "unreadable", "reason": str(exc)})
            spans.append(entry)
        if (req.get("extract") and req.get("pages") is None
                and status == "local-observed" and next_action is None
                and any(span.get("format") == "pdf"
                        and (span.get("extraction") == "truncated"
                             or span.get("excerpt_truncated"))
                        for span in spans)):
            # A cut-off extract is exactly where the unit-scoped page search
            # helps; route the operator there from the output itself.
            next_action = (
                'This excerpt is cut off. Locate the page first: '
                f'material-search --unit {unit.id} "terms", '
                f"then rerun material-span {unit.id} {route['id']}{placement_flags} "
                '--extract --pages "<the hit\'s span_reference pages>".'
            )
        payload = {
            "contract": "material-span-v1", "unit_id": unit.id,
            "module_id": unit.module_id, "route_id": route["id"],
            "source_id": route.get("source_id"),
            "locator": route.get("locator"),
            "url": route.get("url") or source.get("url"),
            "availability": status,
            "next_action": next_action,
            "analysis_refs": analysis,
            "spans": spans,
            "expansion": None if req.get("extract") else expansion(
                "material-span", unit.id, route["id"],
                *([ "--stage", req["stage_id"], "--resource-index",
                    str(req["resource_index"])]
                  if req.get("stage_id") is not None else []),
                "--extract", "--expected-snapshot", snapshot),
        }
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc), site=f"{ctx.operation}.stale-snapshot",
            prefixed=True, exit_code=3,
        ) from exc
    except WriteRefused as exc:
        if exc.gateway_message is None:
            exc.gateway_message = f"los: {exc}"
        if exc.exit_code is None:
            exc.exit_code = 2
        raise
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.read-failed",
            prefixed=True, exit_code=2,
        ) from exc


# ---------------------------------------------------------------------------
# Private reading memory (Plan C, ADR-021): the study read, settlement and the
# study scope of search and context. The store module decides; these handlers
# turn its decisions into typed refusals and contracts.


def _study_session(ctx, req, *, required: bool):
    """The hook-injected study session, or None when the call has no study scope."""
    session = req.get("session")
    if session is None and not required:
        return None
    if not valid_session(session):
        raise WriteRefused(
            "the study session is missing or malformed: the study profile's hook "
            "supplies --session from its own input (a lowercase UUID), and an agent "
            f"never types it (got {session!r})",
            site=f"{ctx.operation}.bad-session", prefixed=True, exit_code=2)
    return session


def _span_runs(pages) -> list[tuple[int, int]]:
    """Contiguous inclusive runs of the physical pages an extraction returned."""
    runs: list[tuple[int, int]] = []
    for page in sorted(set(pages)):
        if runs and page == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], page)
        else:
            runs.append((page, page))
    return runs


def _study_reads(ctx, payload) -> tuple[list[Read], list[dict]]:
    """The gated PDF spans of one material-span answer, or a refusal (P2, P3)."""
    reads: list[Read] = []
    described: list[dict] = []
    for span in payload.get("spans", []):
        excerpt = span.get("excerpt")
        if span.get("extraction") == "unreadable" or not excerpt:
            continue  # nothing was returned, so nothing is owed
        material = (span.get("binding") or {}).get("material") or span.get("material")
        if span.get("format") != "pdf":
            raise WriteRefused(
                f"{material or span.get('material_uri')} is not a PDF: a study read keys "
                "reading memory by PDF page range, so non-PDF text is not served under the "
                "study profile",
                site=f"{ctx.operation}.not-pdf", prefixed=True, exit_code=2)
        pages = list(span.get("pages") or [])
        if span.get("extraction") != "complete" or span.get("excerpt_truncated"):
            first = pages[0] if pages else 1
            raise WriteRefused(
                f"{material} {pages_label(min(pages), max(pages)) if pages else ''} does not fit "
                "one excerpt, so a study read returns no text and opens no entry; read fewer "
                f'pages, e.g. --pages "pdf p. {first}"',
                site=f"{ctx.operation}.clipped", prefixed=True, exit_code=2)
        runs = _span_runs(pages)
        if len(runs) > 1:
            raise WriteRefused(
                f"{material} {pages_label(min(pages), max(pages))} names {len(runs)} "
                "discontiguous page runs, and one excerpt is one combined text, so a "
                "study read of it cannot carry the exact digest of the pages a card "
                "would cover; issue one read per contiguous range, e.g. "
                f'--pages "pdf p. {runs[0][0]}" then --pages "pdf p. {runs[-1][0]}"',
                site=f"{ctx.operation}.discontiguous", prefixed=True, exit_code=2)
        digest = str(span["file_sha256"]).removeprefix("sha256:")
        text_sha = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
        for start, end in runs:
            reads.append(Read(digest=digest, material=material, start=start, end=end,
                              text_sha256=text_sha))
            described.append({"material": material, "file_sha256": f"sha256:{digest}",
                              "pages": pages_label(start, end)})
    return reads, described


def _exact_notes(root, repo, read: Read) -> list[dict]:
    """Durable analysis notes bound to these exact bytes and containing the range."""
    found = []
    for note in _analysis_notes(repo):
        binding = note.meta["material_analysis"]
        rng = binding.get("inspected_range") or {}
        if (binding.get("recorded_source_digest") == read.digest
                and isinstance(rng.get("start"), int) and isinstance(rng.get("end"), int)
                and rng["start"] <= read.start and read.end <= rng["end"]):
            found.append({
                "kind": "analysis-note", "note_id": note.id,
                "path": note.path.relative_to(root).as_posix(),
                "review": note.meta.get("semantic_review"),
                "resolution": binding.get("resolution"),
                "inspected_range": dict(rng),
                "pages": pages_label(rng["start"], rng["end"]),
            })
    return found


def _gate_entries(rows) -> str:
    return ", ".join(f"{row['entry']} ({row['material']} {pages_label(row['inspected_range']['start'], row['inspected_range']['end'])})"
                     for row in rows)


# Lock-order invariant (Phase D watch-point): shared or exclusive operator_lock
# ALWAYS precedes ReadingStore.locked(), and ReadingStore (store layer) never
# acquires operator_lock. Declaring lock="shared" on both study operations keeps
# that order invariant even if CLI metadata sets _operation_kind="tool".
@register("material.study-span", kind="query", lock="shared", effects=OperationEffects.DERIVED_WRITE)
def material_study_span(ctx: OpContext, req: dict) -> Result:
    """A study read: the material-span read, gated by the private reading memory (C1).

    The unchanged material-span answer is computed first, in memory. A PDF
    span no current card or settled dismissal contains then needs a pending
    entry, persisted before this returns; the gate may refuse instead, and
    then no text leaves the gateway.
    """
    session = _study_session(ctx, req, required=True)
    if not req.get("extract"):
        raise WriteRefused(
            "material-study-span always reads text; pass --extract (the study hook "
            "rewrites material-span ... --extract into this command)",
            site=f"{ctx.operation}.needs-extract", prefixed=True, exit_code=2)
    span_req = {key: value for key, value in req.items() if key != "session"}
    payload = material_span(ctx, span_req).payload
    reads, described = _study_reads(ctx, payload)
    store = ReadingStore(ctx.root)
    try:
        admission = store.admit(session, reads)
    except ReadingStoreError as exc:
        raise WriteRefused(
            f"the reading store cannot record this read, so no text is returned: {exc}",
            site=f"{ctx.operation}.store-unavailable", prefixed=True, exit_code=2) from exc
    if admission.refusal == "overdue":
        raise WriteRefused(
            "this session holds overdue reading entries; settle them before reading new "
            f"pages (pending spans stay readable): {_gate_entries(admission.blocking)}",
            site=f"{ctx.operation}.overdue", prefixed=True, exit_code=2,
            remedy="  ||  ".join(settle_command(row["entry"]) for row in admission.blocking))
    if admission.refusal == "adoptable":
        named = "; ".join(f"session {name}: {_gate_entries(rows)}"
                          for name, rows in admission.adoptable.items())
        raise WriteRefused(
            "an ended or idle session left unsettled reading entries; adopt and settle "
            f"them before reading new pages: {named}",
            site=f"{ctx.operation}.adoptable", prefixed=True, exit_code=2,
            remedy="  ||  ".join(adopt_command(name) for name in admission.adoptable))
    if admission.refusal == "limit":
        raise WriteRefused(
            f"this read would hold more than {MAX_OPEN_ENTRIES} open reading entries in one "
            f"turn; settle one first (pending spans stay readable): {_gate_entries(admission.blocking)}",
            site=f"{ctx.operation}.limit", prefixed=True, exit_code=2,
            remedy="  ||  ".join(settle_command(row["entry"]) for row in admission.blocking))
    repo = ctx.repo()
    known = set(repo.concepts)
    rows, memory, seen = [], [], set()
    for state, described_read in zip(admission.states, described, strict=True):
        read = state["read"]
        for note in _exact_notes(ctx.root, repo, read):
            if ("note", note["note_id"]) not in seen:
                seen.add(("note", note["note_id"]))
                memory.append(note)
        covered_by = []
        for item in state.get("covering", []):
            if item.get("record") == "card":
                covered_by.append(item["card"])
                if ("card", item["card"]) not in seen:
                    seen.add(("card", item["card"]))
                    memory.append({"kind": "card", **store.served_card(item, known)})
            else:
                covered_by.append(item["entry"])
                if ("dismissal", item["entry"]) not in seen:
                    seen.add(("dismissal", item["entry"]))
                    memory.append({"kind": "dismissal", **entry_view(item),
                                   "outcome": item["settlement"]["outcome"],
                                   "reason": item["settlement"].get("reason"),
                                   "covering_card": item["settlement"].get("covering_card")})
        for item in state.get("prior_dismissals", []):
            if ("prior-dismissal", item["entry"]) not in seen:
                seen.add(("prior-dismissal", item["entry"]))
                memory.append({"kind": "prior-dismissal", **entry_view(item),
                               "outcome": item["settlement"]["outcome"],
                               "reason": item["settlement"].get("reason"),
                               "covering_card": item["settlement"].get("covering_card")})
        entry = state.get("entry")
        rows.append({**described_read, "state": state["state"],
                     "entry": entry["entry"] if entry else None, "covered_by": covered_by})
    try:
        with store.locked(create=False):
            for read in reads:
                for card in store.cards(read.digest):
                    rng = card["inspected_range"]
                    if (("card", card["card"]) not in seen and rng["start"] <= read.end
                            and read.start <= rng["end"]):
                        seen.add(("card", card["card"]))
                        memory.append({"kind": "card", **store.served_card(card, known)})
    except ReadingStoreError as exc:
        raise WriteRefused(
            f"the reading store cannot be read, so no text is returned: {exc}",
            site=f"{ctx.operation}.store-unavailable", prefixed=True, exit_code=2) from exc
    memory.sort(key=lambda row: 0 if row["kind"] == "analysis-note" else 1)
    open_rows = [entry_view(row) for row in admission.open_entries]
    next_action = None
    if open_rows:
        next_action = (
            f"Before the turn ends, settle each open entry ({len(open_rows)} of at most "
            f"{MAX_OPEN_ENTRIES}): save a card or dismiss it. "
            + "  ||  ".join(settle_command(row["entry"]) for row in open_rows[:MAX_OPEN_ENTRIES]))
    return Result({
        "schema_version": 1, "snapshot_id": payload["snapshot_id"],
        "contract": "material-study-span-v1", "span": payload,
        "study": {"session": session, "reads": rows, "memory": memory,
                  "open_entries": open_rows, "limit": MAX_OPEN_ENTRIES,
                  "next_action": next_action},
    })


def _settle_result(ctx, repo, session, settlement, store) -> Result:
    known = set(repo.concepts)
    return Result({
        "schema_version": 1, "contract": "material-card-settle-v1",
        "session": session, "outcome": settlement.outcome,
        "replayed": settlement.replayed,
        "entries": [entry_view(row) for row in settlement.entries],
        "card": (store.served_card(settlement.card, known)
                 if settlement.card is not None else None),
        "remaining": [entry_view(row) for row in settlement.remaining],
    })


@register("material.card.settle", kind="tool", lock="shared", effects=OperationEffects.DERIVED_WRITE)
def material_card_settle(ctx: OpContext, req: dict) -> Result:
    """Settle one reading entry, or adopt an ended or idle session's entries (step 3, C7)."""
    session = _study_session(ctx, req, required=True)
    modes = [name for name in ("card", "dismiss", "source_changed", "source_gone", "adopt")
             if req.get(name) not in (None, False)]
    entry = req.get("entry")
    if len(modes) != 1 or (modes == ["adopt"]) == (entry is not None):
        raise WriteRefused(
            "material-card-settle takes ENTRY with exactly one of --card JSON, --dismiss "
            "irrelevant|redundant, --source-changed or --source-gone; or --adopt SESSION "
            "without ENTRY",
            site=f"{ctx.operation}.bad-form", prefixed=True, exit_code=2)
    if req.get("observed_sha256") is not None and modes != ["source_changed"]:
        raise WriteRefused(
            "--observed-sha256 belongs to --source-changed only",
            site=f"{ctx.operation}.bad-form", prefixed=True, exit_code=2)
    store = ReadingStore(ctx.root)
    repo = ctx.repo()
    try:
        if modes == ["card"]:
            settlement = store.save(session, entry, req["card"])
        elif modes == ["dismiss"]:
            settlement = store.dismiss(session, entry, req["dismiss"], reason=req.get("reason"),
                                       covering_card=req.get("covering_card"))
        elif modes == ["adopt"]:
            settlement = store.adopt(session, req["adopt"])
        else:
            settlement = store.close_source(
                session, entry, gone=modes == ["source_gone"],
                observed=req.get("observed_sha256"),
                materials_root=repo.learningos_root / "materials")
    except ReadingStoreError as exc:
        raise WriteRefused(
            f"the reading store cannot be updated; the entry stays as it was: {exc}",
            site=f"{ctx.operation}.store-unavailable", prefixed=True, exit_code=2) from exc
    except SettleRefusal as exc:
        if exc.slug == "bad-card":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.bad-card", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "bad-dismissal":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.bad-dismissal", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "not-covering":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.not-covering", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "source-check":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.source-check", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "already-settled":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.already-settled", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "not-owner":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.not-owner", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug == "adopt-live":
            raise WriteRefused(str(exc), site=f"{ctx.operation}.adopt-live", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        if exc.slug in ("bad-adopt", "nothing-to-adopt"):
            raise WriteRefused(str(exc), site=f"{ctx.operation}.bad-adopt", prefixed=True,
                               exit_code=2, remedy=exc.remedy) from exc
        raise WriteRefused(str(exc), site=f"{ctx.operation}.unknown-entry", prefixed=True,
                           exit_code=2, remedy=exc.remedy) from exc
    return _settle_result(ctx, repo, session, settlement, store)


def _study_hit_cards(ctx, repo, session, payload) -> None:
    """Attach compact current cards to each search hit whose pages they overlap."""
    store = ReadingStore(ctx.root)
    known = set(repo.concepts)
    attached = 0
    study: dict = {"session": session,
                   "review": "unreviewed private cards; never coverage evidence"}
    try:
        with store.locked(create=False):
            for hit in payload.get("hits", []):
                digest = str(hit.get("sha256") or "").removeprefix("sha256:")
                ranges = parse_locator_page_ranges(str(hit.get("span_pages") or ""))
                if not ranges:
                    hit["cards"] = []
                    continue
                start, end = ranges[0][0], ranges[-1][1]
                cards = [store.served_card(card, known, compact=True)
                         for card in store.cards(digest)
                         if card["inspected_range"]["start"] <= end
                         and start <= card["inspected_range"]["end"]]
                hit["cards"] = cards[:3]
                attached += len(hit["cards"])
    except ReadingStoreError as exc:
        study["cards_unavailable"] = str(exc)
    study["cards"] = attached
    payload["study"] = study


def _study_context_cards(ctx, repo, *, raw_terms, concept_id, material) -> dict:
    """Current cards matching the need: every query word, the concept, the material."""
    store = ReadingStore(ctx.root)
    known = set(repo.concepts)
    words = [term.casefold() for term in raw_terms]
    try:
        with store.locked(create=False):
            rows = store.all_cards()
    except ReadingStoreError as exc:
        return {"items": [], "total": 0, "cards_unavailable": str(exc)}
    matched = []
    for card in rows:
        if material and card["material"] != material:
            continue
        if concept_id and concept_id not in (card.get("concepts") or []):
            continue
        text = " ".join([card["paraphrase"], *(row["label"] for row in card["pointers"])]).casefold()
        if any(word not in text for word in words):
            continue
        matched.append(card)
    matched.sort(key=lambda card: (card["material"], card["inspected_range"]["start"], card["card"]))
    return {"items": [store.served_card(card, known, compact=True) for card in matched[:5]],
            "total": len(matched),
            "review": "unreviewed private cards; never coverage evidence"}


ASSESSMENT_TEXT_FIELDS = ("contribution", "assumptions", "notation",
                          "exercise_value", "best_for", "limitations",
                          "locator")

_CONCEPT_VIA_LIMIT = 20

_ANCHOR_PREVIEW_LIMIT = 8

_ANCHOR_TEXT_LIMIT = 200


def _unit_route_pairs(repo, unit_id) -> list:
    """(source_id, route-dict) pairs routed to one unit.

    The same membership the scope check always used — a bare unit id or
    an expanded route carrying it — with string routes arriving as empty
    dicts so the shared rule, not the caller, decides what they prove.
    """
    unit = repo.units[unit_id]
    source_map = repo.module_source_maps.get(unit.module_id) or {}
    pairs = []
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict) or not source.get("source_id"):
            continue
        for route in source.get("unit_routes", []) or []:
            if route == unit.id:
                pairs.append((source["source_id"], {}))
            elif isinstance(route, dict) and route.get("unit_id") == unit.id:
                pairs.append((source["source_id"], route))
    return pairs

def _route_material_index(repo, unit_id=None) -> dict:
    """route_id -> (source_id, route-dict), for one unit or every module."""
    if unit_id is not None:
        return {route.get("id"): pair for pair in _unit_route_pairs(repo, unit_id)
                for route in [pair[1]] if route.get("id")}
    index = {}
    for source_map in (repo.module_source_maps or {}).values():
        if not isinstance(source_map, dict):
            continue
        for source in source_map.get("sources", []) or []:
            if not isinstance(source, dict) or not source.get("source_id"):
                continue
            for route in source.get("unit_routes", []) or []:
                if isinstance(route, dict) and route.get("id"):
                    index.setdefault(route["id"], (source["source_id"], route))
    return index

def _concept_stage_routes(repo) -> dict[str, dict[str, list[tuple[str, dict]]]]:
    """concept id -> stage id -> the (source_id, route) pairs that stage places (F12).

    A stage joins a concept to a route when it tags the concept AND places
    the route — two declared edges, read-side only. Nothing is inferred and
    nothing is recorded: analysis notes carry no concept tags by
    construction, so without this join the concept filter's note branch
    could never match them. A note then joins only through the shared
    note-to-route rule (`_unit_note_scope`), never through a shared source
    id alone: one source (a lecture deck, a textbook) serves many concepts,
    and an analysis of its other pages is not evidence for this one.
    """
    routes = _route_material_index(repo, None)
    joined: dict[str, dict[str, list[tuple[str, dict]]]] = {}
    for map_id in sorted(repo.study_maps):
        stages = repo.study_maps[map_id].data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            stage_id = stage.get("id")
            if not isinstance(stage_id, str) or not stage_id:
                continue
            concepts = stage.get("concepts") or []
            if not concepts:
                continue
            placed: list[tuple[str, dict]] = []
            for resource in stage.get("resources", []) or []:
                if not isinstance(resource, dict):
                    continue
                route_id = resource.get("route_id")
                if not route_id and isinstance(
                        resource.get("material_ref"), dict):
                    route_id = resource["material_ref"].get("route_id")
                hit = routes.get(route_id)
                if hit is not None and isinstance(hit[0], str) and hit[0]:
                    placed.append(hit)
            if not placed:
                continue
            for concept_id in concepts:
                if not isinstance(concept_id, str) or not concept_id:
                    continue
                joined.setdefault(concept_id, {}).setdefault(
                    stage_id, []).extend(placed)
    return joined

def _explanation_snippets(title, text, body_offset, terms) -> list:
    """Title label plus true-file-line body windows for matched terms.

    A title hit yields one title snippet; body hits reuse the content
    search's windowing over the full text, so the reported lines are true
    file lines even though matching never sees the frontmatter. At most
    eight snippets either way, the title counting as one.
    """
    snippets = []
    if any(regex.search(title) for regex in terms):
        snippets.append({"label": "title", "text": title})
    body = text[body_offset:]
    positions = sorted({match.start() for regex in terms
                        if (match := regex.search(body)) is not None})
    for position in positions[:8 - len(snippets)]:
        absolute = body_offset + position
        start = max(text.rfind("\n", 0, absolute) + 1, absolute - 100)
        end = text.find("\n", absolute)
        end = min(end if end >= 0 else len(text), absolute + 180)
        snippets.append({"line": text.count("\n", 0, absolute) + 1,
                         "text": text[start:end]})
    return snippets

def _observations_digest(observations: dict) -> str:
    encoded = json.dumps(
        {key: observations[key] for key in sorted(observations)},
        ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

def _note_purpose_hit(binding, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    anchors = binding.get("anchors")
    if not isinstance(anchors, list):
        return False
    return any(wanted in str(anchor.get("purpose", "")).casefold()
               for anchor in anchors if isinstance(anchor, dict))

def _assessment_purpose_hit(assessment, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    return any(wanted in str(assessment.get(field) or "").casefold()
               for field in ("best_for", "exercise_value"))

def _anchor_purpose_hit(anchor, wanted) -> bool:
    return (isinstance(anchor, dict)
            and wanted in str(anchor.get("purpose", "")).casefold())

def _anchor_selection(anchors, purpose):
    """Original-order anchors with literal purpose matches first, deduplicated.

    Returns (ordered, match_count): match_count is None without a purpose
    filter. Both groups keep file order; no anchor appears twice.
    """
    if not purpose:
        return list(anchors), None
    wanted = purpose.casefold()
    matches = [anchor for anchor in anchors
               if _anchor_purpose_hit(anchor, wanted)]
    seen = {id(anchor) for anchor in matches}
    return (matches + [anchor for anchor in anchors
                       if id(anchor) not in seen], len(matches))

def _clipped_name(value):
    """A route's title or angle for display beside its id, bounded; else None."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value[:_ANCHOR_TEXT_LIMIT]


def _clip_anchor_text(anchor):
    """The anchor with every long text field bounded, naming what clipped."""
    if not isinstance(anchor, dict):
        return anchor
    clipped = []
    shaped = {}
    for key, value in anchor.items():
        if isinstance(value, str) and len(value) > _ANCHOR_TEXT_LIMIT:
            shaped[key] = value[:_ANCHOR_TEXT_LIMIT]
            clipped.append(key)
        else:
            shaped[key] = value
    shaped["clipped_fields"] = clipped
    return shaped

def _analysis_note_item(root, note, *, raw_terms, terms, concept_id, purpose,
                        unit, material_ref, scope, evidence, observations,
                        include_anchors=False, concept_via=None):
    """One matched analysis note, or None when the terms miss.

    Terms match the explanation text — title plus body — with lexical AND;
    frontmatter (provenance paths, digests, ids) never matches. Title hits
    yield a title snippet; body hits yield true file line numbers. The
    scope label exists only under --unit, where direct and related mean
    something. Anchors preview bounded (purpose matches first) with exact
    totals; the complete index needs the explicit expansion.
    """
    raw = _note_bytes(root, note)
    text = raw.decode("utf-8")
    title = note.meta.get("title", note.id)
    front = FRONTMATTER_RE.match(text)
    body_offset = front.end() if front else 0
    body = text[body_offset:]
    matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
               if regex.search(title) or regex.search(body)]
    if len(matched) != len(raw_terms):
        return None
    binding = note.meta["material_analysis"]
    inspected = binding.get("inspected_range") or {}
    reasons = {"terms": matched}
    if concept_id is not None:
        reasons["concept"] = concept_id
    if concept_via:
        reasons["concept_via"] = [f"stage:{stage_id}" for stage_id in concept_via]
    if purpose:
        reasons["purpose"] = purpose
    if unit:
        reasons["unit"] = unit
    if material_ref is not None:
        reasons["material"] = material_ref
    item = {
        "origin": "analysis-note",
        "id": note.id, "title": title,
        "path": note.path.relative_to(root).as_posix(),
        "use_evidence": _evidence_label(
            evidence.get(binding.get("source_id")) or {}),
        "match": {**reasons, "snippets": _explanation_snippets(
            title, text, body_offset, terms)},
        "source": {
            "ref": binding.get("material"),
            "pages": [inspected.get("start"), inspected.get("end")],
            "freshness": _freshness_label(root, binding, observations),
        },
        "review": {
            "semantic_review": note.meta.get("semantic_review"),
            "resolution": binding.get("resolution"),
        },
    }
    anchors = binding.get("anchors") or []
    ordered, match_count = _anchor_selection(anchors, purpose)
    if include_anchors:
        item["anchors"] = list(anchors)
        item["anchor_returned"] = len(anchors)
        item["anchors_truncated"] = False
    else:
        item["anchors"] = [_clip_anchor_text(anchor)
                           for anchor in ordered[:_ANCHOR_PREVIEW_LIMIT]]
        item["anchor_returned"] = len(item["anchors"])
        item["anchors_truncated"] = len(anchors) > _ANCHOR_PREVIEW_LIMIT
    item["anchor_total"] = len(anchors)
    if purpose:
        item["purpose_match_count"] = match_count
        item["purpose_other_count"] = len(anchors) - match_count
    if scope is not None:
        item["scope"] = scope
    return item


def _resolve_concept(ctx, repo, raw):
    """A concept id or declared alias, matched case-insensitively.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); only the miss carries the caller's site, the
    ambiguous match keeps the legacy plain refusal and its text.
    """
    if raw in repo.concepts:
        return raw
    lowered = raw.casefold()
    hits = [cid for cid, concept in repo.concepts.items()
            if isinstance(concept, dict)
            and any(str(alias).casefold() == lowered
                    for alias in (concept.get("aliases") or []))]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise WriteRefused(
            f"unknown concept: {raw!r} matches no id or declared alias",
            site=f"{ctx.operation}.unknown-concept")
    raise WriteRefused(f"concept {raw!r} is ambiguous across {len(hits)} concepts; use an id")


def _check_material_ref(ctx, root, ref) -> str:
    """The exact materials-tree path a --material filter names, else refused.

    Exact: no canonicalization, so a near-miss matches nothing rather than
    something nearby. The boundary is still enforced — an escape refuses
    instead of reading outside the tree.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); only the caller's site is added.
    """
    materials = root.parent / "materials"
    pure = PurePosixPath(ref) if isinstance(ref, str) else None
    if (pure is None or not ref or pure.is_absolute()
            or "\\" in ref
            or any(part in {".", ".."} for part in pure.parts)):
        raise WriteRefused(
            f"--material must be a materials-tree-relative path: {ref!r}",
            site=f"{ctx.operation}.bad-material")
    try:
        (materials / ref).resolve(strict=False).relative_to(materials.resolve())
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            f"--material must be a materials-tree-relative path: {ref!r}",
            site=f"{ctx.operation}.bad-material") from exc
    return ref


def _anchor_expansion_command(req, limit, snapshot, observed) -> str:
    """Re-run this read's selected page with complete anchor indexes.

    Moved from ``commands.reads`` with its last legacy caller (SPEC
    (bo) item 2); the request replaces the namespace.
    """
    parts = ["material-context", req.get("query") or ""]
    if req.get("concept"):
        parts += ["--concept", req["concept"]]
    if req.get("purpose"):
        parts += ["--purpose", req["purpose"]]
    if req.get("unit"):
        parts += ["--unit", req["unit"]]
    if req.get("material"):
        parts += ["--material", req["material"]]
    if req.get("include_related", False):
        parts += ["--include-related"]
    parts += ["--include-anchors", "--limit", str(limit),
              "--offset", str(req.get("offset")),
              "--expected-snapshot", snapshot,
              "--expected-observations", observed]
    return expansion(*parts)


@register("material.context", kind="query", effects=OperationEffects.READ)
def material_context(ctx: OpContext, req: dict) -> Result:
    """Find saved explanations from an explanation need."""
    root = ctx.root
    try:
        session = _study_session(ctx, req, required=False)
        try:
            # An explicit limit passes through verbatim, so 0 reaches the
            # 1..maximum check and is refused by the existing bad-window
            # site; only an absent limit takes the default page.
            req_limit = req.get("limit")
            offset, limit = _window_values(
                req.get("offset") or 0,
                20 if req_limit is None else req_limit,
                req.get("expected_snapshot"), 20)
        except WriteRefused as exc:
            exc.site = f"{ctx.operation}.bad-window"
            raise
        if offset and not req.get("expected_observations"):
            raise WriteRefused(
                "continuation requires --expected-observations from the "
                "previous response",
                site=f"{ctx.operation}.offset-needs-observations")
        raw_terms = (req.get("query") or "").split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        material_ref = req.get("material")
        if not terms and material_ref is None and not req.get("concept"):
            raise WriteRefused(
                "material context requires a nonempty query, --concept, "
                "or --material",
                site=f"{ctx.operation}.empty-need")
        if req.get("include_related") and not req.get("unit"):
            raise WriteRefused("--include-related needs --unit",
                               site=f"{ctx.operation}.related-needs-unit")
        if material_ref is not None:
            _check_material_ref(ctx, root, material_ref)
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        repo = ctx.repo()
        note_dir = root / "knowledge" / "notes"
        note_failures = [
            (path, message) for path, message in repo.parse_failures
            if path.is_relative_to(note_dir)
        ]
        if note_failures:
            raise WriteRefused(unreadable_refusal(root, note_failures, "context"))
        synthesis_failures = [
            (path, message) for path, message in repo.parse_failures
            if path.name == "material-synthesis.yaml"
        ]
        if synthesis_failures:
            raise WriteRefused(unreadable_refusal(root, synthesis_failures, "context"))
        concept_id = _resolve_concept(ctx, repo, req["concept"]) \
            if req.get("concept") else None
        if req.get("unit") and req["unit"] not in repo.units:
            complaint = with_suggestions(
                f"unknown unit: {req['unit']!r}", req["unit"], repo.units)
            raise NotFound("unit", req["unit"], repo.units,
                           message=complaint,
                           site=f"{ctx.operation}.unknown-unit")
        assessments = _approved_assessments(repo)
        related_count = 0
        searched_related: list = []
        if req.get("unit"):
            assessments = [row for row in assessments if row[1] == req["unit"]]
            pairs = _unit_route_pairs(repo, req["unit"])
            direct_pool = []
            related_pool = []
            for note in _analysis_notes(repo):
                standing = _unit_note_scope(
                    repo, note.meta.get("material_analysis") or {}, pairs)
                if standing == "direct":
                    direct_pool.append(note)
                elif standing == "related":
                    related_pool.append(note)
            notes = direct_pool
            related_count = len(related_pool)
            if req.get("include_related"):
                searched_related = related_pool
        else:
            notes = _analysis_notes(repo)
        if concept_id is not None:
            concept_join = _concept_stage_routes(repo).get(concept_id, {})

            def _note_concept_via(note) -> list[str]:
                binding = note.meta.get("material_analysis") or {}
                if not isinstance(binding, dict):
                    return []
                via = [stage_id
                       for stage_id, placed in sorted(concept_join.items())
                       if _unit_note_scope(repo, binding, placed) == "direct"]
                return via[:_CONCEPT_VIA_LIMIT]

            def _note_matches_concept(note) -> bool:
                return (concept_id in (note.meta.get("concepts") or [])
                        or bool(_note_concept_via(note)))

            notes = [note for note in notes
                     if _note_matches_concept(note)]
            searched_related = [
                note for note in searched_related
                if _note_matches_concept(note)]
            assessments = [row for row in assessments
                           if concept_id in (row[2].get("concept_ids") or [])]
            via_by_note = {note.id: _note_concept_via(note)
                           for note in (*notes, *searched_related)}
        else:
            via_by_note = {}
        notes = [note for note in notes
                 if _note_purpose_hit(note.meta["material_analysis"], req.get("purpose"))]
        searched_related = [
            note for note in searched_related
            if _note_purpose_hit(note.meta["material_analysis"], req.get("purpose"))]
        assessments = [row for row in assessments
                       if _assessment_purpose_hit(row[2], req.get("purpose"))]
        if material_ref is not None:
            notes = [note for note in notes
                     if (note.meta.get("material_analysis") or {}).get("material")
                     == material_ref]
            searched_related = [
                note for note in searched_related
                if (note.meta.get("material_analysis") or {}).get("material")
                == material_ref]
            route_index = _route_material_index(repo, req.get("unit"))
            assessments = [
                row for row in assessments
                if material_ref in _route_material_files(
                    repo, *route_index.get(row[2].get("route_id"), (None, {})))]
        # Use evidence is deliberately global: feedback says a source
        # served in some stage, which bears on every result bound to
        # that source, however the query scoped the pool.
        evidence = _use_evidence(repo)
        # Readable names beside every route id the answer carries: a bare
        # route-<hash> tells the reader nothing about which material it is.
        named_routes = _route_material_index(repo, None) if assessments else {}
        pool = {
            "analysis_notes": len(notes),
            "assessments": len(assessments),
            # Related notes are counted, never pooled: the resolution
            # tallies below describe the default-visible direct set.
            "related_analysis_notes": related_count,
            "analysis_by_resolution": {},
            "analysis_unreviewed": 0,
        }
        for note in notes:
            binding = note.meta["material_analysis"]
            resolution = binding.get("resolution")
            pool["analysis_by_resolution"][resolution] = \
                pool["analysis_by_resolution"].get(resolution, 0) + 1
            if note.meta.get("semantic_review") == "unreviewed":
                pool["analysis_unreviewed"] += 1
        items = []
        observations: dict[str, str] = {}
        dossier_freshness: dict[str, dict] = {}
        include_anchors = bool(req.get("include_anchors", False))
        for note in notes:
            item = _analysis_note_item(
                root, note, raw_terms=raw_terms, terms=terms,
                concept_id=concept_id, purpose=req.get("purpose"),
                unit=req.get("unit"), material_ref=material_ref,
                scope="direct" if req.get("unit") else None,
                evidence=evidence, observations=observations,
                include_anchors=include_anchors,
                concept_via=via_by_note.get(note.id))
            if item is not None:
                items.append(item)
        for synthesis_id, unit_id, assessment in assessments:
            joined = "\n".join(str(assessment.get(field) or "")
                               for field in ASSESSMENT_TEXT_FIELDS)
            matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
                       if regex.search(joined)]
            if len(matched) != len(raw_terms):
                continue
            excerpts = []
            for field in ASSESSMENT_TEXT_FIELDS:
                if len(excerpts) >= 3:
                    break
                value = str(assessment.get(field) or "")
                if value and any(regex.search(value) for regex in terms):
                    excerpts.append({"field": field, "text": value[:200]})
            reasons = {"terms": matched}
            if concept_id is not None:
                reasons["concept"] = concept_id
            if req.get("purpose"):
                reasons["purpose"] = req["purpose"]
            if req.get("unit"):
                reasons["unit"] = req["unit"]
            if material_ref is not None:
                reasons["material"] = material_ref
            origin = repo.unit_material_synthesis_origins.get(synthesis_id)
            fresh = dossier_freshness.get(synthesis_id)
            if fresh is None:
                dossier = repo.unit_material_syntheses.get(synthesis_id)
                material_hashes = {}
                fresh = material_synthesis_freshness(
                    root, unit_id, dossier
                    if isinstance(dossier, dict) else {}, repo=repo,
                    cache=material_hashes)
                dossier_freshness[synthesis_id] = fresh
                observations[f"dossier:{synthesis_id}"] = (
                    f"{fresh['status']}:{','.join(fresh['reasons'])}")
                # Bind the bytes actually read by the shared freshness
                # calculation: two different sources can both be stale
                # for the same reason. Missing files remove an entry;
                # newly available files add one on the next read.
                observations.update({
                    f"dossier-material:{path}": digest
                    for path, digest in material_hashes.items()
                })
            named = named_routes.get(assessment.get("route_id"), (None, {}))[1]
            items.append({
                "origin": "unit-assessment",
                "unit_id": unit_id, "synthesis_id": synthesis_id,
                "use_evidence": _evidence_label(
                    evidence.get(assessment.get("source_id")) or {}),
                "route_id": assessment.get("route_id"),
                "route_title": _clipped_name(named.get("title")),
                "route_angle": _clipped_name(named.get("angle")),
                "source_id": assessment.get("source_id"),
                "locator": assessment.get("locator"),
                "review_status": assessment.get("review_status"),
                "freshness": fresh,
                "concept_ids": assessment.get("concept_ids") or [],
                "match": {**reasons, "excerpts": excerpts},
                "open": {
                    "synthesis": origin.relative_to(root).as_posix()
                    if origin is not None else None,
                    "route_id": assessment.get("route_id"),
                },
            })
        related_items = []
        for note in searched_related:
            item = _analysis_note_item(
                root, note, raw_terms=raw_terms, terms=terms,
                concept_id=concept_id, purpose=req.get("purpose"),
                unit=req.get("unit"), material_ref=material_ref,
                scope="related",
                evidence=evidence, observations=observations,
                include_anchors=include_anchors,
                concept_via=via_by_note.get(note.id))
            if item is not None:
                related_items.append(item)
        # Stable sort: evidence ranks, ties keep insertion order
        # (notes by id, then assessments by unit and route). Without
        # recorded feedback every key is (0, 0) and the order is
        # exactly the pre-ranking stable order. Related notes rank
        # under the same key but append after every direct item.
        items.sort(key=lambda row: (-row["use_evidence"]["positive"],
                                    row["use_evidence"]["mismatch"]))
        related_items.sort(key=lambda row: (
            -row["use_evidence"]["positive"],
            row["use_evidence"]["mismatch"]))
        items.extend(related_items)
        # The continuation binds the normalized filters alongside the
        # observed bytes: equivalent filters (reordered terms, a
        # concept alias for its id) page on, changed ones refuse.
        observations["filter/query"] = " ".join(
            sorted(term.casefold() for term in raw_terms))
        observations["filter/unit"] = req.get("unit") or ""
        observations["filter/concept"] = concept_id or ""
        observations["filter/purpose"] = (req.get("purpose") or "").casefold()
        observations["filter/material"] = material_ref or ""
        observations["filter/related"] = \
            "related" if req.get("include_related") else "direct"
        observed = _observations_digest(observations)
        expected_observations = req.get("expected_observations")
        if expected_observations is not None and expected_observations != observed:
            raise StaleSnapshot(
                "material or filters observed by this query changed "
                "between pages; re-run from offset 0")
        ranked_by = ("recorded stage use-evidence per source: positive "
                     "feedback first, mismatch feedback last; ties keep "
                     "stable order (notes by id, then assessments by "
                     "unit and route)")
        if req.get("include_related"):
            ranked_by += ("; --include-related appends related notes "
                          "under the same ranking")
        returned = items[offset:offset + limit]
        payload = {
            "contract": "material-context",
            "ranked_by": ranked_by,
            "items": returned,
            "total": len(items),
            "next_offset": offset + limit if offset + limit < len(items) else None,
            "observations_sha256": observed,
            "searched": {
                "query_terms": raw_terms, "concept": concept_id,
                "purpose": req.get("purpose"), "unit": req.get("unit"),
                "material": material_ref,
                "include_related": bool(req.get("include_related")),
                "analysis_notes": len(_analysis_notes(repo)),
                "assessments": len(_approved_assessments(repo)),
            },
            "pool": pool,
        }
        if not items:
            payload["empty"] = (
                "no match in the searched records; this never proves "
                "no source explains the topic")
        if not include_anchors and any(
                item.get("origin") == "analysis-note"
                and (item.get("anchors_truncated")
                     or any(row.get("clipped_fields")
                            for row in item.get("anchors", [])
                            if isinstance(row, dict)))
                for item in returned):
            payload["expand"] = {"anchors": _anchor_expansion_command(
                req, limit, snapshot, observed)}
        if session is not None:
            payload["study_cards"] = _study_context_cards(
                ctx, repo, raw_terms=raw_terms, concept_id=concept_id,
                material=material_ref)
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc), site=f"{ctx.operation}.stale-snapshot",
            prefixed=True, exit_code=3,
        ) from exc
    except WriteRefused as exc:
        if exc.gateway_message is None:
            exc.gateway_message = f"los: {exc}"
        if exc.exit_code is None:
            exc.exit_code = 2
        raise
    except (OSError, UnicodeError) as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.read-failed",
            prefixed=True, exit_code=2,
        ) from exc


@register("material.search", kind="query", effects=OperationEffects.READ)
def material_search(ctx: OpContext, req: dict) -> Result:
    """Search local learning materials and return bounded candidate references."""
    from learning_os.store.materials.search_index import (
        DEFAULT_SEARCH_LIMIT,
        MAX_QUERY_LENGTH,
        MAX_QUERY_TERMS,
        MAX_SEARCH_LIMIT,
        MAX_SEARCH_OFFSET,
        execute_search,
        normalize_query_terms,
    )

    root = ctx.root
    session = _study_session(ctx, req, required=False)
    raw_query = req.get("query") or ""
    if not isinstance(raw_query, str) or not raw_query.strip():
        raise WriteRefused(
            "material.search requires a nonempty query",
            site=f"{ctx.operation}.empty-query",
            prefixed=True,
            exit_code=2,
        )
    if len(raw_query) > MAX_QUERY_LENGTH:
        raise WriteRefused(
            f"query length {len(raw_query)} exceeds maximum of {MAX_QUERY_LENGTH} characters",
            site=f"{ctx.operation}.query-too-long",
            prefixed=True,
            exit_code=2,
        )

    limit = req.get("limit") if req.get("limit") is not None else DEFAULT_SEARCH_LIMIT
    offset = req.get("offset") if req.get("offset") is not None else 0
    if (
        not isinstance(offset, int)
        or isinstance(offset, bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or offset < 0
        or offset > MAX_SEARCH_OFFSET
        or not (1 <= limit <= MAX_SEARCH_LIMIT)
    ):
        raise WriteRefused(
            f"offset must be between 0 and {MAX_SEARCH_OFFSET} and limit between 1 and {MAX_SEARCH_LIMIT}",
            site=f"{ctx.operation}.offset-too-large",
            prefixed=True,
            exit_code=2,
        )

    clean_query = raw_query.strip()
    terms = normalize_query_terms(clean_query)
    if not terms:
        raise WriteRefused(
            "material.search query contains no searchable terms after normalization",
            site=f"{ctx.operation}.no-terms",
            prefixed=True,
            exit_code=2,
        )
    if len(terms) > MAX_QUERY_TERMS:
        raise WriteRefused(
            f"material.search query has {len(terms)} terms after normalization (maximum is {MAX_QUERY_TERMS})",
            site=f"{ctx.operation}.too-many-terms",
            prefixed=True,
            exit_code=2,
        )

    unit_filter = req.get("unit")
    module_filter = req.get("module")
    repo = ctx.repo()

    if unit_filter and unit_filter not in repo.units:
        complaint = with_suggestions(
            f"unknown unit: {unit_filter!r}", unit_filter, repo.units
        )
        raise NotFound(
            "unit",
            unit_filter,
            repo.units,
            message=complaint,
            site=f"{ctx.operation}.unknown-unit",
            gateway_message=f"los: {complaint}",
            exit_code=2,
        )
    if module_filter and module_filter not in repo.modules:
        complaint = with_suggestions(
            f"unknown module: {module_filter!r}", module_filter, repo.modules
        )
        raise NotFound(
            "module",
            module_filter,
            repo.modules,
            message=complaint,
            site=f"{ctx.operation}.unknown-module",
            gateway_message=f"los: {complaint}",
            exit_code=2,
        )

    search_res = execute_search(
        repo_root=root,
        query=clean_query,
        limit=limit,
        offset=offset,
        unit_id=unit_filter,
        module_id=module_filter,
        repo=repo,
    )

    snapshot_val = _snapshot(root)
    payload = search_res.to_dict()
    payload["snapshot_id"] = snapshot_val
    if session is not None:
        _study_hit_cards(ctx, repo, session, payload)

    return Result(payload)

