"""Reads-area converted handlers (PLAN D4)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from learning_os import __version__
from learning_os.contracts.capability_catalog import load_capability_catalog
from learning_os.domain.failures import (
    NotFound,
    StaleSnapshot,
    WriteRefused,
    unreadable_refusal,
)
from learning_os.domain.suggest import expansion, not_found
from learning_os.genout import adoption_counts, exam_spine
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.githistory import GitHistoryError
from learning_os.material_refs import unit_routes
from learning_os.materials_resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
from learning_os.ops._legacy_plumbing import (
    SESSION_ID_ENV,
    _fresh_manifest,
    _inbox_search_rows,
    _json_layout,
    _resolve_session_identity,
    _snapshot,
    _window_values,
    ranked_scan,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError, read_text_inside
from learning_os.semantics.dossiers import (
    DossierError,
    build_dossier,
    cache_path,
    is_fresh,
    load_dossier,
    store_dossier,
)
from learning_os.semantics.goals import RankedCluster, goal_to_dict
from learning_os.semantics.predicates import (
    CONTRACT_VERSION as SEMANTIC_CONTRACT_VERSION,
)
from learning_os.semantics.predicates import (
    PREDICATES,
    evaluate,
)
from learning_os.semantics.recipes import RecipeError, recipes_for
from learning_os.semantics.session_counts import FeedError, feed_scan_kwargs
from learning_os.validation_cache import observe_pins, status_issues

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
                    "semantic-contract": str(SEMANTIC_CONTRACT_VERSION),
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


def _dumps_status(payload: dict) -> str:
    """The exact status encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _human_status(payload: dict) -> str:
    """The exact status screen: counts, exam spine, validation, home page."""
    c = payload["counts"]
    adoption = payload["adoption"]
    spine = payload["exam_spine"]
    validation = payload["validation"]
    lines = [
        f"Learning OS v3 · learning_os v{payload['learning_os']} · {payload['root']}",
        f"  notes {c['notes']} · concepts {c['concepts']} · "
        f"relations {c['concept_relations']} · sources {c['sources']}",
        f"  programs {c['programs']} · modules {c['modules']} "
        f"({c['modules_enrolled']} enrolled) · projects {c['projects']} · units {c['units']} · "
        f"study maps {c['study_maps']} · "
        f"workspaces {c['active_workspaces']} active "
        f"({c['standing_workspaces']} standing), "
        f"{c['archived_workspaces']} archived",
        f"  inbox {c['inbox_items']} top-level · {c['inbox_files']} files · "
        f"garden {c['garden_notes']} · "
        f"reviewed {adoption['notes_reviewed']}/{c['notes']} · "
        f"evidence {adoption['notes_with_evidence']}/{c['notes']}",
    ]
    if spine:
        for e in spine:
            lines.append(f"  exam: {e['date']} — {e['title']} (Termin {e['termin']})")
    else:
        lines.append("  exam: no registered attempt in any module's module.yaml")
    if validation == {"skipped": True}:
        lines.append("  validation: skipped (--no-validate)")
    else:
        errors = validation["errors"]
        warnings = validation["warnings"]
        state = f"{errors} error(s)" if errors else "OK"
        if warnings:
            state += (f" · {warnings} warning(s), visible and nonblocking "
                      "(`make warnings` for the delta)")
        lines.append(f"  validation: {state}")
    lines.append("  human home page: generated/reading-room.md (make views)")
    return "\n".join(lines)


