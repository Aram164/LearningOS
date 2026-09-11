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
- lineage staleness via the revision ledger plus live evidence bytes,
  with moved keys as evidence (manifest digests and repo-file bytes are
  re-resolved; a hash compared to itself is not validation, so missing
  or unreadable evidence fails closed while unrelated claims stay
  unchanged);
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

import hashlib
import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..githistory import last_commit_timestamps
from ..learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from ..loader import load_repo
from ..pathing import PathBoundaryError, resolve_symlinks_inside
from .goals import (
    CandidateGoal,
    detect_covering_routes_stale,
    detect_source_changed_under_claim,
    stale_observations,
)
from .lineage import effective_statuses, load_ledger
from .predicates import CONTRACT_VERSION, needs_study_map

#: Revision ledger: the current-revisions source for staleness.
REVISIONS_RELATIVE = "operations/transactions/revisions.yaml"

#: Default recency window. Stateless by design: see the module docstring.
DEFAULT_DAYS = 30

#: Aram's explicit goal decisions, written only by `los goal`.
GOAL_LEDGER_RELATIVE = "operations/goal-ledger.yaml"

#: Ledger states that suppress re-emission: each one is Aram having
#: decided, which is exactly what ``detected`` is not.
DECIDED_GOAL_STATES = ("rejected", "deferred", "closed")


def _unit_ids_by_path(root: Path, repo) -> dict[str, str]:
    """Unit file rel to unit id. A changed unit file is the unit that
    moved — the covering-routes clustering key. Unresolvable paths stay
    absent; those goals simply cluster alone, never wrongly."""
    owners: dict[str, str] = {}
    for unit_id, unit in (getattr(repo, "units", {}) or {}).items():
        path = getattr(unit, "path", None)
        if not isinstance(path, Path):
            continue
        try:
            rel = path.relative_to(root) if path.is_absolute() else path
        except (OSError, ValueError):
            continue
        owners[rel.as_posix()] = unit_id
    return owners


def _read_goal_ledger(root: Path) -> tuple[str, ...]:
    """Goal ids Aram already decided. Tolerant: missing or malformed input
    reads as no decisions, so the scan never crashes on operational state
    and never invents a decision nobody recorded."""
    data = _read_yaml(root / GOAL_LEDGER_RELATIVE)
    if not isinstance(data, dict):
        return ()
    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        return ()
    return tuple(sorted(
        goal_id for goal_id, row in decisions.items()
        if isinstance(goal_id, str) and goal_id
        and isinstance(row, dict) and row.get("state") in DECIDED_GOAL_STATES
    ))


@dataclass(frozen=True)
class ScanInput:
    """Everything the scan interprets: observations, already assembled."""

    changed_nodes: tuple[str, ...] = ()
    route_covers: tuple[tuple[str, tuple[str, ...]], ...] = ()
    changed_sources: tuple[str, ...] = ()
    claim_sources: tuple[tuple[str, tuple[str, ...]], ...] = ()
    stale_claims: tuple[tuple[str, tuple[str, ...]], ...] = ()
    obligations: tuple[str, ...] = ()
    evidence_stale: tuple[tuple[str, str], ...] = ()
    node_units: tuple[tuple[str, str], ...] = ()
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
        node_units=dict(observations.node_units),
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
            f"Dependencies changed or cannot be verified for {claim_id} ({', '.join(moved)}); "
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
    for observation_id, requirement_id in observations.evidence_stale:
        goal_id = f"evidence-superseded:{observation_id}"
        if goal_id in known:
            continue
        goals.append(_emit(
            goal_id, "evidence-superseded",
            f"Re-check {observation_id}: its requirement moved",
            f"Recorded against {requirement_id}, whose fingerprint no "
            "longer matches — the result may no longer prove what it "
            "proved. Re-run the requirement or supersede the result.",
            [f"observation:{observation_id}",
             f"requirement:{requirement_id}"],
        ))
    return tuple(sorted(goals, key=lambda goal: goal.goal_id))


def _read_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


