from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

import learning_os.commands.support as command_support
import learning_os.fingerprint as fingerprint_module
import learning_os.transactions as transaction_module
from learning_os.fingerprint import source_fingerprint
from learning_os.loader import load_repo
from learning_os.rules.common import Issue
from learning_os.transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    artifact_revision,
    canonical_fingerprint,
)

TOOLS = Path(__file__).resolve().parent.parent / "tools"


# --------------------------------------------------------------------------
# One fingerprint, one root list.
#
# Two implementations existed until 2026-08-18: `transactions.canonical_
# fingerprint` produced the value a receipt records as snapshot_before/after,
# and `genout.source_fingerprint` produced the value the projection publishes
# as `_generated.snapshot_id` — the token the UI hands back to guard its next
# write. Same roots, same algorithm, nothing holding them together. Add a
# canonical root to one and forget the other and the receipt starts describing
# a different state than the one the write was checked against, silently.
#
# Value equality on a fixture is too weak to guard this on its own: a root the
# fixture happens not to contain could diverge without moving either digest.
# So the structure is asserted too.
# --------------------------------------------------------------------------

def test_the_receipt_and_the_projection_share_one_digest_function():
    assert canonical_fingerprint is fingerprint_module.canonical_fingerprint


def test_only_one_module_declares_the_canonical_root_list():
    """No second copy of the root list may appear anywhere under tools/."""
    roots = set(fingerprint_module.CANONICAL_ROOTS)
    declaring: list[str] = []
    for path in sorted(TOOLS.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                continue
            try:
                literal = set(ast.literal_eval(node))
            except (ValueError, TypeError, SyntaxError):
                continue
            if roots <= literal:
                declaring.append(path.relative_to(TOOLS).as_posix())
                break
    assert declaring == ["learning_os/fingerprint.py"], (
        f"the canonical root list is declared in more than one place: {declaring}"
    )


def test_the_receipt_and_the_projection_agree_on_a_real_repository(mini_repo: Path):
    assert source_fingerprint(load_repo(mini_repo)) == canonical_fingerprint(mini_repo)


def test_source_fingerprint_cache_does_not_mutate_the_loaded_repo(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    repo = load_repo(mini_repo)
    calls = 0
    original = fingerprint_module.canonical_fingerprint

    def counted(root: Path):
        nonlocal calls
        calls += 1
        return original(root)

    monkeypatch.setattr(fingerprint_module, "canonical_fingerprint", counted)
    first = source_fingerprint(repo)
    assert source_fingerprint(repo) == first
    assert calls == 1
    assert not hasattr(repo, "_source_fingerprint_cache")


def test_a_transaction_refuses_an_already_invalid_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    target = mini_repo / "work/inbox/strict-validation.md"
    monkeypatch.setattr(
        command_support,
        "validate",
        lambda _repo, online=False: [
            Issue("E", "PREEXISTING", "the repository is already invalid", "somewhere.yaml")
        ],
    )
    monkeypatch.setattr(command_support, "_publish", lambda _root: None)

    code, errors, confirmation = command_support._write_transaction(
        mini_repo,
        {target: "must roll back\n"},
        capability="capture.create",
    )

    assert code == 2
    assert "PREEXISTING" in errors[0]
    assert confirmation == {}
    assert not target.exists()


def test_validation_and_publication_share_one_loaded_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    target = mini_repo / "work/inbox/one-load.md"
    loads = 0
    original = command_support.load_repo

    def counted(root: Path):
        nonlocal loads
        loads += 1
        return original(root)

    monkeypatch.setattr(command_support, "load_repo", counted)
    code, errors, confirmation = command_support._write_transaction(
        mini_repo,
        {target: "one load\n"},
        capability="capture.create",
    )

    assert (code, errors) == (0, [])
    assert confirmation["transaction_id"]
    assert loads == 1


def test_snapshot_check_does_not_parse_the_repository(
        mini_repo: Path, monkeypatch: pytest.MonkeyPatch):
    expected = f"sha256:{canonical_fingerprint(mini_repo)}"

    def unexpected_load(_root: Path):
        raise AssertionError("a content digest must not require a domain parse")

    monkeypatch.setattr(command_support, "load_repo", unexpected_load)

    assert command_support._expected_ok(mini_repo, expected) is True


def test_session_ledger_excludes_every_canvas_filename(mini_repo: Path):
    canvas = mini_repo / "Untitled 37.canvas"
    regular = mini_repo / "work/inbox/kept.md"
    command_support._record_touched(mini_repo, [canvas, regular])
    recorded = json.loads(
        command_support._session_ledger(mini_repo).read_text(encoding="utf-8")
    )
    assert "Untitled 37.canvas" not in recorded
    assert "work/inbox/kept.md" in recorded


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


def test_atomic_transaction_write_fsyncs_file_and_parent_directory(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    calls: list[int] = []
    monkeypatch.setattr(transaction_module.os, "fsync", lambda fd: calls.append(fd))
    target = tmp_path / "durable.yaml"

    transaction_module._atomic_write_bytes(target, b"durable\n")

    assert target.read_bytes() == b"durable\n"
    assert len(calls) == 2


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


def test_transaction_owned_writes_share_the_receipt_identity(tmp_path: Path):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    request = root / "operations/ai-actions/requests/request-demo/request.yaml"
    observed: list[str] = []

    def complete_request(transaction_id: str):
        observed.append(transaction_id)
        return {request: f"status: completed\nreceipt_id: {transaction_id}\n"}

    result = TransactionService(root).commit(
        capability="ai-action.demo",
        writes={target: "demo\n"},
        artifact_ids=["project-demo"],
        transaction_writes=complete_request,
    )

    assert observed == [result.transaction_id]
    assert f"receipt_id: {result.transaction_id}" in request.read_text(encoding="utf-8")
    receipt = yaml.safe_load(result.receipt_path.read_text(encoding="utf-8"))
    assert {row["path"] for row in receipt["writes"]} == {
        "operations/ai-actions/requests/request-demo/request.yaml",
        "projects/registry/project-demo.yaml",
    }


def test_incomplete_rollback_is_reported_with_the_unrestored_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    target = root / "projects/registry/project-demo.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")
    original_write = transaction_module._atomic_write_bytes

    def fail_only_when_restoring(path: Path, content: bytes):
        if path == target and content == b"old\n":
            raise TransactionFailure("forced restore failure")
        return original_write(path, content)

    monkeypatch.setattr(transaction_module, "_atomic_write_bytes", fail_only_when_restoring)
    with pytest.raises(TransactionFailure, match="rollback incomplete for: projects/registry/project-demo.yaml"):
        TransactionService(root).commit(
            capability="project.update",
            writes={target: "new\n"},
            artifact_ids=["project-demo"],
            validate_state=lambda: ["forced validation failure"],
        )

    # The caller is told the truth: this is not presented as a clean rollback.
    assert target.read_text(encoding="utf-8") == "new\n"
