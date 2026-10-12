"""The D7 session machine through the public CLI (PLAN D7, SPEC §13).

Every behavioral case drives `los session-end` in a child over a
miniature world: matching and invalidated witnesses, failed commit and
push with their exact streams and exits, the exact-SHA push retry,
unpushed refusals, close, and corrupt and unwritable ledger state.
Remotes are scratch-local bare repositories only, never the network.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from arch_audit_hook import SITE_WITNESS_ENV
from gateway_helpers import approved_v2_envelope, run_v2_capability

from learning_os.contracts.gateway import request_artifact_id
from learning_os.store import session_ledger as session_store

LOS = Path(__file__).resolve().parent.parent / "tools" / "los.py"
ARCH_SITE = Path(__file__).resolve().parent / "arch_site"


def _git_init(root: Path) -> None:
    for command in (["git", "init", "-q"],
                    ["git", "config", "user.email", "tests@example.invalid"],
                    ["git", "config", "user.name", "Tests"],
                    ["git", "add", "."],
                    ["git", "commit", "-qm", "fixture baseline"]):
        subprocess.run(command, cwd=root, check=True)


def _capture(root: Path, *, key: str, text: str) -> str:
    envelope = approved_v2_envelope(
        root, capability="capture.create", payload={"text": text},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    result = run_v2_capability(root, envelope)
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)["result"]["captured"]


def _session_end(root: Path, *args: str, env: dict | None = None):
    run_env = dict(os.environ)
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(LOS), "--root", str(root), "session-end", *args],
        capture_output=True, text=True, timeout=120, env=run_env,
    )


def _read_witness_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _witnessed_session_end(root: Path, tmp_path: Path, *args: str):
    """Run the CLI with a per-test witness file; return (proc, lines).

    The child installs the audit hook through `tests/arch_site` exactly
    like a scenario child, but the witness file is per-test, so the
    session file stays clean.
    """
    log = tmp_path / f"audit-{uuid.uuid4().hex}.jsonl"
    witness = tmp_path / f"sites-{uuid.uuid4().hex}.jsonl"
    witness.touch()
    pythonpath = str(ARCH_SITE) + os.pathsep + os.environ.get("PYTHONPATH", "")
    proc = _session_end(root, *args, env={
        "PYTHONPATH": pythonpath,
        "LOS_ARCH_AUDIT_LOG": str(log),
        "LOS_ARCH_LAUNCH_TOKEN": f"t70-{uuid.uuid4().hex}",
        SITE_WITNESS_ENV: str(witness),
    })
    return proc, _read_witness_lines(witness)


def _head(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True).stdout.strip()


def _live_digests(root: Path, touched: list[str]) -> dict[str, dict]:
    states = {}
    for relative in touched:
        data = (root / relative).read_bytes()
        states[relative] = {"sha256": hashlib.sha256(data).hexdigest()}
    return states


def _own_envelope(root: Path, session: str = "channel:operator") -> dict:
    envelope = session_store._load_session_ledger(root, session)
    assert envelope is not None
    return envelope


def test_review_without_a_ledger_persists_an_empty_witness(
        mini_repo, monkeypatch):
    """A review with no writes persists version 0 and empty states (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    assert json.loads(review.stdout)["touched"] == []
    envelope = _own_envelope(mini_repo)
    assert envelope["state"] == "reviewed"
    assert envelope["version"] == 0
    assert envelope["review"] == {"version": 0, "states": {}}
    assert envelope["commit_sha"] is None


def test_matching_witness_commit_succeeds(mini_repo, monkeypatch):
    """Review then commit with no intermediate write commits (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    captured = _capture(mini_repo, key="match-001", text="match me")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    touched = json.loads(review.stdout)["touched"]
    assert captured in touched
    envelope = _own_envelope(mini_repo)
    assert envelope["state"] == "reviewed"
    assert envelope["review"]["version"] == envelope["version"]
    assert envelope["review"]["states"] == _live_digests(mini_repo, touched)

    closed = _session_end(mini_repo, "--commit-message", "match")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["committed"] is True
    assert not session_store._session_ledger(
        mini_repo, "channel:operator").exists()


def test_write_after_review_refuses_and_retains_the_witness(
        mini_repo, monkeypatch):
    """A post-review write invalidates; the witness is retained (M-07)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="invalidate-001", text="first")
    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    witnessed_version = _own_envelope(mini_repo)["review"]["version"]

    _capture(mini_repo, key="invalidate-002", text="second")
    refused = _session_end(mini_repo, "--commit-message", "must refuse")
    assert refused.returncode == 2, refused.stdout
    assert refused.stderr == (
        "los: INVALID_REQUEST: "
        "the session changed after review — run session-end again\n")
    envelope = _own_envelope(mini_repo)
    assert envelope["state"] == "reviewed"
    assert envelope["review"]["version"] == witnessed_version
    assert envelope["version"] != witnessed_version

    # The retained witness keeps refusing: no never-reviewed bypass.
    again = _session_end(mini_repo, "--commit-message", "still refused")
    assert again.returncode == 2
    assert "the session changed after review" in again.stderr

    rereviewed = _session_end(mini_repo)
    assert rereviewed.returncode == 0, rereviewed.stderr
    closed = _session_end(mini_repo, "--commit-message", "after re-review")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["committed"] is True


