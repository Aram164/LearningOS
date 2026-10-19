"""Production transaction fault schedules (S1/S2).

The receipt-parent witness in
``receipts/S1-receipt-parent-production-red-witness.json`` showed a real
defect: the receipt became visible, its parent-directory synchronization
failed with EIO, and the transaction then rolled its data back behind the
retained receipt. These tests inject that fault at the actual
synchronization point of a real ``TransactionService`` commit — no model
engine — and observe the data, receipt and journal independently.
"""

from __future__ import annotations

import errno
import json
import os
import stat
from pathlib import Path

import pytest
import yaml

import learning_os.store.transactions as transaction_module
from learning_os.domain.failures import (
    TransactionFailure,
    TransactionPublicationUncertain,
    TransactionRecoveryConflict,
)
from learning_os.store.contracts.gateway import GatewayRequestContext
from learning_os.store.transactions import (
    TransactionService,
    reconcile_inflight_transactions,
)


def _receipt_parent_eio(root: Path):
    """An fsync that fails only for the receipt parent, after visibility.

    Every earlier directory synchronization delegates to the real fsync.
    The receipt's parent sync is the first directory sync attempted while
    a matching receipt file is already visible in ``operations/transactions``
    — exactly the interval the saved production witness occupies.
    """
    real_fsync = os.fsync
    fired: list[bool] = []

    def fake_fsync(fd: int) -> None:
        if not fired and stat.S_ISDIR(os.fstat(fd).st_mode):
            receipts = list(
                (root / "operations" / "transactions").glob("transaction-*.yaml")
            )
            if receipts:
                fired.append(True)
                raise OSError(errno.EIO, "injected receipt parent failure")
        real_fsync(fd)

    return fake_fsync, fired


def _gateway_context(key: str) -> GatewayRequestContext:
    intent = "sha256:" + "1" * 64
    return GatewayRequestContext(
        request_id=f"request-{key}",
        idempotency_key=key,
        capability="capture.create",
        channel="codex",
        intent_sha256=intent,
        approval_kind="operator-approval",
        approval_subject_sha256=intent,
    )


def _commit_capture(root: Path, key: str, text: str = "forward\n"):
    target = root / f"work/inbox/{key}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old\n", encoding="utf-8")
    context = _gateway_context(key)
    return target, context


def _inflight_dirs(root: Path) -> list[Path]:
    inflight = root / "operations" / "transactions" / ".inflight"
    if not inflight.is_dir():
        return []
    return sorted(entry for entry in inflight.iterdir() if entry.is_dir())


