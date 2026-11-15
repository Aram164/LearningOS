"""The receipt-drift detector: boundary 16's hand-edit hole, measured."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

TOOL = Path(__file__).resolve().parent.parent / "tools" / "receipt_drift.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt(root: Path, receipt_id: str, before: str, after: str,
             writes: list[dict], *, status: str = "committed") -> None:
    directory = root / "operations" / "transactions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{receipt_id}.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "id": receipt_id,
        "type": "transaction-receipt",
        "status": status,
        "snapshot_before": f"sha256:{before}",
        "snapshot_after": f"sha256:{after}",
        "writes": writes,
    }, sort_keys=False), encoding="utf-8")


def _write_receipt_file(root: Path, name: str, receipt: dict) -> None:
    """Write one ledger file verbatim, for receipts the helper cannot build."""
    directory = root / "operations" / "transactions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(yaml.safe_dump(receipt, sort_keys=False),
                                  encoding="utf-8")


def _run(root: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _plan_file(root: Path, name: str, text: str) -> Path:
    path = root / "curriculum" / "modules" / "module-demo" / "units" / "unit-demo" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_clean_ledger_reports_nothing(tmp_path):
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _receipt(tmp_path, "transaction-20261105-000001-001",
             "b" * 64, "c" * 64,
             [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
               "sha256_before": "a" * 64,
               "sha256_after": _sha(plan),
               "created": False}])
    findings = _run(tmp_path)
    assert findings["drift"] == []
    assert findings["untracked"] == []
    assert findings["malformed_receipts"] == []
    assert findings["receipts"] == 1
    assert findings["records_checked"] == 1


def test_hand_edit_and_unreceipted_delete_are_drift(tmp_path):
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    note = tmp_path / "curriculum" / "modules" / "module-demo" / "module.yaml"
    note.write_text("id: module-demo\n", encoding="utf-8")
    chain_head = "c" * 64
    _receipt(tmp_path, "transaction-20261105-000001-001",
             "b" * 64, chain_head,
             [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
               "sha256_before": "a" * 64, "sha256_after": _sha(plan),
               "created": False},
              {"path": "curriculum/modules/module-demo/module.yaml",
               "sha256_before": None, "sha256_after": _sha(note),
               "created": True}])
    # A hand edit after the receipt: the file validates, the ledger disagrees.
    plan.write_text("stages: []\n# hand-tuned\n", encoding="utf-8")
    # A delete after the receipt recorded bytes.
    note.unlink()
    findings = _run(tmp_path)
    drifted = {row["path"] for row in findings["drift"]}
    assert drifted == {
        "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
        "curriculum/modules/module-demo/module.yaml",
    }


def test_recreated_file_after_a_deletion_receipt_is_drift(tmp_path):
    """The last receipt recorded a delete; the file is back with no receipt."""
    path = tmp_path / "curriculum" / "modules" / "module-demo" / "units" / "unit-demo" / "study-map.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stages: []\n", encoding="utf-8")
    _receipt(tmp_path, "transaction-20261105-000001-001",
             "b" * 64, "c" * 64,
             [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
               "sha256_before": "a" * 64, "sha256_after": None,
               "created": False}])
    findings = _run(tmp_path)
    assert len(findings["drift"]) == 1
    assert findings["drift"][0]["note"] == \
        "file exists but the last receipt recorded its deletion"


def test_untracked_record_is_reported(tmp_path):
    _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _receipt(tmp_path, "transaction-20261105-000001-001",
             "b" * 64, "c" * 64, writes=[])
    findings = _run(tmp_path)
    assert findings["untracked"] == [
        "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"]


def test_non_receipt_documents_in_the_ledger_are_malformed(tmp_path):
    directory = tmp_path / "operations" / "transactions"
    directory.mkdir(parents=True)
    (directory / "idempotency.yaml").write_text("entries: []\n", encoding="utf-8")
    findings = _run(tmp_path)
    assert "idempotency.yaml" not in findings["malformed_receipts"]  # glob excludes it
    (directory / "transaction-broken.yaml").write_text("::: not yaml", encoding="utf-8")
    findings = _run(tmp_path)
    assert findings["malformed_receipts"] == ["transaction-broken.yaml"]


def test_malformed_writes_shape_is_reported_not_raised(tmp_path):
    """A typed-but-wrong ``writes`` is MALFORMED, never a traceback.

    Before the shape gate, ``writes: {…}`` or ``writes: [str]`` reached the
    drift loop and crashed on ``row.get`` / ``root / path`` — in --json mode
    with no JSON at all.
    """
    _write_receipt_file(tmp_path, "transaction-20261106-000001-001.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-001",
        "type": "transaction-receipt", "status": "committed",
        "writes": {"curriculum/x.yaml": "a" * 64}})
    _write_receipt_file(tmp_path, "transaction-20261106-000001-002.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-002",
        "type": "transaction-receipt", "status": "committed",
        "writes": ["curriculum/x.yaml"]})
    findings = _run(tmp_path)
    assert findings["drift"] == []
    assert findings["receipts"] == 0
    assert sorted(findings["malformed_receipts"]) == [
        "transaction-20261106-000001-001.yaml",
        "transaction-20261106-000001-002.yaml"]


def test_nonconforming_receipt_id_is_malformed(tmp_path):
    """Lexicographic id order is chronological only for schema-shaped ids."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _write_receipt_file(tmp_path, "transaction-20261106-000001-003.yaml", {
        "schema_version": 1, "id": "transaction-20261106-13",
        "type": "transaction-receipt", "status": "committed",
        "writes": [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
                    "sha256_before": "a" * 64, "sha256_after": _sha(plan),
                    "created": False}]})
    findings = _run(tmp_path)
    assert findings["malformed_receipts"] == ["transaction-20261106-000001-003.yaml"]
    assert findings["receipts"] == 0
    assert findings["untracked"] == [
        "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"]


