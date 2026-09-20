"""Crash-recovery conflict matrix: compare-and-undo must never clobber.

A stale inflight journal proves nothing by itself. Recovery may modify a
path only while the live file still equals the crashed transaction's exact
post-state (safe to undo) or its original pre-state (already undone). Any
other live state is foreign — a later writer owns those bytes — so recovery
touches nothing, preserves the journal, and raises
TransactionRecoveryConflict. Row 15 is the S10 reproducer that discovered
the old blind-rollback defect, kept as the permanent regression.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from learning_os.contracts.gateway import GatewayRequestContext
from learning_os.fingerprint import canonical_fingerprint
from learning_os.transactions import (
    TransactionRecoveryConflict,
    TransactionService,
    reconcile_inflight_transactions,
)

TOOLS = Path(__file__).resolve().parent.parent / "tools"
LOS = TOOLS / "los.py"


def _sha(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _write_journal_v2(root: Path, tx_id: str, entries: list,
                      *, receipt_rel: str | None = None) -> Path:
    """Hand-craft a schema-2 crash journal. Each entry is
    (relative, before_bytes | None, after_bytes | None | "UNKNOWN").
    """
    tx_dir = root / "operations" / "transactions" / ".inflight" / tx_id
    tx_dir.mkdir(parents=True)
    paths = []
    for index, (relative, before, after) in enumerate(entries):
        if before is None:
            recorded_before: dict = {"kind": "absent"}
        else:
            backup_id = f"backup-{index}"
            (tx_dir / backup_id).write_bytes(before)
            recorded_before = {"kind": "file", "sha256": _sha(before),
                               "backup_id": backup_id}
        record: dict = {"path": relative, "before": recorded_before}
        if after == "UNKNOWN":
            pass
        elif after is None:
            record["after"] = {"kind": "absent"}
        else:
            record["after"] = {"kind": "file", "sha256": _sha(after)}
        paths.append(record)
    intent = {
        "schema_version": 2,
        "transaction_id": tx_id,
        "receipt_path": receipt_rel
        or f"operations/transactions/transaction-{tx_id}.yaml",
        "paths": paths,
    }
    (tx_dir / "intent.json").write_text(json.dumps(intent), encoding="utf-8")
    return tx_dir


def _write_journal_v1(root: Path, tx_id: str, rows: list,
                      *, receipt_rel: str | None = None) -> Path:
    """Hand-craft a schema-1 (undo-only) journal. Each row is
    (relative, created, backup_bytes | None).
    """
    tx_dir = root / "operations" / "transactions" / ".inflight" / tx_id
    tx_dir.mkdir(parents=True)
    backups = []
    for index, (relative, created, backup) in enumerate(rows):
        row: dict = {"path": relative, "created": created}
        if backup is not None:
            backup_id = f"backup-{index}"
            (tx_dir / backup_id).write_bytes(backup)
            row["backup_id"] = backup_id
        backups.append(row)
    intent = {
        "transaction_id": tx_id,
        "receipt_path": receipt_rel
        or f"operations/transactions/transaction-{tx_id}.yaml",
        "backups": backups,
    }
    (tx_dir / "intent.json").write_text(json.dumps(intent), encoding="utf-8")
    return tx_dir


def _mini_with_curriculum(tmp_path: Path, name: str) -> Path:
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    mini = build_mini_repo(tmp_path / name)
    add_curriculum(mini)
    return mini


def _crash_stage_write(mini: Path, key: str) -> dict:
    """A real crashed commit: chmod breaks projection, the v2 journal stays."""
    from gateway_helpers import approved_v2_envelope

    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key=key)
    generated = mini / "generated"
    generated.mkdir(exist_ok=True)
    os.chmod(generated, 0o555)
    try:
        proc = subprocess.run(
            [sys.executable, str(LOS), "--root", str(mini), "capability",
             "stage.progress.update", "--payload-file", "-"],
            input=json.dumps(envelope), capture_output=True, text=True,
            timeout=120)
    finally:
        os.chmod(generated, 0o755)
    body = json.loads(proc.stdout)
    assert body["error"]["code"] == "INTERNAL_FAILURE", body
    journals = list((mini / "operations" / "transactions" / ".inflight").iterdir())
    assert len(journals) == 1, "the crash must leave exactly one journal"
    return envelope


# ---------------------------------------------------------------------------
# Clean crashes unwind automatically (rows 1-4).
# ---------------------------------------------------------------------------

def test_clean_crash_rolls_back_create_update_delete(tmp_path: Path):
    root = tmp_path / "clean"
    created = root / "work" / "new.md"
    updated = root / "work" / "mod.md"
    deleted = root / "work" / "gone.md"
    created.parent.mkdir(parents=True)
    created.write_bytes(b"created\n")
    updated.write_bytes(b"new\n")
    # deleted is absent: the crash took it after the transaction removed it.
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-001",
        [("work/new.md", None, b"created\n"),
         ("work/mod.md", b"old\n", b"new\n"),
         ("work/gone.md", b"gone\n", None)])

    reconcile_inflight_transactions(root)

    assert not created.exists()
    assert updated.read_bytes() == b"old\n"
    assert deleted.read_bytes() == b"gone\n"
    assert not tx_dir.exists()


def test_already_restored_paths_are_noops(tmp_path: Path):
    root = tmp_path / "noop"
    target = root / "work" / "mod.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"old\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-002",
        [("work/mod.md", b"old\n", b"new\n")])

    reconcile_inflight_transactions(root)

    assert target.read_bytes() == b"old\n"
    assert not tx_dir.exists()


# ---------------------------------------------------------------------------
# Later writers own their bytes (rows 5-8).
# ---------------------------------------------------------------------------

def test_later_edits_are_preserved_with_conflict(tmp_path: Path):
    root = tmp_path / "diverged"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "new.md").write_bytes(b"later owner's bytes\n")
    (work / "mod.md").write_bytes(b"later\n")
    (work / "gone.md").write_bytes(b"recreated differently\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-003",
        [("work/new.md", None, b"created\n"),
         ("work/mod.md", b"old\n", b"new\n"),
         ("work/gone.md", b"gone\n", None)])
    intent_before = (tx_dir / "intent.json").read_bytes()

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert exc_info.value.transaction_id == "transaction-20260101-000000-003"
    assert [entry["reason"] for entry in exc_info.value.conflicts] == [
        "DIVERGED_FROM_TRANSACTION"] * 3
    assert "No conflicting path was modified" in str(exc_info.value)
    assert (work / "new.md").read_bytes() == b"later owner's bytes\n"
    assert (work / "mod.md").read_bytes() == b"later\n"
    assert (work / "gone.md").read_bytes() == b"recreated differently\n"
    assert (tx_dir / "intent.json").read_bytes() == intent_before


def test_single_conflict_blocks_all_restores(tmp_path: Path):
    root = tmp_path / "preflight"
    work = root / "work"
    work.mkdir(parents=True)
    entries = []
    for index in range(10):
        name = f"file-{index}.md"
        if index == 4:
            (work / name).write_bytes(b"foreign\n")
        else:
            (work / name).write_bytes(f"after-{index}\n".encode())
        entries.append((f"work/{name}", f"before-{index}\n".encode(),
                        f"after-{index}\n".encode()))
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-004", entries)
    before_files = {path: path.read_bytes() for path in sorted(work.iterdir())}
    intent_before = (tx_dir / "intent.json").read_bytes()

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert len(exc_info.value.conflicts) == 1
    assert exc_info.value.conflicts[0]["path"] == "work/file-4.md"
    assert {path: path.read_bytes() for path in sorted(work.iterdir())} == before_files
    assert (tx_dir / "intent.json").read_bytes() == intent_before


# ---------------------------------------------------------------------------
# Corrupt evidence fails closed (rows 9-10).
# ---------------------------------------------------------------------------

def test_corrupt_backup_blocks_all_restores(tmp_path: Path):
    root = tmp_path / "backup"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "bad.md").write_bytes(b"after\n")
    (work / "good.md").write_bytes(b"after\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-005",
        [("work/bad.md", b"before\n", b"after\n"),
         ("work/good.md", b"before\n", b"after\n")])
    (tx_dir / "backup-0").write_bytes(b"tampered backup\n")

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert exc_info.value.conflicts[0]["reason"] == "BACKUP_HASH_MISMATCH"
    # Preflight atomicity: the clean entry is not restored either.
    assert (work / "bad.md").read_bytes() == b"after\n"
    assert (work / "good.md").read_bytes() == b"after\n"
    assert tx_dir.is_dir()


def test_substituted_symlink_is_never_followed(tmp_path: Path):
    root = tmp_path / "symlink"
    work = root / "work"
    work.mkdir(parents=True)
    canary = work / "canary.md"
    canary.write_bytes(b"precious\n")
    link = work / "mod.md"
    os.symlink(canary, link)
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-006",
        [("work/mod.md", b"old\n", b"new\n")])

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert exc_info.value.conflicts[0]["reason"] == "UNEXPECTED_FILE_TYPE"
    assert link.is_symlink(), "the link itself must survive untouched"
    assert canary.read_bytes() == b"precious\n"
    assert tx_dir.is_dir()


def test_substituted_directory_is_never_entered(tmp_path: Path):
    root = tmp_path / "directory"
    work = root / "work"
    victim = work / "mod.md"
    victim.mkdir(parents=True)
    (victim / "inside.md").write_bytes(b"precious\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-007",
        [("work/mod.md", b"old\n", b"new\n")])

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert exc_info.value.conflicts[0]["reason"] == "UNEXPECTED_FILE_TYPE"
    assert (victim / "inside.md").read_bytes() == b"precious\n"
    assert tx_dir.is_dir()


# ---------------------------------------------------------------------------
# The receipt boundary (rows 11-12).
# ---------------------------------------------------------------------------

def _commit_capture(mini_repo: Path, key: str):
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


def test_valid_receipt_cleans_journal_and_preserves_commit(mini_repo: Path):
    _context, result = _commit_capture(mini_repo, "receipt-ok")
    target = mini_repo / "work/inbox/receipt-ok.md"
    receipt_rel = result.receipt_path.relative_to(mini_repo).as_posix()
    tx_dir = _write_journal_v2(
        mini_repo, result.transaction_id,
        [("work/inbox/receipt-ok.md", None, b"committed\n")],
        receipt_rel=receipt_rel)

    reconcile_inflight_transactions(mini_repo)

    assert not tx_dir.exists(), "a committed journal must be cleaned"
    assert target.read_bytes() == b"committed\n"
    assert (mini_repo / receipt_rel).is_file()


def test_contradictory_receipt_preserves_everything(mini_repo: Path):
    _context, result = _commit_capture(mini_repo, "receipt-bad")
    target = mini_repo / "work/inbox/receipt-bad.md"
    receipt_path = mini_repo / result.receipt_path.relative_to(mini_repo)
    receipt_path.write_text("{invalid yaml: [", encoding="utf-8")
    tx_dir = _write_journal_v2(
        mini_repo, result.transaction_id,
        [("work/inbox/receipt-bad.md", None, b"committed\n")],
        receipt_rel=result.receipt_path.relative_to(mini_repo).as_posix())

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(mini_repo)

    assert exc_info.value.conflicts[0]["reason"] == "INVALID_COMMIT_RECEIPT"
    assert target.read_bytes() == b"committed\n"
    assert tx_dir.is_dir()


def test_wrong_receipt_id_preserves_everything(mini_repo: Path):
    _context, result = _commit_capture(mini_repo, "receipt-id")
    target = mini_repo / "work/inbox/receipt-id.md"
    receipt_path = mini_repo / result.receipt_path.relative_to(mini_repo)
    receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    receipt["id"] = "transaction-00000000-000000-000"
    receipt_path.write_text(yaml.safe_dump(receipt, sort_keys=False),
                            encoding="utf-8")
    tx_dir = _write_journal_v2(
        mini_repo, result.transaction_id,
        [("work/inbox/receipt-id.md", None, b"committed\n")],
        receipt_rel=result.receipt_path.relative_to(mini_repo).as_posix())

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(mini_repo)

    assert exc_info.value.conflicts[0]["reason"] == "INVALID_COMMIT_RECEIPT"
    assert target.read_bytes() == b"committed\n"
    assert tx_dir.is_dir()


# ---------------------------------------------------------------------------
# Idempotence, foreign files, legacy journals (rows 13-14, 16).
# ---------------------------------------------------------------------------

def test_interrupted_recovery_completes_idempotently(tmp_path: Path):
    root = tmp_path / "halfway"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "one.md").write_bytes(b"before\n")
    (work / "two.md").write_bytes(b"before\n")
    (work / "three.md").write_bytes(b"after\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-008",
        [("work/one.md", b"before\n", b"after\n"),
         ("work/two.md", b"before\n", b"after\n"),
         ("work/three.md", b"before\n", b"after\n")])

    reconcile_inflight_transactions(root)

    assert (work / "one.md").read_bytes() == b"before\n"
    assert (work / "two.md").read_bytes() == b"before\n"
    assert (work / "three.md").read_bytes() == b"before\n"
    assert not tx_dir.exists()
    reconcile_inflight_transactions(root)


def test_unrelated_changes_do_not_block_rollback(tmp_path: Path):
    root = tmp_path / "unrelated"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "one.md").write_bytes(b"after\n")
    (work / "two.md").write_bytes(b"after\n")
    (work / "elsewhere.md").write_bytes(b"someone else's edit\n")
    tx_dir = _write_journal_v2(
        root, "transaction-20260101-000000-009",
        [("work/one.md", b"before\n", b"after\n"),
         ("work/two.md", b"before\n", b"after\n")])

    reconcile_inflight_transactions(root)

    assert (work / "one.md").read_bytes() == b"before\n"
    assert (work / "two.md").read_bytes() == b"before\n"
    assert (work / "elsewhere.md").read_bytes() == b"someone else's edit\n"
    assert not tx_dir.exists()


def test_legacy_journal_blocks_instead_of_overwriting(tmp_path: Path):
    root = tmp_path / "legacy"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "new.md").write_bytes(b"later owner's bytes\n")
    (work / "mod.md").write_bytes(b"later\n")
    tx_dir = _write_journal_v1(
        root, "transaction-20260101-000000-010",
        [("work/new.md", True, None),
         ("work/mod.md", False, b"old\n")])

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(root)

    assert [entry["reason"] for entry in exc_info.value.conflicts] == [
        "LEGACY_JOURNAL_UNPROVABLE"] * 2
    # Especially: a created file that exists is never unlinked.
    assert (work / "new.md").read_bytes() == b"later owner's bytes\n"
    assert (work / "mod.md").read_bytes() == b"later\n"
    assert tx_dir.is_dir()


def test_legacy_benign_journal_still_cleans(tmp_path: Path):
    root = tmp_path / "legacy-clean"
    work = root / "work"
    work.mkdir(parents=True)
    (work / "mod.md").write_bytes(b"old\n")
    tx_dir = _write_journal_v1(
        root, "transaction-20260101-000000-011",
        [("work/new.md", True, None),
         ("work/mod.md", False, b"old\n")])

    reconcile_inflight_transactions(root)

    assert (work / "mod.md").read_bytes() == b"old\n"
    assert not tx_dir.exists()


# ---------------------------------------------------------------------------
# End to end: the S10 reproducer and its complement (row 15).
# ---------------------------------------------------------------------------

def test_later_ledger_write_survives_crash_recovery(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "s10-shape")
    _crash_stage_write(mini, "recovery-clobber")
    ledger_path = mini / "operations" / "transactions" / "revisions.yaml"
    foreign = {"schema_version": 1, "type": "artifact-revision-ledger",
               "revisions": {"unit-demo-l01": 9, "study-map-demo-l01": 9}}
    ledger_path.write_text(yaml.safe_dump(foreign, sort_keys=False),
                           encoding="utf-8")
    foreign_bytes = ledger_path.read_bytes()

    with pytest.raises(TransactionRecoveryConflict) as exc_info:
        reconcile_inflight_transactions(mini)

    assert len(exc_info.value.conflicts) == 1
    assert exc_info.value.conflicts[0]["path"] == \
        "operations/transactions/revisions.yaml"
    assert exc_info.value.conflicts[0]["reason"] == "DIVERGED_FROM_TRANSACTION"
    assert ledger_path.read_bytes() == foreign_bytes
    journals = list((mini / "operations" / "transactions" / ".inflight").iterdir())
    assert len(journals) == 1, "the journal stays for diagnosis"


def test_untouched_crash_rolls_back_automatically(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "clean-crash")
    envelope = _crash_stage_write(mini, "recovery-clean")

    reconcile_inflight_transactions(mini)

    assert f"sha256:{canonical_fingerprint(mini)}" == envelope["expected_snapshot"]
    assert not list((mini / "operations" / "transactions").glob("transaction-*.yaml"))
    assert not list((mini / "operations" / "transactions" / ".inflight").iterdir())


def test_gateway_reports_recovery_conflict_as_internal_failure(tmp_path: Path):
    from gateway_helpers import approved_v2_envelope

    mini = _mini_with_curriculum(tmp_path, "gateway-conflict")
    _crash_stage_write(mini, "recovery-gateway")
    ledger_path = mini / "operations" / "transactions" / "revisions.yaml"
    foreign = {"schema_version": 1, "type": "artifact-revision-ledger",
               "revisions": {"unit-demo-l01": 9, "study-map-demo-l01": 9}}
    ledger_path.write_text(yaml.safe_dump(foreign, sort_keys=False),
                           encoding="utf-8")
    foreign_bytes = ledger_path.read_bytes()
    retry = approved_v2_envelope(
        mini, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="recovery-gateway-retry")
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "stage.progress.update", "--payload-file", "-"],
        input=json.dumps(retry), capture_output=True, text=True, timeout=120)

    assert proc.returncode == 2, proc.stderr
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "INTERNAL_FAILURE", body
    assert body["error"]["retryable"] is False, body
    assert "operations/transactions/revisions.yaml" in \
        body["error"]["details"]["conflicting_paths"], body
    assert ledger_path.read_bytes() == foreign_bytes
    journals = list((mini / "operations" / "transactions" / ".inflight").iterdir())
    assert len(journals) == 1
