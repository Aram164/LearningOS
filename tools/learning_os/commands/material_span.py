"""One common source-span description, with optional bounded local inspection."""

from __future__ import annotations

from pathlib import Path

from ..loader import load_repo
from ..material_refs import unit_routes
from ..material_slices import SliceResolutionError, _read_part
from ..materials_resolution import (
    project_material_resource,
    resolve_route_material_files,
    sha256_file,
)
from .material import _brief_analysis_refs, _map_for_unit, _route_entry
from .reads import _print_stable, _refusal, _snapshot
from .suggest import MAX_SUGGESTIONS, expansion, suggest, with_suggestions
from .support import WriteRefused, _operator_lock, _root

MAX_EXCERPT = 6000


def _placement_route(repo, unit, source_map, routes, route, args):
    """Use only a snapshot-bound canonical placement, never caller-supplied paths."""
    stage_id = getattr(args, "stage_id", None)
    index = getattr(args, "resource_index", None)
    if bool(stage_id) != (index is not None):
        raise WriteRefused("--stage and --resource-index must be supplied together")
    if not stage_id:
        return route, ""
    study_map = _map_for_unit(repo, unit.id)
    if study_map is None:
        raise WriteRefused("unit has no stage placement to inspect")
    stages = [row for row in study_map.data.get("stages", [])
              if isinstance(row, dict) and row.get("id") == stage_id]
    if len(stages) != 1 or index < 0 or index >= len(stages[0].get("resources", [])):
        raise WriteRefused("placement is missing or ambiguous in this unit")
    uses = _route_entry(routes, study_map, source_map, unit, route["id"])["uses"]
    if not any(use["stage_id"] == stage_id and use["resource_index"] == index
               for use in uses):
        raise WriteRefused("placement is missing or does not belong to this route")
    resource = stages[0]["resources"][index]
    if resource.get("source_id") != route.get("source_id"):
        raise WriteRefused("placement source does not match its route")
    selected = {**route, **{key: resource[key] for key in ("locator", "vault_path", "url")
                           if key in resource}}
    return selected, f" --stage {stage_id} --resource-index {index}"


def cmd_material_span(args) -> int:
    root = _root(args)
    try:
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            unit = repo.units.get(args.unit_id)
            if unit is None:
                raise WriteRefused(with_suggestions(
                    f"unknown unit {args.unit_id}", args.unit_id, repo.units))
            source_map = repo.module_source_maps.get(unit.module_id)
            if source_map is None:
                raise WriteRefused("unit has no module source map")
            routes = unit_routes(source_map, unit.module_id, unit.id)
            matches = [row for row in routes
                       if row["id"] == args.route_id]
            if len(matches) > 1:
                raise WriteRefused(
                    f"route {args.route_id} is ambiguous in {unit.id}: "
                    f"{len(matches)} matches")
            if not matches:
                route_ids = sorted(row["id"] for row in routes if row.get("id"))
                base = f"route not found: {args.route_id} in {unit.id}"
                if suggest(args.route_id, route_ids):
                    raise WriteRefused(with_suggestions(
                        base, args.route_id, route_ids))
                # No ranked near-miss: still name the unit's routes, bounded,
                # so the caller picks an existing one instead of guessing.
                listed = route_ids[:MAX_SUGGESTIONS]
                extra = len(route_ids) - len(listed)
                detail = ", ".join([*listed, f"+{extra} more"] if extra > 0
                                   else listed)
                raise WriteRefused(
                    f"{base} (routes: {detail})" if detail else base)
            route, placement_flags = _placement_route(
                repo, unit, source_map, routes, matches[0], args)
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
            for resolved in files:
                path = Path(resolved.path)
                entry = {"material_uri": resolved.material_uri,
                         "format": path.suffix.lower().lstrip(".") or "unknown",
                         "file_sha256": sha256_file(path),
                         "extraction": "not-requested"}
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
                if args.extract:
                    try:
                        part = _read_part(route["id"], resolved, route.get("locator", ""))
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
            return _print_stable(root, snapshot, {
                "contract": "material-span-v1", "unit_id": unit.id,
                "module_id": unit.module_id, "route_id": route["id"],
                "source_id": route.get("source_id"),
                "locator": route.get("locator"),
                "url": route.get("url") or source.get("url"),
                "availability": status,
                "next_action": next_action,
                "analysis_refs": analysis,
                "spans": spans,
                "expansion": None if args.extract else expansion(
                    "material-span", unit.id, route["id"],
                    *(["--stage", args.stage_id, "--resource-index",
                       str(args.resource_index)]
                      if getattr(args, "stage_id", None) is not None else []),
                    "--extract", "--expected-snapshot", snapshot),
            })
    except (WriteRefused, OSError, ValueError) as exc:
        return _refusal(exc)