def test_bad_write_path_or_hash_shape_is_malformed(tmp_path):
    """Non-string/empty paths and hash-shaped violations cannot reach the
    drift loop; they are named in malformed_receipts instead."""
    _write_receipt_file(tmp_path, "transaction-20261106-000001-004.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-004",
        "type": "transaction-receipt", "status": "committed",
        "writes": [{"path": 7, "sha256_before": None, "sha256_after": "a" * 64,
                    "created": False}]})
    _write_receipt_file(tmp_path, "transaction-20261106-000001-005.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-005",
        "type": "transaction-receipt", "status": "committed",
        "writes": [{"path": "", "sha256_before": None, "sha256_after": "a" * 64,
                    "created": False}]})
    _write_receipt_file(tmp_path, "transaction-20261106-000001-006.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-006",
        "type": "transaction-receipt", "status": "committed",
        "writes": [{"path": "curriculum/x.yaml", "sha256_before": None,
                    "sha256_after": "not-a-hash", "created": False}]})
    findings = _run(tmp_path)
    assert sorted(findings["malformed_receipts"]) == [
        "transaction-20261106-000001-004.yaml",
        "transaction-20261106-000001-005.yaml",
        "transaction-20261106-000001-006.yaml"]


def test_duplicate_paths_within_one_receipt_are_malformed(tmp_path):
    """The journal refuses a twice-written path at commit time; the detector
    re-checks the ledger after the fact, so a forged duplicate cannot quietly
    redefine the after-hash by file order."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _write_receipt_file(tmp_path, "transaction-20261106-000001-007.yaml", {
        "schema_version": 1, "id": "transaction-20261106-000001-007",
        "type": "transaction-receipt", "status": "committed",
        "writes": [
            {"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
             "sha256_before": "a" * 64, "sha256_after": _sha(plan), "created": False},
            {"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
             "sha256_before": None, "sha256_after": "f" * 64, "created": True}]})
    findings = _run(tmp_path)
    assert findings["malformed_receipts"] == ["transaction-20261106-000001-007.yaml"]
    assert findings["tracked_paths"] == 0


def test_symlinked_record_is_drift_even_when_bytes_match(tmp_path, tmp_path_factory):
    """A symlink to byte-identical content outside the root hashes to the
    receipted value; provenance is still broken and is reported."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _receipt(tmp_path, "transaction-20261106-000001-008",
             "b" * 64, "c" * 64,
             [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
               "sha256_before": "a" * 64, "sha256_after": _sha(plan),
               "created": False}])
    outside = tmp_path_factory.mktemp("outside-root")
    real = outside / "study-map.yaml"
    real.write_text("stages: []\n", encoding="utf-8")
    plan.unlink()
    plan.symlink_to(real)
    findings = _run(tmp_path)
    assert len(findings["drift"]) == 1
    assert "symlink" in findings["drift"][0]["note"]


