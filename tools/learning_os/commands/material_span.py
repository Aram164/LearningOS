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
from .material import _brief_analysis_refs
from .reads import _print_stable, _refusal, _snapshot
from .support import WriteRefused, _operator_lock, _root

MAX_EXCERPT = 6000


def cmd_material_span(args) -> int:
    root = _root(args)
    try:
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            unit = repo.units.get(args.unit_id)
            if unit is None:
                raise WriteRefused(f"unknown unit {args.unit_id}")
            source_map = repo.module_source_maps.get(unit.module_id)
            if source_map is None:
                raise WriteRefused("unit has no module source map")
            matches = [row for row in unit_routes(source_map, unit.module_id, unit.id)
                       if row["id"] == args.route_id]
            if len(matches) != 1:
                raise WriteRefused("route is missing or ambiguous in this unit")
            route = matches[0]
            source = repo.sources.get(route.get("source_id"), {})
            projected = project_material_resource(repo, route)
            files = resolve_route_material_files(repo, route)
            status = ("local-observed" if files else
                      "local-unavailable" if projected.get("material_uri") else
                      "remote-unobserved" if route.get("url") or source.get("url") else
                      "unavailable")
            analysis = _brief_analysis_refs(root, repo, unit, [route])
            notes = analysis["analysis_notes"]
            analysis["analysis_notes_total"] = len(notes)
            analysis["analysis_notes_truncated"] = len(notes) > 20
            analysis["analysis_notes"] = notes[:20]
            analysis["expand"] = f"plan-edit-context {unit.id} --route-id {route['id']}"
            analysis["approved_assessment_routes"] = [
                item for item in analysis["approved_assessment_routes"] if item == route["id"]]
            analysis["stale_assessment_routes"] = [
                item for item in analysis["stale_assessment_routes"] if item == route["id"]]
            spans = []
            for resolved in files:
                path = Path(resolved.path)
                entry = {"material_uri": resolved.material_uri,
                         "format": path.suffix.lower().lstrip(".") or "unknown",
                         "file_sha256": sha256_file(path),
                         "extraction": "not-requested"}
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
                "analysis_refs": analysis,
                "spans": spans,
                "expansion": None if args.extract else
                    f"material-span {unit.id} {route['id']} --extract",
            })
    except (WriteRefused, OSError, ValueError) as exc:
        return _refusal(exc)
