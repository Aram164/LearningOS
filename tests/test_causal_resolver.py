"""Research track #2, Phase 2A gate: one diagnose invocation per scenario.

The resolver prototype must reproduce the hand-labelled ground truth for all
fourteen baseline scenarios — first failure stage, canonical outcome, and
recovery requirement — from spans plus authority evidence alone, with no raw
log, receipt, or manifest inspection. Scenario S7 is pinned as an explicit
regression: execution says rolled-back, authority says nothing definitive,
so the answer stays AMBIGUOUS with reconciliation still required. S9-S11
extend the pin to recovery attempts: a definitive refusal on attempt 2
never proves an ambiguous attempt 1 wrote nothing. S12-S14 extend it to
adversarial evidence: spans say committed, but tampered bindings fail
strict verification, so the answer stays AMBIGUOUS.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from learning_os.contracts.gateway import GatewayRequestContext
from learning_os.diagnostics import conventions
from learning_os.diagnostics.resolver import (
    AuthorityEvidence,
    collect_authority,
    resolve,
)
from learning_os.transactions import TransactionService

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
    "S9": ("core.projection", "rolled-back", "AMBIGUOUS", "failed",
           "reconcile-exact-request"),
    "S10": ("core.projection", "rolled-back", "AMBIGUOUS", "failed",
            "reconcile-exact-request"),
    "S11": ("core.projection", "rolled-back", "AMBIGUOUS", "failed",
            "reconcile-exact-request"),
    "S12": (None, "committed", "AMBIGUOUS", "published",
            "reconcile-exact-request"),
    "S13": (None, "committed", "AMBIGUOUS", "published",
            "reconcile-exact-request"),
    "S14": (None, "committed", "AMBIGUOUS", "published",
            "reconcile-exact-request"),
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
    assert len(report["scenarios"]) == 14, report
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


def _commit_capture_v2(mini_repo: Path, key: str, request_id: str):
    """One genuine v2 commit whose evidence strictly verifies."""
    target = mini_repo / f"work/inbox/{key}.md"
    context = GatewayRequestContext(
        request_id=request_id, idempotency_key=key,
        capability="capture.create", channel="codex",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
    )
    result = TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={target: "committed\n"},
        artifact_ids=[f"capture:{key}"],
        expected_revisions={f"capture:{key}": 0},
        gateway_request=context,
    )
    return context, result


def test_receipt_beats_telemetry_even_when_hooks_failed(mini_repo: Path):
    """Committed-but-post-commit-hooks-failed carries a stage.failed event
    for core.commit — verified authority still proves COMMITTED."""
    _commit_capture_v2(mini_repo, "hooks-proof", "request-hooks-proof")
    records = [
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_CORE_TRANSACTION_COMMITTED, "ts": 1},
        {"v": 2, "kind": "event", "name": conventions.EVENT_STAGE_FAILED,
         "stage": "core.commit", "status": "error", "ts": 2},
    ]
    authority = collect_authority(
        mini_repo, request_id="request-hooks-proof",
        idempotency_key="hooks-proof", capability="capture.create",
        response={"error": {"code": "INTERNAL_FAILURE"}})
    assert authority.verification_error is None
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


def test_projection_failed_is_definitive_after_complete_rollback():
    """Matrix row two: rolled-back execution plus PROJECTION_FAILED is
    NOT_COMMITTED with nothing left to reconcile — the rollback proof,
    not the telemetry, decides."""
    records = [
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_PROJECTION_STARTED, "ts": 1},
        {"v": 2, "kind": "event", "name": conventions.EVENT_STAGE_FAILED,
         "stage": "core.projection", "status": "error", "ts": 2},
        {"v": 2, "kind": "event",
         "name": conventions.EVENT_ROLLBACK_COMPLETED, "status": "ok", "ts": 3},
    ]
    diagnosis = resolve(records, _authority(response_code="PROJECTION_FAILED"))
    assert diagnosis.first_failure_stage == "core.projection"
    assert diagnosis.execution_outcome == "rolled-back"
    assert diagnosis.canonical_outcome == "NOT_COMMITTED"
    assert diagnosis.projection_outcome == "failed"
    assert diagnosis.recovery_requirement == "none"


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


def test_committed_but_unobserved_requires_verification(mini_repo: Path):
    _, result = _commit_capture_v2(mini_repo, "unobserved", "request-unobserved")
    authority = collect_authority(
        mini_repo, request_id="request-unobserved",
        idempotency_key="unobserved", capability="capture.create",
        response={"snapshot_after": result.snapshot_after})
    assert authority.verification_error is None
    assert authority.observed_snapshot is None
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


def test_manifest_covers_receipt_positions_the_live_manifest():
    """Settlement is positional: at-or-past the commit settles (JF-19)."""
    from learning_os.diagnostics.resolver import manifest_covers_receipt

    receipts = [
        {"id": "transaction-20260101-000001-001", "snapshot_after": "sha256:aaa"},
        {"id": "transaction-20260101-000002-001", "snapshot_after": "sha256:bbb"},
    ]
    assert manifest_covers_receipt(receipts, "sha256:aaa", "sha256:aaa")
    assert manifest_covers_receipt(receipts, "sha256:bbb", "sha256:aaa")
    assert not manifest_covers_receipt(receipts, "sha256:aaa", "sha256:bbb")
    assert not manifest_covers_receipt(receipts, "sha256:hand-made", "sha256:aaa")
    assert not manifest_covers_receipt(receipts, None, "sha256:aaa")
    assert not manifest_covers_receipt([], "sha256:bbb", "sha256:aaa")


def test_superseded_commit_settles_without_exact_observation():
    """A commit the live manifest has moved past is settled (JF-19)."""
    committed = {"_path": "operations/transactions/transaction-1.yaml"}
    settled = resolve([], _authority(verified_receipt=committed,
                                     response_snapshot_after="sha256:aaa",
                                     superseded_snapshot=True))
    assert settled.canonical_outcome == "COMMITTED"
    assert settled.recovery_requirement == "none"
    assert any("past this commit" in reason for reason in settled.reasons)
    behind = resolve([], _authority(verified_receipt=committed,
                                    response_snapshot_after="sha256:aaa",
                                    superseded_snapshot=False))
    assert behind.recovery_requirement == "verify-observation"


def test_contract_only_drift_settles_without_exact_observation():
    """An unchained manifest over unchanged data is settled, with the
    contract-only reason — not verify-observation."""
    committed = {"_path": "operations/transactions/transaction-1.yaml"}
    diagnosis = resolve([], _authority(
        verified_receipt=committed,
        response_snapshot_after="sha256:aaa",
        contract_only_drift=True,
        contract_only_receipt_id="transaction-20260101-000009-001"))
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "none"
    assert any("authored data unchanged" in reason
               for reason in diagnosis.reasons)
    assert any("transaction-20260101-000009-001" in reason
               for reason in diagnosis.reasons)


def test_contract_only_drift_receipt_needs_unchained_manifest_and_digest(
        tmp_path: Path):
    from learning_os.diagnostics.resolver import contract_only_drift_receipt
    from learning_os.fingerprint import data_roots_fingerprint

    recorded = f"sha256:{data_roots_fingerprint(tmp_path)}"
    receipts = [{"id": "transaction-20260101-000001-001",
                 "snapshot_after": "sha256:aaa",
                 "metadata": {"data_roots_sha256": recorded}}]
    # A chained manifest keeps the positional rule, never this one.
    assert contract_only_drift_receipt(tmp_path, receipts, "sha256:aaa") is None
    assert contract_only_drift_receipt(tmp_path, receipts, None) is None
    assert contract_only_drift_receipt(tmp_path, [], "sha256:zzz") is None
    assert contract_only_drift_receipt(
        tmp_path, receipts, "sha256:zzz") == receipts[0]
    # A newest receipt too old to record the digest keeps old behaviour.
    old = [{"id": "transaction-20260101-000001-001",
            "snapshot_after": "sha256:aaa", "metadata": {}}]
    assert contract_only_drift_receipt(tmp_path, old, "sha256:zzz") is None


def test_data_roots_digest_ignores_contract_moves_but_follows_data(
        mini_repo: Path):
    from learning_os.fingerprint import (
        canonical_fingerprint,
        data_roots_fingerprint,
    )

    before_data = data_roots_fingerprint(mini_repo)
    before_full = canonical_fingerprint(mini_repo)
    contracts = mini_repo / "system/contracts/capabilities.yaml"
    contracts.write_text(
        contracts.read_text(encoding="utf-8") + "\n# digest probe\n",
        encoding="utf-8")
    assert canonical_fingerprint(mini_repo) != before_full
    assert data_roots_fingerprint(mini_repo) == before_data
    concepts = mini_repo / "knowledge/concepts.yaml"
    concepts.write_text(
        concepts.read_text(encoding="utf-8") + "\n# digest probe\n",
        encoding="utf-8")
    assert data_roots_fingerprint(mini_repo) != before_data


def _live_snapshot(root: Path) -> str:
    from learning_os.fingerprint import canonical_fingerprint

    return f"sha256:{canonical_fingerprint(root)}"


def test_contract_only_commit_settles_earlier_committed_writes(
        mini_repo: Path):
    """After a commit touching only system/contracts, the earlier committed
    write reads settled with the contract-only reason."""
    _, result = _commit_capture_v2(mini_repo, "contract-drift", "request-drift")
    assert result.snapshot_after
    contracts = mini_repo / "system/contracts/capabilities.yaml"
    contracts.write_text(
        contracts.read_text(encoding="utf-8") + "\n# contract-only drift probe\n",
        encoding="utf-8")
    live = _live_snapshot(mini_repo)
    authority = collect_authority(
        mini_repo, request_id="request-drift",
        idempotency_key="contract-drift", capability="capture.create",
        response={"snapshot_after": result.snapshot_after},
        manifest_snapshot=live)
    assert authority.verification_error is None
    assert authority.superseded_snapshot is False
    assert authority.contract_only_drift is True
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "none"
    assert any("authored data unchanged" in reason
               for reason in diagnosis.reasons)


def test_hand_edit_to_data_keeps_verify_observation(mini_repo: Path):
    """Authored data moved without a receipt is still the hand-edit signal:
    verify-observation stands even though the manifest is unchained."""
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    _, result = _commit_capture_v2(mini_repo, "data-drift", "request-data")
    target = (mini_repo / "curriculum/modules/module-demo/units"
              / "unit-demo-l01/unit.yaml")
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# hand-edited outside the gateway\n",
        encoding="utf-8")
    authority = collect_authority(
        mini_repo, request_id="request-data",
        idempotency_key="data-drift", capability="capture.create",
        response={"snapshot_after": result.snapshot_after},
        manifest_snapshot=_live_snapshot(mini_repo))
    assert authority.verification_error is None
    assert authority.contract_only_drift is False
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "verify-observation"


def test_old_receipt_without_digest_keeps_verify_observation(mini_repo: Path):
    """A newest receipt from before the data-roots digest keeps today's
    behaviour even when the drift is contract-only."""
    import yaml

    _, result = _commit_capture_v2(mini_repo, "old-receipt", "request-old")
    receipt_path = mini_repo / result.receipt_path
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert receipt["metadata"].pop("data_roots_sha256")
    receipt_path.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True),
        encoding="utf-8")
    contracts = mini_repo / "system/contracts/capabilities.yaml"
    contracts.write_text(
        contracts.read_text(encoding="utf-8") + "\n# contract-only drift probe\n",
        encoding="utf-8")
    authority = collect_authority(
        mini_repo, request_id="request-old",
        idempotency_key="old-receipt", capability="capture.create",
        response={"snapshot_after": result.snapshot_after},
        manifest_snapshot=_live_snapshot(mini_repo))
    assert authority.verification_error is None
    assert authority.contract_only_drift is False
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "verify-observation"


def test_idempotency_conflict_proves_no_commit_for_its_attempt():
    """A definite conflict retires its own request (JF-19)."""
    attempt = [
        {"v": 2, "kind": "span-start", "name": "attempt", "span": "s1", "ts": 1},
        {"v": 2, "kind": "span-end", "name": "attempt", "span": "s1",
         "status": "error", "ts": 2},
    ]
    diagnosis = resolve(attempt, _authority(
        response_code="IDEMPOTENCY_CONFLICT",
        response_codes=["IDEMPOTENCY_CONFLICT"]))
    assert diagnosis.canonical_outcome == "NOT_COMMITTED"
    assert diagnosis.recovery_requirement == "none"
    # The other intent's row contradicts this request's evidence; the
    # conflict still retires it (ordering before the contradiction branches).
    contradicted = resolve(attempt, _authority(
        response_code="IDEMPOTENCY_CONFLICT",
        response_codes=["IDEMPOTENCY_CONFLICT"],
        ledger={"x": {"channel": "operator"}},
        verification_error="intent mismatch"))
    assert contradicted.canonical_outcome == "NOT_COMMITTED"
    assert contradicted.recovery_requirement == "none"
    # ... but never an earlier ambiguous attempt (the S9-S11 rule holds
    # for the new code too).
    two_attempts = attempt + [
        {"v": 2, "kind": "span-start", "name": "attempt", "span": "s2", "ts": 3},
    ]
    second = resolve(two_attempts, _authority(
        response_code="IDEMPOTENCY_CONFLICT",
        response_codes=["IDEMPOTENCY_CONFLICT"]))
    assert second.canonical_outcome == "AMBIGUOUS"
    assert second.recovery_requirement == "reconcile-exact-request"


@pytest.mark.paired
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


def test_shared_drift_cache_walks_the_data_roots_once(mini_repo: Path,
                                                      monkeypatch):
    """Diagnosing many operations against one authority load walks the
    authored-data roots once, not once per row (Operations lists 20)."""
    from learning_os.diagnostics import resolver

    _, result = _commit_capture_v2(mini_repo, "drift-cache", "request-cache")
    contracts = mini_repo / "system/contracts/capabilities.yaml"
    contracts.write_text(
        contracts.read_text(encoding="utf-8") + "\n# contract-only drift probe\n",
        encoding="utf-8")
    live = _live_snapshot(mini_repo)
    calls = []
    real = resolver.data_roots_fingerprint
    monkeypatch.setattr(resolver, "data_roots_fingerprint",
                        lambda root: calls.append(root) or real(root))
    shared = resolver.load_authority_files(mini_repo)
    cache: dict = {}
    for _ in range(5):
        authority = collect_authority(
            mini_repo, request_id="request-cache",
            idempotency_key="drift-cache", capability="capture.create",
            response={"snapshot_after": result.snapshot_after},
            manifest_snapshot=live, authority_files=shared, drift_cache=cache)
        assert authority.contract_only_drift is True
    assert len(calls) == 1


# ------------------------------------------------- fingerprint-definition transition (#112)
SCAN_REL = "knowledge/attachments/note-demo/scan.pdf"


def _pre_exclusion_receipt(root: Path) -> dict:
    """A newest receipt as the cutover left it: a definition-1
    data-roots digest and no recorded definition."""
    from learning_os.fingerprint import data_roots_fingerprint

    return {"id": "transaction-20260101-000001-001",
            "snapshot_after": "sha256:aaa",
            "metadata": {"data_roots_sha256":
                         f"sha256:{data_roots_fingerprint(root, definition=1)}"}}


def test_definition_transition_receipt_needs_old_definition_and_digest(
        mini_repo: Path):
    from repo_builders import declare_scan

    from learning_os.diagnostics.resolver import (
        fingerprint_definition_transition_receipt,
    )
    from learning_os.fingerprint import data_roots_fingerprint

    declare_scan(mini_repo, SCAN_REL)
    receipts = [_pre_exclusion_receipt(mini_repo)]
    # A chained manifest keeps the positional rule, never this one.
    assert fingerprint_definition_transition_receipt(
        mini_repo, receipts, "sha256:aaa") is None
    assert fingerprint_definition_transition_receipt(
        mini_repo, receipts, None) is None
    assert fingerprint_definition_transition_receipt(
        mini_repo, [], "sha256:zzz") is None
    assert fingerprint_definition_transition_receipt(
        mini_repo, receipts, "sha256:zzz") == receipts[0]
    # A newest receipt too old to record the digest keeps old behaviour.
    old = [{"id": "transaction-20260101-000001-001",
            "snapshot_after": "sha256:aaa", "metadata": {}}]
    assert fingerprint_definition_transition_receipt(
        mini_repo, old, "sha256:zzz") is None
    # A current-definition receipt never takes the transition, even
    # when its digest is stale.
    current = [{"id": "transaction-20260101-000001-001",
                "snapshot_after": "sha256:aaa",
                "metadata": {"data_roots_sha256": receipts[0]["metadata"]["data_roots_sha256"],
                             "fingerprint_definition": 2}}]
    assert fingerprint_definition_transition_receipt(
        mini_repo, current, "sha256:zzz") is None
    # An unknown future definition fails closed.
    future = [{"id": "transaction-20260101-000001-001",
               "snapshot_after": "sha256:aaa",
               "metadata": {"data_roots_sha256":
                            f"sha256:{data_roots_fingerprint(mini_repo)}",
                            "fingerprint_definition": 9}}]
    assert fingerprint_definition_transition_receipt(
        mini_repo, future, "sha256:zzz") is None
    # Data moved without a receipt: no transition.
    (mini_repo / "knowledge/concepts.yaml").write_text(
        (mini_repo / "knowledge/concepts.yaml").read_text(encoding="utf-8")
        + "\n# hand-edited outside the gateway\n", encoding="utf-8")
    assert fingerprint_definition_transition_receipt(
        mini_repo, receipts, "sha256:zzz") is None


def test_definition_transition_settles_without_exact_observation():
    """A pre-exclusion newest receipt matching under its own definition
    is settled, with the transition reason — not verify-observation."""
    committed = {"_path": "operations/transactions/transaction-1.yaml"}
    diagnosis = resolve([], _authority(
        verified_receipt=committed,
        response_snapshot_after="sha256:aaa",
        definition_transition_drift=True,
        definition_transition_receipt_id="transaction-20260101-000009-001"))
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "none"
    assert any("definitional move, not drift" in reason
               for reason in diagnosis.reasons)
    assert any("transaction-20260101-000009-001" in reason
               for reason in diagnosis.reasons)


def _rewrite_newest_receipt_as_pre_exclusion(mini_repo: Path, receipt_path: Path):
    """Simulate the cutover: the newest receipt keeps a definition-1
    data-roots digest and loses its recorded definition."""
    import yaml

    from learning_os.fingerprint import data_roots_fingerprint

    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["metadata"] = {
        "data_roots_sha256": f"sha256:{data_roots_fingerprint(mini_repo, definition=1)}",
    }
    receipt_path.write_text(
        yaml.safe_dump(receipt, sort_keys=False, allow_unicode=True),
        encoding="utf-8")


def test_pre_exclusion_newest_receipt_settles_earlier_committed_writes(
        mini_repo: Path):
    """After the cutover, a commit whose newest receipt predates the
    local-only exclusion reads settled when the data roots match it
    under its own definition."""
    from repo_builders import declare_scan

    declare_scan(mini_repo, SCAN_REL)
    _, result = _commit_capture_v2(mini_repo, "transition", "request-transition")
    _rewrite_newest_receipt_as_pre_exclusion(
        mini_repo, mini_repo / result.receipt_path)
    contracts = mini_repo / "system/contracts/capabilities.yaml"
    contracts.write_text(
        contracts.read_text(encoding="utf-8") + "\n# contract-only drift probe\n",
        encoding="utf-8")
    live = _live_snapshot(mini_repo)
    authority = collect_authority(
        mini_repo, request_id="request-transition",
        idempotency_key="transition", capability="capture.create",
        response={"snapshot_after": result.snapshot_after},
        manifest_snapshot=live)
    assert authority.verification_error is None
    assert authority.superseded_snapshot is False
    assert authority.contract_only_drift is False
    assert authority.definition_transition_drift is True
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "none"
    assert any("definitional move, not drift" in reason
               for reason in diagnosis.reasons)


def test_pre_exclusion_newest_receipt_with_data_change_keeps_verify_observation(
        mini_repo: Path):
    """The transition proves unchanged data, not merely an old receipt:
    a data move without a receipt keeps verify-observation."""
    from repo_builders import declare_scan

    declare_scan(mini_repo, SCAN_REL)
    _, result = _commit_capture_v2(mini_repo, "transition-dirty", "request-transition-dirty")
    _rewrite_newest_receipt_as_pre_exclusion(
        mini_repo, mini_repo / result.receipt_path)
    concepts = mini_repo / "knowledge/concepts.yaml"
    concepts.write_text(
        concepts.read_text(encoding="utf-8") + "\n# hand-edited outside the gateway\n",
        encoding="utf-8")
    authority = collect_authority(
        mini_repo, request_id="request-transition-dirty",
        idempotency_key="transition-dirty", capability="capture.create",
        response={"snapshot_after": result.snapshot_after},
        manifest_snapshot=_live_snapshot(mini_repo))
    assert authority.verification_error is None
    assert authority.contract_only_drift is False
    assert authority.definition_transition_drift is False
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"
    assert diagnosis.recovery_requirement == "verify-observation"
