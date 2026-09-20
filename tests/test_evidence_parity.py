"""Gateway replay and Operations must judge committed evidence identically.

Both call the shared verifier in ``learning_os.evidence``. Each tamper
below breaks one binding of a genuine committed receipt; the Gateway
replay and the Operations authority verdict must reject it with the same
failure, and the untampered control must pass on both sides.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learning_os.contracts.gateway import GatewayRequestContext
from learning_os.diagnostics.resolver import collect_authority, resolve
from learning_os.errors import ReplayEvidenceError
from learning_os.transactions import TransactionService, replay_for_request


def _commit(mini_repo: Path, key: str):
    target = mini_repo / f"work/inbox/{key}.md"
    context = GatewayRequestContext(
        request_id=f"request-{key}", idempotency_key=key,
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


def _retamper(receipt_path: Path, mutate) -> None:
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    mutate(receipt)
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False),
                            encoding="utf-8")


def _assert_parity(mini_repo: Path, key: str, tamper) -> None:
    context, _result = _commit(mini_repo, key)
    tamper(mini_repo)
    with pytest.raises(ReplayEvidenceError) as replay_exc:
        replay_for_request(mini_repo, context)
    authority = collect_authority(
        mini_repo, request_id=context.request_id,
        idempotency_key=key, capability="capture.create")
    assert authority.verified_receipt is None
    assert authority.verification_error == str(replay_exc.value)
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "AMBIGUOUS"
    assert diagnosis.recovery_requirement == "reconcile-exact-request"


def _receipt_tamper(key: str, mutate):
    def tamper(mini_repo: Path) -> None:
        [receipt_path] = list(
            (mini_repo / "operations" / "transactions").glob("transaction-*.yaml"))
        _retamper(receipt_path, mutate)

    tamper.__name__ = f"tamper_{key}"
    return tamper


def test_untampered_evidence_replays_and_resolves_committed(mini_repo: Path):
    context, result = _commit(mini_repo, "parity-ok")
    replayed = replay_for_request(mini_repo, context)
    assert replayed is not None and replayed.replayed is True
    assert replayed.transaction_id == result.transaction_id
    authority = collect_authority(
        mini_repo, request_id=context.request_id,
        idempotency_key="parity-ok", capability="capture.create")
    assert authority.verification_error is None
    assert authority.verified_receipt is not None
    assert authority.verified_receipt["id"] == result.transaction_id
    diagnosis = resolve([], authority)
    assert diagnosis.canonical_outcome == "COMMITTED"


def test_wrong_capability_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        receipt["capability"] = "stage.progress.update"

    _assert_parity(mini_repo, "parity-capability",
                   _receipt_tamper("capability", mutate))


def test_wrong_intent_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        receipt["request"]["intent_sha256"] = "sha256:" + "f" * 64

    _assert_parity(mini_repo, "parity-intent", _receipt_tamper("intent", mutate))


def test_wrong_approval_subject_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        receipt["request"]["approval"]["subject_sha256"] = "sha256:" + "e" * 64

    _assert_parity(mini_repo, "parity-approval",
                   _receipt_tamper("approval", mutate))


def test_invalid_grant_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        receipt["authority"]["grants"][0]["declared_writes"] = [
            "work/inbox/**", "elsewhere/**"]

    _assert_parity(mini_repo, "parity-grant", _receipt_tamper("grant", mutate))


def test_out_of_scope_write_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        receipt["writes"][0]["path"] = "work/active/evil.md"

    _assert_parity(mini_repo, "parity-scope", _receipt_tamper("scope", mutate))


def test_schema_defect_rejected_on_both_sides(mini_repo: Path):
    def mutate(receipt: dict) -> None:
        del receipt["status"]

    _assert_parity(mini_repo, "parity-schema", _receipt_tamper("schema", mutate))


def test_live_revision_below_recorded_rejected_on_both_sides(mini_repo: Path):
    def tamper(mini_repo: Path) -> None:
        [receipt_path] = list(
            (mini_repo / "operations" / "transactions").glob("transaction-*.yaml"))
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
        [[artifact, recorded]] = list(receipt["artifact_revisions"].items())
        ledger_path = mini_repo / "operations" / "transactions" / "revisions.yaml"
        ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
        ledger["revisions"][artifact] = recorded["after"] - 1
        ledger_path.write_text(yaml.safe_dump(ledger, sort_keys=False),
                               encoding="utf-8")

    _assert_parity(mini_repo, "parity-revision", tamper)