def test_non_committed_receipt_is_skipped_and_surfaced(tmp_path):
    """A non-committed row is not authority: counted, skipped, surfaced —
    and the path it would have vouched for stays untracked."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    _receipt(tmp_path, "transaction-20261106-000001-009",
             "b" * 64, "c" * 64,
             [{"path": "curriculum/modules/module-demo/units/unit-demo/study-map.yaml",
               "sha256_before": "a" * 64, "sha256_after": _sha(plan),
               "created": False}],
             status="pending")
    findings = _run(tmp_path)
    assert findings["receipts"] == 1
    assert findings["non_committed_skipped"] == 1
    assert findings["tracked_paths"] == 0
    assert findings["untracked"] == [
        "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"]


def test_chain_break_between_committed_receipts_is_reported_and_gates_check(tmp_path):
    """D-03/D-14: A -> hand edit -> B produces sha256_before != prev.sha256_after."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    h1 = _sha(plan)
    rel = "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"
    _receipt(tmp_path, "transaction-20261106-000001-010",
             "b" * 64, "c" * 64,
             [{"path": rel, "sha256_before": None, "sha256_after": h1, "created": True}])
    plan.write_text("stages: [hand-edited]\n", encoding="utf-8")
    h_hand = _sha(plan)
    plan.write_text("stages: [b-write]\n", encoding="utf-8")
    h2 = _sha(plan)
    _receipt(tmp_path, "transaction-20261106-000001-011",
             "c" * 64, "d" * 64,
             [{"path": rel, "sha256_before": h_hand, "sha256_after": h2, "created": False}])
    findings = _run(tmp_path)
    assert len(findings["chain_breaks"]) == 1
    brk = findings["chain_breaks"][0]
    assert brk["path"] == rel
    assert brk["receipt"] == "transaction-20261106-000001-011"
    assert brk["previous_receipt"] == "transaction-20261106-000001-010"
    assert brk["expected_sha256_before"] == h1
    assert brk["actual_sha256_before"] == h_hand
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(tmp_path), "--check"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    assert "CHAIN-BREAK" in proc.stdout


def test_migration_receipt_is_exempt_from_chain_break(tmp_path):
    """Explicit migration receipts repair chain continuity from their sha256_after."""
    plan = _plan_file(tmp_path, "study-map.yaml", "stages: []\n")
    h1 = _sha(plan)
    rel = "curriculum/modules/module-demo/units/unit-demo/study-map.yaml"
    _receipt(tmp_path, "transaction-20261106-000001-012",
             "b" * 64, "c" * 64,
             [{"path": rel, "sha256_before": None, "sha256_after": h1, "created": True}])
    plan.write_text("stages: [migrated]\n", encoding="utf-8")
    h2 = _sha(plan)
    _write_receipt_file(tmp_path, "transaction-20261106-000001-013.yaml", {
        "schema_version": 1,
        "id": "transaction-20261106-000001-013",
        "type": "transaction-receipt",
        "status": "committed",
        "capability": "migration.test-format-bump",
        "snapshot_before": "sha256:" + "c" * 64,
        "snapshot_after": "sha256:" + "d" * 64,
        "writes": [{"path": rel, "sha256_before": "f" * 64, "sha256_after": h2, "created": False}],
        "metadata": {"migration": "test-format-bump"},
    })
    findings = _run(tmp_path)
    assert findings["chain_breaks"] == []
    assert findings["migration_exempt_breaks"] == 1


