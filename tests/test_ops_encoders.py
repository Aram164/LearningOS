"""Shared JSON encoders (P6-02 Task 1, PLAN 6.A.1 OD4a)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from learning_os.ops import encoders

ROOT = Path(__file__).resolve().parent.parent

PAYLOAD = {"z": "café ☃", "a": [3, 1, {"b": "ü"}]}


class _FakeStdout:
    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_dumps_unescaped():
    assert encoders.dumps_unescaped(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False
    )


def test_dumps_compact():
    assert encoders.dumps_compact(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, separators=(",", ":")
    )


def test_dumps_indented():
    assert encoders.dumps_indented(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2
    )


def test_dumps_ascii():
    assert encoders.dumps_ascii(PAYLOAD) == json.dumps(PAYLOAD)


def test_dumps_sorted():
    assert encoders.dumps_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, sort_keys=True
    )


def test_dumps_indented_sorted():
    assert encoders.dumps_indented_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2, sort_keys=True
    )


def test_dumps_layout_sorted(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStdout(True))
    assert encoders.dumps_layout_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, indent=2, sort_keys=True, ensure_ascii=False
    )
    monkeypatch.setattr(sys, "stdout", _FakeStdout(False))
    assert encoders.dumps_layout_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, separators=(",", ":"), sort_keys=True, ensure_ascii=False
    )


def test_no_dumps_definitions_remain():
    pattern = re.compile(r"def _dumps_")
    hits = []
    base = ROOT / "tools" / "learning_os"
    for path in sorted(base.rglob("*.py")):
        if pattern.search(path.read_text(encoding="utf-8")):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []
