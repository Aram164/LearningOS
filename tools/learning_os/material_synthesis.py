"""Validated, evidence-bearing comparative material dossiers for one unit.

This module is deliberately independent from the UI and from provider APIs.
It validates an already reviewed delivery against the *current* unit routes and
returns the one canonical file that a gateway transaction may publish.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from learning_os.contracts.json_schema import validate_contract
from learning_os.genout.materials import (
    _MATERIAL_SUFFIX_TOKEN,
    _material_location,
    _material_uri_authority,
    _project_material_resource,
    _safe_material_locator,
)
from learning_os.loader import load_repo
from learning_os.transactions import artifact_revision


class MaterialSynthesisError(ValueError):
    """A dossier is invalid or stale; callers must leave canonical state unchanged."""


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_checksum(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_bytes(payload.encode("utf-8"))


def _rich_routes(repo, unit_id: str) -> list[dict[str, Any]]:
    unit = repo.units.get(unit_id)
    if unit is None:
        raise MaterialSynthesisError(f"unit not found: {unit_id}")
    source_map = repo.module_source_maps.get(unit.module_id) or {}
    output: list[dict[str, Any]] = []
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("unit_id") == unit_id:
                row = dict(route)
                row["source_id"] = source_id
                output.append(row)
    return output


def _route_material_files(repo, route: dict[str, Any]) -> list[tuple[str, Path]]:
    """Resolve every exact local file named by one route, or none.

    Most routes name one file and use the ordinary material projection.  A
    small but important class (including SaD L03's current exercise route)
    deliberately binds two files with a semicolon.  Treating that locator as
    prose made freshness fall back to a route-text hash, so changing either
    reviewed PDF did not stale the dossier.  The multi-file branch is strict:
    every semicolon-delimited part must name exactly one safe existing file,
    otherwise no partial byte-coverage claim is made.
    """
    projected = _project_material_resource(repo, {
        "source_id": route.get("source_id"),
        "locator": route.get("locator"),
        "vault_path": route.get("vault_path"),
    })
    material_uri = projected.get("material_uri")
    relative = projected.get("material_path")
    if isinstance(material_uri, str) and isinstance(relative, str) \
            and projected.get("material_exists"):
        path = repo.learningos_root / relative
        if path.is_file() and not path.is_symlink():
            return [(material_uri, path)]

    locator = route.get("locator")
    source = repo.sources.get(route.get("source_id"))
    source_material = source.get("material") if isinstance(source, dict) else None
    authority = _material_uri_authority(source_material)
    if not isinstance(locator, str) or ";" not in locator or not authority:
        return []

    candidates: list[str] = []
    for part in locator.split(";"):
        matches = list(_MATERIAL_SUFFIX_TOKEN.finditer(part))
        if len(matches) != 1:
            return []
        candidate = _safe_material_locator(part[:matches[0].end()].strip())
        if candidate is None:
            return []
        candidates.append(candidate)
    if len(candidates) < 2 or len(candidates) != len(set(candidates)):
        return []

    files: list[tuple[str, Path]] = []
    for candidate in candidates:
        uri = f"material://{authority}/{candidate}"
        location = _material_location(repo, uri)
        relative = location.get("material_path")
        if not isinstance(relative, str) or not location.get("material_exists"):
            return []
        path = repo.learningos_root / relative
        if not path.is_file() or path.is_symlink():
            return []
        files.append((uri, path))
    return files


def _route_material_checksum(repo, route: dict[str, Any]) -> str:
    """Hash local material bytes when resolvable; otherwise hash the exact route.

    Remote and deliberately unavailable resources still need a stable freshness
    token.  The route hash is explicitly provenance, not a claim that remote
    bytes were reviewed.
    """
    files = _route_material_files(repo, route)
    if len(files) == 1:
        return _sha256_file(files[0][1])
    if files:
        return _stable_checksum([
            {"material_uri": uri, "sha256": _sha256_file(path)}
            for uri, path in sorted(files, key=lambda row: row[0])
        ])
    return _stable_checksum({
        key: route.get(key)
        for key in ("id", "source_id", "unit_id", "locator", "url", "vault_path")
    })


def current_unit_material_basis(root: Path, unit_id: str) -> dict[str, Any]:
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        raise MaterialSynthesisError(f"unit not found: {unit_id}")
    source_map_path = repo.module_source_map_origins.get(unit.module_id)
    if source_map_path is None or not source_map_path.is_file():
        raise MaterialSynthesisError(f"unit has no module source map: {unit_id}")
    routes = _rich_routes(repo, unit_id)
    if not routes:
        raise MaterialSynthesisError(f"unit has no rich material routes: {unit_id}")
    route_ids = [route.get("id") for route in routes]
    if any(not isinstance(route_id, str) or not route_id.startswith("route-")
           for route_id in route_ids):
        raise MaterialSynthesisError(
            "unit routes do not yet have stable route IDs; complete Data Contract v13 migration"
        )
    if len(route_ids) != len(set(route_ids)):
        raise MaterialSynthesisError(f"unit has duplicate route IDs: {unit_id}")
    route_rows = sorted(routes, key=lambda row: str(row["id"]))
    return {
        "unit_revision": artifact_revision(root, unit_id),
        # Module-plan transactions guard the module source map with the owning
        # module artifact revision.  Keep that revision alongside the byte
        # checksum: either a coordinated module-plan change or an out-of-band
        # byte change makes a reviewed dossier stale.
        "source_map_revision": artifact_revision(root, unit.module_id),
        "source_map_checksum": _sha256_file(source_map_path),
        "route_set_checksum": _stable_checksum(route_rows),
        "material_checksums": {
            str(route["id"]): _route_material_checksum(repo, route)
            for route in route_rows
        },
        "policy": "tiered-v1",
    }


def validate_unit_material_synthesis(
    root: Path,
    unit_id: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    try:
        validate_contract(root, "unit-material-synthesis.schema.json", value)
    except ValueError as exc:
        raise MaterialSynthesisError(str(exc)) from exc
    if value.get("unit_id") != unit_id:
        raise MaterialSynthesisError("dossier unit_id does not match the requested unit")

    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        raise MaterialSynthesisError(f"unit not found: {unit_id}")
    routes = _rich_routes(repo, unit_id)
    by_route = {str(route.get("id")): route for route in routes if route.get("id")}
    if len(by_route) != len(routes):
        raise MaterialSynthesisError("every current rich route must have one unique stable ID")
    assessments = value["route_assessments"]
    assessed = {str(row["route_id"]): row for row in assessments}
    if len(assessed) != len(assessments):
        raise MaterialSynthesisError("route assessments contain duplicate route IDs")
    missing = sorted(set(by_route) - set(assessed))
    extra = sorted(set(assessed) - set(by_route))
    if missing or extra:
        raise MaterialSynthesisError(
            f"route assessment coverage mismatch (missing={missing}, extra={extra})"
        )
    for route_id, route in by_route.items():
        assessment = assessed[route_id]
        if assessment.get("source_id") != route.get("source_id"):
            raise MaterialSynthesisError(f"{route_id} source_id does not match the current route")
        if assessment.get("locator") != route.get("locator"):
            raise MaterialSynthesisError(f"{route_id} locator does not match the current route")
        if route.get("scope") in {"current", "prerequisite"} \
                and assessment.get("review_status") != "deep-reviewed":
            raise MaterialSynthesisError(
                f"{route_id} is {route.get('scope')} and must be deep-reviewed"
            )

    basis = value["basis"]
    current = current_unit_material_basis(root, unit_id)
    for field in ("unit_revision", "source_map_revision", "source_map_checksum",
                  "route_set_checksum", "material_checksums", "policy"):
        if basis.get(field) != current[field]:
            raise MaterialSynthesisError(f"dossier basis is stale at {field}")

    concept_ids = set(repo.concepts)
    note_ids = set(repo.notes)
    unit_ids = set(repo.units)
    local_nodes = {
        str(node.get("id"))
        for node in (unit.data.get("knowledge_map") or {}).get("nodes", []) or []
        if isinstance(node, dict) and node.get("id")
    }
    mapped_nodes: list[str] = []
    for group in value["concept_groups"]:
        if group["concept_id"] not in concept_ids:
            raise MaterialSynthesisError(f"unknown global concept: {group['concept_id']}")
        mapped_nodes.extend(group["local_node_ids"])
        unknown_units = sorted(set(group["related_unit_ids"]) - unit_ids)
        unknown_notes = sorted(set(group["bridge_note_ids"]) - note_ids)
        if unknown_units or unknown_notes:
            raise MaterialSynthesisError(
                f"concept group has unknown references (units={unknown_units}, notes={unknown_notes})"
            )
    if len(mapped_nodes) != len(set(mapped_nodes)):
        raise MaterialSynthesisError("a local knowledge node is mapped more than once")
    if set(mapped_nodes) != local_nodes:
        raise MaterialSynthesisError(
            "every local knowledge node must be mapped exactly once before approval"
        )

    for row in assessments:
        unknown = sorted(set(row["concept_ids"]) - concept_ids)
        if unknown:
            raise MaterialSynthesisError(f"{row['route_id']} names unknown concepts: {unknown}")
        expected_checksum = basis["material_checksums"][row["route_id"]]
        for evidence in row.get("evidence", []) or []:
            if evidence.get("checksum") != expected_checksum:
                raise MaterialSynthesisError(
                    f"{row['route_id']} evidence checksum does not match its material basis"
                )
    seen_comparisons: set[tuple[str, str, str]] = set()
    for comparison in value["comparisons"]:
        left, right = comparison["left_route_id"], comparison["right_route_id"]
        if left == right or left not in by_route or right not in by_route:
            raise MaterialSynthesisError("comparison endpoints must be two current distinct routes")
        if assessed[left]["review_status"] != "deep-reviewed" \
                or assessed[right]["review_status"] != "deep-reviewed":
            raise MaterialSynthesisError(
                "pairwise comparisons require two deep-reviewed sources"
            )
        comparison_key = (*sorted((left, right)), comparison["relation"])
        if comparison_key in seen_comparisons:
            raise MaterialSynthesisError(
                "duplicate pairwise comparison relation"
            )
        seen_comparisons.add(comparison_key)
        unknown = sorted(set(comparison["concept_ids"]) - concept_ids)
        if unknown:
            raise MaterialSynthesisError(f"comparison names unknown concepts: {unknown}")
        for side, route_id in (("left", left), ("right", right)):
            expected_checksum = basis["material_checksums"][route_id]
            if any(
                evidence.get("checksum") != expected_checksum
                for evidence in comparison["evidence"][side]
            ):
                raise MaterialSynthesisError(
                    f"comparison {side} evidence checksum does not match {route_id}"
                )
    return value


def material_synthesis_freshness(root: Path, unit_id: str, value: dict[str, Any]) -> dict[str, Any]:
    """Return derived freshness without trusting a stored status flag."""
    reasons: list[str] = []
    try:
        current = current_unit_material_basis(root, unit_id)
    except Exception:
        # A published historical dossier remains useful evidence even when its
        # current basis can no longer be resolved.  Keep the projection
        # deliberately content-free here: diagnostics can report the detailed
        # local failure, while an ordinary manifest exposes only a stable code.
        return {"status": "stale", "reasons": ["current-basis-unavailable"]}
    basis = value.get("basis") or {}
    for field in ("unit_revision", "source_map_revision", "source_map_checksum",
                  "route_set_checksum", "material_checksums", "policy"):
        if basis.get(field) != current.get(field):
            reasons.append(field)
    return {"status": "current" if not reasons else "stale", "reasons": reasons}


def material_synthesis_completeness(
    root: Path,
    unit_id: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    """Derive current route coverage while retaining every historical row.

    Counts describe assessments whose route IDs still belong to the unit.  A
    removed route remains visible in the raw dossier and is called out as an
    orphan; a new route appears as missing.  No current-basis validation is
    used as a publication filter.
    """
    try:
        repo = load_repo(root)
        current_route_ids = sorted(
            str(route["id"])
            for route in _rich_routes(repo, unit_id)
            if isinstance(route.get("id"), str)
        )
    except Exception:
        current_route_ids = []

    assessments = [
        row for row in (value.get("route_assessments") or [])
        if isinstance(row, dict) and isinstance(row.get("route_id"), str)
    ]
    by_route: dict[str, dict[str, Any]] = {}
    duplicate_route_ids = {
        route_id for route_id, count in Counter(current_route_ids).items()
        if count > 1
    }
    for assessment in assessments:
        route_id = str(assessment["route_id"])
        if route_id in by_route:
            duplicate_route_ids.add(route_id)
            continue
        by_route[route_id] = assessment

    current = set(current_route_ids)
    assessed = set(by_route)
    missing_route_ids = sorted(current - assessed)
    orphaned_route_ids = sorted(assessed - current)
    status_counts = {
        "deep_reviewed_count": 0,
        "screened_count": 0,
        "unevaluated_count": 0,
        "unavailable_count": 0,
    }
    status_keys = {
        "deep-reviewed": "deep_reviewed_count",
        "screened": "screened_count",
        "unevaluated": "unevaluated_count",
        "unavailable": "unavailable_count",
    }
    for route_id in sorted(current & assessed):
        key = status_keys.get(by_route[route_id].get("review_status"))
        if key is not None:
            status_counts[key] += 1

    assessed_current_count = len(current & assessed)
    classified_count = sum(status_counts.values())
    complete = (
        bool(current_route_ids)
        and not missing_route_ids
        and not orphaned_route_ids
        and not duplicate_route_ids
        and assessed_current_count == classified_count
    )
    return {
        "complete": complete,
        "current_route_count": len(current_route_ids),
        "assessed_route_count": assessed_current_count,
        **status_counts,
        "missing_route_ids": missing_route_ids,
        "orphaned_route_ids": orphaned_route_ids,
        "duplicate_route_ids": sorted(duplicate_route_ids),
    }


def synthesis_destination(root: Path, unit_id: str) -> Path:
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        raise MaterialSynthesisError(f"unit not found: {unit_id}")
    return unit.path.parent / "material-synthesis.yaml"
