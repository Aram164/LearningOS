"""Committed receipts against the live revision ledger (TRANSACTION-REVISION-*).

Every scenario is built from genuine gateway commits. A "rollback" is what
git stash did on 2026-09-29: the revision and idempotency ledgers go back
to their pre-commit bytes while the receipt stays.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import learning_os.derive.validation.projects as projects
import learning_os.derive.validation.receipt_cache as rc
from learning_os.derive.validation import validate
from learning_os.derive.validation.revision_ledger import RETIREMENTS_RELATIVE
from learning_os.store.contracts.gateway import GatewayRequestContext
from learning_os.store.loader import load_repo
from learning_os.store.revisions import dump_revisions, load_revisions
from learning_os.store.transactions import TransactionService

LEDGERS = ("operations/transactions/revisions.yaml",
           "operations/transactions/idempotency.yaml")
RULE_CODES = ("TRANSACTION-REVISION-FLOOR", "TRANSACTION-REVISION-REUSED",
              "TRANSACTION-RETIREMENT", "TRANSACTION-REVISIONS")


def _commit(root: Path, artifact: str, key: str):
    """One genuine v2 capture commit on ``artifact``, at its live revision."""
    target = root / "work" / "inbox" / f"{artifact.removeprefix('capture:')}.md"
    context = GatewayRequestContext(
        request_id=f"request-{key}", idempotency_key=key,
        capability="capture.create", channel="codex",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
    )
    return TransactionService(root).commit(
        capability="capture.create",
        writes={target: f"committed by {key}\n"},
        artifact_ids=[artifact],
        expected_revisions={artifact: load_revisions(root).get(artifact, 0)},
        gateway_request=context,
    )


def _ledgers(root: Path) -> dict[str, bytes | None]:
    return {rel: (root / rel).read_bytes() if (root / rel).exists() else None
            for rel in LEDGERS}


def _roll_back(root: Path, saved: dict[str, bytes | None]) -> None:
    """Put both ledgers back; the receipt and the written file stay."""
    for rel, content in saved.items():
        if content is None:
            (root / rel).unlink(missing_ok=True)
        else:
            (root / rel).write_bytes(content)


def _transaction_id(result) -> str:
    return Path(result.receipt_path).stem


def _rel(root: Path, result) -> str:
    """The receipt path as issues name it (relative to the repository)."""
    return Path(result.receipt_path).resolve().relative_to(root.resolve()).as_posix()


def _findings(root: Path) -> list[tuple[str, str, str, str]]:
    return [(i.severity, i.code, i.path, i.message)
            for i in validate(load_repo(root), online=False)
            if i.code in RULE_CODES
            or (i.code == "SCHEMA" and i.path == RETIREMENTS_RELATIVE)]


def _retire(root: Path, *entries: dict) -> None:
    rows = [{"cause": "rolled-back",
             "reason": "Rolled back outside the gateway in this test scenario.",
             "decided_by": "test", "decided_on": "2026-11-07", **entry}
            for entry in entries]
    (root / RETIREMENTS_RELATIVE).write_text(yaml.safe_dump(
        {"schema_version": 1, "type": "artifact-revision-retirements",
         "retirements": rows}, sort_keys=False), encoding="utf-8")


def _stage_receipt_producers(root: Path) -> None:
    """Copy the real receipt-node producer bytes so verdicts are cached."""
    repo_root = Path(__file__).resolve().parent.parent
    for rel in dict.fromkeys(rc.RECEIPT_PRODUCER_FILES):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((repo_root / rel).read_bytes())


@pytest.fixture
def rolled_back(mini_repo: Path):
    """A receipt whose ledger write a stash took back (the 191223 shape)."""
    saved = _ledgers(mini_repo)
    first = _commit(mini_repo, "capture:x", "key-1")
    _roll_back(mini_repo, saved)
    return mini_repo, first


def test_gateway_history_alone_raises_nothing(mini_repo: Path):
    _commit(mini_repo, "capture:x", "key-1")
    _commit(mini_repo, "capture:x", "key-2")
    _commit(mini_repo, "capture:y", "key-3")
    assert _findings(mini_repo) == []


def test_a_rolled_back_ledger_contradicts_its_receipt(rolled_back):
    root, first = rolled_back
    findings = _findings(root)
    assert [(s, c, p) for s, c, p, _ in findings] == [
        ("E", "TRANSACTION-REVISION-FLOOR", _rel(root, first))]
    assert "'capture:x' has no ledger entry, below the revision 1" in findings[0][3]


def test_a_lowered_entry_names_where_the_ledger_stands(mini_repo: Path):
    _commit(mini_repo, "capture:x", "key-1")
    saved = _ledgers(mini_repo)
    second = _commit(mini_repo, "capture:x", "key-2")
    _roll_back(mini_repo, saved)
    findings = _findings(mini_repo)
    assert [(c, p) for _, c, p, _ in findings] == [
        ("TRANSACTION-REVISION-FLOOR", _rel(mini_repo, second))]
    assert "'capture:x' stands at 1, below the revision 2" in findings[0][3]


def test_a_rewrite_after_the_rollback_is_caught_by_reuse_not_floor(rolled_back):
    """The laundering case: the redo raises the ledger again, so the floor
    holds, and only the duplicate claim still shows the rollback (the
    192027 / 20260930 pairs on main)."""
    root, first = rolled_back
    redo = _commit(root, "capture:x", "key-2")
    findings = _findings(root)
    assert [(c, p) for _, c, p, _ in findings] == [
        ("TRANSACTION-REVISION-REUSED", _rel(root, redo))]
    assert f"recorded by this receipt and by {_rel(root, first)}" in findings[0][3]


def test_a_retirement_clears_exactly_the_named_claim(rolled_back):
    root, first = rolled_back
    redo = _commit(root, "capture:x", "key-2")
    _retire(root, {"transaction": _transaction_id(first), "artifacts": ["capture:x"]})
    assert _findings(root) == []
    # The retirement covers that one receipt's claim, not the artifact:
    # losing the redo's ledger write as well is reported again.
    revisions = dict(load_revisions(root))
    del revisions["capture:x"]
    (root / LEDGERS[0]).write_text(dump_revisions(revisions), encoding="utf-8")
    assert [(c, p) for _, c, p, _ in _findings(root)] == [
        ("TRANSACTION-REVISION-FLOOR", _rel(root, redo))]


def test_a_malformed_retirement_record_retires_nothing(rolled_back):
    root, first = rolled_back
    _retire(root, {"transaction": _transaction_id(first), "artifacts": ["capture:x"]})
    data = yaml.safe_load((root / RETIREMENTS_RELATIVE).read_text(encoding="utf-8"))
    del data["retirements"][0]["decided_by"]
    (root / RETIREMENTS_RELATIVE).write_text(yaml.safe_dump(data), encoding="utf-8")
    codes = sorted(c for _, c, _, _ in _findings(root))
    assert codes == ["SCHEMA", "TRANSACTION-REVISION-FLOOR"]


@pytest.mark.parametrize("entry, expected", [
    ({"transaction": "transaction-20990101-000000-001", "artifacts": ["capture:x"]},
     "is not a committed receipt"),
    ({"transaction": None, "artifacts": ["capture:elsewhere"]},
     "records no revision for 'capture:elsewhere'"),
], ids=["unknown-transaction", "unrecorded-artifact"])
def test_a_retirement_must_name_a_recorded_claim(rolled_back, entry, expected):
    root, first = rolled_back
    entry = dict(entry, transaction=entry["transaction"] or _transaction_id(first))
    _retire(root, entry)
    findings = _findings(root)
    assert sorted(c for _, c, _, _ in findings) == [
        "TRANSACTION-RETIREMENT", "TRANSACTION-REVISION-FLOOR"]
    assert any(c == "TRANSACTION-RETIREMENT" and expected in m and p == RETIREMENTS_RELATIVE
               for _, c, p, m in findings)


def test_a_claim_retired_twice_is_reported_and_still_retired(rolled_back):
    root, first = rolled_back
    entry = {"transaction": _transaction_id(first), "artifacts": ["capture:x"]}
    _retire(root, entry, dict(entry))
    assert [c for _, c, _, _ in _findings(root)] == ["TRANSACTION-RETIREMENT"]


def test_version_one_receipts_are_held_to_the_same_floor(rolled_back):
    """40 of main's 449 artifacts were last written by a v1 receipt."""
    root, first = rolled_back
    path = root / first.receipt_path
    receipt = yaml.safe_load(path.read_text(encoding="utf-8"))
    receipt["schema_version"] = 1
    receipt.pop("authority")
    receipt.pop("request")
    path.write_text(yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8")
    issues = validate(load_repo(root), online=False)
    assert not [i for i in issues if i.path == _rel(root, first) and i.code == "SCHEMA"]
    assert [(i.code, i.path) for i in issues if i.code in RULE_CODES] == [
        ("TRANSACTION-REVISION-FLOOR", _rel(root, first))]


def test_an_unreadable_ledger_is_reported_once(rolled_back):
    root, _first = rolled_back
    (root / LEDGERS[0]).write_text("revisions: [unclosed\n", encoding="utf-8")
    assert [c for _, c, _, _ in _findings(root)] == ["TRANSACTION-REVISIONS"]


def test_a_commit_landing_after_the_receipt_pass_cannot_fake_a_floor(
        mini_repo: Path, monkeypatch):
    """The ledger is read after the receipts, so a concurrent write only
    raises it; reading it first would report the new receipt as broken."""
    _commit(mini_repo, "capture:x", "key-1")
    original = projects.receipt_file_issues

    def receipts_then_a_commit(validator):
        claims = original(validator)
        _commit(mini_repo, "capture:x", "key-2")
        return claims

    monkeypatch.setattr(projects, "receipt_file_issues", receipts_then_a_commit)
    assert _findings(mini_repo) == []


def test_warm_runs_reuse_cached_claims_and_match_cold(rolled_back, monkeypatch):
    root, _first = rolled_back
    _stage_receipt_producers(root)
    cold = _findings(root)
    calls: list[str] = []
    original = rc._validate_fresh

    def counted(validator, path, rel):
        calls.append(rel)
        return original(validator, path, rel)

    monkeypatch.setattr(rc, "_validate_fresh", counted)
    warm = _findings(root)
    assert warm == cold and warm
    assert calls == []  # every receipt's claims came from its cached verdict


def test_a_verdict_without_claims_is_never_served():
    """A version-1 blob (no ``revisions``) is rebuilt, not trusted."""
    verdict = {"sha256": "0" * 64, "parse_failed": False, "id": "transaction-x",
               "idempotency_key": "k", "issues": []}
    assert not rc._valid_verdict(verdict)
    assert rc._valid_verdict(dict(verdict, revisions={"capture:x": 1}))
    assert not rc._valid_verdict(dict(verdict, revisions={"capture:x": True}))
