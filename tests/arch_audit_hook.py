"""PEP 578 audit hook attributing canonical writes (SPEC §3.2c)."""

from __future__ import annotations

import json
import os
import sys
import threading
from collections.abc import Mapping
from pathlib import Path

import yaml

_INSTALLED = False
_ACTIVE_LOG: str | None = None
_STATE = threading.local()
_EVENTS: dict | None = None
_RENDER_FN = None

# Only these mechanical frames may delegate, and only to their immediate
# production caller. An engine frame further out cannot authorize a callback.
MECHANICAL_HELPERS = {
    "learning_os.store.durable_fs": frozenset({"learning_os.store.transactions"}),
}

#: Events logged only while the render marker is set (SPEC §3.5b).
_RENDER_ONLY_EVENTS = frozenset({
    "os.listdir",
    "os.scandir",
    "glob.glob",
    "socket.connect",
    "socket.getaddrinfo",
    "learningos.observation",
})

#: The refusal-witness file (SPEC (bf) item 10): when set, every
#: ``learningos.refusal`` audit event appends one item 8.1 JSON line.
#: The single home of the variable name; the session fixture and the
#: A9 module import it from here.
SITE_WITNESS_ENV = "LOS_SITE_WITNESS_FILE"

#: Render-only events a reads-mode install also logs without the marker.
_READS_EVENTS = frozenset({
    "os.listdir",
    "os.scandir",
    "glob.glob",
})

#: Reads mode for the active window: log every `open` in any mode, plus
#: the directory-traversal events above. Set by `install(reads=True)`.
_READS = False

_CAPTURE_LOCK = threading.Lock()
_CAPTURE_ERROR: str | None = None


class AuditCaptureError(Exception):
    """Audit evidence could not be captured or read (SPEC §3.2c, K30)."""


_DIR_FD_INDEX: dict[str, tuple[int, ...]] = {
    "os.rename": (2, 3),
    "os.remove": (1,),
    "os.rmdir": (1,),
    "os.mkdir": (2,),
    "os.link": (2, 3),
    "os.symlink": (2,),
}

_WRITE_FLAGS = (
    os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
)


def _events_for_version() -> dict:
    path = Path(__file__).resolve().parent / "architecture" / "audit-events.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    key = f"{sys.version_info[0]}.{sys.version_info[1]}"
    if key not in data:
        raise RuntimeError(f"no audit-event inventory for Python {key}")
    return data[key]


def install(log_path: str, *, reads: bool = False) -> None:
    """Validate ``log_path``, register the hook once, and activate the path.

    Validation runs first: a directory path, a missing parent, or a failed
    append-open raises ``AuditCaptureError`` and activates nothing. A
    successful install clears the sticky capture error (amendment (k)).
    With ``reads`` true the window logs every ``open`` in any mode, plus
    ``os.listdir``, ``os.scandir`` and ``glob.glob``.
    """
    global _INSTALLED, _ACTIVE_LOG, _EVENTS, _READS
    candidate = str(log_path)
    if os.path.isdir(candidate):
        raise AuditCaptureError(
            f"audit log path is a directory: {candidate}")
    parent = os.path.dirname(os.path.abspath(candidate))
    if not os.path.isdir(parent):
        raise AuditCaptureError(
            f"audit log parent does not exist: {parent}")
    try:
        with open(candidate, "a", encoding="utf-8"):
            pass
    except OSError as exc:
        raise AuditCaptureError(
            f"cannot open audit log for append: {candidate}: {exc}") from exc
    if not _INSTALLED:
        _EVENTS = _events_for_version()
        sys.addaudithook(_hook)
        _INSTALLED = True
    with _CAPTURE_LOCK:
        global _CAPTURE_ERROR
        _CAPTURE_ERROR = None
    _ACTIVE_LOG = candidate
    _READS = bool(reads)


def uninstall() -> None:
    """Deactivate logging; the hook stays registered and idle.

    Never clears the sticky capture error (amendment (k)).
    """
    global _ACTIVE_LOG, _READS
    _ACTIVE_LOG = None
    _READS = False


