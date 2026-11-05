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
             writes: list[dict]) -> None:
    directory = root / "operations" / "transactions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{receipt_id}.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "id": receipt_id,
        "type": "transaction-receipt",
        "status": "committed",
        "snapshot_before": f"sha256:{before}",
        "snapshot_after": f"sha256:{after}",
        "writes": writes,
    }, sort_keys=False), encoding="utf-8")


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
