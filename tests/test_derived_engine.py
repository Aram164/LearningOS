"""Derived evaluator: reuse, change pruning, and fail-closed misses.

Commit 2 of the incremental-computation plan. Pins the core guarantee —
a rebuilt dependency with an identical output does not invalidate its
dependents — plus the failure taxonomy: corrupt cache is a miss,
programming bugs (unknown nodes, cycles, missing producers) are loud.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import learning_os.derived.model as model_module
from learning_os.derived import (
    DerivedError,
    NodeSpec,
    Staging,
    commit_staging,
    evaluate,
    evaluate_many,
    read_state,
)


def _producer(root: Path, name: str = "producer.py") -> str:
    rel = f"tools/{name}"
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# v1\n", encoding="utf-8")
    return rel


def _spec(node_id: str, producer: str, **overrides) -> NodeSpec:
    args = {"id": node_id, "version": 1, "producer_files": (producer,)}
    args.update(overrides)
    return NodeSpec(**args)


def test_first_evaluation_builds_and_second_hits(tmp_path: Path):
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build(ctx):
        calls.append(ctx.spec.id)
        return {"value": 1}

    registry = {"a": (_spec("a", producer), build)}
    first = evaluate(tmp_path, "a", registry=registry, inputs={})
    assert (first.status, first.value) == ("rebuilt", {"value": 1})
    second = evaluate(tmp_path, "a", registry=registry, inputs={})
    assert (second.status, second.value) == ("hit", {"value": 1})
    assert second.output_sha256 == first.output_sha256
    assert calls == ["a"]


def test_changed_input_rebuilds(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (
        _spec("a", producer, direct_inputs=("doc",)),
        lambda ctx: {"seen": ctx.inputs["doc"]},
    )}
    first = evaluate(tmp_path, "a", registry=registry, inputs={"doc": "d1"})
    assert first.status == "rebuilt"
    assert evaluate(tmp_path, "a", registry=registry, inputs={"doc": "d1"}).status == "hit"
    third = evaluate(tmp_path, "a", registry=registry, inputs={"doc": "d2"})
    assert third.status == "rebuilt"
    assert third.value == {"seen": "d2"}


def test_changed_dependency_output_rebuilds_dependent(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {
        "a": (_spec("a", producer, direct_inputs=("doc",)),
              lambda ctx: {"seen": ctx.inputs["doc"]}),
        "b": (_spec("b", producer, dependencies=("a",)),
              lambda ctx: {"up": ctx.dependencies["a"].value}),
    }
    assert evaluate(tmp_path, "b", registry=registry, inputs={"doc": "d1"}).status == "rebuilt"
    assert evaluate(tmp_path, "b", registry=registry, inputs={"doc": "d1"}).status == "hit"
    third = evaluate(tmp_path, "b", registry=registry, inputs={"doc": "d2"})
    assert third.status == "rebuilt"
    assert third.value == {"up": {"seen": "d2"}}


def test_identical_rebuild_prunes_downstream_invalidation(tmp_path: Path):
    """The change-pruning guarantee: B rebuilds, C never notices."""
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build_a(ctx):
        calls.append("a")
        return {"seen": ctx.inputs["doc"]}

    def build_b(ctx):
        calls.append("b")
        # Normalizes its dependency away: same output whatever A says.
        return {"stable": True, "ignored": ctx.dependencies["a"].value["seen"][:0]}

    def build_c(ctx):
        calls.append("c")
        return {"up": ctx.dependencies["b"].value}

    registry = {
        "a": (_spec("a", producer, direct_inputs=("doc",)), build_a),
        "b": (_spec("b", producer, dependencies=("a",)), build_b),
        "c": (_spec("c", producer, dependencies=("b",)), build_c),
    }
    trace: list = []
    first = evaluate(tmp_path, "c", registry=registry, inputs={"doc": "d1"}, trace=trace)
    assert first.status == "rebuilt"
    assert [event.status for event in trace] == ["rebuilt", "rebuilt", "rebuilt"]
    assert calls == ["a", "b", "c"]

    trace.clear()
    calls.clear()
    second = evaluate(tmp_path, "c", registry=registry, inputs={"doc": "d2"}, trace=trace)
    assert second.status == "hit"
    assert second.value == first.value
    assert [(event.node, event.status) for event in trace] == [
        ("a", "rebuilt"), ("b", "rebuilt"), ("c", "hit")]
    assert [event.reason for event in trace] == [
        "node-key-changed-output-changed", "node-key-changed-output-same", "node-key-equal"]
    assert calls == ["a", "b"]


def test_rebuild_reasons_distinguish_changed_and_pruned(tmp_path: Path):
    """Refined reasons name the pruning verdict without affecting reuse."""
    producer = _producer(tmp_path)
    registry = {
        "same": (_spec("same", producer, direct_inputs=("doc",)), lambda ctx: {"fixed": 1}),
        "diff": (_spec("diff", producer, direct_inputs=("doc",)),
                 lambda ctx: {"seen": ctx.inputs["doc"]}),
    }
    for node in ("same", "diff"):
        assert evaluate(tmp_path, node, registry=registry, inputs={"doc": "d1"}).status == "rebuilt"
    trace: list = []
    assert evaluate(
        tmp_path, "same", registry=registry, inputs={"doc": "d2"}, trace=trace).status == "rebuilt"
    assert [(event.node, event.reason) for event in trace] == [
        ("same", "node-key-changed-output-same")]
    trace.clear()
    assert evaluate(
        tmp_path, "diff", registry=registry, inputs={"doc": "d2"}, trace=trace).status == "rebuilt"
    assert [(event.node, event.reason) for event in trace] == [
        ("diff", "node-key-changed-output-changed")]


def test_diamond_evaluates_shared_nodes_once(tmp_path: Path):
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build(ctx):
        calls.append(ctx.spec.id)
        return {"id": ctx.spec.id}

    registry = {
        name: (_spec(name, producer,
                      dependencies=tuple(deps)), build)
        for name, deps in (("a", ()), ("b", ("a",)), ("c", ("a",)), ("d", ("b", "c")))}
    assert evaluate(tmp_path, "d", registry=registry, inputs={}).status == "rebuilt"
    assert sorted(calls) == ["a", "b", "c", "d"]


def test_producer_change_rebuilds(tmp_path: Path):
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build(ctx):
        calls.append("a")
        return {"v": 1}

    registry = {"a": (_spec("a", producer), build)}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "hit"
    (tmp_path / producer).write_text("# v2\n", encoding="utf-8")
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    assert calls == ["a", "a"]


def test_engine_version_change_rebuilds(tmp_path: Path, monkeypatch):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"v": 1})}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "hit"
    monkeypatch.setattr(model_module, "ENGINE_VERSION", 999)
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"


def test_corrupt_cache_rebuilds_quietly(tmp_path: Path):
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build(ctx):
        calls.append("a")
        return {"v": 1}

    registry = {"a": (_spec("a", producer), build)}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    state = tmp_path / "generated" / "derived-state" / "state-v1.json"
    state.write_text("{corrupt", encoding="utf-8")
    trace: list = []
    assert evaluate(tmp_path, "a", registry=registry, inputs={}, trace=trace).status == "rebuilt"
    assert [event.reason for event in trace] == ["cache-miss"]
    assert calls == ["a", "a"]


def test_missing_blob_rebuilds_quietly(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"v": 1})}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    for blob in (tmp_path / "generated" / "derived-state" / "blobs").iterdir():
        blob.unlink()
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"


def test_unknown_node_is_loud(tmp_path: Path):
    with pytest.raises(DerivedError):
        evaluate(tmp_path, "nope", registry={}, inputs={})


def test_unknown_dependency_is_loud(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer, dependencies=("ghost",)), lambda ctx: {})}
    with pytest.raises(DerivedError):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_cycle_is_loud(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {
        "a": (_spec("a", producer, dependencies=("b",)), lambda ctx: {}),
        "b": (_spec("b", producer, dependencies=("a",)), lambda ctx: {}),
    }
    with pytest.raises(DerivedError, match="cycle"):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_registry_mismatch_is_loud(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("WRONG", producer), lambda ctx: {})}
    with pytest.raises(DerivedError, match="holds spec"):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_missing_input_digest_is_loud(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer, direct_inputs=("doc",)), lambda ctx: {})}
    with pytest.raises(DerivedError, match="missing input"):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_missing_producer_file_is_loud(tmp_path: Path):
    registry = {"a": (_spec("a", "tools/gone.py"), lambda ctx: {})}
    with pytest.raises(DerivedError, match="producer"):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_non_serializable_value_is_loud(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"bad": object()})}
    with pytest.raises(DerivedError):
        evaluate(tmp_path, "a", registry=registry, inputs={})


def test_evaluate_many_shares_one_session(tmp_path: Path):
    producer = _producer(tmp_path)
    calls: list[str] = []

    def build(ctx):
        calls.append(ctx.spec.id)
        return {"id": ctx.spec.id}

    registry = {
        "shared": (_spec("shared", producer), build),
        "left": (_spec("left", producer, dependencies=("shared",)), build),
        "right": (_spec("right", producer, dependencies=("shared",)), build),
    }
    trace: list = []
    results = evaluate_many(tmp_path, ["left", "right"], registry=registry, inputs={}, trace=trace)
    assert sorted(results) == ["left", "right"]
    assert sorted(calls) == ["left", "right", "shared"]
    assert [(event.node, event.status) for event in trace] == [
        ("shared", "rebuilt"), ("left", "rebuilt"), ("right", "rebuilt")]


def test_trace_is_optional_and_diagnostic_only(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"v": 1})}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"
    trace: list = []
    assert evaluate(tmp_path, "a", registry=registry, inputs={}, trace=trace).status == "hit"
    assert [(event.node, event.status, event.reason) for event in trace] == [
        ("a", "hit", "node-key-equal")]


def test_staging_defers_store_until_commit(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"v": 1})}
    staging = Staging()
    first = evaluate(tmp_path, "a", registry=registry, inputs={}, staging=staging)
    assert (first.status, first.value) == ("rebuilt", {"v": 1})
    assert read_state(tmp_path) == {}
    assert set(staging.pending) == {"a"}
    commit_staging(tmp_path, staging)
    assert staging.pending == {}
    second = evaluate(tmp_path, "a", registry=registry, inputs={})
    assert (second.status, second.value) == ("hit", {"v": 1})


def test_discarded_staging_leaves_the_store_empty(tmp_path: Path):
    producer = _producer(tmp_path)
    registry = {"a": (_spec("a", producer), lambda ctx: {"v": 1})}
    staging = Staging()
    assert evaluate(tmp_path, "a", registry=registry, inputs={}, staging=staging).status == "rebuilt"
    staging.discard()
    assert staging.pending == {}
    assert read_state(tmp_path) == {}
    assert evaluate(tmp_path, "a", registry=registry, inputs={}).status == "rebuilt"


def test_one_session_reads_the_state_index_once(tmp_path: Path, monkeypatch):
    import learning_os.derived.engine as engine_module

    producer = _producer(tmp_path)
    registry = {
        f"dep-{i}": (_spec(f"dep-{i}", producer), lambda ctx: {"i": ctx.spec.id})
        for i in range(5)
    }
    registry["root"] = (
        _spec("root", producer,
              dependencies=tuple(f"dep-{i}" for i in range(5))),
        lambda ctx: {"n": len(ctx.dependencies)},
    )
    assert evaluate(tmp_path, "root", registry=registry, inputs={}).status == "rebuilt"
    calls: list[Path] = []
    real_read_state = engine_module.read_state

    def counted(root: Path):
        calls.append(root)
        return real_read_state(root)

    monkeypatch.setattr(engine_module, "read_state", counted)
    assert evaluate(tmp_path, "root", registry=registry, inputs={}).status == "hit"
    assert len(calls) == 1