def capture_ok() -> bool:
    """True when no recording error has been captured in this window."""
    return _CAPTURE_ERROR is None


def capture_error() -> str | None:
    """The first recording error in this window, or None."""
    return _CAPTURE_ERROR


def assert_capture_ok() -> None:
    """Raise ``AuditCaptureError`` when this window captured an error."""
    error = _CAPTURE_ERROR
    if error is not None:
        raise AuditCaptureError(f"audit capture failed: {error}")


def read_log(log_path: str | Path) -> list[dict]:
    """Parsed JSON records from an activated audit log.

    A missing or unreadable log raises ``AuditCaptureError``: absent
    evidence is a failure, never an empty capture.
    """
    candidate = str(log_path)
    try:
        text = Path(candidate).read_text(encoding="utf-8")
    except OSError as exc:
        raise AuditCaptureError(
            f"cannot read audit log: {candidate}: {exc}") from exc
    records = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _record_capture_error(exc: BaseException) -> None:
    global _CAPTURE_ERROR
    with _CAPTURE_LOCK:
        if _CAPTURE_ERROR is None:
            _CAPTURE_ERROR = f"{type(exc).__name__}: {exc}"


def _coerce_path(value):
    if isinstance(value, int):
        return value
    if isinstance(value, bytes):
        try:
            return os.fsdecode(value)
        except OSError:
            return repr(value)
    if isinstance(value, str):
        return value
    return str(value)


def _dir_fd_used(event: str, args) -> bool:
    for index in _DIR_FD_INDEX.get(event, ()):
        if index < len(args):
            value = args[index]
            if value is not None and value != -1:
                return True
    return False


def _resolve_relative(event: str, args, path: str) -> str:
    if os.path.isabs(path):
        return path
    if _dir_fd_used(event, args):
        return path
    try:
        cwd = os.getcwd()
    except OSError:
        return path
    return os.path.normpath(os.path.join(cwd, path))


def _operational_paths(event: str, args, paths: list, mode=None) -> list:
    """Supplemental resolved destinations for A19; original A2 paths stay exact.

    Python's open audit omits os.open's dir_fd. A relative descriptor-open
    therefore remains unresolved. Other pinned events expose dir_fd, which
    can be resolved live through F_GETPATH on Darwin or /proc on Linux.
    """
    resolved = []
    indexes = _DIR_FD_INDEX.get(event, ())
    for index, path in enumerate(paths):
        if isinstance(path, int):
            fd = path
            path = ""
        elif not isinstance(path, str):
            resolved.append(None)
            continue
        elif os.path.isabs(path):
            resolved.append(path)
            continue
        elif event == "open" and mode is None:
            resolved.append(None)
            continue
        else:
            fd_index = indexes[index] if index < len(indexes) else None
            if event == "os.symlink":
                fd_index = 2 if index == 1 else None
            fd = args[fd_index] if fd_index is not None and fd_index < len(args) else None
        try:
            if fd is None or fd == -1:
                base = os.getcwd()
            elif sys.platform == "darwin":
                import fcntl

                raw = fcntl.fcntl(fd, fcntl.F_GETPATH, b"\0" * 1024)
                base = os.fsdecode(raw.split(b"\0", 1)[0])
            elif sys.platform.startswith("linux"):
                base = os.readlink(f"/proc/self/fd/{fd}")
            else:
                resolved.append(None)
                continue
            resolved.append(os.path.normpath(os.path.join(base, path)))
        except (OSError, ValueError, TypeError):
            resolved.append(None)
    return resolved


def _is_write_open(mode, flags) -> bool:
    if isinstance(mode, str) and any(mark in mode for mark in "wax+"):
        return True
    if isinstance(flags, int) and (flags & _WRITE_FLAGS):
        return True
    return False


def _current_phase():
    try:
        from learning_os.store.transactions import current_engine_phase

        return current_engine_phase()
    except Exception:
        return None


