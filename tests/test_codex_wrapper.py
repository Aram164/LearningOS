"""Agentic Copilot → Codex safety-wrapper permission tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


WRAPPER = Path(__file__).resolve().parent.parent / "tools" / "codex_obsidian.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("codex_obsidian_test", WRAPPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Result:
    returncode = 0


def test_ordinary_chat_is_read_only(monkeypatch):
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), "Explain this stage."])
    assert wrapper.main() == 0
    assert len(calls) == 1
    assert calls[0][calls[0].index("--sandbox") + 1] == "read-only"


def test_operational_marker_grants_write_and_forces_validation(monkeypatch):
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    prompt = f"{wrapper.OPERATIONAL} Create the approved path."
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), prompt])
    assert wrapper.main() == 0
    assert calls[0][calls[0].index("--sandbox") + 1] == "workspace-write"
    assert calls[1][-1] == "validate"
    assert calls[2][-1] == "generate"


def test_shelving_and_job_have_distinct_markers():
    wrapper = load_wrapper()
    assert wrapper.SHELVING != wrapper.OPERATIONAL
    assert wrapper.JOB_TASK not in {wrapper.SHELVING, wrapper.OPERATIONAL}