def test_changed_bytes_after_review_refuse_as_conflict(
        mini_repo, monkeypatch):
    """An off-ledger change after review names its files (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    captured = _capture(mini_repo, key="conflict-001", text="claimed")
    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr

    (mini_repo / captured).write_text("changed off-ledger\n", encoding="utf-8")
    refused = _session_end(mini_repo, "--commit-message", "must refuse")
    assert refused.returncode == 2, refused.stdout
    assert captured in refused.stderr
    assert "changed after their recorded" in refused.stderr


def test_repeated_review_replaces_the_witness(mini_repo, monkeypatch):
    """A second review replaces the witness, same list, then commits (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="repeat-001", text="repeat me")

    first = _session_end(mini_repo)
    assert first.returncode == 0, first.stderr
    assert _own_envelope(mini_repo)["review"]["states"]
    second = _session_end(mini_repo)
    assert second.returncode == 0, second.stderr
    assert (json.loads(second.stdout)["touched"]
            == json.loads(first.stdout)["touched"])
    envelope = _own_envelope(mini_repo)
    assert envelope["review"]["version"] == envelope["version"]
    assert (envelope["review"]["states"]
            == _live_digests(mini_repo, json.loads(second.stdout)["touched"]))

    closed = _session_end(mini_repo, "--commit-message", "repeat")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["committed"] is True


def test_stale_opt_in_flag_change_refuses_until_rereview(
        mini_repo, monkeypatch):
    """Staging more than reviewed refuses; the opt-in review binds it."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="flag-change-001", text="aging")
    ledger = session_store._session_ledger(mini_repo, "channel:operator")
    data = json.loads(ledger.read_text(encoding="utf-8"))
    aged = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=25)).isoformat()
    for row in data["paths"].values():
        row["recorded_at"] = aged
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    assert json.loads(review.stdout)["touched"] == []
    refused = _session_end(mini_repo, "--commit-message", "more than seen",
                           "--include-stale")
    assert refused.returncode == 2, refused.stdout
    assert "the session changed after review" in refused.stderr

    rereviewed = _session_end(mini_repo, "--include-stale")
    assert rereviewed.returncode == 0, rereviewed.stderr
    assert json.loads(rereviewed.stdout)["touched"]
    closed = _session_end(mini_repo, "--commit-message", "stale, reviewed",
                          "--include-stale")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["committed"] is True


def test_direct_commit_from_a_never_reviewed_set(mini_repo, monkeypatch):
    """No review at all: the authorized direct commit succeeds (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="direct-001", text="direct me")
    assert _own_envelope(mini_repo)["review"] is None

    closed = _session_end(mini_repo, "--commit-message", "direct")
    assert closed.returncode == 0, closed.stderr
    payload = json.loads(closed.stdout)
    assert payload["committed"] is True
    assert payload["session_closed"] is True