def _production_frames() -> list[tuple[str, str, int]]:
    import traceback

    result = []
    for frame in reversed(traceback.extract_stack()):
        filename = frame.filename.replace(os.sep, "/")
        for marker, prefix in (("/tools/learning_os/", "learning_os."),
                               ("/tools/migrations/", "migrations.")):
            index = filename.rfind(marker)
            if index >= 0:
                relative = filename[index + len(marker):].removesuffix(".py")
                result.append((prefix + relative.replace("/", "."), frame.filename, frame.lineno))
                break
    return result


def delegated_owner(frames: list[tuple[str, str, int]]) -> str | None:
    if not frames:
        return None
    helper = frames[0][0]
    allowed = MECHANICAL_HELPERS.get(helper)
    if allowed is None:
        return None
    caller = next((module for module, _, _ in frames if module != helper), None)
    return caller if caller in allowed else None


def _current_writer() -> tuple[str | None, str | None, int | None]:
    """The innermost writing module under tools/ (SPEC §3.6, A19).

    Walks the live stack outward from the hook frame and returns
    ``(module, file, line)`` for the first frame whose file lies under
    ``tools/learning_os/`` or ``tools/migrations/``. A shared sink frame
    is only the first such frame; ownership still requires the sink
    rules in the A19 test, never this value alone. Returns
    ``(None, None, None)`` when no such frame exists (fail closed).
    """
    try:
        frames = _production_frames()
    except Exception:
        return None, None, None
    return frames[0] if frames else (None, None, None)


def _current_render():
    """The running renderer as [operation, callback], or None (SPEC §3.5b).

    The render module is imported lazily; success is cached, while a miss
    is retried on the next event (the module may become importable after
    startup path setup). Nested audit events during the import return
    early on the active flag set by the calling hook.
    """
    global _RENDER_FN
    if _RENDER_FN is None:
        try:
            from learning_os.app.render import current_render
        except Exception:
            return None
        _RENDER_FN = current_render
    try:
        marker = _RENDER_FN()
    except Exception:
        return None
    if marker is None:
        return None
    return [marker[0], marker[1]]


def _launch_token_and_crash(args) -> tuple:
    """The launch token and crash expectation for a Popen event (K28)."""
    env = args[3] if len(args) > 3 else None
    if isinstance(env, Mapping):
        try:
            token = env.get("LOS_ARCH_LAUNCH_TOKEN")
        except Exception:
            token = None
        try:
            expect_crash = env.get("LOS_ARCH_EXPECT_CRASH") == "1"
        except Exception:
            expect_crash = False
        return token, expect_crash
    try:
        token = os.environ.get("LOS_ARCH_LAUNCH_TOKEN")
    except Exception:
        token = None
    try:
        expect_crash = os.environ.get("LOS_ARCH_EXPECT_CRASH") == "1"
    except Exception:
        expect_crash = False
    return token, expect_crash


def _refusal_line(args) -> dict | None:
    """The item 8.1 JSON line for a ``learningos.refusal`` event.

    ``(operation, kind, site, class_name, code)`` from
    ``ops/pipeline.py``; anything else is not a refusal line. The
    commit-refused, direct-refused, diagnostic-failure and
    command-failure lines carry a null site, exactly as item 8.1,
    SPEC (bg) item 1, SPEC (ct) item 1 and SPEC (cx) D-9 fix them.
    """
    operation, kind, site, class_name, code = args
    if kind == "failure":
        return {"operation": operation, "kind": kind, "site": site,
                "class": class_name, "exit_code": code}
    if kind == "commit-refused":
        return {"operation": operation, "kind": kind, "site": None,
                "code": code}
    if kind == "direct-refused":
        return {"operation": operation, "kind": kind, "site": None,
                "code": code}
    if kind == "diagnostic-failure":
        if site is not None or class_name is not None:
            return None
        if type(code) is not int or code != 1:
            return None
        return {"operation": operation, "kind": kind, "site": None,
                "code": code}
    if kind == "command-failure":
        if site is not None or class_name is not None:
            return None
        if type(code) is not int or code == 0:
            return None
        return {"operation": operation, "kind": kind, "site": None,
                "code": code}
    return None


