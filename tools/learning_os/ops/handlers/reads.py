"""Reads-area converted handlers (PLAN D4)."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

from learning_os import __version__
from learning_os.contracts.capability_catalog import load_capability_catalog
from learning_os.contracts.json_schema import ContractValidationError, validate_contract
from learning_os.domain.failures import (
    NotFound,
    StaleSnapshot,
    WriteRefused,
    unreadable_refusal,
)
from learning_os.domain.suggest import expansion, not_found, with_suggestions
from learning_os.genout import adoption_counts, exam_spine
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.genout.common import _first_para
from learning_os.genout.learner_interpreter import _collect_and_interpret
from learning_os.genout.modules_view import _academic_deadlines
from learning_os.genout.projection.atlas import STAGE_CONCEPT
from learning_os.genout.resume_dossier import ResumeDossierError, build_resume_dossier
from learning_os.genout.session_compiler import compile_session, replan_session
from learning_os.githistory import GitHistoryError, last_commit_date
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    stage_results_for,
)
from learning_os.material_refs import unit_routes
from learning_os.materials_resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
from learning_os.observations import today as observed_today
from learning_os.ops._legacy_plumbing import (
    SESSION_ID_ENV,
    _evidence_label,
    _fresh_manifest,
    _inbox_search_rows,
    _json_layout,
    _resolve_session_identity,
    _snapshot,
    _use_evidence,
    _window_values,
    ranked_scan,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError, read_text_inside, resolved_inside
from learning_os.semantics.dossiers import (
    DossierError,
    build_dossier,
    cache_path,
    is_fresh,
    load_dossier,
    store_dossier,
)
from learning_os.semantics.goals import RankedCluster, goal_to_dict, stale_observations
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


def _use_evidence_from_manifest(manifest: dict) -> dict[str, dict[str, int]]:
    """Recorded stage-use evidence per source id, read from the manifest.

    The same tally `_use_evidence` computes from the loaded repo: every
    study map is projected and projected stages keep `source_feedback`
    verbatim, so the two agree exactly. Lets `related` skip the repo load
    on the manifest-reuse fast path (#83).
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        for stage in study_map.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


#: Declared-edge fields walked from the record itself, in stable order.
RELATED_LIST_FIELDS = ("concepts", "sources", "contexts", "notes",
                       "program_ids", "module_ids", "unit_ids", "unit_order",
                       "related_module_ids")
RELATED_SCALAR_FIELDS = ("workspace_id", "area_id", "module_id", "unit_id",
                         "current_study_map")

#: Backlink tables walked in both directions. Every table maps an owner to
#: its members; the walk answers the direct lookup and the inverse scan, so
#: membership in one direction always implies the reverse edge (JF-15). The
#: differently-shaped concept_relations table stays out: concept relations
#: are already walked both ways from the manifest relations list.
RELATED_BACKLINK_TABLES = ("concept_to_notes", "source_to_notes",
                           "workspace_to_notes", "module_to_workspaces",
                           "unit_to_workspaces", "module_to_units",
                           "source_to_units", "note_incoming")

#: The read-time label for a note→source analysis edge (#81). The edge says
#: "this note analyses pages of that source", not "this note cites it".
ANALYSES_VIA = "analyses"


def _analysis_source_of(record) -> str | None:
    """The registered source a record's resolved analysis binds, or None."""
    binding = record.get("material_analysis") if isinstance(record, dict) else None
    if not isinstance(binding, dict) or binding.get("resolution") != "resolved":
        return None
    source_id = binding.get("source_id")
    return source_id if isinstance(source_id, str) else None


def related_records(manifest: dict, raw_id: str, repo=None, *, tallies=None) -> list[dict]:
    """Ranked one-hop connections for one record id.

    Pure over the manifest (plus recorded use-evidence tallied from the
    repo when given, or the precomputed `tallies` when the caller read
    them from the manifest instead): the record's own declared edges,
    every backlink table in both directions, concept relations both ways,
    project relationships both ways, and the published module-concept
    edges between a concept and the units whose stages tag it (each edge
    reasoned by its stage, `stage-concept:<stage-id>`). Unknown ids
    answer [] — the caller owns the not-found error. Aliases resolve
    through project_aliases.

    Ranking is deterministic: more distinct edges first, then recorded
    stage use-evidence per source exactly as material-context ranks it
    (positive counts first, mismatch counts last), then stable id order.
    Each result names the edges that produced it in `via`. A source↔note
    edge through `source_to_notes` gains the additional `analyses` token
    when the note's resolved material analysis binds that source (#81).
    """
    by_id = {r.get("id"): r for r in manifest.get("records", [])}
    resolved = (manifest.get("project_aliases") or {}).get(raw_id, raw_id)
    rec = by_id.get(resolved)
    if rec is None:
        return []
    reasons: dict[str, set[str]] = {}

    def link(rid, why):
        if isinstance(rid, str) and rid in by_id:
            reasons.setdefault(rid, set()).add(why)

    for key in RELATED_LIST_FIELDS:
        for rid in rec.get(key, []) or []:
            link(rid, key)
    for key in RELATED_SCALAR_FIELDS:
        if rec.get(key):
            link(rec[key], key)
    backlinks = manifest.get("backlinks", {}) or {}
    for table in RELATED_BACKLINK_TABLES:
        members = (backlinks.get(table) or {}).get(resolved, []) or []
        for rid in members:
            link(rid, f"backlink:{table}")
            if table == "source_to_notes" \
                    and _analysis_source_of(by_id.get(rid)) == resolved:
                link(rid, ANALYSES_VIA)
        for owner, owned in ((backlinks.get(table) or {}).items()):
            if isinstance(owned, list) and resolved in owned:
                link(owner, f"inverse:{table}")
                if table == "source_to_notes" \
                        and _analysis_source_of(by_id.get(resolved)) == owner:
                    link(owner, ANALYSES_VIA)
    for relation in manifest.get("relations", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from") == resolved:
            link(relation.get("to"), "relation")
        if relation.get("to") == resolved:
            link(relation.get("from"), "relation")
    # Stage concept tags ride the published module-concept edges (#97): a
    # concept links to the units whose stages tag it, and a unit links to
    # its stages' concepts, each edge reasoned by its exact stage. Stages
    # are structural sub-ids, not records, so they reason the edge rather
    # than row in it. Knowledge-node evidence stays out: the edge kind and
    # the issue scope are stage tags only.
    for edge in manifest.get("module_concept_edges", []) or []:
        if not isinstance(edge, dict):
            continue
        concept_id = edge.get("concept_id")
        for evidence in edge.get("evidence") or []:
            if not isinstance(evidence, dict):
                continue
            if evidence.get("kind") != STAGE_CONCEPT:
                continue
            unit_id = evidence.get("unit_id")
            stage_id = evidence.get("stage_id")
            if not unit_id or not stage_id:
                continue
            reason = f"{STAGE_CONCEPT}:{stage_id}"
            if resolved == concept_id:
                link(unit_id, reason)
            if resolved == unit_id:
                link(concept_id, reason)
    for relation in manifest.get("project_relationships", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from_project_id") == resolved:
            link(relation.get("to_id"), "project_relationship")
        if relation.get("to_id") == resolved:
            link(relation.get("from_project_id"), "project_relationship")
    if repo is not None:
        tallies = _use_evidence(repo)
    elif tallies is None:
        tallies = {}
    ranked = []
    for rid, whys in reasons.items():
        tally = tallies.get(rid, {}) if by_id[rid].get("type") == "source" else {}
        label = _evidence_label(tally)
        ranked.append((-len(whys), -label["positive"], label["mismatch"], rid))
    ranked.sort()
    return [{"id": rid, "type": by_id[rid].get("type"),
             "title": by_id[rid].get("title"), "path": by_id[rid].get("path"),
             "via": sorted(reasons[rid])}
            for _, _, _, rid in ranked]


def _dumps_related(payload) -> str:
    """The exact related encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


@register("cli.related", kind="query")
def related(ctx: OpContext, req: dict) -> Result:
    """Ranked one-hop connections for one record id."""
    root = ctx.root
    manifest = _fresh_manifest(root)
    by_id = {r.get("id"): r for r in manifest["records"]}
    resolved_id = (manifest.get("project_aliases") or {}).get(req["id"], req["id"])
    if resolved_id not in by_id:
        message = not_found("record", req["id"], by_id)
        raise NotFound(
            "record", req["id"], by_id,
            site=f"{ctx.operation}.unknown-id",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    # Tallies come from the manifest itself (identical to the repo tally),
    # so related skips the repo load on the reuse fast path (#83).
    out = related_records(manifest, resolved_id, None,
                          tallies=_use_evidence_from_manifest(manifest))
    return Result(out, json_dumps=_dumps_related)


def _live_observations(observations: list[dict]) -> list[dict]:
    """Non-superseded observations, newest first. Unparseable timestamps
    sort as oldest rather than crashing the screen."""
    superseded = {obs.get("supersedes") for obs in observations
                  if isinstance(obs, dict) and obs.get("supersedes")}
    live = [obs for obs in observations
            if isinstance(obs, dict) and obs.get("id") not in superseded]

    def _when(obs: dict) -> str:
        stamp = obs.get("timestamp")
        if not isinstance(stamp, str):
            return ""
        try:
            _dt.datetime.fromisoformat(stamp)
        except ValueError:
            return ""
        return stamp

    return sorted(live, key=_when, reverse=True)


def _resolve_stage(repo):
    """Return ``(via, module_id, unit_id, study_map_id, stage_id)``.

    The pointer wins when it resolves. It is the learner's own last explicit
    study action — `stage.progress.update` writes it in the same transaction
    as the records that moved — so nothing derived may outrank it. What
    follows is *recovery* for a pointer that is missing or no longer resolves,
    labeled as such on the screen: the last recorded result, then the most
    recently touched study map.

    Recovery guesses, and it should look like a guess. It reads commit
    timestamps and evidence chronology, neither of which is a statement of
    intent: a result recorded against one subject says nothing about which
    subject he chose to sit down with next. Before 2026-09-13 nothing wrote
    the pointer at all, so this fallback *was* the destination, and activating
    an Analysis stage still sent him back to Statistics (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F05).
    """
    pointer = repo.resume_pointer if isinstance(repo.resume_pointer, dict) else {}
    # Reaching past this point at all is recovery, and the screen says so
    # either way. A pointer that exists but no longer resolves and a pointer
    # that was never written are the same thing to the learner — both mean
    # "nobody recorded where you were, so this is a guess" — and labelling
    # only the first left the second reading like an answer.
    stale = True
    if pointer:
        unit = repo.units.get(str(pointer.get("unit_id") or ""))
        study_map = repo.study_maps.get(str(pointer.get("study_map_id") or ""))
        stages = study_map.data.get("stages", []) \
            if study_map is not None else []
        stage = next((s for s in stages
                      if isinstance(s, dict) and s.get("id") == pointer.get("stage_id")),
                     None)
        if unit is not None and study_map is not None and stage is not None \
                and unit.module_id == pointer.get("module_id") \
                and study_map.unit_id == unit.id \
                and study_map.module_id == unit.module_id:
            return ("resume pointer", unit.module_id, unit.id,
                    study_map.id, str(stage["id"]))
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError:
        requirements = []
    try:
        observations = _live_observations(read_observations(repo, requirements))
    except RuntimeInputError:
        observations = []
    known = {req["id"]: req for req in requirements if isinstance(req, dict)}
    for obs in observations:
        req = known.get(obs.get("requirement", ""))
        if not isinstance(req, dict):
            continue
        source = req.get("source_stage", {})
        unit = repo.units.get(str(source.get("unit_id") or ""))
        study_map = repo.study_maps.get(
            (unit.data or {}).get("current_study_map", "")) if unit else None
        if unit is None or study_map is None:
            continue
        label = "last recorded result"
        if stale:
            label += " (resume pointer missing or stale)"
        return (label, unit.module_id, unit.id, study_map.id,
                str(source.get("stage_id") or ""))
    try:
        from learning_os.githistory import last_commit_timestamps

        stamps = last_commit_timestamps(str(repo.root))
    except GitHistoryError:
        stamps = {}
    touched: list[tuple[float, str]] = []
    for rel, stamp in stamps.items():
        if not rel.endswith("study-map.yaml"):
            continue
        try:
            when = float(stamp)
        except (TypeError, ValueError):
            continue
        touched.append((when, rel))
    # Newest touch wins, and only that. This used to skip past the newest map
    # to find one whose stage had an authored runtime requirement — so the
    # recovered destination preferred a stage the evidence loop could be
    # demonstrated on over the stage most recently worked. One authored
    # requirement exists today, which made "prefer a runtime stage" and
    # "always return to that one stage" the same rule. A screen honestly
    # reporting "none authored" for the map he actually touched is the
    # truthful answer; steering him somewhere else to have something to show
    # is not (audit `synthetic-learner-2026-09-12`, F05).
    maps = {}
    for study_map in repo.study_maps.values():
        try:
            rel = study_map.path.relative_to(repo.root).as_posix()
        except (OSError, ValueError, AttributeError):
            continue
        maps[rel] = study_map
    fallback = None
    for _, rel in sorted(touched, reverse=True):
        study_map = maps.get(rel)
        if study_map is None:
            continue
        current = (study_map.data or {}).get("current_stage")
        stages = [s for s in (study_map.data or {}).get("stages", [])
                  if isinstance(s, dict)]
        stage = next((s for s in stages if s.get("id") == current),
                     stages[0] if stages else None)
        if stage is None:
            continue
        label = "recently touched stage"
        if stale:
            label += " (resume pointer missing or stale)"
        fallback = (label, study_map.module_id, study_map.unit_id,
                    study_map.id, str(stage["id"]))
        break
    if fallback is not None:
        return fallback
    return (None, "no resumable stage: the resume pointer is missing or stale, "
                  "no results were ever recorded, and no study map was ever "
                  "touched — start any stage to set one")


#: Study-map statuses eligible for the exam menu, best first. Active
#: maps are work in progress, paused ones are shelved tracks worth
#: resuming, ready ones are prepared ground; anything else (not-started
#: and beyond) is not a next step.
_STUDY_STATUS_RANK = {"active": 0, "paused": 1, "ready": 2}

#: At most this many options; the menu stays one screen.
MAX_STUDY_OPTIONS = 5

#: At most this many untargeted rows ride the resume screen; the section's
#: ``total`` stays exact past the bound. A copy of the bound plan's
#: material.py reads from commands.resume: one integer, two screens, each
#: area owns its copy so neither pair edits the other's files.
MAX_STAGE_RESULTS = 5


def _display_registration_state(state: object) -> object:
    """The learner-facing phrase for one projected registration state.

    The projection says ``unregistered`` for a sitting with no recorded
    attempt; on this screen that absence reads as a missing fact, never
    a decision, so it says ``registration not recorded`` — the same
    phrase the brief uses. ``unrecorded`` (elapsed) and every settled
    state pass through unchanged, as do the manifest values themselves.
    """
    if state == "unregistered":
        return "registration not recorded"
    return state


def _nearest_exam(repo):
    """(date, module_id, exam row) for the nearest recorded exam, or None."""
    today = observed_today()
    exams = []
    for row in _academic_deadlines(repo):
        if not isinstance(row, dict) or row.get("kind") != "exam":
            continue
        module_id = row.get("module_id")
        module = repo.modules.get(module_id)
        if not isinstance(module, dict) or module.get("status") != "enrolled":
            continue
        if row.get("registration_state") not in {"registered", "unregistered"}:
            continue
        try:
            date = _dt.date.fromisoformat(row.get("start_date", ""))
        except (TypeError, ValueError):
            continue
        if date >= today:
            exams.append((date, str(module_id), row))
    if not exams:
        return None
    return min(exams, key=lambda item: (item[0], item[1]))


def _study_open(stage):
    """The first required-now resource locator, or None (today's shape)."""
    resource = next((row for row in stage.get("resources", [])
                     if isinstance(row, dict)
                     and row.get("scope_triage") == "required-now"
                     and row.get("label") and row.get("locator")), None)
    if resource is None:
        return None
    return {"label": resource["label"], "locator": resource["locator"],
            "source_id": resource.get("source_id")}


def _study_stage(repo, study_map):
    """(stage_id, stage) for one map's current stage, else None."""
    stage_id = (study_map.data or {}).get("current_stage")
    stage = next((row for row in (study_map.data or {}).get("stages", [])
                  if isinstance(row, dict) and row.get("id") == stage_id), None)
    if not isinstance(stage_id, str) or stage is None \
            or study_map.unit_id not in repo.units:
        return None
    return stage_id, stage


def _single_study_option(repo, date, exam, study_map):
    """Today's single suggestion: the resolved stage plus the option row."""
    found = _study_stage(repo, study_map)
    if found is None:
        return (None, f"{study_map.id} has no resolvable current stage; "
                      f"inspect it with `inspect {study_map.id}`")
    stage_id, stage = found
    if stage.get("status") in {"complete", "archived"}:
        return (None, f"{study_map.id} names a completed current stage; "
                      f"inspect it with `inspect {study_map.id}`")
    option = {
        "exam_date": date.isoformat(),
        "registration_state": _display_registration_state(
            exam.get("registration_state")),
        "open": _study_open(stage),
        "learner_choice": False,
    }
    resolved = ("nearest recorded exam (study suggestion)", study_map.module_id,
                study_map.unit_id, study_map.id, stage_id)
    return (resolved, option)


def _study_option_row(repo, study_map):
    """One menu row, or None when the map names nothing studyable.

    A map whose current stage is missing, unresolvable, or already
    complete offers no next step, so it offers no row either — the menu
    lists stages to study, not maps to admire.
    """
    found = _study_stage(repo, study_map)
    if found is None:
        return None
    stage_id, stage = found
    if stage.get("status") in {"complete", "archived"}:
        return None
    return {
        "unit_id": study_map.unit_id,
        "study_map_id": study_map.id,
        "current_stage": stage_id,
        "stage_title": stage.get("title") or stage_id,
        "open": _study_open(stage),
        "learner_choice": False,
    }


def _study_options_payload(repo, date, module_id, exam):
    """The bounded exam menu: payload dict, or a refusal when it is empty.

    Active maps first, then paused, then ready, each run in curriculum
    order; at most five rows. Every refusal names a command that exists.
    """
    pool = [study_map for study_map in repo.study_maps.values()
            if study_map.module_id == module_id
            and (study_map.data or {}).get("status") in _STUDY_STATUS_RANK]

    def order(study_map):
        unit = repo.units.get(study_map.unit_id)
        rank = (unit.data or {}).get("order") if unit is not None else None
        return (_STUDY_STATUS_RANK[(study_map.data or {}).get("status")],
                rank is None, rank if isinstance(rank, int) else 0,
                study_map.unit_id, study_map.id)

    options = []
    for study_map in sorted(pool, key=order):
        row = _study_option_row(repo, study_map)
        if row is not None:
            options.append(row)
        if len(options) >= MAX_STUDY_OPTIONS:
            break
    if not options:
        return (f"{module_id} has no active, paused, or ready study maps "
                f"with a current stage; list its units with `unit-list "
                f"--compact --module-id {module_id}`")
    return {
        "contract": "resume-study-options",
        "module_id": module_id,
        "exam_date": date.isoformat(),
        "registration_state": _display_registration_state(
            exam.get("registration_state")),
        "options": options,
        "select_with": "resume --study --unit UNIT_ID",
    }


def _study_option(repo, unit_id=None):
    """One study suggestion, the options menu, or a refusal.

    Returns ``(resolved, option)`` exactly as today when the exam module
    has one active map — or when ``--unit`` selects one map explicitly.
    When the exam module has 0 or >=2 active maps, returns ``(None,
    options-payload)``: a bounded menu, never a guess. Otherwise
    ``(None, refusal-text)``, where every refusal names a command that
    exists. Never moves the resume pointer on any path.
    """
    exam = _nearest_exam(repo)
    if exam is None:
        return (None, "no upcoming exam is recorded for an enrolled module; "
                      "`status` shows the recorded exam spine")
    date, module_id, exam_row = exam
    if unit_id is not None:
        unit = repo.units.get(unit_id)
        if unit is None:
            module_units = [uid for uid, row in repo.units.items()
                            if row.module_id == module_id]
            refusal = with_suggestions(f"unit not found: {unit_id}",
                                       unit_id, module_units)
            return (None, f"{refusal}; list the exam "
                          f"module's units with `unit-list --compact "
                          f"--module-id {module_id}`")
        if unit.module_id != module_id:
            return (None, f"unit {unit_id} is outside the nearest-exam "
                          f"module {module_id}; run `resume --study` to "
                          "list its options")
        pool = sorted(
            (study_map for study_map in repo.study_maps.values()
             if study_map.unit_id == unit_id
             and (study_map.data or {}).get("status") in _STUDY_STATUS_RANK),
            key=lambda row: (_STUDY_STATUS_RANK[(row.data or {}).get("status")],
                             row.id))
        if not pool:
            return (None, f"unit {unit_id} has no active, paused, or ready "
                          f"study map; inspect it with `inspect {unit_id}`")
        return _single_study_option(repo, date, exam_row, pool[0])
    maps = [study_map for study_map in repo.study_maps.values()
            if study_map.module_id == module_id
            and (study_map.data or {}).get("status") == "active"]
    if len(maps) == 1:
        return _single_study_option(repo, date, exam_row, maps[0])
    return (None, _study_options_payload(repo, date, module_id, exam_row))


#: Trailing excerpt kept in the dossier: progress notes append, so the
#: tail is the latest recorded work. Bounded so the screen stays one page.
STAGE_NOTE_EXCERPT_CHARS = 800


def _stage_note_facts(root: Path, stage: dict) -> dict | None:
    """Bounded facts about one stage's working note, or None.

    None means the stage names no note. A missing or unreadable file is
    zero lines — "nothing recorded yet", never an error: resume is a
    best-effort screen, and the validator (not this read) names defects.
    A note path escaping the tree is also None; serving it would be the
    defect this read must not add.
    """
    if not isinstance(stage, dict):
        return None
    rel = stage.get("working_note")
    if not isinstance(rel, str) or not rel:
        return None
    try:
        candidate = resolved_inside(root, root / rel, strict=False)
    except PathBoundaryError:
        return None
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace") \
            if candidate.is_file() else ""
    except OSError:
        text = ""
    excerpt = text[-STAGE_NOTE_EXCERPT_CHARS:]
    if len(text) > STAGE_NOTE_EXCERPT_CHARS:
        excerpt = excerpt.split("\n", 1)[-1]
    try:
        updated = last_commit_date(root, rel) or None
    except GitHistoryError:
        updated = None
    return {"working_note": rel, "lines": len(text.splitlines()),
            "updated": updated, "excerpt": excerpt}


def _top_cluster(root: Path) -> dict | None:
    """The single highest-ranked goal cluster, or None.

    Best-effort read-only: a scan that cannot run (no Git history, bad
    input) leaves the screen unchanged rather than refusing it. Bounded
    to one cluster with countdown-free fields, so the dossier digest
    moves when the top cluster moves and never with the clock.
    """
    try:
        from learning_os.ops._legacy_plumbing import ranked_scan

        _, ranked, _ = ranked_scan(root, days=30)
    except (GitHistoryError, OSError, ValueError):
        return None
    if not ranked:
        return None
    row = ranked[0]
    cluster = row.cluster
    return {
        "cluster_id": cluster.cluster_id,
        "detector": cluster.detector,
        "title": cluster.title,
        "tier": row.tier,
        "nearest_sitting": row.nearest_sitting,
        "member_count": len(cluster.member_ids),
    }


def _open_items(root: Path, repo, unit_id: str, stage_id: str,
                requirement_id: str | None) -> tuple[str, ...]:
    """Workspace Deferred bullets plus deferred-item lines naming this unit."""
    items: list[str] = []

    def covers(meta: dict) -> bool:
        return unit_id in meta.get("unit_ids", [])

    for workspace in sorted(repo.workspaces.values(), key=lambda ws: ws.id):
        if workspace.archived or workspace.status != "active" \
                or not covers(workspace.meta):
            continue
        section = workspace.section("Deferred")
        if not section:
            continue
        items.extend(
            line[2:].strip() for line in section.splitlines()
            if line.startswith("- ") and line[2:].strip())
    needles = {unit_id, stage_id, *( [requirement_id] if requirement_id else [])}
    proposals = root / "work/proposals"
    try:
        deferred = sorted(proposals.glob("deferred-items-*.md"))
    except OSError:
        deferred = []
    for path in deferred:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        items.extend(
            line.strip()[:200] for line in lines
            if any(needle in line for needle in needles) and line.strip())
    return tuple(items[:8])


def _recorded_aims(repo, module_id: str, unit_id: str) -> list[tuple[str, str, str]]:
    """At most two sourced planning excerpts; neither is a fresh priority."""
    aims: list[tuple[str, str, str]] = []

    def excerpt(value: str, limit: int) -> str:
        value = value.replace("**", "").replace("`", "")
        if len(value) <= limit:
            return value
        prefix = value[:limit]
        sentences = [match.end() for match in re.finditer(r"[.!?](?:\s|$)", prefix)
                     if match.end() >= limit // 2]
        return (prefix[:sentences[-1]].rstrip() if sentences else
                prefix.rsplit(" ", 1)[0]) + "…"

    if repo.coordination is not None:
        priority = _first_para(repo.coordination.section("Priorities"))
        if priority:
            date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", priority)
            label = f"Coordination decision {date.group()}" if date else "Coordination priorities (undated)"
            aims.append((label, excerpt(priority, 260), "work/COORDINATION.md#Priorities"))
    owning = [ws for ws in repo.workspaces.values()
              if not ws.archived and ws.status == "active"
              and (unit_id in (ws.meta.get("unit_ids") or [])
                   or module_id in (ws.meta.get("module_ids") or []))]
    owning.sort(key=lambda ws: (unit_id not in (ws.meta.get("unit_ids") or []), ws.id))
    if owning:
        workspace = owning[0]
        next_action = _first_para(workspace.section("Next Action"))
        if next_action:
            source = workspace.path.relative_to(repo.root).as_posix() + "#Next-Action"
            aims.append((f"Workspace {workspace.id}", excerpt(next_action, 450), source))
    return aims


def _ago(day: str) -> str:
    """Render-time relative time; never hashed, never trusted to parse."""
    try:
        delta = (observed_today() - _dt.date.fromisoformat(day)).days
    except ValueError:
        return ""
    if delta < 0:
        return ""
    if delta == 0:
        return " (today)"
    if delta == 1:
        return " (yesterday)"
    return f" ({delta} days ago)"


def _render(dossier, requirement, observations, open_items, sittings,
            titles, via_detail: str, stale_count: int = 0,
            top_cluster: dict | None = None,
            recorded_aims: list[tuple[str, str, str]] | None = None,
            stage_note: dict | None = None,
            stage_progress: dict | None = None,
            stage_results: dict | None = None,
            today: _dt.date | None = None) -> str:
    # The screen's clock read lives with the caller: renderers must not
    # perform audited observation reads (SPEC §3.5b). The default keeps
    # direct callers on the seam clock.
    if today is None:
        today = observed_today()
    lines = [f"{titles['module']} · {titles['unit']} · {dossier.stage_id}",
             f"  ({via_detail})", ""]
    if recorded_aims:
        lines.append("  Recorded aims (compare with current dates and state):")
        for label, excerpt, source in recorded_aims[:2]:
            lines.append(f"    {label}: {excerpt}")
            lines.append(f"      source: {source}")
        lines.append("")
    if isinstance(requirement, dict):
        capability = requirement.get("capability", {})
        concept = str(requirement.get("concept", ""))
        lines.append(f"  Requirement  {concept}")
        lines.append(f"               capability: {json.dumps(capability, sort_keys=True)}")
        lines.append(f"               under: {', '.join(requirement.get('conditions', [])) or '—'}")
        lines.append(f"               evidence: {', '.join(requirement.get('evidence_spec', [])) or '—'}")
    else:
        lines.append("  Requirement  none authored for this stage")
    lines.append("")
    if observations:
        lines.append(f"  Evidence     {len(observations)} recorded")
        last = observations[0]
        lines.append(f"  Last result  {last.get('result')} ({last.get('timestamp', '?')})")
    else:
        lines.append("  Evidence     none recorded yet")
        lines.append("  Last result  none")
    if stale_count:
        noun = "result" if stale_count == 1 else "results"
        lines.append(f"  Changed since  {stale_count} earlier {noun} "
                     "were against a requirement that has since changed.")
    if isinstance(stage_results, dict) and stage_results.get("total"):
        total = stage_results["total"]
        noun = "result" if total == 1 else "results"
        lines.append(f"  Stage results  {total} untargeted {noun} (no credit — "
                     "context only, never retro-credited)")
        first = (stage_results.get("results") or [{}])[0]
        lines.append(f"  Last untargeted  {first.get('result', '?')} "
                     f"({first.get('timestamp', '?')}) — {first.get('activity', '?')}")
    if isinstance(stage_note, dict) and stage_note.get("working_note"):
        count = stage_note.get("lines") or 0
        noun = "line" if count == 1 else "lines"
        when = f", updated {stage_note['updated']}" if stage_note.get("updated") else ""
        if count > 0:
            lines.append(f"  Stage note   {count} {noun} recorded ({stage_note['working_note']}{when})")
            tail = [line for line in (stage_note.get("excerpt") or "").splitlines()
                    if line.strip()][-3:]
            lines.extend(f"               {line[:200]}" for line in tail)
        else:
            lines.append(f"  Stage note   nothing recorded yet ({stage_note['working_note']})")
    if isinstance(stage_progress, dict) and stage_progress.get("summary"):
        when = f" (updated {stage_progress['updated']})" if stage_progress.get("updated") else ""
        lines.append(f"  Progress     {str(stage_progress['summary'])[:200]}{when}")
        if stage_progress.get("next"):
            lines.append(f"               next: {str(stage_progress['next'])[:200]}")
    lines.append("")
    if open_items:
        lines.append(f"  Open here    {open_items[0]}")
        lines.extend(f"               {item}" for item in open_items[1:])
    else:
        lines.append("  Open here    —")
    lines.append("")
    if isinstance(top_cluster, dict) and top_cluster.get("cluster_id"):
        count = top_cluster.get("member_count", 0)
        noun = "goal" if count == 1 else "goals"
        lines.append(f"  Top goal     {top_cluster.get('title', '?')} ({count} {noun})")
        sitting = top_cluster.get("nearest_sitting") or ""
        when = ""
        if isinstance(sitting, str) and sitting:
            try:
                days = (_dt.date.fromisoformat(sitting) - today).days
                when = f" — {sitting} ({days} days)" if days >= 0 else f" — {sitting}"
            except ValueError:
                when = f" — {sitting}"
        lines.append(f"               tier {top_cluster.get('tier', '?')}{when}; "
                     "seeing it files nothing")
        lines.append("               decide per goal id: "
                     "los goal <id> --reject|--defer|--close")
        lines.append("")
    if isinstance(requirement, dict):
        lines.append(f"  Next         los observe {requirement['id']} --activity <what-you-did> "
                     "--result <correct|incorrect|partial|abandoned>")
    else:
        # Bare stage-note refuses (canonical writes need a GatewayEnvelopeV2),
        # so name the seal-and-submit path instead.
        lines.append("  Next         .venv/bin/python tools/seal_envelope.py --capability stage.note.write "
                     "--payload {unit_id, stage_id, text} --guards auto, then")
        lines.append("               los capability stage.note.write --payload-file ENVELOPE.json")
    upcoming = [(row.get("start_date", ""), row) for row in sittings
                if isinstance(row.get("start_date"), str)
                and row["start_date"] >= today.isoformat()]
    if upcoming:
        start, row = sorted(upcoming)[0]
        try:
            days = (_dt.date.fromisoformat(start) - today).days
            when = f"{start} ({days} days)"
        except ValueError:
            when = start
        lines.append(f"  Exam         {row.get('label', '')} — {when}")
    else:
        lines.append("  Exam         no upcoming sitting recorded")
    return "\n".join(lines)


def _dumps_resume(payload) -> str:
    """The exact resume encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def _human_resume(payload, view) -> str:
    """The exact resume screen, rendered from the handler's view (SPEC (bu) 1)."""
    if view["screen"] == "study-menu":
        registration = payload["registration_state"] or "unknown"
        lines = [f"Study options for {payload['exam_date']} ({payload['module_id']}; "
                 f"registration recorded as {registration}; "
                 "your resume pointer is unchanged)"]
        for row in payload["options"]:
            line = (f"  {row['unit_id']} · {row['current_stage']} "
                    f"\"{row['stage_title']}\" [{row['study_map_id']}]")
            if row["open"]:
                line += f" — open {row['open']['label']} at {row['open']['locator']}"
            lines.append(line)
        lines.append("Select one with `resume --study --unit UNIT_ID`.")
        return "\n".join(lines)
    study_option = payload.get("study_option")
    rendered = _render(SimpleNamespace(stage_id=view["stage_id"]),
                       view["requirement"], view["observations"],
                       view["open_items"], view["sittings"], view["titles"],
                       view["via_detail"], view["stale_count"],
                       view["top_cluster"], view["aims"], view["stage_note"],
                       view["stage_progress"], view["untargeted_section"],
                       today=_dt.date.fromisoformat(view["today_iso"]))
    if study_option is not None:
        lines = [f"Study suggestion for {study_option['exam_date']} "
                 f"(registration recorded as {study_option['registration_state'] or 'unknown'}; "
                 "your resume pointer is unchanged)"]
        resource = study_option["open"]
        if resource:
            lines.append(f"  Open {resource['label']} at {resource['locator']}")
        rendered = "\n".join([*lines, "", rendered])
    return rendered


@register("cli.resume", kind="tool", human=_human_resume)
def resume(ctx: OpContext, req: dict) -> Result:
    """Compile and print the return-to-study screen. Read-only."""
    root = ctx.root
    repo = ctx.repo()
    study_option = None
    if req.get("study"):
        resolved, study_option = _study_option(repo, unit_id=req.get("unit"))
        if resolved is None:
            if isinstance(study_option, dict):
                return Result(study_option, json_dumps=_dumps_resume,
                              human_view={"screen": "study-menu"})
            raise WriteRefused(
                study_option,
                site=f"{ctx.operation}.no-study-option",
                gateway_message=f"los: {study_option}",
                exit_code=2,
            )
    elif req.get("unit"):
        raise WriteRefused(
            "resume --unit needs --study",
            site=f"{ctx.operation}.unit-without-study",
            gateway_message="los: resume --unit needs --study",
            exit_code=2,
        )
    else:
        resolved = _resolve_stage(repo)
    if resolved[0] is None:
        raise WriteRefused(
            resolved[1],
            site=f"{ctx.operation}.no-resumable-stage",
            gateway_message=f"los: {resolved[1]}",
            exit_code=2,
        )
    via, module_id, unit_id, study_map_id, stage_id = resolved
    pointer = repo.resume_pointer if isinstance(repo.resume_pointer, dict) else {}
    via_detail = f"via {via}"
    if via == "resume pointer" and isinstance(pointer.get("updated"), str):
        via_detail += f"; pointer updated {pointer['updated']}{_ago(pointer['updated'])}"
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError:
        requirements = []
    requirement = next(
        (item for item in requirements
         if item.get("source_stage", {}).get("unit_id") == unit_id
         and item.get("source_stage", {}).get("stage_id") == stage_id),
        None)
    try:
        observations = [obs for obs in _live_observations(
            read_observations(repo, requirements))
            if requirement is not None and obs.get("requirement") == requirement["id"]]
    except RuntimeInputError:
        observations = []
    try:
        untargeted = stage_results_for(
            read_stage_results(repo), unit_id, stage_id)
    except RuntimeInputError:
        untargeted = []
    stale_here = [row for row in stale_observations(requirements, observations)
                  if requirement is not None and row.requirement == requirement["id"]]
    study_map = repo.study_maps.get(study_map_id)
    stages = (study_map.data or {}).get("stages", []) if study_map else []
    stage = next((s for s in stages
                  if isinstance(s, dict) and s.get("id") == stage_id), {})
    unit = repo.units.get(unit_id)
    module = repo.modules.get(module_id, {})
    titles = {
        "module": str(module.get("title", module_id)) if isinstance(module, dict) else module_id,
        "unit": str((unit.data or {}).get("title", unit_id)) if unit else unit_id,
        "stage": str(stage.get("title", stage_id)) if isinstance(stage, dict) else stage_id,
    }
    open_items = _open_items(
        root, repo, unit_id, stage_id,
        requirement["id"] if isinstance(requirement, dict) else None)
    sittings = [
        {"label": row.get("label"), "start_date": row.get("start_date"),
         "end_date": row.get("end_date"),
         "registration_state": row.get("registration_state")}
        for row in _academic_deadlines(repo)
        if isinstance(row, dict) and row.get("kind") == "exam"
        and row.get("module_id") == module_id
    ]
    obs_rows = [
        {"id": obs.get("id"), "result": obs.get("result"),
         "timestamp": obs.get("timestamp"),
         "conditions": obs.get("conditions", []),
         "context": obs.get("context", "")}
        for obs in observations
    ]
    top_cluster = _top_cluster(root)
    stage_note = _stage_note_facts(root, stage)
    progress = stage.get("progress") if isinstance(stage, dict) else None
    stage_progress = progress if isinstance(progress, dict) else None
    untargeted_rows = [
        {"id": row.get("id"), "activity": row.get("activity"),
         "result": row.get("result"), "timestamp": row.get("timestamp"),
         "conditions": row.get("conditions", []),
         "assistance": row.get("assistance", ""),
         "note": row.get("note", "")}
        for row in untargeted[:MAX_STAGE_RESULTS]
    ]
    untargeted_section = (
        {"results": untargeted_rows, "total": len(untargeted),
         "credit": "none"}
        if untargeted else None
    )
    try:
        dossier = build_resume_dossier(
            unit_id=unit_id, module_id=module_id, stage_id=stage_id,
            study_map_id=study_map_id, via=via, requirement=requirement,
            observations=obs_rows, open_items=open_items, sittings=sittings,
            titles=titles, top_cluster=top_cluster, stage_note=stage_note,
            stage_progress=stage_progress,
            stage_results=untargeted_section)
    except ResumeDossierError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.dossier-build-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    output = {"key": dossier.key, "via": via,
              "content": {section: value for section, value in dossier.content}}
    if study_option is not None:
        output["study_option"] = study_option
    aims = _recorded_aims(repo, module_id, unit_id)
    view = {
        "screen": "main",
        "today_iso": observed_today().isoformat(),
        "stage_id": dossier.stage_id,
        "requirement": requirement,
        "observations": observations,
        "open_items": list(open_items),
        "sittings": sittings,
        "titles": titles,
        "via_detail": via_detail,
        "stale_count": len(stale_here),
        "top_cluster": top_cluster,
        "aims": [list(item) for item in aims],
        "stage_note": stage_note,
        "stage_progress": stage_progress,
        "untargeted_section": untargeted_section,
    }
    return Result(output, json_dumps=_dumps_resume, human_view=view)


def _dumps_runtime_session(payload) -> str:
    """The exact runtime-session encoder: sorted, unescaped, no layout."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


@register("cli.runtime-session", kind="porcelain")
@register("runtime.session", kind="porcelain")
def runtime_session(ctx: OpContext, req: dict) -> Result:
    """Propose (or repair) one runtime study session. Read-only."""
    root = ctx.root
    try:
        before = ctx.snapshot_id()
        if req["expected_snapshot"] is not None and req["expected_snapshot"] != before:
            raise StaleSnapshot(
                "snapshot changed; reload before proposing a session",
                site=f"{ctx.operation}.stale-snapshot",
            )
        context = json.loads(req["context_json"])
        repo = ctx.repo()
        requirement = next((r for r in collect_requirements(repo) if r["id"] == req["requirement"]), None)
        if requirement is None:
            raise RuntimeInputError(f"unknown requirement: {req['requirement']}")
        interpretation = _collect_and_interpret(repo)[requirement["id"]]
        if bool(req["previous_json"]) != bool(req["event"]):
            raise RuntimeInputError("bounded repair requires both --previous-json and --event")
        if req["previous_json"]:
            previous_packet = json.loads(req["previous_json"])
            validate_contract(root, "runtime-session.schema.json", previous_packet)
            if previous_packet.get("snapshot_id") != before:
                raise StaleSnapshot(
                    "previous proposal belongs to a different snapshot; propose a fresh session",
                    site=f"{ctx.operation}.previous-stale",
                )
            session = replan_session(repo, previous_packet, requirement,
                                     interpretation, context, req["event"], before)
        else:
            session = compile_session(repo, requirement, interpretation, context)
        result = {"contract": "runtime-session-v1", "schema_version": 1,
                  "snapshot_id": before, "session": session}
        validate_contract(root, "runtime-session.schema.json", result)
        if before != _snapshot(ctx.root):
            raise StaleSnapshot(
                "snapshot changed during runtime read; retry",
                site=f"{ctx.operation}.mid-read-stale",
            )
        return Result(result, json_dumps=_dumps_runtime_session)
    except (RuntimeInputError, ContractValidationError,
            json.JSONDecodeError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-input",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
