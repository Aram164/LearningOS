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


def test_memo_hits_once_per_epoch_and_pin_change_misses(tmp_path):
    s = ReadSession(_root(tmp_path))
    s.put(("inspect", "x"), {"ok": True})
    assert s.get(("inspect", "x")) == {"ok": True}
    assert s.hits == 1
    (_root(tmp_path) / "generated/manifest.json").write_text('{"_generated":{"snapshot_id":"s2"}}')
    assert s.get(("inspect", "x")) is None  # pin changed: no stale hit


def test_close_ends_epoch(tmp_path):
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