def test_receipt_parent_eio_preserves_forward_state_and_journal(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """The saved production witness, as a regression.

    Before the repair this raised ``TransactionRollbackIncomplete`` with
    the data rolled back to ``old`` behind a retained committed receipt.
    """
    target, context = _commit_capture(mini_repo, "fault-parent")
    fake_fsync, fired = _receipt_parent_eio(mini_repo)
    monkeypatch.setattr(transaction_module.os, "fsync", fake_fsync)

    with pytest.raises(TransactionPublicationUncertain) as caught:
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-parent"],
            expected_revisions={"capture:fault-parent": 0},
            gateway_request=context,
        )

    assert fired, "the fault must land on the receipt-parent synchronization"
    # Independent observers: forward data, matching receipt, journal.
    assert target.read_bytes() == b"forward\n", (
        "data must not roll back behind a possibly published receipt"
    )
    receipts = sorted(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert len(receipts) == 1
    receipt = yaml.safe_load(receipts[0].read_text(encoding="utf-8"))
    assert receipt["status"] == "committed"
    assert receipt["id"] == caught.value.transaction_id
    assert receipt["request"]["idempotency_key"] == "fault-parent"
    journals = _inflight_dirs(mini_repo)
    assert len(journals) == 1, "uncertainty preserves the recovery journal"
    assert journals[0].name == receipt["id"]
    intent = json.loads((journals[0] / "intent.json").read_text(encoding="utf-8"))
    assert intent["transaction_id"] == receipt["id"]


def test_uncertain_publication_settles_on_restart_and_replays_once(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """After the barrier is restored, restart settles without repeating."""
    target, context = _commit_capture(mini_repo, "fault-restart")
    fake_fsync, _fired = _receipt_parent_eio(mini_repo)
    monkeypatch.setattr(transaction_module.os, "fsync", fake_fsync)
    with pytest.raises(TransactionPublicationUncertain):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-restart"],
            expected_revisions={"capture:fault-restart": 0},
            gateway_request=context,
        )
    monkeypatch.undo()

    # Fresh-process equivalent: recovery verifies the matching receipt and
    # retires only the journal; the forward bytes are not rewritten.
    reconcile_inflight_transactions(mini_repo)
    assert _inflight_dirs(mini_repo) == []
    assert target.read_bytes() == b"forward\n"

    replay = TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={target: "forward\n"},
        artifact_ids=["capture:fault-restart"],
        expected_revisions={"capture:fault-restart": 0},
        gateway_request=context,
    )
    assert replay.replayed is True
    receipts = list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert len(receipts) == 1, "exact replay must not create a second receipt"
    ledger = yaml.safe_load(
        (mini_repo / "operations/transactions/idempotency.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert list(ledger["entries"]) == ["fault-restart"]
    assert target.read_bytes() == b"forward\n"


def test_contradictory_receipt_after_uncertainty_blocks_settlement(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """A tampered receipt is not matching evidence: everything is preserved."""
    target, context = _commit_capture(mini_repo, "fault-contradict")
    fake_fsync, _fired = _receipt_parent_eio(mini_repo)
    monkeypatch.setattr(transaction_module.os, "fsync", fake_fsync)
    with pytest.raises(TransactionPublicationUncertain):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-contradict"],
            expected_revisions={"capture:fault-contradict": 0},
            gateway_request=context,
        )
    monkeypatch.undo()

    (receipt_path,) = list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["id"] = "transaction-00000000-000000-999"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    tampered = receipt_path.read_bytes()

    with pytest.raises(TransactionRecoveryConflict):
        reconcile_inflight_transactions(mini_repo)

    assert target.read_bytes() == b"forward\n"
    assert receipt_path.read_bytes() == tampered
    assert len(_inflight_dirs(mini_repo)) == 1, "contradiction preserves the journal"


def test_foreign_receipt_at_receipt_path_is_never_ours_to_publish_over(
    mini_repo: Path,
):
    """A foreign file squatting on the receipt path blocks publication.

    It is preserved byte-for-byte, the owned data unwind, and the outcome
    is not publication uncertainty — this transaction never published.
    """
    target, context = _commit_capture(mini_repo, "fault-foreign")
    foreign = b"foreign receipt\n"

    def squat_then_pass():
        inflight = mini_repo / "operations" / "transactions" / ".inflight"
        (tx_dir,) = [entry for entry in inflight.iterdir() if entry.is_dir()]
        intent = json.loads((tx_dir / "intent.json").read_text(encoding="utf-8"))
        squat = mini_repo / intent["receipt_path"]
        squat.parent.mkdir(parents=True, exist_ok=True)
        squat.write_bytes(foreign)
        return []

    with pytest.raises(TransactionFailure) as caught:
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-foreign"],
            expected_revisions={"capture:fault-foreign": 0},
            gateway_request=context,
            validate_state=squat_then_pass,
        )

    assert not isinstance(caught.value, TransactionPublicationUncertain)
    receipts = list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert len(receipts) == 1
    assert receipts[0].read_bytes() == foreign
    assert target.read_bytes() == b"old\n", "owned paths still unwind"


def test_gateway_serializes_publication_uncertainty_as_ambiguous(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """The real Gateway response must not flatten uncertainty into a refusal."""
    from gateway_helpers import approved_v2_envelope

    import learning_os.app.pipeline as pipeline_module
    from learning_os.adapters.cli_parser import build_parser
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.contracts.gateway import request_artifact_id
    from learning_os.store.diagnostics import tracer as diag_tracer
    from learning_os.store.diagnostics.store import bind_store

    envelope = approved_v2_envelope(
        mini_repo,
        capability="capture.create",
        payload={"text": "uncertain capture"},
        artifact_ids=[request_artifact_id("capture.create", "fault-gateway")],
        idempotency_key="fault-gateway",
    )
    fake_fsync, fired = _receipt_parent_eio(mini_repo)
    monkeypatch.setattr(transaction_module.os, "fsync", fake_fsync)
    bind_store(mini_repo)
    attempt = diag_tracer.begin_attempt({"capability": "capture.create"})
    outcome = pipeline_module.run_gateway(
        mini_repo,
        envelope,
        requested="capture.create",
        definitions=command_definitions(mini_repo),
        attempt=attempt,
        replay_only=False,
        parser_factory=build_parser,
    )
    assert outcome is not None
    assert fired
    response = json.loads(outcome.stdout)
    assert response["ok"] is False
    assert response["error"]["code"] == "INTERNAL_FAILURE"
    assert response["error"]["retryable"] is True
    assert response["error"]["code"] not in {
        "INVALID_REQUEST",
        "VALIDATION_FAILED",
        "PROJECTION_FAILED",
        "UNCONFIRMED",
        "STALE_SNAPSHOT",
        "REVISION_CONFLICT",
        "OUT_OF_SCOPE",
    }, "uncertainty must never reuse a definitive no-commit code"
    assert not response.get("snapshot_after") or response.get("error", {}).get(
        "details", {}
    ).get("committed") is not True
    # The forward capture and its recovery evidence survive the response.
    receipts = list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert len(receipts) == 1
    assert len(_inflight_dirs(mini_repo)) == 1
    inbox = [p for p in (mini_repo / "work" / "inbox").iterdir() if p.is_file()]
    assert len(inbox) == 1, "the forward capture must not roll back"
    assert "uncertain capture" in inbox[0].read_text(encoding="utf-8")


def test_receipt_failure_before_exposure_still_rolls_back(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """Proven absence is the one uncertain-state exit that may roll back.

    If the receipt write fails before the receipt can be exposed, the
    publication boundary was never crossed: owned data unwind and no
    journal or receipt remains.
    """
    target, context = _commit_capture(mini_repo, "fault-absent")
    real_atomic = transaction_module.atomic_write_bytes

    def failing_receipt_write(path: Path, content: bytes) -> None:
        if path.parent.name == "transactions" and path.name.startswith(
            "transaction-"
        ):
            raise TransactionFailure("injected pre-exposure receipt failure")
        real_atomic(path, content)

    monkeypatch.setattr(
        transaction_module, "atomic_write_bytes", failing_receipt_write
    )
    with pytest.raises(TransactionFailure) as caught:
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-absent"],
            expected_revisions={"capture:fault-absent": 0},
            gateway_request=context,
        )
    assert not isinstance(caught.value, TransactionPublicationUncertain)
    assert target.read_bytes() == b"old\n"
    assert not list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert _inflight_dirs(mini_repo) == []


def test_enospc_at_receipt_write_rolls_back_without_a_receipt(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """ENOSPC before receipt exposure: proven absence, guarded rollback."""
    target, context = _commit_capture(mini_repo, "fault-enospc")
    real_atomic = transaction_module.atomic_write_bytes

    def full_disk(path: Path, content: bytes) -> None:
        if path.parent.name == "transactions" and path.name.startswith(
            "transaction-"
        ):
            raise OSError(errno.ENOSPC, "injected disk full")
        real_atomic(path, content)

    monkeypatch.setattr(transaction_module, "atomic_write_bytes", full_disk)
    with pytest.raises(TransactionFailure) as caught:
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=["capture:fault-enospc"],
            expected_revisions={"capture:fault-enospc": 0},
            gateway_request=context,
        )
    assert not isinstance(caught.value, TransactionPublicationUncertain)
    assert target.read_bytes() == b"old\n"
    assert not list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    assert _inflight_dirs(mini_repo) == []


def test_pre_apply_guard_disabled_control_overwrites_the_foreign_edit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Negative control: without the recheck, the foreign edit is lost.

    This proves the guard in
    ``test_foreign_edit_between_capture_and_apply_is_preserved`` is the
    mechanism that saves the bytes, not an accident of the schedule.
    """
    root = tmp_path / "apply-unguarded"
    first = root / "work" / "a.md"
    second = root / "work" / "b.md"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"old-a\n")
    second.write_bytes(b"old-b\n")
    real_atomic = transaction_module.atomic_write_bytes
    mutated: list[bool] = []

    def interpose(path: Path, content: bytes) -> None:
        if path == first and not mutated:
            mutated.append(True)
            second.write_bytes(b"foreign-b\n")
        real_atomic(path, content)

    monkeypatch.setattr(transaction_module, "atomic_write_bytes", interpose)
    monkeypatch.setattr(
        TransactionService, "_guard_apply", lambda self, run, path, intended: None
    )
    TransactionService(root).commit(
        capability="project.update",
        writes={first: "new-a\n", second: "new-b\n"},
        artifact_ids=["project-demo"],
    )
    assert second.read_bytes() == b"new-b\n", (
        "with the protection disabled the foreign edit is overwritten — "
        "the enabled guard is what preserves it"
    )


# ---------------------------------------------------------------------------
# S2: receipt-journal-effect binding, pre-apply rechecks, restart schedules.
# ---------------------------------------------------------------------------


def _make_uncertain(mini_repo: Path, monkeypatch: pytest.MonkeyPatch, key: str):
    """One real uncertain publication; returns (target, receipt_path)."""
    target, context = _commit_capture(mini_repo, key)
    fake_fsync, _fired = _receipt_parent_eio(mini_repo)
    monkeypatch.setattr(transaction_module.os, "fsync", fake_fsync)
    with pytest.raises(TransactionPublicationUncertain):
        TransactionService(mini_repo).commit(
            capability="capture.create",
            writes={target: "forward\n"},
            artifact_ids=[f"capture:{key}"],
            expected_revisions={f"capture:{key}": 0},
            gateway_request=context,
        )
    monkeypatch.undo()
    (receipt_path,) = list(
        (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")
    )
    return target, receipt_path


@pytest.mark.parametrize("tamper", ["effect-hash", "request-identity"])
def test_wrong_effect_or_identity_receipt_blocks_settlement(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
):
    """Schema validity plus a matching transaction id is not enough.

    A well-formed receipt whose recorded effects (or request identity) do
    not join the journal and idempotency evidence must preserve the
    journal and block settlement, with the forward bytes untouched.
    """
    key = f"fault-bind-{tamper}"
    target, receipt_path = _make_uncertain(mini_repo, monkeypatch, key)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    if tamper == "effect-hash":
        receipt["writes"][0]["sha256_after"] = "0" * 64
    else:
        receipt["request"]["idempotency_key"] = "someone-else"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    tampered = receipt_path.read_bytes()

    with pytest.raises(TransactionRecoveryConflict):
        reconcile_inflight_transactions(mini_repo)

    assert target.read_bytes() == b"forward\n"
    assert receipt_path.read_bytes() == tampered
    assert len(_inflight_dirs(mini_repo)) == 1


def test_genuine_commit_survives_a_later_legitimate_write(
    mini_repo: Path,
):
    """Old evidence verifies against its recorded transaction, not live bytes.

    After a second legitimate commit moves the revision ledger, the
    idempotency ledger and the snapshot, the first transaction's evidence
    must still replay — settlement never required the whole current
    ledger to equal the old postimage.
    """
    from learning_os.store.evidence import replay_for_request

    _target1, context1 = _commit_capture(mini_repo, "fault-first")
    first = TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={_target1: "first\n"},
        artifact_ids=["capture:fault-first"],
        expected_revisions={"capture:fault-first": 0},
        gateway_request=context1,
    )
    target2, context2 = _commit_capture(mini_repo, "fault-second")
    TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={target2: "second\n"},
        artifact_ids=["capture:fault-second"],
        expected_revisions={"capture:fault-second": 0},
        gateway_request=context2,
    )

    replay = replay_for_request(mini_repo, context1)
    assert replay is not None
    assert replay.replayed is True
    assert replay.transaction_id == first.transaction_id


def test_foreign_edit_between_capture_and_apply_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A foreign write landing mid-apply must not be overwritten.

    The first canonical write is interposed to edit the second target;
    the pre-apply comparison for the second target must detect the
    changed bytes and preserve them. Compare-and-undo preflight is
    all-or-nothing, so the owned first file stays forward (not silently
    half-unwound) while the journal preserves the ambiguity.
    """
    root = tmp_path / "apply-foreign"
    first = root / "work" / "a.md"
    second = root / "work" / "b.md"
    first.parent.mkdir(parents=True)
    first.write_bytes(b"old-a\n")
    second.write_bytes(b"old-b\n")
    real_atomic = transaction_module.atomic_write_bytes
    mutated: list[bool] = []

    def interpose(path: Path, content: bytes) -> None:
        if path == first and not mutated:
            mutated.append(True)
            second.write_bytes(b"foreign-b\n")
        real_atomic(path, content)

    monkeypatch.setattr(transaction_module, "atomic_write_bytes", interpose)
    with pytest.raises(TransactionFailure):
        TransactionService(root).commit(
            capability="project.update",
            writes={first: "new-a\n", second: "new-b\n"},
            artifact_ids=["project-demo"],
        )

    assert first.read_bytes() == b"new-a\n", (
        "a conflicted unwind changes nothing rather than half-rolling-back"
    )
    assert second.read_bytes() == b"foreign-b\n", "the foreign edit survives"
    assert len(_inflight_dirs(root)) == 1, "ambiguity preserves the journal"


def test_foreign_edit_of_a_delete_target_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Deletion rechecks too: a foreign-edited target is never unlinked."""
    root = tmp_path / "delete-foreign"
    written = root / "work" / "a.md"
    victim = root / "work" / "victim.md"
    written.parent.mkdir(parents=True)
    written.write_bytes(b"old-a\n")
    victim.write_bytes(b"old-victim\n")
    real_atomic = transaction_module.atomic_write_bytes
    mutated: list[bool] = []

    def interpose(path: Path, content: bytes) -> None:
        if path == written and not mutated:
            mutated.append(True)
            victim.write_bytes(b"foreign-victim\n")
        real_atomic(path, content)

    monkeypatch.setattr(transaction_module, "atomic_write_bytes", interpose)
    with pytest.raises(TransactionFailure):
        TransactionService(root).commit(
            capability="project.update",
            writes={written: "new-a\n"},
            deletes=[victim],
            artifact_ids=["project-demo"],
        )

    assert victim.read_bytes() == b"foreign-victim\n"
    assert written.read_bytes() == b"new-a\n", (
        "a conflicted unwind changes nothing rather than half-rolling-back"
    )
    assert len(_inflight_dirs(root)) == 1


_CHILD_SCRIPT = """
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from learning_os.store.transactions import TransactionService
root = Path(sys.argv[2]); mode = sys.argv[3]; relative = sys.argv[4]
schema_src = Path(sys.argv[1]).parent / "system" / "schema" / "transaction-receipt.schema.json"
schema_dst = root / "system" / "schema" / "transaction-receipt.schema.json"
schema_dst.parent.mkdir(parents=True, exist_ok=True)
schema_dst.write_bytes(schema_src.read_bytes())
target = root / relative
target.parent.mkdir(parents=True, exist_ok=True)
if mode != "kill-new-directory" and not target.exists():
    target.write_bytes(b"old\\n")
def kill_validate():
    os._exit(70)
def kill_touched(paths):
    os._exit(70)
kwargs = {}
if mode in ("kill-after-apply", "kill-new-directory"):
    kwargs["validate_state"] = kill_validate
elif mode == "kill-after-receipt":
    kwargs["touched"] = kill_touched
TransactionService(root).commit(
    capability="project.update", writes={target: "forward\\n"},
    artifact_ids=["project-demo"], **kwargs)
"""

_RECONCILE_SCRIPT = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from learning_os.store.transactions import reconcile_inflight_transactions
reconcile_inflight_transactions(Path(sys.argv[2]))
"""


def _child(root: Path, tools: Path, script: str, *args: str):
    import subprocess
    import sys as _sys

    return subprocess.run(
        [_sys.executable, "-c", script, str(tools), str(root), *args],
        capture_output=True, text=True, timeout=120,
    )


def test_child_interruption_before_receipt_restarts_to_prestate(
    tmp_path: Path,
):
    """Process death after apply, before receipt: restart unwinds.

    This is process interruption evidence, not physical power-loss proof.
    """
    tools = Path(__file__).resolve().parent.parent / "tools"
    root = tmp_path / "kill-apply"
    target = root / "work" / "mod.md"
    result = _child(root, tools, _CHILD_SCRIPT, "kill-after-apply", "work/mod.md")
    assert result.returncode == 70, result.stderr
    assert target.read_bytes() == b"forward\n", "the crash leaves forward bytes"
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))

    restarted = _child(root, tools, _RECONCILE_SCRIPT)
    assert restarted.returncode == 0, restarted.stderr
    assert target.read_bytes() == b"old\n"
    assert _inflight_dirs(root) == []


