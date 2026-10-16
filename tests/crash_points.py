"""Named engine crash points for the recovery scenarios (SPEC A16).

This generalizes the crash wrapper from ``tests/test_transactions.py:1014``:
a child process runs the real ``los`` entry with the transaction engine
patched at one named point. The point writes its marker file, then the child
dies via ``os._exit``. Deliberately crashed children are launched with
``LOS_ARCH_EXPECT_CRASH=1``, so the missing ``completed`` witness is expected
(SPEC §3.2(c), amended (j)).

A point is selected with ``LOS_CRASH_POINT``; the marker path comes from
``LOS_CRASH_MARKER``; ``LOS_CRASH_TOOLS`` names the Core ``tools/`` directory.
``LOS_CRASH_POINT=none`` runs the child unpatched (used with the start gate
below). Everything after the ``--`` separator becomes the ``los`` argv.
"""

from __future__ import annotations

from pathlib import Path

#: The six crash points, in commit order.
POINTS = (
    "before-first-write",
    "after-first-write",
    "after-writes-before-validation",
    "after-validation-before-publish",
    "after-publish-before-receipt",
    "after-receipt-before-bookkeeping",
)

#: How a deliberately crashed child dies (distinct from 0/1/2/3).
CRASH_EXIT = 77

#: Unpatched run (only the start gate, when set, still applies).
NO_CRASH = "none"

WRAPPER_SOURCE = '''\
"""S07 crash wrapper: patch the engine at LOS_CRASH_POINT, then run los."""
import functools
import os
import sys
from pathlib import Path as _Path

sys.path.insert(0, os.environ["LOS_CRASH_TOOLS"])

POINT = os.environ.get("LOS_CRASH_POINT", "none")
MARKER = os.environ.get("LOS_CRASH_MARKER", "")
KNOWN = (
    "before-first-write",
    "after-first-write",
    "after-writes-before-validation",
    "after-validation-before-publish",
    "after-publish-before-receipt",
    "after-receipt-before-bookkeeping",
    "none",
)
if POINT not in KNOWN:
    raise RuntimeError(f"unknown crash point: {POINT}")

# Optional start gate: wait until a new transaction receipt lands. The wait
# models a slow client, so a concurrent submission deterministically finds
# the committed row instead of racing it. Timing only; no behaviour changes.
GATE_DIR = os.environ.get("LOS_CRASH_GATE_DIR", "")
GATE_BEFORE = os.environ.get("LOS_CRASH_GATE_BEFORE", "[]")
if GATE_DIR:
    import json
    import time

    _before = set(json.loads(GATE_BEFORE))
    _deadline = time.monotonic() + 180
    while True:
        _now = {p.name for p in _Path(GATE_DIR).glob("transaction-*.yaml")}
        if _now - _before:
            break
        if time.monotonic() > _deadline:
            raise RuntimeError("crash gate timed out waiting for a receipt")
        time.sleep(0.05)

from learning_os.store import transactions  # noqa: E402
import los  # noqa: E402


def _crash():
    with open(MARKER, "w", encoding="utf-8") as handle:
        handle.write(POINT)
    os._exit(77)


if POINT in ("before-first-write", "after-first-write"):
    _original_write = transactions.atomic_write_bytes
    _armed = True

    def _counting_write(path, content):
        global _armed
        # Staging and journal bytes under .inflight are not the write the
        # point names; only the first write outside them can crash here.
        if _armed and ".inflight" not in _Path(path).parts:
            _armed = False
            if POINT == "before-first-write":
                _crash()
            _original_write(path, content)
            _crash()
        else:
            _original_write(path, content)

    transactions.atomic_write_bytes = _counting_write
elif POINT != "none":
    _original_commit = transactions.TransactionService.commit

    def _patched_commit(self, *args, **kwargs):
        if POINT == "after-writes-before-validation":
            if kwargs.get("validate_state") is None:
                raise RuntimeError("after-writes-before-validation needs validate_state")

            def _validate(*a, **k):
                _crash()

            kwargs["validate_state"] = _validate
        elif POINT == "after-validation-before-publish":
            if kwargs.get("validate_state") is None:
                raise RuntimeError("after-validation-before-publish needs validate_state")
            _original_validate = kwargs["validate_state"]

            @functools.wraps(_original_validate)
            def _validate(*a, **k):
                _original_validate(*a, **k)
                _crash()

            kwargs["validate_state"] = _validate
        elif POINT == "after-publish-before-receipt":
            if kwargs.get("publish") is None:
                raise RuntimeError("after-publish-before-receipt needs publish")
            _original_publish = kwargs["publish"]

            @functools.wraps(_original_publish)
            def _publish(*a, **k):
                _original_publish(*a, **k)
                _crash()

            kwargs["publish"] = _publish
        elif POINT == "after-receipt-before-bookkeeping":
            if kwargs.get("touched") is None:
                raise RuntimeError("after-receipt-before-bookkeeping needs touched")

            def _touched(*a, **k):
                _crash()

            kwargs["touched"] = _touched
        return _original_commit(self, *args, **kwargs)

    transactions.TransactionService.commit = _patched_commit

_separator = sys.argv.index("--")
sys.argv = [sys.argv[0], *sys.argv[_separator + 1:]]
raise SystemExit(los.main())
'''


def write_wrapper(path: Path) -> Path:
    """Write the crash wrapper script; returns its path."""
    path = Path(path)
    path.write_text(WRAPPER_SOURCE, encoding="utf-8")
    return path


def crash_env(*, point: str, marker: Path, tools_dir: Path,
              gate_dir: Path | None = None,
              gate_before: list[str] | None = None) -> dict[str, str]:
    """Extra child environment for one crash-wrapper launch."""
    import json

    env = {
        "LOS_CRASH_POINT": point,
        "LOS_CRASH_MARKER": str(marker),
        "LOS_CRASH_TOOLS": str(tools_dir),
    }
    if point != NO_CRASH:
        env["LOS_ARCH_EXPECT_CRASH"] = "1"
    if gate_dir is not None:
        env["LOS_CRASH_GATE_DIR"] = str(gate_dir)
        env["LOS_CRASH_GATE_BEFORE"] = json.dumps(list(gate_before or []))
    return env