def test_canvas_rows_are_never_selected(mini_repo, monkeypatch):
    """A canvas row in the ledger is never touched or staged (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    captured = _capture(mini_repo, key="canvas-001", text="with canvas")
    ledger = session_store._session_ledger(mini_repo, "channel:operator")
    data = json.loads(ledger.read_text(encoding="utf-8"))
    data["paths"]["work/board.canvas"] = {
        "state": "file", "channel": "operator",
        "recorded_at": dt.datetime.now(dt.UTC).isoformat(),
        "sha256": hashlib.sha256(b"canvas\n").hexdigest(),
    }
    ledger.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")

    review = _session_end(mini_repo)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert "work/board.canvas" not in payload["touched"]
    assert captured in payload["touched"]
    envelope = _own_envelope(mini_repo)
    assert "work/board.canvas" not in envelope["review"]["states"]


def test_failed_commit_keeps_state_witness_and_ledger(mini_repo, monkeypatch,
                                                     tmp_path):
    """A failing hook: exact exit/streams, ledger bytes kept (D7, D-9)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="fail-commit-001", text="doomed")
    before = session_store._session_ledger(
        mini_repo, "channel:operator").read_bytes()
    hook = mini_repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho t70-hook-marker >&2\nexit 3\n",
                    encoding="utf-8")
    hook.chmod(0o755)

    proc, lines = _witnessed_session_end(
        mini_repo, tmp_path, "--commit-message", "doomed")
    assert "t70-hook-marker" in proc.stderr
    assert proc.stdout == ""
    assert session_store._session_ledger(
        mini_repo, "channel:operator").read_bytes() == before
    assert lines == [{"operation": "cli.session-end",
                      "kind": "command-failure", "site": None,
                      "code": proc.returncode}]
    assert proc.returncode != 0

    # The passthrough is exact: the same git call says the same bytes.
    direct = subprocess.run(
        ["git", "commit", "-m", "doomed"], cwd=mini_repo,
        capture_output=True, text=True, timeout=120)
    assert (direct.returncode, direct.stdout, direct.stderr) == (
        proc.returncode, proc.stdout, proc.stderr)


def test_failed_push_records_sha_and_keeps_the_window(mini_repo, monkeypatch,
                                                     tmp_path):
    """A failed push: committed_unpushed holds the SHA (M-08, D-9)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="fail-push-001", text="unpushable")
    subprocess.run(["git", "remote", "add", "origin",
                    str(tmp_path / "no-such-remote")],
                   cwd=mini_repo, check=True)

    proc, lines = _witnessed_session_end(
        mini_repo, tmp_path, "--commit-message", "unpushable", "--push")
    assert proc.returncode == 128, proc.stderr
    envelope = _own_envelope(mini_repo)
    assert envelope["state"] == "committed_unpushed"
    assert envelope["commit_sha"] == _head(mini_repo)
    assert lines == [{"operation": "cli.session-end",
                      "kind": "command-failure", "site": None, "code": 128}]

    direct = subprocess.run(
        ["git", "push"], cwd=mini_repo,
        capture_output=True, text=True, timeout=120)
    assert (direct.returncode, direct.stdout, direct.stderr) == (
        proc.returncode, proc.stdout, proc.stderr)


def test_push_retry_succeeds_on_the_exact_sha(mini_repo, monkeypatch,
                                             tmp_path):
    """Standalone --push retries the stored SHA and closes (D-2)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    remote = tmp_path / "retry-remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)],
                   cwd=mini_repo, check=True)
    subprocess.run(["git", "push", "-q", "--set-upstream", "origin", "main"],
                   cwd=mini_repo, check=True)
    _capture(mini_repo, key="retry-001", text="retry me")
    subprocess.run(["git", "remote", "set-url", "origin",
                    str(tmp_path / "no-such-remote-yet")],
                   cwd=mini_repo, check=True)

    failed = _session_end(mini_repo, "--commit-message", "retry me", "--push")
    assert failed.returncode == 128, failed.stderr
    sha = _own_envelope(mini_repo)["commit_sha"]
    subprocess.run(["git", "remote", "set-url", "origin", str(remote)],
                   cwd=mini_repo, check=True)

    # The stored-SHA retry against a working remote closes the window.
    retried = _session_end(mini_repo, "--push")
    assert retried.returncode == 0, retried.stderr
    payload = json.loads(retried.stdout)
    assert payload["committed"] is True
    assert payload["pushed"] is True
    assert payload["session_closed"] is True
    assert not session_store._session_ledger(
        mini_repo, "channel:operator").exists()
    landed = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
        capture_output=True, text=True, check=True).stdout.strip()
    assert landed == sha