def test_child_interruption_after_receipt_restarts_to_forward_state(
    tmp_path: Path,
):
    """Process death after the receipt, before cleanup: restart settles."""
    tools = Path(__file__).resolve().parent.parent / "tools"
    root = tmp_path / "kill-receipt"
    target = root / "work" / "mod.md"
    result = _child(root, tools, _CHILD_SCRIPT, "kill-after-receipt", "work/mod.md")
    assert result.returncode == 70, result.stderr
    assert target.read_bytes() == b"forward\n"
    assert len(list((root / "operations/transactions").glob("transaction-*.yaml"))) == 1
    assert len(_inflight_dirs(root)) == 1

    restarted = _child(root, tools, _RECONCILE_SCRIPT)
    assert restarted.returncode == 0, restarted.stderr
    assert target.read_bytes() == b"forward\n"
    assert _inflight_dirs(root) == []
    assert len(list((root / "operations/transactions").glob("transaction-*.yaml"))) == 1


def test_child_interruption_in_new_directory_restarts_without_the_file(
    tmp_path: Path,
):
    """Interrupted creation under new ancestors leaves no forward file."""
    tools = Path(__file__).resolve().parent.parent / "tools"
    root = tmp_path / "kill-newdir"
    relative = "work/deep/nested/mod.md"
    result = _child(root, tools, _CHILD_SCRIPT, "kill-new-directory", relative)
    assert result.returncode == 70, result.stderr
    assert (root / relative).read_bytes() == b"forward\n"

    restarted = _child(root, tools, _RECONCILE_SCRIPT)
    assert restarted.returncode == 0, restarted.stderr
    assert not (root / relative).exists()


