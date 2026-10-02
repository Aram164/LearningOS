"""Shared plumbing for every command: repository root, the operator lock, atomic writes,
the transaction wrapper and its receipt, and the small YAML/Markdown helpers."""

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
from pathlib import Path

import yaml

from learning_os.commands.suggest import not_found
from learning_os.contracts.gateway import (
    current_gateway_request,
    gateway_snapshot_is_verified,
)
from learning_os.derived.model import DerivedError
from learning_os.fingerprint import (
    canonical_fingerprint,
    seed_source_fingerprint,
    source_fingerprint,
)
from learning_os.genout import (
    build_backlinks,
    build_manifest,
    generate_all,
    stable_generated_at,
    write_outputs,
)
from learning_os.genout.common import _git_state
from learning_os.loader import load_repo
from learning_os.manifest_identity import IDENTITY_FILENAME, bytes_sha256, check_identity
from learning_os.rules import validate
from learning_os.transactions import (
    PostCommitFailure,
    ProjectionFailure,
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    TransactionSnapshotConflict,
    parse_expected_revisions,
    reconcile_inflight_transactions,
)

TOOLS = Path(__file__).resolve().parent.parent.parent
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

def _root(args) -> Path:
    return Path(args.root).resolve() if args.root else TOOLS.parent


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
              "since": _dt.datetime.now().strftime("%H:%M:%S")}
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(record))
        handle.flush()
    except OSError:
        pass  # a waiter then prints the bare waiting line instead


def _allocate_attachment_path(attachment_dir: Path, source_name: str) -> Path:
    """A destination no existing attachment occupies.

    Attachment bytes are approved canonical content, so the previous holder of a
    name must never be overwritten. A timestamp was not a uniqueness argument:
    it is precise to one second and the name it produced was never itself
    checked, so two uploads of `handwriting.png` within the same second silently
    replaced the first one's bytes.

    Every candidate is checked now, and the counter guarantees the search ends
    on a free name. Checking existence is sufficient here — and only here —
    because every caller allocates while holding the operator lock, so no other
    process can take the name between this check and the transaction that writes
    it.
    """
    target = attachment_dir / source_name
    if not target.exists():
        return target

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = attachment_dir / f"{stamp}-{source_name}"
    if not target.exists():
        return target

    counter = 1
    while True:
        target = attachment_dir / f"{stamp}-{counter}-{source_name}"
        if not target.exists():
            return target
        counter += 1


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


class WriteRefused(Exception):
    """A canonical write could not be performed; nothing was changed."""


class StaleSnapshot(WriteRefused):
    """A supplied concurrency token no longer matches live state; nothing was changed.

    The only refusal that maps to exit 3 (optimistic-concurrency conflict).
    Raised only where a supplied snapshot — or the material-context
    observations digest — differs from the live one. Never inferred from
    message prose: refusals echo user input, and the word "snapshot" in a
    mistyped id or a missing-flag hint is not a conflict.
    """



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


def _expected_ok(root: Path, expected: str | None) -> bool:
    if expected is None:
        return True
    request = current_gateway_request()
    if request is not None:
        if request.expected_snapshot != expected:
            print(
                "los: handler snapshot does not match the approved gateway intent",
                file=sys.stderr,
            )
            return False
        # cmd_capability marks this only while it holds the same operator lock
        # through the complete handler dispatch. Direct service tests and any
        # future bypass do not inherit the shortcut and must compare normally.
        if gateway_snapshot_is_verified(root, expected):
            return True
    if not expected.strip():
        # An empty token is almost always a scripting slip (a command
        # substitution that returned nothing), not a deliberate unguarded
        # write. Omitting the flag remains the way to write unguarded.
        print("los: --expected-snapshot was empty; refusing to write without a "
              "concurrency token", file=sys.stderr)
        return False
    # The snapshot is a content digest, not a loaded-domain property. Loading
    # the whole repository only to call the same path-based digest added a full
    # parse to every UI write and did not strengthen the concurrency check.
    actual = f"sha256:{canonical_fingerprint(root)}"
    if actual == expected:
        return True
    if current_gateway_request() is None:
        # Found by synthetic use: a direct CLI write with a current snapshot is
        # refused by `_write_transaction` as "use GatewayEnvelopeV2", but the
        # same write with a stale or invented one was refused here first, as a
        # projection conflict telling the caller to reload and try again. It
        # cannot succeed on any snapshot, so "reload before writing" sends a
        # script into a loop against a door that is closed for another reason.
        # Both facts are true; the one that decides the outcome goes first.
        print("los: canonical writes must use GatewayEnvelopeV2; direct CLI "
              "application is disabled — reloading will not change this. The "
              "supplied snapshot is also out of date. Submit the write with "
              "`los capability NAME --payload-file ENVELOPE.json` "
              "(envelope: WORKFLOWS §25c).", file=sys.stderr)
        print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
        return False
    print("los: projection conflict — authored files changed since the app loaded; "
          "reload before writing", file=sys.stderr)
    print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
    return False


