"""Private reading memory: cards, reading debts and their settlement (Plan C).

The store sits beside the repository, never inside it::

    <LearningOS>/reading-memory/
        cards/<sha256>/p<start>-<end>/v<N>.json   immutable card versions
        pending/<entry>.json                     open or overdue reading debts
        settled/<entry>.json                     settled debts (a dismissal covers its session)
        sessions/<session>.json                  last call, recorded end, Stop asks
        log/<session>.jsonl                      one line per save, dismissal, adoption
        .journal/  .lock                         crash-safe multi-file updates

Nothing here is canonical Core data: it is private, owner-only (directories
0700, files 0600), outside Core Git, outside the materials inventory and outside
the published manifest. Records keep the ``material_analysis`` binding concepts
(materials-relative ``material``, bare-hex ``recorded_source_digest``, physical
PDF ``inspected_range``) and validate against
``system/schema/material-reading-card.schema.json`` before they are written.

A card is keyed by file digest and page range; the path is only where the
bytes were last seen, so moving a file keeps its cards. A range is covered when
every page lies inside one current card for the same digest, or inside one
settled dismissal of the caller's own session — another session's dismissal
never covers a later read, it is surfaced as prior-dismissal memory instead.
Every write runs under one ``flock`` and goes through a journal, so a
settlement writes the card version, closes the entry and appends the log line
as one update even across a crash; an append first repairs a torn journal
tail left by a crash.

This module decides; it never raises a gateway refusal. Callers turn the
returned decisions into typed refusals with their own sites.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import stat
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard, cast

from learning_os.store import observations

#: The store directory, a sibling of the Core checkout (C2).
STORE_DIRNAME = "reading-memory"

#: The stored-data schema every record validates against before it is written (C6).
SCHEMA_NAME = "material-reading-card.schema.json"

#: A session may hold this many open entries within one turn (C1.2).
MAX_OPEN_ENTRIES = 4

#: A session with no gateway call for this long may be adopted from (C7).
ADOPT_IDLE = dt.timedelta(hours=2)

#: The Stop hook asks the agent to settle at most this many times per turn (C1.3).
STOP_ASKS = 2

#: The fixed treatment kinds a card may name (agent-first research, section 4.5).
TREATMENT_KINDS = (
    "intuition", "visual", "statement", "derivation", "proof",
    "worked-example", "exercises", "solutions", "application", "overview",
)

DISMISS_REASONS = ("irrelevant", "redundant")

SESSION_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
ENTRY_RE = re.compile(r"^rd-[0-9a-f]{16}$")
CARD_RE = re.compile(r"^card-([0-9a-f]{16})-p([1-9][0-9]*)-([1-9][0-9]*)$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
CONCEPT_RE = re.compile(r"^concept-[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^v([1-9][0-9]*)\.json$")
_RANGE_DIR_RE = re.compile(r"^p([1-9][0-9]*)-([1-9][0-9]*)$")

PARAPHRASE_MIN, PARAPHRASE_MAX = 20, 800
LABEL_MAX = 160
REASON_MIN, REASON_MAX = 5, 300
MAX_POINTERS = 20
MAX_CONCEPTS = 12

_DIR_MODE = 0o700
_FILE_MODE = 0o600


class ReadingStoreError(Exception):
    """The private store cannot be read or written as required.

    Capture fails closed: a study read that cannot persist its entry refuses,
    naming this error, rather than returning text without a debt.
    """


def store_root(core_root: Path) -> Path:
    """The private store for one Core checkout: ``<LearningOS>/reading-memory``."""
    return Path(core_root).resolve().parent / STORE_DIRNAME


def valid_session(value: object) -> TypeGuard[str]:
    """A Claude Code session id: a lowercase canonical UUID (narrows to str)."""
    return isinstance(value, str) and SESSION_RE.fullmatch(value) is not None


def card_name(digest: str, start: int, end: int) -> str:
    """The stable card handle for one digest and page range (C3)."""
    return f"card-{digest[:16]}-p{start}-{end}"


def pages_label(start: int, end: int) -> str:
    """The locator house style for one inclusive physical page range."""
    return f"pdf p. {start}" if start == end else f"pdf pp. {start}-{end}"


def _iso(moment: dt.datetime) -> str:
    return moment.replace(microsecond=0).isoformat()


def _parse_time(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.astimezone()


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _record_bytes(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode("utf-8")


def _contains(outer: dict[str, int], start: int, end: int) -> bool:
    return outer["start"] <= start and end <= outer["end"]


def _overlaps(outer: dict[str, int], start: int, end: int) -> bool:
    return outer["start"] <= end and start <= outer["end"]


def _row_range(row: dict[str, object]) -> dict[str, int]:
    """The inspected_range of a loaded record: a JSON object with start and end."""
    return cast("dict[str, int]", row["inspected_range"])


def settle_command(entry: str) -> str:
    """The exact save and dismiss forms for one entry (C1.6)."""
    return (f"los material-card-settle {entry} --card "
            "'{\"paraphrase\": \"<what these pages do, in your words>\", "
            "\"kinds\": [\"<kind>\"], \"pointers\": [{\"page\": <page>, "
            "\"kind\": \"<kind>\", \"label\": \"<what is there>\"}]}'"
            f"  |  los material-card-settle {entry} --dismiss irrelevant "
            "--reason '<why>'")


def adopt_command(session: str) -> str:
    """The exact adoption form for one ended or idle session (C7)."""
    return f"los material-card-settle --adopt {session}"


@dataclass(frozen=True)
class Read:
    """One extracted PDF span a study read is about to return."""

    digest: str          # bare hex of the bytes the text came from
    material: str        # materials-relative path, where the bytes were seen
    start: int
    end: int
    text_sha256: str     # bare hex of the returned excerpt


@dataclass
class Admission:
    """The gate's answer for one study read (C1).

    ``refusal`` is None when the read may return its text; otherwise one of
    ``overdue``, ``adoptable`` or ``limit`` and nothing was opened.
    """

    refusal: str | None
    states: list[dict[str, object]] = field(default_factory=list)
    opened: list[dict[str, object]] = field(default_factory=list)
    blocking: list[dict[str, object]] = field(default_factory=list)
    adoptable: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    open_entries: list[dict[str, object]] = field(default_factory=list)


@dataclass
class Settlement:
    """One settlement or adoption, as written or as replayed."""

    outcome: str
    entries: list[dict[str, object]]
    card: dict[str, object] | None = None
    replayed: bool = False
    remaining: list[dict[str, object]] = field(default_factory=list)


@dataclass
class SettleRefusal(Exception):
    """A settlement rule refuses the request; nothing was written."""

    slug: str
    message: str
    remedy: str | None = None

    def __str__(self) -> str:
        return self.message


@dataclass
class StopDecision:
    """What the Stop hook does at turn end (C1.3)."""

    block: bool
    entries: list[dict[str, object]]
    asked: int
    overdue: list[dict[str, object]] = field(default_factory=list)


class ReadingStore:
    """The private reading memory of one LearningOS folder."""

    def __init__(self, core_root: Path, *, root: Path | None = None) -> None:
        self.core_root = Path(core_root).resolve()
        self.root = Path(root) if root is not None else store_root(self.core_root)
        self._locked = False

    # ------------------------------------------------------------------ files

    def _check_root(self) -> None:
        try:
            st = os.lstat(self.root)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ReadingStoreError(f"the reading store is unreadable: {self.root}: {exc}") from exc
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise ReadingStoreError(
                f"the reading store must be a real directory, not a link or file: {self.root}")

    def _ensure_dirs(self) -> None:
        self._check_root()
        try:
            for path in (self.root, *(self.root / name for name in
                                      ("cards", "pending", "settled", "sessions", "log", ".journal"))):
                with contextlib.suppress(FileExistsError):
                    os.mkdir(path, _DIR_MODE)
                st = os.lstat(path)
                if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
                    raise ReadingStoreError(f"the reading store holds a non-directory at {path}")
                if stat.S_IMODE(st.st_mode) & 0o077:
                    os.chmod(path, _DIR_MODE)
        except OSError as exc:
            raise ReadingStoreError(f"the reading store cannot be created: {self.root}: {exc}") from exc

    def exists(self) -> bool:
        self._check_root()
        return self.root.is_dir()

    @contextlib.contextmanager
    def locked(self, *, create: bool = True) -> Iterator[bool]:
        """Hold the store lock and recover any journal; yields whether the store exists."""
        if self._locked:
            yield True
            return
        if create:
            self._ensure_dirs()
        elif not self.exists():
            yield False
            return
        try:
            descriptor = os.open(self.root / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                                 _FILE_MODE)
        except OSError as exc:
            raise ReadingStoreError(f"the reading store cannot be locked: {exc}") from exc
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self._locked = True
            self._recover()
            yield True
        finally:
            self._locked = False
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _fsync_dir(self, path: Path) -> None:
        with contextlib.suppress(OSError):
            descriptor = os.open(path, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def _write_file(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
        try:
            if path.read_bytes() == data:
                return
        except FileNotFoundError:
            pass
        # Stage temp files in .journal so crash leftovers stay out of backup_manifest roots.
        journal_dir = self.root / ".journal"
        journal_dir.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
        temp = journal_dir / f".{path.name}.tmp-{os.getpid()}"
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, _FILE_MODE)
        try:
            try:
                view = memoryview(data)
                written = 0
                while written < len(view):
                    written += os.write(descriptor, view[written:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temp, path)
        except BaseException:
            with contextlib.suppress(OSError):
                temp.unlink()
            raise
        self._fsync_dir(journal_dir)
        self._fsync_dir(path.parent)

    def _repair_log_tail(self, path: Path) -> None:
        """Truncate a torn JSONL tail to its last complete newline (fsync).

        A crash mid-append leaves partial bytes after the last newline, which
        key-based dedupe would silently skip forever; nothing else truncates
        them. Appends run under the store lock, so repairing here is safe.
        """
        try:
            descriptor = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ReadingStoreError(f"the reading log is unreadable: {path}: {exc}") from exc
        try:
            size = os.fstat(descriptor).st_size
            if size == 0:
                return
            data = b""
            while len(data) < size:
                chunk = os.read(descriptor, size - len(data))
                if not chunk:
                    break
                data += chunk
            if data.endswith(b"\n"):
                return
            os.ftruncate(descriptor, data.rfind(b"\n") + 1)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _append_line(self, path: Path, line: dict[str, object], key: str) -> None:
        path.parent.mkdir(mode=_DIR_MODE, parents=True, exist_ok=True)
        self._repair_log_tail(path)
        with contextlib.suppress(FileNotFoundError):
            for existing in path.read_text(encoding="utf-8").splitlines():
                with contextlib.suppress(ValueError):
                    if json.loads(existing).get("key") == key:
                        return
        record = dict(line, key=key)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, _FILE_MODE)
        try:
            os.write(descriptor, _canonical(record) + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _apply(self, operations: list[dict[str, object]]) -> None:
        for operation in operations:
            path = self.root / cast(str, operation["path"])
            if operation["op"] == "write":
                self._write_file(path, cast(str, operation["data"]).encode("utf-8"))
            elif operation["op"] == "delete":
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()
            elif operation["op"] == "append":
                self._append_line(path, cast("dict[str, object]", operation["line"]),
                                  cast(str, operation["key"]))
            else:
                raise ReadingStoreError(f"unknown journal operation: {operation['op']!r}")

    def _commit(self, operations: list[dict[str, object]]) -> None:
        """Apply several file changes as one update (journal, then apply, then drop)."""
        if not operations:
            return
        if not self._locked:
            raise ReadingStoreError("store writes need the store lock")
        payload = _canonical({"operations": operations})
        journal = self.root / ".journal" / f"{hashlib.sha256(payload).hexdigest()[:20]}.json"
        try:
            self._write_file(journal, payload)
            self._apply(operations)
            journal.unlink()
            self._fsync_dir(journal.parent)
        except OSError as exc:
            raise ReadingStoreError(f"the reading store cannot be written: {exc}") from exc

    def _recover(self) -> None:
        directory = self.root / ".journal"
        if directory.is_dir():
            for path in sorted(directory.glob("*.json")):
                try:
                    operations = json.loads(path.read_text(encoding="utf-8"))["operations"]
                    self._apply(operations)
                    path.unlink()
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise ReadingStoreError(
                        f"the reading store holds an unreadable journal {path.name}: {exc}") from exc
        data_trees = ("cards", "pending", "settled", "sessions", "log")
        for tree in (directory, *(self.root / name for name in data_trees)):
            if not tree.is_dir():
                continue
            for stale in sorted(tree.rglob(".*.tmp-*")):
                try:
                    if not stale.is_symlink() and stale.is_file():
                        stale.unlink()
                except OSError as exc:
                    raise ReadingStoreError(
                        f"cannot clean stale reading-store temp file {stale.name}: {exc}") from exc

    def _load(self, path: Path) -> dict[str, object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ReadingStoreError(f"unreadable reading-store record {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise ReadingStoreError(f"reading-store record is not an object: {path}")
        return value

    def _validated(self, record: dict[str, object]) -> str:
        from learning_os.store.contracts.json_schema import validate_contract

        try:
            validate_contract(self.core_root, SCHEMA_NAME, record)
        except ValueError as exc:
            raise ReadingStoreError(str(exc)) from exc
        return _record_bytes(record).decode("utf-8")

    def _write_op(self, relative: str, record: dict[str, object]) -> dict[str, object]:
        return {"op": "write", "path": relative, "data": self._validated(record)}

    # ----------------------------------------------------------------- reads

    def entries(self, *, session: str | None = None, settled: bool = False) -> list[dict[str, object]]:
        directory = self.root / ("settled" if settled else "pending")
        if not directory.is_dir():
            return []
        rows = [self._load(path) for path in sorted(directory.glob("rd-*.json"))]
        if session is not None:
            rows = [row for row in rows if row.get("session") == session]
        return sorted(rows, key=lambda row: (cast(str, row.get("opened_at") or ""),
                                             cast(str, row["entry"])))

    def entry(self, name: str) -> tuple[dict[str, object] | None, bool]:
        """The entry and whether it is settled, or (None, False)."""
        if ENTRY_RE.fullmatch(name) is None:
            return None, False
        for settled in (False, True):
            path = self.root / ("settled" if settled else "pending") / f"{name}.json"
            if path.is_file():
                return self._load(path), settled
        return None, False

    def cards(self, digest: str) -> list[dict[str, object]]:
        """The newest version of every card for one digest."""
        directory = self.root / "cards" / digest
        if DIGEST_RE.fullmatch(digest) is None or not directory.is_dir():
            return []
        found: list[dict[str, object]] = []
        for range_dir in sorted(directory.iterdir()):
            if _RANGE_DIR_RE.fullmatch(range_dir.name) is None or not range_dir.is_dir():
                continue
            versions = sorted((int(match.group(1)), path) for path in range_dir.iterdir()
                              if (match := _VERSION_RE.fullmatch(path.name)))
            if versions:
                found.append(self._load(versions[-1][1]))
        return found

    def all_cards(self) -> list[dict[str, object]]:
        directory = self.root / "cards"
        if not directory.is_dir():
            return []
        rows: list[dict[str, object]] = []
        for digest_dir in sorted(directory.iterdir()):
            rows.extend(self.cards(digest_dir.name))
        return rows

    def card(self, name: str) -> dict[str, object] | None:
        """The newest version of one card, by its handle."""
        match = CARD_RE.fullmatch(name or "")
        directory = self.root / "cards"
        if match is None or not directory.is_dir():
            return None
        prefix, start, end = match.group(1), int(match.group(2)), int(match.group(3))
        for digest_dir in sorted(directory.glob(f"{prefix}*")):
            for row in self.cards(digest_dir.name):
                if row["inspected_range"] == {"start": start, "end": end}:
                    return row
        return None

    def covering(self, digest: str, start: int, end: int, *,
                 session: str) -> list[dict[str, object]]:
        """Current cards, plus this session's own settled dismissals, for the range (C4).

        A saved card is reusable coverage for every caller. A dismissal closes
        the obligation only for the session that dismissed it (ADR-021 decision
        4): another session's one-time judgement never suppresses this
        session's reading memory.
        """
        rows: list[dict[str, object]] = [
            card for card in self.cards(digest)
            if _contains(_row_range(card), start, end)]
        rows.sort(key=lambda card: (_row_range(card)["end"] - _row_range(card)["start"],
                                    cast(str, card["card"])))
        for entry in self.entries(settled=True):
            settlement = cast("dict[str, object]", entry.get("settlement") or {})
            if (entry["recorded_source_digest"] == digest
                    and entry.get("session") == session
                    and settlement.get("outcome") in ("dismissed-irrelevant", "dismissed-redundant")
                    and _contains(_row_range(entry), start, end)):
                rows.append(entry)
        return rows

    def prior_dismissals(self, digest: str, start: int, end: int) -> list[dict[str, object]]:
        """Settled dismissals of this range from any session, for surfacing only.

        Informational, never coverage (ADR-021 decision 4): a study read of a
        range another session dismissed still opens its own entry, and the
        answer names the prior dismissal as ``prior-dismissal`` memory.
        """
        found: list[dict[str, object]] = []
        for entry in self.entries(settled=True):
            settlement = cast("dict[str, object]", entry.get("settlement") or {})
            if (entry["recorded_source_digest"] == digest
                    and settlement.get("outcome") in ("dismissed-irrelevant", "dismissed-redundant")
                    and _contains(_row_range(entry), start, end)):
                found.append(entry)
        return found

    def session(self, name: str) -> dict[str, object] | None:
        path = self.root / "sessions" / f"{name}.json"
        return self._load(path) if valid_session(name) and path.is_file() else None

    def _session_record(self, name: str) -> dict[str, object]:
        return self.session(name) or {
            "record": "session", "schema_version": 1, "session": name,
            "started_at": None, "last_call_at": None, "ended_at": None, "stop_blocks": 0}

    def _last_activity(self, name: str, entries: Iterable[dict[str, object]]) -> dt.datetime | None:
        record = self.session(name) or {}
        moments = [_parse_time(record.get("last_call_at")), _parse_time(record.get("started_at"))]
        moments += [_parse_time(row.get("opened_at")) for row in entries]
        present = [moment for moment in moments if moment is not None]
        return max(present) if present else None

    def ended(self, name: str, now: dt.datetime, entries: Iterable[dict[str, object]] = ()) -> bool:
        """A recorded end with no later call, or no gateway call for two hours (C7)."""
        record = self.session(name) or {}
        ended_at = _parse_time(record.get("ended_at"))
        last_call = _parse_time(record.get("last_call_at"))
        if ended_at is not None and (last_call is None or last_call <= ended_at):
            return True
        last = self._last_activity(name, entries)
        return last is None or now - last >= ADOPT_IDLE

    def adoptable(self, caller: str | None, now: dt.datetime) -> dict[str, list[dict[str, object]]]:
        """Unsettled entries of ended or idle sessions other than the caller."""
        by_session: dict[str, list[dict[str, object]]] = {}
        for row in self.entries():
            if row["session"] != caller:
                by_session.setdefault(cast(str, row["session"]), []).append(row)
        return {name: rows for name, rows in sorted(by_session.items())
                if self.ended(name, now, rows)}

    # ----------------------------------------------------------------- serve

    def served_card(self, card: dict[str, object], known_concepts: Iterable[str] | None,
                    *, compact: bool = False) -> dict[str, object]:
        """One card as reads return it: visibly unreviewed, dangling concepts marked."""
        rng = _row_range(card)
        concepts = list(cast("list[str]", card.get("concepts") or []))
        known = set(known_concepts) if known_concepts is not None else None
        dangling = [name for name in concepts if known is not None and name not in known]
        paraphrase = cast(str, card["paraphrase"])
        value: dict[str, object] = {
            "card": card["card"], "version": card["version"],
            "pages": pages_label(rng["start"], rng["end"]),
            "material": card["material"],
            "file_sha256": f"sha256:{card['recorded_source_digest']}",
            "kinds": list(cast("list[str]", card["kinds"])),
            "paraphrase": paraphrase if not compact or len(paraphrase) <= 300
            else paraphrase[:297].rstrip() + "...",
            "concepts": concepts, "dangling_concepts": dangling,
            "review": "unreviewed", "coverage_evidence": False,
        }
        if not compact:
            value["pointers"] = [dict(row) for row in
                                 cast("list[dict[str, object]]", card["pointers"])]
            value["written"] = dict(cast("dict[str, object]", card["written"]))
        return value

    # ------------------------------------------------------------------ gate

    def _touch_op(self, name: str, now: dt.datetime, *, start: bool = False) -> dict[str, object]:
        record = self._session_record(name)
        record["last_call_at"] = _iso(now)
        if start:
            # Only an explicit start/resume clears a recorded end within the same second;
            # passive touches keep ended_at so late hook/shutdown races cannot resurrect it.
            record["ended_at"] = None
            record["started_at"] = _iso(now)
        return self._write_op(f"sessions/{name}.json", record)

    def touch(self, name: str, *, start: bool = False, now: dt.datetime | None = None) -> None:
        """Record a gateway call (or a session start) for one session."""
        if not valid_session(name):
            raise ReadingStoreError(f"not a session id: {name!r}")
        moment = now or observations.now()
        with self.locked(create=True):
            self._commit([self._touch_op(name, moment, start=start)])

    def admit(self, session: str, reads: list[Read], *, now: dt.datetime | None = None) -> Admission:
        """Decide one study read and persist its new entries before any text returns."""
        moment = now or observations.now()
        with self.locked(create=True):
            mine = self.entries(session=session)
            states: list[dict[str, object]] = []
            new: list[Read] = []
            for read in reads:
                covering = self.covering(read.digest, read.start, read.end, session=session)
                if covering:
                    states.append({"read": read, "state": "covered", "covering": covering})
                    continue
                pending = next((row for row in mine
                                if row["recorded_source_digest"] == read.digest
                                and _contains(_row_range(row), read.start, read.end)), None)
                if pending is not None:
                    states.append({"read": read, "state": "pending", "entry": pending})
                    continue
                states.append({"read": read, "state": "opened",
                               "prior_dismissals": self.prior_dismissals(
                                   read.digest, read.start, read.end)})
                new.append(read)
            admission = Admission(refusal=None, states=states)
            open_rows = [row for row in mine if row["state"] == "open"]
            admission.open_entries = list(mine)
            operations = [self._touch_op(session, moment)]
            if new:
                overdue = [row for row in mine if row["state"] == "overdue"]
                adoptable = self.adoptable(session, moment)
                if overdue:
                    admission.refusal, admission.blocking = "overdue", overdue
                elif adoptable:
                    admission.refusal, admission.adoptable = "adoptable", adoptable
                elif len(open_rows) + len(new) > MAX_OPEN_ENTRIES:
                    admission.refusal, admission.blocking = "limit", open_rows
            if admission.refusal is None:
                for read in new:
                    seed = f"{session}\0{read.digest}\0{read.start}\0{read.end}\0{_iso(moment)}"
                    name = "rd-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
                    record = {
                        "record": "entry", "schema_version": 1, "entry": name,
                        "session": session, "material": read.material,
                        "recorded_source_digest": read.digest,
                        "inspected_range": {"start": read.start, "end": read.end},
                        "text_sha256": read.text_sha256, "opened_at": _iso(moment),
                        "state": "open", "overdue_at": None, "adopted_from": [],
                        "settlement": None,
                    }
                    operations.append(self._write_op(f"pending/{name}.json", record))
                    admission.opened.append(record)
                for state in states:
                    if state["state"] == "opened":
                        read = cast(Read, state["read"])
                        state["entry"] = next(row for row in admission.opened
                                              if row["recorded_source_digest"] == read.digest
                                              and row["inspected_range"] == {"start": read.start,
                                                                             "end": read.end})
                admission.open_entries = list(mine) + admission.opened
            self._commit(operations)
            return admission

    # ------------------------------------------------------------ settlement

    def _owned(self, session: str, name: str, request_sha: str) -> tuple[dict[str, object] | None, Settlement | None]:
        """The caller's open entry, or a replay of an existing settlement."""
        if ENTRY_RE.fullmatch(name or "") is None:
            raise SettleRefusal("unknown-entry", f"not an entry handle: {name!r} (rd- and 16 hex)")
        row, settled = self.entry(name)
        if row is None:
            open_names = [cast(str, entry["entry"])
                          for entry in self.entries(session=session)]
            raise SettleRefusal(
                "unknown-entry", f"no reading entry {name}",
                remedy=("your unsettled entries: " + ", ".join(open_names)) if open_names
                else "you hold no unsettled entries")
        if settled:
            settlement = cast("dict[str, object]", row.get("settlement") or {})
            if (settlement.get("session") == session
                    and settlement.get("request_sha256") == request_sha):
                return None, Settlement(outcome=cast(str, settlement.get("outcome", "")),
                                        entries=[row], replayed=True)
            raise SettleRefusal(
                "already-settled",
                f"{name} is already settled as {settlement.get('outcome')} by session "
                f"{settlement.get('session')}; a different settlement would rewrite it")
        if row["session"] != session:
            raise SettleRefusal(
                "not-owner", f"{name} belongs to session {row['session']}, not this one",
                remedy=(adopt_command(cast(str, row["session"]))
                        + "  (only once that session has ended or made no call for two hours)"))
        return row, None

    def _close(self, session: str, row: dict[str, object], outcome: str, now: dt.datetime,
               request_sha: str, *, card: dict[str, object] | None = None, reason: str | None = None,
               covering_card: str | None = None, observed: str | None = None,
               ) -> tuple[list[dict[str, object]], dict[str, object]]:
        closed = dict(row, state="settled", settlement={
            "outcome": outcome, "at": _iso(now), "session": session,
            "request_sha256": request_sha,
            "card": ({"card": card["card"], "version": card["version"]} if card else None),
            "reason": reason, "covering_card": covering_card, "observed_sha256": observed,
        })
        line = {"record": "log", "schema_version": 1, "at": _iso(now), "session": session,
                "entry": row["entry"], "outcome": outcome,
                "card_version": card["version"] if card else None, "from_session": None}
        self._validated(dict(line, key="0" * 64))
        return [
            self._write_op(f"settled/{row['entry']}.json", closed),
            {"op": "delete", "path": f"pending/{row['entry']}.json"},
            {"op": "append", "path": f"log/{session}.jsonl", "line": line,
             "key": hashlib.sha256(f"{row['entry']}\0{outcome}\0{request_sha}".encode()).hexdigest()},
            self._touch_op(session, now),
        ], closed

    def _remaining(self, session: str) -> list[dict[str, object]]:
        return self.entries(session=session)

    def save(self, session: str, name: str, card_input: object, *,
             now: dt.datetime | None = None) -> Settlement:
        """Settle one entry with a card admitted by structure (step 3)."""
        moment = now or observations.now()
        request_sha = hashlib.sha256(_canonical({"save": card_input})).hexdigest()
        with self.locked(create=True):
            row, replay = self._owned(session, name, request_sha)
            if replay is not None:
                replay.remaining = self._remaining(session)
                replay.card = self._recorded_card(replay.entries[0])
                return replay
            assert row is not None
            digest = cast(str, row["recorded_source_digest"])
            rng = _row_range(row)
            card_fields = admit_card(card_input, rng)
            handle = card_name(digest, rng["start"], rng["end"])
            directory = f"cards/{digest}/p{rng['start']}-{rng['end']}"
            existing = sorted(int(match.group(1)) for path in (self.root / directory).glob("v*.json")
                              if (match := _VERSION_RE.fullmatch(path.name)))
            version = (existing[-1] + 1) if existing else 1
            card = {
                "record": "card", "schema_version": 1, "card": handle, "version": version,
                "material": row["material"], "recorded_source_digest": digest,
                "inspected_range": dict(rng), **card_fields, "review": "unreviewed",
                "written": {"session": session, "entry": name, "at": _iso(moment)},
                "supersedes": existing[-1] if existing else None,
            }
            closing, closed = self._close(session, row, "saved", moment, request_sha, card=card)
            self._commit([self._write_op(f"{directory}/v{version}.json", card), *closing])
            return Settlement(outcome="saved", entries=[closed], card=card,
                              remaining=self._remaining(session))

    def _recorded_card(self, row: dict[str, object]) -> dict[str, object] | None:
        settlement = cast("dict[str, object]", row.get("settlement") or {})
        reference = settlement.get("card")
        if not reference:
            return None
        rng = _row_range(row)
        card_ref = cast("dict[str, object]", reference)
        path = (self.root / "cards" / cast(str, row["recorded_source_digest"])
                / f"p{rng['start']}-{rng['end']}" / f"v{card_ref['version']}.json")
        return self._load(path) if path.is_file() else None

    def dismiss(self, session: str, name: str, reason_kind: str, *, reason: str | None = None,
                covering_card: str | None = None, now: dt.datetime | None = None) -> Settlement:
        """Settle one entry as ``irrelevant`` (with a reason) or ``redundant`` (with a card)."""
        moment = now or observations.now()
        request = {"dismiss": reason_kind, "reason": reason, "covering_card": covering_card}
        request_sha = hashlib.sha256(_canonical(request)).hexdigest()
        with self.locked(create=True):
            row, replay = self._owned(session, name, request_sha)
            if replay is not None:
                replay.remaining = self._remaining(session)
                return replay
            assert row is not None
            rng = _row_range(row)
            if reason_kind == "irrelevant":
                text = (reason or "").strip()
                if not REASON_MIN <= len(text) <= REASON_MAX or covering_card is not None:
                    raise SettleRefusal(
                        "bad-dismissal",
                        f"--dismiss irrelevant needs --reason of {REASON_MIN}-{REASON_MAX} "
                        "characters and no --covering-card")
                outcome, kept_reason, kept_card = "dismissed-irrelevant", text, None
            elif reason_kind == "redundant":
                if not covering_card or reason is not None:
                    raise SettleRefusal(
                        "bad-dismissal",
                        "--dismiss redundant needs --covering-card CARD (the card that already "
                        "holds these pages) and no --reason")
                card = self.card(covering_card)
                if (card is None or card["recorded_source_digest"] != row["recorded_source_digest"]
                        or not _contains(_row_range(card), rng["start"], rng["end"])):
                    candidates = [cast(str, row2["card"]) for row2 in self.covering(
                        cast(str, row["recorded_source_digest"]), rng["start"], rng["end"],
                        session=session)
                        if row2.get("record") == "card"]
                    raise SettleRefusal(
                        "not-covering",
                        f"{covering_card} does not hold {pages_label(rng['start'], rng['end'])} "
                        f"of this file (C4: every page inside one current card of the same digest)",
                        remedy=("covering cards: " + ", ".join(candidates)) if candidates
                        else "no current card holds these pages; save a card or dismiss as irrelevant")
                outcome, kept_reason, kept_card = "dismissed-redundant", None, covering_card
            else:
                raise SettleRefusal("bad-dismissal", f"--dismiss takes {' or '.join(DISMISS_REASONS)}")
            operations, closed = self._close(session, row, outcome, moment, request_sha,
                                             reason=kept_reason, covering_card=kept_card)
            self._commit(operations)
            return Settlement(outcome=outcome, entries=[closed], remaining=self._remaining(session))

    def close_source(self, session: str, name: str, *, gone: bool, observed: str | None,
                     materials_root: Path, now: dt.datetime | None = None) -> Settlement:
        """Close one entry whose source changed or vanished, after checking it (step 3)."""
        from learning_os.store.material_analysis import observe_local_material

        moment = now or observations.now()
        request = {"source": "gone" if gone else "changed", "observed": observed}
        request_sha = hashlib.sha256(_canonical(request)).hexdigest()
        with self.locked(create=True):
            row, replay = self._owned(session, name, request_sha)
            if replay is not None:
                replay.remaining = self._remaining(session)
                return replay
            assert row is not None
            seen = observe_local_material(materials_root, cast(str, row["material"]),
                                          cast(str, row["recorded_source_digest"]))
            status = seen["status"]
            if status == "outside-boundary":
                raise SettleRefusal("source-check",
                                    f"{row['material']} resolves outside the materials boundary")
            if gone:
                if status in ("current", "stale"):
                    raise SettleRefusal(
                        "source-check",
                        f"{row['material']} is still there (status {status}); --source-gone "
                        "closes only an entry whose file is absent")
                # The shared observer also reports unreadable paths as missing.
                # Closing a debt requires an observed absence.
                try:
                    (materials_root / cast(str, row["material"])).lstat()
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    raise SettleRefusal(
                        "source-check",
                        f"cannot verify that {row['material']} is absent") from exc
                else:
                    raise SettleRefusal(
                        "source-check",
                        f"{row['material']} still exists; --source-gone requires an absent path")
                outcome, kept = "source-gone", None
            else:
                if status == "current":
                    raise SettleRefusal(
                        "source-check",
                        f"{row['material']} still hashes to the recorded digest; settle the "
                        "entry with a card or a dismissal")
                if status != "stale":
                    raise SettleRefusal(
                        "source-check",
                        f"{row['material']} is absent; close the entry with --source-gone")
                if observed is None:
                    raise SettleRefusal(
                        "source-check",
                        "--source-changed needs --observed-sha256 (the file's current bytes)")
                observed_digest = observed.removeprefix("sha256:")
                if DIGEST_RE.fullmatch(observed_digest) is None:
                    raise SettleRefusal(
                        "source-check",
                        "--observed-sha256 must be a SHA-256 digest "
                        "(bare hex or sha256: prefixed)")
                if observed_digest != seen["live_digest"]:
                    raise SettleRefusal(
                        "source-check",
                        f"--observed-sha256 must equal the file's current bytes "
                        f"(sha256:{seen['live_digest']})")
                outcome, kept = "source-changed", seen["live_digest"]
            operations, closed = self._close(session, row, outcome, moment, request_sha,
                                             observed=kept)
            self._commit(operations)
            return Settlement(outcome=outcome, entries=[closed], remaining=self._remaining(session))

    def adopt(self, session: str, other: str, *, now: dt.datetime | None = None) -> Settlement:
        """Move an ended or idle session's unsettled entries to the caller (C7)."""
        moment = now or observations.now()
        if not valid_session(other) or other == session:
            raise SettleRefusal("bad-adopt", "--adopt takes another session's id (a lowercase UUID)")
        with self.locked(create=True):
            theirs = self.entries(session=other)
            if not theirs:
                mine = [row for row in self.entries(session=session)
                        if other in cast("list[str]", row.get("adopted_from") or [])]
                done = [row for row in self.entries(session=session, settled=True)
                        if other in cast("list[str]", row.get("adopted_from") or [])]
                if mine or done:
                    return Settlement(outcome="adopted", entries=mine + done, replayed=True,
                                      remaining=self._remaining(session))
                raise SettleRefusal("nothing-to-adopt",
                                    f"session {other} holds no unsettled entries")
            if not self.ended(other, moment, theirs):
                raise SettleRefusal(
                    "adopt-live",
                    f"session {other} is still live: it has no recorded end and made a gateway "
                    "call within the last two hours; its entries are not yours to settle")
            operations: list[dict[str, object]] = []
            moved: list[dict[str, object]] = []
            for row in theirs:
                adopted_from = [*cast("list[str]", row.get("adopted_from") or []), other]
                record = dict(row, session=session, state="overdue",
                              overdue_at=row.get("overdue_at") or _iso(moment),
                              adopted_from=adopted_from)
                operations.append(self._write_op(f"pending/{row['entry']}.json", record))
                line = {"record": "log", "schema_version": 1, "at": _iso(moment),
                        "session": session, "entry": row["entry"], "outcome": "adopted",
                        "card_version": None, "from_session": other}
                self._validated(dict(line, key="0" * 64))
                hop = f"{row['entry']}\0adopted\0{other}\0{len(adopted_from)}"
                operations.append({
                    "op": "append", "path": f"log/{session}.jsonl", "line": line,
                    "key": hashlib.sha256(hop.encode()).hexdigest()})
                moved.append(record)
            operations.append(self._touch_op(session, moment))
            self._commit(operations)
            return Settlement(outcome="adopted", entries=moved, remaining=self._remaining(session))

    # ------------------------------------------------------------------ hooks

    def stop(self, session: str, *, continuing: bool, now: dt.datetime | None = None) -> StopDecision:
        """Turn end: ask twice, then mark open entries overdue (C1.3).

        Stop fires per turn, so it never records an end: only ``session_end``
        (the SessionEnd hook) or the two-hour idle threshold makes a session's
        unsettled entries adoptable (C7, ADR-021 decision 5).
        """
        moment = now or observations.now()
        with self.locked(create=True):
            record = self._session_record(session)
            asked = int(cast(int, record.get("stop_blocks") or 0)) if continuing else 0
            mine = self.entries(session=session)
            if mine and asked < STOP_ASKS:
                record["stop_blocks"] = asked + 1
                self._commit([self._write_op(f"sessions/{session}.json", record)])
                return StopDecision(block=True, entries=mine, asked=asked + 1)
            operations: list[dict[str, object]] = []
            overdue: list[dict[str, object]] = []
            for row in mine:
                if row["state"] == "open":
                    marked = dict(row, state="overdue", overdue_at=_iso(moment))
                    operations.append(self._write_op(f"pending/{row['entry']}.json", marked))
                    overdue.append(marked)
            record["stop_blocks"] = 0
            operations.append(self._write_op(f"sessions/{session}.json", record))
            self._commit(operations)
            return StopDecision(block=False, entries=mine, asked=asked, overdue=overdue)

    def session_end(self, name: str, *, now: dt.datetime | None = None) -> None:
        """Session termination: record the end and reset the Stop counter (C7).

        The SessionEnd hook calls this when a session terminates; with the
        two-hour idle threshold it is the only thing that makes a session's
        unsettled entries adoptable. The stored schema needs no change: a
        session record already carries ``ended_at``.
        """
        if not valid_session(name):
            raise ReadingStoreError(f"not a session id: {name!r}")
        moment = now or observations.now()
        with self.locked(create=True):
            record = self._session_record(name)
            record["ended_at"] = _iso(moment)
            record["stop_blocks"] = 0
            self._commit([self._write_op(f"sessions/{name}.json", record)])