@register("cli.status", kind="tool", human=_human_status)
def status(ctx: OpContext, req: dict) -> Result:
    """Serve the status screen: counts, exam spine, and validation."""
    root = ctx.root
    no_validate = req.get("no_validate")
    # Cache pins are observed before anything is read, so a write landing
    # mid-read can only cost a later miss, never a stale hit.
    pins = None if no_validate else observe_pins(root)
    repo = ctx.repo()
    if repo.parse_failures:
        # Fail closed like every other manifest-backed read: the counts
        # below would silently exclude whatever could not be read.
        message = unreadable_refusal(root, repo.parse_failures, "status")
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.unreadable-records",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    # --no-validate skips validation but never the refusal above: an
    # unreadable tree refuses before these counts are even considered.
    if no_validate:
        errors = warnings = 0
    else:
        issues = status_issues(repo, pins)
        errors = sum(1 for i in issues if i.severity == "E")
        warnings = sum(1 for i in issues if i.severity == "W")

    inbox = root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir()
                   if not f.name.startswith(".")]) if inbox.is_dir() else 0
    # The recursive file count agrees with `inbox-list` by construction:
    # it is the same discovery rows `inbox-list` prints. `inbox_items`
    # keeps its top-level meaning, so a folder drop still counts 1 there.
    n_inbox_files = len(_inbox_search_rows(root))
    active = repo.active_workspaces()
    ad = adoption_counts(repo)
    # Programs and modules count the way the manifest does: the quarantined
    # Master's Planning program and compatibility-only (project-migrated)
    # modules are boundary records, not study records. The projection in
    # genout/projection/records_curriculum.py (project_programs,
    # project_modules) is the authority for the filters; the
    # status/bootstrap parity test fails if the two drift apart.
    programs = [p for p in repo.programs.values()
                if p.data.get("status") not in {"quarantined", "boundary-only"}
                and p.data.get("kind") not in {"quarantine", "boundary"}]
    modules = {mid: m for mid, m in repo.modules.items()
               if not m.get("compatibility_only")}
    spine = [
        {"date": date, "module_id": mid,
         "title": module.get("title", mid), "termin": att.get("termin")}
        for date, mid, module, att in exam_spine(repo)
    ]

    payload = {
        "learning_os": __version__,
        "root": str(root),
        "counts": {
            "notes": len(repo.notes),
            "concepts": len(repo.concepts),
            "concept_relations": len(repo.relations),
            "sources": len(repo.sources),
            "programs": len(programs),
            "programs_quarantined": len(repo.programs) - len(programs),
            "modules": len(modules),
            "modules_compatibility_only": len(repo.modules) - len(modules),
            "projects": len(repo.projects),
            "modules_enrolled": sum(
                1 for m in modules.values() if m.get("status") == "enrolled"),
            "active_workspaces": len(active),
            "standing_workspaces": sum(1 for w in active if w.standing),
            "archived_workspaces": len(repo.archived_workspaces()),
            "inbox_items": n_inbox,
            "inbox_files": n_inbox_files,
            "garden_notes": len(repo.garden_notes),
            "units": len(repo.units),
            "study_maps": len(repo.study_maps),
        },
        "adoption": {
            "notes_reviewed": ad["notes_reviewed"],
            "notes_with_evidence": ad["notes_with_evidence"],
        },
        "exam_spine": spine,
        # `ok` means what validation success means: zero errors. It used to
        # require zero warnings too, which made this field permanently false
        # against a repository carrying 535 deliberately deferred warnings —
        # an always-red light nobody can act on is not a signal. Whether a
        # warning is NEW is a separate question with its own gate,
        # `tools/warning_baseline.py --check`; status does not run it, because
        # a status read must not depend on a recorded baseline being current.
        "validation": {"skipped": True} if no_validate else {
            "errors": errors, "warnings": warnings, "ok": errors == 0},
    }
    return Result(payload, json_dumps=_dumps_status,
                  diagnostic_failed=bool(errors))


def _coerce(raw: str) -> object:
    """One ``--input k=v`` value. JSON first (numbers, booleans, arrays,
    objects, quoted strings), falling back to the bare string — so
    ``--input scope=current`` and ``--input
    entries='[{"type":"derivation","ref":"note://x"}]'`` both work."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw


def _dumps_semantic(payload) -> str:
    """The exact semantic encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


@register("cli.semantic", kind="tool")
def semantic(ctx: OpContext, req: dict) -> Result:
    """Evaluate one predicate, list the registry, or serve a recipe."""
    if req.get("recipe"):
        try:
            rows = recipes_for(req["recipe"])
        except RecipeError as exc:
            raise WriteRefused(
                str(exc),
                site=f"{ctx.operation}.bad-recipe",
                gateway_message=f"los: {exc}",
                exit_code=2,
            ) from exc
        return Result({"class": req["recipe"], "recipes": rows},
                      json_dumps=_dumps_semantic)
    if req.get("list"):
        return Result(
            [{"name": name,
              "inputs": list(PREDICATES[name].authoritative_inputs),
              "authority": PREDICATES[name].authority,
              "description": PREDICATES[name].description}
             for name in sorted(PREDICATES)],
            json_dumps=_dumps_semantic)
    name = req.get("predicate")
    if name not in PREDICATES:
        message = f"unknown semantic predicate: {name}"
        see = (f"los: see `los semantic --list` for the {len(PREDICATES)} "
               "registered names")
        raise WriteRefused(
            message,
            site=f"{ctx.operation}.unknown-predicate",
            extra_stderr=(see,),
            gateway_message=f"los: {message}\n{see}",
            exit_code=2,
        )
    inputs: dict[str, object] = {}
    for item in req.get("input") or []:
        key, separator, value = item.partition("=")
        if not separator or not key.strip():
            raise WriteRefused(
                f"--input takes k=v, got {item!r}",
                site=f"{ctx.operation}.bad-input",
                gateway_message=f"los: --input takes k=v, got {item!r}",
                exit_code=2,
            )
        inputs[key.strip()] = _coerce(value)
    try:
        verdict = evaluate(name, **inputs)
    except TypeError as exc:
        raise WriteRefused(
            f"malformed inputs for {name}: {exc}",
            site=f"{ctx.operation}.malformed-inputs",
            gateway_message=f"los: malformed inputs for {name}: {exc}",
            exit_code=2,
        ) from exc
    return Result({"predicate": name, "verdict": verdict,
                   "inputs": inputs},
                  json_dumps=_dumps_semantic)


