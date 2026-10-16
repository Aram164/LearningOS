"""The observation seam: overrides fix time, Git reads and ids (PLAN D19)."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from learning_os.store import observations
from learning_os.store.session import githistory

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"

HEAD = "0123456789abcdef0123456789abcdef01234567"
HEAD_TIME = "2026-10-01T09:00:00+02:00"


@pytest.fixture(autouse=True)
def _berlin_time(monkeypatch):
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""
    old = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Europe/Berlin")
    if hasattr(time, "tzset"):
        time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    if hasattr(time, "tzset"):
        time.tzset()


def _write_override(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _git_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict:
    payload = {
        "now": HEAD_TIME,
        "git": {
            "head": HEAD,
            "head_time": HEAD_TIME,
            "dates": {"a.md": "2026-09-01"},
            "timestamps": {"a.md": "1725141600"},
        },
    }
    monkeypatch.setenv(
        observations.OVERRIDE_ENV, _write_override(tmp_path / "obs.json", payload))
    return payload


def test_override_fixes_now_and_today(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    assert observations.now().isoformat() == HEAD_TIME
    assert observations.today().isoformat() == "2026-10-01"


def test_epoch_and_mtime_follow_the_real_clock_without_override(monkeypatch, tmp_path):
    monkeypatch.delenv(observations.OVERRIDE_ENV, raising=False)
    before = time.time()
    during = observations.epoch()
    after = time.time()
    assert before <= during <= after
    probe = tmp_path / "probe.md"
    probe.write_text("x", encoding="utf-8")
    assert observations.mtime(probe, tmp_path) == probe.stat().st_mtime


def test_epoch_is_fixed_now_with_override(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    assert observations.epoch() == observations.now().timestamp()


def test_mtime_reads_the_listed_instant(monkeypatch, tmp_path):
    listed_at = "2026-09-28T09:00:00+02:00"
    payload = {"now": HEAD_TIME, "mtimes": {"work/inbox/note-drop.md": listed_at}}
    monkeypatch.setenv(
        observations.OVERRIDE_ENV, _write_override(tmp_path / "obs.json", payload))
    listed = tmp_path / "work" / "inbox" / "note-drop.md"
    listed.parent.mkdir(parents=True)
    listed.write_text("x", encoding="utf-8")
    assert observations.mtime(listed, tmp_path) == (
        datetime.datetime.fromisoformat(listed_at).timestamp())


def test_mtime_unlisted_and_outside_paths_are_now(monkeypatch, tmp_path):
    payload = {"now": HEAD_TIME,
               "mtimes": {"work/inbox/note-drop.md": "2026-09-28T09:00:00+02:00"}}
    monkeypatch.setenv(
        observations.OVERRIDE_ENV, _write_override(tmp_path / "obs.json", payload))
    root = tmp_path / "root"
    unlisted = root / "work" / "inbox" / "fresh.md"
    unlisted.parent.mkdir(parents=True)
    unlisted.write_text("y", encoding="utf-8")
    assert observations.mtime(unlisted, root) == observations.now().timestamp()
    outside = tmp_path / "outside.md"
    outside.write_text("z", encoding="utf-8")
    assert observations.mtime(outside, root) == observations.now().timestamp()


def test_snapshot_returns_override_head_and_dates(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    snapshot = githistory.fresh_git_snapshot(tmp_path)
    assert snapshot.head == HEAD
    assert snapshot.table == {"a.md": "2026-09-01"}


def test_last_commit_timestamp_returns_override_timestamps(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    assert githistory.last_commit_timestamp(tmp_path, "a.md") == 1725141600.0
    assert githistory.last_commit_date(tmp_path, "a.md") == "2026-09-01"


def test_absent_path_has_no_history(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    assert githistory.last_commit_timestamp(tmp_path, "missing.md") is None
    assert githistory.last_commit_date(tmp_path, "missing.md") == ""


def test_unhandled_read_history_arguments_reach_real_git(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    expected = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%an"],
        capture_output=True, text=True, timeout=60)
    assert expected.returncode == 0
    assert githistory.read_history(REPO_ROOT, "-1", "--format=%an") == expected.stdout
    assert githistory.read_history(REPO_ROOT, "-1", "--format=%H") == HEAD + "\n"


def test_walk_other_formats_reach_real_git(monkeypatch, tmp_path):
    _git_fixture(monkeypatch, tmp_path)
    table = githistory._walk(str(REPO_ROOT), "%an")
    assert table, "an unhandled walk format must still read real Git"


def test_new_hex_random_without_override(monkeypatch):
    monkeypatch.delenv(observations.OVERRIDE_ENV, raising=False)
    first, second = observations.new_hex(), observations.new_hex()
    assert len(first) == 32 and len(second) == 32
    int(first, 16)
    int(second, 16)
    assert first != second


_CHILD = (
    f"import sys; sys.path.insert(0, {str(TOOLS)!r});"
    "from learning_os.store import observations;"
    "print(observations.new_hex())"
)


def _child_ids(payload_path: str, count: int) -> list[str]:
    env = {**os.environ, observations.OVERRIDE_ENV: payload_path,
           "TZ": "Europe/Berlin"}
    ids = []
    for _ in range(count):
        proc = subprocess.run(
            [sys.executable, "-c", _CHILD],
            capture_output=True, text=True, timeout=60, env=env)
        assert proc.returncode == 0, proc.stderr
        ids.append(proc.stdout.strip())
    return ids


def test_new_hex_counter_shared_across_processes(tmp_path):
    counter = tmp_path / "ids.counter"
    payload = {"ids": {"seed": "case/demo", "counter_file": str(counter)}}
    payload_path = _write_override(tmp_path / "obs.json", payload)
    first_run = _child_ids(payload_path, 2)
    assert first_run[0] != first_run[1]
    assert first_run[0] == hashlib.sha256(b"case/demo:0").hexdigest()[:32]
    assert first_run[1] == hashlib.sha256(b"case/demo:1").hexdigest()[:32]
    assert counter.read_text(encoding="utf-8") == "2"
    counter.unlink()
    assert _child_ids(payload_path, 2) == first_run


def test_record_captures_real_observations(monkeypatch, tmp_path):
    record = tmp_path / "record.json"
    monkeypatch.delenv(observations.OVERRIDE_ENV, raising=False)
    monkeypatch.setenv(observations.RECORD_ENV, str(record))
    before = observations.now()
    stored = json.loads(record.read_text(encoding="utf-8"))
    assert stored["now"] == before.isoformat()
    assert "git" not in stored
    snapshot = githistory.fresh_git_snapshot(REPO_ROOT)
    stored = json.loads(record.read_text(encoding="utf-8"))
    assert stored["git"]["head"] == snapshot.head
    assert stored["git"]["dates"] == snapshot.table
    after = observations.now()
    assert after >= before
    assert json.loads(record.read_text(encoding="utf-8"))["now"] == before.isoformat()
