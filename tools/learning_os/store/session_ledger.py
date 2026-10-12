"""The session-ownership ledger store (PLAN D7, SPEC §13).

Session identity, ledger paths, reads, writes, row helpers, staleness and
foreign-ledger discovery, moved verbatim from `ops/_legacy_plumbing.py` and
the session parts of `commands/support.py`. This module is the single owner
of the ledger sink; every importer was updated in the same commit.
"""

from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from learning_os import observations
from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.failures import WriteRefused

#: Positive-only cache of repository roots to their git directories. A root
#: that gains a `.git` mid-process (tests do) must be re-probed, so misses
#: are never cached; hits are revalidated with `is_dir`.
_GIT_DIR_CACHE: dict[str, tuple[tuple[int, ...], Path]] = {}


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
#: every row with its channel and recording time; version 3 adds the D7
#: machine envelope (`version`, `state`, `review`, `commit_sha`).
SESSION_LEDGER_SCHEMA_VERSION = 3

#: Ledger contracts the reader accepts. A version 2 file reads as
#: recording/version 0/null witness and is rewritten as v3 on the next
#: write (SPEC §13, M-06).
_READABLE_SESSION_LEDGER_VERSIONS = frozenset({2, 3})

#: D7 machine states (PLAN D7, SPEC §13).
_SESSION_STATES = frozenset({"recording", "reviewed", "committed_unpushed"})


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


def _validate_session_review(review: object) -> dict | None:
    """The v3 `review` member, validated, or None when absent.

    A present witness carries the ledger version it was taken at plus the
    exact per-path sha256 (None when the path was no readable file then).
    Anything else is a contract violation, refused with today's message.
    """
    if review is None:
        return None
    if not isinstance(review, dict) \
            or not isinstance(review.get("version"), int) \
            or isinstance(review.get("version"), bool) \
            or not isinstance(review.get("states"), dict):
        raise WriteRefused("session ownership ledger has an unsupported contract")
    states = {}
    for relative, state in review["states"].items():
        if not isinstance(relative, str) or not isinstance(state, dict):
            raise WriteRefused("session ownership ledger has an unsupported contract")
        digest = state.get("sha256")
        if digest is not None and not isinstance(digest, str):
            raise WriteRefused("session ownership ledger has an unsupported contract")
        states[relative] = {"sha256": digest}
    return {"version": review["version"], "states": states}