#: Brief cap: at most this many ranked groups, whatever the tiers hold. The
#: top two tiers alone held 61 groups on 2026-09-23, so a tier cutoff cannot
#: bound the page -- only a rank cutoff can.
BRIEF_GROUP_LIMIT = 5

#: Member goal ids sampled per brief group summary. The rest count toward
#: ``omitted_members`` and never print: a summary stays a summary even for
#: the largest cluster.
BRIEF_MEMBER_SAMPLE = 6


def _tier_label(row: RankedCluster) -> str:
    if row.tier == 1:
        return f"before {row.nearest_sitting} ({row.days_until}d)"
    if row.tier == 2:
        return f"ahead of {row.nearest_sitting} ({row.days_until}d)"
    if row.tier == 3:
        return "active study, no dated pressure"
    if row.tier == 5:
        return "retired module"
    return "no dated pressure"


def _full_result_route(req) -> str:
    """The runnable command for the un-truncated scan behind a brief page."""
    parts = ["intelligence-scan"]
    if req.get("days", 30) != 30:
        parts += ["--days", str(req["days"])]
    if req.get("feed"):
        parts += ["--feed", str(req["feed"])]
    return " ".join([*parts, "--json"])


def _brief_group_summary(number: int, row: RankedCluster) -> dict:
    """One bounded ranked-group summary for the brief page."""
    cluster = row.cluster
    members = list(cluster.member_ids)
    sample = members[:BRIEF_MEMBER_SAMPLE]
    return {
        "rank": number,
        "cluster_id": cluster.cluster_id,
        "detector": cluster.detector,
        "title": cluster.title,
        "tier": row.tier,
        "tier_label": _tier_label(row),
        "nearest_sitting": row.nearest_sitting,
        "days_until": row.days_until,
        "member_count": len(members),
        "sample_goal_ids": sample,
        "omitted_members": len(members) - len(sample),
    }


def _brief_scan_page(req, goals, ranked) -> dict:
    """At most five ranked groups plus totals; the agent entry path.

    Bounded by rank, never by tier: even when every shown group bears on
    an exam, the page stays five summaries. The omitted counts and
    ``full_result`` route to the complete scan; the full ``--json`` shape
    is untouched for consumers that need every goal.
    """
    shown = list(ranked[:BRIEF_GROUP_LIMIT])
    summaries = [_brief_group_summary(number, row)
                 for number, row in enumerate(shown, start=1)]
    shown_goals = sum(item["member_count"] for item in summaries)
    return {
        "contract": "intelligence-scan-brief",
        "groups": summaries,
        "total_groups": len(ranked),
        "total_goals": len(goals),
        "omitted_groups": len(ranked) - len(shown),
        "omitted_goals": len(goals) - shown_goals,
        "full_result": _full_result_route(req),
    }


