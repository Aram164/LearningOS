"""Read-only intelligence commands. Nothing here writes: the scan reads
the current world, proposes candidate investigations on stdout, and
exits. Filing anything into the proposal queue is the operator's job."""

from __future__ import annotations

import datetime as _dt
import json
import sys

from learning_os.genout.modules_view import _academic_deadlines
from learning_os.githistory import GitHistoryError
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from learning_os.loader import load_repo
from learning_os.semantics.goals import (
    CandidateGoal,
    RankedCluster,
    cluster_goals,
    rank_clusters,
)
from learning_os.semantics.scan import _read_goal_ledger, intelligence_scan

from .support import _root


def _route_modules(repo) -> dict[str, str]:
    """Route id to owning module id, from the loaded source maps."""
    owners: dict[str, str] = {}
    for module_id, smap in (getattr(repo, "module_source_maps", {}) or {}).items():
        if not isinstance(smap, dict):
            continue
        sources = smap.get("sources")
        if not isinstance(sources, list):
            continue
        for src in sources:
            if not isinstance(src, dict):
                continue
            routes = src.get("unit_routes")
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, dict):
                    continue
                rid = route.get("id")
                if isinstance(rid, str) and rid and rid not in owners:
                    owners[rid] = module_id
    return owners


def _requirement_modules(repo) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Requirement id to owning modules, plus observation id to requirement.

    Best-effort: an unreadable runtime resolves nothing rather than
    refusing the whole scan.
    """
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError:
        return {}, {}
    units = getattr(repo, "units", {}) or {}
    req_modules: dict[str, set[str]] = {}
    for req in requirements:
        if not isinstance(req, dict):
            continue
        source = req.get("source_stage", {})
        unit = units.get(source.get("unit_id", "")) if isinstance(source, dict) else None
        module_id = getattr(unit, "module_id", None)
        if isinstance(req.get("id"), str) and isinstance(module_id, str) and module_id:
            req_modules[req["id"]] = {module_id}
    try:
        observations = read_observations(repo, requirements)
    except RuntimeInputError:
        return req_modules, {}
    obs_requirements = {
        obs["id"]: obs.get("requirement") for obs in observations
        if isinstance(obs, dict) and isinstance(obs.get("id"), str)}
    return req_modules, obs_requirements


def _cluster_modules(repo, route_modules: dict[str, str],
                     req_modules: dict[str, set[str]],
                     obs_requirements: dict[str, str],
                     cluster) -> set[str]:
    """Modules behind one cluster, resolved from member goal ids.

    Study-map obligations name their unit; covering-routes goals name
    their route; lineage and changed-source goals name claims, and a
    ``covers:`` claim resolves through its route; superseded-evidence
    goals name observations, resolved through their requirement.
    Anything unresolvable stays unknown — the ranker treats that as
    tier 4, never urgent.
    """
    modules: set[str] = set()
    units = getattr(repo, "units", {}) or {}
    for goal_id in cluster.member_ids:
        kind, _, rest = goal_id.partition(":")
        if kind == "study-map-obligation":
            unit = units.get(rest)
            module_id = getattr(unit, "module_id", None)
            if isinstance(module_id, str) and module_id:
                modules.add(module_id)
            continue
        if kind == "evidence-superseded":
            req_id = obs_requirements.get(rest)
            modules.update(req_modules.get(req_id, ()))
            continue
        route = rest if kind == "covering-routes-stale" else None
        if route is None and rest.startswith("covers:"):
            route = rest[len("covers:"):]
        if route and route in route_modules:
            modules.add(route_modules[route])
    return modules


def ranked_scan(root, *, days: int = 30
                ) -> tuple[tuple[CandidateGoal, ...], tuple[RankedCluster, ...], int]:
    """Goals clustered by shared cause, ordered by exam proximity.

    Returns ``(goals, ranked, decided_hidden)``. Orchestration over the
    existing detectors plus the goal ledger; still read-only.
    """
    goals = intelligence_scan(root, days=days)
    clusters = cluster_goals(goals)
    repo = load_repo(root)
    deadlines = _academic_deadlines(repo)
    module_status = {
        module_id: (module.get("status") if isinstance(module, dict) else None)
        for module_id, module in (getattr(repo, "modules", {}) or {}).items()
    }
    route_modules = _route_modules(repo)
    req_modules, obs_requirements = _requirement_modules(repo)
    mapping = {
        cluster.cluster_id: _cluster_modules(
            repo, route_modules, req_modules, obs_requirements, cluster)
        for cluster in clusters
    }
    ranked = rank_clusters(
        clusters, today=_dt.date.today(), deadlines=deadlines,
        module_status=module_status, cluster_modules=mapping)
    return goals, ranked, len(_read_goal_ledger(root))


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


def cmd_intelligence_scan(args) -> int:
    """Run one observation loop: observe, interpret, propose."""
    if args.days < 0:
        print("intelligence scan: --days is never negative")
        return 2
    root = _root(args)
    try:
        goals, ranked, hidden = ranked_scan(root, days=args.days)
    except GitHistoryError as exc:
        print(f"intelligence scan: cannot read Git history: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"intelligence scan: cannot rank the queue: {exc}", file=sys.stderr)
        return 2
    if args.json:
        from learning_os.semantics.goals import goal_to_dict

        print(json.dumps(
            {"goals": [goal_to_dict(goal) for goal in goals]},
            indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if not goals:
        print("intelligence scan: no candidates — "
              "nothing moved that the detectors cover")
        return 0
    print(f"intelligence scan: {len(goals)} candidate(s) in "
          f"{len(ranked)} group(s) — filing is yours:")
    attention = [row for row in ranked if row.tier <= 2]
    upcoming = [row.days_until for row in attention
                if row.days_until is not None]
    if upcoming:
        urgent_goals = sum(len(row.cluster.member_ids) for row in attention)
        print(f"{len(attention)} group(s), {urgent_goals} goal(s), bear on a "
              f"sitting in the next {min(upcoming)}d.")
    by_id = {goal.goal_id: goal for goal in goals}
    for number, row in enumerate(ranked, start=1):
        cluster = row.cluster
        print(f"{number}. [{_tier_label(row)}] {cluster.title}")
        members = list(cluster.member_ids)
        if len(members) == 1 and members[0] in by_id:
            print(f"   evidence: {', '.join(by_id[members[0]].evidence)}")
        else:
            shown = ", ".join(members[:6])
            if len(members) > 6:
                shown += f" … +{len(members) - 6} more"
            print(f"   goals ({len(members)}): {shown}")
    print("Decide per goal id: los goal <id> --reject|--defer|--close")
    if hidden:
        print(f"({hidden} decided goal(s) stay hidden — see `los goal`)")
    return 0
