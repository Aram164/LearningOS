"""Intelligence scan: the read-only observation loop.

OBSERVE (this module) → INTERPRET (Phase-3 detectors) → PROPOSE (goals
on stdout) → Aram decides queue entry. No daemon, no background
process, no telemetry database, no automatic writes: every run reads
the current world and exits.

v1 observes what the repository already records and nothing else:
- changed canonical files in a recency window (git history, stateless —
  "moved in the last N days", never "since the last scan"), joined to
  knowledge nodes (changed unit files) and source definitions (changed
  source-map files), fed to the covering-routes and changed-source
  detectors;
- lineage staleness via the revision ledger, with moved keys as
  evidence (hash moves have no oracle yet: records are compared
  against their own hashes, so only revision and contract moves flag);
- study-map obligations derived per unit, one definition with the
  producer.

Deliberately excluded: critique points (OPERATOR.md boundary 17 — an
open point is not a work item, and the scan must not convert any into
goals); question, inspection, and correction counts (no observable
source exists, and creating one would be telemetry — those detectors
stay caller-fed); dossier freshness (no registry of live dossier keys;
Phase 5 left serving as operator wiring).
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..githistory import GitHistoryError, last_commit_timestamps
from ..loader import load_repo
from .goals import (
    CandidateGoal,
    detect_covering_routes_stale,
    detect_source_changed_under_claim,
)
from .lineage import load_ledger
from .predicates import CONTRACT_VERSION, claim_stale, needs_study_map

#: Revision ledger: the current-revisions source for staleness.
REVISIONS_RELATIVE = "operations/transactions/revisions.yaml"

#: Default recency window. Stateless by design: see the module docstring.
DEFAULT_DAYS = 30


@dataclass(frozen=True)
class ScanInput:
    """Everything the scan interprets: observations, already assembled."""

    changed_nodes: tuple[str, ...] = ()
    route_covers: tuple[tuple[str, tuple[str, ...]], ...] = ()
    changed_sources: tuple[str, ...] = ()
    claim_sources: tuple[tuple[str, tuple[str, ...]], ...] = ()
    stale_claims: tuple[tuple[str, tuple[str, ...]], ...] = ()
    obligations: tuple[str, ...] = ()
    known_ids: tuple[str, ...] = ()


def _emit(goal_id: str, detector: str, title: str,
          rationale: str, evidence: Sequence[str]) -> CandidateGoal:
    return CandidateGoal(
        goal_id=goal_id, detector=detector, title=title,
        rationale=rationale, evidence=tuple(evidence),
    )


def scan_observations(observations: ScanInput) -> tuple[CandidateGoal, ...]:
    """Interpret assembled observations: existing detectors plus two
    scan-level emitters (stale lineage, study-map obligation). Pure:
    same observations, same goals, sorted for determinism."""
    known = set(observations.known_ids)
    goals: list[CandidateGoal] = []
    goals.extend(detect_covering_routes_stale(
        changed_nodes=list(observations.changed_nodes),
        route_covers={rid: list(covers)
                      for rid, covers in observations.route_covers},
        known_ids=list(observations.known_ids),
    ))
    goals.extend(detect_source_changed_under_claim(
        changed_sources=list(observations.changed_sources),
        claim_sources={cid: list(sources)
                       for cid, sources in observations.claim_sources},
        known_ids=list(observations.known_ids),
    ))
    for claim_id, moved in observations.stale_claims:
        goal_id = f"lineage-stale:{claim_id}"
        if goal_id in known:
            continue
        goals.append(_emit(
            goal_id, "lineage-stale",
            f"Re-judge {claim_id}: lineage reads moved",
            f"Revision moves under {claim_id} ({', '.join(moved)}); "
            "the claim is stale until re-judged.",
            [f"claim:{claim_id}",
             *(f"moved:{key}" for key in moved)],
        ))
    for unit_id in observations.obligations:
        goal_id = f"study-map-obligation:{unit_id}"
        if goal_id in known:
            continue
        goals.append(_emit(
            goal_id, "study-map-obligation",
            f"Unit {unit_id} owes a study map",
            "An active unit with no ordered study map: coverage without "
            "a path. The obligation is derived, one definition with the "
            "producer.",
            [f"unit:{unit_id}"],
        ))
    return tuple(sorted(goals, key=lambda goal: goal.goal_id))


def _read_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


def _changed_files(root: Path, *, days: int) -> tuple[str, ...]:
    """Canonical files moved in the window. Git history is the only
    change feed; a repository without readable history observes nothing
    rather than failing."""
    try:
        stamps = last_commit_timestamps(str(root))
    except GitHistoryError:
        return ()
    cutoff = time.time() - max(days, 0) * 86400
    return tuple(sorted(
        rel for rel, stamp in stamps.items()
        if isinstance(stamp, (int, float)) and stamp >= cutoff
    ))


def _nodes_in_unit_file(root: Path, rel: str) -> tuple[str, ...]:
    if not rel.startswith("curriculum/modules/") \
            or not rel.endswith("/unit.yaml"):
        return ()
    data = _read_yaml(root / rel)
    if not isinstance(data, dict):
        return ()
    knowledge = data.get("knowledge_map")
    nodes = knowledge.get("nodes") if isinstance(knowledge, dict) else None
    if not isinstance(nodes, list):
        return ()
    return tuple(sorted(
        str(node["id"]) for node in nodes
        if isinstance(node, dict) and str(node.get("id") or "").strip()
    ))


def _sources_in_source_map(root: Path, rel: str) -> tuple[str, ...]:
    if not rel.startswith("curriculum/modules/") \
            or not rel.endswith("source-map.yaml"):
        return ()
    data = _read_yaml(root / rel)
    if not isinstance(data, dict):
        return ()
    sources = data.get("sources")
    if not isinstance(sources, list):
        return ()
    return tuple(sorted(
        str(src["source_id"]) for src in sources
        if isinstance(src, dict) and str(src.get("source_id") or "").strip()
    ))


def _route_covers(repo) -> dict[str, list[str]]:
    """Route id to covered knowledge nodes, from the loaded source maps."""
    covers: dict[str, list[str]] = {}
    maps = getattr(repo, "module_source_maps", {}) or {}
    for smap in maps.values():
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
                nodes = route.get("covers")
                if isinstance(rid, str) and rid \
                        and isinstance(nodes, list):
                    covers[rid] = [str(n) for n in nodes]
    return covers


def _current_revisions(root: Path) -> dict[str, int]:
    data = _read_yaml(root / REVISIONS_RELATIVE)
    if not isinstance(data, dict):
        return {}
    revisions = data.get("revisions")
    if not isinstance(revisions, dict):
        return {}
    try:
        return {str(k): int(v) for k, v in revisions.items()}
    except (TypeError, ValueError):
        return {}


def collect_observations(root: Path | str, *,
                         days: int = DEFAULT_DAYS) -> ScanInput:
    """OBSERVE: read the current world. No writes, no queue, no memory."""
    root = Path(root)
    changed = _changed_files(root, days=days)
    nodes: set[str] = set()
    sources: set[str] = set()
    for rel in changed:
        nodes.update(_nodes_in_unit_file(root, rel))
        sources.update(_sources_in_source_map(root, rel))
    records = load_ledger(root)
    current = _current_revisions(root)
    claim_sources: dict[str, list[str]] = {}
    stale: list[tuple[str, tuple[str, ...]]] = []
    for claim_id, lineage in records.items():
        reads = dict(lineage.derived_from.revisions)
        claim_sources[claim_id] = sorted(
            str(key) for key, _ in lineage.derived_from.source_hashes)
        moved = sorted(
            key for key, rev in reads.items() if current.get(key) != rev)
        if lineage.derived_from.contract_version != CONTRACT_VERSION:
            moved = sorted(set(moved) | {"contract-version"})
        if claim_stale(
            read_contract_version=lineage.derived_from.contract_version,
            current_contract_version=CONTRACT_VERSION,
            read_revisions=reads,
            current_revisions=current,
        ):
            stale.append((claim_id, tuple(moved)))
    repo = load_repo(root)
    study_map_units = set()
    for smap in (getattr(repo, "study_maps", {}) or {}).values():
        unit_id = getattr(smap, "unit_id", None)
        if unit_id:
            study_map_units.add(unit_id)
    obligations: list[str] = []
    for unit_id, unit in (getattr(repo, "units", {}) or {}).items():
        module = (getattr(repo, "modules", {}) or {}).get(
            getattr(unit, "module_id", ""), {})
        if needs_study_map(
            unit_status=getattr(unit, "data", {}).get("status"),
            module_status=module.get("status")
            if isinstance(module, dict) else None,
            has_study_map=unit_id in study_map_units,
        ):
            obligations.append(unit_id)
    return ScanInput(
        changed_nodes=tuple(sorted(nodes)),
        route_covers=tuple(sorted(
            (rid, tuple(covers)) for rid, covers in _route_covers(repo).items()
        )),
        changed_sources=tuple(sorted(sources)),
        claim_sources=tuple(sorted(
            (cid, tuple(srcs)) for cid, srcs in claim_sources.items())),
        stale_claims=tuple(sorted(stale)),
        obligations=tuple(sorted(obligations)),
    )


def intelligence_scan(root: Path | str, *,
                      days: int = DEFAULT_DAYS) -> tuple[CandidateGoal, ...]:
    """One observation loop: read the world, interpret, propose."""
    return scan_observations(collect_observations(root, days=days))
