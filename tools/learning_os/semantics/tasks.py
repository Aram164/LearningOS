"""Phase-4 agent tasks: logical plans and static dispatch.

A Task IR states *what* a task needs — read a node, compare coverage,
generate a candidate — with no model bound to any step. The physical
planner maps each step to deterministic tooling or to model work; the
static router dispatches each step under policy vetoes. Every step
carries an id, its dependencies, and a fixed effect class
(pure | judgment | mutation): mutations never reorder, judgments never
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
#: applies); model steps need interpretation. No step names a model —
#: models stay interchangeable executors behind this mapping.
STEP_EXECUTORS = {
    "read-knowledge-node": "deterministic",
    "read-existing-route": "deterministic",
    "acquire-source-evidence": "model",
    "compare-coverage": "deterministic",
    "verify-locator": "deterministic",
    "generate-candidate-change": "model",
    "review-evidence": "model",
    "apply-governed-mutation": "deterministic",
}

#: Steps no deterministic tool may take: each needs judgment, not lookup.
MODEL_ONLY_STEPS = frozenset({
    "acquire-source-evidence",
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
    "compare-coverage": "pure",
    "verify-locator": "pure",
    "generate-candidate-change": "judgment",
    "review-evidence": "judgment",
    "apply-governed-mutation": "mutation",
}

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
    """One physical step: logical content plus its executor class."""

    id: str
    kind: str
    detail: str
    executor: str
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
    never cycle.
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


def rewrite_pushdown(task_ir: TaskIR) -> TaskIR:
    """Predicate pushdown: deterministic steps run before model steps.

    Cheap checks first — a failed locator or an empty comparison aborts
    before any model spend. Dependencies are never violated: a step moves
    earlier only past steps it does not depend on, directly or
    transitively. Stable otherwise: class priority first, original order
    among the ready.
    """
    validate_ir(task_ir)
    remaining = list(task_ir.steps)
    emitted: set[str] = set()
    ordered: list[TaskStep] = []
    while remaining:
        ready = [step for step in remaining
                 if all(dep in emitted for dep in step.depends_on)]
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

    Exact-duplicate pure (kind, detail) steps collapse to their first
    occurrence; a surviving read that lost a duplicate is marked
    dossier-served, which is what the Phase 5 cache will honor.
    Mutations and judgments never deduplicate — two identical-looking
    operations are not interchangeable without a purity proof, and this
    rewrite does not invent one. Dependencies pointing at a dropped
    duplicate re-point at its survivor; the survivor waits for the union
    of both dependency sets, and the rebuilt plan revalidates.
    """
    validate_ir(task_ir)
    survivor: dict[tuple[str, str], TaskStep] = {}
    remap: dict[str, str] = {}
    kept: list[TaskStep] = []
    collapsed: set[tuple[str, str]] = set()
    for step in task_ir.steps:
        key = (step.kind, step.detail)
        if key in survivor and step.effect == "pure":
            first = survivor[key]
            merged = tuple(dict.fromkeys(first.depends_on + step.depends_on))
            survivor[key] = TaskStep(
                id=first.id, kind=first.kind, detail=first.detail,
                depends_on=merged, effect="pure",
                uses_dossier=first.uses_dossier,
            )
            collapsed.add(key)
            remap[step.id] = first.id
            continue
        if step.effect == "pure":
            survivor[key] = step
        kept.append(step)
    steps = []
    for step in kept:
        key = (step.kind, step.detail)
        current = survivor[key] if step.effect == "pure" else step
        deps = tuple(remap.get(dep, dep) for dep in current.depends_on)
        served = key in collapsed and current.kind in DOSSIER_SERVABLE
        if served or deps != current.depends_on:
            current = TaskStep(
                id=current.id, kind=current.kind, detail=current.detail,
                depends_on=deps, effect=current.effect,
                uses_dossier=True if served else current.uses_dossier,
            )
        steps.append(current)
    return validate_ir(TaskIR(task_type=task_ir.task_type, steps=tuple(steps)))


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
    return _cheapest_first(task_ir, priced)


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
