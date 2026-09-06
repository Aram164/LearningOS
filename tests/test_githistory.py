"""History failures stay distinct from exports, unborn branches and empty logs."""

import subprocess

import pytest

from learning_os import githistory
from learning_os.errors import TransactionFailure
from learning_os.genout import generate_all
from learning_os.genout.common import _git_last_commit, stable_generated_at
from learning_os.loader import load_repo
from learning_os.rules.common import BASELINE_EXEMPT_WARNINGS
from learning_os.rules.core import Validator


@pytest.fixture(autouse=True)
def isolated_history(monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    for name in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
        monkeypatch.setenv(name, "2020-01-02T03:04:05+00:00")
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()
    yield
    githistory.last_commit_dates.cache_clear()
    githistory.last_commit_timestamps.cache_clear()


def git(root, *args):
    return subprocess.run(
        ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args],
        cwd=root, check=True, capture_output=True, text=True,
    ).stdout.strip()


def init_repo(root, *, commit=True):
    git(root, "init")
    if commit:
        (root / "folder").mkdir()
        (root / "folder" / "file.txt").write_text("hello", encoding="utf-8")
        git(root, "add", "folder/file.txt")
        git(root, "commit", "-m", "initial")


def assert_empty(root):
    assert githistory.last_commit_dates(str(root)) == {}
    assert githistory.last_commit_timestamps(str(root)) == {}
    assert githistory.last_commit_date(root, "folder") == ""
    assert githistory.last_commit_timestamp(root, "folder") is None
    assert stable_generated_at(root) == "(no Git history available)"


def test_plain_directory(tmp_path):
    assert_empty(tmp_path)


def test_export_does_not_inherit_parent_history(tmp_path):
    init_repo(tmp_path)
    export = tmp_path / "export"
    export.mkdir()
    assert_empty(export)


def test_empty_repository(tmp_path):
    init_repo(tmp_path, commit=False)
    assert_empty(tmp_path)


@pytest.mark.parametrize("kind", ["export", "unborn", "committed"])
def test_invalid_git_environment_is_not_empty(tmp_path, monkeypatch, kind):
    if kind != "export":
        init_repo(tmp_path, commit=kind == "committed")
    monkeypatch.setenv("GIT_DIR", "/dev/null")
    for lookup in (githistory.last_commit_dates, githistory.last_commit_timestamps):
        with pytest.raises(githistory.GitHistoryError, match="fatal:.*not a git repository"):
            lookup(str(tmp_path))
        assert lookup.cache_info().currsize == 0


def test_explicit_git_environment_is_honored(tmp_path, monkeypatch):
    init_repo(tmp_path)
    export = tmp_path / "export"
    export.mkdir()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))
    assert githistory.last_commit_date(export, "folder") == "2020-01-02"


