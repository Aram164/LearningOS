"""Validated, evidence-bearing comparative material dossiers for one unit.

This module is deliberately independent from the UI and from provider APIs.
It validates an already reviewed delivery against the *current* unit routes and
returns the one canonical file that a gateway transaction may publish.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from learning_os.contracts.json_schema import validate_contract
from learning_os.loader import load_repo
from learning_os.material_slices import parse_locator_page_ranges
from learning_os.materials_resolution import (
    MATERIAL_SUFFIX_TOKEN,
    evidential_route_projection,
    evidential_source_map_projection,
    route_material_checksum,
    stable_checksum,
)
from learning_os.transactions import artifact_revision

#: Widest cited page span the provenance check expands before refusing.
#: Real evidence cites dozens of pages at most; anything wider cannot be
#: covered by bounded slices and is rejected as uncitable, never sampled.
_MAX_CITED_SPAN = 100_000


class MaterialSynthesisError(ValueError):
    """A dossier is invalid or stale; callers must leave canonical state unchanged."""


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


# `unit_revision` is recorded but deliberately not compared. Publishing a
# dossier guards the unit artifact, so the commit bumps the unit's revision
# after the basis has already been derived: every dossier was born one
# revision behind and reported "stale basis" from the moment it was written
# (L03 recorded 19 against a live 20, L04 recorded 17 against 20). It travels
# as provenance, like a continued file SHA. What the dossier genuinely owes
# the unit — a concept group for every local knowledge node, exactly once —
# is enforced directly by `validate_unit_material_synthesis` at publish.
#
# `source_map_revision` is recorded but deliberately not compared, for the
# same reason at module granularity: it is a logical counter that moves on
# every canonical edit to the module, prose included. Comparing it reimposed
# through the back door the exact punishment the evidential checksums were
# built to remove — a corrected angle staling every dossier in the module,
# including other units'. A prose change moves no evidential checksum, so the
# dossier stays current; an evidential change moves exactly the checksums of
# the units that rest on it. The revision travels as provenance so a reader
# can still tell which module state was live at review time.
_COMPARED_BASIS_FIELDS = (
    "source_map_checksum",
    "route_set_checksum",
    "material_checksums",
    "policy",
)

def current_unit_material_basis(
    root: Path,
    unit_id: str,
    *,
    repo=None,
    cache: dict[Path, str] | None = None,
) -> dict[str, Any]:
    """Derive one unit's current material basis.

    ``repo`` lets a caller that has already loaded the repository — a manifest
    build projecting many dossiers — reuse it instead of paying a full load per
    dossier per derived field. Omitting it keeps the standalone contract.
    """
    repo = load_repo(root) if repo is None else repo
    if cache is None:
        cache = {}
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
        # module artifact revision.  Keep that revision as provenance only:
        # the evidential checksums below are what stale a dossier, so a
        # prose-only edit moves nothing while an evidential edit moves exactly
        # the affected units.  The checksum covers the map's evidential
        # projection for THIS unit, not the file's bytes — hashing the bytes
        # made every dossier in a module depend on every word in it, so a prose
        # fix on an unrelated unit's route staled this one too.
        "source_map_revision": artifact_revision(root, unit.module_id),
        "source_map_checksum": stable_checksum(
            evidential_source_map_projection(
                repo.module_source_maps.get(unit.module_id) or {}, unit_id
            )
        ),
        # Prose is deliberately outside the hash. Hashing whole rows made a
        # typo fix in one `angle` stale a whole unit's dossier, which is the
        # wrong incentive: the canonical route is exactly where a corrected
        # angle belongs.
        "route_set_checksum": stable_checksum(
            [evidential_route_projection(route) for route in route_rows]
        ),
        "material_checksums": {
            str(route["id"]): route_material_checksum(repo, route, cache)
            for route in route_rows
        },
        "policy": "tiered-v2",
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
    for field in _COMPARED_BASIS_FIELDS:
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


def inspected_pages_by_route(
    index_records: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Union of inspected PDF pages per route across every slice pass."""
    inspected: dict[str, set[int]] = {}
    for record in index_records or []:
        if not isinstance(record, dict):
            continue
        route_id = record.get("route_id")
        if not isinstance(route_id, str):
            continue
        pages = inspected.setdefault(route_id, set())
        for part in record.get("parts", []) or []:
            if not isinstance(part, dict):
                continue
            for page in part.get("pages", []) or []:
                if isinstance(page, bool):
                    continue
                if isinstance(page, int) and page >= 1:
                    pages.add(page)
    return {route_id: sorted(pages) for route_id, pages in inspected.items()}


