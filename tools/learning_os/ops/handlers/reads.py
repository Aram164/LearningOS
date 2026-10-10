"""Reads-area converted handlers (PLAN D4)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.material_refs import unit_routes
from learning_os.materials_resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
from learning_os.ops._legacy_plumbing import _snapshot
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError
from learning_os.semantics.dossiers import (
    DossierError,
    build_dossier,
    cache_path,
    is_fresh,
    load_dossier,
    store_dossier,
)
from learning_os.semantics.predicates import CONTRACT_VERSION

#: Operator-contract version hashed into every dossier key. There is no
#: version constant for OPERATOR.md; this string tracks its title
#: ("LearningOS Operator Contract v2") and changes only with it.
OPERATOR_CONTRACT_VERSION = "operator-v2"

SKIP_NAMES = frozenset({".DS_Store"})


def _live_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


def _iter_material_files(directory: Path):
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        yield path


def _evidence(repo, source_ids) -> dict[str, str]:
    """One content digest per file under the unit's source authorities.

    Authority-prefix, not route-target-only: a re-uploaded video changes
    the key even though no locator moved — which is exactly what makes a
    transcript a legitimate dossier input with zero route edits. Digests
    always hash live bytes; recorded inventory checksums are historical
    observations and never stand in for current content.
    """
    materials = repo.learningos_root / "materials"
    evidence: dict[str, str] = {}
    for sid in sorted(source_ids):
        source = repo.sources.get(sid)
        material = source.get("material") if isinstance(source, dict) else None
        if material_uri_authority(material) is None:
            continue
        single = single_file_material(str(material))
        if single is not None:
            try:
                path = resolve_material_target(
                    single, resolution_root=repo.materials_root,
                    boundary_root=materials)
            except (PathBoundaryError, FileNotFoundError, OSError):
                continue
            digest = _live_sha256(path)
            if digest is not None:
                evidence[single] = f"sha256:{digest}"
            continue
        authority = material_uri_authority(str(material))
        try:
            directory = resolve_material_target(
                f"material://{authority}", resolution_root=repo.materials_root,
                boundary_root=materials)
        except (PathBoundaryError, FileNotFoundError, OSError):
            continue
        if not directory.is_dir():
            continue
        try:
            anchored = directory.resolve()
        except OSError:
            continue
        for path in _iter_material_files(directory):
            digest = _live_sha256(path)
            if digest is None:
                continue
            try:
                within = path.resolve().relative_to(anchored).as_posix()
            except (OSError, ValueError):
                continue
            evidence[f"material://{authority}/{within}"] = f"sha256:{digest}"
    return evidence


def _dumps_dossier(payload: dict) -> str:
    """The exact dossier encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


@register("cli.dossier", kind="porcelain")
def dossier(ctx: OpContext, req: dict) -> Result:
    """Build, serve, or rebuild one unit's semantic dossier. Read-only."""
    root = ctx.root
    try:
        snapshot = _snapshot(root)
        repo = ctx.repo()
        if repo.parse_failures:
            raise WriteRefused(
                "dossier refuses unreadable canonical records",
                site=f"{ctx.operation}.unreadable-records",
                gateway_message="los: dossier refuses unreadable canonical records",
                exit_code=2,
            )
        unit = repo.units.get(req["unit_id"])
        if unit is None:
            message = not_found("unit", req["unit_id"], repo.units)
            raise NotFound(
                "unit", req["unit_id"], repo.units,
                site=f"{ctx.operation}.unknown-unit",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
        if unit.module_id not in repo.module_source_maps:
            raise WriteRefused(
                f"unit {unit.id} has no module source map",
                site=f"{ctx.operation}.no-source-map",
                gateway_message=f"los: unit {unit.id} has no module source map",
                exit_code=2,
            )
        source_map = repo.module_source_maps[unit.module_id]
        routes = unit_routes(source_map, unit.module_id, unit.id)
        knowledge_map = unit.data.get("knowledge_map") or {}
        if not isinstance(knowledge_map, dict):
            raise WriteRefused(
                f"unit {unit.id} knowledge map is not a mapping",
                site=f"{ctx.operation}.bad-knowledge-map",
                gateway_message=f"los: unit {unit.id} knowledge map is not a mapping",
                exit_code=2,
            )
        source_ids = {str(route["source_id"]) for route in routes
                      if isinstance(route.get("source_id"), str)}
        for entry in unit.data.get("scope_sources", []) or []:
            if isinstance(entry, dict) and isinstance(
                    entry.get("source_id"), str):
                source_ids.add(entry["source_id"])
        try:
            fresh = build_dossier(
                unit_id=unit.id,
                knowledge_map=knowledge_map,
                source_map=source_map,
                routes=routes,
                evidence=_evidence(repo, source_ids),
                contract_versions={
                    "semantic-contract": str(CONTRACT_VERSION),
                    "operator-contract": OPERATOR_CONTRACT_VERSION,
                },
            )
        except DossierError as exc:
            raise WriteRefused(
                f"cannot build dossier for {unit.id}: {exc}",
                site=f"{ctx.operation}.build-failed",
                gateway_message=f"los: cannot build dossier for {unit.id}: {exc}",
                exit_code=2,
            ) from exc
        path = cache_path(root, fresh)
        served = False
        if path.is_file():
            try:
                served = is_fresh(load_dossier(path),
                                  dict(fresh.hashes))
            except DossierError:
                served = False
        if not served:
            try:
                store_dossier(root, fresh)
            except DossierError:
                pass  # the bundle is the deliverable; cache is best-effort
        try:
            cache_rel = path.relative_to(root).as_posix()
        except ValueError:
            cache_rel = str(path)
        payload = {
            "contract": "unit-dossier",
            "unit_id": unit.id,
            "module_id": unit.module_id,
            "key": fresh.key,
            "hashes": dict(fresh.hashes),
            "cache_path": cache_rel,
            "served_from_cache": served,
            "evidence_files": len(dict(fresh.content).get("evidence", {})),
        }
        if req.get("json"):
            payload["content"] = {
                section: value for section, value in fresh.content}
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},
            json_dumps=_dumps_dossier,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            gateway_message=f"los: {exc}",
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
