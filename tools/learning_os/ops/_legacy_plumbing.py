"""Downward-owned command plumbing with a single owner (S13 candidate).

The operator lock, gateway refusal cellar, publish helpers,
session-ledger readers and small leaves, moved verbatim from
commands.support so the ops pipeline can import them downward.
Candidate sequencing ahead of S28/S29; the bodies are unchanged and
this module is their only owner.
"""

from __future__ import annotations

import contextlib
import contextvars
import datetime as _dt
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

import jsonschema
import yaml

from learning_os import observations
from learning_os.contracts.gateway import (
    current_gateway_request,
    intent_sha256,
)
from learning_os.derived.model import DerivedError
from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.fingerprint import canonical_fingerprint, seed_source_fingerprint
from learning_os.genout import (
    build_backlinks,
    build_manifest,
    generate_all,
    stable_generated_at,
    write_outputs,
)
from learning_os.genout.common import _git_state
from learning_os.genout.modules_view import _academic_deadlines
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
)
from learning_os.loader import load_repo
from learning_os.loading import Repo, load_notes
from learning_os.loading.yamlio import UniqueKeySafeLoader
from learning_os.manifest_identity import IDENTITY_FILENAME, bytes_sha256, check_identity
from learning_os.material_analysis import observe_local_material
from learning_os.material_slices import parse_locator_page_ranges
from learning_os.materials_resolution import (
    MATERIAL_RESOURCE_SUFFIXES,
    MATERIAL_SCHEME,
    MATERIAL_SUFFIX_TOKEN,
    leading_material_locator,
    material_location,
    material_uri_authority,
    safe_material_locator,
)
from learning_os.ops.outcomes import classify, resolve
from learning_os.semantics.goals import (
    CandidateGoal,
    RankedCluster,
    cluster_goals,
    rank_clusters,
)
from learning_os.semantics.scan import _read_goal_ledger, intelligence_scan
from learning_os.transactions import artifact_revision, reconcile_inflight_transactions

#: Roots locked by this context: ``((root_key, mode, handle), ...)`` with
#: mode ``"shared"``, ``"exclusive"``, or ``"released"`` after a failed
#: escalation. Immutable tuples, never mutated in
#: place: escalation replaces the whole value, and the owning scope's reset
#: still restores the pre-scope value afterwards.
_HELD_OPERATOR_LOCKS: contextvars.ContextVar[tuple] = (
    contextvars.ContextVar("learningos_held_operator_locks", default=())
)


#: Positive-only cache of repository roots to their git directories. A root
#: that gains a `.git` mid-process (tests do) must be re-probed, so misses
#: are never cached; hits are revalidated with `is_dir`.
_GIT_DIR_CACHE: dict[str, tuple[tuple[int, ...], Path]] = {}


#: Environment override for the operator-lock wait. `los --lock-timeout`
#: sets this for the process; in-process callers set it directly. Unset or
#: malformed means wait as long as the holder needs, announced on stderr.
LOS_LOCK_TIMEOUT_ENV = "LOS_LOCK_TIMEOUT"


#: Poll interval while a lock timeout is armed. The default (unbounded)
#: wait keeps kernel blocking with no polling.
_LOCK_POLL_INTERVAL_S = 0.05


def _lock_timeout_seconds() -> float | None:
    """The configured lock wait bound, or None for an unbounded announced wait."""
    raw = os.environ.get(LOS_LOCK_TIMEOUT_ENV)
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return max(0.0, value)


def _read_holder(lock_path: Path) -> str | None:
    """The advisory `(held by pid N: <command>, since HH:MM:SS)` fragment.

    Display only, never trusted for correctness: anything unreadable or
    misshapen answers None and the waiter prints the bare waiting line.
    """
    try:
        record = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None
    pid = record.get("pid")
    command = record.get("command")
    since = record.get("since")
    if (not isinstance(pid, int) or isinstance(pid, bool)
            or not isinstance(command, str) or not isinstance(since, str)):
        return None
    return f"(held by pid {pid}: {command[:200]}, since {since[:32]})"


def _write_holder(handle) -> None:
    """Record this process as the lock holder. Best effort: advisory only."""
    prog = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else "los"
    command = " ".join([prog, *sys.argv[1:3]])[:160] or "los"
    record = {"pid": os.getpid(), "command": command,
              "since": observations.now().replace(tzinfo=None).strftime("%H:%M:%S")}
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(record))
        handle.flush()
    except OSError:
        pass  # a waiter then prints the bare waiting line instead


