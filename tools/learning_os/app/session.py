"""The D7 session state machine (PLAN D7, SPEC §13).

`session_end` runs the whole `cli.session-end` flow — review, commit, push
retry and close — over the v3 ledger, returning either the legacy JSON
payload or the raw `CommandOutput` of a failed child process. Business
refusals raise the machine's `WriteRefused` subclasses; the thin
`ops/handlers/session.py` facade translates them to sited refusals.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

import yaml

from learning_os.app.lock import operator_lock as _operator_lock
from learning_os.app.projection import publish as _publish
from learning_os.app.validation import validation_run
from learning_os.domain.failures import ReplayRecoveryError as _ReplayRecoveryError
from learning_os.domain.failures import ToolFailure, WriteRefused
from learning_os.domain.transaction import TransactionResult
from learning_os.store import observations
from learning_os.store.contracts.gateway import GATEWAY_CHANNELS
from learning_os.store.evidence import shared_ledgers_canonical, shared_ledgers_proven_since
from learning_os.store.fs import clean_git_env
from learning_os.store.session_ledger import SESSION_LEDGER_STALE_HOURS
from learning_os.store.session_ledger import close_session_ledger as _close_session_ledger
from learning_os.store.session_ledger import current_session_id as _current_session_id
from learning_os.store.session_ledger import delete_session_ledger as _delete_session_ledger
from learning_os.store.session_ledger import is_anchored as _is_anchored
from learning_os.store.session_ledger import (
    load_other_session_ledgers as _load_other_session_ledgers,
)
from learning_os.store.session_ledger import load_session_ledger as _load_session_ledger
from learning_os.store.session_ledger import receipt_released as _receipt_released
from learning_os.store.session_ledger import row_is_stale as _row_is_stale
from learning_os.store.session_ledger import row_proven_state as _row_proven_state
from learning_os.store.session_ledger import row_recorded_at as _row_recorded_at
from learning_os.store.session_ledger import session_ledger as _session_ledger
from learning_os.store.session_ledger import session_path_state as _session_path_state
from learning_os.store.session_ledger import stamp_session_row as _stamp_session_row
from learning_os.store.session_ledger import write_session_ledger as _write_session_ledger

TOOLS = Path(__file__).resolve().parent.parent.parent

_SHARED_TRANSACTION_LEDGERS = frozenset({
    "operations/transactions/revisions.yaml",
    "operations/transactions/idempotency.yaml",
})

#: Environment variable naming the Core client and its build, stamped by the
#: interface on every Core child it spawns (`obsidian-ui/<build>`). An
#: unmarked call stays valid: terminal agents send nothing, and `session-end`
#: never refuses one. Informational only — staleness is proven by comparing
#: the installed build against the built one (see `health._ui_plugin_check`),
#: never by trusting this marker.
CLIENT_ENV = "LOS_CLIENT"


class SessionUsageError(WriteRefused):
    """`--close` with `--commit-message`: usage, nothing was changed."""


class SessionChannelError(WriteRefused):
    """An unknown session channel: usage, nothing was changed."""


class SessionLedgerError(WriteRefused):
    """The own ledger cannot be read: nothing was changed."""


class SessionEmptyError(WriteRefused):
    """No files were touched through this session: nothing was changed."""


class SessionConflictError(WriteRefused):
    """A touched file changed after its recorded transaction: uncommitted."""


class SessionMismatchError(WriteRefused):
    """The session changed after review: uncommitted, witness retained."""


class SessionCommittedError(WriteRefused):
    """Already committed; only push retry or close: the commit stands."""


class SessionHeadMovedError(WriteRefused):
    """The stored commit is no longer HEAD: nothing was pushed."""


def _other_session_summary(rows: dict[str, dict]) -> dict:
    """One foreign session's rows for the `other_sessions` report.

    Fresh and stale rows are listed separately; the age is the oldest row's.
    Undated rows (the pre-session `legacy` file) count as stale — their age
    cannot be proven.
    """
    now = observations.now().astimezone(_dt.UTC)
    fresh = sorted(path for path, row in rows.items() if not _row_is_stale(row, now))
    stale = sorted(path for path, row in rows.items() if _row_is_stale(row, now))
    moments = [moment for row in rows.values()
               if (moment := _row_recorded_at(row)) is not None]
    oldest = min(moments) if moments else None
    return {
        "paths": fresh,
        "stale_paths": stale,
        "oldest_recorded_at": oldest.isoformat() if oldest else None,
        "age_hours": round((now - oldest).total_seconds() / 3600, 2)
        if oldest else None,
    }


def _witness_states(root: Path, touched: list[str]) -> dict[str, dict[str, str | None]]:
    """The exact selected owned path states (SPEC §13 review format)."""
    return {relative: {"sha256": _session_path_state(root, relative).get("sha256")}
            for relative in touched}


def _persist_review(root: Path, own_session: str, envelope: dict | None,
                    touched: list[str]) -> None:
    """Record the review witness, replacing any earlier one (SPEC §13)."""
    version = envelope["version"] if envelope is not None else 0
    _write_session_ledger(
        root, envelope["paths"] if envelope is not None else {}, own_session,
        version=version, state="reviewed",
        review={"version": version, "states": _witness_states(root, touched)},
        commit_sha=None)


def _witness_states_match(
    root: Path,
    witness_states: dict[str, dict[str, str | None]],
    current_states: dict[str, dict[str, str | None]],
) -> bool:
    if witness_states == current_states:
        return True
    if witness_states.keys() != current_states.keys():
        return False
    shared_proven: bool | None = None
    for path, expected in witness_states.items():
        if current_states.get(path) == expected:
            continue
        if path not in _SHARED_TRANSACTION_LEDGERS:
            return False
        if shared_proven is None:
            shared_proven = shared_ledgers_proven_since(
                root,
                revisions_sha256=(
                    witness_states.get("operations/transactions/revisions.yaml") or {}
                ).get("sha256"),
                idempotency_sha256=(
                    witness_states.get("operations/transactions/idempotency.yaml") or {}
                ).get("sha256"),
            )
        if not shared_proven:
            return False
    return True


def _ownership_conflicts(
    root: Path, touched: list[str], recorded: dict[str, dict]
) -> list[str]:
    shared_proven: bool | None = None
    conflicts: list[str] = []
    for path in touched:
        if _session_path_state(root, path) == _row_proven_state(recorded[path]):
            continue
        if path in _SHARED_TRANSACTION_LEDGERS:
            if shared_proven is None:
                shared_proven = shared_ledgers_proven_since(
                    root,
                    revisions_sha256=_row_proven_state(
                        recorded["operations/transactions/revisions.yaml"]
                    ).get("sha256")
                    if "operations/transactions/revisions.yaml" in recorded
                    else None,
                    idempotency_sha256=_row_proven_state(
                        recorded["operations/transactions/idempotency.yaml"]
                    ).get("sha256")
                    if "operations/transactions/idempotency.yaml" in recorded
                    else None,
                )
            if shared_proven:
                continue
        conflicts.append(path)
    return conflicts


def _verify_witness(root: Path, envelope: dict | None, touched: list[str]) -> None:
    """Refuse a commit whose witness no longer matches (SPEC §13).

    A set that was never reviewed (`review` null) takes the direct
    authorized path; a retained but invalidated witness refuses rather
    than falling back to it.
    """
    review = envelope["review"] if envelope is not None else None
    if review is None:
        return
    version = envelope["version"] if envelope is not None else 0
    if review["version"] != version or not _witness_states_match(
        root, review["states"], _witness_states(root, touched)
    ):
        raise SessionMismatchError(
            "the session changed after review — run session-end again")


def _current_head(root: Path) -> str | None:
    """HEAD's SHA, or None when the checkout no longer resolves one."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root, capture_output=True, text=True, timeout=30,
        env=clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"}))
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _git_status_changes(root: Path) -> list[tuple[str, str, str | None]]:
    """Return ``(xy, path, source)`` tuples from ``git status --porcelain=v1 -z``."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "."],
            cwd=root, capture_output=True, timeout=30,
            env=clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"}),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SessionLedgerError(f"git status could not be inspected: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip() or "no output"
        raise SessionLedgerError(f"git status exited {proc.returncode}: {detail}")
    raw = proc.stdout
    if raw.endswith(b"\0"):
        raw = raw[:-1]
    records = raw.split(b"\0") if raw else []

    def _decode(token: bytes) -> str:
        try:
            return token.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SessionLedgerError(
                f"git status produced an undecodable path: {token!r}"
            ) from exc

    parsed: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(records):
        entry = _decode(records[index])
        index += 1
        if len(entry) < 4 or entry[2] != " ":
            raise SessionLedgerError(
                f"git status produced an unexpected record: {entry!r}"
            )
        xy, path = entry[:2], entry[3:]
        if not path:
            raise SessionLedgerError(
                f"git status produced an empty path record: {entry!r}"
            )
        source: str | None = None
        if "R" in xy or "C" in xy:
            if index >= len(records):
                raise SessionLedgerError(
                    f"git status truncated rename/copy source for {entry!r}"
                )
            source = _decode(records[index])
            index += 1
            if not source:
                raise SessionLedgerError(
                    f"git status produced an empty rename/copy source for {entry!r}"
                )
        parsed.append((xy, path, source))
    return parsed


def _git_cached_paths(root: Path) -> list[str]:
    """Return NUL-decoded staged paths currently in the Git index."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "-z"],
            cwd=root, capture_output=True, timeout=30,
            env=clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"}),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SessionLedgerError(f"git index could not be inspected: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip() or "no output"
        raise SessionLedgerError(f"git diff --cached exited {proc.returncode}: {detail}")
    paths: list[str] = []
    for token in proc.stdout.split(b"\0"):
        if not token:
            continue
        try:
            paths.append(token.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise SessionLedgerError(
                f"git diff --cached produced an undecodable path: {token!r}"
            ) from exc
    return sorted(paths)


def _git_tree_blob(root: Path, rev: str, relative: str) -> bytes | None:
    """Read a regular blob from ``rev:relative``; return None for missing or symlinks."""
    env = clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"})
    try:
        tree_proc = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-z", rev, "--", relative],
            capture_output=True, timeout=10, env=env,
        )
        if tree_proc.returncode != 0 or not tree_proc.stdout:
            return None
        entry = tree_proc.stdout.split(b"\0", 1)[0]
        meta = entry.split(b"\t", 1)[0].split()
        if len(meta) < 3 or meta[1] != b"blob" or meta[0] not in {b"100644", b"100755"}:
            return None
        cat_proc = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-p", f"{rev}:{relative}"],
            capture_output=True, timeout=10, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if cat_proc.returncode != 0:
        return None
    return cat_proc.stdout


