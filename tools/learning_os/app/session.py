"""The D7 session state machine (PLAN D7, SPEC §13).

`session_end` runs the whole `cli.session-end` flow — review, commit, push
retry and close — over the v3 ledger, returning either the legacy JSON
payload or the raw `CommandOutput` of a failed child process. Business
refusals raise the machine's `WriteRefused` subclasses; the thin
`ops/handlers/session.py` facade translates them to sited refusals.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

from learning_os.app.projection import publish as _publish
from learning_os.app.proposal import CommandOutput
from learning_os.contracts.gateway import GATEWAY_CHANNELS
from learning_os.domain.failures import WriteRefused
from learning_os.store import observations
from learning_os.store.session_ledger import SESSION_LEDGER_STALE_HOURS
from learning_os.store.session_ledger import current_session_id as _current_session_id
from learning_os.store.session_ledger import delete_session_ledger as _delete_session_ledger
from learning_os.store.session_ledger import (
    load_other_session_ledgers as _load_other_session_ledgers,
)
from learning_os.store.session_ledger import load_session_ledger as _load_session_ledger
from learning_os.store.session_ledger import row_is_stale as _row_is_stale
from learning_os.store.session_ledger import row_proven_state as _row_proven_state
from learning_os.store.session_ledger import row_recorded_at as _row_recorded_at
from learning_os.store.session_ledger import session_path_state as _session_path_state
from learning_os.store.session_ledger import write_session_ledger as _write_session_ledger

TOOLS = Path(__file__).resolve().parent.parent.parent

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
    if review["version"] != version \
            or review["states"] != _witness_states(root, touched):
        raise SessionMismatchError(
            "the session changed after review — run session-end again")


def _current_head(root: Path) -> str | None:
    """HEAD's SHA, or None when the checkout no longer resolves one."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def session_end(root: Path, *, channel: str | None, session_id: str | None,
                include_stale: bool, close: bool,
                commit_message: str | None, push: bool) -> dict | CommandOutput:
    """Run one `session-end` invocation (PLAN D7, SPEC §13).

    Returns the legacy JSON payload, or the raw `CommandOutput` of a
    failed validation/commit/push child with that child's exact streams
    and exit. Business refusals raise the machine's `WriteRefused`
    subclasses; the handler gives them sites.

    Runs under the pipeline's exclusive operator lock; the review
    witness it persists is what bridges the interval between the
    review and the later commit invocations.
    """
    if close and commit_message:
        raise SessionUsageError(
            "--close and --commit-message are mutually exclusive: "
            "closing discards the ownership window instead of committing it")
    if channel is not None and channel not in GATEWAY_CHANNELS:
        raise SessionChannelError(
            f"unknown session channel {channel!r} "
            f"(one of: {', '.join(sorted(GATEWAY_CHANNELS))})")
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
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != _row_proven_state(recorded[path])
    ]
    # `validate.py` resolves its repository from its own location unless told
    # otherwise, so a bare `cwd=root` would validate the repository the tools
    # live in — not the one this session touched. Pass the root explicitly.
    # --compact: a failed close prints its errors and the summary line, not
    # every baselined warning; the full list is in the validation report.
    validation = subprocess.run(
        [sys.executable, str(TOOLS / "validate.py"), "--compact", "--root", str(root)],
        cwd=root, capture_output=True, text=True)
    if validation.returncode != 0:
        return CommandOutput(
            stdout=validation.stdout, stderr=validation.stderr,
            exit_code=validation.returncode or 1)
    # Errors gate; warnings are advisory and reported. Gating on zero warnings
    # made session-end impossible in a repository carrying the by-design
    # "material may be offline" set. External link rot is gated only by the
    # explicit online validator and never runs during session-end.
    validation_line = next((line for line in validation.stdout.splitlines()
                            if "warning(s)" in line), "").strip()
    _publish(root)
    all_changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        cwd=root, capture_output=True, text=True, timeout=30,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.splitlines()
    owned = [line for line in all_changed if line[3:] in touched]
    unrelated = [line for line in all_changed if line[3:] not in touched]
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
    if retry:
        pushed = subprocess.run(["git", "push"], cwd=root, capture_output=True,
                                text=True, timeout=180)
        if pushed.returncode != 0:
            return CommandOutput(
                stdout=pushed.stdout, stderr=pushed.stderr,
                exit_code=pushed.returncode)
        payload["pushed"] = True
        _delete_session_ledger(root, own_session)
        payload["session_closed"] = True
        return payload
    if not commit_message:
        # A review never closes: it validates, publishes, and lists owned
        # and unrelated changes while the ledger survives, so the documented
        # review-then-commit sequence can stage exactly the reviewed list.
        # Only the explicit --close ends this session's ownership window,
        # deleting just its own ledger; foreign ledgers are left untouched
        # either way, so closing here never wipes another session's (or the
        # UI's) unclaimed rows. Running a review twice shows the same list.
        if close:
            _delete_session_ledger(root, own_session)
            payload["session_closed"] = True
        else:
            if not unpushed:
                _persist_review(root, own_session, envelope, touched)
            payload["session_closed"] = False
        return payload
    if not touched:
        raise SessionEmptyError(
            "no files were touched through this learning session")
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != _row_proven_state(recorded[path])
    ]
    payload["ownership_conflicts"] = ownership_conflicts
    if ownership_conflicts:
        raise SessionConflictError(
            "refusing to stage files changed after their recorded LearningOS "
            "transaction: " + ", ".join(ownership_conflicts))
    _verify_witness(root, envelope, touched)
    subprocess.run(["git", "add", "--", *touched], cwd=root, check=True, timeout=30)
    commit = subprocess.run(["git", "commit", "-m", commit_message], cwd=root,
                            capture_output=True, text=True, timeout=180)
    if commit.returncode != 0:
        return CommandOutput(
            stdout=commit.stdout, stderr=commit.stderr,
            exit_code=commit.returncode)
    payload["committed"] = True
    if push:
        pushed = subprocess.run(["git", "push"], cwd=root, capture_output=True,
                                text=True, timeout=180)
        if pushed.returncode != 0:
            sha = _current_head(root)
            if sha is None:  # pragma: no cover - the commit just succeeded
                raise SessionLedgerError(
                    "cannot record the unpushed commit: HEAD is unresolvable")
            _write_session_ledger(
                root, recorded, own_session,
                version=envelope["version"] if envelope is not None else 0,
                state="committed_unpushed",
                review=envelope["review"] if envelope is not None else None,
                commit_sha=sha)
            return CommandOutput(
                stdout=pushed.stdout, stderr=pushed.stderr,
                exit_code=pushed.returncode)
        payload["pushed"] = True
    _delete_session_ledger(root, own_session)
    payload["session_closed"] = True
    return payload
