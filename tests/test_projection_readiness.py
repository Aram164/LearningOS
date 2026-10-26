"""Shared readiness: strict dependency mode vs UI settlement mode."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from learning_os.app.projection_readiness import dependency_ready, observe, settlement_ready  # noqa: E402


def _root(tmp_path, stamp="sB"):
    gen = tmp_path / "generated"
    gen.mkdir(exist_ok=True)
    (gen / "manifest.json").write_text(json.dumps({"_generated": {"snapshot_id": stamp}}))
    (gen / "manifest.identity.json").write_text(json.dumps({"snapshot_id": stamp}))
    rec = tmp_path / "operations/transactions/r1.yaml"
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text("ok: true\n")
    return tmp_path


def test_dependency_ready_at_latest_and_later_known_write(tmp_path):
    root = _root(tmp_path)
    a = {"receipt_path": "operations/transactions/r1.yaml", "snapshot_after": "sA"}
    b = {"receipt_path": "operations/transactions/r1.yaml", "snapshot_after": "sB"}
    assert dependency_ready(root, [a], [a, b]) == (True, "ready")
    assert dependency_ready(root, [b], [a])[0] is False  # predecessor only


def test_unknown_projection_and_missing_receipt_refuse(tmp_path):
    root = _root(tmp_path, stamp="sX")
    b = {"receipt_path": "operations/transactions/r1.yaml", "snapshot_after": "sB"}
    assert dependency_ready(root, [b], [b])[1] == "projection-not-current"
    bad = {"receipt_path": "operations/transactions/nope.yaml", "snapshot_after": "sB"}
    assert dependency_ready(root, [bad], [bad])[0] is False


def test_settlement_mode_separates_completion_from_currency(tmp_path):
    root = _root(tmp_path)
    out = settlement_ready(root, "operations/transactions/r1.yaml", "sOld")
    assert out["write_completed"] is True and out["settled"] is True
    assert observe(root)["published"] is True
