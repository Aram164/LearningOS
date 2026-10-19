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
from pathlib import Path

from learning_os.app.projection import publish as _publish
from learning_os.app.validation import validation_run
from learning_os.domain.failures import ReplayRecoveryError as _ReplayRecoveryError
from learning_os.domain.failures import ToolFailure, WriteRefused
from learning_os.domain.transaction import TransactionResult
from learning_os.store import observations
from learning_os.store.contracts.gateway import GATEWAY_CHANNELS
from learning_os.store.evidence import shared_ledgers_canonical, shared_ledgers_proven_since
from learning_os.store.session_ledger import SESSION_LEDGER_STALE_HOURS
from learning_os.store.session_ledger import close_session_ledger as _close_session_ledger
from learning_os.store.session_ledger import current_session_id as _current_session_id
from learning_os.store.session_ledger import delete_session_ledger as _delete_session_ledger
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
        cwd=root, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def session_end(root: Path, *, channel: str | None, session_id: str | None,
                include_stale: bool, close: bool,
                commit_message: str | None, push: bool) -> dict:
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
    ownership_conflicts = _ownership_conflicts(root, touched, recorded)
    # Validate the repository this session touched, in process. A failed
    # close prints its issues; a clean one names where the baselined
    # warnings are listed, as `validate.py --compact` does.
    validation = validation_run(root)
    if validation["errors"]:
        raise ToolFailure("", "\n".join(validation["issues"]), 1)
    validation_line = (f"0 error(s), {validation['warnings']} warning(s) — OK"
                       "; warning list: generated/reports/validation-report.md")
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
            raise ToolFailure(
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
    changed_paths = {line[3:] for line in all_changed}
    stage_paths = [
        path for path in touched
        if (root / path).exists() or path in changed_paths
    ]
    if stage_paths:
        added = subprocess.run(
            ["git", "add", "--", *stage_paths],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if added.returncode != 0:
            raise ToolFailure(
                stdout=added.stdout,
                stderr=added.stderr,
                exit_code=added.returncode,
            )
    commit = subprocess.run(["git", "commit", "-m", commit_message], cwd=root,
                            capture_output=True, text=True, timeout=180)
    if commit.returncode != 0:
        raise ToolFailure(
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
            raise ToolFailure(
                stdout=pushed.stdout, stderr=pushed.stderr,
                exit_code=pushed.returncode)
        payload["pushed"] = True
    _delete_session_ledger(root, own_session)
    payload["session_closed"] = True
    return payload


# only carry forward a *prior* row this session already proved by directly
# observing its own fresh write, never assert one from scratch.
UNPROVABLE_AGGREGATE_LEDGERS = (
    "operations/transactions/revisions.yaml",
    "operations/transactions/idempotency.yaml",
)


def _is_receipt_committed_in_head(root: Path, receipt_relative: str,
                                  receipt_bytes: bytes) -> bool:
    if not (root / ".git").exists():
        return False
    env = {
        key: value for key, value in os.environ.items()
        if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-p", f"HEAD:{receipt_relative}"],
            capture_output=True, timeout=10,
            env={**env, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and proc.stdout == receipt_bytes


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
    in_head = _is_receipt_committed_in_head(root, receipt_relative, receipt_bytes)
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
            commit_sha=envelope["commit_sha"])
    except WriteRefused as exc:
        raise _ReplayRecoveryError(
            f"cannot repair replayed session ownership: {exc}"
        ) from exc
