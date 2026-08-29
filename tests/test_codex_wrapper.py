"""Agentic Copilot → Codex safety-wrapper permission tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

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


def test_legacy_operational_marker_fails_closed_to_read_only(monkeypatch):
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    prompt = f"{wrapper.OPERATIONAL} Create the approved path."
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), prompt])
    assert wrapper.main() == 0
    assert len(calls) == 1
    assert calls[0][calls[0].index("--sandbox") + 1] == "read-only"


def test_scoped_capability_grants_write_and_forces_validation(monkeypatch):
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(wrapper, "dirty_paths", lambda: set())
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    prompt = ("[LearningOS capability:stage-note module=module-demo "
              "unit=unit-demo-l01 stage=stage-demo] Save the note.")
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), prompt])
    assert wrapper.main() == 0
    assert calls[0][calls[0].index("--sandbox") + 1] == "workspace-write"
    assert "module-demo" in calls[0][-1]
    assert calls[1][-1] == "validate"
    assert calls[2][-1] == "generate"


def test_capability_scope_allows_only_unit_and_approved_shelving_destinations():
    wrapper = load_wrapper()
    cap = wrapper.parse_capability(
        "[LearningOS capability:shelving-apply module=module-demo unit=unit-demo-l01]")
    prefixes = wrapper.allowed_prefixes(cap)
    assert wrapper.outside_scope({
        "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
        "knowledge/garden/idea.md",
        "Untitled 37.canvas",
        "records/modules.yaml",
    }, prefixes) == {"records/modules.yaml"}


def test_legacy_write_markers_remain_distinct_and_fail_closed():
    wrapper = load_wrapper()
    assert wrapper.SHELVING != wrapper.OPERATIONAL


# ============================================================================
# Phase 3 — the wrapper fails closed on every Git status failure
# (release-hardening 2026-08-29)
# ============================================================================

_SCOPED_PROMPT = ("[LearningOS capability:stage-note module=module-demo "
                  "unit=unit-demo-l01 stage=stage-demo] Save the note.")


class _FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _run_git_status_only(returncode=0, stdout="", stderr=""):
    """A fake ``subprocess.run`` that only understands the git-status call."""
    def fake_run(cmd, **kwargs):
        assert cmd[:2] == ["git", "status"], f"unexpected command: {cmd}"
        return _FakeCompleted(returncode=returncode, stdout=stdout, stderr=stderr)
    return fake_run


def test_dirty_paths_raises_on_nonzero_git_exit(monkeypatch):
    wrapper = load_wrapper()
    monkeypatch.setattr(wrapper.subprocess, "run",
                        _run_git_status_only(returncode=128, stderr="fatal: not a git repository"))
    with pytest.raises(wrapper.GitStatusError):
        wrapper.dirty_paths()


def test_dirty_paths_raises_on_git_timeout(monkeypatch):
    wrapper = load_wrapper()

    def fake_run(cmd, **kwargs):
        raise wrapper.subprocess.TimeoutExpired(cmd=cmd, timeout=30)
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run)
    with pytest.raises(wrapper.GitStatusError):
        wrapper.dirty_paths()


def test_dirty_paths_raises_on_os_error(monkeypatch):
    wrapper = load_wrapper()

    def fake_run(cmd, **kwargs):
        raise OSError("git executable not found")
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run)
    with pytest.raises(wrapper.GitStatusError):
        wrapper.dirty_paths()


def test_dirty_paths_raises_on_malformed_status_line(monkeypatch):
    wrapper = load_wrapper()
    monkeypatch.setattr(wrapper.subprocess, "run",
                        _run_git_status_only(stdout="not a real status line\n"))
    with pytest.raises(wrapper.GitStatusError):
        wrapper.dirty_paths()


def test_preflight_git_failure_never_launches_codex(monkeypatch):
    wrapper = load_wrapper()
    codex_calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")

    def fake_dirty_paths():
        raise wrapper.GitStatusError("git status exited 128: fatal: not a git repository")
    monkeypatch.setattr(wrapper, "dirty_paths", fake_dirty_paths)

    def fake_run(cmd, **kwargs):
        codex_calls.append(cmd)
        return Result()
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), _SCOPED_PROMPT])

    assert wrapper.main() == 2
    assert codex_calls == [], "a preflight status failure must never launch Codex"


def test_postflight_git_failure_never_runs_validation_or_generation(monkeypatch):
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")

    dirty_path_results = iter([set()])

    def fake_dirty_paths():
        try:
            return next(dirty_path_results)
        except StopIteration:
            raise wrapper.GitStatusError("git status timed out") from None
    monkeypatch.setattr(wrapper, "dirty_paths", fake_dirty_paths)

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return Result()
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), _SCOPED_PROMPT])

    assert wrapper.main() == 2
    # Exactly one subprocess call: the Codex run itself. Validation and
    # generation must never follow an unknown post-run repository state.
    assert len(calls) == 1
    assert calls[0][-1] != "validate"
    assert calls[0][-1] != "generate"


def test_ordinary_clean_scoped_write_still_succeeds(monkeypatch):
    """The fail-closed change must not regress the ordinary bounded-write path."""
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(wrapper, "dirty_paths", lambda: set())
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), _SCOPED_PROMPT])
    assert wrapper.main() == 0
    assert calls[1][-1] == "validate"
    assert calls[2][-1] == "generate"


def test_ordinary_bounded_dirty_write_still_succeeds(monkeypatch):
    """A dirty path inside the capability's own unit scope is not a failure."""
    wrapper = load_wrapper()
    calls = []
    monkeypatch.setattr(wrapper, "codex_binary", lambda: "/fake/codex")
    monkeypatch.setattr(
        wrapper, "dirty_paths",
        lambda: {"curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"},
    )
    monkeypatch.setattr(wrapper.subprocess, "run",
                        lambda cmd, **kwargs: calls.append(cmd) or Result())
    monkeypatch.setattr(sys, "argv", [str(WRAPPER), _SCOPED_PROMPT])
    assert wrapper.main() == 0
    assert calls[1][-1] == "validate"
    assert calls[2][-1] == "generate"