def _git_commit_changed_paths(root: Path, rev: str = "HEAD") -> set[str] | None:
    env = clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"})
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "diff-tree", "--root", "--no-commit-id",
             "--name-only", "-r", "-z", rev],
            capture_output=True, timeout=10, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    paths: set[str] = set()
    for token in proc.stdout.split(b"\0"):
        if not token:
            continue
        try:
            paths.add(token.decode("utf-8"))
        except UnicodeDecodeError:
            return None
    return paths


def _head_already_committed_session(
    root: Path,
    recorded: dict[str, dict],
    touched: list[str],
    commit_message: str,
) -> str | None:
    """Detect whether a crash left HEAD committed for this session before ledger close."""
    if not touched:
        return None
    # Verify working tree on disk matches the proven post-transaction state for all
    # touched paths before checking HEAD (covers a crash after an isolated commit
    # before shared .git/index entries were refreshed).
    for path in touched:
        proven = _row_proven_state(recorded[path])
        target = root / path
        if proven.get("state") == "file":
            if not target.is_file() or target.is_symlink():
                return None
            if hashlib.sha256(target.read_bytes()).hexdigest() != proven.get("sha256"):
                return None
        elif proven.get("state") == "absent":
            if target.exists() or target.is_symlink():
                return None
        else:
            return None
    head_sha = _current_head(root)
    if head_sha is None:
        return None
    env = clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"})
    try:
        subject_proc = subprocess.run(
            ["git", "-C", str(root), "show", "-s", "--format=%s", "HEAD"],
            capture_output=True, text=True, timeout=10, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if subject_proc.returncode != 0:
        return None
    expected_subject = commit_message.splitlines()[0] if commit_message else ""
    if subject_proc.stdout.strip() != expected_subject.strip():
        return None
    head_changed = _git_commit_changed_paths(root, "HEAD")
    if not head_changed or not (set(touched) & head_changed):
        return None
    receipt_paths = [
        p for p in touched
        if p.startswith("operations/transactions/") and p.endswith(("/receipt.json", "/receipt.yaml"))
        and (root / p).is_file()
    ]
    if any(p not in head_changed for p in receipt_paths):
        return None
    for path in touched:
        if path not in head_changed:
            continue
        proven = _row_proven_state(recorded[path])
        if proven.get("state") == "file":
            blob = _git_tree_blob(root, "HEAD", path)
            if blob is None or hashlib.sha256(blob).hexdigest() != proven.get("sha256"):
                return None
        elif proven.get("state") == "absent":
            if _git_tree_blob(root, "HEAD", path) is not None:
                return None
    return head_sha


def _refresh_shared_index_paths(root: Path, stage_paths: list[str]) -> None:
    """Refresh committed ``stage_paths`` in shared index without touching unrelated entries."""
    if not stage_paths or _current_head(root) is None:
        return
    subprocess.run(
        ["git", "reset", "-q", "HEAD", "--", *stage_paths],
        cwd=root,
        capture_output=True,
        timeout=30,
        env=clean_git_env(),
    )


def _commit_with_isolated_index(
    root: Path,
    *,
    stage_paths: list[str],
    touched_set: set[str],
    commit_message: str,
) -> None:
    """Commit ``stage_paths`` via an isolated GIT_INDEX_FILE so shared index races cannot leak."""
    head_sha = _current_head(root)
    with tempfile.TemporaryDirectory(prefix="learningos-session-index-") as tmp_dir:
        temp_index = Path(tmp_dir) / "index"
        iso_env = clean_git_env(extra={
            "GIT_INDEX_FILE": str(temp_index),
            "GIT_OPTIONAL_LOCKS": "0",
        })
        if head_sha is not None:
            seeded = subprocess.run(
                ["git", "read-tree", head_sha],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                env=iso_env,
            )
            if seeded.returncode != 0:
                raise ToolFailure(
                    stdout=seeded.stdout,
                    stderr=seeded.stderr,
                    exit_code=seeded.returncode,
                )
        if stage_paths:
            added = subprocess.run(
                ["git", "add", "-A", "--", *stage_paths],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                env=iso_env,
            )
            if added.returncode != 0:
                raise ToolFailure(
                    stdout=added.stdout,
                    stderr=added.stderr,
                    exit_code=added.returncode,
                )
        if head_sha is not None:
            diff_proc = subprocess.run(
                ["git", "diff-index", "--cached", "--name-only", "-z", head_sha, "--"],
                cwd=root,
                capture_output=True,
                timeout=30,
                env=iso_env,
            )
        else:
            diff_proc = subprocess.run(
                ["git", "ls-files", "--cached", "-z"],
                cwd=root,
                capture_output=True,
                timeout=30,
                env=iso_env,
            )
        if diff_proc.returncode != 0:
            raise ToolFailure(
                stdout=diff_proc.stdout.decode("utf-8", "replace"),
                stderr=diff_proc.stderr.decode("utf-8", "replace"),
                exit_code=diff_proc.returncode,
            )
        isolated_paths = [
            token.decode("utf-8")
            for token in diff_proc.stdout.split(b"\0")
            if token
        ]
        extra_staged = sorted(
            path for path in isolated_paths if path not in touched_set
        )
        if extra_staged:
            raise SessionConflictError(
                "refusing to commit unrelated staged paths: "
                + ", ".join(extra_staged)
            )
        commit = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
            env=clean_git_env(extra={"GIT_INDEX_FILE": str(temp_index)}),
        )
        if commit.returncode != 0:
            raise ToolFailure(
                stdout=commit.stdout,
                stderr=commit.stderr,
                exit_code=commit.returncode,
            )
    _refresh_shared_index_paths(root, stage_paths)


