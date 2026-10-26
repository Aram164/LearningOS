"""ReadSession epoch, memo eligibility, and parallel-wave proof."""
from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from learning_os.adapters.agent_workers import parallel_reads  # noqa: E402
from learning_os.app.read_session import ReadSession  # noqa: E402


def _root(tmp_path):
    gen = tmp_path / "generated"
    gen.mkdir(exist_ok=True)
    (gen / "manifest.json").write_text('{"_generated":{"snapshot_id":"s1"}}')
    (gen / "manifest.identity.json").write_text('{"snapshot_id":"s1"}')
    return tmp_path


def test_memo_hits_once_per_epoch_and_pin_change_misses(mini_repo):
    tmp_path = mini_repo
    s = ReadSession(_root(tmp_path))
    s.put(("inspect", "x"), {"ok": True})
    assert s.get(("inspect", "x")) == {"ok": True}
    assert s.hits == 1
    (_root(tmp_path) / "generated/manifest.json").write_text('{"_generated":{"snapshot_id":"s2"}}')
    assert s.get(("inspect", "x")) is None  # pin changed: no stale hit


def test_close_ends_epoch(mini_repo):
    tmp_path = mini_repo
    s = ReadSession(_root(tmp_path))
    s.put(("a",), 1)
    s.close()
    assert s.get(("a",)) is None


def test_parallel_reads_overlap_and_preserve_order(tmp_path):
    barrier = threading.Barrier(2)

    def slow(argv):
        barrier.wait(timeout=10)
        return 0, argv[0], ""

    out = parallel_reads(tmp_path, [["a"], ["b"]], 2, executor=slow)
    assert [r[1] for r in out] == ["a", "b"]  # overlap proved by barrier


def test_cancellable_worker_never_recovers_or_escalates(mini_repo, monkeypatch):
    import pytest

    from learning_os.app import lock
    from learning_os.domain.failures import WriteRefused

    calls = []
    monkeypatch.setenv(lock.LOS_DEFER_RECOVERY_ENV, '1')
    monkeypatch.setattr(lock, 'reconcile_inflight_transactions', lambda *_: calls.append('recover'))
    with pytest.raises(WriteRefused, match='deferred'):
        with lock.operator_lock(mini_repo):
            pass
    with lock.operator_lock(mini_repo, shared=True):
        before = lock._HELD_OPERATOR_LOCKS.get()
        with pytest.raises(WriteRefused, match='deferred'):
            lock.escalate_operator_lock(mini_repo)
        assert lock._HELD_OPERATOR_LOCKS.get() == before
        with pytest.raises(WriteRefused, match='deferred'):
            with lock.operator_lock(mini_repo):
                pass
        with lock.operator_lock(mini_repo, shared=True):
            assert lock._HELD_OPERATOR_LOCKS.get() == before
    journal = mini_repo / 'operations/transactions/.inflight/armed'
    journal.mkdir(parents=True)
    with pytest.raises(WriteRefused, match='foreground recovery'):
        with lock.operator_lock(mini_repo, shared=True):
            pass
    assert journal.is_dir() and calls == []
