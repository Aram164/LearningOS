"""`los dossier`: serve one unit's materialized context bundle.

Read-only. Resolves the unit's knowledge map, module source map, routes,
and manifest-digest evidence, then serves the cached semantic dossier when
its hashes still match — otherwise rebuilds and best-effort stores the
fresh bundle under ``generated/dossiers/``. The cache is a rebuilt view,
never canonical state: a store failure never fails the read, and a cache
file whose content fails its hashes is refused and rebuilt, never served.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from learning_os.loader import load_repo
from learning_os.material_refs import unit_routes
from learning_os.materials_resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
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

from .reads import _print_stable, _refusal, _snapshot
from .support import WriteRefused, _operator_lock, _root

#: Operator-contract version hashed into every dossier key. There is no
#: version constant for OPERATOR.md; this string tracks its title
#: ("LearningOS Operator Contract v2") and changes only with it.
OPERATOR_CONTRACT_VERSION = "operator-v2"

SKIP_NAMES = frozenset({".DS_Store"})


def _manifest_digests(root: Path) -> dict[str, str]:
    """Recorded sha256 per materials relpath, or {} when uninventoried."""
    try:
        data = yaml.safe_load(
            (root / "records" / "materials-manifest.yaml").read_text(
                encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, dict):
        return {}
    return {str(rel): row["sha256"] for rel, row in files.items()
            if isinstance(row, dict) and isinstance(row.get("sha256"), str)}


def _live_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


def _recorded_or_live(recorded: dict[str, str], base: Path | None,
                      path: Path) -> str | None:
    """The content digest behind one material file.

    Recorded manifest checksums win; files the inventory has not seen yet
    (transcripts fetched since the last ``make inventory``) fall back to
    live bytes. Both are content digests, so either invalidates on change.
    """
    if base is not None:
        try:
            rel = path.resolve().relative_to(base).as_posix()
        except (OSError, ValueError):
            rel = None
        if rel is not None and rel in recorded:
            return recorded[rel]
    return _live_sha256(path)


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
    transcript a legitimate dossier input with zero route edits.
    """
    recorded = _manifest_digests(repo.root)
    materials = repo.learningos_root / "materials"
    try:
        base = materials.resolve()
    except OSError:
        base = None
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
            digest = _recorded_or_live(recorded, base, path)
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
            digest = _recorded_or_live(recorded, base, path)
            if digest is None:
                continue
            try:
                within = path.resolve().relative_to(anchored).as_posix()
            except (OSError, ValueError):
                continue
            evidence[f"material://{authority}/{within}"] = f"sha256:{digest}"
    return evidence


def cmd_dossier(args) -> int:
    """Build, serve, or rebuild one unit's semantic dossier. Read-only."""
    root = _root(args)
    try:
        with _operator_lock(root):
            snapshot = _snapshot(root)
            repo = load_repo(root)
            if repo.parse_failures:
                raise WriteRefused(
                    "dossier refuses unreadable canonical records")
            unit = repo.units.get(args.unit_id)
            if unit is None:
                raise WriteRefused(f"unit not found: {args.unit_id}")
            if unit.module_id not in repo.module_source_maps:
                raise WriteRefused(
                    f"unit {unit.id} has no module source map")
            source_map = repo.module_source_maps[unit.module_id]
            routes = unit_routes(source_map, unit.module_id, unit.id)
            knowledge_map = unit.data.get("knowledge_map") or {}
            if not isinstance(knowledge_map, dict):
                raise WriteRefused(
                    f"unit {unit.id} knowledge map is not a mapping")
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
                    f"cannot build dossier for {unit.id}: {exc}") from exc
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
            if args.json:
                payload["content"] = {
                    section: value for section, value in fresh.content}
            return _print_stable(root, snapshot, payload)
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)