def test_push_retry_repeats_while_the_remote_is_dead(mini_repo, monkeypatch,
                                                    tmp_path):
    """A retry against a dead remote fails alike and keeps the SHA (D-2)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="retry-dead-001", text="still dead")
    subprocess.run(["git", "remote", "add", "origin",
                    str(tmp_path / "no-such-remote")],
                   cwd=mini_repo, check=True)

    failed = _session_end(mini_repo, "--commit-message", "dead", "--push")
    assert failed.returncode == 128, failed.stderr
    sha = _own_envelope(mini_repo)["commit_sha"]
    again = _session_end(mini_repo, "--push")
    assert (again.returncode, again.stdout, again.stderr) == (
        failed.returncode, failed.stdout, failed.stderr)
    envelope = _own_envelope(mini_repo)
    assert envelope["state"] == "committed_unpushed"
    assert envelope["commit_sha"] == sha


def test_commit_and_review_refuse_in_committed_unpushed(
        mini_repo, monkeypatch, tmp_path):
    """Only push retry or close follow a failed push (D-2)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="unpushed-001", text="stuck")
    subprocess.run(["git", "remote", "add", "origin",
                    str(tmp_path / "no-such-remote")],
                   cwd=mini_repo, check=True)
    failed = _session_end(mini_repo, "--commit-message", "stuck", "--push")
    assert failed.returncode == 128, failed.stderr
    sha = _own_envelope(mini_repo)["commit_sha"]
    want = f"already committed as {sha}; use --push or --close"

    refused_commit, commit_lines = _witnessed_session_end(
        mini_repo, tmp_path, "--commit-message", "another")
    assert refused_commit.returncode == 2, refused_commit.stdout
    assert refused_commit.stderr == f"los: INVALID_REQUEST: {want}\n"
    assert commit_lines == [{"operation": "cli.session-end",
                             "kind": "failure",
                             "site": "cli.session-end.already-committed",
                             "class": "WriteRefused", "exit_code": 2}]

    refused_review, review_lines = _witnessed_session_end(
        mini_repo, tmp_path)
    assert refused_review.returncode == 2, refused_review.stdout
    assert refused_review.stderr == f"los: INVALID_REQUEST: {want}\n"
    assert review_lines == [{"operation": "cli.session-end",
                             "kind": "failure",
                             "site": "cli.session-end.already-committed",
                             "class": "WriteRefused", "exit_code": 2}]


