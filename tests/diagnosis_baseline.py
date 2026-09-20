"""Phase-0 diagnostic baseline: what diagnosis costs before track #2.

Drives fourteen failure/success/adversarial scenarios through the real Core CLI on throwaway
mini repositories and records, per scenario, the ground truth (manually
labelled: no resolver exists yet), the evidence a diagnoser must open today,
and the commands diagnosis takes today. Also measures the Phase-1 trace
hook's CLI-level overhead (traced vs untraced writes on twin minis).

Read-only with respect to the live tree: every scenario runs in a scratch
mini repository under $TMPDIR. Writes a JSON report (default: out of the
repository, under /tmp) and prints a human-readable summary.

Usage:
    .venv/bin/python tests/diagnosis_baseline.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(ROOT / "tools"))

from conftest import build_mini_repo  # noqa: E402
from gateway_helpers import approved_v2_envelope  # noqa: E402
from repo_builders import add_curriculum  # noqa: E402

LOS = ROOT / "tools" / "los.py"

STAGE_PAYLOAD = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"}
STAGE_ARTIFACTS = ["unit-demo-l01", "study-map-demo-l01"]


def _fresh_mini(scratch: Path, name: str) -> Path:
    mini = build_mini_repo(scratch / name)
    add_curriculum(mini)
    return mini


#: The trace environment for the scenario currently running. Resolve mode
#: mints one operation per scenario and one fresh span per dispatch —
#: exactly the UI's send path (stable trace id, fresh span per attempt).
_TRACE_ENV: dict = {}


def _env() -> dict:
    import secrets

    env = dict(os.environ)
    env.update(_TRACE_ENV)
    trace_id = env.pop("TRACE_ID", None)
    if trace_id is not None and "LOS_TRACE_DEBUG_FILE" in env:
        env["TRACEPARENT"] = f"00-{trace_id}-{secrets.token_hex(8)}-01"
    return env


def _run_capability(root: Path, envelope: dict,
                    timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "capability",
         envelope["capability"], "--payload-file", "-"],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env(),
    )


def _response(proc: subprocess.CompletedProcess) -> dict | None:
    try:
        return json.loads(proc.stdout)
    except (json.JSONDecodeError, TypeError):
        return None


def _receipts(root: Path) -> list[Path]:
    return sorted((root / "operations" / "transactions").glob("transaction-*.yaml"))


def _ledger_keys(root: Path) -> list[str]:
    import yaml

    ledger = root / "operations" / "transactions" / "idempotency.yaml"
    if not ledger.is_file():
        return []
    return sorted(
        (yaml.safe_load(ledger.read_text(encoding="utf-8")) or {}).get("entries", {}))


def _seed_envelope(root: Path, key: str) -> dict:
    from gateway_helpers import request_artifact_id

    return approved_v2_envelope(
        root,
        capability="garden.seed.create",
        payload={"title": "Baseline probe", "text": "overhead probe seed"},
        artifact_ids=[request_artifact_id("garden.seed.create", key)],
        idempotency_key=key,
    )


# ---------------------------------------------------------------------------
# Scenarios. Each returns its report row; ground truth is labelled by hand.
# ---------------------------------------------------------------------------

def _s1_success(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s1")
    proc = _run_capability(mini, approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s1"))
    body = _response(proc)
    return {
        "scenario": "S1 successful stage.progress.update",
        "request_id": "request-baseline-s1",
        "idempotency_key": "baseline-s1",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body or {}).get("error"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": None, "canonical": "COMMITTED",
                         "ui": "SETTLED"},
        "evidence_opened_today": [
            "CLI stdout (GatewayResultV2 success)",
            "operations/transactions/transaction-*.yaml (receipt)",
            "generated/manifest.json snapshot_after (UI observation)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
    }


def _s2_stale_snapshot(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s2")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s2",
        expected_snapshot="sha256:" + "0" * 64)
    # Re-sign: the envelope helper signs the real snapshot, but the scenario
    # is a genuinely stale guard, so the approval must cover the stale value.
    from learning_os.contracts.gateway import intent_sha256

    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    proc = _run_capability(mini, envelope)
    body = _response(proc) or {}
    return {
        "scenario": "S2 stale snapshot refusal",
        "request_id": "request-baseline-s2",
        "idempotency_key": "baseline-s2",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.snapshot_guard",
                         "canonical": "NOT_COMMITTED", "ui": "REFUSED"},
        "evidence_opened_today": [
            "CLI stdout (typed STALE_SNAPSHOT error)",
            "generated/manifest.json _generated.snapshot_id (current guard)",
            "operations/transactions/ (absence of a receipt proves no commit)",
        ],
        "commands_run_today": ["los capability stage.progress.update …",
                               "los generate (refresh the guard, then retry)"],
    }


def _s3_revision_conflict(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s3")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s3")
    envelope["expected_revisions"]["study-map-demo-l01"] += 5
    from learning_os.contracts.gateway import intent_sha256

    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    proc = _run_capability(mini, envelope)
    body = _response(proc) or {}
    return {
        "scenario": "S3 revision conflict refusal",
        "request_id": "request-baseline-s3",
        "idempotency_key": "baseline-s3",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.revision_guard",
                         "canonical": "NOT_COMMITTED", "ui": "REFUSED"},
        "evidence_opened_today": [
            "CLI stdout (typed REVISION_CONFLICT error)",
            "operations/transactions/revisions.yaml (current guards)",
            "operations/transactions/ (absence of a receipt proves no commit)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
    }


def _s4_invalid_payload(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s4")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload={"unit_id": "x"},
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s4")
    proc = _run_capability(mini, envelope)
    body = _response(proc) or {}
    return {
        "scenario": "S4 invalid payload refusal",
        "request_id": "request-baseline-s4",
        "idempotency_key": "baseline-s4",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.admission",
                         "canonical": "NOT_COMMITTED", "ui": "REFUSED"},
        "evidence_opened_today": [
            "CLI stdout (typed INVALID_REQUEST error)",
            "system/schema/capabilities/<name>.schema.json (expected shape)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
    }


def _s5_child_failure(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s5")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s5")
    try:
        proc = subprocess.run(
            ["/nonexistent-python-9f3b", str(LOS), "--root", str(mini),
             "capability", envelope["capability"], "--payload-file", "-"],
            input=json.dumps(envelope), capture_output=True, text=True,
            timeout=60,
        )
        transport = f"exit={proc.returncode} stderr={proc.stderr.strip()[:120]}"
    except OSError as exc:
        transport = f"spawn failed: {exc}"
    return {
        "scenario": "S5 child-process failure",
        "request_id": "request-baseline-s5",
        "idempotency_key": "baseline-s5",
        "response": None,
        "transport_note": transport,
        "_mini": mini,
        "exit_code": None,
        "typed_error": None,
        "transport": transport,
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "ui.transport",
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "process exit code / spawn error (transport only)",
            "operations/transactions/ (receipt present => committed anyway)",
            "operations/transactions/idempotency.yaml (entry => seen before)",
        ],
        "commands_run_today": ["(retry the exact envelope: replay decides)"],
        "note": "nothing about the write is knowable from the transport; only "
                "a replay against the ledger resolves commit vs no-commit.",
    }


def _s6_lost_response(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s6")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s6")
    first = _run_capability(mini, envelope)
    # The response bytes are lost (pipe closed, window shut): the diagnoser
    # sees only "no readable answer", while canonical state has committed.
    assert first.returncode == 0, first.stderr
    replay = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         envelope["capability"], "--payload-file", "-", "--replay-only"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120, env=_env(),
    )
    replay_body = _response(replay) or {}
    return {
        "scenario": "S6 committed write with lost response, then replay-only",
        "request_id": "request-baseline-s6",
        "idempotency_key": "baseline-s6",
        "response": replay_body,
        "transport_note": "attempt 1 response discarded (simulated loss)",
        "_mini": mini,
        "exit_code": first.returncode,
        "typed_error": None,
        "response_seen_by_diagnoser": None,
        "replay_replayed": replay_body.get("replayed"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "ui.transport",
                         "canonical": "COMMITTED", "ui": "SETTLED"},
        "evidence_opened_today": [
            "(no readable response — the ambiguity window)",
            "replay-only response (replayed=true proves the earlier commit)",
            "operations/transactions/transaction-*.yaml (the one receipt)",
            "operations/transactions/idempotency.yaml (one entry)",
        ],
        "commands_run_today": ["los capability stage.progress.update …",
                               "los capability … --replay-only (same bytes)"],
    }


def _s7_projection_failure(scratch: Path) -> dict:
    # Every capability commit publishes the projection synchronously, so the
    # failure is injected before the write: generated/ is read-only when the
    # commit-time publication runs. Measured behavior: INTERNAL_FAILURE
    # (retryable), rollback, no receipt, no ledger entry.
    mini = _fresh_mini(scratch, "s7")
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        proc = _run_capability(mini, approved_v2_envelope(
            mini, capability="stage.progress.update",
            payload=dict(STAGE_PAYLOAD),
            artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s7"))
    finally:
        os.chmod(generated, 0o755)
    body = _response(proc) or {}
    return {
        "scenario": "S7 commit-time projection publication fails",
        "request_id": "request-baseline-s7",
        "idempotency_key": "baseline-s7",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "retryable": (body.get("error") or {}).get("retryable"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.projection",
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout (typed INTERNAL_FAILURE, retryable)",
            "operations/transactions/ (absence of a receipt proves rollback)",
            "operations/transactions/idempotency.yaml (no entry)",
            "generated/ permissions (the cause, found last)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
        "note": "the UI must read INTERNAL_FAILURE as ambiguous (not a "
                "definitive no-commit code) even though this instance "
                "rolled back — the resolver's job in Phase 3 is to sharpen "
                "exactly this case.",
    }


def _s8_recovery_replay(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s8")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s8")
    frozen = json.dumps(envelope)  # the persisted recovery bytes
    first = _run_capability(mini, json.loads(frozen))
    assert first.returncode == 0, first.stderr
    # "Restart": a new process resends the stored string, byte for byte.
    second = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         envelope["capability"], "--payload-file", "-"],
        input=frozen, capture_output=True, text=True, timeout=120, env=_env())
    second_body = _response(second) or {}
    return {
        "scenario": "S8 recovery replay of the persisted envelope bytes",
        "request_id": "request-baseline-s8",
        "idempotency_key": "baseline-s8",
        "response": second_body,
        "_mini": mini,
        "exit_code": second.returncode,
        "replay_replayed": second_body.get("replayed"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": None, "canonical": "COMMITTED",
                         "ui": "SETTLED"},
        "evidence_opened_today": [
            "recovery record envelope_json (the exact bytes resent)",
            "replay response (replayed=true, same transaction_id)",
            "operations/transactions/ (exactly one receipt)",
            "operations/transactions/idempotency.yaml (exactly one entry)",
        ],
        "commands_run_today": ["los capability stage.progress.update … (same bytes)"],
    }


def _s9_ambiguous_then_stale_recovery(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s9")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s9")
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        first = _run_capability(mini, envelope)
    finally:
        os.chmod(generated, 0o755)
    assert (_response(first) or {}).get("error", {}).get("code") == "INTERNAL_FAILURE", \
        (_response(first), first.stderr[-500:])
    # Recovery re-prepares the same request against a snapshot that is
    # already stale at arrival; the refusal proves nothing about attempt 1.
    import copy

    from learning_os.contracts.gateway import intent_sha256

    retry = copy.deepcopy(envelope)
    retry["expected_snapshot"] = "sha256:" + "0" * 64
    retry["approval"]["subject_sha256"] = intent_sha256(retry)
    second = _run_capability(mini, retry)
    body = _response(second) or {}
    return {
        "scenario": "S9 ambiguous attempt with stale recovery",
        "request_id": "request-baseline-s9",
        "idempotency_key": "baseline-s9",
        "response": body,
        "_mini": mini,
        "exit_code": second.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.projection",
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout, both attempts (INTERNAL_FAILURE, then STALE_SNAPSHOT)",
            "operations/transactions/ (no receipt for either attempt)",
        ],
        "commands_run_today": ["los capability stage.progress.update … (twice)"],
        "note": "the STALE_SNAPSHOT refusal covers only the recovery attempt; "
                "attempt 1 stays ambiguous, so the operation does too.",
    }


def _s10_ambiguous_then_revision_recovery(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s10")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s10")
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        first = _run_capability(mini, envelope)
    finally:
        os.chmod(generated, 0o755)
    assert (_response(first) or {}).get("error", {}).get("code") == "INTERNAL_FAILURE", \
        (_response(first), first.stderr[-500:])
    # A concurrent writer commits the same artifacts between the attempts. It
    # is a real second transaction under its own idempotency key — never a
    # hand-written ledger bump — so its startup drains attempt 1's stale
    # inflight journal exactly as production recovery would, then bumps the
    # guarded revisions. It re-affirms the already-active stage, leaving the
    # retry's completion domain-valid so the recovery dies on the revision
    # guard instead of on stage state. It runs untraced: it is a different
    # operation, so its spans belong to no diagnosis here. (A hand-written
    # ledger cannot model this: the next command startup would replay
    # attempt 1's stale rollback intent and delete the foreign write.)
    writer_payload = dict(STAGE_PAYLOAD)
    writer_payload["status"] = "active"
    writer = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=writer_payload,
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s10-writer")
    saved_trace = dict(_TRACE_ENV)
    _TRACE_ENV.clear()
    try:
        concurrent = _run_capability(mini, writer)
    finally:
        _TRACE_ENV.update(saved_trace)
    writer_body = _response(concurrent) or {}
    assert writer_body.get("ok") is True, \
        (writer_body, concurrent.stderr[-500:])
    assert writer_body.get("snapshot_after"), writer_body
    # Recovery re-prepares against the current snapshot but still carries the
    # pre-writer revision floor: the snapshot guard passes and the revision
    # guard refuses. The refusal proves nothing about attempt 1.
    import copy

    from learning_os.contracts.gateway import intent_sha256

    retry = copy.deepcopy(envelope)
    retry["expected_snapshot"] = writer_body["snapshot_after"]
    retry["approval"]["subject_sha256"] = intent_sha256(retry)
    second = _run_capability(mini, retry)
    body = _response(second) or {}
    assert (body.get("error") or {}).get("code") == "REVISION_CONFLICT", \
        (body, second.stderr[-500:])
    return {
        "scenario": "S10 ambiguous attempt with revision-conflict recovery",
        "request_id": "request-baseline-s10",
        "idempotency_key": "baseline-s10",
        "response": body,
        "_mini": mini,
        "exit_code": second.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.projection",
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout, all attempts (INTERNAL_FAILURE, writer ok, then "
            "REVISION_CONFLICT)",
            "operations/transactions/revisions.yaml (moved between attempts)",
        ],
        "commands_run_today": ["los capability stage.progress.update … (thrice)"],
        "note": "the REVISION_CONFLICT refusal covers only the recovery attempt; "
                "attempt 1 stays ambiguous, so the operation does too.",
    }


def _s11_ambiguous_then_invalid_recovery(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s11")
    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s11")
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        first = _run_capability(mini, envelope)
    finally:
        os.chmod(generated, 0o755)
    assert (_response(first) or {}).get("error", {}).get("code") == "INTERNAL_FAILURE", \
        (_response(first), first.stderr[-500:])
    # Recovery re-prepares with an approval flag in the payload instead of
    # the envelope; the gateway refuses the malformed retry, which proves
    # nothing about attempt 1.
    import copy

    from learning_os.contracts.gateway import intent_sha256

    retry = copy.deepcopy(envelope)
    retry["payload"]["approve"] = True
    retry["approval"]["subject_sha256"] = intent_sha256(retry)
    second = _run_capability(mini, retry)
    body = _response(second) or {}
    return {
        "scenario": "S11 ambiguous attempt with invalid recovery",
        "request_id": "request-baseline-s11",
        "idempotency_key": "baseline-s11",
        "response": body,
        "_mini": mini,
        "exit_code": second.returncode,
        "typed_error": (body.get("error") or {}).get("code"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": "core.projection",
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout, both attempts (INTERNAL_FAILURE, then INVALID_REQUEST)",
        ],
        "commands_run_today": ["los capability stage.progress.update … (twice)"],
    }


def _s12_tampered_receipt(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s12")
    proc = _run_capability(mini, approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s12"))
    body = _response(proc) or {}
    assert body.get("ok") is True, (body, proc.stderr[-500:])
    # Adversarial: the receipt's intent binding is edited after a genuine
    # commit. Execution says committed; the evidence can no longer be
    # trusted — contradiction, not proof.
    import yaml

    [receipt_path] = list(
        (mini / "operations" / "transactions").glob("transaction-*.yaml"))
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    intent = receipt["request"]["intent_sha256"]
    flipped = intent[:-1] + ("0" if intent[-1:] != "0" else "1")
    receipt["request"]["intent_sha256"] = flipped
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False),
                            encoding="utf-8")
    return {
        "scenario": "S12 committed write with tampered receipt",
        "request_id": "request-baseline-s12",
        "idempotency_key": "baseline-s12",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body or {}).get("error"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": None,
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout (GatewayResultV2 success: the tamper came after)",
            "operations/transactions/transaction-*.yaml (intent edited post-commit)",
            "los operations (strict verification fails: not COMMITTED)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
        "note": "no failure occurred during execution; the ambiguity is the "
                "tampered binding, found by verification, not by spans.",
    }


def _s13_tampered_ledger_row(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s13")
    proc = _run_capability(mini, approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s13"))
    body = _response(proc) or {}
    assert body.get("ok") is True, (body, proc.stderr[-500:])
    # Adversarial: the idempotency row is repointed at a transaction that
    # does not exist. The receipt is genuine; the ledger contradicts it.
    import yaml

    ledger_path = mini / "operations" / "transactions" / "idempotency.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger["entries"]["baseline-s13"]["transaction_id"] = \
        "transaction-00000000-000000-000"
    ledger_path.write_text(yaml.safe_dump(ledger, sort_keys=False),
                           encoding="utf-8")
    return {
        "scenario": "S13 committed write with tampered ledger row",
        "request_id": "request-baseline-s13",
        "idempotency_key": "baseline-s13",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body or {}).get("error"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": None,
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout (GatewayResultV2 success: the tamper came after)",
            "operations/transactions/idempotency.yaml (row repointed post-commit)",
            "los operations (strict verification fails: not COMMITTED)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
        "note": "no failure occurred during execution; the ambiguity is the "
                "tampered row, found by verification, not by spans.",
    }


def _s14_tampered_revision_floor(scratch: Path) -> dict:
    mini = _fresh_mini(scratch, "s14")
    proc = _run_capability(mini, approved_v2_envelope(
        mini, capability="stage.progress.update", payload=dict(STAGE_PAYLOAD),
        artifact_ids=list(STAGE_ARTIFACTS), idempotency_key="baseline-s14"))
    body = _response(proc) or {}
    assert body.get("ok") is True, (body, proc.stderr[-500:])
    # Adversarial: the live revision floor is dropped below what the genuine
    # receipt recorded. Revisions only ever increase, so this is provable
    # mutation of shared evidence.
    import yaml

    [receipt_path] = list(
        (mini / "operations" / "transactions").glob("transaction-*.yaml"))
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    artifact, recorded = next(iter(receipt["artifact_revisions"].items()))
    ledger_path = mini / "operations" / "transactions" / "revisions.yaml"
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    ledger["revisions"][artifact] = recorded["after"] - 1
    ledger_path.write_text(yaml.safe_dump(ledger, sort_keys=False),
                           encoding="utf-8")
    return {
        "scenario": "S14 committed write with tampered revision floor",
        "request_id": "request-baseline-s14",
        "idempotency_key": "baseline-s14",
        "response": body,
        "_mini": mini,
        "exit_code": proc.returncode,
        "typed_error": (body or {}).get("error"),
        "receipts": len(_receipts(mini)),
        "ledger_keys": _ledger_keys(mini),
        "ground_truth": {"failure_stage": None,
                         "canonical": "AMBIGUOUS", "ui": "BLOCKED"},
        "evidence_opened_today": [
            "CLI stdout (GatewayResultV2 success: the tamper came after)",
            "operations/transactions/revisions.yaml (floor dropped post-commit)",
            "los operations (strict verification fails: not COMMITTED)",
        ],
        "commands_run_today": ["los capability stage.progress.update …"],
        "note": "no failure occurred during execution; the ambiguity is the "
                "tampered floor, found by verification, not by spans.",
    }


SCENARIOS = (_s1_success, _s2_stale_snapshot, _s3_revision_conflict,
             _s4_invalid_payload, _s5_child_failure, _s6_lost_response,
             _s7_projection_failure, _s8_recovery_replay,
             _s9_ambiguous_then_stale_recovery,
             _s10_ambiguous_then_revision_recovery,
             _s11_ambiguous_then_invalid_recovery,
             _s12_tampered_receipt, _s13_tampered_ledger_row,
             _s14_tampered_revision_floor)


# ---------------------------------------------------------------------------
# Overhead probe: traced vs untraced writes on twin minis.
# ---------------------------------------------------------------------------

def _overhead_probe(scratch: Path, rounds: int = 6) -> dict:
    first = _fresh_mini(scratch, "ov-a")
    second = _fresh_mini(scratch, "ov-b")
    traced_ms, plain_ms = [], []
    for index in range(rounds):
        key = f"baseline-overhead-{index:03d}"
        env = {**os.environ,
               "TRACEPARENT": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(first), "capability",
             "garden.seed.create", "--payload-file", "-"],
            input=json.dumps(_seed_envelope(first, key)), capture_output=True,
            text=True, timeout=120, env=env)
        traced_ms.append((time.perf_counter() - started) * 1000.0)
        assert proc.returncode == 0, proc.stderr
        started = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(second), "capability",
             "garden.seed.create", "--payload-file", "-"],
            input=json.dumps(_seed_envelope(second, key)), capture_output=True,
            text=True, timeout=120)
        plain_ms.append((time.perf_counter() - started) * 1000.0)
        assert proc.returncode == 0, proc.stderr
    return {
        "rounds": rounds,
        "traced_median_ms": statistics.median(traced_ms),
        "untraced_median_ms": statistics.median(plain_ms),
        "delta_median_ms": statistics.median(traced_ms) - statistics.median(plain_ms),
    }


def _observe(mini: Path) -> str | None:
    """The projection-observation act: read the published snapshot id."""
    manifest = mini / "generated" / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        return (json.loads(manifest.read_text(encoding="utf-8"))
                .get("_generated", {}).get("snapshot_id"))
    except (ValueError, OSError):
        return None


def _resolve_row(row: dict, debug: Path) -> None:
    from learning_os.diagnostics.resolver import collect_authority, resolve

    mini = row.pop("_mini")
    records = []
    if debug.is_file():
        for line in debug.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    authority = collect_authority(
        mini,
        request_id=row["request_id"],
        idempotency_key=row["idempotency_key"],
        capability="stage.progress.update",
        response=row.get("response"),
        transport_error=row.get("transport_note"),
        observed_snapshot=_observe(mini),
    )
    row["diagnosis"] = resolve(records, authority).to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None)
    parser.add_argument("--resolve", action="store_true",
                        help="run the resolver prototype over every scenario")
    args = parser.parse_args()
    # Resolved like every real caller: write_target() grants authority to a
    # stable path, so an unresolved scratch (macOS /var TMPDIR) would read
    # as escaping its own repository under strict verification.
    scratch = Path(tempfile.mkdtemp(prefix="diagnosis-baseline-")).resolve()
    try:
        rows = []
        for scenario in SCENARIOS:
            debug = scratch / f"{scenario.__name__}.jsonl"
            if args.resolve:
                import secrets

                _TRACE_ENV.clear()
                _TRACE_ENV["TRACE_ID"] = secrets.token_hex(16)
                _TRACE_ENV["LOS_TRACE_DEBUG_FILE"] = str(debug)
            try:
                row = scenario(scratch)
            except Exception as exc:  # noqa: BLE001 — baseline must not abort
                rows.append({"scenario": scenario.__name__,
                             "status": f"error: {exc}"[:300]})
                continue
            if args.resolve and "_mini" in row:
                _resolve_row(row, debug)
            else:
                row.pop("_mini", None)
            rows.append(row)
        report = {
            "scenarios": rows,
            "effort": {
                "evidence_sources_opened_median": statistics.median(
                    len(row.get("evidence_opened_today", [])) for row in rows
                    if "evidence_opened_today" in row),
                "commands_run_median": statistics.median(
                    len(row.get("commands_run_today", [])) for row in rows
                    if "commands_run_today" in row),
                "first_failure_stage_accuracy": "manual labels only "
                    "(no resolver exists; Phase 3 target: 20/20 on faults)",
                "commit_outcome_accuracy": "manual labels only "
                    "(no resolver exists; Phase 3 target: 20/20 on faults)",
            },
            "trace_hook_overhead": _overhead_probe(scratch),
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else Path(f"/tmp/diagnosis-baseline-{stamp}.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("== Phase-0 diagnostic baseline ==")
    for row in report["scenarios"]:
        if "status" in row and "ground_truth" not in row:
            print(f"  {row['scenario']}: {row['status']}")
            continue
        truth = row["ground_truth"]
        print(f"  {row['scenario']}: exit={row.get('exit_code')} "
              f"error={row.get('typed_error')} receipts={row.get('receipts')} "
              f"-> {truth['failure_stage']}/{truth['canonical']}/{truth['ui']}")
        diagnosis = row.get("diagnosis")
        if diagnosis is not None:
            print(f"    diagnose: stage={diagnosis['first_failure_stage']} "
                  f"exec={diagnosis['execution_outcome']} "
                  f"canonical={diagnosis['canonical_outcome']} "
                  f"proj={diagnosis['projection_outcome']} "
                  f"recovery={diagnosis['recovery_requirement']}")
    effort = report["effort"]
    print(f"\nevidence sources opened (median): {effort['evidence_sources_opened_median']}")
    print(f"commands run (median): {effort['commands_run_median']}")
    overhead = report["trace_hook_overhead"]
    print(f"trace hook overhead: traced {overhead['traced_median_ms']:.0f} ms vs "
          f"untraced {overhead['untraced_median_ms']:.0f} ms "
          f"(delta {overhead['delta_median_ms']:+.1f} ms)")
    print(f"\nJSON report: {out}")


if __name__ == "__main__":
    main()
