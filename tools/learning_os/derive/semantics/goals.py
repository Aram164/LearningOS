"""Phase-3 candidate goals: read-only detectors plus a proposal queue.

The engine surfaces what is worth investigating; it never performs a
semantic mutation itself. Detectors are pure functions over caller-supplied
signals — repeated questions, digest pins against live rows, inspection
patterns, reviewer corrections — and emit goals in ``detected`` state
with their rationale and evidence attached. A goal then walks an explicit lifecycle; only Aram moves
it to ``authorized``, wired to the critique-point rule that an open point
is not work until he says so in that session.

Spam control is structural: per-detector eligibility thresholds, ``known_ids``
dedup at detection, and the STALE/SUPERSEDED exits. The queue lives under
``work/proposals/goals/`` as one YAML file per goal (shape validated by
``goal_from_dict``); detectors write nothing — the operator files what the
engine proposes.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from learning_os.derive.learning_runtime import requirement_fingerprint
from learning_os.derive.semantics.claim_audits import (
    SAMPLE_SIZE,
    AuditRecord,
    audit_id,
    eligible_pool,
)
from learning_os.derive.semantics.claim_status import ClaimStatus


class GoalError(ValueError):
    """A goal record or lifecycle transition cannot be read as written."""


#: The full lifecycle. Forward motion walks the chain one step at a time;
#: STALE and SUPERSEDED exit sideways; DEFERRED waits; CLOSED and REJECTED
#: are terminal.
STATES = (
    "detected", "formulated", "eligible", "proposed", "authorized",
    "planned", "executing", "verified", "closed",
    "deferred", "rejected", "stale", "superseded",
)

TERMINAL_STATES = ("closed", "rejected", "superseded")

#: Allowed exits from each state. Skipping steps is refused: a goal that
#: never stood as PROPOSED cannot become AUTHORIZED.
TRANSITIONS: Mapping[str, tuple[str, ...]] = {
    "detected": ("formulated", "rejected", "stale"),
    "formulated": ("eligible", "rejected", "stale", "superseded"),
    "eligible": ("proposed", "deferred", "rejected", "stale", "superseded"),
    "proposed": ("authorized", "deferred", "rejected", "stale", "superseded"),
    "authorized": ("planned", "deferred", "stale"),
    "planned": ("executing", "stale"),
    "executing": ("verified", "stale"),
    "verified": ("closed",),
    "deferred": ("eligible", "rejected"),
    "stale": ("detected", "rejected"),
    "superseded": (),
    "closed": (),
    "rejected": (),
}

#: Only Aram authorizes — the critique-point rule, applied to proposals.
AUTHORIZER = "Aram"


@dataclass(frozen=True)
class CandidateGoal:
    """One proposed investigation, with its state in the queue."""

    goal_id: str
    detector: str
    title: str
    rationale: str
    evidence: tuple[str, ...] = ()
    state: str = "detected"
    authorized_by: str = ""
    superseded_by: str = ""
    quiet: bool = False


def transition(
    goal: CandidateGoal,
    to_state: str,
    *,
    authorized_by: str = "",
    superseded_by: str = "",
) -> CandidateGoal:
    """Move a goal one lifecycle step. Illegal moves fail closed.

    AUTHORIZED requires Aram's explicit action; SUPERSEDED names the goal
    that replaces this one; FORMULATED and beyond require the rationale and
    evidence a detector attached. Terminal states never move.
    """
    if to_state not in STATES:
        raise GoalError(f"unknown goal state: {to_state!r}")
    if to_state not in TRANSITIONS[goal.state]:
        raise GoalError(
            f"goal {goal.goal_id!r} cannot move {goal.state} -> {to_state}")
    if to_state == "authorized" and authorized_by != AUTHORIZER:
        raise GoalError(
            f"goal {goal.goal_id!r} needs {AUTHORIZER}'s explicit action")
    if to_state == "superseded" and not superseded_by:
        raise GoalError(
            f"goal {goal.goal_id!r} superseded by nothing names no successor")
    if to_state not in {"detected", "rejected", "stale"} and (
        not goal.rationale.strip() or not goal.evidence
    ):
        raise GoalError(
            f"goal {goal.goal_id!r} reaches {to_state} without rationale "
            "or evidence")
    return CandidateGoal(
        goal_id=goal.goal_id,
        detector=goal.detector,
        title=goal.title,
        rationale=goal.rationale,
        evidence=goal.evidence,
        state=to_state,
        authorized_by=authorized_by if to_state == "authorized" else goal.authorized_by,
        superseded_by=superseded_by if to_state == "superseded" else goal.superseded_by,
    )


def _strings(value: object, label: str) -> list[str]:
    """A list of strings, or a refusal. A bare string is never a list."""
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise GoalError(f"malformed {label}: expected a list of strings")
    try:
        items = [str(item) for item in value]
    except TypeError as exc:
        raise GoalError(f"malformed {label}: {exc}") from exc
    if any(not item for item in items):
        raise GoalError(f"malformed {label}: empty entries")
    return items


def _emit(
    detector: str,
    key: str,
    title: str,
    rationale: str,
    evidence: Sequence[str],
    known_ids: Sequence[str],
) -> CandidateGoal | None:
    """One detection, or None when this goal is already known (dedup)."""
    goal_id = f"{detector}:{key}"
    if goal_id in known_ids:
        return None
    trails = tuple(_strings(evidence, f"evidence for {goal_id!r}"))
    if not title.strip() or not rationale.strip() or not trails:
        raise GoalError(f"detector {detector!r} proposed {goal_id!r} bare")
    return CandidateGoal(
        goal_id=goal_id, detector=detector, title=title,
        rationale=rationale, evidence=trails,
    )


# ---- detectors: read-only, thresholded, deduplicated ------------------------


def detect_claim_findings(*, claims: Sequence[ClaimStatus],
                          known_ids: Sequence[str] = ()) -> tuple[CandidateGoal, ...]:
    goals = []
    for row in claims:
        if not row.goal_id or row.goal_id in known_ids:
            continue
        detector = "lineage-stale" if row.status == "stale" else "claims-needing-review"
        if detector == "lineage-stale":
            if "coarse-pin" in row.causes:
                cause = ["cause:coarse-pin"]
            elif "contract-version" in row.causes:
                cause = ["cause:contract-version"]
            elif "evidence-changed" in row.causes:
                cause = ["cause:evidence:" + key for key in row.moved
                         if not key.startswith(("route-content:", "node-content:"))]
            else:
                cause = ["cause:unit:" + row.unit_id] if row.unit_id else []
            title = f"Re-judge {row.claim_id}: lineage reads moved"
            rationale = "Relevant dependencies changed or cannot be verified; re-judge the claim against current material."
        else:
            cause = []
            title = f"Resolve {row.claim_id}: disputed claim needs a reviewer"
            rationale = "A contest or an exact-basis audit defect needs a reviewed repair."
        evidence = ["claim:" + row.claim_id, "basis:" + row.basis,
                    *("moved:" + key for key in row.moved), *cause]
        if row.unit_id:
            evidence.append("unit:" + row.unit_id)
        goal = _emit(detector, row.goal_id.split(":", 1)[1], title, rationale, evidence, known_ids)
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


def detect_claims_audit(*, claims: Sequence[ClaimStatus], audits: Mapping[str, AuditRecord],
                       known_ids: Sequence[str] = ()) -> tuple[CandidateGoal, ...]:
    pool = eligible_pool(claims)
    if len(pool) < SAMPLE_SIZE:
        return ()
    gid = audit_id(pool)
    # A frozen draw remains one draw even if its mutable attention decision is
    # rejected or deferred. A failed result can only lead to a new basis/pool.
    if gid in audits and audits[gid].result is not None:
        return ()
    goal = _emit("claims-audit", gid.split(":", 1)[1],
                 f"Audit {len(pool)} fresh claims with one frozen sample of 30",
                 "Authorize the complete current pool once before drawing and reviewing its sample.",
                 ["pool:" + gid.split(":", 1)[1], "population:" + str(len(pool))], known_ids)
    return (goal,) if goal is not None else ()


def detect_repeated_question_gap(
    *,
    question_counts: Mapping[str, int],
    voq_classes: Sequence[str],
    threshold: int = 3,
    known_ids: Sequence[str] = (),
) -> tuple[CandidateGoal, ...]:
    """An operator-question class keeps recurring with no VOQ: add one.

    A question class asked past the threshold without a verified triple is
    understanding the system re-derives every time. One goal per gap.
    """
    covered = set(_strings(voq_classes, "voq classes"))
    goals = []
    try:
        items = sorted(question_counts.items())
    except (TypeError, ValueError) as exc:
        raise GoalError(f"malformed question counts: {exc}") from exc
    for asked_class, count in items:
        if not isinstance(count, int) or isinstance(count, bool):
            raise GoalError(f"malformed count for {asked_class!r}")
        if count < threshold or asked_class in covered:
            continue
        goal = _emit(
            "repeated-question-gap", str(asked_class),
            f"Cover question class {asked_class!r} with a VOQ",
            f"Asked {count} times past the threshold of {threshold} with no "
            "verified triple; every future agent re-derives the answer.",
            [f"question-class:{asked_class}"],
            known_ids,
        )
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


def detect_inspection_without_dossier(
    *,
    inspection_counts: Mapping[tuple[str, ...], int],
    dossier_sets: Sequence[Sequence[str]],
    threshold: int = 3,
    known_ids: Sequence[str] = (),
) -> tuple[CandidateGoal, ...]:
    """A file set is inspected repeatedly with no dossier: build one.

    Repeated N-file reads of the same set without a cached dossier is the
    reuse the dossier layer exists to capture. Keys are sorted file tuples
    so the same set in any order dedups to one goal.
    """
    try:
        covered = [set(_strings(files, "dossier set")) for files in dossier_sets]
    except TypeError as exc:
        raise GoalError(f"malformed dossier sets: {exc}") from exc
    goals = []
    try:
        items = sorted(inspection_counts.items())
    except TypeError as exc:
        raise GoalError(f"malformed inspection counts: {exc}") from exc
    for files, count in items:
        if isinstance(files, str):
            raise GoalError("malformed inspection set: expected file tuples")
        try:
            names = tuple(sorted(_strings(files, "inspection set")))
        except TypeError as exc:
            raise GoalError(f"malformed inspection set: {exc}") from exc
        if not isinstance(count, int) or isinstance(count, bool):
            raise GoalError(f"malformed count for {names!r}")
        if count < threshold or not names:
            continue
        if any(set(names) <= files_covered for files_covered in covered):
            continue
        goal = _emit(
            "inspection-without-dossier", "|".join(names),
            f"Build a dossier for {len(names)} repeatedly read files",
            f"Read together {count} times past the threshold of {threshold} "
            "with no cached dossier; every future task rebuilds the context.",
            [f"file:{path}" for path in names],
            known_ids,
        )
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


def detect_reviewer_correction_pattern(
    *,
    correction_counts: Mapping[str, int],
    threshold: int = 3,
    known_ids: Sequence[str] = (),
) -> tuple[CandidateGoal, ...]:
    """Reviewers correct one task class systematically: fix the contract.

    A correction pattern past the threshold is not agent error but missing
    guidance — a predicate, a VOQ, or a worked rule. One goal per class.
    """
    goals = []
    try:
        items = sorted(correction_counts.items())
    except (TypeError, ValueError) as exc:
        raise GoalError(f"malformed correction counts: {exc}") from exc
    for task_class, count in items:
        if not isinstance(count, int) or isinstance(count, bool):
            raise GoalError(f"malformed count for {task_class!r}")
        if count < threshold:
            continue
        goal = _emit(
            "reviewer-correction-pattern", str(task_class),
            f"Address systematic corrections of {task_class!r}",
            f"Corrected {count} times past the threshold of {threshold}; "
            "the contract, not the agents, is missing something.",
            [f"task-class:{task_class}"],
            known_ids,
        )
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


# ---- clustering: one shared cause, one row ----------------------------------

#: Evidence prefixes that name the shared cause behind a fanned-out goal.
#: A covering-routes goal fans out per route over the moved units; a
#: lineage goal fans out per claim over the same moved keys; a review
#: goal fans out per claim over its unit. A changed-source goal fires
#: for its own route row alone and shares no cause with its siblings,
#: so it stands alone. The unit keys are deliberately the unit, not the
#: node set: one decision is "this unit's nodes moved — revalidate its
#: routes," and an exact node set would split that decision wherever
#: one route happens to also cover one more node.
CAUSE_PREFIXES = {
    "covering-routes-stale": "unit:",
    "lineage-stale": "cause:",
    "claims-needing-review": "unit:",
}


@dataclass(frozen=True)
class GoalCluster:
    """Goals fanning out from one shared cause, with nothing lost.

    ``member_ids`` carries every goal id in the group, so clustering
    hides no goal — it only stops printing the same cause N times.
    """

    cluster_id: str
    detector: str
    title: str
    member_ids: tuple[str, ...] = ()
    cause: tuple[str, ...] = ()


@dataclass(frozen=True)
class RankedCluster:
    """One cluster placed in the exam-proximity order, with its reason."""

    cluster: GoalCluster
    tier: int
    nearest_sitting: str = ""
    days_until: int | None = None


def _cluster_cause(goal: CandidateGoal) -> tuple[str, ...] | None:
    """The shared cause behind one goal, or None when it stands alone."""
    try:
        prefix = CAUSE_PREFIXES[goal.detector]
    except KeyError:
        return None
    cause = tuple(sorted(
        evidence for evidence in goal.evidence if evidence.startswith(prefix)))
    return cause or None


def _cluster_title(detector: str, members: list[CandidateGoal],
                   cause: tuple[str, ...]) -> str:
    if len(members) == 1:
        return members[0].title
    joined = ", ".join(cause)
    if detector == "covering-routes-stale":
        return f"{len(members)} routes cover moved nodes in {joined}"
    if detector == "lineage-stale":
        return f"{len(members)} claims read moved dependencies ({joined})"
    if detector == "claims-needing-review":
        return f"{len(members)} claims need review in {joined}"
    return f"{len(members)} {detector} goals"


def cluster_goals(goals: Sequence[CandidateGoal]) -> tuple[GoalCluster, ...]:
    """Group goals fanning out from one shared cause. Pure.

    Same goals, same clusters, sorted for determinism. A detector without
    a shared-cause structure clusters one goal per row — clustering never
    merges what it cannot prove shares a cause.
    """
    groups: dict[tuple, list[CandidateGoal]] = {}
    for goal in goals:
        cause = _cluster_cause(goal)
        key = (goal.detector, cause) if cause is not None \
            else (goal.detector, (goal.goal_id,))
        groups.setdefault(key, []).append(goal)
    clusters = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda goal: goal.goal_id)
        detector = members[0].detector
        cause = _cluster_cause(members[0]) or ()
        member_ids = tuple(goal.goal_id for goal in members)
        digest = hashlib.sha256(
            "\n".join(member_ids).encode("utf-8")).hexdigest()[:8]
        clusters.append(GoalCluster(
            cluster_id=f"{detector}:cluster:{digest}",
            detector=detector,
            title=_cluster_title(detector, members, cause),
            member_ids=member_ids,
            cause=cause,
        ))
    return tuple(clusters)


#: A sitting this near makes its module's goals urgent; inside the wider
#: window they are near. Hand-set, readable, no weights to tune.
URGENT_SITTING_DAYS = 30
NEAR_SITTING_DAYS = 90

#: Module statuses that sort last, always: history, not work.
RETIRED_MODULE_STATUSES = frozenset({"dropped", "archived"})

#: Modules being studied but not exam-registered: pressure-free by default.
STUDYING_MODULE_STATUSES = frozenset({"enrolled", "active"})

#: Within one urgency tier, belief risk outranks fan-out size: a lone
#: contested claim surfaces above a ten-route obligation cluster, and
#: system self-improvement sorts below learner-facing work. Unknown
#: detectors sort last — a new detector earns its precedence
#: explicitly; nothing is promoted by accident of id spelling. This is
#: Aram-tunable data, not a fitted model: edit the order, keep the
#: shape.
DETECTOR_PRECEDENCE = (
    "claims-needing-review",
    "lineage-stale",
    "evidence-superseded",
    "claims-audit",
    "study-map-obligation",
    "reviewer-correction-pattern",
    "repeated-question-gap",
    "inspection-without-dossier",
)


def _sort_days(days: int | None) -> float:
    return float(days) if days is not None else float("inf")


def _cluster_urgency(
    modules: set[str],
    *,
    today: _dt.date,
    deadlines: Sequence[Mapping],
    module_status: Mapping[str, str | None],
) -> tuple[int, str, int | None]:
    """(tier, nearest sitting, days until) for one cluster's modules.

    1 blocks a sitting inside 30 days, module enrolled; 2 the same inside
    90 days; 3 a studying module with no dated pressure; 4 everything
    else; 5 retired modules, last, always. The most urgent module wins.
    """
    upcoming: dict[str, tuple[int, str]] = {}
    for row in deadlines:
        if not isinstance(row, Mapping) or row.get("kind") != "exam":
            continue
        module_id, start = row.get("module_id"), row.get("start_date")
        if not isinstance(module_id, str) or not isinstance(start, str):
            continue
        try:
            delta = (_dt.date.fromisoformat(start) - today).days
        except ValueError:
            continue
        if delta < 0:
            continue
        if module_id not in upcoming or delta < upcoming[module_id][0]:
            upcoming[module_id] = (delta, start)
    best: tuple[int, str, int | None] | None = None
    for module_id in sorted(modules):
        status = module_status.get(module_id)
        if status in RETIRED_MODULE_STATUSES:
            candidate: tuple[int, str, int | None] = (5, "", None)
        elif status == "enrolled" and module_id in upcoming \
                and upcoming[module_id][0] <= URGENT_SITTING_DAYS:
            delta, start = upcoming[module_id]
            candidate = (1, start, delta)
        elif status == "enrolled" and module_id in upcoming \
                and upcoming[module_id][0] <= NEAR_SITTING_DAYS:
            delta, start = upcoming[module_id]
            candidate = (2, start, delta)
        elif status in STUDYING_MODULE_STATUSES:
            candidate = (3, "", None)
        else:
            candidate = (4, "", None)
        if best is None or (candidate[0], _sort_days(candidate[2])) < (
                best[0], _sort_days(best[2])):
            best = candidate
    # No known module is "everything else", never urgent and never retired.
    return best if best is not None else (4, "", None)


def rank_clusters(
    clusters: Sequence[GoalCluster],
    *,
    today: _dt.date,
    deadlines: Sequence[Mapping],
    module_status: Mapping[str, str | None],
    cluster_modules: Mapping[str, set[str]] | None = None,
) -> tuple[RankedCluster, ...]:
    """Order clusters by exam proximity, then detector precedence.

    A pure sort, not a cost model. ``cluster_modules`` names the
    modules behind each cluster id; a cluster with no known module is
    "everything else" (tier 4), never urgent and never retired. Ties
    break on detector precedence (belief risk before fan-out size),
    then cluster size, then id, so the same queue always prints in the
    same order.
    """
    known = dict(cluster_modules or {})
    order = {detector: index
             for index, detector in enumerate(DETECTOR_PRECEDENCE)}
    ranked = []
    for cluster in clusters:
        tier, sitting, days = _cluster_urgency(
            set(known.get(cluster.cluster_id, ())),
            today=today, deadlines=deadlines, module_status=module_status)
        ranked.append(RankedCluster(
            cluster=cluster, tier=tier,
            nearest_sitting=sitting, days_until=days))
    return tuple(sorted(
        ranked,
        key=lambda row: (row.tier, _sort_days(row.days_until),
                         order.get(row.cluster.detector, len(order)),
                         -len(row.cluster.member_ids),
                         row.cluster.cluster_id),
    ))


# ---- evidence staleness: the TMS pointed at the learning side -----------------

#: The belief whose retraction matters is not "this route is evidenced"
#: (cheap to recompute) but "this recorded result still proves its
#: requirement" — held under assumptions (the requirement text) that later
#: moved. The fingerprint is recorded on every observation; this compares
#: it. Doyle's TMS, applied where it pays.


@dataclass(frozen=True)
class StaleEvidence:
    """One recorded result held against a requirement that has since moved."""

    observation_id: str
    requirement: str
    recorded_sha: str
    current_sha: str


def stale_observations(
    requirements: Sequence[Mapping],
    observations: Sequence[Mapping],
) -> tuple[StaleEvidence, ...]:
    """Results whose requirement fingerprint no longer matches. Pure.

    A missing or blank recorded fingerprint is stale, never trusted: a
    result that cannot say what it was evidence for is not evidence.
    Observations of unknown requirements are skipped — the runtime reader
    already refuses those loudly; this comparison must not double-report.
    """
    wanted: dict[str, str] = {}
    for requirement in requirements:
        if isinstance(requirement, Mapping) and requirement.get("id"):
            wanted[str(requirement["id"])] = requirement_fingerprint(
                dict(requirement))
    stale = []
    for obs in observations:
        if not isinstance(obs, dict):
            continue
        req_id = obs.get("requirement")
        current = wanted.get(str(req_id)) if req_id else None
        if current is None:
            continue
        recorded = obs.get("requirement_sha256")
        if recorded != current:
            stale.append(StaleEvidence(
                observation_id=str(obs.get("id") or ""),
                requirement=str(req_id),
                recorded_sha=str(recorded or ""),
                current_sha=current,
            ))
    return tuple(sorted(stale, key=lambda row: row.observation_id))


# ---- queue records ----------------------------------------------------------


def goal_to_dict(goal: CandidateGoal) -> dict:
    """One queue file under work/proposals/goals/: the record shape."""
    return {
        "goal_id": goal.goal_id,
        "detector": goal.detector,
        "title": goal.title,
        "rationale": goal.rationale,
        "evidence": list(goal.evidence),
        "state": goal.state,
        "authorized_by": goal.authorized_by,
        "superseded_by": goal.superseded_by,
        "quiet": goal.quiet,
    }


def goal_from_dict(record: dict) -> CandidateGoal:
    """Rebuild a queue record. Raises GoalError on anything malformed."""
    try:
        state = str(record["state"])
        goal = CandidateGoal(
            goal_id=str(record["goal_id"]),
            detector=str(record["detector"]),
            title=str(record["title"]),
            rationale=str(record["rationale"]),
            evidence=tuple(str(item) for item in record["evidence"]),
            state="detected",
            authorized_by=str(record.get("authorized_by") or ""),
            superseded_by=str(record.get("superseded_by") or ""),
            quiet=record.get("quiet") is True,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GoalError(f"malformed goal record: {exc}") from exc
    if state not in STATES:
        raise GoalError(f"unknown goal state: {state!r}")
    return _restore_state(goal, state)


def _restore_state(goal: CandidateGoal, state: str) -> CandidateGoal:
    """Reload a persisted state without replaying authorization.

    Queue files record where a goal stands, including past Aram's
    authorization — reloading is not authorizing. Only the stored
    authorized_by/superseded_by ride along; anything else would rewrite
    history the queue does not own.
    """
    if state == "detected":
        return goal
    return CandidateGoal(
        goal_id=goal.goal_id,
        detector=goal.detector,
        title=goal.title,
        rationale=goal.rationale,
        evidence=goal.evidence,
        state=state,
        authorized_by=goal.authorized_by,
        superseded_by=goal.superseded_by,
    )


# A reset follows an intentional detector change; decisions before it are not
# measurements of today's detector. The latest decision per occurrence counts
# once. Authorization measures intent, never completed work.
DETECTOR_RESETS = {name: "2026-10-18" for name in DETECTOR_PRECEDENCE}


def detector_metrics(decisions: Mapping[str, object]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for detector in DETECTOR_PRECEDENCE:
        rows = []
        for gid, value in decisions.items():
            if not gid.startswith(detector + ":") or not isinstance(value, dict):
                continue
            state, date = value.get("state"), value.get("decided_at")
            if state not in {"authorized", "closed", "rejected"} or not isinstance(date, str):
                continue
            try:
                _dt.date.fromisoformat(date)
            except ValueError:
                continue
            if date >= DETECTOR_RESETS[detector]:
                rows.append((date, gid, state))
        recent = sorted(rows, reverse=True)[:30]
        n, rejected = len(recent), sum(row[2] == "rejected" for row in recent)
        rate = rejected / n if n else 0.0
        z = 1.959963984540054
        lower = ((rate + z*z/(2*n) - z*math.sqrt(rate*(1-rate)/n + z*z/(4*n*n)))
                 / (1+z*z/n)) if n else 0.0
        out[detector] = {"decisions": n, "rejected": rejected, "not_useful": rate,
                         "wilson_lower_95": lower, "quiet": n >= 10 and lower > 0.10,
                         "reset_on": DETECTOR_RESETS[detector]}
    return out