def _publish(root: Path) -> None:
    _publish_repo(load_repo(root))


def _publish_repo(repo) -> None:
    write_outputs(repo, generate_all(repo))


def _path_or_error(root: Path, path_id: str):
    repo = load_repo(root)
    learning_path = repo.learning_paths.get(path_id)
    if learning_path is None or learning_path.archived:
        active = [key for key, row in repo.learning_paths.items()
                  if not row.archived]
        print(f"los: {not_found('active learning path', path_id, active)}",
              file=sys.stderr)
        return repo, None
    return repo, learning_path


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
        # sharing it keeps the read at two hashes (see
        # test_bounded_read_hashes_twice_with_seeded_manifest).
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


def _print_rows(rows: list[dict]) -> int:
    print(json.dumps(rows, **_json_layout(), sort_keys=True, ensure_ascii=False))
    return 0


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


# --------------------------------------------------------- curriculum writes
#: Environment variable naming the calling session. Every gateway write and
#: every `session-end` in one agent session must see the same value, so the
#: harness exports it once per session (WORKFLOWS §25c step 4), or the agent
#: seals `session_id` in each write envelope when the shell does not persist
#: (WORKFLOWS §22). The Obsidian UI exports `ui` for every child it spawns.
SESSION_ID_ENV = "LOS_SESSION_ID"

#: Environment variable naming the Core client and its build, stamped by the
#: interface on every Core child it spawns (`obsidian-ui/<build>`). An
#: unmarked call stays valid: terminal agents send nothing, and `session-end`
#: never refuses one. Informational only — staleness is proven by comparing
#: the installed build against the built one (see `health._ui_plugin_check`),
#: never by trusting this marker.
CLIENT_ENV = "LOS_CLIENT"

#: Channel assumed when no session is named and no gateway request is active
#: (a bare `session-end`, a direct `_record_touched` call). This is the
#: operator path WORKFLOWS §25c documents, so the default claims exactly the
#: writes the documented ceremony produces.
DEFAULT_SESSION_CHANNEL = "operator"

#: A ledger row older than this is reported as stale and is no longer staged
#: by default. A forgotten window is surfaced, never silently inherited.
SESSION_LEDGER_STALE_HOURS = 24

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


def _legacy_session_ledger(root: Path) -> Path:
    """The pre-session shared ledger filename, now read-only history."""
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}-touched.json"


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


def _row_is_stale(row: dict, now: _dt.datetime | None = None) -> bool:
    """Whether a row is too old to stage without an explicit flag.

    A row whose age cannot be proven is stale: staging it would inherit a
    claim of unknown vintage.
    """
    moment = _row_recorded_at(row)
    if moment is None:
        return True
    now = now or _dt.datetime.now(_dt.UTC)
    return (now - moment).total_seconds() > SESSION_LEDGER_STALE_HOURS * 3600


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


def _write_session_ledger(root: Path, paths: dict[str, dict[str, str]],
                          session_id: str | None = None) -> None:
    identity = _current_session_id(explicit=session_id)
    _atomic_text(_session_ledger(root, identity), json.dumps({
        "schema_version": SESSION_LEDGER_SCHEMA_VERSION,
        "session_id": identity,
        "paths": dict(sorted(paths.items())),
    }, indent=2, sort_keys=True) + "\n")


def _stamp_session_row(root: Path, relative: str, channel: str) -> dict[str, str]:
    row = _session_path_state(root, relative)
    row["channel"] = channel
    row["recorded_at"] = _dt.datetime.now(_dt.UTC).replace(
        microsecond=0).isoformat()
    return row


