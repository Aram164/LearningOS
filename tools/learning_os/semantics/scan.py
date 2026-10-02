"""Intelligence scan: the read-only observation loop.

OBSERVE (this module) → INTERPRET (Phase-3 detectors) → PROPOSE (goals
on stdout) → Aram decides queue entry. No daemon, no background
process, no telemetry database, no automatic writes: every run reads
the current world and exits.

v1 observes what the repository already records and nothing else:
- per-row content digests: every covers claim pins its route row
  (``route-content:``) and each covered knowledge node
  (``node-content:``); the covering-routes and changed-source
  detectors compare those pins against the live rows, so only the
  claim whose own row moved fires — never its co-imported siblings;
- lineage staleness via the revision ledger plus live evidence bytes,
  with moved keys as evidence (manifest digests and repo-file bytes are
  re-resolved; a hash compared to itself is not validation, so missing
  or unreadable evidence fails closed while unrelated claims stay
  unchanged);
- study-map obligations derived per unit, one definition with the
  producer.

Deliberately excluded: critique points (OPERATOR.md boundary 17 — an
open point is not a work item, and the scan must not convert any into
goals). Prospective material-synthesis publications register freshness lineage;
unregistered context dossiers remain operator wiring, with no historical backfill.

Question, inspection, and correction counts have no observable source
inside the repository, and creating one would be telemetry — those
detectors stay caller-fed. A live caller counts ephemerally
(``session_counts.SessionCounts``, in memory only, never persisted)
and hands the counts to the scan (``--feed`` file or ``ScanInput``
fields). The scan records nothing; an empty feed behaves exactly
like no feed.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from ..learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from ..loader import load_repo
from ..pathing import PathBoundaryError, resolve_symlinks_inside
from .goals import (
    CandidateGoal,
    detect_claims_needing_review,
    detect_covering_routes_stale,
    detect_inspection_without_dossier,
    detect_repeated_question_gap,
    detect_reviewer_correction_pattern,
    detect_source_changed_under_claim,
    stale_observations,
)
from .lineage import (
    NODE_CONTENT_PREFIX,
    ROUTE_CONTENT_PREFIX,
    effective_statuses,
    load_ledger,
    node_content_digest,
    route_content_digest,
)
from .predicates import CONTRACT_VERSION, needs_study_map
from .session_counts import feed_scan_kwargs

#: Revision ledger: the current-revisions source for staleness.
REVISIONS_RELATIVE = "operations/transactions/revisions.yaml"

#: Retained default for the ``days`` argument. Staleness compares stored
#: digests and revision pins against live rows, not a recency window;
#: the argument stays so existing callers (``intelligence-scan --days``,
#: ``ranked_scan(days=...)``) keep working unchanged.
DEFAULT_DAYS = 30

#: Aram's explicit goal decisions, written only by `los goal`.
GOAL_LEDGER_RELATIVE = "operations/goal-ledger.yaml"

#: Ledger states that suppress re-emission: each one is Aram having
#: decided, which is exactly what ``detected`` is not.
DECIDED_GOAL_STATES = ("rejected", "deferred", "closed")


def _node_units(repo) -> dict[str, str]:
    """Knowledge node id to owning unit id, from the loaded units.

    The covering-routes clustering key. Only exact, unambiguous
    ownership counts: a node id claimed by zero units — or by more
    than one — resolves to no owner, so those goals simply cluster
    alone, never wrongly.
    """
    owners: dict[str, str] = {}
    ambiguous: set[str] = set()
    for unit_id, unit in (getattr(repo, "units", {}) or {}).items():
        data = getattr(unit, "data", None)
        if not isinstance(data, dict):
            continue
        knowledge = data.get("knowledge_map")
        rows = knowledge.get("nodes") if isinstance(knowledge, dict) else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            node_id = str(row.get("id") or "").strip()
            if not node_id or node_id in ambiguous:
                continue
            if node_id in owners and owners[node_id] != unit_id:
                del owners[node_id]
                ambiguous.add(node_id)
            else:
                owners[node_id] = unit_id
    return owners


def _route_units(repo) -> dict[str, str]:
    """Route id to owning unit id, from the rows' own ``unit_id``.

    The review clustering key for covers claims. Only exact,
    unambiguous ownership counts, as in :func:`_node_units`.
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
            routes = src.get("unit_routes")
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, dict):
                    continue
                rid = route.get("id")
                unit_id = route.get("unit_id")
                if not isinstance(rid, str) or not rid \
                        or not isinstance(unit_id, str) or not unit_id.strip():
                    continue
                if rid in ambiguous:
                    continue
                if rid in owners and owners[rid] != unit_id:
                    del owners[rid]
                    ambiguous.add(rid)
                else:
                    owners[rid] = unit_id
    return owners


