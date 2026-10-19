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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType

from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from learning_os.derive.semantics.claim_audits import AuditError, AuditRecord, audits_from_ledger
from learning_os.derive.semantics.claim_status import (
    ClaimStatus,
    observe_claims,
    read_optional_yaml,
)
from learning_os.derive.semantics.goals import (
    CandidateGoal,
    detect_claim_findings,
    detect_claims_audit,
    detect_inspection_without_dossier,
    detect_repeated_question_gap,
    detect_reviewer_correction_pattern,
    detector_metrics,
    stale_observations,
)
from learning_os.derive.semantics.predicates import needs_study_map
from learning_os.derive.semantics.session_counts import feed_scan_kwargs
from learning_os.store import observations
from learning_os.store.loader import load_repo

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


def read_goal_ledger(root: Path, *, today: _dt.date | None = None) -> tuple[str, ...]:
    """Goal ids Aram already decided. Tolerant: missing or malformed input
    reads as no decisions, so the scan never crashes on operational state
    and never invents a decision nobody recorded."""
    data = read_optional_yaml(root / GOAL_LEDGER_RELATIVE)
    if not isinstance(data, dict):
        return ()
    decisions = data.get("decisions")
    if not isinstance(decisions, dict):
        return ()
    return _decided_goal_ids(decisions, today=today)


def _decided_goal_ids(decisions: Mapping[str, object], *, today: _dt.date | None = None) -> tuple[str, ...]:
    day = today or observations.today()
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
class GoalLedgerObservation:
    """Immutable values for one read operation, never later write authority."""

    known_ids: tuple[str, ...]
    audits: tuple[tuple[str, AuditRecord], ...]
    metrics: Mapping[str, Mapping[str, object]]


def observe_goal_ledger(root: Path | str) -> GoalLedgerObservation:
    path = Path(root) / GOAL_LEDGER_RELATIVE
    value = read_optional_yaml(path)
    if value is None and not path.exists() and not path.is_symlink():
        value = {"decisions": {}}
    if value is None:
        raise AuditError("cannot read preserved audit state: goal ledger is unreadable or malformed")
    audits = audits_from_ledger(value)
    assert isinstance(value, dict)  # Validated by audits_from_ledger.
    decisions = {key: row for key, row in value["decisions"].items() if isinstance(key, str)}
    metrics = MappingProxyType({key: MappingProxyType(row)
                                for key, row in detector_metrics(decisions).items()})
    return GoalLedgerObservation(_decided_goal_ids(decisions), tuple(sorted(audits.items())), metrics)


@dataclass(frozen=True)
class ScanInput:
    """Everything the scan interprets: observations, already assembled."""

    claims: tuple[ClaimStatus, ...] = ()
    audits: tuple[tuple[str, AuditRecord], ...] = ()
    obligations: tuple[str, ...] = ()
    evidence_stale: tuple[tuple[str, str], ...] = ()
    known_ids: tuple[str, ...] = ()
    # Caller-fed session counts (see session_counts.py). Empty means
    # unfed: the three count detectors stay silent, exactly as before.
    question_counts: tuple[tuple[str, int], ...] = ()
    inspection_counts: tuple[tuple[tuple[str, ...], int], ...] = ()
    correction_counts: tuple[tuple[str, int], ...] = ()
    voq_classes: tuple[str, ...] = ()
    dossier_sets: tuple[tuple[str, ...], ...] = ()

    @property
    def stale_claims(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return tuple((row.claim_id, row.moved) for row in self.claims if row.status == "stale")


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
    goals.extend(detect_claim_findings(claims=observations.claims, known_ids=observations.known_ids))
    goals.extend(detect_claims_audit(claims=observations.claims, audits=dict(observations.audits),
                                    known_ids=observations.known_ids))
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


def collect_observations(root: Path | str, *,
                         days: int = DEFAULT_DAYS,
                         goal_ledger: GoalLedgerObservation | None = None) -> ScanInput:
    """OBSERVE: read the current world. No writes, no queue, no memory.

    ``days`` is retained for caller compatibility and ignored:
    staleness compares each claim's stored pins against the live rows,
    never a recency window, so the scan needs no Git history at all.
    """
    root = Path(root)
    repo = load_repo(root)
    ledger = goal_ledger if goal_ledger is not None else observe_goal_ledger(root)
    audits = dict(ledger.audits)
    status_map = observe_claims(root, repo=repo, audits=audits)
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
    # `commands/goal.py`. The shared observation validates ledger structure;
    # malformed decision rows are skipped rather than trusted as decisions.
    decided = ledger.known_ids
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
    return ScanInput(claims=tuple(status_map.values()), audits=tuple(sorted(audits.items())),
                     obligations=tuple(sorted(obligations)), evidence_stale=evidence_stale,
                     known_ids=decided)



def intelligence_scan(root: Path | str, *,
                      days: int = DEFAULT_DAYS,
                      feed: Mapping | None = None,
                      goal_ledger: GoalLedgerObservation | None = None,
                      ) -> tuple[CandidateGoal, ...]:
    """One observation loop: read the world, interpret, propose.

    ``feed`` is a caller-supplied session-count mapping (see
    ``session_counts.parse_feed`` for the shape). None or empty
    behaves exactly like no feed: the three count detectors stay
    silent. The scan records nothing either way.
    """
    ledger = goal_ledger if goal_ledger is not None else observe_goal_ledger(Path(root))
    observations = collect_observations(root, days=days, goal_ledger=ledger)
    if feed:
        observations = replace(observations, **feed_scan_kwargs(feed))
    goals = scan_observations(observations)
    metrics = ledger.metrics
    return tuple(replace(goal, quiet=metrics.get(goal.detector, {}).get("quiet") is True) for goal in goals)