def admit_card(value: object, rng: dict[str, int]) -> dict[str, object]:
    """The admitted card fields, or a refusal naming the first structural defect (step 3)."""
    def bad(message: str) -> SettleRefusal:
        return SettleRefusal("bad-card", f"card refused: {message}")

    if not isinstance(value, dict):
        raise bad("--card must be one JSON object")
    allowed = {"paraphrase", "kinds", "pointers", "concepts"}
    extra = sorted(set(value) - allowed)
    if extra:
        raise bad(f"unknown fields {', '.join(extra)}; allowed: {', '.join(sorted(allowed))}")
    paraphrase = value.get("paraphrase")
    if not isinstance(paraphrase, str) or not PARAPHRASE_MIN <= len(paraphrase.strip()) <= PARAPHRASE_MAX:
        raise bad(f"paraphrase must be {PARAPHRASE_MIN}-{PARAPHRASE_MAX} characters in your own words")
    kinds = value.get("kinds")
    if (not isinstance(kinds, list) or not kinds or len(set(map(str, kinds))) != len(kinds)
            or any(kind not in TREATMENT_KINDS for kind in kinds)):
        raise bad(f"kinds must be a non-empty list of distinct values from: {', '.join(TREATMENT_KINDS)}")
    pointers = value.get("pointers")
    if not isinstance(pointers, list) or not 1 <= len(pointers) <= MAX_POINTERS:
        raise bad(f"pointers must be a list of 1-{MAX_POINTERS} {{page, kind, label}} objects")
    kept: list[dict[str, object]] = []
    for index, pointer in enumerate(pointers):
        if not isinstance(pointer, dict) or set(pointer) != {"page", "kind", "label"}:
            raise bad(f"pointer {index} must be exactly {{page, kind, label}}")
        page, kind, label = pointer["page"], pointer["kind"], pointer["label"]
        if not isinstance(page, int) or isinstance(page, bool) or not rng["start"] <= page <= rng["end"]:
            raise bad(f"pointer {index} page {page!r} is outside the recorded range "
                      f"{pages_label(rng['start'], rng['end'])}")
        if kind not in kinds:
            raise bad(f"pointer {index} kind {kind!r} is not one of the card's kinds")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= LABEL_MAX:
            raise bad(f"pointer {index} label must be 1-{LABEL_MAX} characters")
        kept.append({"page": page, "kind": kind, "label": label.strip()})
    unbacked = [kind for kind in kinds if not any(row["kind"] == kind for row in kept)]
    if unbacked:
        raise bad(f"kinds {', '.join(unbacked)} have no page pointer inside the range")
    concepts = value.get("concepts", [])
    if (not isinstance(concepts, list) or len(concepts) > MAX_CONCEPTS
            or any(not isinstance(name, str) or CONCEPT_RE.fullmatch(name) is None for name in concepts)
            or len(set(concepts)) != len(concepts)):
        raise bad(f"concepts must be a list of at most {MAX_CONCEPTS} distinct concept ids")
    return {"paraphrase": paraphrase.strip(), "kinds": list(kinds), "pointers": kept,
            "concepts": list(concepts)}


def entry_view(row: dict[str, object]) -> dict[str, object]:
    """One entry as refusals and reads name it."""
    rng = _row_range(row)
    return {"entry": row["entry"], "state": row["state"], "material": row["material"],
            "file_sha256": f"sha256:{row['recorded_source_digest']}",
            "pages": pages_label(rng["start"], rng["end"]), "session": row["session"]}


__all__ = [
    "ADOPT_IDLE", "MAX_OPEN_ENTRIES", "STOP_ASKS", "STORE_DIRNAME", "TREATMENT_KINDS",
    "Admission", "Read", "ReadingStore", "ReadingStoreError", "SettleRefusal",
    "Settlement", "StopDecision", "adopt_command", "admit_card",
    "card_name", "entry_view", "pages_label", "settle_command", "store_root",
    "valid_session",
]
