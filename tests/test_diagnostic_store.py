"""Research track #2, Phase 3B gate: bounded durable diagnostics.

The trace store must survive restarts, tolerate corruption, retain pinned
unresolved operations, stay out of the canonical fingerprint, and — above
all — never affect canonical behavior: persistence failure, a corrupt
store, a missing store, or a deleted store must all leave the gateway
exactly as correct as before.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from gateway_helpers import approved_v2_envelope

from learning_os.diagnostics.resolver import collect_authority, resolve
from learning_os.diagnostics.store import (
    prune_store,
    read_records,
    traces_path,
)
from learning_os.fingerprint import CANONICAL_ROOTS, canonical_fingerprint

TOOLS = Path(__file__).resolve().parent.parent / "tools"
LOS = TOOLS / "los.py"

STAGE_PAYLOAD = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"}
STAGE_ARTIFACTS = ["unit-demo-l01", "study-map-demo-l01"]


def _mini_with_curriculum(tmp_path: Path, name: str) -> Path:
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    mini = build_mini_repo(tmp_path / name)
    add_curriculum(mini)
    return mini


def _stage_write(mini: Path, key: str, **overrides):
    from learning_os.contracts.gateway import intent_sha256

    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update",
        payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key=key)
    envelope.update(overrides)
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "stage.progress.update", "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120)


def _seed_write(mini: Path, key: str):
    """A follow-up write that always applies (stages complete only once)."""
    from gateway_helpers import request_artifact_id

    envelope = approved_v2_envelope(
        mini, capability="garden.seed.create",
        payload={"title": "Store probe", "text": "follow-up write"},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key)
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "garden.seed.create", "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120)


def _read_in_fresh_process(mini: Path) -> list[dict]:
    """Restart simulation: a new interpreter reads the persisted store."""
    probe = (
        f"import json, sys; sys.path.insert(0, {str(TOOLS)!r}); "
        "from learning_os.diagnostics.store import read_records; "
        f"print(json.dumps(read_records({str(mini)!r})))")
    proc = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# Restart survival.
# ---------------------------------------------------------------------------

def test_successful_operation_survives_restart(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "restart-ok")
    proc = _stage_write(mini, "store-restart-ok")
    assert proc.returncode == 0, proc.stderr
    records = _read_in_fresh_process(mini)
    names = [record["name"] for record in records
             if record.get("kind") == "event"]
    assert "core.transaction.committed" in names
    assert "core.receipt.persisted" in names


def test_failed_operation_survives_restart(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "restart-fail")
    proc = _stage_write(mini, "store-restart-fail",
                        expected_snapshot="sha256:" + "0" * 64)
    assert proc.returncode == 3, proc.stdout
    records = _read_in_fresh_process(mini)
    failed = [record for record in records
              if record.get("name") == "core.stage.failed"]
    assert failed and failed[0]["stage"] == "core.snapshot_guard"


def test_replay_attempts_stay_linked_across_restart(tmp_path: Path):
    """Two attempts, two operations (a restart mints a fresh operation),
    one request: grouped by request id, the replay links to the original."""
    import secrets

    mini = _mini_with_curriculum(tmp_path, "restart-link")
    from gateway_helpers import approved_v2_envelope as envelope_for

    envelope = envelope_for(
        mini, capability="stage.progress.update",
        payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="store-link-1")
    frozen = json.dumps(envelope)
    for _ in range(2):
        parent = (f"00-{secrets.token_hex(16)}-{secrets.token_hex(8)}-01")
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini), "capability",
             "stage.progress.update", "--payload-file", "-"],
            input=frozen, capture_output=True, text=True, timeout=120,
            env={**os.environ, "TRACEPARENT": parent})
        assert proc.returncode == 0, proc.stderr
    records = _read_in_fresh_process(mini)
    assert len({record["op"] for record in records}) == 2
    authority = collect_authority(
        mini, request_id="request-store-link-1",
        idempotency_key="store-link-1",
        capability="stage.progress.update",
        response=json.loads(proc.stdout))
    diagnosis = resolve(records, authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert len(diagnosis.attempts) == 2
    assert diagnosis.attempts[1]["replay_of"] == diagnosis.attempts[0]["span"]


def test_s6_resolves_committed_from_persisted_store(tmp_path: Path):
    import secrets

    mini = _mini_with_curriculum(tmp_path, "store-s6")
    from gateway_helpers import approved_v2_envelope as envelope_for

    envelope = envelope_for(
        mini, capability="stage.progress.update",
        payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="store-s6")
    trace_id = secrets.token_hex(16)
    first = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "stage.progress.update", "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120,
        env={**os.environ,
             "TRACEPARENT": f"00-{trace_id}-{secrets.token_hex(8)}-01"})
    assert first.returncode == 0, first.stderr
    # Response lost; the replay carries a fresh span on the same operation.
    replay = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "stage.progress.update", "--payload-file", "-", "--replay-only"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120,
        env={**os.environ,
             "TRACEPARENT": f"00-{trace_id}-{secrets.token_hex(8)}-01"})
    replay_body = json.loads(replay.stdout)
    assert replay_body["replayed"] is True
    records = [record for record in _read_in_fresh_process(mini)
               if record["op"] == trace_id]
    authority = collect_authority(
        mini, request_id="request-store-s6", idempotency_key="store-s6",
        capability="stage.progress.update", response=replay_body,
        transport_error="attempt 1 response discarded")
    diagnosis = resolve(records, authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.first_failure_stage == "ui.transport"
    assert len(diagnosis.attempts) == 2


def test_s7_resolves_ambiguous_from_persisted_store(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-s7")
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        proc = _stage_write(mini, "store-s7")
    finally:
        os.chmod(generated, 0o755)
    body = json.loads(proc.stdout)
    assert body["error"]["code"] == "INTERNAL_FAILURE"
    records = _read_in_fresh_process(mini)
    authority = collect_authority(
        mini, request_id="request-store-s7", idempotency_key="store-s7",
        capability="stage.progress.update", response=body)
    diagnosis = resolve(records, authority)
    assert diagnosis.first_failure_stage == "core.projection"
    assert diagnosis.execution_outcome == "rolled-back"
    assert diagnosis.canonical_outcome == "AMBIGUOUS"
    assert diagnosis.recovery_requirement == "reconcile-exact-request"


# ---------------------------------------------------------------------------
# Corruption, absence, and failure invisibility.
# ---------------------------------------------------------------------------

def test_corrupt_store_leaves_canonical_behavior_untouched(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-corrupt")
    proc = _stage_write(mini, "store-corrupt-1")
    assert proc.returncode == 0, proc.stderr
    path = traces_path(mini)
    path.write_text(
        path.read_text(encoding="utf-8")
        + "this is not json\n"
        + '{"schema_version": 1, "conventions_version": 999}\n'
        + '{"truncated": true,\n',
        encoding="utf-8")
    reread = read_records(mini)
    assert reread, "valid lines must survive beside corrupt ones"
    proc = _seed_write(mini, "store-corrupt-2")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["ok"] is True


def test_missing_store_leaves_canonical_behavior_untouched(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-missing")
    assert read_records(mini) == []
    proc = _stage_write(mini, "store-missing-1")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["ok"] is True


def test_unwritable_store_never_rejects_a_write(tmp_path: Path):
    """Fault injection: persistence fails, the learner's write proceeds."""
    mini = _mini_with_curriculum(tmp_path, "store-readonly")
    store_dir = traces_path(mini).parent
    store_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(store_dir, 0o555)
    try:
        proc = _stage_write(mini, "store-readonly-1")
    finally:
        os.chmod(store_dir, 0o755)
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["ok"] is True
    assert (mini / body["receipt_path"]).is_file()