def _load_session_ledger(root: Path, session_id: str | None = None) -> dict | None:
    """The own ledger as a v3 envelope, or None when no ledger file exists.

    A version 2 file reads as recording/version 0/null witness/null SHA and
    is rewritten as v3 on the next write. Every refusal keeps today's
    message: unreadable, unsupported contract, or a different session.
    """
    identity = _current_session_id(explicit=session_id)
    ledger = _session_ledger(root, identity)
    if not ledger.is_file():
        return None
    try:
        data = json.loads(ledger.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WriteRefused(f"session ownership ledger is unreadable: {exc}") from exc
    if not isinstance(data, dict) \
            or data.get("schema_version") not in _READABLE_SESSION_LEDGER_VERSIONS \
            or not isinstance(data.get("paths"), dict):
        raise WriteRefused("session ownership ledger has an unsupported contract")
    if data.get("session_id") != identity:
        raise WriteRefused("session ownership ledger names a different session")
    paths = {
        relative: _validate_session_row(relative, state)
        for relative, state in data["paths"].items()
    }
    if data.get("schema_version") == 2:
        return {"schema_version": 3, "session_id": identity, "version": 0,
                "state": "recording", "paths": paths, "review": None,
                "commit_sha": None}
    version = data.get("version")
    state = data.get("state")
    commit_sha = data.get("commit_sha")
    if not isinstance(version, int) or isinstance(version, bool) \
            or state not in _SESSION_STATES \
            or (commit_sha is not None and not isinstance(commit_sha, str)):
        raise WriteRefused("session ownership ledger has an unsupported contract")
    return {"schema_version": 3, "session_id": identity, "version": version,
            "state": state, "paths": paths,
            "review": _validate_session_review(data.get("review")),
            "commit_sha": commit_sha}


def _load_session_paths(root: Path, session_id: str | None = None) -> dict[str, dict[str, str]]:
    """The own ledger's validated path rows, or {} when no ledger exists."""
    envelope = _load_session_ledger(root, session_id)
    if envelope is None:
        return {}
    return envelope["paths"]


def _stamp_session_row(root: Path, relative: str, channel: str) -> dict[str, str]:
    row = _session_path_state(root, relative)
    row["channel"] = channel
    row["recorded_at"] = observations.now().astimezone(_dt.UTC).replace(
        microsecond=0).isoformat()
    return row


def _atomic_text(path: Path, content: str) -> None:
    """Temp file + os.replace, cleaning up after any failure.

    The ledger sink's own I/O: an ordinary filesystem problem — target
    replaced by a directory, permission denied, full disk — surfaces as an
    actionable refusal instead of a traceback that leaves a stray `.tmp`
    sibling behind.
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
                          session_id: str | None = None, *,
                          version: int, state: str,
                          review: dict | None, commit_sha: str | None) -> None:
    """Write the own ledger as one v3 envelope (SPEC §13, M-06).

    The whole envelope is explicit: no caller may silently reset the
    version, the state, the witness or the recorded SHA.
    """
    identity = _current_session_id(explicit=session_id)
    _atomic_text(_session_ledger(root, identity), json.dumps({
        "schema_version": SESSION_LEDGER_SCHEMA_VERSION,
        "session_id": identity,
        "version": version,
        "state": state,
        "paths": dict(sorted(paths.items())),
        "review": review,
        "commit_sha": commit_sha,
    }, indent=2, sort_keys=True) + "\n")


def _record_touched(root: Path, paths, channel: str | None = None, *,
                    session_id: str | None = None) -> None:
    """Stamp post-write rows into the caller's session ledger.

    The explicit id (`--session-id`) wins over the envelope, the
    environment, and the channel, exactly as `session-end` resolves it,
    so a direct command (like `los goal`, which seals no envelope) can
    still claim its write for the caller's session.

    Every call increments the envelope version and keeps the state, the
    witness and the recorded SHA: a later recording invalidates a review
    by version, never by erasing the witness.
    """
    identity = _current_session_id(channel=channel, explicit=session_id)
    envelope = (_load_session_ledger(root, identity)
                if _session_ledger(root, identity).is_file() else None)
    current = dict(envelope["paths"]) if envelope is not None else {}
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
    _write_session_ledger(
        root, current, identity,
        version=(envelope["version"] if envelope is not None else 0) + 1,
        state=envelope["state"] if envelope is not None else "recording",
        review=envelope["review"] if envelope is not None else None,
        commit_sha=envelope["commit_sha"] if envelope is not None else None)


#: A ledger row older than this is reported as stale and is no longer staged
#: by default. A forgotten window is surfaced, never silently inherited.
SESSION_LEDGER_STALE_HOURS = 24


def _legacy_session_ledger(root: Path) -> Path:
    """The pre-session shared ledger filename, now read-only history."""
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}-touched.json"


def _row_is_stale(row: dict, now: _dt.datetime | None = None) -> bool:
    """Whether a row is too old to stage without an explicit flag.

    A row whose age cannot be proven is stale: staging it would inherit a
    claim of unknown vintage.
    """
    moment = _row_recorded_at(row)
    if moment is None:
        return True
    now = now or observations.now().astimezone(_dt.UTC)
    return (now - moment).total_seconds() > SESSION_LEDGER_STALE_HOURS * 3600


def _read_sibling_session_ledger(path: Path) -> tuple[str, dict[str, dict]] | None:
    """Parse one foreign ledger file, tolerantly: a corrupt sibling must not
    break this session's close — its own owner still hits the strict loader."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("paths"), dict):
        return None
    identity = data.get("session_id")
    if data.get("schema_version") not in _READABLE_SESSION_LEDGER_VERSIONS \
            or not isinstance(identity, str) or not identity:
        return None
    rows: dict[str, dict] = {}
    for relative, state in data["paths"].items():
        if not isinstance(relative, str) or not relative \
                or Path(relative).is_absolute() or ".." in Path(relative).parts \
                or not isinstance(state, dict):
            return None
        rows[relative] = {str(key): str(value) for key, value in state.items()}
    return identity, rows


def _load_other_session_ledgers(root: Path,
                                session_id: str | None = None
                                ) -> dict[str, dict[str, dict]]:
    """Every session ledger for this root except this session's own.

    Includes the pre-session shared file (reported as `legacy`, with its rows
    undated) so an upgrade never silently drops rows — they surface as
    foreign, never staged. During the transition from the temp-dir location,
    ledgers still sitting in the old location are found here too and
    reported as foreign — including this session's own previous-location
    rows, which are labelled so they cannot be mistaken for the live ones.
    """
    own = _current_session_id(explicit=session_id)
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    pattern = f"learningos-{token}-*-touched.json"
    others: dict[str, dict[str, dict]] = {}
    own_ledger = _session_ledger(root, own)

    def _claim(candidate: Path, *, previous_location: bool) -> None:
        if candidate == own_ledger:
            return
        parsed = _read_sibling_session_ledger(candidate)
        if parsed is None:
            return
        identity, rows = parsed
        if identity == own:
            if not previous_location:
                return
            identity = f"{own} (previous location)"
        if identity in others:
            others[identity] = {**rows, **others[identity]}
        else:
            others[identity] = rows

    try:
        current = sorted(_process_state_dir(root).glob(pattern))
    except OSError:
        current = []
    for candidate in current:
        _claim(candidate, previous_location=False)
    if _is_anchored(root):
        # The old temp-dir location: every ledger written there before the
        # move still surfaces, as foreign, until the OS reclaims it.
        try:
            previous = sorted(Path(tempfile.gettempdir()).glob(pattern))
        except OSError:
            previous = []
        for candidate in previous:
            _claim(candidate, previous_location=True)
    legacy = _legacy_session_ledger(root)
    if legacy.is_file():
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            data = None
        if isinstance(data, dict) and isinstance(data.get("paths"), dict):
            rows = {}
            for relative, state in data["paths"].items():
                if isinstance(relative, str) and relative \
                        and not Path(relative).is_absolute() \
                        and ".." not in Path(relative).parts \
                        and isinstance(state, dict):
                    rows[relative] = {str(key): str(value)
                                      for key, value in state.items()}
            if rows:
                others.setdefault("legacy", rows)
    return others
