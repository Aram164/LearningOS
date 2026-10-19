"""The ranked intelligence scan: goals clustered by shared cause, ordered by exam proximity."""

from __future__ import annotations

from collections.abc import Mapping

from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from learning_os.derive.projection.modules_view import academic_deadlines as _academic_deadlines
from learning_os.derive.semantics.goals import (
    CandidateGoal,
    RankedCluster,
    cluster_goals,
    rank_clusters,
)
from learning_os.derive.semantics.scan import (
    GoalLedgerObservation,
    intelligence_scan,
    observe_goal_ledger,
)
from learning_os.store import observations
from learning_os.store.loader import load_repo


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
            route = rest[len("covers:"):].split("@", 1)[0]
        if route and route in route_modules:
            modules.add(route_modules[route])
    return modules


def ranked_scan(root, *, days: int = 30,
                feed: Mapping | None = None,
                goal_ledger: GoalLedgerObservation | None = None,
                ) -> tuple[tuple[CandidateGoal, ...], tuple[RankedCluster, ...], int]:
    """Goals clustered by shared cause, ordered by exam proximity.

    Returns ``(goals, ranked, decided_hidden)``. Orchestration over the
    existing detectors plus the goal ledger; still read-only. ``feed``
    is a caller-supplied session-count mapping; None behaves as before.
    """
    ledger = goal_ledger if goal_ledger is not None else observe_goal_ledger(root)
    goals = intelligence_scan(root, days=days, feed=feed, goal_ledger=ledger)
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
        clusters, today=observations.today(), deadlines=deadlines,
        module_status=module_status, cluster_modules=mapping)
    return goals, ranked, len(ledger.known_ids)