def test_restart_retries_receipt_barrier_before_retiring_journal(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """R1: settlement re-proves receipt durability before deleting evidence.

    With the receipt-parent sync still failing at restart, recovery must
    attempt that barrier, fail, and preserve the journal and forward data.
    """
    target, receipt_path = _make_uncertain(
        mini_repo, monkeypatch, "fault-restart-barrier")
    real_sync = transaction_module._sync_directory
    seen: list[str] = []

    def failing_receipt_sync(path: Path) -> None:
        seen.append(str(path.relative_to(mini_repo)))
        if path == receipt_path.parent:
            raise OSError(errno.EIO, "receipt parent still cannot flush")
        real_sync(path)

    monkeypatch.setattr(transaction_module, "_sync_directory", failing_receipt_sync)
    with pytest.raises(TransactionRecoveryConflict):
        reconcile_inflight_transactions(mini_repo)

    assert "operations/transactions" in seen, (
        "the receipt publication barrier must be retried at restart")
    assert target.read_bytes() == b"forward\n"
    assert len(_inflight_dirs(mini_repo)) == 1


def test_new_inflight_namespace_is_durable_before_first_effect(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """R2: a newly created journal namespace gets its parent barrier first."""
    target, context = _commit_capture(mini_repo, "fault-new-namespace")
    inflight = mini_repo / "operations/transactions/.inflight"
    if inflight.exists():
        import shutil

        shutil.rmtree(inflight)
    real_sync = transaction_module._sync_directory
    real_apply = TransactionService._apply
    seen: list[str] = []
    at_apply: list[str] = []

    def recording_sync(path: Path) -> None:
        seen.append(str(path.relative_to(mini_repo)))
        real_sync(path)

    def recording_apply(service, run):
        at_apply.extend(seen)
        return real_apply(service, run)

    monkeypatch.setattr(transaction_module, "_sync_directory", recording_sync)
    monkeypatch.setattr(TransactionService, "_apply", recording_apply)
    TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={target: "forward\n"},
        artifact_ids=["capture:fault-new-namespace"],
        expected_revisions={"capture:fault-new-namespace": 0},
        gateway_request=context,
    )
    assert "operations/transactions" in at_apply, (
        "the new .inflight entry's parent barrier must precede the first effect")


def test_new_namespace_barrier_failure_prevents_every_effect(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    target, context = _commit_capture(mini_repo, "fault-namespace-barrier")
    real_sync = transaction_module._sync_directory
    applied = []
    real_apply = TransactionService._apply

    def fail_parent(path: Path) -> None:
        if path == mini_repo / "operations/transactions":
            raise OSError(errno.EIO, "journal namespace barrier failed")
        real_sync(path)

    def apply(service, run):
        applied.append(True)
        return real_apply(service, run)

    monkeypatch.setattr(transaction_module, "_sync_directory", fail_parent)
    monkeypatch.setattr(TransactionService, "_apply", apply)
    # Failed creation leaves the namespace visible. A retry must still
    # attempt the same barrier, rather than trusting existence as durability.
    for _attempt in range(2):
        with pytest.raises(TransactionFailure, match="journal namespace durable"):
            TransactionService(mini_repo).commit(
                capability="capture.create", writes={target: "forward\n"},
                artifact_ids=["capture:fault-namespace-barrier"],
                expected_revisions={"capture:fault-namespace-barrier": 0},
                gateway_request=context,
            )
    assert applied == []
    assert target.read_bytes() == b"old\n"
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_damaged_journal_after_uncertainty_keeps_recovery_proof(
    mini_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """Partial journal damage cannot manufacture a settlement.

    A published journal whose intent is gone is corruption after arming:
    recovery preserves the directory and the forward bytes rather than
    silently cleaning the remains and calling the state settled.
    """
    target, _receipt_path = _make_uncertain(mini_repo, monkeypatch, "fault-damaged")
    (journal,) = _inflight_dirs(mini_repo)
    (journal / "intent.json").unlink()

    with pytest.raises(TransactionRecoveryConflict):
        reconcile_inflight_transactions(mini_repo)

    assert target.read_bytes() == b"forward\n"
    assert journal.is_dir(), "damaged recovery evidence is preserved, not cleaned"