def _record_touched(root: Path, paths, channel: str | None = None) -> None:
    identity = _current_session_id(channel=channel)
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
    if data.get("schema_version") != SESSION_LEDGER_SCHEMA_VERSION \
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


def _write_transaction(root: Path, writes: dict[Path, str | bytes],
                       *, capability: str = "legacy.write",
                       expected_revisions: dict[str, int] | None = None,
                       artifact_ids=(), deletes=(),
                       metadata=None) -> tuple[int, list, dict]:
    """Commit one named, receipt-producing canonical transaction.

    Returns ``(code, errors, confirmation)``. The confirmation travels back to
    the caller explicitly rather than through module state: a command reports
    the receipt for *its own* transaction, and a module global could not
    express that — it outlived the operator lock and was read after release.
    On any failure the confirmation is empty, so a caller cannot accidentally
    report a receipt for a write that did not happen.
    """
    if current_gateway_request() is None:
        # Name the way through, not only the refusal: the bare named command
        # is what agents find first, and without a pointer the envelope format
        # has to be reverse-engineered from the gateway source.
        return 2, [
            "canonical writes must use GatewayEnvelopeV2; direct CLI application "
            f"is disabled — apply it with `los capability {capability} "
            f"--payload-file ENVELOPE.json` (payload schema: `los capabilities "
            f"{capability} --json`; envelope: WORKFLOWS §25c)"
        ], {}
    service = TransactionService(root)
    delete_paths = tuple(Path(path) for path in deletes)
    for path in (*writes, *delete_paths):
        if path.exists() and not path.is_file():
            return 2, [f"cannot change {path}: target is not a regular file"], {}
    validated_repo = None

    def validation_errors():
        nonlocal validated_repo
        validated_repo = load_repo(root)
        return [
            issue for issue in validate(validated_repo, online=False)
            if issue.severity == "E"
        ]

    def publish_validated_state(snapshot_after_id: str | None = None) -> str:
        nonlocal validated_repo
        repo = validated_repo or load_repo(root)
        if snapshot_after_id is not None:
            seed_source_fingerprint(repo, snapshot_after_id)
        _publish_repo(repo)
        projected_snapshot = f"sha256:{source_fingerprint(repo)}"
        validated_repo = None
        return projected_snapshot

    try:
        result = service.commit(
            capability=capability,
            writes=writes,
            deletes=delete_paths,
            artifact_ids=artifact_ids,
            expected_revisions=expected_revisions or {},
            validate_state=validation_errors,
            publish=publish_validated_state,
            rollback_publish=lambda: _publish(root),
            touched=lambda paths: _record_touched(root, paths),
            metadata=metadata,
        )
    except TransactionConflict as exc:
        print("los: artifact revision conflict — reload the affected record before writing",
              file=sys.stderr)
        print(json.dumps({
            "conflicts": {artifact: {"expected": expected, "actual": actual}
                          for artifact, (expected, actual) in exc.conflicts.items()}
        }, ensure_ascii=False), file=sys.stderr)
        return 3, [], {}
    except TransactionSnapshotConflict:
        # The V2 gateway owns the typed stale-snapshot response. Let the exact
        # expected/actual values cross that boundary without being flattened
        # into a generic transaction failure.
        raise
    except (ProjectionFailure, PostCommitFailure):
        # Typed failure provenance crosses the (code, errors) channel by
        # propagation: the gateway classifies by its attrs, and direct CLI
        # use still exits 2 through los.py's TransactionFailure handler.
        raise
    except TransactionFailure as exc:
        # Canonical write refusal is a handled operator error, not an internal
        # process failure. Preserve the gateway's established exit-code 2.
        return 2, [str(exc)], {}
    return 0, [], _confirmation_from(result)


def _expected_revisions_from_args(args) -> dict[str, int]:
    try:
        return parse_expected_revisions(getattr(args, "expected_revision", None))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc


def _add_expected_revision_argument(parser) -> None:
    parser.add_argument(
        "--expected-revision", action="append", default=[],
        help="artifact-level concurrency token <artifact-id>=<revision>; repeatable",
    )


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


