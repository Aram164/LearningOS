"""Git co-occurrence is evidence to inspect, never proof of gateway mediation."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "tools/plan_write_audit.py"
PLAN = "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"
RECEIPT = "operations/transactions/transaction-demo.yaml"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=Audit Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args], cwd=root,
        text=True, capture_output=True, check=True).stdout.strip()


def _write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _commit(root: Path, subject: str, files: dict[str, str]) -> str:
    for path, text in files.items():
        _write(root, path, text)
    _git(root, "add", ".")
    _git(root, "commit", "-m", subject)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def audit(tmp_path, monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    spec = importlib.util.spec_from_file_location("plan_audit_under_review", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPO = tmp_path
    _git(tmp_path, "init", "-b", "main")
    return module


def test_receipt_cooccurrence_excludes_ledgers_and_existing_receipt_edits(audit, capsys):
    root = audit.REPO
    _commit(root, "plan with an unrelated receipt", {
        PLAN: "title: first\n",
        RECEIPT: "type: transaction-receipt\nwrites: [{path: work/unrelated.md}]\n",
        "operations/transactions/revisions.yaml": "type: artifact-revision-ledger\n",
    })
    ledger_edit = _commit(root, "plan and ledger edit", {
        PLAN: "title: second\n",
        "operations/transactions/revisions.yaml": "type: artifact-revision-ledger\nx: 1\n",
    })
    receipt_edit = _commit(root, "plan and existing receipt edit", {
        PLAN: "title: third\n",
        RECEIPT: "type: transaction-receipt\nwrites: []\n",
    })
    assert not audit.receipt_added(ledger_edit)
    assert not audit.receipt_added(receipt_edit)
    assert audit.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "commits that changed a plan record : 3" in output
    assert "also adding a receipt document   : 1 (33%)" in output
    assert "without a receipt addition       : 2" in output
    assert "receipt documents in working tree  : 1" in output
    listed = output.split("newest first:", 1)[1]
    assert "plan and ledger edit" in listed
    assert "plan and existing receipt edit" in listed
    assert "plan with an unrelated receipt" not in listed
    assert "not gateway mediation or per-write" in output
    assert "Receipt schemas, write" in output
    assert "off-gateway" not in output


def test_added_ledgers_and_misnamed_non_receipts_do_not_count(audit, capsys):
    _commit(audit.REPO, "plan and operational records", {
        PLAN: "title: first\n",
        "operations/transactions/transaction-not-a-receipt.yaml": "type: artifact-revision-ledger\n",
        "operations/transactions/idempotency.yaml": "type: transaction-idempotency-ledger\n",
        "operations/transactions/lineage.yaml": "type: semantic-lineage-ledger\n",
        "operations/transactions/list.yaml": "- transaction-receipt\n",
        "operations/transactions/readme.yaml": "null\n",
        "operations/transactions/not-yaml.txt": "type: transaction-receipt\n",
    })
    assert audit.main([]) == 0
    output = capsys.readouterr().out
    assert "also adding a receipt document   : 0 (0%)" in output
    assert "receipt documents in working tree  : 0" in output


@pytest.mark.parametrize("original", [RECEIPT, "work/archived-receipt.yaml"])
def test_receipt_rename_is_not_a_new_addition(audit, original):
    _commit(audit.REPO, "original receipt", {
        original: "type: transaction-receipt\nwrites: []\n",
    })
    renamed = "operations/transactions/renamed-receipt.yaml"
    (audit.REPO / renamed).parent.mkdir(parents=True, exist_ok=True)
    _git(audit.REPO, "mv", original, renamed)
    commit = _commit(audit.REPO, "plan and receipt rename", {PLAN: "title: first\n"})
    assert not audit.receipt_added(commit)
    assert audit.receipts_on_disk() == 1


def test_migration_and_direct_edit_are_listed_without_claiming_bypass(audit, capsys):
    _commit(audit.REPO, "recorded migration", {
        "curriculum/paths/old-path.yaml": "title: old layout\n",
        "tools/migrations/demo.py": "# recorded migration\n",
    })
    _write(audit.REPO, PLAN, "title: moved plan\n")
    _git(audit.REPO, "rm", "curriculum/paths/old-path.yaml")
    _commit(audit.REPO, "move into partitioned layout", {})
    _commit(audit.REPO, "direct plan edit", {PLAN: "title: changed plan\n"})
    assert len(audit.commits_touching(audit.PLAN_PATHS)) == 3
    assert audit.main(["--list"]) == 0
    output = capsys.readouterr().out
    assert "without a receipt addition       : 3" in output
    assert "recorded migration" in output
    assert "move into partitioned layout" in output
    assert "direct plan edit" in output
    assert "recorded migrations are legitimate" in output


def test_all_refs_scope_and_disk_inventory_are_separate(audit, capsys):
    root = audit.REPO
    _commit(root, "main plan", {PLAN: "title: main\n"})
    _git(root, "checkout", "-b", "unmerged-work")
    _commit(root, "branch plan with receipt", {
        PLAN: "title: branch\n", RECEIPT: "type: transaction-receipt\n",
    })
    _git(root, "checkout", "main")
    _write(root, "operations/transactions/uncommitted.yaml", "type: transaction-receipt\n")
    _write(root, PLAN, "title: uncommitted plan\n")
    assert audit.main([]) == 0
    output = capsys.readouterr().out
    assert "history scope: all refs available in this clone (git log --all)" in output
    assert "commits that changed a plan record : 2" in output
    assert "also adding a receipt document   : 1 (50%)" in output
    assert "receipt documents in working tree  : 1" in output
    assert "Uncommitted, unreachable and unavailable history" in output
    assert "shallow or incomplete clone" in output


@pytest.mark.parametrize("new_receipt", [False, True])
def test_merge_only_counts_a_receipt_added_relative_to_every_parent(audit, new_receipt):
    root = audit.REPO
    _commit(root, "base plan", {PLAN: "title: first\n"})
    _git(root, "checkout", "-b", "feature")
    _commit(root, "branch plan with receipt", {
        PLAN: "title: branch\n", RECEIPT: "type: transaction-receipt\n",
    })
    _git(root, "checkout", "main")
    _commit(root, "main work", {"README.md": "# main\n"})
    _git(root, "merge", "--no-ff", "--no-commit", "feature")
    files = {"operations/transactions/merge.yaml": "type: transaction-receipt\n"} \
        if new_receipt else {}
    merge = _commit(root, "merge feature", files)
    assert audit.receipt_added(merge) is new_receipt


def test_invalid_transaction_yaml_refuses_a_partial_receipt_count(audit, capsys):
    _commit(audit.REPO, "plan with invalid transaction YAML", {
        PLAN: "title: first\n", RECEIPT: "type: [\n",
    })
    with pytest.raises(SystemExit, match="transaction YAML could not be inspected"):
        audit.main([])
    assert capsys.readouterr().out == ""


def test_invalid_working_tree_yaml_refuses_before_reporting_counts(audit, capsys):
    _commit(audit.REPO, "plan", {PLAN: "title: first\n"})
    _write(audit.REPO, RECEIPT, "type: [\n")
    with pytest.raises(SystemExit, match="transaction YAML could not be inspected"):
        audit.main([])
    assert capsys.readouterr().out == ""


def test_no_plan_history_is_a_successful_empty_report(audit, capsys):
    _commit(audit.REPO, "unrelated", {"README.md": "# demo\n"})
    assert audit.main(["--list"]) == 0
    assert "no commits touch a plan record" in capsys.readouterr().out