def test_deleted_store_keeps_learningos_fully_correct(tmp_path: Path):
    """Permanent invariant: the store is disposable without remainder."""
    mini = _mini_with_curriculum(tmp_path, "store-deleted")
    before = canonical_fingerprint(mini)
    proc = _stage_write(mini, "store-deleted-1")
    assert proc.returncode == 0, proc.stderr
    assert traces_path(mini).is_file()
    shutil.rmtree(traces_path(mini).parent)
    assert read_records(mini) == []
    # Canonical behavior is unchanged: the next write commits identically.
    proc = _seed_write(mini, "store-deleted-2")
    assert proc.returncode == 0, proc.stderr
    assert (mini / json.loads(proc.stdout)["receipt_path"]).is_file()
    # And the resolver degrades to authority-only verdicts, still correct.
    body = json.loads(proc.stdout)
    authority = collect_authority(
        mini, request_id="request-store-deleted-2",
        idempotency_key="store-deleted-2",
        capability="garden.seed.create", response=body)
    assert resolve([], authority).canonical_outcome == "COMMITTED"
    assert canonical_fingerprint(mini) != before  # the writes landed


# ---------------------------------------------------------------------------
# Fingerprint, retention, and payload privacy.
# ---------------------------------------------------------------------------

def test_store_is_outside_the_canonical_fingerprint(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-fingerprint")
    store = traces_path(mini).parent
    assert not any(
        store.resolve().is_relative_to((mini / root).resolve())
        for root in CANONICAL_ROOTS), "store must live outside every root"
    before = canonical_fingerprint(mini)
    proc = _stage_write(mini, "store-fingerprint-1")
    assert proc.returncode == 0, proc.stderr
    assert traces_path(mini).is_file()
    after_write = canonical_fingerprint(mini)
    with open(traces_path(mini), "a", encoding="utf-8") as handle:
        handle.write('{"injected": "junk"}\n')
    assert canonical_fingerprint(mini) == after_write != before


def test_retention_keeps_newest_and_never_evicts_pins(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-retain")
    path = traces_path(mini)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for index in range(600):
        op = f"{index:032x}"
        attrs = {"request_id": "request-pinned"} if index == 7 else {}
        lines.append(json.dumps({
            "schema_version": 1, "conventions_version": 2,
            "timestamp": float(index), "trace_id": op,
            "operation_id": op, "attempt_id": "a" * 16,
            "span_id": "a" * 16, "parent_span_id": None,
            "kind": "event", "name": "core.transaction.started",
            "stage": None, "status": "ok", "attributes": attrs,
        }))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = prune_store(mini, keep_last=500,
                         pinned_request_ids=frozenset({"request-pinned"}))
    assert result["kept_operations"] == 501
    assert result["evicted_operations"] == 99
    surviving = {record["trace_id"]
                 for record in (json.loads(line) for line in
                                path.read_text(encoding="utf-8").splitlines())}
    assert f"{7:032x}" in surviving, "the pinned operation must survive"
    assert f"{0:032x}" not in surviving, "the oldest operation must go"


def test_prune_tool_reports_and_supports_dry_run(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "store-prune-tool")
    proc = _stage_write(mini, "store-prune-1")
    assert proc.returncode == 0, proc.stderr
    before = traces_path(mini).read_text(encoding="utf-8")
    dry = subprocess.run(
        [sys.executable, str(TOOLS / "diagnostics_prune.py"),
         "--root", str(mini), "--dry-run", "--keep-last", "500"],
        capture_output=True, text=True, timeout=120)
    assert dry.returncode == 0, dry.stderr
    assert "would keep" in dry.stdout
    assert traces_path(mini).read_text(encoding="utf-8") == before
    real = subprocess.run(
        [sys.executable, str(TOOLS / "diagnostics_prune.py"),
         "--root", str(mini), "--keep-last", "500"],
        capture_output=True, text=True, timeout=120)
    assert real.returncode == 0, real.stderr
    assert "kept" in real.stdout


def test_no_learner_payload_text_reaches_the_store(tmp_path: Path):
    canary = "canary-payload-7f3e9a2b1c"
    mini = _mini_with_curriculum(tmp_path, "store-privacy")
    from gateway_helpers import approved_v2_envelope, request_artifact_id

    key = "store-privacy-1"
    envelope = approved_v2_envelope(
        mini, capability="garden.seed.create",
        payload={"title": f"Seed {canary}",
                 "text": f"freeform prose carrying {canary} inside"},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key)
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "garden.seed.create", "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120)
    assert proc.returncode == 0, proc.stderr
    stored = traces_path(mini).read_text(encoding="utf-8")
    assert canary not in stored
    assert "freeform prose" not in stored


def test_no_validation_body_reaches_the_store(tmp_path: Path):
    """Failure-path canary: validator prose is caller detail, not telemetry."""
    import pytest

    from learning_os.errors import TransactionFailure
    from learning_os.transactions import TransactionService

    canary = "canary-validation-8b4f2d1e9a"
    root = tmp_path / "store-validation-privacy"
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")
    service = TransactionService(root)
    with pytest.raises(TransactionFailure, match=canary):
        service.commit(
            capability="project.update", writes={target: "new\n"},
            artifact_ids=["project-demo"],
            validate_state=lambda: [
                f"fabricated issue quoting {canary} and 'learner prose here'"],
        )
    stored = traces_path(root).read_text(encoding="utf-8")
    assert canary not in stored
    assert "learner prose" not in stored
    failures = [
        record for record in read_records(root)
        if record.get("name") == "core.stage.failed"
        and record.get("stage") == "core.validation"
    ]
    assert failures, "the validation failure must stay on record"
    assert failures[0]["attrs"]["error"] == "canonical validation failed"
    assert failures[0]["attrs"]["issues"] == 1


def test_no_exception_body_reaches_the_store(tmp_path: Path):
    """Failure-path canary: exception text is caller detail, not telemetry.

    A chmod projection failure raises with an errno body quoting the absolute
    target path. The store may record the failure kind; the body must not
    persist anywhere in it.
    """
    from gateway_helpers import approved_v2_envelope, request_artifact_id

    mini = _mini_with_curriculum(tmp_path, "store-exception-privacy")
    key = "store-exception-privacy-1"
    envelope = approved_v2_envelope(
        mini, capability="garden.seed.create",
        payload={"title": "Seed probe", "text": "doomed write"},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key)
    generated = mini / "generated"
    os.chmod(generated, 0o555)
    try:
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini), "capability",
             "garden.seed.create", "--payload-file", "-"],
            input=json.dumps(envelope), capture_output=True, text=True,
            timeout=120)
    finally:
        os.chmod(generated, 0o755)
    body = json.loads(proc.stdout)
    assert body["error"]["code"] == "INTERNAL_FAILURE", body
    # The body the canary guards against: it must exist on the response (the
    # failure really happened) and must not exist in the store.
    assert "Permission denied" in body["error"]["message"], body
    stored = traces_path(mini).read_text(encoding="utf-8")
    assert "Permission denied" not in stored
    assert "[Errno" not in stored
    assert str(mini) not in stored
    failures = [
        record for record in read_records(mini)
        if record.get("name") == "core.stage.failed"
        and record.get("stage") == "core.projection"
    ]
    assert failures, "the projection failure must stay on record"
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",
                        failures[0]["attrs"]["error"]), failures[0]["attrs"]