def _push_destination(root: Path) -> tuple[str, str]:
    """The (remote, branch) HEAD pushes to, resolved under the operator lock.

    Recorded alongside the commit SHA so the network push after the lock is
    released names an explicit ``<sha>:refs/heads/<branch>`` refspec and can
    never silently push whatever branch is checked out by then.
    """
    branch_proc = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root, capture_output=True, text=True, timeout=30,
        env=clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"}))
    branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else ""
    if not branch:
        raise SessionLedgerError(
            "cannot record a push destination: HEAD is detached; "
            "check out the session branch or push the commit by hand")
    upstream_proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name",
         f"{branch}@{{upstream}}"],
        cwd=root, capture_output=True, text=True, timeout=30,
        env=clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"}))
    upstream = upstream_proc.stdout.strip() if upstream_proc.returncode == 0 else ""
    if "/" in upstream:
        remote, _, remote_branch = upstream.partition("/")
        if remote and remote_branch:
            return remote, remote_branch
    return "origin", branch


def session_end(root: Path, *, channel: str | None, session_id: str | None,
                include_stale: bool, close: bool,
                commit_message: str | None, push: bool) -> dict:
    """Run one `session-end` invocation (PLAN D7, SPEC §13).

    Returns the legacy JSON payload, or the raw `CommandOutput` of a
    failed validation/commit/push child with that child's exact streams
    and exit. Business refusals raise the machine's `WriteRefused`
    subclasses; the handler gives them sites.

    Takes the exclusive operator lock around local ledger, validation,
    publication, witness, commit, and `committed_unpushed` transitions, and
    releases it before running network `git push` so concurrent readers and
    UI writes do not stall behind the remote (D-17).
    """
    if close and commit_message:
        raise SessionUsageError(
            "--close and --commit-message are mutually exclusive: "
            "closing discards the ownership window instead of committing it")
    if channel is not None and channel not in GATEWAY_CHANNELS:
        raise SessionChannelError(
            f"unknown session channel {channel!r} "
            f"(one of: {', '.join(sorted(GATEWAY_CHANNELS))})")
    push_sha: str | None = None
    push_target: tuple[str, str] | None = None
    with _operator_lock(root):
        own_session = _current_session_id(channel=channel, explicit=session_id)
        try:
            envelope = _load_session_ledger(root, own_session)
        except WriteRefused as exc:
            raise SessionLedgerError(str(exc)) from exc
        unpushed = envelope is not None and envelope["state"] == "committed_unpushed"
        if unpushed and not close and not (push and not commit_message):
            raise SessionCommittedError(
                f"already committed as {envelope['commit_sha']}; use --push or --close")
        retry = bool(unpushed and push and not commit_message and not close)
        if retry:
            head = _current_head(root)
            if head != envelope["commit_sha"]:
                raise SessionHeadMovedError(
                    f"session commit {envelope['commit_sha']} is no longer HEAD "
                    f"({head or 'unknown'}); push it by hand or close the session")
            push_sha = envelope["commit_sha"]
            recorded_remote = envelope.get("push_remote")
            recorded_branch = envelope.get("push_branch")
            push_target = (
                (recorded_remote, recorded_branch)
                if recorded_remote and recorded_branch
                else _push_destination(root)
            )
        others = _load_other_session_ledgers(root, own_session)
        recorded = envelope["paths"] if envelope is not None else {}
        include_stale = bool(include_stale)
        fresh = sorted(
            path for path, row in recorded.items()
            if Path(path).suffix.lower() != ".canvas" and not _row_is_stale(row)
        )
        stale_paths = sorted(
            path for path, row in recorded.items()
            if Path(path).suffix.lower() != ".canvas" and _row_is_stale(row)
        )
        # Only this session's own rows are ever claimed; foreign rows are
        # reported under `other_sessions` and never staged, and stale own rows
        # need the explicit opt-in.
        touched = sorted(fresh + stale_paths) if include_stale else fresh
        ownership_conflicts = _ownership_conflicts(root, touched, recorded)
        if not retry and commit_message and ownership_conflicts:
            raise SessionConflictError(
                "refusing to stage files changed after their recorded LearningOS "
                "transaction: " + ", ".join(ownership_conflicts))
        # Validate the repository this session touched, in process. A failed
        # close prints its issues; a clean one names where the baselined
        # warnings are listed, as `validate.py --compact` does.
        validation = validation_run(root)
        if validation["errors"]:
            raise ToolFailure("", "\n".join(validation["issues"]), 1)
        validation_line = (f"0 error(s), {validation['warnings']} warning(s) — OK"
                           "; warning list: generated/reports/validation-report.md")
        _publish(root)
        git_required = bool(retry or commit_message or push)
        try:
            anchored = _is_anchored(root)
        except WriteRefused as exc:
            raise SessionLedgerError(str(exc)) from exc
        if git_required and not anchored:
            raise SessionLedgerError(
                "cannot commit or push: checkout has no git repository"
            )
        status_records = (
            _git_status_changes(root) if (git_required or anchored) else []
        )
        touched_set = set(touched)
        owned = [
            (f"{xy} {source} -> {path}" if source is not None else f"{xy} {path}")
            for xy, path, source in status_records
            if path in touched_set and (source is None or source in touched_set)
        ]
        unrelated = [
            (f"{xy} {source} -> {path}" if source is not None else f"{xy} {path}")
            for xy, path, source in status_records
            if not (path in touched_set and (source is None or source in touched_set))
        ]
        changed_paths = {
            item
            for _, path, source in status_records
            for item in ((path, source) if source is not None else (path,))
        }
        payload = {"ok": True, "touched": touched, "owned_changes": owned,
                   "unrelated_changes": unrelated, "committed": bool(unpushed), "pushed": False,
                   "validation": validation_line,
                   "ownership_conflicts": ownership_conflicts,
                   "session_id": own_session,
                   # The calling client when it marks itself (`obsidian-ui/<build>`
                   # on every UI-spawned child); None for terminal agents, which
                   # stay valid unmarked. Informational: never a refusal input.
                   "client": os.environ.get(CLIENT_ENV),
                   "stale_paths": stale_paths,
                   "stale_hours": SESSION_LEDGER_STALE_HOURS,
                   "other_sessions": {
                       identity: _other_session_summary(rows)
                       for identity, rows in sorted(others.items())
                   }}
        if not retry:
            if not commit_message:
                # A review never closes: it validates, publishes, and lists owned
                # and unrelated changes while the ledger survives, so the documented
                # review-then-commit sequence can stage exactly the reviewed list.
                # Only the explicit --close ends this session's ownership window,
                # deleting just its own ledger; foreign ledgers are left untouched
                # either way, so closing here never wipes another session's (or the
                # UI's) unclaimed rows. Running a review twice shows the same list.
                if close:
                    _close_session_ledger(root, own_session)
                    payload["session_closed"] = True
                else:
                    if not unpushed:
                        _persist_review(root, own_session, envelope, touched)
                    payload["session_closed"] = False
                return payload
            if not touched:
                raise SessionEmptyError(
                    "no files were touched through this learning session")
            ownership_conflicts = _ownership_conflicts(root, touched, recorded)
            payload["ownership_conflicts"] = ownership_conflicts
            if ownership_conflicts:
                raise SessionConflictError(
                    "refusing to stage files changed after their recorded LearningOS "
                    "transaction: " + ", ".join(ownership_conflicts))
            _verify_witness(root, envelope, touched)
            pre_staged = sorted(
                path for path in _git_cached_paths(root) if path not in touched_set
            )
            if pre_staged:
                raise SessionConflictError(
                    "refusing to commit while unrelated paths are already staged in the git index: "
                    + ", ".join(pre_staged)
                )
            stage_paths = [
                path for path in touched
                if (root / path).exists() or path in changed_paths
            ]
            recovered_sha = _head_already_committed_session(
                root, recorded, touched, commit_message,
            )
            if recovered_sha is None:
                _commit_with_isolated_index(
                    root,
                    stage_paths=stage_paths,
                    touched_set=touched_set,
                    commit_message=commit_message,
                )
            else:
                _refresh_shared_index_paths(root, stage_paths)
            payload["committed"] = True
            if not push:
                _delete_session_ledger(root, own_session)
                payload["session_closed"] = True
                return payload
            sha = recovered_sha or _current_head(root)
            if sha is None:  # pragma: no cover - the commit just succeeded
                raise SessionLedgerError(
                    "cannot record the unpushed commit: HEAD is unresolvable")
            # Persist committed_unpushed under the lock BEFORE dropping it for
            # network push, so same-session writes refuse cleanly while concurrent
            # readers/writers in other sessions do not block behind git push.
            push_target = _push_destination(root)
            push_sha = sha
            _write_session_ledger(
                root, recorded, own_session,
                version=envelope["version"] if envelope is not None else 0,
                state="committed_unpushed",
                review=envelope["review"] if envelope is not None else None,
                commit_sha=sha,
                push_remote=push_target[0],
                push_branch=push_target[1])

    assert push_sha is not None and push_target is not None  # set under the lock
    pushed = subprocess.run(
        ["git", "push", push_target[0],
         f"{push_sha}:refs/heads/{push_target[1]}"],
        cwd=root, capture_output=True, text=True, timeout=180,
        env=clean_git_env())
    if pushed.returncode != 0:
        raise ToolFailure(
            stdout=pushed.stdout, stderr=pushed.stderr,
            exit_code=pushed.returncode)
    payload["pushed"] = True
    with _operator_lock(root):
        _delete_session_ledger(root, own_session)
    payload["session_closed"] = True
    return payload


