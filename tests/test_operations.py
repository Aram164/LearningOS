"""The read-only Operations surface behind Diagnostics → Operations."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"


def _mini_with_curriculum(tmp_path: Path, name: str) -> Path:
    from conftest import build_mini_repo
    from repo_builders import add_curriculum

    mini = build_mini_repo(tmp_path / name)
    add_curriculum(mini)
    return mini


def _write(mini: Path, key: str, **overrides) -> dict | None:
    from gateway_helpers import approved_v2_envelope

    from learning_os.contracts.gateway import intent_sha256

    envelope = approved_v2_envelope(
        mini, capability="stage.progress.update",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "status": "complete"},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key=key)
    envelope.update(overrides)
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "capability",
         "stage.progress.update", "--payload-file", "-"],
        input=json.dumps(envelope), capture_output=True, text=True,
        timeout=120)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return None


def _operations(mini: Path, *args: str):
    proc = subprocess.run(
        [sys.executable, str(LOS), "--root", str(mini), "operations", *args],
        capture_output=True, text=True, timeout=120)
    return proc.returncode, json.loads(proc.stdout)


def test_empty_store_lists_nothing(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-empty")
    code, body = _operations(mini)
    assert code == 0
    assert body == {"operations": []}


def test_list_reports_verdicts_newest_first(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-list")
    _write(mini, "ops-list-ok")
    _write(mini, "ops-list-stale", expected_snapshot="sha256:" + "0" * 64)
    code, body = _operations(mini)
    assert code == 0
    rows = body["operations"]
    assert [row["request_id"] for row in rows] == [
        "request-ops-list-stale", "request-ops-list-ok"]
    stale, ok = rows
    assert stale["canonical_outcome"] == "NOT_COMMITTED"
    assert stale["first_failure_stage"] == "core.snapshot_guard"
    assert stale["needs_attention"] is False
    assert ok["canonical_outcome"] == "COMMITTED"
    assert ok["duration_ms"] is not None and ok["duration_ms"] >= 0
    assert ok["attempts"] == 1 and ok["replayed"] is False


def test_list_limit_is_capped(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-limit")
    _write(mini, "ops-limit-1")
    code, body = _operations(mini, "--limit", "500")
    assert code == 0
    assert len(body["operations"]) == 1


def test_detail_explains_one_request(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-detail")
    _write(mini, "ops-detail-ok")
    _write(mini, "ops-detail-stale", expected_snapshot="sha256:" + "0" * 64)
    code, body = _operations(mini, "--request-id", "request-ops-detail-stale")
    assert code == 0
    assert body["request_id"] == "request-ops-detail-stale"
    assert body["diagnosis"]["canonical_outcome"] == "NOT_COMMITTED"
    assert body["ui_outcome"] == "REFUSED"
    assert body["diagnosis"]["first_failure_stage"] == "core.snapshot_guard"
    stages = [(row["stage"], row["state"]) for row in body["timeline"]]
    assert ("Snapshot guard", "failed") in stages
    assert ("Core admitted request", "passed") in stages


def test_detail_unknown_request_is_a_typed_refusal(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-unknown")
    code, body = _operations(mini, "--request-id", "request-nope")
    assert code == 2
    assert body["error"] == "unknown request_id"


def test_operations_is_read_only(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-readonly")
    _write(mini, "ops-readonly-1")
    from learning_os.fingerprint import canonical_fingerprint

    before = canonical_fingerprint(mini)
    store_before = (mini / "operations" / "diagnostics" / "traces.jsonl").read_bytes()
    code, _ = _operations(mini)
    assert code == 0
    code, _ = _operations(mini, "--request-id", "request-ops-readonly-1")
    assert code == 0
    assert canonical_fingerprint(mini) == before
    assert (mini / "operations" / "diagnostics" / "traces.jsonl").read_bytes() == store_before
