"""The resume view and its dossier."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result
from learning_os.app.registry import OperationEffects, register
from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    stage_results_for,
    timestamp_sort_key,
)
from learning_os.derive.projection.common import excerpt as _excerpt
from learning_os.derive.projection.common import first_para as _first_para
from learning_os.derive.projection.modules_view import academic_deadlines as _academic_deadlines
from learning_os.derive.projection.resume_dossier import ResumeDossierError, build_resume_dossier
from learning_os.derive.semantics.claim_status import claims_summary, observe_claims_with_audits
from learning_os.derive.semantics.dossiers import (
    DossierError,
    build_dossier,
    cache_path,
    is_fresh,
    load_dossier,
    store_dossier,
)
from learning_os.derive.semantics.goals import stale_observations
from learning_os.derive.semantics.predicates import CONTRACT_VERSION as SEMANTIC_CONTRACT_VERSION
from learning_os.domain.curriculum.lifecycle import module_lifecycle
from learning_os.domain.curriculum.stages import (
    entry_resource,
    resolve_resume_target,
    study_candidate_stage,
)
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.material_refs import unit_routes
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.layout import PathBoundaryError, resolved_inside
from learning_os.store.materials.resolution import (
    material_uri_authority,
    resolve_material_target,
    single_file_material,
)
from learning_os.store.observations import today as observed_today
from learning_os.store.session.githistory import GitHistoryError, last_commit_date

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


@register("dossier.read", kind="porcelain", effects=OperationEffects.DERIVED_WRITE)
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
                prefixed=True,
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
                prefixed=True,
                exit_code=2,
            )
        source_map = repo.module_source_maps[unit.module_id]
        routes = unit_routes(source_map, unit.module_id, unit.id)
        knowledge_map = unit.data.get("knowledge_map") or {}
        if not isinstance(knowledge_map, dict):
            raise WriteRefused(
                f"unit {unit.id} knowledge map is not a mapping",
                site=f"{ctx.operation}.bad-knowledge-map",
                prefixed=True,
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
                prefixed=True,
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
        try:
            payload["claims"] = claims_summary(observe_claims_with_audits(root, repo=repo, route_ids=[r["id"] for r in routes]))
        except ValueError as exc:
            raise WriteRefused(f"cannot read claim status: {exc}") from exc
        if req.get("json"):
            payload["content"] = {
                section: value for section, value in fresh.content}
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},

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


def _live_observations(observations: list[dict]) -> list[dict]:
    """Non-superseded observations, newest first. Unparseable timestamps
    sort as oldest rather than crashing the screen."""
    superseded = {obs.get("supersedes") for obs in observations
                  if isinstance(obs, dict) and obs.get("supersedes")}
    live = [obs for obs in observations
            if isinstance(obs, dict) and obs.get("id") not in superseded]

    return sorted(
        live,
        key=lambda obs: timestamp_sort_key(obs, allow_unparseable=True),
        reverse=True,
    )


def _historical_destination(repo):
    """The recovery trail's destination, or None — history, never intent.

    Last recorded result first, then the most recently touched study map.
    Callers label both as history: neither label ever reads as an
    available study choice.
    """
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
        return ("last recorded result (resume pointer missing or stale)",
                unit.module_id, unit.id, study_map.id,
                str(source.get("stage_id") or ""))
    try:
        from learning_os.store.session.githistory import last_commit_timestamps

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
        return ("recently touched stage (resume pointer missing or stale)",
                study_map.module_id, study_map.unit_id,
                study_map.id, str(stage["id"]))
    return None


def _resolve_stage(repo):
    """Return ``(via, module_id, unit_id, study_map_id, stage_id)`` — or
    ``(None, options-payload)`` when recovery has choices to offer.

    The pointer wins when it resolves. It is the learner's own last explicit
    study action — `stage.progress.update` writes it in the same transaction
    as the records that moved — so nothing derived may outrank it.

    What follows is *recovery* for a pointer that is missing or no longer
    resolves, and recovery asks instead of guessing: the open study choices
    come back as a menu built independently of any history, and the
    historical trail — last recorded result, then the most recently touched
    study map — rides along as clearly labeled context, opening as the
    destination only when nothing is selectable anywhere.

    The trail reads commit timestamps and evidence chronology, neither of
    which is a statement of intent: a result recorded against one subject
    says nothing about which subject he chose to sit down with next. Before
    2026-09-13 nothing wrote the pointer at all, so this fallback *was* the
    destination, and activating an Analysis stage still sent him back to
    Statistics (audit `workbench/audits/synthetic-learner-2026-09-12`, F05).
    """
    pointer = repo.resume_pointer if isinstance(repo.resume_pointer, dict) else {}
    # Reaching past this point at all is recovery, and the screen says so
    # either way. A pointer that exists but no longer resolves and a pointer
    # that was never written are the same thing to the learner — both mean
    # "nobody recorded where you were, so this is a guess" — and labelling
    # only the first left the second reading like an answer.
    if pointer:
        resolved_target = resolve_resume_target(repo)
        if resolved_target is not None:
            unit, study_map, stage = resolved_target
            return ("resume pointer", unit.module_id, unit.id,
                    study_map.id, str(stage["id"]))
    historical = _historical_destination(repo)
    rows = _study_rows(repo)
    if rows:
        recovery = {
            "pointer": "stale" if pointer else "missing",
            "historical": (dict(zip(("via", "module_id", "unit_id",
                                     "study_map_id", "stage_id"),
                                    historical, strict=True))
                           if historical is not None else None),
        }
        return (None, _study_menu(rows, recovery=recovery))
    if historical is not None:
        return historical
    return (None, "no resumable stage: the resume pointer is missing or "
                  "stale, nothing was ever recorded, and no study map is "
                  "open — see what exists with `unit-list --compact`, then "
                  "start any stage to set one")


#: At most this many options; the menu stays one screen.
MAX_STUDY_OPTIONS = 5

#: At most this many untargeted rows ride the resume screen; the section's
#: ``total`` stays exact past the bound. A copy of the bound plan's
#: material.py reads from commands.resume: one integer, two screens, each
#: area owns its copy so neither pair edits the other's files.
MAX_STAGE_RESULTS = 5


def _study_open(stage):
    """The first required-now resource locator, or None (today's shape)."""
    resource = entry_resource(stage, allow_untriaged=False)
    if (
        resource is None
        or not resource.get("label")
        or not resource.get("locator")
    ):
        return None
    return {
        "label": resource["label"],
        "locator": resource["locator"],
        "source_id": resource.get("source_id"),
    }


def _study_rows(repo):
    """Every open study choice in the repository, in the pinned order.

    One row per map the domain predicate calls a candidate
    (``study_candidate_stage``): active, paused, or ready, with a
    resolvable unit and a current stage that is neither complete,
    archived, nor skipped. The pool spans every module of any kind, but a
    settled administrative status (awaiting-grade, completed, dropped,
    archived) closes it: those modules keep their records as history.
    Enrollment rides each row as display-only lifecycle metadata and
    never filters it. Ordered by module ID, then each unit's position in the
    authored ``module.unit_order``, then the unit's numeric ``order``,
    then unit ID, then map ID — status is metadata, not a rank.
    Eligibility filters before anything counts: one valid row beside one
    ineligible map is one choice. ``learner_choice`` is False on every
    row, and nothing here writes the resume pointer — only an explicit
    stage action does.
    """
    rows: list[dict] = []
    lifecycles: dict[str, dict] = {}
    for study_map in repo.study_maps.values():
        found = study_candidate_stage(repo, study_map)
        if found is None:
            continue
        stage_id, stage = found
        map_status = (study_map.data or {}).get("status")
        module = repo.modules.get(study_map.module_id) or {}
        module_kind = str(module.get("kind", "academic") or "academic")
        if study_map.module_id not in lifecycles:
            lifecycles[study_map.module_id] = module_lifecycle(module, [
                str((unit.data or {}).get("status", ""))
                for unit in repo.units.values()
                if unit.module_id == study_map.module_id
            ])
        rows.append({
            "module_id": study_map.module_id,
            "module_title": str(module.get("title") or study_map.module_id),
            "unit_id": study_map.unit_id,
            "study_map_id": study_map.id,
            "current_stage": stage_id,
            "stage_title": stage.get("title") or stage_id,
            "open": _study_open(stage),
            "learner_choice": False,
            "map_status": map_status,
            "module_kind": module_kind,
            "administrative_status": lifecycles[
                study_map.module_id].get("administrative_status"),
        })

    def order(row):
        module = repo.modules.get(row["module_id"]) or {}
        authored = list(module.get("unit_order") or [])
        unit = repo.units.get(row["unit_id"])
        numeric = (unit.data or {}).get("order") if unit is not None else None
        try:
            position = authored.index(row["unit_id"])
        except ValueError:
            position = None
        if position is not None:
            intra = (0, position, 0, "")
        else:
            intra = (1, 0 if isinstance(numeric, int) else 1,
                     numeric if isinstance(numeric, int) else 0,
                     row["unit_id"])
        return (row["module_id"], *intra, row["study_map_id"])

    rows.sort(key=order)
    return rows


def _study_menu(rows, recovery=None):
    """The bounded options payload for whichever screen asks for choices.

    At most five rows; ``total`` is computed before the truncation so the
    one-screen bound never lies about how many choices exist. Every
    continuation names a command that exists: ``unit-list --compact``
    lists units, ``bootstrap --compact`` publishes every study map with
    status, current_stage, and is_study_candidate.
    """
    payload = {
        "contract": "resume-study-options",
        "options": rows[:MAX_STUDY_OPTIONS],
        "total": len(rows),
        "select_with": "resume --study --unit UNIT_ID",
        "continuation": ("list units with `unit-list --compact`; every "
                         "study map with status, current_stage, and "
                         "is_study_candidate rides `bootstrap --compact`"),
    }
    if recovery is not None:
        payload["recovery"] = recovery
    return payload


def _study_option(repo, unit_id=None):
    """One study suggestion, the options menu, or a refusal.

    No exam scoping anywhere: the builder pools every module's open maps.
    A single eligible row becomes a read-only suggestion — labeled as a
    suggestion, learner_choice false, and the resume pointer never moves
    on any path. Several rows come back as the bounded menu; none come
    back as a refusal that still names a command that exists.
    """
    rows = _study_rows(repo)
    if unit_id is not None:
        unit = repo.units.get(unit_id)
        if unit is None:
            refusal = with_suggestions(
                f"unit not found: {unit_id}", unit_id,
                [known_id for known_id, _ in repo.units.items()])
            return (None, f"{refusal}; list units with `unit-list --compact`")
        rows = [row for row in rows if row["unit_id"] == unit_id]
        if not rows:
            return (None, f"unit {unit_id} has no open study map with a "
                          f"current stage; inspect it with `inspect {unit_id}`")
        row = rows[0]
        return (("requested unit (study suggestion)", row["module_id"],
                 row["unit_id"], row["study_map_id"], row["current_stage"]),
                {"open": row["open"], "learner_choice": False})
    if len(rows) == 1:
        row = rows[0]
        return (("single open study map (suggestion)", row["module_id"],
                 row["unit_id"], row["study_map_id"], row["current_stage"]),
                {"open": row["open"], "learner_choice": False})
    if not rows:
        return (None, "no open study map: every study map is not-started or "
                      "closed to new work — see what exists with "
                      "`unit-list --compact` and `bootstrap --compact`")
    return (None, _study_menu(rows))


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
        from learning_os.app.ranking import ranked_scan

        goals, ranked, _ = ranked_scan(root, days=30)
        quiet_ids = {goal.goal_id for goal in goals if goal.quiet}
        ranked = [row for row in ranked if not set(row.cluster.member_ids).issubset(quiet_ids)]
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
        # display surface: drop markdown emphasis, then cut with the shared
        # marked sentence-boundary excerpt so the cut idiom exists once.
        return _excerpt(value.replace("**", "").replace("`", ""), limit)

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
        requirement_id = str(requirement.get("id", ""))
        concept = str(requirement.get("concept", ""))
        lines.append(f"  Requirement  {requirement_id}")
        lines.append(f"               concept: {concept}")
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


def _human_resume(payload, view) -> str:
    """The exact resume screen, rendered from the handler's view (SPEC (bu) 1)."""
    if view["screen"] in {"study-menu", "recovery-menu"}:
        if view["screen"] == "study-menu":
            count = payload["total"]
            noun = "choice" if count == 1 else "choices"
            lines = [f"Study options — {count} open {noun} across all modules "
                     "(your resume pointer is unchanged)"]
        else:
            state = payload["recovery"]["pointer"]
            lines = [f"No resume pointer to follow ({state}); recovery asks — "
                     "pick where to study (your resume pointer is unchanged)"]
        for row in payload["options"]:
            line = (f"  {row['module_id']} · {row['unit_id']} · "
                    f"{row['current_stage']} \"{row['stage_title']}\" "
                    f"[{row['study_map_id']}] ({row['map_status']} map)")
            if row["open"]:
                line += f" — open {row['open']['label']} at {row['open']['locator']}"
            lines.append(line)
        shown = len(payload["options"])
        if shown < payload["total"]:
            lines.append(f"  … {payload['total'] - shown} more past the one-screen "
                         "bound; `bootstrap --compact` lists every open map")
        historical = (payload.get("recovery") or {}).get("historical")
        if historical:
            lines.append(
                f"  Where you were (history, not a choice): {historical['via']}"
                f" — {historical['module_id']} · {historical['unit_id']}"
                f" · {historical['stage_id']}")
        lines.append("Select one with `resume --study --unit UNIT_ID`.")
        return "\n".join(lines)
    study_option = payload.get("study_option")
    rendered = _render(SimpleNamespace(stage_id=view["stage_id"]),
                       view["requirement"], view["observations"],
                       view["open_items"], view["sittings"], view["titles"],
                       view["via_detail"], view["stale_count"],
                       view["aims"], view["stage_note"],
                       view["stage_progress"], view["untargeted_section"],
                       today=_dt.date.fromisoformat(view["today_iso"]))
    if study_option is not None:
        lines = ["Study suggestion (your resume pointer is unchanged)"]
        resource = study_option["open"]
        if resource:
            lines.append(f"  Open {resource['label']} at {resource['locator']}")
        rendered = "\n".join([*lines, "", rendered])
    return rendered


@register("resume.read", kind="tool", human=_human_resume, effects=OperationEffects.READ)
def resume(ctx: OpContext, req: dict) -> Result:
    """Compile and print the return-to-study screen. Read-only."""
    root = ctx.root
    repo = ctx.repo()
    study_option = None
    if req.get("study"):
        resolved, study_option = _study_option(repo, unit_id=req.get("unit"))
        if resolved is None:
            if isinstance(study_option, dict):
                return Result(study_option,
                              human_view={"screen": "study-menu"})
            raise WriteRefused(
                study_option,
                site=f"{ctx.operation}.no-study-option",
                prefixed=True,
                exit_code=2,
            )
    elif req.get("unit"):
        raise WriteRefused(
            "resume --unit needs --study",
            site=f"{ctx.operation}.unit-without-study",
            prefixed=True,
            exit_code=2,
        )
    else:
        resolved = _resolve_stage(repo)
    if resolved[0] is None:
        if isinstance(resolved[1], dict):
            # Recovery with selectable choices: the menu is the answer, and
            # it must reach JSON clients in the payload — the human view is
            # presentation-only, so options living there alone would make
            # --json blind to the very choices the screen shows.
            return Result(resolved[1],
                          human_view={"screen": "recovery-menu"})
        raise WriteRefused(
            resolved[1],
            site=f"{ctx.operation}.no-resumable-stage",
            prefixed=True,
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
            prefixed=True,
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
        "aims": [list(item) for item in aims],
        "stage_note": stage_note,
        "stage_progress": stage_progress,
        "untargeted_section": untargeted_section,
    }
    return Result(output,  human_view=view)