def _unique_feed_object(pairs: list[tuple[str, object]]) -> dict:
    """Refuse ambiguous JSON before a duplicate key can discard evidence."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise FeedError(f"malformed feed: duplicate JSON key {key!r}")
        result[key] = value
    return result


def _dumps_intelligence_scan(payload) -> str:
    """The exact scan encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _human_intelligence_scan(payload, view) -> str:
    """The exact scan screen, rendered from the handler's view (SPEC (bu) 1)."""
    if view["goal_count"] == 0:
        return ("intelligence scan: no candidates — "
                "nothing moved that the detectors cover")
    lines = [f"intelligence scan: {view['goal_count']} candidate(s) in "
             f"{len(view['ranked'])} group(s) — review before Aram decides:"]
    attention = [row for row in view["ranked"] if row["tier"] <= 2]
    upcoming = [row["days_until"] for row in attention
                if row["days_until"] is not None]
    if upcoming:
        urgent_goals = sum(len(row["members"]) for row in attention)
        lines.append(f"{len(attention)} group(s), {urgent_goals} goal(s), bear on a "
                     f"sitting in the next {min(upcoming)}d.")
    visible = view["ranked"][:BRIEF_GROUP_LIMIT] if view["brief"] else view["ranked"]
    for number, row in enumerate(visible, start=1):
        lines.append(f"{number}. [{row['tier_label']}] {row['title']}")
        members = row["members"]
        if len(members) == 1 and members[0] in view["evidence"]:
            lines.append(f"   evidence: {', '.join(view['evidence'][members[0]])}")
        else:
            shown = ", ".join(members[:6])
            if len(members) > 6:
                shown += f" … +{len(members) - 6} more"
            lines.append(f"   goals ({len(members)}): {shown}")
    if view["brief"] and len(view["ranked"]) > len(visible):
        omitted = view["goal_count"] - sum(len(row["members"]) for row in visible)
        lines.append(f"({len(view['ranked']) - len(visible)} more group(s), {omitted} goal(s) "
                     "omitted -- rerun without --brief for the full queue)")
    lines.append("Record Aram's explicit decision per goal id: "
                 "los goal <id> --reject|--defer|--close")
    if view["hidden_count"]:
        lines.append(f"({view['hidden_count']} decided goal(s) stay hidden — see `los goal`)")
    return "\n".join(lines)


@register("cli.intelligence-scan", kind="tool", human=_human_intelligence_scan)
def intelligence_scan(ctx: OpContext, req: dict) -> Result:
    """Run one observation loop: observe, interpret, propose.

    ``--brief`` caps the page at five ranked groups plus totals; with
    ``--json`` that is the agent entry path. ``--feed`` reads a
    caller-owned JSON session-count file (see session_counts) so the
    three count detectors can fire; the scan never writes it.
    """
    if req["days"] < 0:
        raise WriteRefused(
            "intelligence scan: --days is never negative",
            site=f"{ctx.operation}.negative-days",
            exit_code=2,
        )
    feed = None
    if req.get("feed"):
        try:
            raw = Path(req["feed"]).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise WriteRefused(
                f"intelligence scan: cannot read --feed: {exc}",
                site=f"{ctx.operation}.unreadable-feed",
                exit_code=2,
            ) from exc
        try:
            feed = json.loads(raw, object_pairs_hook=_unique_feed_object)
        except FeedError as exc:
            raise WriteRefused(
                f"intelligence scan: {exc}",
                site=f"{ctx.operation}.malformed-feed",
                exit_code=2,
            ) from exc
        except (ValueError, RecursionError) as exc:
            raise WriteRefused(
                f"intelligence scan: --feed is not JSON: {exc}",
                site=f"{ctx.operation}.feed-not-json",
                exit_code=2,
            ) from exc
        try:
            feed_scan_kwargs(feed)
        except FeedError as exc:
            raise WriteRefused(
                f"intelligence scan: {exc}",
                site=f"{ctx.operation}.invalid-feed",
                exit_code=2,
            ) from exc
    root = ctx.root
    try:
        goals, ranked, hidden = ranked_scan(root, days=req["days"], feed=feed)
    except GitHistoryError as exc:
        raise WriteRefused(
            f"intelligence scan: cannot read Git history: {exc}",
            site=f"{ctx.operation}.git-history",
            exit_code=2,
        ) from exc
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            f"intelligence scan: cannot rank the queue: {exc}",
            site=f"{ctx.operation}.unrankable-queue",
            exit_code=2,
        ) from exc
    if req.get("brief"):
        payload = _brief_scan_page(req, goals, ranked)
    else:
        payload = {"goals": [goal_to_dict(goal) for goal in goals]}
    view = {
        "brief": bool(req.get("brief")),
        "goal_count": len(goals),
        "ranked": [{
            "tier": row.tier,
            "nearest_sitting": row.nearest_sitting,
            "days_until": row.days_until,
            "title": row.cluster.title,
            "members": list(row.cluster.member_ids),
            "tier_label": _tier_label(row),
        } for row in ranked],
        "evidence": {goal.goal_id: list(goal.evidence) for goal in goals},
        "hidden_count": hidden,
    }
    return Result(payload, json_dumps=_dumps_intelligence_scan, human_view=view)


