"""Phase-3 candidate goals: read-only detectors plus a proposal queue.

The engine surfaces what is worth investigating; it never performs a
semantic mutation itself. Detectors are pure functions over caller-supplied
signals — repeated questions, changed nodes, inspection patterns, reviewer
corrections — and emit goals in ``detected`` state with their rationale and
evidence attached. A goal then walks an explicit lifecycle; only Aram moves
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from learning_os.learning_runtime import requirement_fingerprint


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


def detect_covering_routes_stale(
    *,
    changed_nodes: Sequence[str],
    route_covers: Mapping[str, Sequence[str]],
    known_ids: Sequence[str] = (),
    node_units: Mapping[str, str] | None = None,
) -> tuple[CandidateGoal, ...]:
    """Node semantics changed under covering routes: revalidate each route.

    A route whose covered nodes moved may now promise what the lecture no
    longer teaches. One goal per affected route, naming the changed nodes
    and the moved units behind them — the unit is the clustering key, so
    routes over the same moved unit print as the one decision they are.
    """
    changed = set(_strings(changed_nodes, "changed nodes"))
    owners = dict(node_units or {})
    goals = []
    for route_id in sorted(route_covers):
        covered = set(_strings(
            route_covers[route_id], f"covers for {route_id!r}"))
        hit = sorted(changed & covered)
        if not hit:
            continue
        moved = sorted({owners[node] for node in hit if node in owners})
        goal = _emit(
            "covering-routes-stale", str(route_id),
            f"Revalidate {route_id}: covered nodes changed",
            f"Covers {', '.join(hit)}, whose semantics moved; the route may "
            "promise what the lecture no longer teaches.",
            [f"route:{route_id}", *(f"node:{node}" for node in hit),
             *(f"unit:{unit}" for unit in moved)],
            known_ids,
        )
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


def detect_source_changed_under_claim(
    *,
    changed_sources: Sequence[str],
    claim_sources: Mapping[str, Sequence[str]],
    known_ids: Sequence[str] = (),
) -> tuple[CandidateGoal, ...]:
    """A changed source underpins live claims: re-examine each claim."""
    changed = set(_strings(changed_sources, "changed sources"))
    goals = []
    for claim_id in sorted(claim_sources):
        pinned = set(_strings(
            claim_sources[claim_id], f"sources for {claim_id!r}"))
        hit = sorted(changed & pinned)
        if not hit:
            continue
        goal = _emit(
            "source-changed-under-claim", str(claim_id),
            f"Re-examine {claim_id}: underpinning source changed",
            f"Pinned {', '.join(hit)}, which moved; the claim's lineage is "
            "stale until re-judged.",
            [f"claim:{claim_id}", *(f"source:{source}" for source in hit)],
            known_ids,
        )
        if goal is not None:
            goals.append(goal)
    return tuple(goals)


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
#: lineage goal fans out per claim over the same moved keys; a
#: changed-source goal fans out per claim over the same moved sources.
#: The covering-routes key is deliberately the unit, not the node set:
#: one decision is "this unit's nodes moved — revalidate its routes,"
#: and an exact node set would split that decision wherever one route
#: happens to also cover one more node.
CAUSE_PREFIXES = {
    "covering-routes-stale": "unit:",
    "lineage-stale": "moved:",
    "source-changed-under-claim": "source:",
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
    if detector == "source-changed-under-claim":
        return f"{len(members)} claims pin changed sources ({joined})"
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
    """Order clusters by exam proximity. A pure sort, not a cost model.

    ``cluster_modules`` names the modules behind each cluster id; a
    cluster with no known module is "everything else" (tier 4), never
    urgent and never retired. Ties break on cluster size, then id, so the
    same queue always prints in the same order.
    """
    known = dict(cluster_modules or {})
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
