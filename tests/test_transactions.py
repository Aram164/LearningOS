from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learning_os.transactions import (
    TransactionConflict, TransactionFailure, TransactionService,
    artifact_revision, canonical_fingerprint,
)


def test_failed_transaction_restores_canonical_state(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")
    before = canonical_fingerprint(root)
    service = TransactionService(root)
    with pytest.raises(TransactionFailure):
        service.commit(
            capability="project.update", writes={target: "new\n"},
            artifact_ids=["project-demo"], validate_state=lambda: ["forced failure"],
        )
    assert target.read_text(encoding="utf-8") == "old\n"
    assert canonical_fingerprint(root) == before
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))


def test_artifact_revision_conflicts_are_scoped(tmp_path: Path):
    root = tmp_path
    a = root / "projects/registry/project-a.yaml"
    b = root / "projects/registry/project-b.yaml"
    a.parent.mkdir(parents=True)
    service = TransactionService(root)
    first = service.commit(capability="project.create", writes={a: "a\n"}, artifact_ids=["project-a"])
    assert first.revisions == {"project-a": 1}
    # A write to another artifact does not conflict with project-a changing.
    second = service.commit(
        capability="project.create", writes={b: "b\n"}, artifact_ids=["project-b"],
        expected_revisions={"project-b": 0},
    )
    assert second.revisions == {"project-b": 1}
    with pytest.raises(TransactionConflict):
        service.commit(
            capability="project.update", writes={a: "a2\n"}, artifact_ids=["project-a"],
            expected_revisions={"project-a": 0},
        )
    assert artifact_revision(root, "project-a") == 1


def test_each_commit_has_exactly_one_append_only_receipt(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    result = TransactionService(root).commit(
        capability="project.create", writes={target: "demo\n"}, artifact_ids=["project-demo"]
    )
    receipts = list((root / "operations/transactions").glob("transaction-*.yaml"))
    assert receipts == [result.receipt_path]
    receipt = yaml.safe_load(result.receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "committed"
    assert receipt["capability"] == "project.create"
    assert receipt["artifact_revisions"]["project-demo"] == {"before": 0, "after": 1}


def test_failed_transaction_removes_new_binary_files(tmp_path: Path):
    root = tmp_path
    target = root / "curriculum/modules/module-demo/units/unit-demo/attachments/note.png"
    service = TransactionService(root)
    with pytest.raises(TransactionFailure):
        service.commit(
            capability="unit.note.append",
            writes={target: b"not-really-a-png"},
            artifact_ids=["unit-demo"],
            validate_state=lambda: ["forced failure"],
        )
    assert not target.exists()
    assert artifact_revision(root, "unit-demo") == 0
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))


def test_post_commit_bookkeeping_failure_rolls_back_receipt_and_state(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")

    def fail_bookkeeping(_paths):
        raise RuntimeError("forced touched-ledger failure")

    with pytest.raises(TransactionFailure):
        TransactionService(root).commit(
            capability="project.update",
            writes={target: "new\n"},
            artifact_ids=["project-demo"],
            touched=fail_bookkeeping,
        )

    assert target.read_text(encoding="utf-8") == "old\n"
    assert artifact_revision(root, "project-demo") == 0
    assert not list((root / "operations/transactions").glob("transaction-*.yaml"))
