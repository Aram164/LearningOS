"""Phase-4 agent tasks: logical plans and static dispatch.

A Task IR states *what* a task needs — read a node, compare coverage,
generate a candidate — with no model bound to any step. The physical
planner maps each step to deterministic tooling or to model work; the
static router dispatches each step under policy vetoes. The four
rewrites cheapen plans without changing them. Nothing here tracks,
measures, or learns: no telemetry, no costs, no fitted weights.
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


@dataclass(frozen=True)
class TaskStep:
    """One logical step: what, precisely enough to deduplicate."""

    kind: str
    detail: str
    uses_dossier: bool = False


@dataclass(frozen=True)
class TaskIR:
    """A logical plan: ordered steps with no model bound."""

    task_type: str
    steps: tuple[TaskStep, ...]


@dataclass(frozen=True)
class PlannedStep:
    """One physical step: logical content plus its executor class."""

    kind: str
    detail: str
    executor: str
    uses_dossier: bool = False


def validate_ir(task_ir: TaskIR) -> TaskIR:
    """Accept a well-formed plan; refuse anything else, loudly."""
    if not isinstance(task_ir.task_type, str) or not task_ir.task_type.strip():
        raise TaskError("a task plan needs a non-empty task type")
    if not isinstance(task_ir.steps, tuple) or not task_ir.steps:
        raise TaskError("a task plan needs at least one step")
    for step in task_ir.steps:
        if not isinstance(step, TaskStep):
            raise TaskError("a task plan holds TaskStep rows only")
        if step.kind not in STEP_KINDS:
            raise TaskError(f"unknown logical step: {step.kind!r}")
        if not isinstance(step.detail, str) or not step.detail.strip():
            raise TaskError(f"step {step.kind!r} needs a non-empty detail")
    return task_ir


def plan_task(task_ir: TaskIR) -> tuple[PlannedStep, ...]:
    """Map a validated logical plan onto executor classes."""
    validate_ir(task_ir)
    return tuple(
        PlannedStep(
            kind=step.kind,
            detail=step.detail,
            executor=STEP_EXECUTORS[step.kind],
            uses_dossier=step.uses_dossier,
        )
        for step in task_ir.steps
    )


# ---- rewrites: cheaper plans, same meaning ----------------------------------


def rewrite_pushdown(task_ir: TaskIR) -> TaskIR:
    """Predicate pushdown: deterministic steps run before model steps.

    Cheap checks first — a failed locator or an empty comparison aborts
    before any model spend. Stable: relative order inside each class holds.
    """
    validate_ir(task_ir)
    ordered = tuple(
        step for step in task_ir.steps
        if STEP_EXECUTORS[step.kind] == "deterministic"
    ) + tuple(
        step for step in task_ir.steps
        if STEP_EXECUTORS[step.kind] != "deterministic"
    )
    return TaskIR(task_type=task_ir.task_type, steps=ordered)


def rewrite_dedup(task_ir: TaskIR) -> TaskIR:
    """Dedup via dossiers: repeated reads serve from cache, not re-read.

    Exact-duplicate (kind, detail) steps collapse to their first
    occurrence; a surviving read that lost a duplicate is marked
    dossier-served, which is what the Phase 5 cache will honor.
    """
    validate_ir(task_ir)
    seen: set[tuple[str, str]] = set()
    deduped: set[tuple[str, str]] = set()
    kept: list[TaskStep] = []
    for step in task_ir.steps:
        key = (step.kind, step.detail)
        if key in seen:
            deduped.add(key)
            continue
        seen.add(key)
        kept.append(step)
    return TaskIR(
        task_type=task_ir.task_type,
        steps=tuple(
            TaskStep(kind=step.kind, detail=step.detail, uses_dossier=True)
            if (step.kind, step.detail) in deduped
            and step.kind in {
                "read-knowledge-node", "read-existing-route",
                "acquire-source-evidence",
            }
            else step
            for step in kept
        ),
    )


def rewrite_cheapest_evidence_first(
    task_ir: TaskIR, costs: Mapping[str, float],
) -> TaskIR:
    """Cheapest evidence first: order acquisition by caller cost estimates.

    Only acquire-source-evidence steps move, stably, by ascending cost;
    every other step holds its position. Unknown costs refuse — an order
    nobody priced is not an optimization.
    """
    validate_ir(task_ir)
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
    fetches sit at the end. Relative order otherwise holds.
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
    return TaskIR(
        task_type=task_ir.task_type,
        steps=tuple(rest[:index] + movers + rest[index:]),
    )


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
