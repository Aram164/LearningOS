"""Agent tasks: logical plans validate, rewrites preserve meaning,
and the router dispatches under policy vetoes with no prices.

The plan's Phase 4 validation in executable form, as amended and
hardened: IR schema validation (ids, effects, dependencies, acyclicity),
router unit tests on fixtures, no telemetry, no cost function. Rewrite
tests pin that cheaper never means different — and that a rewrite that
cannot prove order-preservation refuses instead of reordering.
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
        steps=tuple(TaskStep(id=f"s{n}", kind=kind, detail=f"{kind}-{n}",
                             effect=_effect(kind))
                    for n, kind in enumerate(kinds)),
    )


def _effect(kind: str) -> str:
    if kind == "apply-governed-mutation":
        return "mutation"
    if kind in ("generate-candidate-change", "review-evidence"):
        return "judgment"
    return "pure"


def _read(detail: str, sid: str, deps=()) -> TaskStep:
    return TaskStep(id=sid, kind="read-knowledge-node", detail=detail,
                    depends_on=tuple(deps), effect="pure")


def _acquire(detail: str, sid: str, deps=()) -> TaskStep:
    return TaskStep(id=sid, kind="acquire-source-evidence", detail=detail,
                    depends_on=tuple(deps), effect="pure")


def _judge(kind: str, detail: str, sid: str, deps=()) -> TaskStep:
    return TaskStep(id=sid, kind=kind, detail=detail,
                    depends_on=tuple(deps), effect="judgment")


def _apply(detail: str, sid: str, deps=()) -> TaskStep:
    return TaskStep(id=sid, kind="apply-governed-mutation", detail=detail,
                    depends_on=tuple(deps), effect="mutation")


def test_ir_refuses_unknown_kinds_empty_plans_and_bare_steps():
    with pytest.raises(TaskError):
        validate_ir(TaskIR(task_type="t", steps=()))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(
            task_type="t",
            steps=(TaskStep(id="s0", kind="ponder", detail="x",
                            effect="pure"),)))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(
            task_type="t",
            steps=(TaskStep(id="s0", kind="read-knowledge-node", detail="  ",
                            effect="pure"),)))
    with pytest.raises(TaskError):
        validate_ir(TaskIR(task_type=" ", steps=(_read("a", "s0"),)))


def test_ir_needs_ids_effects_and_sound_dependencies():
    with pytest.raises(TaskError):  # empty id
        validate_ir(TaskIR(task_type="t", steps=(
            TaskStep(id=" ", kind="read-knowledge-node", detail="a",
                     effect="pure"),)))
    with pytest.raises(TaskError):  # duplicate ids
        validate_ir(TaskIR(task_type="t", steps=(
            _read("a", "s0"), _read("b", "s0"))))
    with pytest.raises(TaskError):  # dangling dependency
        validate_ir(TaskIR(task_type="t", steps=(
            _read("a", "s0", deps=["ghost"]),)))
    with pytest.raises(TaskError):  # self-dependency
        validate_ir(TaskIR(task_type="t", steps=(
            _read("a", "s0", deps=["s0"]),)))
    with pytest.raises(TaskError):  # cycle
        validate_ir(TaskIR(task_type="t", steps=(
            _read("a", "s0", deps=["s1"]),
            _read("b", "s1", deps=["s0"]))))
    with pytest.raises(TaskError):  # purity is not self-asserted
        validate_ir(TaskIR(task_type="t", steps=(
            TaskStep(id="s0", kind="read-knowledge-node", detail="a",
                     effect="mutation"),)))
    with pytest.raises(TaskError):  # dependencies come as a list
        validate_ir(TaskIR(task_type="t", steps=(
            TaskStep(id="s0", kind="read-knowledge-node", detail="a",
                     depends_on="s1", effect="pure"),)))


def test_the_planner_binds_no_model_and_keeps_ids():
    planned = plan_task(_ir(
        "read-knowledge-node", "acquire-source-evidence",
        "compare-coverage", "generate-candidate-change",
        "apply-governed-mutation",
    ))
    assert [(step.id, step.kind, step.executor) for step in planned] == [
        ("s0", "read-knowledge-node", "deterministic"),
        ("s1", "acquire-source-evidence", "model"),
        ("s2", "compare-coverage", "deterministic"),
        ("s3", "generate-candidate-change", "model"),
        ("s4", "apply-governed-mutation", "deterministic"),
    ]
    assert all("Muse" not in step.executor and "Claude" not in step.executor
               for step in planned)


def test_pushdown_runs_cheap_checks_first_stably():
    task_ir = TaskIR(task_type="t", steps=(
        _judge("generate-candidate-change", "g", "s0"),
        _read("a", "s1"),
        _judge("review-evidence", "r", "s2"),
        _read("b", "s3"),
    ))
    kinds = [step.kind for step in rewrite_pushdown(task_ir).steps]
    assert kinds == [
        "read-knowledge-node", "read-knowledge-node",
        "generate-candidate-change", "review-evidence",
    ]


def test_pushdown_never_moves_a_step_past_its_dependencies():
    """The reviewer's scenario: apply is deterministic but waits its turn."""
    task_ir = TaskIR(task_type="t", steps=(
        _read("route", "s0"),
        _acquire("deck.pdf", "s1", deps=["s0"]),
        TaskStep(id="s2", kind="compare-coverage", detail="c",
                 depends_on=("s1",), effect="pure"),
        _judge("generate-candidate-change", "g", "s3", deps=["s2"]),
        _judge("review-evidence", "r", "s4", deps=["s3"]),
        _apply("m", "s5", deps=["s4"]),
    ))
    order = [step.id for step in rewrite_pushdown(task_ir).steps]
    assert order == ["s0", "s1", "s2", "s3", "s4", "s5"]