def test_validate_gates_chain_break_and_idempotency_rows(mini_repo: Path):
    """D-03/D-18: validator reports TRANSACTION-CHAIN-BREAK and TRANSACTION-IDEMPOTENCY."""
    import hashlib

    import yaml as _yaml
    from repo_builders import add_curriculum

    from learning_os.derive.validation import validate
    from learning_os.store.contracts.gateway import GatewayRequestContext
    from learning_os.store.loader import load_repo
    from learning_os.store.revisions import load_revisions
    from learning_os.store.transactions import TransactionService

    add_curriculum(mini_repo)
    target = mini_repo / "curriculum/programs/program-bachelors.yaml"
    rel = "curriculum/programs/program-bachelors.yaml"
    before_bytes = target.read_bytes()
    h0 = hashlib.sha256(before_bytes).hexdigest()

    # Commit via gateway or receipt directly to test chain break & baseline on program file.
    tx_dir = mini_repo / "operations/transactions"
    tx_dir.mkdir(parents=True, exist_ok=True)
    h1 = hashlib.sha256(b"title: v1\n").hexdigest()
    (tx_dir / "transaction-20261106-000002-001.yaml").write_text(_yaml.safe_dump({
        "schema_version": 1, "id": "transaction-20261106-000002-001",
        "type": "transaction-receipt", "status": "committed",
        "capability": "program.update",
        "snapshot_before": "sha256:" + "0" * 64, "snapshot_after": "sha256:" + "1" * 64,
        "expected_revisions": {}, "artifact_revisions": {},
        "writes": [{"path": rel, "sha256_before": h0, "sha256_after": h1, "created": False}],
    }, sort_keys=False), encoding="utf-8")
    h_hand = hashlib.sha256(b"hand edit\n").hexdigest()
    (tx_dir / "transaction-20261106-000002-002.yaml").write_text(_yaml.safe_dump({
        "schema_version": 1, "id": "transaction-20261106-000002-002",
        "type": "transaction-receipt", "status": "committed",
        "capability": "program.update",
        "snapshot_before": "sha256:" + "1" * 64, "snapshot_after": "sha256:" + "2" * 64,
        "expected_revisions": {}, "artifact_revisions": {},
        "writes": [{"path": rel, "sha256_before": h_hand, "sha256_after": h0, "created": False}],
    }, sort_keys=False), encoding="utf-8")

    chain_issues = [i for i in validate(load_repo(mini_repo), online=False)
                    if i.code == "TRANSACTION-CHAIN-BREAK"]
    assert len(chain_issues) == 1
    assert chain_issues[0].severity == "E"
    assert rel in chain_issues[0].message

    # Baselining clears the error; wrong hashes fail closed.
    baseline_path = mini_repo / "operations/receipt-chain-baseline.yaml"
    baseline_path.write_text(_yaml.safe_dump({
        "schema_version": 1,
        "type": "receipt-chain-baseline",
        "entries": [{
            "transaction": "transaction-20261106-000002-002",
            "path": rel,
            "previous_transaction": "transaction-20261106-000002-001",
            "expected_sha256_before": "e" * 64,
            "actual_sha256_before": h_hand,
            "reason": "Mismatch hash must fail closed.",
            "decided_by": "test",
            "decided_on": "2026-11-15",
        }],
    }, sort_keys=False), encoding="utf-8")
    bad_issues = [i for i in validate(load_repo(mini_repo), online=False)
                  if i.code in {"TRANSACTION-CHAIN-BREAK", "TRANSACTION-CHAIN-BASELINE"}]
    assert any(i.code == "TRANSACTION-CHAIN-BASELINE" for i in bad_issues)
    assert any(i.code == "TRANSACTION-CHAIN-BREAK" for i in bad_issues)

    baseline_path.write_text(_yaml.safe_dump({
        "schema_version": 1,
        "type": "receipt-chain-baseline",
        "entries": [{
            "transaction": "transaction-20261106-000002-002",
            "path": rel,
            "previous_transaction": "transaction-20261106-000002-001",
            "expected_sha256_before": h1,
            "actual_sha256_before": h_hand,
            "reason": "Pre-gate test break.",
            "decided_by": "test",
            "decided_on": "2026-11-15",
        }],
    }, sort_keys=False), encoding="utf-8")
    cleared = [i for i in validate(load_repo(mini_repo), online=False)
               if i.code in {"TRANSACTION-CHAIN-BREAK", "TRANSACTION-CHAIN-BASELINE"}]
    assert cleared == []

    # D-18: deleted receipt referenced by idempotency.yaml fails validation naming key.
    inbox_note = mini_repo / "work/inbox/idem-bind.md"
    ctx = GatewayRequestContext(
        request_id="request-idem-bind",
        idempotency_key="idem-bind-key",
        capability="capture.create",
        channel="codex",
        intent_sha256="sha256:" + "1" * 64,
        approval_kind="operator-approval",
        approval_subject_sha256="sha256:" + "1" * 64,
    )
    res = TransactionService(mini_repo).commit(
        capability="capture.create",
        writes={inbox_note: "captured\n"},
        artifact_ids=["capture:idem-bind"],
        expected_revisions={"capture:idem-bind": load_revisions(mini_repo).get("capture:idem-bind", 0)},
        gateway_request=ctx,
    )
    (mini_repo / res.receipt_path).unlink()
    idem_issues = [i for i in validate(load_repo(mini_repo), online=False)
                   if i.code == "TRANSACTION-IDEMPOTENCY"]
    assert any("idem-bind-key" in i.message for i in idem_issues), idem_issues


