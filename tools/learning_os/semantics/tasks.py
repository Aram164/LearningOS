"""Phase-4 agent tasks: logical plans and static dispatch.

A Task IR states *what* a task needs — read a node, compare coverage,
generate a candidate — with no model bound to any step. The physical
planner maps each step to deterministic tooling or to model work; the
static router dispatches each step under policy vetoes. Every step
carries an id, its dependencies, and a fixed effect class
(pure | judgment | mutation): the tuple order itself must satisfy every
edge, mutations are barriers no rewrite may move past, judgments never
deduplicate, and the four rewrites cheapen plans only when they prove
the partial order survives — otherwise they refuse. Nothing here
tracks, measures, or learns: no telemetry, no costs, no fitted weights.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


class TaskError(ValueError):
    """A task plan or routing decision cannot be read as written."""


#: Logical step kinds. A plan is an ordered subset; the planner and the
#: rewrites only ever reorder or annotate, never invent.
STEP_KINDS = (
    "read-knowledge-node",
    "read-existing-route",
    "acquire-source-evidence",
    "compare-coverage",
    "verify-locator",
    "generate-candidate-change",
    "review-evidence",
    "apply-governed-mutation",
)

#: Physical mapping. Deterministic steps are pure computation over loaded
#: records (projection reads, predicate evaluation, set joins, gateway
#: applies) or retrieval of identified evidence; model steps need
#: interpretation. Coverage comparison judges semantic support, so it
#: runs on a model; acquiring evidence retrieves it, so deterministic
#: tooling may run that — interpretation belongs to the judgment step
#: that consumes the evidence. No step names a model: models stay
#: interchangeable executors behind this mapping.
STEP_EXECUTORS = {
    "read-knowledge-node": "deterministic",
    "read-existing-route": "deterministic",
    "acquire-source-evidence": "deterministic",
    "compare-coverage": "model",
    "verify-locator": "deterministic",
    "generate-candidate-change": "model",
    "review-evidence": "model",
    "apply-governed-mutation": "deterministic",
}

#: Steps no deterministic tool may take: each needs judgment, not lookup.
MODEL_ONLY_STEPS = frozenset({
    "compare-coverage",
    "generate-candidate-change",
    "review-evidence",
})

#: Effect classes. Only pure steps may deduplicate; mutations never
#: reorder; judgments never deduplicate.
EFFECTS = ("pure", "judgment", "mutation")

#: Effect class per step kind. Fixed per kind: a step may not declare
#: itself pure — the mapping refuses anything else.
STEP_EFFECTS = {
    "read-knowledge-node": "pure",
    "read-existing-route": "pure",
    "acquire-source-evidence": "pure",
    "compare-coverage": "judgment",
    "verify-locator": "pure",
    "generate-candidate-change": "judgment",
    "review-evidence": "judgment",
    "apply-governed-mutation": "mutation",
}

#: Pure steps whose duplicates may collapse: reads of clearly identified
#: records with immutable identity. Acquisitions are excluded on purpose —
#: fetching external evidence has no proved content identity, so two
#: identical-looking acquisitions are not interchangeable without one.
DEDUPABLE_READ_KINDS = frozenset({
    "read-knowledge-node",
    "read-existing-route",
    "verify-locator",
})

#: Steps whose surviving duplicates the dossier cache may serve.
DOSSIER_SERVABLE = frozenset({
    "read-knowledge-node",
    "read-existing-route",
    "acquire-source-evidence",
})


@dataclass(frozen=True)
class TaskStep:
    """One logical step: what, what it waits for, what it may do.

    ``effect`` is fixed per kind and refused otherwise — purity is not
    self-asserted. ``depends_on`` names step ids that run first; the
    rewrites may only produce orders honoring every edge.
    """

    id: str
    kind: str
    detail: str
    depends_on: tuple[str, ...] = ()
    effect: str = ""
    uses_dossier: bool = False


@dataclass(frozen=True)
class TaskIR:
    """A logical plan: ordered steps with no model bound."""

    task_type: str
    steps: tuple[TaskStep, ...]


@dataclass(frozen=True)
class PlannedStep:
    """One physical step: logical content plus its executor class.

    Dependencies and effects travel with the plan: execution order is
    meaningless without them, and no consumer may reorder blind.
    """

    id: str
    kind: str
    detail: str
    executor: str
    depends_on: tuple[str, ...] = ()
    effect: str = ""
    uses_dossier: bool = False


def _has_cycle(task_ir: TaskIR) -> bool:
    """True when no order satisfies the declared dependencies."""
    edges = {step.id: tuple(step.depends_on) for step in task_ir.steps}
    visiting: set[str] = set()
    settled: set[str] = set()

    def visit(node: str) -> bool:
        if node in settled:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        if any(visit(dep) for dep in edges[node]):
            return True
        visiting.discard(node)
        settled.add(node)
        return False

    return any(visit(step.id) for step in task_ir.steps)


def validate_ir(task_ir: TaskIR) -> TaskIR:
    """Accept a well-formed plan; refuse anything else, loudly.

    Beyond shapes, every step needs an id (order is meaningless without
    identity), a declared effect matching its kind (purity is not
    self-asserted), and dependencies that exist, never loop back, and
    never cycle. Finally the tuple order itself must satisfy every edge:
    the tuple is the execution order, and an edge pointing forward is a
    plan that cannot run.
    """
    if not isinstance(task_ir.task_type, str) or not task_ir.task_type.strip():
        raise TaskError("a task plan needs a non-empty task type")
    if not isinstance(task_ir.steps, tuple) or not task_ir.steps:
        raise TaskError("a task plan needs at least one step")
    ids: list[str] = []
    for step in task_ir.steps:
        if not isinstance(step, TaskStep):
            raise TaskError("a task plan holds TaskStep rows only")
        if step.kind not in STEP_KINDS:
            raise TaskError(f"unknown logical step: {step.kind!r}")
        if not isinstance(step.detail, str) or not step.detail.strip():
            raise TaskError(f"step {step.kind!r} needs a non-empty detail")
        if not isinstance(step.id, str) or not step.id.strip():
            raise TaskError("a plan step needs a non-empty id")
        if step.effect != STEP_EFFECTS[step.kind]:
            raise TaskError(
                f"step {step.id!r} declares {step.effect!r}: "
                f"{step.kind!r} is {STEP_EFFECTS[step.kind]!r}")
        if isinstance(step.depends_on, str) \
                or not isinstance(step.depends_on, Sequence):
            raise TaskError(
                f"step {step.id!r} declares dependencies as a list")
        if step.id in step.depends_on:
            raise TaskError(f"step {step.id!r} cannot depend on itself")
        ids.append(step.id)
    known = set(ids)
    if len(known) != len(ids):
        raise TaskError("plan step ids are unique")
    for step in task_ir.steps:
        for dep in step.depends_on:
            if dep not in known:
                raise TaskError(
                    f"step {step.id!r} depends on unknown {dep!r}")
    if _has_cycle(task_ir):
        raise TaskError("plan dependencies cycle: no order satisfies them")
    if not _respects_dependencies(task_ir):
        raise TaskError(
            "plan order violates dependencies: declare the order that runs")
    return task_ir


def plan_task(task_ir: TaskIR) -> tuple[PlannedStep, ...]:
    """Map a validated logical plan onto executor classes."""
    validate_ir(task_ir)
    return tuple(
        PlannedStep(
            id=step.id,
            kind=step.kind,
            detail=step.detail,
            executor=STEP_EXECUTORS[step.kind],
            depends_on=step.depends_on,
            effect=step.effect,
            uses_dossier=step.uses_dossier,
        )
        for step in task_ir.steps
    )


def _respects_dependencies(task_ir: TaskIR) -> bool:
    """True when every dependency edge runs in order."""
    position = {step.id: at for at, step in enumerate(task_ir.steps)}
    return all(
        position[dep] < position[step.id]
        for step in task_ir.steps
        for dep in step.depends_on
    )


# ---- rewrites: cheaper plans, same meaning ----------------------------------


def _mutation_barriers_hold(before: TaskIR, after: TaskIR) -> bool:
    """True when no mutation changed its ordinal relationships.

    For every surviving mutation, the set of steps before it must be
    unchanged (dropped steps are pure duplicates by construction, so
    only surviving ids compare). A mutation that moved past anything —
    or anything moved past it — fails.
    """
    before_ids = [step.id for step in before.steps]
    after_ids = [step.id for step in after.steps]
    surviving = set(after_ids)
    for step in after.steps:
        if step.effect != "mutation":
            continue
        was_before = {i for i in before_ids if i in surviving
                      and before_ids.index(i) < before_ids.index(step.id)}
        is_before = {i for i in after_ids
                     if after_ids.index(i) < after_ids.index(step.id)}
        if was_before != is_before:
            return False
    return True


def rewrite_pushdown(task_ir: TaskIR) -> TaskIR:
    """Predicate pushdown: deterministic steps run before model steps.

    Cheap checks first — a failed locator or an empty comparison aborts
    before any model spend. Dependencies are never violated, and
    mutations are barriers: a mutation emits only after everything
    originally before it, and nothing originally after it emits before
    it does. Stable otherwise: class priority first, original order
    among the ready.
    """
    validate_ir(task_ir)
    position = {step.id: at for at, step in enumerate(task_ir.steps)}
    remaining = list(task_ir.steps)
    emitted: set[str] = set()
    ordered: list[TaskStep] = []
    while remaining:
        ready = []
        for step in remaining:
            if any(dep not in emitted for dep in step.depends_on):
                continue
            preceding = [other for other in task_ir.steps
                         if position[other.id] < position[step.id]]
            if step.effect == "mutation":
                if any(other.id not in emitted for other in preceding):
                    continue
            elif any(other.id not in emitted
                     and other.effect == "mutation" for other in preceding):
                continue
            ready.append(step)
        ready.sort(key=lambda step: (
            0 if STEP_EXECUTORS[step.kind] == "deterministic" else 1,
            task_ir.steps.index(step),
        ))
        first = ready[0]
        ordered.append(first)
        emitted.add(first.id)
        remaining.remove(first)
    return TaskIR(task_type=task_ir.task_type, steps=tuple(ordered))


def rewrite_dedup(task_ir: TaskIR) -> TaskIR:
    """Dedup via dossiers: repeated pure reads serve from cache, not re-read.

    Collapse is scoped to mutation-free segments: the tuple splits at
    every mutation, because a read after a mutation observes a different
    world than the same read before it even when no dependency edge says
    so — tuple order is the barrier. Within one segment, exact-duplicate
    reads of clearly identified records collapse to their first
    occurrence; a surviving read that lost a duplicate is marked
    dossier-served, which is what the Phase 5 cache will honor.
    Acquisitions never collapse, nor do mutations or judgments — two
    identical-looking operations are not interchangeable without a purity
    proof, and this rewrite does not invent one. Dependencies pointing at
    a dropped duplicate re-point at its survivor in that segment; merging
    that would invert dependency order refuses instead of reordering, and
    the rebuilt plan revalidates.
    """
    validate_ir(task_ir)
    position = {step.id: at for at, step in enumerate(task_ir.steps)}
    segments: list[list[TaskStep]] = [[]]
    for step in task_ir.steps:
        segments[-1].append(step)
        if step.effect == "mutation":
            segments.append([])
    remap: dict[str, str] = {}
    collapsed: set[tuple[str, str]] = set()
    kept: list[TaskStep] = []
    for segment in segments:
        kept.extend(_dedup_segment(segment, position, remap, collapsed))
    steps = []
    for step in kept:
        deps = tuple(remap.get(dep, dep) for dep in step.depends_on)
        if deps != step.depends_on:
            step = TaskStep(
                id=step.id, kind=step.kind, detail=step.detail,
                depends_on=deps, effect=step.effect,
                uses_dossier=step.uses_dossier,
            )
        steps.append(step)
    return validate_ir(TaskIR(task_type=task_ir.task_type, steps=tuple(steps)))


def _dedup_segment(
    segment: Sequence[TaskStep],
    position: Mapping[str, int],
    remap: dict[str, str],
    collapsed: set[tuple[str, str]],
) -> list[TaskStep]:
    """Collapse one mutation-free segment; shared remap/collapsed grow."""
    survivor: dict[tuple[str, str], TaskStep] = {}
    kept: list[TaskStep] = []
    for step in segment:
        key = (step.kind, step.detail)
        if key in survivor and step.effect == "pure" \
                and step.kind in DEDUPABLE_READ_KINDS:
            first = survivor[key]
            merged = tuple(dict.fromkeys(first.depends_on + step.depends_on))
            late = [dep for dep in merged
                    if position[dep] >= position[first.id]]
            if late:
                raise TaskError(
                    f"dedup refuses: collapsing {step.id!r} into "
                    f"{first.id!r} would wait on "
                    f"{', '.join(late)} ordered after the survivor")
            survivor[key] = TaskStep(
                id=first.id, kind=first.kind, detail=first.detail,
                depends_on=merged, effect="pure",
                uses_dossier=first.uses_dossier,
            )
            collapsed.add(key)
            remap[step.id] = first.id
            continue
        if step.effect == "pure" and step.kind in DEDUPABLE_READ_KINDS:
            survivor[key] = step
        kept.append(step)
    out = []
    for step in kept:
        key = (step.kind, step.detail)
        if key in survivor:
            current = survivor[key]
            served = key in collapsed and current.kind in DOSSIER_SERVABLE
            if served and not current.uses_dossier:
                current = TaskStep(
                    id=current.id, kind=current.kind, detail=current.detail,
                    depends_on=current.depends_on, effect=current.effect,
                    uses_dossier=True,
                )
            out.append(current)
        else:
            out.append(step)
    return out


def rewrite_cheapest_evidence_first(
    task_ir: TaskIR, costs: Mapping[str, float],
) -> TaskIR:
    """Cheapest evidence first: order acquisition by caller cost estimates.

    Only acquire-source-evidence steps move, stably, by ascending cost;
    every other step holds its position. Unknown costs refuse — an order
    nobody priced is not an optimization. So does any dependency touching
    an acquisition: prices may not decide an order that evidence depends
    on. Declare the dependency and this rewrite steps aside.
    """
    validate_ir(task_ir)
    acquire_ids = {step.id for step in task_ir.steps
                   if step.kind == "acquire-source-evidence"}
    for step in task_ir.steps:
        if step.kind == "acquire-source-evidence" and step.depends_on:
            raise TaskError(
                f"cheapest-first refuses: acquisition {step.id!r} is ordered "
                "by dependencies, not caller prices")
        if set(step.depends_on) & acquire_ids:
            raise TaskError(
                f"cheapest-first refuses: {step.id!r} depends on evidence "
                "whose order prices must not decide")
    try:
        priced = {str(detail): float(cost) for detail, cost in costs.items()}
    except (TypeError, ValueError) as exc:
        raise TaskError(f"malformed evidence costs: {exc}") from exc
    acquires = [
        step for step in task_ir.steps if step.kind == "acquire-source-evidence"
    ]
    for step in acquires:
        if step.detail not in priced:
            raise TaskError(f"no cost estimate for {step.detail!r}")
    candidate = _cheapest_first(task_ir, priced)
    if not _mutation_barriers_hold(task_ir, candidate):
        raise TaskError(
            "cheapest-first refuses: the reorder crosses a mutation")
    return candidate


def _cheapest_first(task_ir: TaskIR, priced: Mapping[str, float]) -> TaskIR:
    """Stable merge: non-acquire steps stay; acquires slot in by cost."""
    ranked = sorted(
        (step for step in task_ir.steps if step.kind == "acquire-source-evidence"),
        key=lambda step: priced[step.detail],
    )
    iterator = iter(ranked)
    return TaskIR(
        task_type=task_ir.task_type,
        steps=tuple(
            next(iterator) if step.kind == "acquire-source-evidence" else step
            for step in task_ir.steps
        ),
    )


def rewrite_late_materialization(
    task_ir: TaskIR, heavy_details: Sequence[str],
) -> TaskIR:
    """Late materialization: heavy fetches move just before first use.

    Large materials (deck PDFs, datasets) are fetched right before the
    first step that consumes evidence — generate, review, or apply — so
    cheap checks and light evidence run first. With no consumer, heavy
    fetches sit at the end. Relative order otherwise holds. The candidate
    order must honor every dependency edge; a move that breaks one
    refuses instead of silently violating it.
    """
    validate_ir(task_ir)
    if isinstance(heavy_details, str):
        raise TaskError("heavy details come as a list, never one string")
    try:
        heavy = set(heavy_details)
    except TypeError as exc:
        raise TaskError(f"malformed heavy details: {exc}") from exc
    movers = [
        step for step in task_ir.steps
        if step.kind == "acquire-source-evidence" and step.detail in heavy
    ]
    rest = [
        step for step in task_ir.steps
        if not (step.kind == "acquire-source-evidence"
                and step.detail in heavy)
    ]
    consumers = {
        "generate-candidate-change", "review-evidence", "apply-governed-mutation",
    }
    index = next(
        (at for at, step in enumerate(rest) if step.kind in consumers),
        len(rest),
    )
    candidate = TaskIR(
        task_type=task_ir.task_type,
        steps=tuple(rest[:index] + movers + rest[index:]),
    )
    if not _respects_dependencies(candidate):
        raise TaskError(
            "late materialization refuses: the move breaks dependencies")
    if not _mutation_barriers_hold(task_ir, candidate):
        raise TaskError(
            "late materialization refuses: the move crosses a mutation")
    return candidate


# ---- static dispatch ----------------------------------------------------------


@dataclass(frozen=True)
class RouterDecision:
    """One routed step: who runs it, who was vetoed."""

    executor: str
    vetoed: tuple[str, ...] = ()


def route_step(
    *,
    step_kind: str,
    unpublished: bool,
    options: Sequence[Mapping[str, object]],
) -> RouterDecision:
    """Dispatch one step under policy vetoes; no prices, no tracking.

    Policy vetoes, applied before anything else: unpublished material
    never leaves the repository (external executors infeasible), and
    model-only steps refuse deterministic executors. No feasible
    executor fails closed. Among feasible executors the first option
    wins, so callers order options by preference — the router itself
    keeps no costs and learns nothing.
    """
    if step_kind not in STEP_KINDS:
        raise TaskError(f"unknown logical step: {step_kind!r}")
    if not options:
        raise TaskError("routing needs at least one executor option")
    feasible: list[str] = []
    vetoed: list[str] = []
    for option in options:
        try:
            executor = option["executor"]
            external = option["external"]
        except (KeyError, TypeError) as exc:
            raise TaskError(f"malformed executor option: {exc}") from exc
        if not isinstance(executor, str) or not executor:
            raise TaskError("executor options name their executor")
        if not isinstance(external, bool):
            raise TaskError("executor options mark external as bool")
        if unpublished and external:
            vetoed.append(executor)
            continue
        if executor == "deterministic" and step_kind in MODEL_ONLY_STEPS:
            vetoed.append(executor)
            continue
        feasible.append(executor)
    if not feasible:
        raise TaskError(
            f"no feasible executor for {step_kind!r}: "
            f"vetoed {', '.join(vetoed) or 'none'}")
    return RouterDecision(
        executor=feasible[0], vetoed=tuple(sorted(set(vetoed))))
