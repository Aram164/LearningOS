"""`los resume`: the one-screen return to study.

Read-only. Resolves the stage to resume — the resume pointer when it is
valid, else the requirement of the last recorded result (the ledger Finding
0 fills), else the most recently touched study map — then compiles the
screen from the five readers that already exist: the stage, its
requirement, live observations, open items, and the exam sittings.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

from learning_os.genout.modules_view import _academic_deadlines
from learning_os.genout.resume_dossier import (
    ResumeDossierError,
    build_resume_dossier,
    store_resume_dossier,
)
from learning_os.githistory import GitHistoryError
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from learning_os.loader import load_repo
from learning_os.semantics.goals import stale_observations

from .support import _root


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

    The pointer wins when it resolves; a stale or missing pointer falls
    through to the last recorded result, then to the most recently
    touched study map. Every fallback is labeled in the output.
    """
    pointer = repo.resume_pointer if isinstance(repo.resume_pointer, dict) else {}
    stale = bool(pointer)
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
    # Newest touch wins — unless it points at a stage with no requirement,
    # in which case the screen would open on "none authored". A stage you
    # can record evidence against demos the feature and resumes the work.
    required = set()
    for req in requirements:
        if not isinstance(req, dict):
            continue
        source = req.get("source_stage", {})
        if isinstance(source, dict):
            required.add((source.get("unit_id"), source.get("stage_id")))
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
        resolved = (label, study_map.module_id, study_map.unit_id,
                    study_map.id, str(stage["id"]))
        if fallback is None:
            fallback = resolved
        if (study_map.unit_id, stage.get("id")) in required:
            return resolved
    if fallback is not None:
        return fallback
    return (None, "no resumable stage: the resume pointer is missing or stale, "
                  "no results were ever recorded, and no study map was ever "
                  "touched — start any stage to set one")


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


def cmd_resume(args) -> int:
    """Compile and print the return-to-study screen. Read-only."""
    root = _root(args)
    repo = load_repo(root)
    resolved = _resolve_stage(repo)
    if resolved[0] is None:
        print(f"los: {resolved[1]}", file=sys.stderr)
        return 2
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
        (req for req in requirements
         if req.get("source_stage", {}).get("unit_id") == unit_id
         and req.get("source_stage", {}).get("stage_id") == stage_id),
        None)
    try:
        observations = [obs for obs in _live_observations(
            read_observations(repo, requirements))
            if requirement is not None and obs.get("requirement") == requirement["id"]]
    except RuntimeInputError:
        observations = []
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
    try:
        dossier = build_resume_dossier(
            unit_id=unit_id, module_id=module_id, stage_id=stage_id,
            study_map_id=study_map_id, via=via, requirement=requirement,
            observations=obs_rows, open_items=open_items, sittings=sittings,
            titles=titles)
    except ResumeDossierError as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    try:
        store_resume_dossier(root, dossier)
    except ResumeDossierError:
        pass  # the screen is the deliverable; the cache is best-effort
    if args.json:
        print(json.dumps(
            {"key": dossier.key, "via": via,
             "content": {section: value for section, value in dossier.content}},
            indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    print(_render(dossier, requirement, observations, open_items, sittings,
                  titles, via_detail, len(stale_here)))
    return 0


def _ago(day: str) -> str:
    """Render-time relative time; never hashed, never trusted to parse."""
    try:
        delta = (_dt.date.today() - _dt.date.fromisoformat(day)).days
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
            titles, via_detail: str, stale_count: int = 0) -> str:
    today = _dt.date.today()
    lines = [f"{titles['module']} · {titles['unit']} · {dossier.stage_id}",
             f"  ({via_detail})", ""]
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