# The OPERATOR contract (system/OPERATOR.md) — what `los.py capabilities`
# announces about the gateway itself. This is a third, independent version:
#   operator/gateway contract  here (CONTRACT_VERSION below)
#   canonical record format    system/contracts/data-contract.yaml
#   published manifest shape   system/contracts/manifest-contract.yaml
# Three contracts sharing the name "contract_version" is how the manifest came
# to be published under an old version after its shape had already changed
# (2026-08-08). Stored and projected versions must always be read from their
# producer-owned declarations, never copied into this comment.
CONTRACT_VERSION = 2


def _capabilities(root: Path) -> dict:
    """Return the executable capability catalogue, not a duplicated list."""
    catalogue = load_capability_catalog(root)
    return {
        "contract_version": CONTRACT_VERSION,
        "capability_contract_version": catalogue["contract_version"],
        "cli_protocol": catalogue.get("cli_protocol", 3),
        "gateway": "tools/los.py",
        "projection": "generated/manifest.json",
        "operator_contract": "system/OPERATOR.md",
        "queries": catalogue.get("queries", {}),
        "commands": catalogue.get("commands", {}),
        "rules": {
            "canonical_writes_are_transactional": True,
            "successful_writes_have_receipts": True,
            "artifact_revision_conflicts_fail_closed": True,
            "shelving_requires_explicit_approval": True,
            "ordinary_interfaces_read_projection_only": True,
            "module_plan_preflight_required": True,
            "ai_actions_are_provider_independent": True,
            "bounded_ai_actions_use_exact_context": True,
        },
        "root": str(root),
    }


def _dumps_capabilities_compact(payload) -> str:
    """The exact name/compact encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _dumps_capabilities(payload) -> str:
    """The exact capabilities encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _human_capabilities(payload, view) -> str:
    """The exact capabilities screen (SPEC (bu) 1).

    The name/compact branches print JSON even without ``--json``; the
    human renderer replays those exact bytes, selected by the view's
    branch. The default branch renders the five-line screen.
    """
    if view["branch"] in ("name", "compact"):
        return _dumps_capabilities_compact(payload)
    return "\n".join(
        [f"LearningOS operator contract v{payload['contract_version']}",
         f"  gateway: {payload['gateway']}",
         f"  projection: {payload['projection']}",
         "  transactional commands: " + ", ".join(sorted(payload["commands"])),
         "  every successful canonical write has one receipt"])


@register("cli.capabilities", kind="tool", human=_human_capabilities)
def capabilities(ctx: OpContext, req: dict) -> Result:
    """Serve the machine discovery/read catalogue, in full or in part."""
    root = ctx.root
    payload = _capabilities(root)
    name = req.get("name")
    compact = req.get("compact")
    if name and compact:
        raise WriteRefused(
            "choose --compact or one capability name",
            site=f"{ctx.operation}.compact-and-name",
            gateway_message="los: choose --compact or one capability name",
            exit_code=2,
        )
    if name:
        section = next((key for key in ("queries", "commands") if name in payload[key]), None)
        if section is None:
            raise WriteRefused(
                f"unknown or non-public capability: {name}",
                site=f"{ctx.operation}.unknown-capability",
                gateway_message=f"los: unknown or non-public capability: {name}",
                exit_code=2,
            )
        definition = payload[section][name]
        for key in ("queries", "commands"):
            payload[key] = {name: definition} if key == section else {}
        if section == "commands":
            relative = f"system/schema/capabilities/{name}.schema.json"
            try:
                schema = json.loads(read_text_inside(root, root / relative))
                if not isinstance(schema, dict):
                    raise ValueError("payload schema must be an object")
            except (OSError, PathBoundaryError, ValueError) as exc:
                raise WriteRefused(
                    f"cannot read declared payload schema: {exc}",
                    site=f"{ctx.operation}.unreadable-payload-schema",
                    gateway_message=f"los: cannot read declared payload schema: {exc}",
                    exit_code=2,
                ) from exc
            payload["payload_schema_path"] = relative
            payload["payload_schema"] = schema
        return Result(payload, json_dumps=_dumps_capabilities_compact,
                      human_view={"branch": "name"})
    if compact:
        for key in ("queries", "commands"):
            payload[key] = sorted(payload[key])
        payload["detail"] = "capabilities NAME --json"
        return Result(payload, json_dumps=_dumps_capabilities_compact,
                      human_view={"branch": "compact"})
    return Result(payload, json_dumps=_dumps_capabilities,
                  human_view={"branch": "screen"})
