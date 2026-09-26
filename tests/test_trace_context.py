"""Research track #2, Phase 1: trace context crosses the process boundary.

The UI propagates one W3C-shaped traceparent per gateway dispatch as a child
environment variable; Core reads it at capability admission. These tests prove
the five Phase-1 properties from the research plan:

1. the child receives the intended context through the real CLI;
2. concurrent operations cannot cross contexts;
3. malformed context is ignored;
4. tracing present/absent leaves gateway behavior identical;
5. canonical state and fingerprints are untouched by trace activity.

Plus a cross-language test proving the UI's real ``GatewayClient`` sends a
context the real Core CLI receives (``obsidian-ui`` + Node required).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from gateway_helpers import (
    approved_v2_envelope,
    request_artifact_id,
)

from learning_os.diagnostics import conventions
from learning_os.diagnostics.context import (
    TraceContext,
    parse_traceparent,
    record_debug,
    trace_context_from_env,
)
from learning_os.fingerprint import canonical_fingerprint

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"
UI_ROOT = Path(__file__).resolve().parents[2] / "obsidian-ui"
TRACE_HARNESS = UI_ROOT / "tests" / "trace-context-harness.js"

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
SPAN_ID = "00f067aa0ba902b7"


def _seed_payload() -> dict:
    return {"title": "Trace probe", "text": "a seed Core plants while traced"}


def _run_traced(root: Path, envelope: dict,
                env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "capability",
         envelope["capability"], "--payload-file", "-"],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )


def _seed_envelope(root: Path, key: str) -> dict:
    return approved_v2_envelope(
        root,
        capability="garden.seed.create",
        payload=_seed_payload(),
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key,
    )


def _debug_records(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Parsing and vocabulary.
# ---------------------------------------------------------------------------

def test_parse_accepts_a_valid_w3c_traceparent():
    context = parse_traceparent(f"00-{TRACE_ID}-{SPAN_ID}-01")
    assert context == TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID,
                                   sampled=True)
    assert context.format() == f"00-{TRACE_ID}-{SPAN_ID}-01"


def test_parse_honours_the_sampling_flag():
    assert parse_traceparent(f"00-{TRACE_ID}-{SPAN_ID}-00").sampled is False


def test_parse_rejects_anything_not_strictly_shaped():
    for bad in (None, "", "  ", "00-xyz", f"01-{TRACE_ID}-{SPAN_ID}-01",
                f"00-{TRACE_ID}-{SPAN_ID}", f"00-{TRACE_ID}-{SPAN_ID}-01-00",
                f"00-{'0' * 32}-{SPAN_ID}-01", f"00-{TRACE_ID}-{'0' * 16}-01",
                f"00-{TRACE_ID.upper()}-{SPAN_ID}-01", 42):
        assert parse_traceparent(bad) is None, bad


def test_env_read_is_absent_or_malformed_safe():
    assert trace_context_from_env({}) is None
    assert trace_context_from_env({"TRACEPARENT": "garbage"}) is None
    assert trace_context_from_env(
        {"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01"}).trace_id == TRACE_ID


def test_env_reads_carry_no_state_between_calls():
    first = trace_context_from_env({"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01"})
    second = trace_context_from_env({"TRACEPARENT": f"00-{'1' * 32}-{'2' * 16}-01"})
    assert first.trace_id == TRACE_ID
    assert second.trace_id == "1" * 32
    assert trace_context_from_env({}) is None


def test_debug_sink_writes_ids_only_and_only_when_opted_in(tmp_path: Path):
    target = tmp_path / "trace.jsonl"
    record_debug(None, operation="capability")
    assert not target.exists()
    context = TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID)
    record_debug(context, operation="capability")  # sink env var unset
    assert _debug_records(target) == []


def test_debug_sink_record_shape_is_bounded(tmp_path: Path, monkeypatch):
    target = tmp_path / "trace.jsonl"
    monkeypatch.setenv("LOS_TRACE_DEBUG_FILE", str(target))
    record_debug(TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID),
                 operation="capability",
                 extra={"capability": "garden.seed.create"})
    (record,) = _debug_records(target)
    assert record["trace_id"] == TRACE_ID
    assert record["span_id"] == SPAN_ID
    assert record["operation"] == "capability"
    assert record["capability"] == "garden.seed.create"
    assert set(record) <= {"trace_id", "span_id", "sampled", "operation",
                           "pid", "capability"}, record


def test_debug_sink_failure_is_invisible(monkeypatch):
    monkeypatch.setenv("LOS_TRACE_DEBUG_FILE",
                       "/nonexistent-dir-9f3b/trace.jsonl")
    record_debug(TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID),
                 operation="capability")  # must not raise


def test_conventions_version_and_vocabularies_are_pinned():
    assert conventions.VOCAB_VERSION == 2
    assert conventions.SPAN_OPERATION in conventions.SPAN_NAMES
    assert conventions.EVENT_TRANSACTION_COMMITTED in conventions.EVENT_NAMES
    assert "core.snapshot_guard" in conventions.FAILURE_STAGES
    assert conventions.EVENT_CORE_TRANSACTION_COMMITTED in (
        conventions.COMMIT_BOUNDARY_EVENTS)
    assert conventions.EVENT_STAGE_FAILED in conventions.COMMIT_BOUNDARY_EVENTS
    assert conventions.CANONICAL_OUTCOMES == {
        "COMMITTED", "NOT_COMMITTED", "AMBIGUOUS"}
    assert conventions.UI_OUTCOMES == {
        "SETTLED", "BLOCKED", "REFUSED", "UNKNOWN"}


# ---------------------------------------------------------------------------
# Through the real CLI.
# ---------------------------------------------------------------------------

def test_child_receives_the_intended_context(mini_repo: Path, tmp_path: Path):
    debug = tmp_path / "trace.jsonl"
    key = "trace-context-probe-001"
    proc = _run_traced(
        mini_repo, _seed_envelope(mini_repo, key),
        {"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01",
         "LOS_TRACE_DEBUG_FILE": str(debug)},
    )
    assert proc.returncode == 0, proc.stderr
    records = _debug_records(debug)
    (record,) = [row for row in records
                 if row.get("operation") == "capability"]
    assert record["trace_id"] == TRACE_ID
    assert record["span_id"] == SPAN_ID
    assert record["capability"] == "garden.seed.create"
    phases = [row for row in records if row.get("v") == 2]
    assert phases, "the attempt span stream must also be recorded"
    # Parentage, never identity (JF-04): the child mints its own operation
    # and attempt spans and records the propagated pair as its parent.
    # Adopting the parent's ids merged unrelated requests sharing one
    # ambient trace into a single misreported operation.
    assert {row["op"] for row in phases} != {TRACE_ID}
    assert len({row["op"] for row in phases}) == 1
    assert SPAN_ID not in {row["span"] for row in phases}
    assert {row["parent_op"] for row in phases} == {TRACE_ID}
    assert {row["parent_span"] for row in phases} == {SPAN_ID}


def test_marked_context_is_adopted_as_operation_identity(
        mini_repo: Path, tmp_path: Path):
    """A LearningOS-owned marked context is adopted: one UI logical
    operation stays one LearningOS operation (JF-04, Option A).

    The Core attempt is a fresh child span of the UI dispatch span — same
    trace, W3C parentage intact — and request_id correlation is unchanged.
    """
    debug = tmp_path / "trace-owned.jsonl"
    key = "trace-owned-probe-001"
    envelope = _seed_envelope(mini_repo, key)
    proc = _run_traced(
        mini_repo, envelope,
        {"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01",
         conventions.TRACE_OWNERSHIP_ENV: TRACE_ID,
         "LOS_TRACE_DEBUG_FILE": str(debug)},
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["request_id"] == envelope["request_id"]
    records = _debug_records(debug)
    phases = [row for row in records if row.get("v") == 2]
    assert phases, "the attempt span stream must also be recorded"
    assert {row["op"] for row in phases} == {TRACE_ID}
    assert SPAN_ID not in {row["span"] for row in phases}
    assert {row["parent_op"] for row in phases} == {TRACE_ID}
    assert {row["parent_span"] for row in phases} == {SPAN_ID}


def test_mismatched_marker_is_parent_only(mini_repo: Path, tmp_path: Path):
    """A marker naming a different context does not adopt it (JF-04).

    Ownership binds the marker to the exact propagated trace: a stale or
    foreign marker leaves the context as ambient parentage.
    """
    debug = tmp_path / "trace-mismatch.jsonl"
    key = "trace-mismatch-probe-001"
    proc = _run_traced(
        mini_repo, _seed_envelope(mini_repo, key),
        {"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01",
         conventions.TRACE_OWNERSHIP_ENV: "f" * 32,
         "LOS_TRACE_DEBUG_FILE": str(debug)},
    )
    assert proc.returncode == 0, proc.stderr
    records = _debug_records(debug)
    phases = [row for row in records if row.get("v") == 2]
    assert phases, "the attempt span stream must also be recorded"
    assert {row["op"] for row in phases} != {TRACE_ID}
    assert len({row["op"] for row in phases}) == 1
    assert {row["parent_op"] for row in phases} == {TRACE_ID}
    assert {row["parent_span"] for row in phases} == {SPAN_ID}


def test_ownership_marker_rules():
    """Ownership requires an exact marker-to-trace match (JF-04)."""
    from learning_os.diagnostics.context import is_learningos_owned

    owned = TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID)
    assert is_learningos_owned(
        owned, {conventions.TRACE_OWNERSHIP_ENV: TRACE_ID})
    assert is_learningos_owned(
        owned, {conventions.TRACE_OWNERSHIP_ENV: f"  {TRACE_ID}  "})
    assert not is_learningos_owned(owned, {})
    assert not is_learningos_owned(
        owned, {conventions.TRACE_OWNERSHIP_ENV: "f" * 32})
    assert not is_learningos_owned(
        owned, {conventions.TRACE_OWNERSHIP_ENV: ""})
    assert not is_learningos_owned(None, {conventions.TRACE_OWNERSHIP_ENV: TRACE_ID})


def test_malformed_context_is_ignored(mini_repo: Path, tmp_path: Path):
    debug = tmp_path / "trace.jsonl"
    key = "trace-context-malformed-001"
    proc = _run_traced(
        mini_repo, _seed_envelope(mini_repo, key),
        {"TRACEPARENT": "not-a-traceparent",
         "LOS_TRACE_DEBUG_FILE": str(debug)},
    )
    assert proc.returncode == 0, proc.stderr
    # Ignored means never honored: no record may carry the garbage parent.
    # (Spans under a fresh operation are still recorded, exactly as for a
    # direct-CLI call with no parent at all.)
    assert "not-a-traceparent" not in debug.read_text(encoding="utf-8")


def _stable_response_shape(proc: subprocess.CompletedProcess) -> dict:
    """The response minus wall-clock-derived fields (ids, receipt paths)."""
    body = json.loads(proc.stdout)
    for node in (body, body.get("result") or {}):
        for volatile in ("transaction_id", "receipt_path", "seed_path"):
            node.pop(volatile, None)
    return body


def test_traced_and_untraced_writes_answer_identically(tmp_path: Path):
    from conftest import build_mini_repo

    first = build_mini_repo(tmp_path / "twin-a")
    second = build_mini_repo(tmp_path / "twin-b")
    key = "trace-context-parity-001"
    traced = _run_traced(
        first, _seed_envelope(first, key),
        {"TRACEPARENT": f"00-{TRACE_ID}-{SPAN_ID}-01"},
    )
    plain = _run_traced(second, _seed_envelope(second, key))
    assert traced.returncode == plain.returncode == 0, (
        traced.stderr, plain.stderr)
    assert _stable_response_shape(traced) == _stable_response_shape(plain)
    assert canonical_fingerprint(first) == canonical_fingerprint(second), (
        "trace activity must not change canonical bytes")


def test_concurrent_operations_cannot_cross_contexts(
        mini_repo: Path, tmp_path: Path):
    span_ids = [f"{index:016x}" for index in range(1, 5)]

    def attempt(index: int) -> None:
        key = f"trace-context-race-{index:03d}"
        debug = tmp_path / f"race-{index}.jsonl"
        _run_traced(
            mini_repo, _seed_envelope(mini_repo, key),
            {"TRACEPARENT": f"00-{TRACE_ID}-{span_ids[index]}-01",
             "LOS_TRACE_DEBUG_FILE": str(debug)},
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(attempt, range(4)))
    # Same parent trace, four attempts: each mints its own operation (JF-04).
    # Identity is per attempt; only the parent linkage is shared.
    seen_ops = set()
    for index in range(4):
        records = _debug_records(tmp_path / f"race-{index}.jsonl")
        assert records, f"attempt {index} recorded nothing"
        phases = [row for row in records if row.get("v") == 2]
        assert phases, f"attempt {index} recorded no phases"
        (op,) = {row["op"] for row in phases}
        assert op != TRACE_ID, f"attempt {index} adopted its parent trace"
        assert op not in seen_ops, f"attempt {index} shares an operation: {op}"
        seen_ops.add(op)
        spans = {row["span"] for row in phases}
        assert span_ids[index] not in spans, (
            f"attempt {index} adopted its parent span: {spans}")
        assert {row["parent_op"] for row in phases} == {TRACE_ID}
        assert {row["parent_span"] for row in phases} == {span_ids[index]}


def test_observation_hook_cost_is_negligible():
    context = TraceContext(trace_id=TRACE_ID, span_id=SPAN_ID)
    started = time.perf_counter()
    for _ in range(2000):
        trace_context_from_env({"TRACEPARENT": context.format()})
        record_debug(context, operation="capability")  # sink unset
    elapsed_ms = (time.perf_counter() - started) * 1000.0 / 2000
    assert elapsed_ms < 1.0, f"{elapsed_ms:.3f} ms per gateway admission"


# ---------------------------------------------------------------------------
# Cross-language: the real UI client against the real Core CLI.
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not TRACE_HARNESS.is_file() or shutil.which("node") is None,
    reason="the sibling obsidian-ui trace harness (or Node) is not available",
)
def test_ui_client_propagates_context_core_receives(
        repo_root: Path, tmp_path: Path):
    from conftest import build_mini_repo

    mini = build_mini_repo(tmp_path / "trace-e2e")
    debug = tmp_path / "e2e-trace.jsonl"
    proc = subprocess.run(
        ["node", str(TRACE_HARNESS), "--core-root", str(repo_root),
         "--repo", str(mini), "--python", sys.executable,
         "--debug-file", str(debug)],
        cwd=str(UI_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert proc.returncode == 0, (
        f"the UI trace harness failed\n--- stdout ---\n{proc.stdout}"
        f"\n--- stderr ---\n{proc.stderr}"
    )
    marker = [line for line in proc.stdout.splitlines()
              if line.startswith("HARNESS_RESULT ")]
    assert marker, f"the harness printed no result:\n{proc.stdout}"
    result = json.loads(marker[-1][len("HARNESS_RESULT "):])
    ui_names = [name for name in result["ui_events"]]
    assert ui_names == ["gateway.envelope.prepared",
                        "gateway.envelope.dispatched",
                        "ui.response.received",
                        "recovery.settled"], ui_names
    core_records = [record for record in _debug_records(debug)
                    if "trace_id" in record]
    (record,) = [record for record in core_records
                 if record.get("operation") == "capability"]
    assert record["trace_id"] == result["trace_id"], (
        "Core must receive the exact operation context the UI sent")
    assert record["span_id"] == result["span_id"]
    assert result["ok"] is True
