"""Disposable report retention and append-only recovery corrections."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from learning_os.app.agent_reporting import (
    RETENTION_MARKER,
    ReportStore,
    expand_report,
    prune_reports,
    write_full_report,
)


def _run(root, parent, *, keep=False, finalize=True):
    with ReportStore(root, parent, keep_report=keep) as store:
        store.inputs({"steps": []}, [])
        if finalize:
            write_full_report(store.path, {"schema_version": 2, "steps": [], "totals": {},
                                          "full_report": str(store.full_path)})
        return store.path


def _created(path, created_ns):
    marker = path / RETENTION_MARKER
    data = json.loads(marker.read_text())
    data["created_ns"] = created_ns
    marker.write_text(json.dumps(data))


def test_new_runs_retain_the_newest_fifty(tmp_path):
    parent = tmp_path / "reports"
    paths = [_run(tmp_path / "root", parent) for _ in range(52)]
    assert not paths[0].exists() and not paths[1].exists()
    assert all(path.is_dir() for path in paths[2:])
    assert len(list(parent.iterdir())) == 50


def test_retention_preserves_active_and_kept_reports(tmp_path):
    parent = tmp_path / "reports"
    expired = _run(tmp_path / "root", parent)
    kept = _run(tmp_path / "root", parent, keep=True)
    now = time.time_ns()
    old = now - 15 * 24 * 60 * 60 * 1_000_000_000
    _created(expired, old)
    _created(kept, old)
    with ReportStore(tmp_path / "root", parent) as active:
        _created(active.path, old)
        prune_reports(parent, now_ns=now, max_runs=0)
        assert active.path.is_dir()
        assert kept.is_dir()
        assert not expired.exists()
    prune_reports(parent, now_ns=now, max_runs=0)
    assert not active.path.exists() and kept.is_dir()


def test_retention_does_not_touch_unowned_or_symlinked_directories(tmp_path):
    parent = tmp_path / "reports"
    parent.mkdir()
    unrelated = parent / "los-agent-plan-unrelated"
    unrelated.mkdir()
    (unrelated / "important.txt").write_text("preserve")
    target = _run(tmp_path / "root", tmp_path / "elsewhere")
    link = parent / "los-agent-plan-linked"
    link.symlink_to(target, target_is_directory=True)
    assert prune_reports(parent, max_runs=0) == []
    assert target.is_dir() and link.is_symlink()
    assert (unrelated / "important.txt").read_text() == "preserve"


def test_invalid_marker_is_preserved_instead_of_treated_as_legacy(tmp_path):
    path = _run(tmp_path / "root", tmp_path / "reports")
    (path / RETENTION_MARKER).write_text('{"kind":"other-app"}')
    assert prune_reports(path.parent, max_runs=0) == []
    assert path.is_dir()


def test_only_finalized_digest_bound_legacy_reports_are_pruned(tmp_path):
    parent = tmp_path / "reports"
    completed = _run(tmp_path / "root", parent)
    partial = _run(tmp_path / "root", parent, finalize=False)
    corrupt = _run(tmp_path / "root", parent)
    for path in (completed, partial, corrupt):
        (path / RETENTION_MARKER).unlink()
    (corrupt / "full-report.sha256").write_text("0" * 64)
    assert prune_reports(parent, max_runs=0) == [completed]
    assert partial.is_dir() and corrupt.is_dir()


def test_report_parent_cannot_be_inside_data_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError, match="outside"):
        ReportStore(root, root / "reports")
    assert not (root / "reports").exists()


def test_correction_appends_evidence_and_detaches_mutable_rows(tmp_path):
    with ReportStore(tmp_path / "root", tmp_path / "reports") as store:
        row = {"id": "read", "status": "ok", "commit_certainty": "none", "output": {"answer": 1}}
        store.record(row)
        row.update(status="error", error={"code": "SNAPSHOT_CONFLICT", "retryable": True})
        row.pop("output")
        assert store.rows[0]["status"] == "ok"
        store.correct(row)
        entries = [json.loads(line) for line in (store.path / "checkpoint.jsonl").read_text().splitlines()]
        assert entries[0]["status"] == "ok" and entries[0]["output"] == {"answer": 1}
        assert entries[1] == {"event": "step-correction", "details_index": 0, "row": row}
        assert store.rows == [row] and store.rows[0] is not row


def test_correction_cannot_erase_commit_receipt(tmp_path):
    with ReportStore(tmp_path / "root", tmp_path / "reports") as store:
        row = {"id": "write", "status": "ok", "commit_certainty": "committed",
               "receipt": {"receipt_path": "operations/transactions/one.yaml", "snapshot_after": "sha256:one"}}
        store.record(row)
        with pytest.raises(ValueError, match="cannot erase"):
            store.correct({"id": "write", "status": "error", "commit_certainty": "none"})
        assert len((store.path / "checkpoint.jsonl").read_text().splitlines()) == 1


def test_correction_requires_an_existing_step(tmp_path):
    with ReportStore(tmp_path / "root", tmp_path / "reports") as store:
        with pytest.raises(ValueError, match="unrecorded"):
            store.correct({"id": "unknown", "status": "error", "commit_certainty": "none"})


def test_expansion_holds_a_read_lease_against_retention(tmp_path, monkeypatch):
    path = _run(tmp_path / "root", tmp_path / "reports")
    full = path / "full-report.json"
    original = Path.read_bytes

    def prune_after_body_read(candidate):
        body = original(candidate)
        if candidate == full:
            assert prune_reports(path.parent, max_runs=0) == []
            assert path.is_dir()
        return body

    monkeypatch.setattr(Path, "read_bytes", prune_after_body_read)
    assert expand_report(full)["schema_version"] == 2
    assert prune_reports(path.parent, max_runs=0) == [path]


def test_expansion_of_an_active_report_refuses_without_waiting(tmp_path):
    with ReportStore(tmp_path / "root", tmp_path / "reports") as store:
        write_full_report(store.path, {"schema_version": 2, "steps": [], "totals": {}})
        with pytest.raises(ValueError, match="still active"):
            expand_report(store.full_path)