# only carry forward a *prior* row this session already proved by directly
# observing its own fresh write, never assert one from scratch.
UNPROVABLE_AGGREGATE_LEDGERS = (
    "operations/transactions/revisions.yaml",
    "operations/transactions/idempotency.yaml",
)


def _is_receipt_committed_in_head(
    root: Path,
    receipt_relative: str,
    receipt_bytes: bytes,
    *,
    receipt: dict | None = None,
) -> bool:
    if not (root / ".git").exists():
        return False
    blob = _git_tree_blob(root, "HEAD", receipt_relative)
    if blob is None or blob != receipt_bytes:
        return False
    env = clean_git_env(extra={"GIT_OPTIONAL_LOCKS": "0"})
    try:
        intro_proc = subprocess.run(
            ["git", "-C", str(root), "log", "-n", "1", "--diff-filter=A",
             "--format=%H", "--", receipt_relative],
            capture_output=True, text=True, timeout=10, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    commit_sha = intro_proc.stdout.strip() if intro_proc.returncode == 0 else ""
    if not commit_sha:
        return False
    changed = _git_commit_changed_paths(root, commit_sha)
    if changed is None or receipt_relative not in changed:
        return False
    tx_id = receipt.get("transaction_id") if isinstance(receipt, dict) else None
    if isinstance(tx_id, str) and tx_id:
        idem_blob = _git_tree_blob(root, commit_sha, "operations/transactions/idempotency.yaml")
        if idem_blob is None:
            return False
        try:
            idem_doc = yaml.safe_load(idem_blob.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError):
            return False
        entries = idem_doc.get("entries") if isinstance(idem_doc, dict) else None
        if not isinstance(entries, dict) or not any(
            isinstance(row, dict)
            and row.get("transaction_id") == tx_id
            and row.get("receipt_path") == receipt_relative
            for row in entries.values()
        ):
            return False
    return True


def repair_replayed_session_ownership(root: Path,
                                       replay: TransactionResult,
                                       session_id: str | None = None) -> None:
    """Rebuild ephemeral session ownership from the already-validated receipt.

    A process can die after Receipt V2 and the idempotency ledger are durable
    but before the temporary learning-session ledger is written.  Exact replay
    is the recovery boundary, so it also repairs that bookkeeping; otherwise
    the UI would retire its durable record while ``session-end`` forgot the
    canonical file the recovered gesture authored.

    This must never simply re-observe the current filesystem and adopt it as
    the ownership claim: an out-of-band edit between the original commit and
    this replay would then be laundered into the session's own authorship, and
    ``session-end`` would happily stage and commit it as though the gateway
    transaction had written it. Every claim made here is instead the
    *authored* state Receipt V2 itself proves — ``writes[].sha256_after``, or
    absence when it is ``null`` (each path already proven safe and canonical
    by ``replay_for_request``), plus the receipt's own bytes, which this
    function reads and hashes itself rather than trusting a second party's
    claim about them. That authored state is compared against the live file;
    a mismatch anywhere refuses the whole repair before a single byte of the
    ownership ledger is written, so an existing row is never overwritten with
    a laundered observation and no replacement ledger is created from an
    unproven one. A replay whose write is already accounted for — its rows
    in the session ledger, its receipt committed to Git HEAD or released by
    `session-end --close` — repairs nothing and so compares nothing.
    """
    receipt = replay.receipt
    if not isinstance(receipt, dict):
        raise _ReplayRecoveryError(
            "cannot repair session ownership: replayed evidence carries no receipt"
        )
    writes = receipt.get("writes")
    if not isinstance(writes, list):
        raise _ReplayRecoveryError(
            "cannot repair session ownership: replayed receipt writes are malformed"
        )

    authored: dict[str, dict[str, str]] = {}
    for row in writes:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str) or not relative:
            raise _ReplayRecoveryError(
                "cannot repair session ownership: replayed receipt path is unsafe"
            )
        sha_after = row.get("sha256_after") if isinstance(row, dict) else None
        if sha_after is None:
            authored[relative] = {"state": "absent"}
        elif isinstance(sha_after, str) and re.fullmatch(r"[0-9a-f]{64}", sha_after):
            authored[relative] = {"state": "file", "sha256": sha_after}
        else:
            raise _ReplayRecoveryError(
                "cannot repair session ownership: replayed receipt write has an "
                "unproven authored state"
            )

    try:
        receipt_bytes = replay.receipt_path.read_bytes()
        receipt_relative = replay.receipt_path.resolve().relative_to(
            root.resolve()
        ).as_posix()
    except (OSError, ValueError) as exc:
        raise _ReplayRecoveryError(
            f"cannot repair session ownership: {exc}"
        ) from exc
    authored[receipt_relative] = {
        "state": "file", "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
    }

    # The repair runs outside any gateway request context, so ambient
    # session resolution would land in the default channel's ledger — not
    # the one the original write recorded. The replayed envelope's sealed
    # session recovers exactly that ledger; without one, the receipt names
    # the writing channel, which recovers the channel ledger when no
    # session is named. A named session still wins: that session is
    # performing the recovery.
    origin = receipt.get("request") if isinstance(receipt, dict) else None
    origin = origin.get("channel") if isinstance(origin, dict) else None
    if not isinstance(origin, str) or not origin:
        origin = None
    session = _current_session_id(channel=origin, explicit=session_id)

    # Nothing is left to repair once the ownership window this write belongs
    # to has ended: session-end --commit-message committed this exact receipt
    # to Git HEAD (ownership retired into history; verify the shared ledgers
    # remain canonically serialized and leave the closed session closed), or
    # session-end --close released it. Later transactions may have changed
    # or moved any path it wrote since, so the live tree proves nothing here,
    # and nothing is written.
    receipt_sha256 = authored[receipt_relative]["sha256"]
    in_head = _is_receipt_committed_in_head(
        root, receipt_relative, receipt_bytes, receipt=receipt,
    )
    if not _session_ledger(root, session).is_file():
        if in_head:
            if not shared_ledgers_canonical(root):
                raise _ReplayRecoveryError(
                    "cannot repair session ownership: "
                    "operations/transactions/revisions.yaml changed since its recorded transaction"
                )
            return
        if _receipt_released(root, session, receipt_relative, receipt_sha256):
            return
        raise _ReplayRecoveryError(
            "cannot repair session ownership: the session ledger is gone, and this "
            "receipt cannot prove the bytes of the shared revision and idempotency "
            "ledgers — reconcile this transaction by hand"
        )
    try:
        envelope = _load_session_ledger(root, session)
    except WriteRefused as exc:
        raise _ReplayRecoveryError(
            f"cannot repair session ownership: {exc}"
        ) from exc
    assert envelope is not None  # the missing ledger failed closed above
    existing = envelope["paths"]

    # The original write's bookkeeping already ran: it records the receipt
    # together with every path the receipt wrote in one atomic ledger write,
    # so those rows stand and nothing is written. A later gateway write may
    # since have moved a path on — its own bookkeeping then proves the live
    # bytes in a session ledger — but bytes no ledger proves are an
    # out-of-band edit, and the replay still refuses rather than confirm it.
    if receipt_relative in existing:
        # The shared ledgers carry this write's rows only as part of the
        # whole file, so their proof is the session's recorded row.
        checks = dict(authored)
        for ledger_relative in UNPROVABLE_AGGREGATE_LEDGERS:
            if ledger_relative in existing:
                checks.setdefault(ledger_relative, existing[ledger_relative])
        ledgers = [existing, *_load_other_session_ledgers(root, session).values()]
        shared_proven: bool | None = None
        for relative, state in checks.items():
            live = _session_path_state(root, relative)
            if live == _row_proven_state(state) or any(
                    isinstance(rows.get(relative), dict)
                    and live == _row_proven_state(rows[relative])
                    for rows in ledgers):
                continue
            if relative in UNPROVABLE_AGGREGATE_LEDGERS:
                if shared_proven is None:
                    shared_proven = shared_ledgers_proven_since(
                        root,
                        revisions_sha256=(existing.get("operations/transactions/revisions.yaml") or {}).get("sha256"),
                        idempotency_sha256=(existing.get("operations/transactions/idempotency.yaml") or {}).get("sha256"),
                    )
                if shared_proven:
                    continue
            raise _ReplayRecoveryError(
                "cannot repair session ownership: "
                f"{relative} changed since its recorded transaction"
            )
        return
    if in_head and shared_ledgers_canonical(root):
        return
    if _receipt_released(root, session, receipt_relative, receipt_sha256):
        return

    actor = origin or "unknown"
    shared_proven = shared_ledgers_proven_since(
        root,
        revisions_sha256=(existing.get("operations/transactions/revisions.yaml") or {}).get("sha256"),
        idempotency_sha256=(existing.get("operations/transactions/idempotency.yaml") or {}).get("sha256"),
    )
    for ledger_relative in UNPROVABLE_AGGREGATE_LEDGERS:
        proven = existing.get(ledger_relative)
        if proven is not None:
            if (
                _session_path_state(root, ledger_relative) != _row_proven_state(proven)
                and shared_proven
            ):
                authored[ledger_relative] = _stamp_session_row(
                    root, ledger_relative, actor
                )
            else:
                authored[ledger_relative] = proven

    for relative, state in authored.items():
        if _session_path_state(root, relative) != _row_proven_state(state):
            if relative in UNPROVABLE_AGGREGATE_LEDGERS and shared_proven:
                continue
            raise _ReplayRecoveryError(
                "cannot repair session ownership: "
                f"{relative} changed since its recorded transaction"
            )

    merged = dict(existing)
    merged.update(authored)
    for relative, state in merged.items():
        if state.get("channel") and state.get("recorded_at"):
            continue
        state["channel"] = actor
        state["recorded_at"] = _stamp_session_row(
            root, relative, actor)["recorded_at"]
    try:
        # The repair keeps the envelope it found: a replay re-proves the
        # recorded bytes, so it neither bumps the version nor disturbs the
        # state, the witness or the recorded SHA.
        _write_session_ledger(
            root, merged, session, version=envelope["version"],
            state=envelope["state"], review=envelope["review"],
            commit_sha=envelope["commit_sha"],
            push_remote=envelope.get("push_remote"),
            push_branch=envelope.get("push_branch"))
    except WriteRefused as exc:
        raise _ReplayRecoveryError(
            f"cannot repair replayed session ownership: {exc}"
        ) from exc