@pytest.mark.parametrize("lookup", [githistory.last_commit_dates, githistory.last_commit_timestamps])
@pytest.mark.parametrize("failure", ["exit", "timeout", "missing-executable"])
def test_failed_log_preserves_diagnostic_and_is_not_cached(tmp_path, monkeypatch, lookup, failure):
    init_repo(tmp_path)
    run = subprocess.run

    def fail_log(args, **kwargs):
        if args[1] == "log":
            if failure == "timeout":
                raise subprocess.TimeoutExpired(args, 120, stderr=b"history timed out")
            if failure == "missing-executable":
                raise FileNotFoundError("history executable missing")
            # Even parseable partial output must never become cached history.
            return subprocess.CompletedProcess(args, 128, "\x002000-01-01\nwrong.txt\n", "history broken")
        return run(args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(githistory.subprocess, "run", fail_log)
        with pytest.raises(githistory.GitHistoryError, match="history"):
            lookup(str(tmp_path))
        assert lookup.cache_info().currsize == 0
    assert "folder/file.txt" in lookup(str(tmp_path))


def test_successful_empty_log(tmp_path, monkeypatch):
    init_repo(tmp_path)
    run = subprocess.run

    def empty_log(args, **kwargs):
        if args[1] == "log":
            return subprocess.CompletedProcess(args, 0, "", "")
        return run(args, **kwargs)

    monkeypatch.setattr(githistory.subprocess, "run", empty_log)
    assert_empty(tmp_path)


@pytest.mark.parametrize("corruption", ["head", "object"])
def test_corrupt_repository_is_not_unborn(tmp_path, corruption):
    init_repo(tmp_path)
    if corruption == "head":
        (tmp_path / ".git" / "HEAD").write_text("invalid HEAD\n", encoding="utf-8")
    else:
        oid = git(tmp_path, "rev-parse", "HEAD")
        (tmp_path / ".git" / "objects" / oid[:2] / oid[2:]).unlink()
    with pytest.raises(githistory.GitHistoryError):
        githistory.last_commit_dates(str(tmp_path))


def test_real_repository_success(tmp_path):
    init_repo(tmp_path)
    assert githistory.last_commit_dates(str(tmp_path)) == {"folder/file.txt": "2020-01-02"}
    assert githistory.last_commit_date(tmp_path, "folder") == "2020-01-02"
    assert githistory.last_commit_timestamp(tmp_path, "folder") == 1577934245.0
    assert githistory.last_commit_date(tmp_path, "missing") == ""
    assert stable_generated_at(tmp_path) == "2020-01-02T03:04:05+00:00 (last commit)"


def test_gitfile_repository(tmp_path):
    init_repo(tmp_path)
    metadata = tmp_path / "metadata"
    (tmp_path / ".git").rename(metadata)
    (tmp_path / ".git").write_text(f"gitdir: {metadata}\n", encoding="utf-8")
    assert githistory.last_commit_date(tmp_path, "folder") == "2020-01-02"


def test_bare_repository_without_commits(tmp_path):
    git(tmp_path, "init", "--bare")
    assert_empty(tmp_path)


def test_history_is_scoped_to_head(tmp_path):
    init_repo(tmp_path)
    # Other branches still have history when HEAD is an unborn branch.
    git(tmp_path, "symbolic-ref", "HEAD", "refs/heads/unborn")
    assert_empty(tmp_path)
    githistory.last_commit_dates.cache_clear()
    # A detached HEAD is also a valid history root.
    oid = git(tmp_path, "rev-list", "--all", "-1")
    git(tmp_path, "update-ref", "--no-deref", "HEAD", oid)
    assert githistory.last_commit_date(tmp_path, "folder") == "2020-01-02"


@pytest.mark.parametrize("check", ["check_workspaces", "_hygiene_stale_views"])
def test_validator_reports_history_failure_under_distinct_code(mini_repo, monkeypatch, check):
    monkeypatch.setenv("GIT_DIR", "/dev/null")
    validator = Validator(load_repo(mini_repo))
    getattr(validator, check)()
    failures = [issue for issue in validator.issues if issue.code == "GIT-HISTORY"]
    assert len(failures) == 1
    assert failures[0].severity == "E"
    assert "fatal:" in failures[0].message
    assert "GIT-HISTORY" not in BASELINE_EXEMPT_WARNINGS
    assert not any(issue.code == "WS-NEGLECT" for issue in validator.issues)


def test_workspace_neglect_remains_a_warning(mini_repo):
    init_repo(mini_repo, commit=False)
    git(mini_repo, "add", "work")
    git(mini_repo, "commit", "-m", "old workspace")
    validator = Validator(load_repo(mini_repo))
    validator.check_workspaces()
    assert any(i.code == "WS-NEGLECT" and i.severity == "W" for i in validator.issues)


def test_hygiene_detects_even_an_empty_commit(mini_repo):
    init_repo(mini_repo, commit=False)
    git(mini_repo, "commit", "--allow-empty", "-m", "empty commit")
    validator = Validator(load_repo(mini_repo))
    validator._hygiene_stale_views()
    assert any(i.code == "HYGIENE-VIEWS" for i in validator.issues)


@pytest.mark.parametrize("caller", ["date", "timestamp", "generate"])
def test_generator_refuses_history_failure(mini_repo, monkeypatch, caller):
    monkeypatch.setenv("GIT_DIR", "/dev/null")
    with pytest.raises(TransactionFailure, match="fatal:") as error:
        if caller == "date":
            _git_last_commit(mini_repo, "work")
        elif caller == "timestamp":
            stable_generated_at(mini_repo)
        else:
            generate_all(load_repo(mini_repo))
    assert isinstance(error.value.__cause__, githistory.GitHistoryError)
