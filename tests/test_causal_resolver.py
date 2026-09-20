"""Research track #2, Phase 2A gate: one diagnose invocation per scenario.

The resolver prototype must reproduce the hand-labelled ground truth for all
eight baseline scenarios — first failure stage, canonical outcome, and
recovery requirement — from spans plus authority evidence alone, with no raw
log, receipt, or manifest inspection. Scenario S7 is pinned as an explicit
regression: execution says rolled-back, authority says nothing definitive,
so the answer stays AMBIGUOUS with reconciliation still required.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.diagnostics import conventions
from learning_os.diagnostics.resolver import (
    AuthorityEvidence,
    collect_authority,
    resolve,
)

TESTS = Path(__file__).resolve().parent
UI_CONTRACT = TESTS.parents[1] / "obsidian-ui" / "src" / "contracts" / "gateway-v2.ts"

EXPECTED = {
    # scenario: (stage, execution, canonical, projection, recovery)
    "S1": (None, "committed", "COMMITTED", "published", "none"),
    "S2": ("core.snapshot_guard", "refused", "NOT_COMMITTED", "skipped", "none"),
    "S3": ("core.revision_guard", "refused", "NOT_COMMITTED", "skipped", "none"),
    "S4": ("core.admission", "refused", "NOT_COMMITTED", "skipped", "none"),
    "S5": ("ui.transport", "transport-lost", "AMBIGUOUS", "unknown",
           "reconcile-exact-request"),
    "S6": ("ui.transport", "committed", "COMMITTED", "published", "none"),
    "S7": ("core.projection", "rolled-back", "AMBIGUOUS", "failed",
           "reconcile-exact-request"),
    "S8": (None, "committed", "COMMITTED", "published", "none"),
}


@pytest.fixture(scope="module")
def resolved(tmp_path_factory) -> dict:
    """One baseline run with the resolver; shared by the gate asserts."""
    out = tmp_path_factory.mktemp("resolver-gate") / "resolved.json"
    proc = subprocess.run(
        [sys.executable, str(TESTS / "diagnosis_baseline.py"),
         "--resolve", "--out", str(out)],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["scenarios"]) == 8, report
    return {row["scenario"].split(" ")[0]: row for row in report["scenarios"]}


def _verdict(row: dict) -> tuple:
    diagnosis = row["diagnosis"]
    return (
        diagnosis["first_failure_stage"],
        diagnosis["execution_outcome"],
        diagnosis["canonical_outcome"],
        diagnosis["projection_outcome"],
        diagnosis["recovery_requirement"],
    )


@pytest.mark.parametrize("code", sorted(EXPECTED))
def test_resolver_reproduces_ground_truth(resolved: dict, code: str):
    assert _verdict(resolved[code]) == EXPECTED[code]


def test_s7_rollback_is_observed_but_never_promoted(resolved: dict):
    """The Phase-0 refinement, pinned: rolled-back execution plus an
    INTERNAL_FAILURE response is AMBIGUOUS, and the exact request must stay
    recoverable. Telemetry informs; only authority decides."""
    diagnosis = resolved["S7"]["diagnosis"]
    assert diagnosis["first_failure_stage"] == "core.projection"
    assert diagnosis["execution_outcome"] == "rolled-back"
    assert diagnosis["canonical_outcome"] == "AMBIGUOUS"
    assert diagnosis["recovery_requirement"] == "reconcile-exact-request"
    assert diagnosis["authoritative_evidence"] == ["response:INTERNAL_FAILURE"]


def test_replay_links_attempts_causally(resolved: dict):
    attempts = resolved["S8"]["diagnosis"]["attempts"]
    assert len(attempts) == 2
    assert attempts[0]["replay_of"] is None
    assert attempts[1]["replay_of"] == attempts[0]["span"]


# ---------------------------------------------------------------------------
# Resolver rules, synthetic and fast.
# ---------------------------------------------------------------------------

def _authority(**overrides) -> AuthorityEvidence:
    base = {"request_id": "request-x", "idempotency_key": "x",
            "capability": "stage.progress.update"}
    base.update(overrides)
    return AuthorityEvidence(**base)


def _receipt(request_id: str = "request-x", key: str = "x") -> dict:
    return {"_path": "operations/transactions/transaction-1.yaml",
            "id": "transaction-1", "status": "committed",
            "request": {"request_id": request_id, "idempotency_key": key}}


def test_receipt_beats_telemetry_even_when_hooks_failed():
    """Committed-but-post-commit-hooks-failed carries a stage.failed event
    for core.commit — authority still proves COMMITTED."""
    records = [
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_CORE_TRANSACTION_COMMITTED, "ts": 1},
        {"v": 2, "kind": "event", "name": conventions.EVENT_STAGE_FAILED,
         "stage": "core.commit", "status": "error", "ts": 2},
    ]
    authority = _authority(
        receipts=[_receipt()],
        ledger={"x": {"transaction_id": "transaction-1"}},
        response_code="INTERNAL_FAILURE")
    diagnosis = resolve(records, authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.execution_outcome == "committed"


def test_telemetry_never_promotes_an_indeterminate_response():
    records = [
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_PROJECTION_STARTED, "ts": 1},
        {"v": 2, "kind": "event", "name": conventions.EVENT_STAGE_FAILED,
         "stage": "core.projection", "status": "error", "ts": 2},
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_ROLLBACK_COMPLETED, "status": "ok", "ts": 3},
    ]
    diagnosis = resolve(records, _authority(response_code="INTERNAL_FAILURE"))
    assert diagnosis.execution_outcome == "rolled-back"
    assert diagnosis.canonical_outcome == "AMBIGUOUS"
    assert diagnosis.recovery_requirement == "reconcile-exact-request"


def test_receipt_ledger_contradiction_is_ambiguous():
    authority = _authority(
        receipts=[_receipt()],
        ledger={"x": {"transaction_id": "transaction-OTHER"}},
        response_code="INTERNAL_FAILURE")
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "AMBIGUOUS"


def test_definitive_code_with_ledger_entry_is_ambiguous():
    authority = _authority(
        ledger={"x": {"transaction_id": "transaction-1"}},
        response_code="STALE_SNAPSHOT")
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "AMBIGUOUS"


def test_committed_but_unobserved_requires_verification():
    authority = _authority(
        receipts=[_receipt()],
        ledger={"x": {"transaction_id": "transaction-1"}},
        response_snapshot_after="sha256:abc",
        observed_snapshot=None)
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "verify-observation"


def test_old_records_are_ignored():
    diagnosis = resolve(
        [{"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736", "operation": "capability"}],
        _authority(response_code="STALE_SNAPSHOT"))
    assert diagnosis.first_failure_stage == "core.snapshot_guard"
    assert diagnosis.canonical_outcome == "NOT_COMMITTED"


def test_collector_reads_only(mini_repo: Path, tmp_path: Path):
    before = {path: path.read_bytes()
              for path in sorted(mini_repo.rglob("*")) if path.is_file()}
    collect_authority(mini_repo, request_id="request-absent",
                      idempotency_key="absent",
                      capability="stage.progress.update")
    after = {path: path.read_bytes()
             for path in sorted(mini_repo.rglob("*")) if path.is_file()}
    assert before == after


def test_definitive_codes_match_the_ui_contract():
    """Core and UI must retire exactly the same dead requests. The UI list
    is authoritative prose; this test fails the drift, not the intent."""
    if not UI_CONTRACT.is_file():
        pytest.skip("sibling obsidian-ui is not available")
    text = UI_CONTRACT.read_text(encoding="utf-8")
    block = re.search(
        r"DEFINITIVE_NO_COMMIT_CODES[^=]*=\s*\[(.*?)\];", text, re.DOTALL)
    assert block, "UI definitive list moved; update this test, not the rule"
    ui_codes = set(re.findall(r"'([A-Z_]+)'", block.group(1)))
    assert ui_codes, "no codes parsed from the UI contract"
    assert set(conventions.DEFINITIVE_NO_COMMIT_CODES) == ui_codes