def _read_goal_ledger(root: Path, *, today: _dt.date | None = None) -> tuple[str, ...]:
    """Goal ids Aram already decided. Tolerant: missing or malformed input
    reads as no decisions, so the scan never crashes on operational state
    and never invents a decision nobody recorded."""
    data = _read_yaml(root / GOAL_LEDGER_RELATIVE)
    if not isinstance(data, dict):
        return ()
    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        return ()
    day = today or _dt.date.today()
    known = []
    for goal_id, row in decisions.items():
        if not isinstance(goal_id, str) or not goal_id or not isinstance(row, dict):
            continue
        state = row.get("state")
        if state not in DECIDED_GOAL_STATES:
            continue
        if state == "deferred" and row.get("revisit_on") is not None:
            try:
                revisit = _dt.date.fromisoformat(row["revisit_on"])
            except (TypeError, ValueError):
                continue  # Bad operational data cannot silently suppress a goal.
            if revisit <= day:
                continue
        known.append(goal_id)
    return tuple(sorted(known))


@dataclass(frozen=True)
class ScanInput:
    """Everything the scan interprets: observations, already assembled."""

    route_covers: tuple[tuple[str, tuple[str, ...]], ...] = ()
    route_digest_pins: tuple[tuple[str, str], ...] = ()
    live_route_digests: tuple[tuple[str, str], ...] = ()
    route_revision_pins: tuple[
        tuple[str, tuple[tuple[str, int], ...]], ...] = ()
    current_revisions: tuple[tuple[str, int], ...] = ()
    node_digest_pins: tuple[
        tuple[str, tuple[tuple[str, str], ...]], ...] = ()
    live_node_digests: tuple[tuple[str, str], ...] = ()
    claim_statuses: tuple[tuple[str, str], ...] = ()
    stale_claims: tuple[tuple[str, tuple[str, ...]], ...] = ()
    obligations: tuple[str, ...] = ()
    evidence_stale: tuple[tuple[str, str], ...] = ()
    node_units: tuple[tuple[str, str], ...] = ()
    claim_units: tuple[tuple[str, str], ...] = ()
    claim_reviews: tuple[tuple[str, str, str], ...] = ()
    known_ids: tuple[str, ...] = ()
    # Caller-fed session counts (see session_counts.py). Empty means
    # unfed: the three count detectors stay silent, exactly as before.
    question_counts: tuple[tuple[str, int], ...] = ()
    inspection_counts: tuple[tuple[tuple[str, ...], int], ...] = ()
    correction_counts: tuple[tuple[str, int], ...] = ()
    voq_classes: tuple[str, ...] = ()
    dossier_sets: tuple[tuple[str, ...], ...] = ()


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
        route_covers={rid: list(covers)
                      for rid, covers in observations.route_covers},
        node_digest_pins={rid: dict(pins)
                          for rid, pins in observations.node_digest_pins},
        live_node_digests=dict(observations.live_node_digests),
        claim_statuses=dict(observations.claim_statuses),
        known_ids=list(observations.known_ids),
        node_units=dict(observations.node_units),
    ))
    goals.extend(detect_source_changed_under_claim(
        route_digest_pins=dict(observations.route_digest_pins),
        live_route_digests=dict(observations.live_route_digests),
        route_revision_pins={rid: dict(pins)
                             for rid, pins in observations.route_revision_pins},
        current_revisions=dict(observations.current_revisions),
        claim_statuses=dict(observations.claim_statuses),
        known_ids=list(observations.known_ids),
    ))
    goals.extend(detect_claims_needing_review(
        claims={cid: {"reviewed_by": reviewed, "status": status}
                for cid, reviewed, status in observations.claim_reviews},
        known_ids=list(observations.known_ids),
        claim_units=dict(observations.claim_units),
    ))
    if observations.question_counts:
        goals.extend(detect_repeated_question_gap(
            question_counts=dict(observations.question_counts),
            voq_classes=list(observations.voq_classes),
            known_ids=list(observations.known_ids),
        ))
    if observations.inspection_counts:
        goals.extend(detect_inspection_without_dossier(
            inspection_counts={
                files: count
                for files, count in observations.inspection_counts},
            dossier_sets=[list(entry) for entry in observations.dossier_sets],
            known_ids=list(observations.known_ids),
        ))
    if observations.correction_counts:
        goals.extend(detect_reviewer_correction_pattern(
            correction_counts=dict(observations.correction_counts),
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


def _scan_manifest_files(root: Path) -> dict:
    """Live materials-manifest files map, or {} when unreadable."""
    data = _read_yaml(root / "records" / "materials-manifest.yaml")
    files = data.get("files") if isinstance(data, dict) else None
    return files if isinstance(files, dict) else {}


def _live_claim_digests(repo) -> tuple[dict[str, str], dict[str, str]]:
    """Live route-row and knowledge-node digests, keyed by claim-read key.

    Mirrors the Phase B digest binding in ``commands.module``: one entry
    per stored route row and per knowledge node. An id claimed twice with
    different digests resolves to no digest — the scan never invents
    ownership, and the affected claims fail closed to stale.
    """
    routes: dict[str, str] = {}
    dropped_routes: set[str] = set()
    maps = getattr(repo, "module_source_maps", {}) or {}
    for module_id, smap in maps.items():
        if not isinstance(smap, dict):
            continue
        for src in smap.get("sources") or []:
            if not isinstance(src, dict):
                continue
            source_id = str(src.get("source_id") or "")
            for row in src.get("unit_routes") or []:
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                key = ROUTE_CONTENT_PREFIX + str(row["id"])
                if key in dropped_routes:
                    continue
                digest = route_content_digest(
                    module_id=str(module_id), source_id=source_id, route=row)
                if key in routes and routes[key] != digest:
                    del routes[key]
                    dropped_routes.add(key)
                else:
                    routes[key] = digest
    nodes: dict[str, str] = {}
    dropped_nodes: set[str] = set()
    for unit in (getattr(repo, "units", {}) or {}).values():
        data = getattr(unit, "data", None)
        if not isinstance(data, dict):
            continue
        knowledge = data.get("knowledge_map")
        rows = knowledge.get("nodes") if isinstance(knowledge, dict) else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or not str(row.get("id") or "").strip():
                continue
            key = NODE_CONTENT_PREFIX + str(row["id"])
            if key in dropped_nodes:
                continue
            digest = node_content_digest(row)
            if key in nodes and nodes[key] != digest:
                del nodes[key]
                dropped_nodes.add(key)
            else:
                nodes[key] = digest
    return routes, nodes


def live_evidence_digest(root: Path, key: str, manifest_files: dict, *, repo=None,
                         route_digests: dict[str, str] | None = None,
                         node_digests: dict[str, str] | None = None) -> str | None:
    """Resolve one stored source-hash key against live bytes.

    Material-synthesis basis keys use the publisher's evidential fields and live
    local bytes, excluding prose and revision-only changes. Mirrors the Phase B
    digest binding in ``commands.module``: manifest keys
    read the registered checksum, file keys hash current bytes inside the
    repository, route-content and node-content keys hash the live route row
    and knowledge node the covers judgment read. Returns ``None`` when the
    dependency is missing, escapes, unreadable, or in an unknown namespace.
    Callers treat ``None`` as stale: an unsupported namespace has no
    trustworthy live value.
    """
    if key.startswith(ROUTE_CONTENT_PREFIX) or key.startswith(NODE_CONTENT_PREFIX):
        if route_digests is None or node_digests is None:
            try:
                repo = load_repo(root) if repo is None else repo
                live_routes, live_nodes = _live_claim_digests(repo)
            except (OSError, ValueError):
                return None
            if route_digests is None:
                route_digests = live_routes
            if node_digests is None:
                node_digests = live_nodes
        if key.startswith(ROUTE_CONTENT_PREFIX):
            return route_digests.get(key)
        return node_digests.get(key)
    if key.startswith("material-synthesis-basis:"):
        from ..material_synthesis import (
            MaterialSynthesisError,
            current_unit_material_basis,
            material_basis_checksum,
            material_synthesis_freshness,
            synthesis_destination,
        )
        unit_id = key[len("material-synthesis-basis:"):]
        try:
            repo = load_repo(root) if repo is None else repo
            cache = {}
            basis = current_unit_material_basis(root, unit_id, repo=repo, cache=cache)
            value = _read_yaml(synthesis_destination(root, unit_id))
            if not isinstance(value, dict) or material_synthesis_freshness(
                    root, unit_id, value, repo=repo, cache=cache)["status"] != "current":
                return None
            return material_basis_checksum(basis)
        except (MaterialSynthesisError, OSError, ValueError):
            return None
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

    ``days`` is retained for caller compatibility and ignored:
    staleness compares each claim's stored pins against the live rows,
    never a recency window, so the scan needs no Git history at all.
    """
    root = Path(root)
    repo = load_repo(root)
    records = load_ledger(root)
    current = _current_revisions(root)
    manifest_files = _scan_manifest_files(root)
    route_units = _route_units(repo)
    route_digest_pins: dict[str, str] = {}
    route_revision_pins: dict[str, dict[str, int]] = {}
    node_digest_pins: dict[str, dict[str, str]] = {}
    claim_units: dict[str, str] = {}
    statuses: list[tuple[str, str]] = []
    stale: list[tuple[str, tuple[str, ...]]] = []
    reviews: list[tuple[str, str, str]] = []
    # Each stored evidence key is resolved against live bytes once per
    # collection: shared evidence is read once no matter how many
    # dependent claims pin it. Unresolvable keys stay absent and fail
    # closed downstream, exactly as before.
    live_all: dict[str, str] = {}
    attempted: set[str] = set()
    claim_routes, claim_nodes = _live_claim_digests(repo)
    for lineage in records.values():
        for key in dict(lineage.derived_from.source_hashes):
            if key not in live_all and key not in attempted:
                attempted.add(key)
                live = live_evidence_digest(
                    root, key, manifest_files, repo=repo,
                    route_digests=claim_routes, node_digests=claim_nodes)
                if live is not None:
                    live_all[key] = live
    effective = effective_statuses(
        records, CONTRACT_VERSION, current, dict(live_all))
    for claim_id, lineage in records.items():
        reads = dict(lineage.derived_from.revisions)
        stored_hashes = dict(lineage.derived_from.source_hashes)
        # Covers claims feed the row-level detectors from their own pins:
        # a new-shape claim pins its route row plus its covered nodes,
        # while an old-shape claim pins only artifact revisions. Every
        # other family (or an unresolvable route) pins nothing here,
        # while the independent revision/hash staleness path below still
        # applies.
        if claim_id.startswith("covers:"):
            route_id = claim_id[len("covers:"):]
            route_key = ROUTE_CONTENT_PREFIX + route_id
            if route_key in stored_hashes:
                route_digest_pins[route_id] = stored_hashes[route_key]
                node_digest_pins[route_id] = {
                    key[len(NODE_CONTENT_PREFIX):]: digest
                    for key, digest in stored_hashes.items()
                    if key.startswith(NODE_CONTENT_PREFIX)
                }
            else:
                route_revision_pins[route_id] = dict(reads)
            if route_id in route_units:
                claim_units[claim_id] = route_units[route_id]
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
        # The row detectors read the ledger's stored verdict: a
        # supported claim whose rows moved is effectively stale, which
        # is exactly the transition they report. Contested and
        # withdrawn claims route to their reviewer and fresh judgment.
        stored = lineage.status
        statuses.append((
            claim_id,
            stored if isinstance(stored, str) else "",
        ))
        if verdict.status == "stale":
            stale.append((
                claim_id,
                tuple(sorted(set(moved) | set(verdict.blocked_by))),
            ))
        reviewed = lineage.reviewed_by
        reviews.append((
            claim_id,
            reviewed if isinstance(reviewed, str) else "",
            verdict.status if isinstance(verdict.status, str) else "",
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
        route_covers=tuple(sorted(
            (rid, tuple(covers)) for rid, covers in _route_covers(repo).items()
        )),
        route_digest_pins=tuple(sorted(route_digest_pins.items())),
        live_route_digests=tuple(sorted(
            (key[len(ROUTE_CONTENT_PREFIX):], digest)
            for key, digest in claim_routes.items()
        )),
        route_revision_pins=tuple(sorted(
            (rid, tuple(sorted(pins.items())))
            for rid, pins in route_revision_pins.items()
        )),
        current_revisions=tuple(sorted(current.items())),
        node_digest_pins=tuple(sorted(
            (rid, tuple(sorted(pins.items())))
            for rid, pins in node_digest_pins.items()
        )),
        live_node_digests=tuple(sorted(
            (key[len(NODE_CONTENT_PREFIX):], digest)
            for key, digest in claim_nodes.items()
        )),
        claim_statuses=tuple(sorted(statuses)),
        node_units=tuple(sorted(_node_units(repo).items())),
        claim_units=tuple(sorted(claim_units.items())),
        stale_claims=tuple(sorted(stale)),
        obligations=tuple(sorted(obligations)),
        evidence_stale=evidence_stale,
        claim_reviews=tuple(sorted(reviews)),
        known_ids=decided,
    )


def intelligence_scan(root: Path | str, *,
                      days: int = DEFAULT_DAYS,
                      feed: Mapping | None = None,
                      ) -> tuple[CandidateGoal, ...]:
    """One observation loop: read the world, interpret, propose.

    ``feed`` is a caller-supplied session-count mapping (see
    ``session_counts.parse_feed`` for the shape). None or empty
    behaves exactly like no feed: the three count detectors stay
    silent. The scan records nothing either way.
    """
    observations = collect_observations(root, days=days)
    if feed:
        observations = replace(observations, **feed_scan_kwargs(feed))
    return scan_observations(observations)