def _git_dir(root: Path) -> Path | None:
    """This checkout's git directory, or None when the root has none.

    `git rev-parse --git-dir` answers per checkout (a worktree names its own
    `.git/worktrees/<name>`), so separate checkouts of one repository keep
    separate locks. A relative answer (`.git`) resolves against the root.
    A root without its own `.git` entry answers None (including synthetic
    roots inside another checkout). An existing but broken anchor refuses:
    using a temp lock would let a contender bypass the checkout's real lock.
    Ambient Git routing variables never determine process-state ownership.
    """
    root_key = str(root.resolve())
    try:
        anchor = (Path(root_key) / ".git").lstat()
    except FileNotFoundError:
        _GIT_DIR_CACHE.pop(root_key, None)
        return None
    except OSError as exc:
        raise WriteRefused(f"cannot resolve the checkout's git directory: {exc}") from exc
    anchor_key = (anchor.st_dev, anchor.st_ino, anchor.st_mtime_ns, anchor.st_ctime_ns)
    hit = _GIT_DIR_CACHE.get(root_key)
    if hit is not None and hit[0] == anchor_key and hit[1].is_dir():
        return hit[1]
    env = {key: value for key, value in os.environ.items()
           if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}}
    try:
        proc = subprocess.run(
            ["git", "-C", root_key, "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=30,
            env={**env, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WriteRefused(f"cannot resolve the checkout's git directory: {exc}") from exc
    if proc.returncode != 0:
        raise WriteRefused(
            f"cannot resolve the checkout's git directory: {proc.stderr.strip()}")
    lines = proc.stdout.strip().splitlines()
    if not lines or not lines[0].strip():
        raise WriteRefused("cannot resolve the checkout's git directory: empty git response")
    candidate = Path(lines[0].strip())
    resolved = candidate if candidate.is_absolute() else root / candidate
    try:
        if not resolved.is_dir():
            raise WriteRefused(f"checkout git directory is unavailable: {resolved}")
        resolved = resolved.resolve()
    except OSError as exc:
        raise WriteRefused(f"cannot resolve the checkout's git directory: {exc}") from exc
    _GIT_DIR_CACHE[root_key] = (anchor_key, resolved)
    return resolved


def _process_state_dir(root: Path) -> Path:
    """Where this checkout's operator lock and session ledgers live.

    `<git-dir>/learningos/` — per checkout, never committed, surviving `git
    clean` — so processes whose environments differ (and whose `$TMPDIR`
    therefore disagrees) still exclude each other and still find each
    other's ledgers. Roots without a git dir (the synthetic test
    repositories) keep today's temp-dir location. When the anchor exists
    but is not writable the command is refused; falling back to a temp
    directory then would silently split the lock again.
    """
    git_dir = _git_dir(root)
    if git_dir is None:
        return Path(tempfile.gettempdir())
    state = git_dir / "learningos"
    try:
        state.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WriteRefused(
            f"operator state directory is not writable: {state}: "
            f"{exc.strerror or exc}") from exc
    return state


def _is_anchored(root: Path) -> bool:
    return _git_dir(root) is not None


def _operator_lock_path(root: Path) -> Path:
    if _is_anchored(root):
        return _process_state_dir(root) / "operator.lock"
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}.lock"


def _held_entry(root_key: str) -> tuple[str, object] | None:
    for key, mode, handle in _HELD_OPERATOR_LOCKS.get():
        if key == root_key:
            return mode, handle
    return None


def _acquire_flock(handle, *, exclusive: bool, lock_path: Path,
                   timeout: float | None) -> None:
    """Take the flock both modes contend for, announcing the wait (#101).

    A contender probes first and announces the wait on stderr — with the
    holder's pid, command, and start time when the lock file names them —
    instead of hanging silently. `LOS_LOCK_TIMEOUT` (or `los
    --lock-timeout`) bounds the wait identically for both modes; on expiry
    a WriteRefused naming the holder propagates, which every entry point
    maps to exit 2 with nothing changed.
    """
    flag = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    try:
        fcntl.flock(handle.fileno(), flag | fcntl.LOCK_NB)
        return
    except BlockingIOError:
        pass
    holder = _read_holder(lock_path)
    detail = f" {holder}" if holder else ""
    print(f"los: waiting for the operator lock{detail}", file=sys.stderr)
    if timeout is None:
        fcntl.flock(handle.fileno(), flag)
        return
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise WriteRefused(
                f"timed out after {timeout:g}s waiting for the "
                f"operator lock{detail}") from None
        time.sleep(min(_LOCK_POLL_INTERVAL_S, remaining))
        try:
            fcntl.flock(handle.fileno(), flag | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            continue


def _has_armed_inflight(root: Path) -> bool:
    """Whether a published crash journal awaits recovery (read-only probe).

    Staging debris (`.preparing-*`) died before the first canonical
    mutation, so it proves nothing and waits for the next exclusive
    acquisition to drop it. A published journal means canonical state may
    be torn, and a shared lock must not serve it without recovery.
    """
    inflight = root / "operations" / "transactions" / ".inflight"
    try:
        return any(not entry.name.startswith(".preparing-")
                   for entry in inflight.iterdir())
    except FileNotFoundError:
        return False


def _escalate_operator_lock(root: Path) -> bool:
    """Drop a held shared lock and take the exclusive one; True when it dropped.

    Never upgrades in place: the shared lock is released first, then the
    exclusive lock is contended for like any fresh acquisition (announced,
    bounded by the same timeout), and only then do the holder record and
    crash recovery run. Already-exclusive answers False having changed
    nothing. The mode update replaces the context value; the owning
    scope's reset still restores the pre-scope value on exit.
    """
    root_key = str(root.resolve())
    entry = _held_entry(root_key)
    if entry is None:
        raise RuntimeError(
            f"cannot escalate the operator lock for {root_key}: not held")
    mode, handle = entry
    if mode == "exclusive":
        return False
    if mode == "released":
        raise WriteRefused("operator lock is no longer held after a failed escalation")
    # Invalidate re-entrancy before dropping SH. If acquisition, holder
    # publication, or recovery fails, an outer caller that catches the
    # exception must never mistake this scope for a still-held read lock.
    _HELD_OPERATOR_LOCKS.set(tuple(
        (key, "released" if key == root_key else held_mode, held_handle)
        for key, held_mode, held_handle in _HELD_OPERATOR_LOCKS.get()
    ))
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    _acquire_flock(handle, exclusive=True,
                   lock_path=_operator_lock_path(root),
                   timeout=_lock_timeout_seconds())
    _write_holder(handle)
    reconcile_inflight_transactions(root)
    _HELD_OPERATOR_LOCKS.set(tuple(
        (key, "exclusive" if key == root_key else held_mode, held_handle)
        for key, held_mode, held_handle in _HELD_OPERATOR_LOCKS.get()
    ))
    return True


@contextlib.contextmanager
def _operator_lock(root: Path, *, shared: bool = False):
    """Cross-process lock for every read and write/generation transaction.

    Writes take it exclusive, as before. Reads that only serve a provably
    current manifest take it shared (`LOCK_SH`) so they no longer
    serialize against each other; a read that must rebuild drops the
    shared lock, takes the exclusive one, re-checks the identity, then
    builds (see `_fresh_manifest_and_repo`). A write nested inside a
    shared section escalates it — exclusive subsumes the read guarantee,
    it never violates it — and a shared request inside an exclusive
    section passes straight through.

    Shared holders neither write the holder record (concurrent writers
    would garble it) nor run crash recovery (it writes); when a published
    crash journal is present the acquisition escalates to exclusive
    immediately, so every read still observes post-recovery state. The
    wait announcement and `--lock-timeout` semantics are identical for
    both modes, and re-entrancy is unchanged.
    """
    root_key = str(root.resolve())
    entry = _held_entry(root_key)
    if entry is not None:
        held_mode, _ = entry
        if held_mode == "released":
            raise WriteRefused("operator lock is no longer held after a failed escalation")
        if not shared and held_mode == "shared":
            _escalate_operator_lock(root)
        yield
        return
    lock_path = _operator_lock_path(root)
    timeout = _lock_timeout_seconds()
    try:
        handle = lock_path.open("a+", encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(
            f"operator lock is not writable: {lock_path}: "
            f"{exc.strerror or exc}") from exc
    with handle:
        _acquire_flock(handle, exclusive=not shared, lock_path=lock_path,
                       timeout=timeout)
        mode = "shared" if shared else "exclusive"
        if not shared:
            _write_holder(handle)
            reconcile_inflight_transactions(root)
        context_token = _HELD_OPERATOR_LOCKS.set(
            _HELD_OPERATOR_LOCKS.get() + ((root_key, mode, handle),))
        try:
            if shared and _has_armed_inflight(root):
                _escalate_operator_lock(root)
            yield
        finally:
            _HELD_OPERATOR_LOCKS.reset(context_token)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


#: The typed refusal a failed handler step recorded for the gateway.
#:
#: Handlers answer with an int exit code plus printed prose, so a typed
#: refusal caught inside a handler (a revision conflict in
#: ``_write_transaction``, a stale delivery in the AI-action handler)
#: would lose its type at that boundary. The catching step records the
#: ``(code, retryable)`` pair here instead, and the gateway dispatch
#: takes it after a non-zero return. Never reconstructed from prose or
#: from the exit code: exit 3 alone is ambiguous (a snapshot guard, a
#: revision conflict, and a stale reviewed digest all use it).
_GATEWAY_REFUSAL: contextvars.ContextVar[tuple[str, bool] | None] = (
    contextvars.ContextVar("learningos_gateway_refusal", default=None)
)


def _record_gateway_refusal(code: str, retryable: bool) -> None:
    """Carry one typed refusal code across the handler's int-exit boundary."""
    _GATEWAY_REFUSAL.set((code, retryable))


def _take_gateway_refusal() -> tuple[str, bool] | None:
    """Read and clear the recorded refusal, if any."""
    refusal = _GATEWAY_REFUSAL.get()
    _GATEWAY_REFUSAL.set(None)
    return refusal


def _refusal_from_failure(failure: BaseException) -> tuple[str, bool] | None:
    """Map a refusal to its V2 ``(code, retryable)`` by type, never by prose.

    Returns ``None`` for an untyped refusal, which the gateway reports as
    ``INVALID_REQUEST``. ``TransactionConflict`` and
    ``TransactionSnapshotConflict`` normally never reach this helper —
    ``_write_transaction`` records the first and re-raises the second —
    but mapping them here keeps the table total over every failure the
    gateway boundary can observe.
    """
    row = classify(failure, "gateway.refusal")
    if row is None:
        return None
    resolved = resolve(row, failure)
    if resolved["code"] is None:
        return None
    return (resolved["code"], resolved["retryable"])


def _publish(root: Path) -> None:
    _publish_repo(load_repo(root))


def _publish_repo(repo) -> None:
    write_outputs(repo, generate_all(repo))


def _json_layout(stream=None) -> dict:
    """Indented JSON for a person at a terminal, compact JSON on a pipe.

    Agents and the UI read through pipes, where indentation was 15-22% of
    the bytes of inspect, resume, search and semantic output and carried no
    information (measured 2026-09-22). Any JSON parser reads both forms.
    """
    if stream is None:
        stream = sys.stdout
    try:
        interactive = stream.isatty()
    except (AttributeError, ValueError):
        interactive = False
    return {"indent": 2} if interactive else {"separators": (",", ":")}


#: Environment variable naming the calling session. Every gateway write and
#: every `session-end` in one agent session must see the same value, so the
#: harness exports it once per session (WORKFLOWS §25c step 4), or the agent
#: seals `session_id` in each write envelope when the shell does not persist
#: (WORKFLOWS §22). The Obsidian UI exports `ui` for every child it spawns.
SESSION_ID_ENV = "LOS_SESSION_ID"


#: Channel assumed when no session is named and no gateway request is active
#: (a bare `session-end`, a direct `_record_touched` call). This is the
#: operator path WORKFLOWS §25c documents, so the default claims exactly the
#: writes the documented ceremony produces.
DEFAULT_SESSION_CHANNEL = "operator"


#: Ephemeral ledger contract. Version 1 was the single shared file with bare
#: `{state, sha256}` rows; version 2 keys the file per session and stamps
#: every row with its channel and recording time.
SESSION_LEDGER_SCHEMA_VERSION = 2


def _resolve_session_identity(*, channel: str | None = None,
                              explicit: str | None = None
                              ) -> tuple[str, str]:
    """The session identity every ledger operation resolves, and its source.

    Resolution order: an explicit id (the `--session-id` flag), then the
    sealed gateway envelope's `session_id`, then the `LOS_SESSION_ID`
    environment, then the gateway channel — so two actors that name
    nothing still land in separate ledgers by channel (`channel:ui` vs
    `channel:operator`), while one named session shares a single ledger
    whatever channel its writes used. The source is one of `explicit`,
    `envelope`, `environment`, or `channel`.
    """
    if explicit is not None and explicit.strip():
        return explicit.strip(), "explicit"
    request = current_gateway_request()
    if request is not None:
        sealed = (request.session_id or "").strip()
        if sealed:
            return sealed, "envelope"
    env = os.environ.get(SESSION_ID_ENV, "").strip()
    if env:
        return env, "environment"
    resolved = channel
    if resolved is None:
        resolved = request.channel if request is not None else DEFAULT_SESSION_CHANNEL
    return f"channel:{resolved}", "channel"


def _current_session_id(*, channel: str | None = None,
                        explicit: str | None = None) -> str:
    """The session identity every ledger operation resolves the same way."""
    identity, _ = _resolve_session_identity(channel=channel, explicit=explicit)
    return identity


def _session_ledger(root: Path, session_id: str | None = None) -> Path:
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    identity = _current_session_id(explicit=session_id)
    slug = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return _process_state_dir(root) / f"learningos-{token}-{slug}-touched.json"


def _session_path_state(root: Path, relative: str) -> dict[str, str]:
    """Return the exact post-transaction state used to prove session ownership."""
    lexical = root / relative
    try:
        resolved = lexical.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return {"state": "unsafe"}
    if lexical.is_symlink():
        return {"state": "unsafe"}
    if not resolved.exists():
        return {"state": "absent"}
    if not resolved.is_file():
        return {"state": "not-file"}
    try:
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError:
        return {"state": "unreadable"}
    return {"state": "file", "sha256": digest}


def _row_proven_state(row: dict) -> dict[str, str]:
    """The bytes-proving subset of a ledger row, for live-file comparison.

    Provenance (`channel`, `recorded_at`) describes the claim, not the file;
    comparing the whole row against `_session_path_state` would refuse every
    v2 row unconditionally.
    """
    proven = {"state": str(row.get("state", ""))}
    if "sha256" in row:
        proven["sha256"] = str(row["sha256"])
    return proven


def _row_recorded_at(row: dict) -> _dt.datetime | None:
    raw = row.get("recorded_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        moment = _dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_dt.UTC)
    return moment


def _validate_session_row(relative: str, state: object) -> dict[str, str]:
    if not isinstance(relative, str) or not relative \
            or Path(relative).is_absolute() or ".." in Path(relative).parts \
            or not isinstance(state, dict):
        raise WriteRefused("session ownership ledger contains an invalid path row")
    row = {str(key): str(value) for key, value in state.items()}
    if not row.get("state") or not row.get("channel") or not row.get("recorded_at"):
        raise WriteRefused("session ownership ledger contains an unstamped path row")
    if _row_recorded_at(row) is None:
        raise WriteRefused("session ownership ledger contains an undated path row")
    return row


def _load_session_paths(root: Path, session_id: str | None = None) -> dict[str, dict[str, str]]:
    identity = _current_session_id(explicit=session_id)
    ledger = _session_ledger(root, identity)
    if not ledger.is_file():
        return {}
    try:
        data = json.loads(ledger.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WriteRefused(f"session ownership ledger is unreadable: {exc}") from exc
    if not isinstance(data, dict) \
            or data.get("schema_version") != SESSION_LEDGER_SCHEMA_VERSION \
            or not isinstance(data.get("paths"), dict):
        raise WriteRefused("session ownership ledger has an unsupported contract")
    if data.get("session_id") != identity:
        raise WriteRefused("session ownership ledger names a different session")
    return {
        relative: _validate_session_row(relative, state)
        for relative, state in data["paths"].items()
    }


def _stamp_session_row(root: Path, relative: str, channel: str) -> dict[str, str]:
    row = _session_path_state(root, relative)
    row["channel"] = channel
    row["recorded_at"] = observations.now().astimezone(_dt.UTC).replace(
        microsecond=0).isoformat()
    return row


def _atomic_text(path: Path, content: str) -> None:
    """Temp file + os.replace, cleaning up after any failure.

    Every mutating command funnels through here, so an ordinary filesystem
    problem — target replaced by a directory, permission denied, full disk —
    must surface as an actionable refusal instead of a traceback that leaves a
    stray `.tmp` sibling behind.
    """
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise WriteRefused(f"cannot write {path}: {exc.strerror or exc}") from exc


def _write_session_ledger(root: Path, paths: dict[str, dict[str, str]],
                          session_id: str | None = None) -> None:
    identity = _current_session_id(explicit=session_id)
    _atomic_text(_session_ledger(root, identity), json.dumps({
        "schema_version": SESSION_LEDGER_SCHEMA_VERSION,
        "session_id": identity,
        "paths": dict(sorted(paths.items())),
    }, indent=2, sort_keys=True) + "\n")


def _record_touched(root: Path, paths, channel: str | None = None, *,
                    session_id: str | None = None) -> None:
    """Stamp post-write rows into the caller's session ledger.

    The explicit id (`--session-id`) wins over the envelope, the
    environment, and the channel, exactly as `session-end` resolves it,
    so a direct command (like `los goal`, which seals no envelope) can
    still claim its write for the caller's session.
    """
    identity = _current_session_id(channel=channel, explicit=session_id)
    ledger = _session_ledger(root, identity)
    current = _load_session_paths(root, identity) if ledger.is_file() else {}
    request = current_gateway_request()
    actor = channel or (request.channel if request is not None else DEFAULT_SESSION_CHANNEL)
    for path in paths:
        p = Path(path)
        try:
            rel = p.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        # Canvas files are Obsidian UI state, not part of a learning-session
        # action ledger. The protection is about the file type, not the first
        # three default names Obsidian happened to generate.
        if p.suffix.lower() != ".canvas":
            current[rel] = _stamp_session_row(root, rel, actor)
    _write_session_ledger(root, current, identity)


def _confirmation_from(result) -> dict:
    """Receipt facts a command reports after its own successful transaction."""
    if result is None:
        return {}
    parts = result.receipt_path.parts
    try:
        relative = Path(*parts[parts.index("operations"):]).as_posix()
    except ValueError:
        relative = result.receipt_path.name
    return {
        "transaction_id": result.transaction_id,
        "receipt_path": relative,
        "artifact_revisions": dict(result.revisions),
        "snapshot_after": result.snapshot_after,
        "replayed": bool(result.replayed),
    }


# ---------------------------------------------------------------------------
# Fresh-manifest reads, moved verbatim from commands.support for the S15 pilot
# conversions (SPEC (az) item 2: the shared fresh-manifest closure moves below
# its callers instead of taking a new upward A1 import).


class _LazyRepo:
    """``load_repo`` deferred to first attribute access (reuse fast path).

    ``_fresh_manifest_and_repo`` serves the stored manifest without parsing
    canonical inputs; callers that only read the manifest never pay for the
    load (measured: load 0.24 s of a 2.0 s read). The first attribute access
    loads once; afterwards this answers exactly like the real repo. Reads
    that need repo-only state (path-stage lookup, use evidence) trigger the
    load implicitly and stay correct.
    """

    def __init__(self, root: Path) -> None:
        self._lazy_root = root
        self._lazy_repo = None

    def _resolve(self):
        if self._lazy_repo is None:
            self._lazy_repo = load_repo(self._lazy_root)
        return self._lazy_repo

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


def _try_reuse_manifest(root: Path, live_snapshot: str, *, restamp: bool) -> dict | None:
    """The stored manifest when it provably describes current state, else None.

    Every mismatch, missing file, or parse error answers None so the caller
    rebuilds exactly as before; a partially matching or corrupt file is
    never served. Contract/git failures propagate: the fresh build raises
    them identically, so swallowing them here would serve reads the fresh
    path refuses.
    """
    try:
        raw = (root / "generated/manifest.json").read_bytes()
        identity = json.loads((root / "generated" / IDENTITY_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # The sidecar pins the exact manifest bytes it describes: a pair caught
    # mid-publication (or a hand-touched file) never passes as current.
    if not isinstance(identity, dict) or identity.get("manifest_sha256") != bytes_sha256(raw):
        return None
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(manifest, dict):
        return None
    try:
        current, _reason = check_identity(
            root, manifest, identity, live_snapshot=live_snapshot)
    except (OSError, ValueError, DerivedError):
        return None
    if not current:
        return None
    if restamp:
        # Runtime metadata is restamped so the served manifest equals a fresh
        # build byte for byte: git state can move (a docs-only commit) while
        # every pinned input still matches.
        manifest["_generated"]["generated_at"] = stable_generated_at(root)
        revision, dirty = _git_state(root)
        manifest["_generated"]["source_revision"] = revision
        manifest["_generated"]["source_dirty"] = dirty
    return manifest


def _fresh_manifest_and_repo(
    root: Path, *, snapshot_id: str | None = None, restamp: bool = False,
) -> tuple[dict, object]:
    """A current manifest plus the repo it was built from.

    The manifest is served from the stored build when it is provably
    current, otherwise rebuilt exactly as before. ``restamp`` refreshes
    the served ``_generated`` runtime metadata (git state, timestamp) to
    what a fresh build would stamp; pass it only when the caller surfaces
    ``_generated`` (today: full bootstrap) — it costs several git queries
    and every other read answers from payload keys the check already
    verified.
    """
    # Every projection read takes the operator lock shared: concurrent
    # current-manifest reads proceed together, and acquisition still runs
    # crash recovery first (escalating when a journal awaits it), so
    # single-ID reads, batch reads, and bootstrap all observe
    # transaction-consistent post-recovery state instead of disagreeing
    # after a kill (JF-21). Re-entrant: callers already holding the lock
    # (batch inspect, bootstrap, gateway dispatch) pass straight through,
    # staying exclusive when they already are.
    with _operator_lock(root, shared=True):
        # Snapshot-bound callers already computed this under the same lock;
        # sharing it keeps a reuse read at two hashes and a rebuild read
        # at three (see test_bounded_read_hashes_thrice_with_seeded_manifest).
        live = snapshot_id if snapshot_id is not None else f"sha256:{canonical_fingerprint(root)}"
        reused = _try_reuse_manifest(root, live, restamp=restamp)
        if reused is not None:
            return reused, _LazyRepo(root)
        # Stale or missing: drop the shared lock, take the exclusive one,
        # re-check the identity (a writer may have published while the
        # shared lock was down), then build. Never upgrade in place. When
        # the caller already held the lock exclusive, nothing dropped and
        # the snapshot above is still the same instant — no re-hash.
        dropped = _escalate_operator_lock(root)
        if dropped:
            live = f"sha256:{canonical_fingerprint(root)}"
        reused = _try_reuse_manifest(root, live, restamp=restamp)
        if reused is not None:
            return reused, _LazyRepo(root)
        repo = load_repo(root)
        if snapshot_id is not None:
            seed_source_fingerprint(repo, live)
        generated_at = stable_generated_at(root)
        backlinks = build_backlinks(repo, generated_at)
        return build_manifest(repo, generated_at, backlinks), repo


def _fresh_manifest(root: Path, *, snapshot_id: str | None = None,
                    restamp: bool = False) -> dict:
    manifest, _ = _fresh_manifest_and_repo(root, snapshot_id=snapshot_id, restamp=restamp)
    return manifest


# ---------------------------------------------------------------------------
# Read preflight, moved verbatim from commands.reads (SPEC (az) item 2).


def _snapshot(root, expected=None) -> str:
    actual = f"sha256:{canonical_fingerprint(root)}"
    if expected is not None and expected != actual:
        raise StaleSnapshot("snapshot changed; restart this read before continuing")
    return actual


# ---------------------------------------------------------------------------
# Content-bound input, moved verbatim from commands.support (SPEC (az) item 2).


def _read_content_bound_file(
    path_value: str,
    expected_sha256: str | None = None,
    *,
    label: str = "file input",
) -> tuple[Path, bytes]:
    """Read an external file once and verify the bytes a V2 request approved.

    The returned bytes are the bytes the caller must parse or write. Hashing
    and then reopening the pathname would merely move the TOCTOU window.
    Direct human CLI preflights may omit the digest; an active V2 gateway
    context may not.
    """
    if path_value == "-" and current_gateway_request() is not None:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {label} must be a real path with an approved SHA-256; "
            "unbound stdin is not allowed"
        )
    source = Path(path_value).expanduser().resolve()
    if not source.is_file():
        raise WriteRefused(f"no such {label}: {source}")
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise WriteRefused(f"cannot read {label} {source}: {exc}") from exc
    if expected_sha256 is None:
        if current_gateway_request() is not None:
            raise WriteRefused(
                f"GatewayEnvelopeV2 {label} requires a SHA-256 bound to the exact bytes"
            )
        return source, content
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_sha256):
        raise WriteRefused(
            f"{label} SHA-256 must use sha256:<64 lowercase hexadecimal digits>"
        )
    actual_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise WriteRefused(
            f"approved {label} changed before use; expected {expected_sha256}, "
            f"found {actual_sha256}. Review the new bytes and create a new approval."
        )
    return source, content


def _read_structured_file(
    path_value: str,
    *,
    expected_sha256: str | None = None,
    label: str = "structured input",
) -> dict:
    """Read a JSON/YAML object from a path, or from stdin when given ``-``.

    Stdin matters for callers that build an envelope in memory: writing it to
    a temp file first means a real file holding canonical intent has to be
    created, found, and cleaned up on every write path, including the ones
    that fail. ``-`` removes that lifecycle entirely.
    """
    if path_value == "-" and expected_sha256 is None \
            and current_gateway_request() is None:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise WriteRefused(f"cannot parse structured input from stdin: {exc}") from exc
        if not isinstance(data, dict):
            raise WriteRefused("structured input must be an object")
        return data
    path, raw_bytes = _read_content_bound_file(
        path_value,
        expected_sha256,
        label=label,
    )
    try:
        raw = raw_bytes.decode("utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"structured input must be an object: {path}")
    return data


def _require_gateway_v2() -> None:
    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def _input_record_values(record, file_name, label: str) -> dict:
    """The record/file core of ``commands/vnext._input_record`` (SPEC (bl) 3).

    Converted handlers pass their request values directly; the vnext
    wrapper keeps extracting them from the argparse namespace until its
    last caller converts. Validations and messages are the originals.
    """
    if record is not None:
        if not isinstance(record, dict):
            raise WriteRefused(f"{label} must be an object")
        return record
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


# ---------------------------------------------------------------------------
# Structured record/file input, moved verbatim from commands.support for the
# plan record/file conversions (SPEC (bo) item 2).


# ---------------------------------------------------------------------------
# Canonical YAML serialization, moved verbatim from commands.support
# (SPEC (az) item 2).


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def _dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def _render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


def _dump_study_map(study_map, data: dict) -> str:
    from learning_os.material_refs import preserve_map_refs

    return _dump_yaml(preserve_map_refs(study_map, data))


# ---------------------------------------------------------------------------
# Material planning helpers, moved verbatim from commands.material for the
# route.patch conversion (SPEC (az) item 2, (bd)).

def _guard_rows(root, artifacts):
    return {rid: artifact_revision(root, rid) for rid in sorted(set(artifacts))}


def _apply_hint(args, capability, snapshot_id, revisions):
    """Ready-to-submit apply values for a successful --check.

    Direct CLI application is disabled, so the hint echoes everything the
    GatewayEnvelopeV2 needs except the per-request fields (request_id,
    idempotency_key, channel, approval): capability, exact payload,
    expected snapshot, and expected revisions. Output layer only —
    validation, guards, and receipts are unchanged.
    """
    if capability != "route.patch":
        return None
    return {
        "apply_via": "GatewayEnvelopeV2",
        "capability": capability,
        "payload": {
            "unit_id": args.unit_id,
            "route_id": args.route_id,
            "changes": args.changes,
        },
        "expected_snapshot": snapshot_id,
        "expected_revisions": dict(revisions),
        "apply_how": ("direct CLI application is disabled; submit a "
                      "GatewayEnvelopeV2 with this capability, payload, "
                      "expected_snapshot and expected_revisions"),
    }


def _map_for_unit(repo, unit_id):
    maps = [sm for sm in repo.study_maps.values() if sm.unit_id == unit_id]
    if len(maps) > 1:
        raise WriteRefused(f"unit {unit_id} has ambiguous study maps")
    return maps[0] if maps else None


def _changed_write(writes, path, data):
    content = _dump_yaml(data)
    # Callers compare record values first; this second check also avoids a
    # write intent when the exact serialized bytes are already current.
    if path.read_bytes() != content.encode("utf-8"):
        writes[path] = content


# ---------------------------------------------------------------------------
# Notes shared helpers, moved verbatim from commands.support, commands.capability,
# commands.query and commands.reads for the wave-1 notes conversions (SPEC (bl),
# CODEX-WAVE1-DISPOSITIONS-20261010 items 2-3). Bodies and signatures unchanged;
# _window_values is the extracted value-based core of commands.reads._window.


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held."""
    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{observations.new_hex()}",
        "idempotency_key": f"reviewed-{observations.new_hex()}",
        "capability": capability_name,
        "channel": "codex",
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _inbox_search_rows(root: Path) -> list[dict]:
    """One discovery row per inbox file, matched on names only, never bytes.

    Inbox drops are arbitrary files (binary captures included), so the
    metadata search reads no content here: the haystack is the file name
    and path. Content stays behind ``inbox-read``, which refuses non-text.
    Raises OSError when the listing itself fails; a missing inbox is empty.
    """
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return []
    rows = []
    for path in sorted(inbox.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(inbox).as_posix()
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        rows.append({"id": rel, "type": "inbox-item", "title": path.name,
                     "path": f"work/inbox/{rel}"})
    return rows


def _discovery_row(rec):
    """One stable discovery row, shared by search and inbox-list."""
    return {k: rec.get(k) for k in
            ("id", "type", "title", "path", "status",
             "state", "deprecated")}


def _bytes_inside_owner(root, path, owner, *, escape, symlink):
    """Read bytes admitted by one owner directory; symlinks always refuse.

    The one admission rule for note, garden, and inbox reads: the resolved
    target must sit below the owner, and no path component may be a link —
    even one that would resolve in-tree. Only the refusal wording differs
    per surface.
    """
    try:
        path.resolve(strict=True).relative_to(owner.resolve(strict=True))
    except (ValueError, OSError) as exc:
        raise WriteRefused(escape) from exc
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise WriteRefused(symlink)
    return path.read_bytes()


def _note_bytes(root, note):
    return _bytes_inside_owner(
        root, note.path, root / "knowledge" / "notes",
        escape="note path escapes its knowledge owner",
        symlink="note read refuses symlinks")


def _content_envelope(contract, ref_key, ref, relpath, raw, content, offset, limit):
    return {
        "contract": contract, ref_key: ref, "path": relpath,
        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "offset": offset, "offset_unit": "unicode_characters",
        "total_characters": len(content),
        "start_line": content.count("\n", 0, offset) + 1,
        "content": content[offset:offset + limit],
        "next_offset": offset + limit if offset + limit < len(content) else None,
    }


def _note_collection(root):
    """Load only the note registry for note reads/search, not a complete Repo.

    The partial model stays inside these note-only paths. Full canonical
    fingerprints still guard the read before and after, including continuation.
    """
    repo = Repo(root=root)
    load_notes(repo, root)
    return repo


def _window_values(offset: int, limit: int, expected_snapshot: str | None,
                   maximum: int) -> tuple[int, int]:
    """Offset/limit validation with the exact commands.reads._window rules."""
    if offset < 0 or not 1 <= limit <= maximum:
        raise WriteRefused(f"offset must be nonnegative and limit between 1 and {maximum}")
    if offset and not expected_snapshot:
        raise WriteRefused("continuation requires --expected-snapshot from the previous response")
    return offset, limit


# Atlas authoring guards, moved verbatim from commands.atlas for the
# atlas.question.save conversion (SPEC (bo) 2).


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"Atlas cannot use a symlink: {relative}")
    return path


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


# ---------------------------------------------------------------------------
# Atlas relation registries, moved verbatim from commands.atlas for the
# concept.relations.change conversion (SPEC (bo) 2).

RELATION_ARTIFACT = "registry-concept-relations"


def _registries(root: Path) -> dict[Path, dict]:
    single = _safe(root, root / "knowledge/concept-relations.yaml")
    folder = _safe(root, root / "knowledge/concept-relations")
    paths = ([single] if single.exists() else []) + (
        sorted(folder.glob("*.yaml")) if folder.exists() else [])
    if single.exists() and len(paths) > 1:
        raise WriteRefused("both consolidated and partitioned relations exist")
    records = {}
    for path in paths:
        data = yaml.load(_safe(root, path).read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
        _schema(root, "concept-relations", data)
        records[path] = data
    return records


# At most this many untargeted rows ride the screen; the section's
# ``total`` stays exact past the bound. Moved verbatim from
# commands.resume for the plan reads (SPEC (bo) item 2).
MAX_STAGE_RESULTS = 5


# ---------------------------------------------------------------------------
# Analysis-note scope and freshness, moved verbatim from commands.reads
# for the plan reads (SPEC (bo) item 2).


def _analysis_notes(repo):
    return sorted((note for note in repo.notes.values()
                   if isinstance(note.meta.get("material_analysis"), dict)),
                  key=lambda note: note.id)

def _approved_assessments(repo):
    found = []
    for synthesis_id in sorted(repo.unit_material_syntheses):
        data = repo.unit_material_syntheses[synthesis_id]
        if not isinstance(data, dict) or data.get("status") != "approved":
            continue
        unit_id = data.get("unit_id")
        assessments = data.get("route_assessments")
        if not isinstance(assessments, list):
            continue
        for assessment in assessments:
            if isinstance(assessment, dict):
                found.append((synthesis_id, unit_id, assessment))
    found.sort(key=lambda row: (row[1] or "", row[2].get("route_id") or ""))
    return found

def _materials_rel_for_uri(repo, uri) -> str | None:
    """The materials-relative file a ``material://`` URI names, or None.

    Identity only: the file need not exist. Anything resolving outside
    the materials tree — or to a directory rather than a material file —
    is not a material path at all, so folder-level URIs prove no file.
    """
    if not isinstance(uri, str) or not uri:
        return None
    path = material_location(repo, uri).get("material_path")
    if not isinstance(path, str) or not path.startswith("materials/"):
        return None
    rel = path[len("materials/"):]
    if PurePosixPath(rel).suffix.lower() not in MATERIAL_RESOURCE_SUFFIXES:
        return None
    return rel

def _route_material_files(repo, source_id, route) -> set[str]:
    """Every materials-relative file one route reads, or empty when unproven.

    A route's own ``vault_path`` wins as a single file; otherwise a
    semicolon-separated locator naming two or more files resolves to the
    set it names — the same deliberate two-file binding the dossier basis
    resolves for freshness; otherwise the locator's leading file resolves
    against the route's source; otherwise the route inherits the source
    record's held material. The multi-file branch is strict: every part
    must name exactly one safe distinct file, otherwise the route proves
    no file at all rather than guessing one. String routes, prose-only
    locators, and material-less sources prove no file.
    """
    if not isinstance(route, dict):
        route = {}
    vault = _materials_rel_for_uri(repo, route.get("vault_path"))
    if vault is not None:
        return {vault}
    record = repo.sources.get(source_id) if isinstance(source_id, str) else None
    held = record.get("material") if isinstance(record, dict) else None
    authority = material_uri_authority(held)
    if authority is None and isinstance(source_id, str) and source_id:
        # Legacy routes can name an exact source-id-prefixed file without
        # a source-level material field. A declared shared authority wins.
        authority = source_id
    locator = route.get("locator")
    if (isinstance(locator, str) and ";" in locator
            and len(MATERIAL_SUFFIX_TOKEN.findall(locator)) >= 2):
        if authority is None:
            return set()
        candidates: list[str] = []
        for part in locator.split(";"):
            matches = list(MATERIAL_SUFFIX_TOKEN.finditer(part))
            if len(matches) != 1:
                return set()
            candidate = safe_material_locator(part[:matches[0].end()].strip())
            if candidate is None:
                return set()
            candidates.append(candidate)
        if len(candidates) < 2 or len(candidates) != len(set(candidates)):
            return set()
        resolved: set[str] = set()
        for candidate in candidates:
            found = _materials_rel_for_uri(
                repo, f"{MATERIAL_SCHEME}{authority}/{candidate}")
            if found is None:
                return set()
            resolved.add(found)
        return resolved
    head = None
    if isinstance(locator, str):
        # Strict first, then the weaker head-of-prose question — the same
        # order the material projection resolves a row.
        head = safe_material_locator(locator) or leading_material_locator(locator)
    if head and authority:
        found = _materials_rel_for_uri(
            repo, f"{MATERIAL_SCHEME}{authority}/{head}")
        if found is not None:
            return {found}
    inherited = _materials_rel_for_uri(repo, held)
    return {inherited} if inherited is not None else set()

def _single_route_range(route) -> tuple[int, int] | None:
    """The one usable page range a route states, or None.

    Zero ranges (a whole-file route) and several ranges (a curated tour)
    both decline the page test: only a single stated range narrows what a
    note about the file must overlap to count as direct evidence.
    """
    locator = route.get("locator") if isinstance(route, dict) else None
    ranges = parse_locator_page_ranges(locator) if isinstance(locator, str) else []
    return ranges[0] if len(ranges) == 1 else None

def _note_pages(binding) -> tuple[int, int] | None:
    """A note's inspected physical page window, or None when unstated."""
    inspected = binding.get("inspected_range") if isinstance(binding, dict) else None
    if not isinstance(inspected, dict):
        return None
    start, end = inspected.get("start"), inspected.get("end")
    if (isinstance(start, bool) or isinstance(end, bool)
            or not isinstance(start, int) or not isinstance(end, int)):
        return None
    return (start, end) if start <= end else None

def _unit_note_scope(repo, binding, routes) -> str | None:
    """"direct", "related", or None: one note's standing against unit routes.

    THE shared note-to-route rule: material-context and the plan brief
    both answer from here. Material identity comes from existing
    resolution, never from a shared source id alone, and a route stating
    a single usable page range additionally requires physical overlap with
    the note's inspected window. Same-source-only notes are related, never
    direct; notes touching neither the source nor the file are out.
    ``routes`` is (source_id, route-dict) pairs; string routes arrive as
    (source_id, {}) and prove identity only through inheritance.
    """
    if not isinstance(binding, dict):
        return None
    note_sid = binding.get("source_id")
    note_ref = binding.get("material")
    pages = _note_pages(binding)
    standing = None
    for source_id, route in routes:
        same_source = (isinstance(note_sid, str) and note_sid
                       and note_sid == source_id)
        route_files = _route_material_files(repo, source_id, route)
        same_file = (isinstance(note_ref, str) and note_ref
                     and note_ref in route_files)
        if not same_source and not same_file:
            continue
        if same_source and same_file:
            window = _single_route_range(route) if len(route_files) == 1 else None
            if window is None or (
                    pages is not None
                    and window[0] <= pages[1] and pages[0] <= window[1]):
                return "direct"
        standing = "related"
    return standing

def _freshness_label(root, binding, observations=None):
    """Live source freshness: current, stale, or unreadable. Never inferred.

    When `observations` is given, the observed bytes (or their absence)
    are recorded under the material relpath so a paged continuation can
    prove the external state it pages over did not move between pages.
    """
    material = str(binding.get("material") or "")
    observation = observe_local_material(
        root.parent / "materials", material,
        str(binding.get("recorded_source_digest") or ""))
    if observations is not None:
        live = observation.get("live_digest")
        observations[f"material:{material}"] = \
            live if live is not None else observation["status"]
    status = observation["status"]
    if status in ("current", "stale"):
        return status
    return "unreadable"


# ---------------------------------------------------------------------------
# Offset/limit validation with the exact commands.reads._window rules,
# added with exactly the conductor's text for the plan reads and the
# notes wave (SPEC (bs) item 4).


# ---------------------------------------------------------------------------
# Use-evidence tallies and note bytes, moved verbatim from
# commands.reads for the plan reads (SPEC (bo) item 2).


POSITIVE_FEEDBACK = frozenset({"helpful", "useful-for-derivation",
                               "useful-for-review"})

MISMATCH_FEEDBACK = frozenset({"too-advanced", "wrong-perspective"})

def _use_evidence(repo):
    """Recorded stage-use evidence per source id: raw feedback counts.

    Canonical study-map data, so the read's snapshot guard already binds
    it — no observation entry is owed. Counts only; grouping into
    positive/mismatch happens at rank time from the sets above, so a new
    vocabulary value degrades to reported-but-unranked, never to a crash
    or a silent demotion.
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in repo.study_maps.values():
        stages = study_map.data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies

def _evidence_label(tally):
    positive = sum(count for value, count in tally.items()
                   if value in POSITIVE_FEEDBACK)
    mismatch = sum(count for value, count in tally.items()
                   if value in MISMATCH_FEEDBACK)
    return {"counts": dict(sorted(tally.items())),
            "positive": positive, "mismatch": mismatch}

# Value-based window core (SPEC (bl) item 3): the exact validations and
# messages of commands/reads.py:_window, taking request values directly so
# converted handlers pass no namespace.


# ---------------------------------------------------------------------------
# Inbox discovery rows, moved verbatim from commands/query.py (SPEC (bo)
# item 2): the status conversion needs them while search and inbox-list
# still call them from commands.


# ---------------------------------------------------------------------------
# Ranked intelligence scan, moved verbatim from commands/intelligence.py
# (SPEC (bo) item 2): the intelligence-scan conversion needs ranked_scan
# while cmd_resume still calls it from commands. It rests here: the body
# keeps its load_repo, which A4 forbids inside ops/handlers.


def _route_modules(repo) -> dict[str, str]:
    """Route id to owning module id, from the loaded source maps."""
    owners: dict[str, str] = {}
    for module_id, smap in (getattr(repo, "module_source_maps", {}) or {}).items():
        if not isinstance(smap, dict):
            continue
        sources = smap.get("sources")
        if not isinstance(sources, list):
            continue
        for src in sources:
            if not isinstance(src, dict):
                continue
            routes = src.get("unit_routes")
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, dict):
                    continue
                rid = route.get("id")
                if isinstance(rid, str) and rid and rid not in owners:
                    owners[rid] = module_id
    return owners


def _requirement_modules(repo) -> tuple[dict[str, set[str]], dict[str, str]]:
    """Requirement id to owning modules, plus observation id to requirement.

    Best-effort: an unreadable runtime resolves nothing rather than
    refusing the whole scan.
    """
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError:
        return {}, {}
    units = getattr(repo, "units", {}) or {}
    req_modules: dict[str, set[str]] = {}
    for req in requirements:
        if not isinstance(req, dict):
            continue
        source = req.get("source_stage", {})
        unit = units.get(source.get("unit_id", "")) if isinstance(source, dict) else None
        module_id = getattr(unit, "module_id", None)
        if isinstance(req.get("id"), str) and isinstance(module_id, str) and module_id:
            req_modules[req["id"]] = {module_id}
    try:
        observations = read_observations(repo, requirements)
    except RuntimeInputError:
        return req_modules, {}
    obs_requirements = {
        obs["id"]: obs.get("requirement") for obs in observations
        if isinstance(obs, dict) and isinstance(obs.get("id"), str)}
    return req_modules, obs_requirements


def _cluster_modules(repo, route_modules: dict[str, str],
                     req_modules: dict[str, set[str]],
                     obs_requirements: dict[str, str],
                     cluster) -> set[str]:
    """Modules behind one cluster, resolved from member goal ids.

    Study-map obligations name their unit; covering-routes goals name
    their route; lineage and changed-source goals name claims, and a
    ``covers:`` claim resolves through its route; superseded-evidence
    goals name observations, resolved through their requirement.
    Anything unresolvable stays unknown — the ranker treats that as
    tier 4, never urgent.
    """
    modules: set[str] = set()
    units = getattr(repo, "units", {}) or {}
    for goal_id in cluster.member_ids:
        kind, _, rest = goal_id.partition(":")
        if kind == "study-map-obligation":
            unit = units.get(rest)
            module_id = getattr(unit, "module_id", None)
            if isinstance(module_id, str) and module_id:
                modules.add(module_id)
            continue
        if kind == "evidence-superseded":
            req_id = obs_requirements.get(rest)
            modules.update(req_modules.get(req_id, ()))
            continue
        route = rest if kind == "covering-routes-stale" else None
        if route is None and rest.startswith("covers:"):
            route = rest[len("covers:"):]
        if route and route in route_modules:
            modules.add(route_modules[route])
    return modules


def ranked_scan(root, *, days: int = 30,
                feed: Mapping | None = None,
                ) -> tuple[tuple[CandidateGoal, ...], tuple[RankedCluster, ...], int]:
    """Goals clustered by shared cause, ordered by exam proximity.

    Returns ``(goals, ranked, decided_hidden)``. Orchestration over the
    existing detectors plus the goal ledger; still read-only. ``feed``
    is a caller-supplied session-count mapping; None behaves as before.
    """
    goals = intelligence_scan(root, days=days, feed=feed)
    clusters = cluster_goals(goals)
    repo = load_repo(root)
    deadlines = _academic_deadlines(repo)
    module_status = {
        module_id: (module.get("status") if isinstance(module, dict) else None)
        for module_id, module in (getattr(repo, "modules", {}) or {}).items()
    }
    route_modules = _route_modules(repo)
    req_modules, obs_requirements = _requirement_modules(repo)
    mapping = {
        cluster.cluster_id: _cluster_modules(
            repo, route_modules, req_modules, obs_requirements, cluster)
        for cluster in clusters
    }
    ranked = rank_clusters(
        clusters, today=observations.today(), deadlines=deadlines,
        module_status=module_status, cluster_modules=mapping)
    return goals, ranked, len(_read_goal_ledger(root))


# ---------------------------------------------------------------------------
# Stage-use evidence tallies, moved verbatim from commands/reads.py
# (SPEC (bo) item 2): cli.related's related_records and plan's
# material-context both need them, so they rest here.


# The declared source-feedback vocabulary, grouped for ranking. Positive
# values say the source served; mismatch values say it did not fit this
# use. "skipped" is recorded evidence about the stage, not about the
# source, so it is reported and never ranks.
POSITIVE_FEEDBACK = frozenset({"helpful", "useful-for-derivation",
                               "useful-for-review"})
MISMATCH_FEEDBACK = frozenset({"too-advanced", "wrong-perspective"})


def _use_evidence(repo):
    """Recorded stage-use evidence per source id: raw feedback counts.

    Canonical study-map data, so the read's snapshot guard already binds
    it — no observation entry is owed. Counts only; grouping into
    positive/mismatch happens at rank time from the sets above, so a new
    vocabulary value degrades to reported-but-unranked, never to a crash
    or a silent demotion.
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in repo.study_maps.values():
        stages = study_map.data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


def _evidence_label(tally):
    positive = sum(count for value, count in tally.items()
                   if value in POSITIVE_FEEDBACK)
    mismatch = sum(count for value, count in tally.items()
                   if value in MISMATCH_FEEDBACK)
    return {"counts": dict(sorted(tally.items())),
            "positive": positive, "mismatch": mismatch}
