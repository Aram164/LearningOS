"""Agent tasks: logical plans validate, rewrites preserve meaning,
the router obeys policy before price, and telemetry appends honestly.

The plan's Phase 4 validation in executable form: IR schema validation,
router unit tests on fixtures, telemetry append tests. Rewrite tests pin
that cheaper never means different — order and cache marks change, steps
do not.
"""

from __future__ import annotations

import pytest

from learning_os.semantics import (
    COST_MODEL_VERSION,
    TaskError,
    TaskIR,
    TaskStep,
    append_telemetry,
    plan_task,
    read_telemetry,
    record_telemetry,
    rewrite_cheapest_evidence_first,
    rewrite_dedup,
    rewrite_late_materialization,
    rewrite_pushdown,
    route_step,
    step_cost,
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


def _option(executor: str, external: bool, **profile) -> dict:
    base = {"tokens": 100, "latency_ms": 50, "semantic_risk": 0.1,
            "privacy_risk": 0.0, "expected_repair": 0.0, "cache_prob": 0.0}
    base.update(profile)
    return {"executor": executor, "external": external, **base}


def test_the_router_picks_the_cheapest_feasible_executor():
    decision = route_step(
        step_kind="review-evidence",
        unpublished=False,
        options=[_option("muse", False, tokens=500),
                 _option("claude", False, tokens=100)],
    )
    assert decision.executor == "claude"
    assert decision.vetoed == ()
    assert decision.cost == step_cost(
        tokens=100, latency_ms=50, semantic_risk=0.1, privacy_risk=0.0,
        expected_repair=0.0, cache_prob=0.0)


def test_unpublished_material_vetoes_external_models():
    """The proposal's own example: contributor models are infeasible here."""
    decision = route_step(
        step_kind="review-evidence",
        unpublished=True,
        options=[_option("external-model", True, tokens=1),
                 _option("local-model", False, tokens=900)],
    )
    assert decision.executor == "local-model"
    assert decision.vetoed == ("external-model",)


def test_model_only_steps_refuse_deterministic_executors():
    decision = route_step(
        step_kind="generate-candidate-change",
        unpublished=False,
        options=[_option("deterministic", False, tokens=0, latency_ms=0,
                         semantic_risk=0.0),
                 _option("muse", False)],
    )
    assert decision.executor == "muse"
    assert decision.vetoed == ("deterministic",)
    with pytest.raises(TaskError):
        route_step(
            step_kind="generate-candidate-change",
            unpublished=False,
            options=[_option("deterministic", False)],
        )


def test_cache_probability_lowers_cost():
    plain = step_cost(tokens=100, latency_ms=50, semantic_risk=0.1,
                      privacy_risk=0.0, expected_repair=0.0, cache_prob=0.0)
    cached = step_cost(tokens=100, latency_ms=50, semantic_risk=0.1,
                       privacy_risk=0.0, expected_repair=0.0, cache_prob=0.9)
    assert cached < plain


def test_cost_and_routing_refuse_nonsense():
    with pytest.raises(TaskError):
        step_cost(tokens=-1, latency_ms=0, semantic_risk=0, privacy_risk=0,
                  expected_repair=0, cache_prob=0)
    with pytest.raises(TaskError):
        step_cost(tokens=0, latency_ms=0, semantic_risk=2, privacy_risk=0,
                  expected_repair=0, cache_prob=0)
    with pytest.raises(TaskError):
        route_step(step_kind="ponder", unpublished=False,
                   options=[_option("m", False)])
    with pytest.raises(TaskError):
        route_step(step_kind="review-evidence", unpublished=False, options=[])
    with pytest.raises(TaskError):
        route_step(step_kind="review-evidence", unpublished=False,
                   options=[{"executor": "m"}])


def test_telemetry_appends_and_reads_back(tmp_path):
    assert read_telemetry(tmp_path) == ()
    first = record_telemetry(
        task_id="task-001", task_type="route-revalidation",
        steps=["read-existing-route", "review-evidence"],
        model="claude", tokens=800, latency_ms=1200.5,
        tool_calls=["los.py inspect"], corrections=1, accepted=True)
    second = record_telemetry(
        task_id="task-002", task_type="route-revalidation",
        steps=["read-existing-route"], model="deterministic",
        tokens=0, latency_ms=30.0, accepted=False)
    append_telemetry(tmp_path, first)
    append_telemetry(tmp_path, second)
    assert read_telemetry(tmp_path) == (first, second)
    assert first.cost_model_version == COST_MODEL_VERSION


def test_telemetry_refuses_unmeasurable_rows():
    with pytest.raises(TaskError):
        record_telemetry(
            task_id="t", task_type="t", steps=["read-existing-route"],
            model="m", tokens=-5, latency_ms=0.0, accepted=True)
    with pytest.raises(TaskError):
        record_telemetry(
            task_id="t", task_type="t", steps=["ponder"],
            model="m", tokens=0, latency_ms=0.0, accepted=True)
    with pytest.raises(TaskError):
        record_telemetry(
            task_id="t", task_type="t", steps=["read-existing-route"],
            model="m", tokens=0, latency_ms=0.0, corrections=-1,
            accepted=True)


def test_telemetry_refuses_a_corrupt_log(tmp_path):
    log = tmp_path / "operations" / "telemetry"
    log.mkdir(parents=True)
    (log / "log.jsonl").write_text(
        '{"task_id": "broken"}\n', encoding="utf-8")
    with pytest.raises(TaskError):
        read_telemetry(tmp_path)
