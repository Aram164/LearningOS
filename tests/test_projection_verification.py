"""Agent-independent proof coordination and publication admission."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from repo_builders import curriculum_mini, stage_manifest_producers

from learning_os import githistory
from learning_os.derived.store import derived_dir
from learning_os.errors import TransactionFailure
from learning_os.genout import derived_generation, manifest_derived, projection_verification
from learning_os.genout.common import stable_generated_at
from learning_os.loader import load_repo

GENERATE = Path(__file__).resolve().parent.parent / "tools/generate.py"
NOTE = "knowledge/notes/mathematics/note-demo.md"


def _git(root, *args, when="2026-09-19T12:00:00+02:00"):
    return subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", *args], cwd=root, check=True,
        capture_output=True, text=True,
        env={**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when},
    ).stdout.strip()


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"):
        monkeypatch.delenv(name, raising=False)
    root = curriculum_mini(tmp_path)
    stage_manifest_producers(root, load_repo(root))
    _git(root, "init")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")
    return root


def _cache_bytes(root):
    cache = derived_dir(root)
    return {p.relative_to(cache): p.read_bytes() for p in cache.rglob("*") if p.is_file()}


@pytest.mark.parametrize("failure_point", ["head", "table"])
def test_related_projection_refuses_unreadable_git(git_repo, monkeypatch, failure_point):
    derived_generation.generate_shadow(load_repo(git_repo))
    before = _cache_bytes(git_repo)
    real = githistory.read_history

    def broken(root, *args):
        if failure_point == "head" or "--name-only" in args:
            raise githistory.GitHistoryError("history unavailable")
        return real(root, *args)

    monkeypatch.setattr(githistory, "read_history", broken)
    with pytest.raises(TransactionFailure, match="Git history was unreadable"):
        derived_generation.generate_shadow(load_repo(git_repo))
    assert _cache_bytes(git_repo) == before


@pytest.mark.parametrize("family", ["manifest", "related"])
def test_stamp_is_refreshed_inside_retried_attempt(git_repo, monkeypatch, family):
    module = manifest_derived if family == "manifest" else derived_generation
    build = module.build_manifest_shadow if family == "manifest" else module.generate_shadow
    real_stamp = module.stable_generated_at
    real_commit = module.commit_staging
    stamps = []
    commits = []

    def racing_stamp(root):
        stamp = real_stamp(root)
        stamps.append(stamp)
        if len(stamps) == 1:
            _git(root, "commit", "--allow-empty", "-m", "raced",
                 when="2026-09-20T12:00:00+02:00")
        return stamp

    def commit(root, staging):
        commits.append(True)
        return real_commit(root, staging)

    monkeypatch.setattr(module, "stable_generated_at", racing_stamp)
    monkeypatch.setattr(module, "commit_staging", commit)
    result = build(load_repo(git_repo))
    payload = result if family == "manifest" else json.loads(result["backlinks.json"])
    assert len(stamps) == 2 and stamps[0] != stamps[1]
    assert payload["_generated"]["generated_at"] == stable_generated_at(git_repo)
    assert commits == [True]


def test_one_verdict_covers_four_artifacts_and_observes_new_commits(git_repo):
    verify = projection_verification.verify_shadow_projections
    before = verify(git_repo)
    assert before["status"] == "verified"
    warm = verify(git_repo)
    assert warm["nodes"] == {
        "manifest": {"reused": 36, "rebuilt": 0},
        "related": {"reused": 3, "rebuilt": 0},
    }
    assert set(warm["artifacts"]) == {
        "manifest.json", "backlinks.json", "concept-map.md", "dependency-report.md"}
    _git(git_repo, "commit", "--allow-empty", "-m", "next",
         when="2026-09-20T12:00:00+02:00")
    after = verify(git_repo)
    assert after["status"] == "verified"
    assert after["source_revision"] != before["source_revision"]
    assert after["input_digest"] != before["input_digest"]
    assert after["generated_at"] != before["generated_at"]
    assert not after["published"]


@pytest.mark.parametrize("persistent", [False, True])
def test_cross_family_movement_retries_or_refuses(git_repo, monkeypatch, persistent):
    real = projection_verification.compare_shadow_generation
    calls = []

    def moving(*args, **kwargs):
        result = real(*args, **kwargs)
        calls.append(True)
        if persistent or len(calls) == 1:
            note = git_repo / NOTE
            note.write_text(note.read_text() + "\nMovement.\n")
        return result

    monkeypatch.setattr(projection_verification, "compare_shadow_generation", moving)
    if persistent:
        with pytest.raises(TransactionFailure, match="cannot verify projections"):
            projection_verification.verify_shadow_projections(git_repo)
        assert len(calls) == projection_verification.SNAPSHOT_ATTEMPTS
    else:
        assert projection_verification.verify_shadow_projections(git_repo)["status"] == "verified"
        assert len(calls) == 2


def test_stable_disagreement_is_not_reported_as_verified(git_repo, monkeypatch):
    real = projection_verification.compare_shadow_generation

    def disagree(*args, **kwargs):
        result = real(*args, **kwargs)
        result.legacy["concept-map.md"] = "Different full output"
        return result

    monkeypatch.setattr(projection_verification, "compare_shadow_generation", disagree)
    report = projection_verification.verify_shadow_projections(git_repo)
    assert report["status"] == "mismatch"
    assert not report["equivalent"]
    assert not report["artifacts"]["concept-map.md"]["equal"]


@pytest.mark.parametrize("malformed", [False, True])
def test_cli_emits_compact_result_without_publishing(git_repo, malformed):
    published = git_repo / "generated/manifest.json"
    published.write_text("previous publication")
    if malformed:
        (git_repo / NOTE).write_text("---\nid: [broken\n---\n")
    result = subprocess.run(
        [sys.executable, str(GENERATE), "--root", str(git_repo), "--shadow-all", "--json"],
        capture_output=True, text=True, timeout=60,
    )
    report = json.loads(result.stdout)
    assert result.returncode == (2 if malformed else 0), result.stderr
    assert report["status"] == ("refused" if malformed else "verified")
    assert not report["published"]
    assert "Traceback" not in result.stderr
    assert published.read_text() == "previous publication"
