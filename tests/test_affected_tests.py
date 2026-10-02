"""Affected-test discovery must refuse unavailable history, never imply no changes."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "tools/affected_tests.py"


@pytest.fixture
def selector(tmp_path, monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    spec = importlib.util.spec_from_file_location("affected_selector_under_review", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = tmp_path
    return module


def _git(root, *args, input=None):
    return subprocess.run(
        ["git", "-c", "user.name=Selector Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args], cwd=root, input=input,
        text=True, capture_output=True, check=True).stdout.strip()


def _changed_world(root):
    _git(root, "init", "-b", "main")
    (root / "base.txt").write_text("base", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "base")
    _git(root, "checkout", "-b", "review")
    path = root / "tools/learning_os/commands/module.py"
    path.parent.mkdir(parents=True)
    path.write_text("changed Core", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Core change")


def test_missing_base_refuses_instead_of_hiding_committed_changes(selector, capsys):
    _changed_world(selector.ROOT)
    assert selector.main(["--base", "missing"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "cannot determine changed paths" in output.err
    assert "missing" in output.err


def test_unrelated_existing_commit_refuses_instead_of_selecting_no_tests(selector, capsys):
    _changed_world(selector.ROOT)
    tree = _git(selector.ROOT, "mktree", input="")
    unrelated = _git(selector.ROOT, "commit-tree", tree, "-m", "unrelated")
    assert selector.main(["--base", unrelated]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "merge-base" in output.err


def test_git_failure_refuses_but_explicit_files_need_no_git(selector, capsys, monkeypatch):
    _changed_world(selector.ROOT)
    monkeypatch.setenv("GIT_DIR", "/dev/null")
    assert selector.main([]) == 2
    assert capsys.readouterr().out == ""
    assert selector.main(["--files", "tools/learning_os/commands/module.py", "--groups"]) == 0
    assert capsys.readouterr().out.strip() == "gateway studyplan"


@pytest.mark.parametrize("operation", ["merge-base", "diff", "status"])
def test_each_git_discovery_error_refuses(selector, capsys, monkeypatch, operation):
    _changed_world(selector.ROOT)
    execute = selector._git

    def fail(*args):
        if args[0] == operation:
            raise selector.SelectionError(f"{operation} unavailable")
        return execute(*args)

    monkeypatch.setattr(selector, "_git", fail)
    assert selector.main([]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert operation in output.err


def test_valid_common_history_selects_changes_and_clean_head_selects_nothing(selector, capsys):
    _changed_world(selector.ROOT)
    assert selector.main(["--groups"]) == 0
    assert capsys.readouterr().out.strip() == "gateway studyplan"
    assert selector.main(["--base", "HEAD"]) == 0
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == ""
