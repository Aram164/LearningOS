"""Reads-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from learning_os import __version__
from learning_os.app.context import OpContext
from learning_os.app.encoders import dumps_compact
from learning_os.app.handlers._shared import inbox_search_rows as _inbox_search_rows
from learning_os.app.handlers._shared import window_values as _window_values
from learning_os.app.projection import fresh_manifest as _fresh_manifest
from learning_os.app.proposal import Result
from learning_os.app.ranking import ranked_scan
from learning_os.app.registry import register
from learning_os.app.validation_service import status_issues
from learning_os.derive.learning_runtime import RuntimeInputError, collect_requirements
from learning_os.derive.projection import adoption_counts, exam_spine
from learning_os.derive.projection.atlas import ATLAS_DOMAINS
from learning_os.derive.projection.learner_interpreter import (
    collect_and_interpret as _collect_and_interpret,
)
from learning_os.derive.projection.projection.atlas import STAGE_CONCEPT
from learning_os.derive.projection.session_compiler import compile_session, replan_session
from learning_os.derive.semantics.goals import RankedCluster, goal_to_dict
from learning_os.derive.semantics.predicates import PREDICATES, evaluate
from learning_os.derive.semantics.recipes import RecipeError, recipes_for
from learning_os.derive.semantics.scan import observe_goal_ledger
from learning_os.derive.semantics.session_counts import FeedError, feed_scan_kwargs
from learning_os.derive.semantics.source_use import evidence_label as _evidence_label
from learning_os.derive.semantics.source_use import use_evidence as _use_evidence
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused, unreadable_refusal
from learning_os.domain.suggest import expansion, not_found, with_suggestions
from learning_os.store.contracts.capability_catalog import load_capability_catalog
from learning_os.store.contracts.json_schema import ContractValidationError, validate_contract
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.session.githistory import GitHistoryError
from learning_os.store.session_ledger import SESSION_ID_ENV
from learning_os.store.session_ledger import resolve_session_identity as _resolve_session_identity
from learning_os.store.validation_cache import observe_pins


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

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            prefixed=True,
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
            prefixed=True,
            exit_code=2,
        )
    if req.get("offset"):
        raise WriteRefused(
            "bootstrap --brief is a single page; "
            "page the collections with --compact instead",
            site=f"{ctx.operation}.brief-with-offset",
            prefixed=True,
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

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


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
    return Result(payload)


@register("program.list", kind="query")
def program_list(ctx: OpContext, req: dict) -> Result:
    """List programs as discovery rows."""
    manifest = _fresh_manifest(ctx.root)
    return Result(manifest.get("programs", []))


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


@register("status.read", kind="tool", human=_human_status)
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
            prefixed=True,
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
    return Result(payload,
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


@register("semantic.query", kind="tool")
def semantic(ctx: OpContext, req: dict) -> Result:
    """Evaluate one predicate, list the registry, or serve a recipe."""
    if req.get("recipe"):
        try:
            rows = recipes_for(req["recipe"])
        except RecipeError as exc:
            raise WriteRefused(
                str(exc),
                site=f"{ctx.operation}.bad-recipe",
                prefixed=True,
                exit_code=2,
            ) from exc
        return Result({"class": req["recipe"], "recipes": rows})
    if req.get("list"):
        return Result(
            [{"name": name,
              "inputs": list(PREDICATES[name].authoritative_inputs),
              "authority": PREDICATES[name].authority,
              "description": PREDICATES[name].description}
             for name in sorted(PREDICATES)])
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
                prefixed=True,
                exit_code=2,
            )
        inputs[key.strip()] = _coerce(value)
    try:
        verdict = evaluate(name, **inputs)
    except TypeError as exc:
        raise WriteRefused(
            f"malformed inputs for {name}: {exc}",
            site=f"{ctx.operation}.malformed-inputs",
            prefixed=True,
            exit_code=2,
        ) from exc
    return Result({"predicate": name, "verdict": verdict,
                   "inputs": inputs})


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
    quiet_ids = {goal.goal_id for goal in goals if goal.quiet}
    ranked = [row for row in ranked if not set(row.cluster.member_ids).issubset(quiet_ids)]
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


@register("intelligence.scan", kind="tool", human=_human_intelligence_scan)
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
        ledger = observe_goal_ledger(root)
        goals, ranked, hidden = ranked_scan(root, days=req["days"], feed=feed, goal_ledger=ledger)
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
        payload["detectors"] = {key: dict(row) for key, row in ledger.metrics.items()}
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
    return Result(payload,  human_view=view)


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


def _human_capabilities(payload, view) -> str:
    """The exact capabilities screen (SPEC (bu) 1).

    The name/compact branches print JSON even without ``--json``; the
    human renderer replays those exact bytes, selected by the view's
    branch. The default branch renders the five-line screen.
    """
    if view["branch"] in ("name", "compact"):
        return dumps_compact(payload)
    return "\n".join(
        [f"LearningOS operator contract v{payload['contract_version']}",
         f"  gateway: {payload['gateway']}",
         f"  projection: {payload['projection']}",
         "  transactional commands: " + ", ".join(sorted(payload["commands"])),
         "  every successful canonical write has one receipt"])


@register("capabilities.read", kind="tool", human=_human_capabilities)
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
            prefixed=True,
            exit_code=2,
        )
    if name:
        section = next((key for key in ("queries", "commands") if name in payload[key]), None)
        if section is None:
            raise WriteRefused(
                f"unknown or non-public capability: {name}",
                site=f"{ctx.operation}.unknown-capability",
                prefixed=True,
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
                    prefixed=True,
                    exit_code=2,
                ) from exc
            payload["payload_schema_path"] = relative
            payload["payload_schema"] = schema
        return Result(payload,
                      human_view={"branch": "name"})
    if compact:
        for key in ("queries", "commands"):
            payload[key] = sorted(payload[key])
        payload["detail"] = "capabilities NAME --json"
        return Result(payload,
                      human_view={"branch": "compact"})
    return Result(payload,
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


@register("related.read", kind="query")
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
    return Result(out)


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
        return Result(result)
    except (RuntimeInputError, ContractValidationError,
            json.JSONDecodeError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.bad-input",
            prefixed=True,
            exit_code=2,
        ) from exc


_UNIT_SUMMARY_FIELDS = ("id", "title", "status", "module_id", "component_id",
                        "order", "current_study_map", "needs_study_map")
_COMPACT_LIMIT_DEFAULT = 20


def _unit_summary(row):
    """The eight discovery fields, with explicit nulls kept and absent dropped."""
    return {key: row[key] for key in _UNIT_SUMMARY_FIELDS if key in row}


#: The unit ``status`` enum from ``system/schema/unit.schema.json``.
#: A test pins this copy against the schema, so the two cannot drift.
#: An unknown filter value refuses with exit 2 instead of answering an
#: empty result, so ``total: 0`` always means "valid filter, no matches".
UNIT_STATUSES = frozenset({
    "needs-map", "not-started", "ready", "active", "paused",
    "ready-to-shelve", "complete",
})


def _component_ids(manifest) -> set[str]:
    """Every known component: declared on a module or named by a unit."""
    ids = set()
    for module in manifest.get("modules", []) or []:
        if not isinstance(module, dict):
            continue
        for component in module.get("components", []) or []:
            if isinstance(component, dict) and component.get("id"):
                ids.add(component["id"])
            elif isinstance(component, str) and component:
                ids.add(component)
    for row in manifest.get("units", []) or []:
        if isinstance(row, dict) and row.get("component_id"):
            ids.add(row["component_id"])
    return ids


def _filtered_units(manifest, req, operation):
    rows = manifest.get("units", [])
    if req.get("module_id"):
        modules = [row.get("id") for row in manifest.get("modules", []) or []
                   if isinstance(row, dict) and row.get("id")]
        if req["module_id"] not in modules:
            message = not_found("module", req["module_id"], modules)
            raise NotFound(
                "module", req["module_id"], modules,
                site=f"{operation}.unknown-module",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
        rows = [row for row in rows if row.get("module_id") == req["module_id"]]
    if req.get("component_id"):
        known = _component_ids(manifest)
        if req["component_id"] not in known:
            message = not_found("component", req["component_id"], known)
            raise NotFound(
                "component", req["component_id"], known,
                site=f"{operation}.unknown-component",
                gateway_message=f"los: {message}",
                exit_code=2,
            )
        rows = [row for row in rows if row.get("component_id") == req["component_id"]]
    if req.get("status"):
        if req["status"] not in UNIT_STATUSES:
            message = with_suggestions(
                f"unknown status: {req['status']}", req["status"], UNIT_STATUSES)
            raise WriteRefused(
                message,
                site=f"{operation}.unknown-status",
                prefixed=True,
                exit_code=2,
            )
        rows = [row for row in rows if row.get("status") == req["status"]]
    return rows


def _unit_list_compact(ctx: OpContext, req: dict) -> Result:
    root = ctx.root
    try:
        try:
            offset, limit = _window_values(
                req.get("offset"), req.get("limit"),
                req.get("expected_snapshot"), 50)
        except WriteRefused as exc:
            exc.site = f"{ctx.operation}.bad-window"
            exc.gateway_message = f"los: {exc}"
            exc.exit_code = 2
            raise
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        manifest = _fresh_manifest(root, snapshot_id=snapshot)
        rows = sorted(_filtered_units(manifest, req, ctx.operation),
                      key=lambda row: row["id"])
        total = len(rows)
        items = [_unit_summary(row) for row in rows[offset:offset + limit]]
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "unit-list-summary",
             "filters": {key: value for key, value in (
                 ("module_id", req.get("module_id")),
                 ("component_id", req.get("component_id")),
                 ("status", req.get("status"))) if value is not None},
             "items": items, "total": total,
             "next_offset": offset + limit if offset + limit < total else None,
             "detail": "inspect UNIT_ID"})
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


@register("unit.list", kind="query")
def unit_list(ctx: OpContext, req: dict) -> Result:
    """List units, optionally filtered; compact serves the summary page."""
    root = ctx.root
    if req.get("compact"):
        return _unit_list_compact(ctx, req)
    if (req.get("offset") or req.get("limit") != _COMPACT_LIMIT_DEFAULT
            or req.get("expected_snapshot") is not None):
        raise WriteRefused(
            "--offset/--limit/--expected-snapshot need --compact",
            site=f"{ctx.operation}.window-needs-compact",
            prefixed=True,
            exit_code=2,
        )
    manifest = _fresh_manifest(root)
    return Result(_filtered_units(manifest, req, ctx.operation))


@register("module.list", kind="query")
def module_list(ctx: OpContext, req: dict) -> Result:
    """List modules with optional program/status filters."""
    root = ctx.root
    manifest = _fresh_manifest(root)
    rows = manifest.get("modules", [])
    if req.get("program_id"):
        rows = [row for row in rows if row.get("area_id") == req["program_id"]]
    if req.get("status"):
        rows = [row for row in rows if row.get("status") == req["status"]]
    return Result(rows)
