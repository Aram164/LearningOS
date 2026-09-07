"""Agent tasks: logical plans validate, rewrites preserve meaning,
and the router dispatches under policy vetoes with no prices.

The plan's Phase 4 validation in executable form, as amended: IR schema
validation, router unit tests on fixtures, no telemetry, no cost
function. Rewrite tests pin that cheaper never means different — order
and cache marks change, steps do not.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import (
    TaskError,
    TaskIR,
    TaskStep,
    plan_task,
    rewrite_cheapest_evidence_first,
    rewrite_dedup,
    rewrite_late_materialization,
    rewrite_pushdown,
    route_step,
    validate_ir,
)


def _ir(*kinds: str) -> TaskIR:
    return TaskIR(
        task_type="route-revalidation",
        steps=tuple(TaskStep(kind=kind, detail=f"{kind}-{n}")
                    for n, kind in enumerate(kinds)),
    )


def _read(detail: str) -> TaskStep:
    return TaskStep(kind="read-knowledge-node", detail=detail)


def _acquire(detail: str) -> TaskStep:
    return TaskStep(kind="acquire-source-evidence", detail=detail)


def test_ir_refuses_unknown_kinds_empty_plans_and_bare_steps():
    with pytest.raises(TaskError):
        validate_ir(TaskIR(task_type="t", steps=()))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(
            task_type="t",
            steps=(TaskStep(kind="ponder", detail="x"),)))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(
            task_type="t",
            steps=(TaskStep(kind="read-knowledge-node", detail="  "),)))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(task_type=" ", steps=(_read("a"),)))


def test_the_planner_binds_no_model():
    planned = plan_task(_ir(
        "read-knowledge-node", "acquire-source-evidence",
        "compare-coverage", "generate-candidate-change",
        "apply-governed-mutation",
    ))
    assert [(step.kind, step.executor) for step in planned] == [
        ("read-knowledge-node", "deterministic"),
        ("acquire-source-evidence", "model"),
        ("compare-coverage", "deterministic"),
        ("generate-candidate-change", "model"),
        ("apply-governed-mutation", "deterministic"),
    ]
    assert all("Muse" not in step.executor and "Claude" not in step.executor
               for step in planned)


def test_pushdown_runs_cheap_checks_first_stably():
    task_ir = TaskIR(task_type="t", steps=(
        TaskStep(kind="generate-candidate-change", detail="g"),
        _read("a"),
        TaskStep(kind="review-evidence", detail="r"),
        _read("b"),
    ))
    kinds = [step.kind for step in rewrite_pushdown(task_ir).steps]
    assert kinds == [
        "read-knowledge-node", "read-knowledge-node",
        "generate-candidate-change", "review-evidence",
    ]


def test_dedup_collapses_repeats_into_dossier_marks():
    task_ir = TaskIR(task_type="t", steps=(
        _read("a"), _acquire("deck.pdf"), _read("a"),
        TaskStep(kind="generate-candidate-change", detail="g"),
        TaskStep(kind="generate-candidate-change", detail="g"),
    ))
    rewritten = rewrite_dedup(task_ir)
    assert [(step.kind, step.detail, step.uses_dossier)
            for step in rewritten.steps] == [
        ("read-knowledge-node", "a", True),
        ("acquire-source-evidence", "deck.pdf", False),
        ("generate-candidate-change", "g", False),
    ]


def test_cheapest_evidence_first_orders_acquires_only():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf"),
        TaskStep(kind="compare-coverage", detail="compare-coverage"),
        _acquire("note.md"),
    ))
    rewritten = rewrite_cheapest_evidence_first(
        task_ir, {"heavy-deck.pdf": 90.0, "note.md": 2.0})
    # Non-acquire steps hold position; acquires slot in by ascending cost.
    assert [step.detail for step in rewritten.steps] == [
        "note.md", "compare-coverage", "heavy-deck.pdf",
    ]
    with pytest.raises(TaskError):
        rewrite_cheapest_evidence_first(task_ir, {"note.md": 1.0})


def test_late_materialization_defers_heavy_fetches_to_first_use():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf"),
        TaskStep(kind="verify-locator", detail="verify-locator"),
        _acquire("note.md"),
        TaskStep(kind="generate-candidate-change", detail="g"),
    ))
    rewritten = rewrite_late_materialization(task_ir, ["heavy-deck.pdf"])
    assert [step.detail for step in rewritten.steps] == [
        "verify-locator", "note.md", "heavy-deck.pdf", "g",
    ]


def test_late_materialization_without_consumer_parks_at_end():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf"), _read("a"),
    ))
    rewritten = rewrite_late_materialization(task_ir, ["heavy-deck.pdf"])
    assert [step.detail for step in rewritten.steps] == ["a", "heavy-deck.pdf"]


def _option(executor: str, external: bool) -> dict:
    return {"executor": executor, "external": external}


def test_the_router_picks_the_first_feasible_executor():
    """No prices: caller order decides among feasible executors."""
    decision = route_step(
        step_kind="review-evidence",
        unpublished=False,
        options=[_option("muse", False), _option("claude", False)],
    )
    assert decision.executor == "muse"
    assert decision.vetoed == ()
    flipped = route_step(
        step_kind="review-evidence",
        unpublished=False,
        options=[_option("claude", False), _option("muse", False)],
    )
    assert flipped.executor == "claude"


def test_unpublished_material_vetoes_external_models():
    """The proposal's own example: contributor models are infeasible here."""
    decision = route_step(
        step_kind="review-evidence",
        unpublished=True,
        options=[_option("external-model", True),
                 _option("local-model", False)],
    )
    assert decision.executor == "local-model"
    assert decision.vetoed == ("external-model",)


def test_model_only_steps_refuse_deterministic_executors():
    decision = route_step(
        step_kind="generate-candidate-change",
        unpublished=False,
        options=[_option("deterministic", False), _option("muse", False)],
    )
    assert decision.executor == "muse"
    assert decision.vetoed == ("deterministic",)
    with pytest.raises(TaskError):
        route_step(
            step_kind="generate-candidate-change",
            unpublished=False,
            options=[_option("deterministic", False)],
        )


def test_routing_refuses_nonsense():
    with pytest.raises(TaskError):
        route_step(step_kind="ponder", unpublished=False,
                   options=[_option("m", False)])
    with pytest.raises(TaskError):
        route_step(step_kind="review-evidence", unpublished=False, options=[])
    with pytest.raises(TaskError):
        route_step(step_kind="review-evidence", unpublished=False,
                   options=[{"executor": "m"}])
