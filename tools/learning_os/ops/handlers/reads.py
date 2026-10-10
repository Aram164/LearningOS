"""Reads-area converted handlers (PLAN D4)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.suggest import expansion, not_found
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.material_refs import unit_routes
from learning_os.materials_resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
from learning_os.ops._legacy_plumbing import (
    SESSION_ID_ENV,
    _capabilities,
    _fresh_manifest,
    _json_layout,
    _resolve_session_identity,
    _snapshot,
    _window_values,
)
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


def _domain_glance(manifest):
    """Summarize the complete projection, independently of record pagination."""
    domains = {domain: {"domain": domain, "notes": 0, "crosswalks": 0,
                        "shelves": 0, "entries": 0}
               for domain in ATLAS_DOMAINS}
    for record in manifest.get("records", []):
        kind = record.get("type")
        if kind not in {"note", "collection", "topic-pack"}:
            continue
        domain = record.get("domain") or "cross-domain"
        if kind == "note" and record.get("path"):
            # The Domain atlas groups by the first directory under notes;
            # a record's domain can instead name a deeper subject folder.
            try:
                parts = PurePosixPath(record["path"]).relative_to("knowledge/notes").parts
                domain = parts[0] if len(parts) > 1 else "cross-domain"
            except ValueError:
                domain = "cross-domain"
        row = domains.setdefault(domain, {"domain": domain, "notes": 0,
                                         "crosswalks": 0, "shelves": 0, "entries": 0})
        if kind == "note":
            row["notes"] += 1
            row["crosswalks"] += record.get("role") == "crosswalk"
        else:
            row["shelves"] += 1
            row["entries"] += len(record.get("entries") or [])
    order = [*ATLAS_DOMAINS, *sorted(set(domains) - set(ATLAS_DOMAINS))]
    return [domains[domain] for domain in order]


#: What the brief's ``pointer_state`` means. A confirmed pointer is the
#: learner's last explicit study action -- where study stopped -- never a
#: recommendation. The note ships in the payload so an agent reading only
#: this page cannot mistake one for the other.
POINTER_STATE_NOTE = "confirmed = where study stopped, not a recommendation"


def _pointer_state(manifest, pointer) -> str:
    """confirmed/missing/invalid for the brief page; the same rule as resume.

    Mirrors ``resume._resolve_stage``'s validity check against the manifest
    instead of the loaded repo, so the brief and resume cannot disagree:
    the pointer counts only when its module, unit, map, and stage all
    resolve and link together. Status plays no part here, exactly as in
    resume -- a pointer to a paused map is still where study stopped.
    """
    if not isinstance(pointer, dict) or not pointer:
        return "missing"
    units = {row.get("id"): row for row in manifest.get("units", [])
             if isinstance(row, dict)}
    maps = {row.get("id"): row for row in manifest.get("study_maps", [])
            if isinstance(row, dict)}
    unit = units.get(str(pointer.get("unit_id") or ""))
    study_map = maps.get(str(pointer.get("study_map_id") or ""))
    stages = study_map.get("stages", []) \
        if isinstance(study_map, dict) else []
    stage_ids = {stage.get("id") for stage in stages
                 if isinstance(stage, dict)}
    if (isinstance(unit, dict) and isinstance(study_map, dict)
            and unit.get("module_id") == pointer.get("module_id")
            and study_map.get("unit_id") == unit.get("id")
            and study_map.get("module_id") == unit.get("module_id")
            and pointer.get("stage_id") in stage_ids):
        return "confirmed"
    return "invalid"


def _recorded_options(manifest) -> list[dict]:
    """Every active track's recorded next action, in id order, unranked.

    Shown regardless of pointer state: the pointer says where study stopped,
    not which active workspace to choose next. Each active workspace's own
    next action carries its id and source path, never a derived ranking. A
    workspace with no recorded action still appears, with an empty action,
    so no track silently drops out of the page.
    """
    options = []
    for record in manifest.get("records", []):
        if not isinstance(record, dict) or record.get("type") != "workspace":
            continue
        if record.get("archived") or record.get("status") != "active":
            continue
        options.append({
            "workspace_id": record.get("id"),
            "next_action": record.get("next_action") or "",
            "source": record.get("path") or "",
        })
    return sorted(options, key=lambda row: str(row["workspace_id"]))


def _brief_deadlines(manifest: dict) -> list[dict]:
    """Brief-visible deadlines: absence of evidence reads as a missing fact.

    The projection says ``unregistered`` for a sitting with no recorded
    attempt; the brief is the surface where that absence is most easily
    misread as a decision, so it says ``registration not recorded``
    instead. ``unrecorded`` (elapsed — the record should exist by now)
    passes through unchanged. Row count and order are preserved.
    """
    rows = []
    for row in manifest.get("academic_deadlines", []):
        if isinstance(row, dict) and row.get("registration_state") == "unregistered":
            row = {**row, "registration_state": "registration not recorded"}
        rows.append(row)
    return rows


def _dumps_bootstrap(payload: dict) -> str:
    """The exact brief/compact encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _dumps_bootstrap_full(payload: dict) -> str:
    """The exact full-bootstrap encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _compact_bootstrap(ctx: OpContext, req: dict) -> Result:
    """Bounded summary pages with snapshot-bound continuation (R1 delegate)."""
    root = ctx.root
    try:
        offset, limit = _window_values(
            req.get("offset"), req.get("limit"),
            req.get("expected_snapshot"), 50)
    except WriteRefused as exc:
        exc.site = f"{ctx.operation}.bad-window"
        exc.gateway_message = f"los: {exc}"
        exc.exit_code = 2
        raise
    try:
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        manifest = _fresh_manifest(root, snapshot_id=snapshot)
        fields = ("id", "title", "status", "module_id", "program_id", "unit_id",
                  "current_study_map", "current_stage", "needs_study_map")
        collections = {}
        for name in ("programs", "modules", "projects", "units", "study_maps"):
            rows = sorted(manifest.get(name, []), key=lambda row: row["id"])
            items = [{key: row[key] for key in fields if key in row}
                     for row in rows[offset:offset + limit]]
            collections[name] = {"items": items, "total": len(rows),
                                 "next_offset": offset + limit if offset + limit < len(rows) else None}
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "bootstrap-summary", "collections": collections,
             "resume_pointer": manifest.get("resume_pointer", {}),
             "counts": manifest.get("counts", {}),
             "domain_atlas": _domain_glance(manifest),
             "detail": {"record": "inspect ID", "notes": "note-read NOTE_ID",
                        "content_search": "search QUERY --type note --content",
                        "capabilities": "capabilities --compact --json",
                        "continuation": "bootstrap --compact --offset NEXT_OFFSET --expected-snapshot SNAPSHOT"},
             },
            json_dumps=_dumps_bootstrap,
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


def _brief_bootstrap(ctx: OpContext, req: dict) -> Result:
    """One-page session entry: guards, resume, owed work, deadlines, expands.

    The plan-edit-context-brief shape applied to startup: identities and
    runnable commands, never collections or prose. Owed study maps name the
    units to prep, active maps name the stages to resume, deadlines carry
    the structured exam spine, and every follow-up read is a listed
    command. Single page by construction: paging belongs to --compact.
    """
    if req.get("compact"):
        raise WriteRefused(
            "bootstrap takes one of --brief, --compact",
            site=f"{ctx.operation}.brief-and-compact",
            gateway_message="los: bootstrap takes one of --brief, --compact",
            exit_code=2,
        )
    if req.get("offset"):
        raise WriteRefused(
            "bootstrap --brief is a single page; "
            "page the collections with --compact instead",
            site=f"{ctx.operation}.brief-with-offset",
            gateway_message=("los: bootstrap --brief is a single page; "
                             "page the collections with --compact instead"),
            exit_code=2,
        )
    root = ctx.root
    try:
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        manifest = _fresh_manifest(root, snapshot_id=snapshot)
        units = sorted(manifest.get("units", []),
                       key=lambda row: row["id"])
        owed = sorted(row["id"] for row in units
                      if row.get("needs_study_map"))
        # Resumable work only: paused maps are shelved tracks, not
        # candidates for the next session. Full bootstrap still lists
        # them; the brief names what can actually start.
        active = sorted(
            ({"id": row["id"], "unit_id": row.get("unit_id"),
              "status": row.get("status"),
              "current_stage": row.get("current_stage")}
             for row in manifest.get("study_maps", [])
             if row.get("status") in {"active", "ready"}),
            key=lambda row: row["id"])
        deadlines = _brief_deadlines(manifest)
        pointer = manifest.get("resume_pointer", {})
        state = _pointer_state(manifest, pointer)
        session_id, session_source = _resolve_session_identity()
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "bootstrap-brief",
             "session_identity": {
                 "session_id": session_id,
                 "source": session_source,
                 "how_to_set": (
                     f"name it before the first write — export "
                     f"{SESSION_ID_ENV}=<id> when the shell persists, or "
                     f"seal session_id in each write envelope "
                     f"(.venv/bin/python tools/seal_envelope.py --session-id <id>); without "
                     f"either, writes share this channel's ledger"
                 ),
             },
             "resume_pointer": pointer,
             "pointer_state": state,
             "pointer_state_note": POINTER_STATE_NOTE,
             "recorded_options": _recorded_options(manifest),
             "recorded_options_note": (
                 "workspace next actions are recorded options, not current "
                 "priorities; compare with current dates and state"
             ),
             "counts": manifest.get("counts", {}),
             "owed_study_maps": owed,
             "active_study_maps": active,
             "academic_deadlines": deadlines,
             "deadline_count": len(deadlines),
             "domain_atlas": _domain_glance(manifest),
             "expand": {
                 "full_compact": expansion(
                     "bootstrap", "--compact",
                     "--expected-snapshot", snapshot),
                 "continuation": expansion(
                     "bootstrap", "--compact", "--offset", "NEXT_OFFSET",
                     "--expected-snapshot", "SNAPSHOT"),
                 "resume": expansion("resume", "--json"),
                 "inspect": expansion("inspect", "ID"),
                 "coordination": expansion("inspect", "coordination"),
                 "intelligence_scan": expansion(
                     "intelligence-scan", "--brief", "--json"),
                 "note_read": expansion("note-read", "NOTE_ID"),
                 "inbox_list": expansion("inbox-list"),
                 "inbox_read": expansion("inbox-read", "NAME"),
                 "content_search": expansion(
                     "search", "QUERY", "--type", "note", "--content"),
                 "material_context": expansion("material-context", "QUERY"),
                 "ability_context": expansion(
                     "ability-context", "--expected-snapshot", snapshot),
                 "material_span": expansion(
                     "material-span", "UNIT_ID", "ROUTE_ID"),
                 "capability_detail": expansion(
                     "capabilities", "NAME", "--json"),
                 "plan_brief": [expansion(
                     "plan-edit-context", unit_id, "--brief",
                     "--expected-snapshot", snapshot)
                                for unit_id in owed],
             },
             },
            json_dumps=_dumps_bootstrap,
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


@register("cli.bootstrap", kind="query")
@register("operator.bootstrap", kind="query")
def bootstrap(ctx: OpContext, req: dict) -> Result:
    """Serve the operator bootstrap: full, brief, or compact pages."""
    if req.get("brief"):
        return _brief_bootstrap(ctx, req)
    if req.get("compact"):
        return _compact_bootstrap(ctx, req)
    root = ctx.root
    manifest = _fresh_manifest(root, restamp=True)
    payload = {
        "capabilities": _capabilities(root),
        "snapshot": manifest.get("_generated", {}),
        "programs": manifest.get("programs", []),
        "modules": manifest.get("modules", []),
        "projects": manifest.get("projects", []),
        "units": manifest.get("units", []),
        "active_study_maps": [m for m in manifest.get("study_maps", [])
                              if m.get("status") in {"active", "paused", "ready"}],
        "resume_pointer": manifest.get("resume_pointer", {}),
        "next": "Resume the pointer or choose any visible module and unit.",
    }
    return Result(payload, json_dumps=_dumps_bootstrap_full)


def _dumps_program_list(payload) -> str:
    """The exact program-list encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


@register("cli.program-list", kind="query")
def program_list(ctx: OpContext, req: dict) -> Result:
    """List programs as discovery rows."""
    manifest = _fresh_manifest(ctx.root)
    return Result(manifest.get("programs", []), json_dumps=_dumps_program_list)