def _normalize_timestamp(value: object) -> float | None:
    """Normalize one Git timestamp to epoch seconds.

    The history provider returns integer strings; legitimate numeric
    inputs are accepted as well. Booleans, malformed strings,
    non-finite values and other types are rejected explicitly — never
    coerced to zero — so a bad value cannot masquerade as an old change.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        candidate = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            candidate = float(text)
        except ValueError:
            return None
    else:
        return None
    if not math.isfinite(candidate):
        return None
    return candidate


def _changed_files(root: Path, *, days: int) -> tuple[str, ...]:
    """Canonical files moved in the window.

    Git history is the only change feed. A repository without history
    (plain export, unborn branch, empty log) observes nothing. An
    unreadable history raises ``GitHistoryError`` so the caller can
    report unavailable observations instead of presenting them as no
    changes.
    """
    stamps = last_commit_timestamps(str(root))
    cutoff = time.time() - max(days, 0) * 86400
    recent: list[str] = []
    for rel, stamp in stamps.items():
        normalized = _normalize_timestamp(stamp)
        if normalized is not None and normalized >= cutoff:
            recent.append(rel)
    return tuple(sorted(recent))


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


def _route_sources(repo) -> dict[str, str]:
    """Route id to owning source id, from the loaded source maps.

    Only exact, unambiguous ownership counts: a route id claimed by
    zero sources — or by more than one — resolves to no owner, so the
    scan never invents source ownership from filename or digest-key
    spelling.
    """
    owners: dict[str, str] = {}
    ambiguous: set[str] = set()
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
            sid = src.get("source_id")
            if not isinstance(sid, str) or not sid.strip():
                continue
            routes = src.get("unit_routes")
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, dict):
                    continue
                rid = route.get("id")
                if not isinstance(rid, str) or not rid:
                    continue
                if rid in ambiguous:
                    continue
                if rid in owners and owners[rid] != sid:
                    del owners[rid]
                    ambiguous.add(rid)
                else:
                    owners[rid] = sid
    return owners


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


def _scan_manifest_files(root: Path) -> dict:
    """Live materials-manifest files map, or {} when unreadable."""
    data = _read_yaml(root / "records" / "materials-manifest.yaml")
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else {}


def live_evidence_digest(root: Path, key: str, manifest_files: dict) -> str | None:
    """Resolve one stored source-hash key against live bytes.

    Mirrors the Phase B digest binding in ``commands.module``: manifest keys
    read the registered checksum, file keys hash current bytes inside the
    repository. Returns ``None`` when the dependency is missing, escapes,
    unreadable, or in an unknown namespace. Callers treat ``None`` as
    stale: an unsupported namespace has no trustworthy live value.
    """
    if key.startswith("manifest:"):
        ref = key[len("manifest:"):]
        entry = manifest_files.get(ref)
        digest = entry.get("sha256") if isinstance(entry, dict) else None
        return digest if isinstance(digest, str) and digest.strip() else None
    if key.startswith("file:"):
        ref = key[len("file:"):]
        try:
            candidate = resolve_symlinks_inside(root, root / ref)
            return "sha256:" + hashlib.sha256(
                candidate.read_bytes()).hexdigest()
        except (OSError, PathBoundaryError):
            return None
    return None


def collect_observations(root: Path | str, *,
                         days: int = DEFAULT_DAYS) -> ScanInput:
    """OBSERVE: read the current world. No writes, no queue, no memory.

    Raises ``GitHistoryError`` when Git history is unreadable, so the
    caller can report unavailable observations instead of presenting
    them as no changes.
    """
    root = Path(root)
    changed = _changed_files(root, days=days)
    repo = load_repo(root)
    unit_of = _unit_ids_by_path(root, repo)
    nodes: set[str] = set()
    node_units: dict[str, str] = {}
    sources: set[str] = set()
    for rel in changed:
        unit_id = unit_of.get(rel)
        for node_id in _nodes_in_unit_file(root, rel):
            nodes.add(node_id)
            if unit_id is not None:
                node_units[node_id] = unit_id
        sources.update(_sources_in_source_map(root, rel))
    route_sources = _route_sources(repo)
    records = load_ledger(root)
    current = _current_revisions(root)
    manifest_files = _scan_manifest_files(root)
    claim_sources: dict[str, list[str]] = {}
    stale: list[tuple[str, tuple[str, ...]]] = []
    # Each stored evidence key is resolved against live bytes once per
    # collection: shared evidence is read once no matter how many
    # dependent claims pin it. Unresolvable keys stay absent and fail
    # closed downstream, exactly as before.
    live_all: dict[str, str] = {}
    attempted: set[str] = set()
    for lineage in records.values():
        for key in dict(lineage.derived_from.source_hashes):
            if key not in live_all and key not in attempted:
                attempted.add(key)
                live = live_evidence_digest(root, key, manifest_files)
                if live is not None:
                    live_all[key] = live
    effective = effective_statuses(
        records, CONTRACT_VERSION, current, dict(live_all))
    for claim_id, lineage in records.items():
        reads = dict(lineage.derived_from.revisions)
        stored_hashes = dict(lineage.derived_from.source_hashes)
        # Source ownership comes from exact route identity in the loaded
        # source maps — never from intersecting source ids with file: or
        # manifest: digest keys. Only route-covers claims earn ownership;
        # every other family (or an unresolved route) pins nothing, while
        # the independent revision/hash staleness path below still applies.
        if claim_id.startswith("covers:"):
            owner = route_sources.get(claim_id[len("covers:"):])
            claim_sources[claim_id] = [owner] if owner else []
        else:
            claim_sources[claim_id] = []
        # Live evidence bytes: resolve manifest/file hashes the same way
        # Phase B bound them. Missing or unreadable evidence fails closed;
        # unknown namespaces also have no verifiable live value.
        live_hashes = {
            key: live_all[key] for key in stored_hashes if key in live_all
        }
        moved = sorted(
            key for key, rev in reads.items() if current.get(key) != rev)
        moved = sorted(set(moved) | {
            key for key, old in stored_hashes.items()
            if live_hashes.get(key) != old
        })
        if lineage.derived_from.contract_version != CONTRACT_VERSION:
            moved = sorted(set(moved) | {"contract-version"})
        verdict = effective[claim_id]
        if verdict.status == "stale":
            stale.append((
                claim_id,
                tuple(sorted(set(moved) | set(verdict.blocked_by))),
            ))
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
    # Decided goals stay decided: Aram's explicit reject/defer/close feeds
    # the detectors' `known_ids` dedup, so every scan stops re-emitting
    # what he already judged. The write side lives in
    # `commands/goal.py`; this read stays tolerant on purpose — a missing
    # ledger means no decisions yet, and a malformed row is skipped rather
    # than trusted, so the scan degrades to re-emitting, never to lying.
    decided = _read_goal_ledger(root)
    # Learning-side truth maintenance: results held against requirements
    # that moved since. An unreadable runtime degrades to no evidence
    # goals — the scan reports the world, never a traceback.
    try:
        runtime_requirements = collect_requirements(repo)
        runtime_observations = read_observations(repo, runtime_requirements)
        evidence_stale = tuple(
            (row.observation_id, row.requirement)
            for row in stale_observations(
                runtime_requirements, runtime_observations)
        )
    except RuntimeInputError:
        evidence_stale = ()
    return ScanInput(
        changed_nodes=tuple(sorted(nodes)),
        node_units=tuple(sorted(node_units.items())),
        route_covers=tuple(sorted(
            (rid, tuple(covers)) for rid, covers in _route_covers(repo).items()
        )),
        changed_sources=tuple(sorted(sources)),
        claim_sources=tuple(sorted(
            (cid, tuple(srcs)) for cid, srcs in claim_sources.items())),
        stale_claims=tuple(sorted(stale)),
        obligations=tuple(sorted(obligations)),
        evidence_stale=evidence_stale,
        known_ids=decided,
    )


def intelligence_scan(root: Path | str, *,
                      days: int = DEFAULT_DAYS) -> tuple[CandidateGoal, ...]:
    """One observation loop: read the world, interpret, propose."""
    return scan_observations(collect_observations(root, days=days))
