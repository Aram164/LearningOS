"""Recompute the RESOURCE-SCOPE-UNBOUND set independently of the validator.

The validator's own rule lives in
``tools/learning_os/derive/validation/plan_rigor.py``. This script states the
rule again, from the brief, and compares the two sets:

1. a ``kind: reference`` row is a pointer and is exempt;
2. a resource naming a route id at the top level is ``references.py``'s
   business (REF-ROUTE / RESOURCE-ROUTE-OWNER) and is not reported here;
3. a resource whose *authored* ``material_ref.route_id`` names a route of the
   module is bound; one that names no such route is reported;
4. otherwise the resource is bound when its (source_id, locator) matches a
   route of the module, and reported when it does not.

Run from a Core checkout:  ``.venv/bin/python <this file>``
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "repository" / "tools"))

from learning_os.domain.route_identity import route_with_identity  # noqa: E402
from learning_os.store.loader import load_repo  # noqa: E402


def expected_unbound(repo) -> set[tuple[str, str, int]]:
    """(study map, stage id, resource index) of every row the rule reports."""
    scope: dict[str, dict] = {}
    for module_id, source_map in repo.module_source_maps.items():
        ids: set[str] = set()
        pairs: set[tuple[str, str]] = set()
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                projected = route_with_identity(module_id, source_id, route)
                route_id = projected.get("id")
                if isinstance(route_id, str):
                    ids.add(route_id)
                pairs.add((source_id, str(route.get("locator") or "")))
        scope[module_id] = {"ids": ids, "pairs": pairs}

    reported: set[tuple[str, str, int]] = set()
    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        if module_id and (module and module.get("status") == "archived"):
            continue
        if not module_id:
            continue
        module_scope = scope.get(module_id)
        if module_scope is None:
            continue

        authored_by_stage: dict[str, list[dict]] = {}
        for stage in (study_map.authored_data or {}).get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            authored_by_stage.setdefault(str(stage.get("id") or ""), []).append(stage)

        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            stage_id = str(stage.get("id") or "")
            authored_resources = []
            for authored_stage in authored_by_stage.get(stage_id, []):
                authored_resources.extend(
                    resource for resource in authored_stage.get("resources", []) or []
                    if isinstance(resource, dict))
            for index, resource in enumerate(stage.get("resources", []) or []):
                if not isinstance(resource, dict):
                    continue
                if resource.get("kind") == "reference":
                    continue
                if isinstance(resource.get("route_id"), str) and resource["route_id"]:
                    continue
                material_route_id = None
                if index < len(authored_resources):
                    ref = authored_resources[index].get("material_ref")
                    if isinstance(ref, dict) and isinstance(ref.get("route_id"), str):
                        material_route_id = ref["route_id"]
                if material_route_id is not None:
                    if material_route_id not in module_scope["ids"]:
                        reported.add((smid, stage_id, index))
                    continue
                source_id = resource.get("source_id")
                locator = str(resource.get("locator") or "")
                if isinstance(source_id, str) and \
                        (source_id, locator) in module_scope["pairs"]:
                    continue
                reported.add((smid, stage_id, index))
    return reported


def observed_unbound(root: Path) -> list[tuple[str, str, str, str]]:
    """The validator's own set, read back from the validation report."""
    report = root / "generated" / "reports" / "validation-report.md"
    text = report.read_text(encoding="utf-8")
    found: list[tuple[str, str, str, str]] = []
    for line in text.splitlines():
        if "RESOURCE-SCOPE-UNBOUND" not in line:
            continue
        match = _ROW_RE.search(line)
        if match is None:
            continue
        found.append(match.group("smid", "stage", "source", "locator"))
    return found


_ROW_RE = re.compile(
    r"study map '(?P<smid>[^']*)' stage '(?P<stage>[^']*)' teaches "
    r"(?P<source>.*?) at '(?P<locator>.*)' — ",
)


def expected_rows(repo) -> list[tuple[str, str, str, str]]:
    """(study map, stage id, source, locator) of every row the rule reports."""
    scope: dict[str, dict] = {}
    for module_id, source_map in repo.module_source_maps.items():
        ids: set[str] = set()
        pairs: set[tuple[str, str]] = set()
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            source_id = str(entry.get("source_id") or "")
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                projected = route_with_identity(module_id, source_id, route)
                route_id = projected.get("id")
                if isinstance(route_id, str):
                    ids.add(route_id)
                pairs.add((source_id, str(route.get("locator") or "")))
        scope[module_id] = {"ids": ids, "pairs": pairs}

    reported: list[tuple[str, str, str, str]] = []
    for smid, study_map in repo.study_maps.items():
        unit = repo.units.get(study_map.unit_id)
        module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
        module = repo.modules.get(module_id) if module_id else None
        if module_id and (module and module.get("status") == "archived"):
            continue
        if not module_id:
            continue
        module_scope = scope.get(module_id)
        if module_scope is None:
            continue

        authored_by_stage: dict[str, list[dict]] = {}
        for stage in (study_map.authored_data or {}).get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            authored_by_stage.setdefault(str(stage.get("id") or ""), []).append(stage)

        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            stage_id = str(stage.get("id") or "")
            authored_resources = []
            for authored_stage in authored_by_stage.get(stage_id, []):
                authored_resources.extend(
                    resource for resource in authored_stage.get("resources", []) or []
                    if isinstance(resource, dict))
            for index, resource in enumerate(stage.get("resources", []) or []):
                if not isinstance(resource, dict):
                    continue
                if resource.get("kind") == "reference":
                    continue
                if isinstance(resource.get("route_id"), str) and resource["route_id"]:
                    continue
                material_route_id = None
                if index < len(authored_resources):
                    ref = authored_resources[index].get("material_ref")
                    if isinstance(ref, dict) and isinstance(ref.get("route_id"), str):
                        material_route_id = ref["route_id"]
                source_id = resource.get("source_id")
                locator = str(resource.get("locator") or "")
                if material_route_id is not None:
                    if material_route_id not in module_scope["ids"]:
                        reported.append((smid, stage_id, _source_label(source_id),
                                         locator[:60]))
                    continue
                if isinstance(source_id, str) and \
                        (source_id, locator) in module_scope["pairs"]:
                    continue
                reported.append((smid, stage_id, _source_label(source_id), locator[:60]))
    return reported


def _source_label(source_id) -> str:
    return source_id if isinstance(source_id, str) else "material without a source"


def main() -> int:
    root = Path(__file__).resolve().parents[2] / "repository"
    repo = load_repo(root)
    expected = sorted(expected_rows(repo))
    observed = sorted(observed_unbound(root))
    out = {
        "expected_rows": len(expected),
        "observed_rows": len(observed),
        "identical": expected == observed,
        "only_in_expected": [r for r in expected if r not in observed][:10],
        "only_in_observed": [r for r in observed if r not in expected][:10],
    }
    print(json.dumps(out, indent=2, default=str))
    return 0 if expected == observed else 1


if __name__ == "__main__":
    raise SystemExit(main())
