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


def test_list_limit_selects_newest_first(tmp_path: Path):
    mini = _mini_with_curriculum(tmp_path, "ops-limit-select")
    _write(mini, "ops-limit-select-1")
    _write(mini, "ops-limit-select-2", expected_snapshot="sha256:" + "0" * 64)
    code, body = _operations(mini, "--limit", "1")
    assert code == 0
    assert [row["request_id"] for row in body["operations"]] == [
        "request-ops-limit-select-2"]


def test_list_diagnoses_only_the_requested_recent_operations(tmp_path, monkeypatch):
    """Limit-first plus one shared authority load (the scaling repair).

    Five traced operations with limit=1 must return the newest row while
    loading the receipt inventory exactly once; limit=0 loads nothing.
    """
    from learning_os.commands import operations as ops_surface
    from learning_os.diagnostics.store import traces_path

    root = tmp_path / "ops-shared"
    path = traces_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    ops = [f"{index:032x}" for index in range(5)]
    path.write_text("\n".join(
        json.dumps({
            "schema_version": 1, "conventions_version": 2,
            "timestamp": float(index), "trace_id": op,
            "operation_id": op, "attempt_id": "b" * 16,
            "span_id": "b" * 16, "parent_span_id": None,
            "kind": "span-start", "name": "attempt",
            "stage": None, "status": "ok",
            "attributes": {"capability": "stage.progress.update"},
        })
        for index, op in enumerate(ops)) + "\n", encoding="utf-8")
    calls = []
    real_load = ops_surface.load_authority_files

    def counting(root_arg):
        calls.append(root_arg)
        return real_load(root_arg)

    monkeypatch.setattr(ops_surface, "load_authority_files", counting)
    rows = ops_surface.list_operations(root, limit=1)
    assert [row["trace_id"] for row in rows] == [ops[-1]]
    assert len(calls) == 1
    calls.clear()
    assert ops_surface.list_operations(root, limit=0) == []
    assert calls == []


def test_malformed_authority_leaves_unrelated_operations_inspectable(tmp_path: Path):
    """One corrupt receipt (or ledger) must not break other operations.

    The corrupt file is skipped, recorded as explicit uncertainty on the
    diagnosis, and the unrelated committed write stays COMMITTED.
    """
    import pytest
    import yaml

    from learning_os.diagnostics.resolver import collect_authority

    mini = _mini_with_curriculum(tmp_path, "ops-badauthority")
    _write(mini, "ops-badauthority-ok")
    bad = mini / "operations" / "transactions" / "transaction-zzz-malformed.yaml"
    bad.write_text("[unclosed flow\n  bad: : :\n", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(bad.read_text(encoding="utf-8"))
    code, body = _operations(mini)
    assert code == 0
    assert body["operations"][0]["canonical_outcome"] == "COMMITTED"
    code, detail = _operations(mini, "--request-id", "request-ops-badauthority-ok")
    assert code == 0
    assert detail["diagnosis"]["canonical_outcome"] == "COMMITTED"
    assert any("authority files unreadable" in reason
               for reason in detail["diagnosis"]["reasons"])
    authority = collect_authority(
        mini, request_id="request-ops-badauthority-ok",
        idempotency_key="ops-badauthority-ok",
        capability="stage.progress.update")
    assert bad.relative_to(mini).as_posix() in authority.unreadable_authority
    # A corrupt ledger degrades the same way: no crash, ambiguity recorded.
    ledger = mini / "operations" / "transactions" / "idempotency.yaml"
    ledger.write_text("entries: [broken\n", encoding="utf-8")
    code, body = _operations(mini)
    assert code == 0
    assert body["operations"][0]["canonical_outcome"] == "AMBIGUOUS"


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


def test_wrongly_shaped_and_duplicate_authority_is_reported(tmp_path: Path):
    from learning_os.diagnostics.resolver import load_authority_files

    mini = _mini_with_curriculum(tmp_path, "ops-shapes")
    _write(mini, "ops-shapes-ok")
    _write(mini, "ops-shapes-refused", expected_snapshot="sha256:" + "0" * 64)
    bad = mini / "operations/transactions/transaction-bad-shape.yaml"
    for content in ("request: broken\nstatus: committed\n", "[]\n",
                    "request: {}\nrequest: {}\n"):
        bad.write_text(content, encoding="utf-8")
        assert bad.relative_to(mini).as_posix() in load_authority_files(mini)[2]
        code, body = _operations(mini)
        assert code == 0
        assert [row["canonical_outcome"] for row in body["operations"]] == [
            "NOT_COMMITTED", "COMMITTED"]
    bad.unlink()
    ledger = mini / "operations/transactions/idempotency.yaml"
    for content in ("- wrong shape\n", "entries: []\n", "{}\n",
                    "schema_version: 999\nentries: {}\n"):
        ledger.write_text(content, encoding="utf-8")
        assert ledger.relative_to(mini).as_posix() in load_authority_files(mini)[2]
        code, detail = _operations(mini, "--request-id", "request-ops-shapes-ok")
        assert code == 0
        assert detail["diagnosis"]["canonical_outcome"] == "AMBIGUOUS"