def test_retry_after_head_moved_refuses(mini_repo, monkeypatch, tmp_path):
    """A retry refuses when HEAD no longer identifies the SHA (D-2)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="moved-001", text="moved")
    subprocess.run(["git", "remote", "add", "origin",
                    str(tmp_path / "no-such-remote")],
                   cwd=mini_repo, check=True)
    failed = _session_end(mini_repo, "--commit-message", "moved", "--push")
    assert failed.returncode == 128, failed.stderr
    sha = _own_envelope(mini_repo)["commit_sha"]

    extra = mini_repo / "work" / "diverged.md"
    extra.write_text("diverge\n", encoding="utf-8")
    subprocess.run(["git", "add", "--", "work/diverged.md"],
                   cwd=mini_repo, check=True)
    subprocess.run(["git", "commit", "-qm", "diverge"], cwd=mini_repo,
                   check=True)
    moved = _head(mini_repo)
    assert moved != sha

    refused, lines = _witnessed_session_end(mini_repo, tmp_path, "--push")
    assert refused.returncode == 2, refused.stdout
    assert sha in refused.stderr and moved in refused.stderr
    assert "is no longer HEAD" in refused.stderr
    assert lines == [{"operation": "cli.session-end",
                      "kind": "failure",
                      "site": "cli.session-end.head-changed",
                      "class": "WriteRefused", "exit_code": 2}]


def test_close_in_committed_unpushed_deletes_only_own_ledger(
        mini_repo, monkeypatch):
    """Close after a failed push drops the window, keeps commit+others."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="close-unpushed-001", text="closing")
    session_store._record_touched(
        mini_repo, [mini_repo / "operations" / "goal-ledger.yaml"],
        session_id="other-session")
    other = session_store._session_ledger(mini_repo, "other-session")
    assert other.is_file()

    closed = _session_end(mini_repo, "--close")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["session_closed"] is True
    assert not session_store._session_ledger(
        mini_repo, "channel:operator").exists()
    assert other.is_file()


def test_close_after_failed_push_keeps_the_commit(mini_repo, monkeypatch,
                                                 tmp_path):
    """Close in committed_unpushed deletes only this ledger (D-2)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="close-push-001", text="keep me")
    subprocess.run(["git", "remote", "add", "origin",
                    str(tmp_path / "no-such-remote")],
                   cwd=mini_repo, check=True)
    failed = _session_end(mini_repo, "--commit-message", "keep me", "--push")
    assert failed.returncode == 128, failed.stderr
    sha = _own_envelope(mini_repo)["commit_sha"]

    closed = _session_end(mini_repo, "--close")
    assert closed.returncode == 0, closed.stderr
    assert json.loads(closed.stdout)["session_closed"] is True
    assert not session_store._session_ledger(
        mini_repo, "channel:operator").exists()
    assert _head(mini_repo) == sha


def test_corrupt_ledger_refuses_with_its_site(mini_repo, monkeypatch,
                                             tmp_path):
    """A damaged own ledger refuses unreadable, witnessed (D7)."""
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    session_store._session_ledger(
        mini_repo, "channel:operator").write_text(
            '{"paths": {"work/x.md": {', encoding="utf-8")

    refused, lines = _witnessed_session_end(mini_repo, tmp_path)
    assert refused.returncode == 2, refused.stdout
    assert "ledger is unreadable" in refused.stderr
    assert lines == [{"operation": "cli.session-end",
                      "kind": "failure",
                      "site": "cli.session-end.unreadable-ledger",
                      "class": "WriteRefused", "exit_code": 2}]


def test_unwritable_state_dir_refuses(mini_repo, monkeypatch):
    """An unwritable git state dir refuses instead of half-writing (D7)."""
    if os.geteuid() == 0:
        pytest.skip("permission bits do not bind root")
    monkeypatch.delenv("LOS_SESSION_ID", raising=False)
    _git_init(mini_repo)
    _capture(mini_repo, key="nowrite-001", text="no room")
    ledger = session_store._session_ledger(mini_repo, "channel:operator")
    before = ledger.read_bytes()
    state_dir = mini_repo / ".git" / "learningos"
    state_dir.chmod(0o555)
    try:
        refused = _session_end(mini_repo)
    finally:
        state_dir.chmod(0o755)
    assert refused.returncode == 2, refused.stdout
    assert "cannot write" in refused.stderr
    assert ledger.read_bytes() == before