def test_dedup_collapses_pure_reads_into_dossier_marks():
    task_ir = TaskIR(task_type="t", steps=(
        _read("a", "s0"), _acquire("deck.pdf", "s1"), _read("a", "s2"),
        _judge("generate-candidate-change", "g", "s3"),
    ))
    rewritten = rewrite_dedup(task_ir)
    assert [(step.id, step.kind, step.detail, step.uses_dossier)
            for step in rewritten.steps] == [
        ("s0", "read-knowledge-node", "a", True),
        ("s1", "acquire-source-evidence", "deck.pdf", False),
        ("s3", "generate-candidate-change", "g", False),
    ]


def test_dedup_never_collapses_mutations_or_judgments():
    task_ir = TaskIR(task_type="t", steps=(
        _apply("m", "s0"), _apply("m", "s1"),
        _judge("review-evidence", "r", "s2"),
        _judge("review-evidence", "r", "s3"),
    ))
    rewritten = rewrite_dedup(task_ir)
    assert [step.id for step in rewritten.steps] == ["s0", "s1", "s2", "s3"]


def test_dedup_remaps_dependencies_onto_the_survivor():
    task_ir = TaskIR(task_type="t", steps=(
        _read("a", "s0"), _read("a", "s1"),
        TaskStep(id="s2", kind="compare-coverage", detail="c",
                 depends_on=("s1",), effect="pure"),
    ))
    rewritten = rewrite_dedup(task_ir)
    compare = [step for step in rewritten.steps if step.id == "s2"][0]
    assert compare.depends_on == ("s0",)


def test_cheapest_evidence_first_orders_acquires_only():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf", "s0"),
        TaskStep(id="s1", kind="compare-coverage",
                 detail="compare-coverage", effect="pure"),
        _acquire("note.md", "s2"),
    ))
    rewritten = rewrite_cheapest_evidence_first(
        task_ir, {"heavy-deck.pdf": 90.0, "note.md": 2.0})
    # Non-acquire steps hold position; acquires slot in by ascending cost.
    assert [step.detail for step in rewritten.steps] == [
        "note.md", "compare-coverage", "heavy-deck.pdf",
    ]
    with pytest.raises(TaskError):
        rewrite_cheapest_evidence_first(task_ir, {"note.md": 1.0})


def test_cheapest_evidence_first_refuses_priced_dependencies():
    """Prices may not decide an order that evidence depends on."""
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf", "s0"),
        TaskStep(id="s1", kind="compare-coverage", detail="c",
                 depends_on=("s0",), effect="pure"),
        _acquire("note.md", "s2"),
    ))
    with pytest.raises(TaskError):
        rewrite_cheapest_evidence_first(
            task_ir, {"heavy-deck.pdf": 90.0, "note.md": 2.0})


def test_late_materialization_defers_heavy_fetches_to_first_use():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf", "s0"),
        TaskStep(id="s1", kind="verify-locator", detail="verify-locator",
                 effect="pure"),
        _acquire("note.md", "s2"),
        _judge("generate-candidate-change", "g", "s3"),
    ))
    rewritten = rewrite_late_materialization(task_ir, ["heavy-deck.pdf"])
    assert [step.detail for step in rewritten.steps] == [
        "verify-locator", "note.md", "heavy-deck.pdf", "g",
    ]


def test_late_materialization_without_consumer_parks_at_end():
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf", "s0"), _read("a", "s1"),
    ))
    rewritten = rewrite_late_materialization(task_ir, ["heavy-deck.pdf"])
    assert [step.detail for step in rewritten.steps] == ["a", "heavy-deck.pdf"]


def test_late_materialization_refuses_a_breaking_move():
    verifier = TaskStep(id="s1", kind="verify-locator", detail="v",
                        depends_on=("s0",), effect="pure")
    task_ir = TaskIR(task_type="t", steps=(
        _acquire("heavy-deck.pdf", "s0"), verifier,
    ))
    with pytest.raises(TaskError):
        rewrite_late_materialization(task_ir, ["heavy-deck.pdf"])


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