def inspected_material_by_route(
    index_records: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Inspected pages per route AND material: route -> uri -> record.

    A route-level page union cannot tell part-a p.22 from part-b p.22, so
    provenance keeps file identity: kind, inspected pages and the file hash
    of every sliced part, across all passes.
    """
    inspected: dict[str, dict[str, dict[str, Any]]] = {}
    for record in index_records or []:
        if not isinstance(record, dict):
            continue
        route_id = record.get("route_id")
        if not isinstance(route_id, str):
            continue
        materials = inspected.setdefault(route_id, {})
        for part in record.get("parts", []) or []:
            if not isinstance(part, dict):
                continue
            uri = part.get("material_uri")
            if not isinstance(uri, str):
                continue
            entry = materials.setdefault(uri, {"kind": part.get("kind"),
                                               "pages": set(),
                                               "file_sha256": part.get("file_sha256")})
            for page in part.get("pages", []) or []:
                if isinstance(page, int) and not isinstance(page, bool) and page >= 1:
                    entry["pages"].add(page)
    return {
        route_id: {
            uri: {"kind": entry["kind"], "pages": sorted(entry["pages"]),
                  "file_sha256": entry["file_sha256"]}
            for uri, entry in materials.items()
        }
        for route_id, materials in inspected.items()
    }


def _evidence_filename(locator: Any) -> str | None:
    """The single material file an evidence locator names, if exactly one.

    House-style filenames carry no whitespace, so each suffix-token span is
    recovered by walking left to the previous boundary. Zero or several
    distinct names mean the locator does not identify one file.
    """
    if not isinstance(locator, str):
        return None
    names: list[str] = []
    for match in MATERIAL_SUFFIX_TOKEN.finditer(locator):
        after = locator[match.end():match.end() + 1]
        if after and (after.isalnum() or after == "."):
            continue
        boundary = max(locator.rfind(char, 0, match.start())
                       for char in (" ", "\t", "\n", ",", ";", '"', "'", "(", "["))
        candidate = locator[boundary + 1:match.end()]
        if candidate and candidate not in names:
            names.append(candidate)
    if len(names) != 1:
        return None
    return names[0]


def _evidence_material(materials: dict[str, dict[str, Any]], locator: Any,
                       *, where: str) -> str:
    """The one bound material an evidence locator can own pages from.

    A single-material route is unambiguous. Otherwise the locator must name
    exactly one bound file — except when it cites pages and only one bound
    material has a page model, which can only be that PDF.
    """
    if len(materials) == 1:
        return next(iter(materials))
    filename = _evidence_filename(locator)
    if filename is not None:
        hits = [uri for uri in materials if uri.rsplit("/", 1)[-1] == filename]
        if len(hits) == 1:
            return hits[0]
    refs = parse_locator_page_ranges(locator)
    if filename is None and refs:
        pdfs = [uri for uri, info in materials.items() if info.get("kind") == "pdf"]
        if len(pdfs) == 1:
            return pdfs[0]
    bound = ", ".join(sorted(uri.rsplit("/", 1)[-1] for uri in materials))
    raise MaterialSynthesisError(
        f"{where} evidence must name exactly one of the route's files "
        f"({bound}); got {locator!r}")


def _check_material_evidence(materials: dict[str, dict[str, Any]], locator: Any,
                             *, where: str) -> None:
    """One evidence locator against its owning material, or raise."""
    uri = _evidence_material(materials, locator, where=where)
    info = materials[uri]
    name = uri.rsplit("/", 1)[-1]
    ranges = parse_locator_page_ranges(locator)
    if info.get("kind") == "pdf":
        if not ranges:
            raise MaterialSynthesisError(
                f"{where} evidence must cite exact PDF pages in house style "
                f"(e.g. '{name}, PDF pp. 34-41'); got {locator!r}")
        seen = set(info.get("pages", []))
        beyond: list[int] = []
        for start, end in ranges:
            for page in range(start, min(end, start + _MAX_CITED_SPAN) + 1):
                if page not in seen:
                    beyond.append(page)
                    if len(beyond) >= 5:
                        break
            if len(beyond) >= 5:
                break
        if beyond:
            raise MaterialSynthesisError(
                f"{where} evidence cites {name} pages never inspected "
                f"(e.g. p.{beyond[0]}); inspected: {sorted(seen)}")
    elif ranges:
        raise MaterialSynthesisError(
            f"{where} evidence cites pages from text material {name}, "
            f"which has no page model; got {locator!r}")


def validate_synthesis_page_provenance(
    inspected: dict[str, dict[str, dict[str, Any]]],
    synthesis: dict[str, Any],
) -> None:
    """Refuse evidence that is not grounded in the attached slices.

    Provenance is per material, not per route: part-a p.22 and part-b p.22
    are different claims and checked against their own inspected sets.
    Routes without a reading record keep their legacy behavior, so bundles
    prepared without slices stay valid. Applies to assessments and both
    comparison sides alike.
    """
    for row in synthesis.get("route_assessments", []) or []:
        if not isinstance(row, dict) or row.get("review_status") != "deep-reviewed":
            continue
        route_id = str(row.get("route_id"))
        materials = inspected.get(route_id)
        if not materials:
            continue
        for evidence in row.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue
            _check_material_evidence(materials, evidence.get("locator"),
                                     where=route_id)
        # The bound every negative claim in this assessment is limited to. It
        # is checked exactly like evidence, because that is what it is: a claim
        # about which pages were in front of the reviewer. An unbounded "no
        # worked solution here" over a file whose pages nobody opened is the
        # one thing the reading budget cannot detect on its own.
        scope = row.get("scope_of_absence")
        if scope is not None:
            _check_material_evidence(materials, scope,
                                     where=f"{route_id} scope_of_absence")
    for comparison in synthesis.get("comparisons", []) or []:
        if not isinstance(comparison, dict):
            continue
        evidence = comparison.get("evidence")
        if not isinstance(evidence, dict):
            continue
        for side, key in (("left", "left_route_id"), ("right", "right_route_id")):
            route_id = comparison.get(key)
            rows = evidence.get(side)
            if not isinstance(route_id, str) or not isinstance(rows, list):
                continue
            materials = inspected.get(route_id)
            if not materials:
                continue
            for item in rows:
                if not isinstance(item, dict):
                    continue
                _check_material_evidence(materials, item.get("locator"),
                                         where=f"comparison {side} of {route_id}")


def material_synthesis_freshness(
    root: Path,
    unit_id: str,
    value: dict[str, Any],
    *,
    repo=None,
    cache: dict[Path, str] | None = None,
) -> dict[str, Any]:
    """Return derived freshness without trusting a stored status flag."""
    reasons: list[str] = []
    try:
        current = current_unit_material_basis(root, unit_id, repo=repo, cache=cache)
    except Exception:
        # A published historical dossier remains useful evidence even when its
        # current basis can no longer be resolved.  Keep the projection
        # deliberately content-free here: diagnostics can report the detailed
        # local failure, while an ordinary manifest exposes only a stable code.
        return {"status": "stale", "reasons": ["current-basis-unavailable"]}
    basis = value.get("basis") or {}
    for field in _COMPARED_BASIS_FIELDS:
        if basis.get(field) != current.get(field):
            reasons.append(field)
    return {"status": "current" if not reasons else "stale", "reasons": reasons}


def material_synthesis_completeness(
    root: Path,
    unit_id: str,
    value: dict[str, Any],
    *,
    repo=None,
) -> dict[str, Any]:
    """Derive current route coverage while retaining every historical row.

    Counts describe assessments whose route IDs still belong to the unit.  A
    removed route remains visible in the raw dossier and is called out as an
    orphan; a new route appears as missing.  No current-basis validation is
    used as a publication filter.
    """
    try:
        repo = load_repo(root) if repo is None else repo
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