def _unit_map_or_error(root: Path, unit_id: str):
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        print(f"los: {not_found('unit', unit_id, repo.units)}", file=sys.stderr)
        return repo, None, None
    map_id = unit.data.get("current_study_map")
    study_map = repo.study_maps.get(map_id) if map_id else None
    if study_map is None:
        print(f"los: unit has no current study map: {unit_id}", file=sys.stderr)
        return repo, unit, None
    return repo, unit, study_map


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def _dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def _dump_study_map(study_map, data: dict) -> str:
    from learning_os.material_refs import preserve_map_refs

    return _dump_yaml(preserve_map_refs(study_map, data))


#: The one return-to-work record. `los resume` and the app's Home both start
#: here, so they cannot disagree about where the learner left off.
RESUME_POINTER_PATH = "curriculum/resume.yaml"


def _resume_pointer_write(root: Path, *, module_id: str, unit_id: str,
                          study_map_id: str, stage_id: str) -> dict[Path, str]:
    """The resume-pointer file for one explicit study action.

    Returned as a ``{path: text}`` fragment to merge into the *same*
    ``_write_transaction`` as the records that moved. That is the whole point:
    the pointer is written under the operator lock the caller already holds,
    inside the capability's declared write scope, covered by the same receipt,
    the same post-action scope check, the same validation and the same
    republished projection. A separate write after the transaction would be an
    untracked side effect that could survive a rolled-back change, or be lost
    while the change committed — and the destination would then be lying about
    where the work actually is.

    Until 2026-09-13 nothing wrote this file at all. `curriculum/resume.yaml`
    did not exist; `los resume` silently recovered through "last recorded
    result", and the app's Home, which reads only this pointer, said "Nothing
    to resume yet". Activating a stage in another subject therefore left both
    interfaces pointing at the old one (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F05).
    """
    pointer = {
        "type": "resume-pointer",
        "module_id": str(module_id),
        "unit_id": str(unit_id),
        "study_map_id": str(study_map_id),
        "stage_id": str(stage_id),
        "updated": _dt.date.today().isoformat(),
    }
    return {root / RESUME_POINTER_PATH: _dump_yaml(pointer)}


def _render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()




def _replace_registry_list_record(content: str, record_id: str, record: dict) -> str:
    """Render one record in a top-level YAML list without reformatting siblings."""
    lines = content.splitlines(keepends=True)
    id_line = next((i for i, line in enumerate(lines)
                    if re.match(rf"^[ ]*(?:- )?id: {re.escape(record_id)}[ ]*$",
                                line.rstrip("\r\n"))), None)
    if id_line is None:
        raise ValueError(f"registry record not found in source text: {record_id}")
    id_indent = len(lines[id_line]) - len(lines[id_line].lstrip(" "))
    if lines[id_line].lstrip(" ").startswith("- id:"):
        start = id_line
        item_indent = " " * id_indent
    else:
        item_indent = " " * max(0, id_indent - 2)
        start = next((i for i in range(id_line, -1, -1)
                      if lines[i].startswith(item_indent + "- ")), None)
        if start is None:
            raise ValueError(f"registry list item not found for: {record_id}")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith(item_indent + "- ")), len(lines))
    rendered = _dump_yaml(record).rstrip().splitlines()
    replacement = item_indent + "- " + rendered[0] + "\n"
    replacement += "\n".join(item_indent + "  " + line if line else ""
                              for line in rendered[1:])
    replacement += "\n\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:]).lstrip("\n")


def _stage(data: dict, stage_id: str):
    return next((row for row in data.get("stages", []) or []
                 if isinstance(row, dict) and row.get("id") == stage_id), None)


def _stage_ids(data: dict) -> list[str]:
    """Stage ids of one study map or learning path, for not-found suggestions."""
    return [str(row["id"]) for row in data.get("stages", []) or []
            if isinstance(row, dict) and row.get("id")]


# ---------------------------------------------------- validate / generate
def _delegate(script: str, extra: list[str], args) -> int:
    """One implementation of every rule: shell out to the canonical script."""
    cmd = [sys.executable, str(TOOLS / script), *extra]
    if args.root:
        cmd += ["--root", str(_root(args))]
    return subprocess.run(cmd).returncode