def _append_refusal_line(args) -> None:
    """Append one witness line when the witness file is set (item 10.2).

    Runs under the re-entrancy guard, so the append is never itself
    audited. The event never reaches the audit log. A write failure
    is swallowed; the missing line then fails the A7/A9 match.
    """
    _STATE.active = True
    try:
        path = os.environ.get(SITE_WITNESS_ENV)
        if not path:
            return
        line = _refusal_line(args)
        if line is None:
            return
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(line) + "\n")
        except OSError:
            pass
    finally:
        _STATE.active = False


def _hook(event: str, args) -> None:
    if getattr(_STATE, "active", False) or _ACTIVE_LOG is None or _EVENTS is None:
        return
    if event == "learningos.refusal":
        try:
            _append_refusal_line(args)
        except Exception as exc:
            _record_capture_error(exc)
        return
    if event not in _EVENTS:
        return
    _STATE.active = True
    try:
        layout = _EVENTS[event]
        render = _current_render()
        if event in _RENDER_ONLY_EVENTS and render is None \
                and not (_READS and event in _READS_EVENTS):
            return
        record: dict | None = None
        if event == "open":
            path_index = layout.get("path", 0)
            mode_index = layout.get("mode", 1)
            flags_index = layout.get("flags", 2)
            raw_path = args[path_index] if path_index < len(args) else None
            mode = args[mode_index] if mode_index < len(args) else None
            flags = args[flags_index] if flags_index < len(args) else None
            if not _is_write_open(mode, flags) and render is None \
                    and not _READS:
                return
            path = _coerce_path(raw_path)
            mode_text = mode if isinstance(mode, str) else None
            writer, writer_file, writer_line = _current_writer()
            record = {
                "event": event,
                "paths": [path],
                "mode": mode_text,
                "phase": _current_phase(),
                "pid": os.getpid(),
                "render": render,
                "writer": writer,
                "writer_file": writer_file,
                "writer_line": writer_line,
            }
        elif event == "subprocess.Popen":
            argv_index = layout.get("argv", 1)
            argv = args[argv_index] if argv_index < len(args) else []
            try:
                argv_list = [str(item) for item in list(argv)]
            except TypeError:
                argv_list = [str(argv)]
            token, expect_crash = _launch_token_and_crash(args)
            record = {
                "event": event,
                "paths": [],
                "mode": None,
                "phase": _current_phase(),
                "pid": os.getpid(),
                "argv": argv_list,
                "token": token,
                "expect_crash": expect_crash,
                "render": render,
            }
        else:
            if "paths" in layout:
                indices = layout["paths"]
            elif "path" in layout:
                indices = [layout["path"]]
            else:
                return
            resolve = layout.get("resolve", True)
            paths = []
            for index in indices:
                if index >= len(args):
                    continue
                coerced = _coerce_path(args[index])
                if resolve and isinstance(coerced, str):
                    coerced = _resolve_relative(event, args, coerced)
                paths.append(coerced)
            writer, writer_file, writer_line = _current_writer()
            record = {
                "event": event,
                "paths": paths,
                "mode": None,
                "phase": _current_phase(),
                "pid": os.getpid(),
                "render": render,
                "writer": writer,
                "writer_file": writer_file,
                "writer_line": writer_line,
            }
        if record is not None:
            if record.get("writer") in MECHANICAL_HELPERS:
                record["delegated_owner"] = delegated_owner(_production_frames())
            if "paths" in record:
                record["resolved_paths"] = _operational_paths(event, args, record["paths"], record.get("mode"))
            with open(_ACTIVE_LOG, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
    except Exception as exc:
        _record_capture_error(exc)
    finally:
        _STATE.active = False