def test_validate_reports_unbaselined_on_disk_drift_and_clears_when_baselined(
    mini_repo: Path,
):
    """D-03/D-14: validate() fails with TRANSACTION-DRIFT on post-receipt hand edits."""
    import hashlib

    import yaml as _yaml
    from repo_builders import add_curriculum

    from learning_os.derive.validation import validate
    from learning_os.store.loader import load_repo

    add_curriculum(mini_repo)
    target = mini_repo / "curriculum/programs/program-bachelors.yaml"
    rel = "curriculum/programs/program-bachelors.yaml"
    h0 = hashlib.sha256(target.read_bytes()).hexdigest()

    tx_dir = mini_repo / "operations/transactions"
    tx_dir.mkdir(parents=True, exist_ok=True)
    tx_id = "transaction-20261106-000003-001"
    (tx_dir / f"{tx_id}.yaml").write_text(_yaml.safe_dump({
        "schema_version": 1,
        "id": tx_id,
        "type": "transaction-receipt",
        "status": "committed",
        "capability": "program.update",
        "snapshot_before": "sha256:" + "0" * 64,
        "snapshot_after": "sha256:" + "1" * 64,
        "expected_revisions": {},
        "artifact_revisions": {},
        "writes": [{"path": rel, "sha256_before": "0" * 64, "sha256_after": h0, "created": False}],
    }, sort_keys=False), encoding="utf-8")

    # Hand-edit the tracked file outside the gateway without updating receipts.
    hand_bytes = target.read_bytes() + b"\n# hand edit outside gateway\n"
    target.write_bytes(hand_bytes)
    h_hand = hashlib.sha256(hand_bytes).hexdigest()

    drift_issues = [
        i for i in validate(load_repo(mini_repo), online=False)
        if i.code == "TRANSACTION-DRIFT"
    ]
    assert len(drift_issues) == 1
    assert drift_issues[0].severity == "E"
    assert rel in drift_issues[0].message
    assert tx_id in drift_issues[0].message

    # Recording an accurate historical_drift baseline clears the error; wrong digest fails.
    baseline_path = mini_repo / "operations/receipt-chain-baseline.yaml"
    baseline_path.write_text(_yaml.safe_dump({
        "schema_version": 1,
        "type": "receipt-chain-baseline",
        "entries": [],
        "historical_drift": [{
            "path": rel,
            "receipt": tx_id,
            "expected_sha256": h0,
            "observed_sha256": "f" * 64,
            "reason": "Mismatch hash must fail closed.",
            "decided_by": "test",
            "decided_on": "2026-11-15",
        }],
    }, sort_keys=False), encoding="utf-8")
    mismatch = [
        i for i in validate(load_repo(mini_repo), online=False)
        if i.code == "TRANSACTION-DRIFT"
    ]
    assert len(mismatch) == 1

    baseline_path.write_text(_yaml.safe_dump({
        "schema_version": 1,
        "type": "receipt-chain-baseline",
        "entries": [],
        "historical_drift": [{
            "path": rel,
            "receipt": tx_id,
            "expected_sha256": h0,
            "observed_sha256": h_hand,
            "reason": "Baselined historical drift.",
            "decided_by": "test",
            "decided_on": "2026-11-15",
        }],
    }, sort_keys=False), encoding="utf-8")
    cleared = [
        i for i in validate(load_repo(mini_repo), online=False)
        if i.code in {"TRANSACTION-DRIFT", "TRANSACTION-CHAIN-BASELINE"}
    ]
    assert cleared == []
