"""Phase-4 agent tasks: logical plans, static routing, and telemetry.

A Task IR states *what* a task needs — read a node, compare coverage,
generate a candidate — with no model bound to any step. The physical
planner maps each step to deterministic tooling or to model work; the
static router picks the cheapest feasible executor per step under policy
vetoes; telemetry records what actually happened so future weights can be
fitted instead of guessed. Learning stays off until the statistics are
significant — this phase ships the logical schema, the static cost table,
and the append-only log, nothing adaptive.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


class TaskError(ValueError):
    """A task plan, routing, or telemetry record cannot be read as written."""


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


# ---- static cost and routing --------------------------------------------------


#: Which telemetry rows may one day fit these weights.
COST_MODEL_VERSION = 1

#: Static-first weights. Tokens, latency, and three 0..1 risk terms add;
#: cache probability subtracts. These are placeholders with honest names,
#: not measurements — promotion to fitted weights waits on significant
#: telemetry, which is exactly what the log below collects.
COST_WEIGHTS = {
    "tokens": 1.0,
    "latency_ms": 0.5,
    "semantic_risk": 1000.0,
    "privacy_risk": 5000.0,
    "expected_repair": 2000.0,
    "cache_prob": 1500.0,
}


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TaskError(f"{label} must be a number, got {value!r}")
    return float(value)


def step_cost(
    *,
    tokens: float,
    latency_ms: float,
    semantic_risk: float,
    privacy_risk: float,
    expected_repair: float,
    cache_prob: float,
    weights: Mapping[str, float] = COST_WEIGHTS,
) -> float:
    """The static cost function.

    C = w_t·tokens + w_l·latency + w_r·semantic_risk + w_p·privacy +
        w_f·expected_repair − w_c·cache_prob. Risks and cache probability
    are 0..1; tokens and latency are non-negative. Out-of-range inputs
    refuse — a cost computed from nonsense ranks nonsense first.
    """
    counts = {
        "tokens": _number(tokens, "tokens"),
        "latency_ms": _number(latency_ms, "latency_ms"),
    }
    ratios = {
        "semantic_risk": _number(semantic_risk, "semantic_risk"),
        "privacy_risk": _number(privacy_risk, "privacy_risk"),
        "expected_repair": _number(expected_repair, "expected_repair"),
        "cache_prob": _number(cache_prob, "cache_prob"),
    }
    if counts["tokens"] < 0 or counts["latency_ms"] < 0:
        raise TaskError("tokens and latency are never negative")
    if any(not 0.0 <= value <= 1.0 for value in ratios.values()):
        raise TaskError("risk and cache terms live on 0..1")
    try:
        scale = {key: float(weights[key]) for key in COST_WEIGHTS}
    except (KeyError, TypeError, ValueError) as exc:
        raise TaskError(f"malformed cost weights: {exc}") from exc
    return (
        scale["tokens"] * counts["tokens"]
        + scale["latency_ms"] * counts["latency_ms"]
        + scale["semantic_risk"] * ratios["semantic_risk"]
        + scale["privacy_risk"] * ratios["privacy_risk"]
        + scale["expected_repair"] * ratios["expected_repair"]
        - scale["cache_prob"] * ratios["cache_prob"]
    )


@dataclass(frozen=True)
class RouterDecision:
    """One routed step: who runs it, at what cost, who was vetoed."""

    executor: str
    cost: float
    vetoed: tuple[str, ...] = ()


def route_step(
    *,
    step_kind: str,
    unpublished: bool,
    options: Sequence[Mapping[str, object]],
) -> RouterDecision:
    """Pick the cheapest feasible executor for one step.

    Policy vetoes, applied before price: unpublished material never leaves
    the repository (external executors infeasible), and model-only steps
    refuse deterministic executors. No feasible executor fails closed —
    there is no cheapest among the forbidden.
    """
    if step_kind not in STEP_KINDS:
        raise TaskError(f"unknown logical step: {step_kind!r}")
    if not options:
        raise TaskError("routing needs at least one executor option")
    feasible: list[tuple[str, float]] = []
    vetoed: list[str] = []
    for option in options:
        try:
            executor = option["executor"]
            external = option["external"]
            profile = {
                "tokens": _number(option["tokens"], "tokens"),
                "latency_ms": _number(option["latency_ms"], "latency_ms"),
                "semantic_risk": _number(option["semantic_risk"], "semantic_risk"),
                "privacy_risk": _number(option["privacy_risk"], "privacy_risk"),
                "expected_repair": _number(
                    option["expected_repair"], "expected_repair"),
                "cache_prob": _number(option["cache_prob"], "cache_prob"),
            }
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
        feasible.append((executor, step_cost(**profile)))
    if not feasible:
        raise TaskError(
            f"no feasible executor for {step_kind!r}: "
            f"vetoed {', '.join(vetoed) or 'none'}")
    executor, cost = min(feasible, key=lambda pair: (pair[1], pair[0]))
    return RouterDecision(
        executor=executor, cost=cost, vetoed=tuple(sorted(set(vetoed))))


# ---- telemetry: the append-only log future weights will fit -------------------


#: One JSON object per line. Git-tracked measurements: rotation policy
#: arrives with the learning it will one day justify.
TELEMETRY_RELATIVE = "operations/telemetry/log.jsonl"


@dataclass(frozen=True)
class TelemetryRecord:
    """What one task cost and whether it was accepted."""

    task_id: str
    task_type: str
    steps: tuple[str, ...]
    model: str
    tokens: int
    latency_ms: float
    tool_calls: tuple[str, ...]
    corrections: int
    accepted: bool
    cost_model_version: int = COST_MODEL_VERSION


def record_telemetry(
    *,
    task_id: str,
    task_type: str,
    steps: Sequence[str],
    model: str,
    tokens: int,
    latency_ms: float,
    tool_calls: Sequence[str] = (),
    corrections: int = 0,
    accepted: bool,
) -> TelemetryRecord:
    """Build one log row. Anything unmeasurable refuses the row."""
    if not isinstance(task_id, str) or not task_id.strip():
        raise TaskError("telemetry needs a non-empty task id")
    if not isinstance(task_type, str) or not task_type.strip():
        raise TaskError("telemetry needs a non-empty task type")
    if isinstance(steps, str) or not isinstance(steps, Sequence) or not steps:
        raise TaskError("telemetry needs at least one step kind")
    kinds = tuple(steps)
    if any(kind not in STEP_KINDS for kind in kinds):
        raise TaskError("telemetry steps use logical step kinds")
    if not isinstance(model, str) or not model.strip():
        raise TaskError("telemetry names its executor")
    if type(tokens) is not int or tokens < 0:
        raise TaskError("telemetry tokens are non-negative ints")
    latency = _number(latency_ms, "latency_ms")
    if latency < 0:
        raise TaskError("telemetry latency is never negative")
    if isinstance(tool_calls, str) or not isinstance(tool_calls, Sequence):
        raise TaskError("telemetry tool calls come as a list")
    tools = tuple(str(call) for call in tool_calls)
    if type(corrections) is not int or corrections < 0:
        raise TaskError("telemetry corrections are non-negative ints")
    if not isinstance(accepted, bool):
        raise TaskError("telemetry acceptance is a bool")
    return TelemetryRecord(
        task_id=task_id,
        task_type=task_type,
        steps=kinds,
        model=model,
        tokens=tokens,
        latency_ms=latency,
        tool_calls=tools,
        corrections=corrections,
        accepted=accepted,
    )


def telemetry_to_dict(record: TelemetryRecord) -> dict:
    """One JSON line, stable key order."""
    return {
        "task_id": record.task_id,
        "task_type": record.task_type,
        "steps": list(record.steps),
        "model": record.model,
        "tokens": record.tokens,
        "latency_ms": record.latency_ms,
        "tool_calls": list(record.tool_calls),
        "corrections": record.corrections,
        "accepted": record.accepted,
        "cost_model_version": record.cost_model_version,
    }


def telemetry_from_dict(row: dict) -> TelemetryRecord:
    """Rebuild a logged row. Raises TaskError on anything malformed."""
    try:
        return record_telemetry(
            task_id=row["task_id"],
            task_type=row["task_type"],
            steps=row["steps"],
            model=row["model"],
            tokens=row["tokens"],
            latency_ms=row["latency_ms"],
            tool_calls=row.get("tool_calls", ()),
            corrections=row.get("corrections", 0),
            accepted=row["accepted"],
        )
    except (KeyError, TypeError) as exc:
        raise TaskError(f"malformed telemetry row: {exc}") from exc


def append_telemetry(root: Path, record: TelemetryRecord) -> Path:
    """Append one row to the log, creating it. Returns the log path."""
    path = root / TELEMETRY_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(telemetry_to_dict(record),
                                ensure_ascii=False) + "\n")
    return path


def read_telemetry(root: Path) -> tuple[TelemetryRecord, ...]:
    """Read the whole log. A missing log is an empty one."""
    path = root / TELEMETRY_RELATIVE
    if not path.is_file():
        return ()
    records = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TaskError(f"cannot read {TELEMETRY_RELATIVE}: {exc}") from exc
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TaskError(
                f"{TELEMETRY_RELATIVE} line {number} is not JSON") from exc
        if not isinstance(row, dict):
            raise TaskError(
                f"{TELEMETRY_RELATIVE} line {number} is not an object")
        try:
            records.append(telemetry_from_dict(row))
        except TaskError as exc:
            raise TaskError(
                f"{TELEMETRY_RELATIVE} line {number}: {exc}") from exc
    return tuple(records)
