"""PEP 578 audit hook attributing canonical writes (SPEC §3.2c)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

_INSTALLED = False
_ACTIVE_LOG: str | None = None
_IN_HOOK = False
_EVENTS: dict | None = None

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


def install(log_path: str) -> None:
    """Register the hook once per process and activate ``log_path``."""
    global _INSTALLED, _ACTIVE_LOG, _EVENTS
    if not _INSTALLED:
        _EVENTS = _events_for_version()
        sys.addaudithook(_hook)
        _INSTALLED = True
    _ACTIVE_LOG = str(log_path)


def uninstall() -> None:
    """Deactivate logging; the hook stays registered and idle."""
    global _ACTIVE_LOG
    _ACTIVE_LOG = None


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


def _is_write_open(mode, flags) -> bool:
    if isinstance(mode, str) and any(mark in mode for mark in "wax+"):
        return True
    if isinstance(flags, int) and (flags & _WRITE_FLAGS):
        return True
    return False


def _current_phase():
    try:
        from learning_os.transactions import current_engine_phase

        return current_engine_phase()
    except Exception:
        return None


def _hook(event: str, args) -> None:
    global _IN_HOOK
    if _IN_HOOK or _ACTIVE_LOG is None or _EVENTS is None:
        return
    if event not in _EVENTS:
        return
    _IN_HOOK = True
    try:
        layout = _EVENTS[event]
        record: dict | None = None
        if event == "open":
            path_index = layout.get("path", 0)
            mode_index = layout.get("mode", 1)
            flags_index = layout.get("flags", 2)
            raw_path = args[path_index] if path_index < len(args) else None
            mode = args[mode_index] if mode_index < len(args) else None
            flags = args[flags_index] if flags_index < len(args) else None
            if not _is_write_open(mode, flags):
                return
            path = _coerce_path(raw_path)
            mode_text = mode if isinstance(mode, str) else None
            record = {
                "event": event,
                "paths": [path],
                "mode": mode_text,
                "phase": _current_phase(),
                "pid": os.getpid(),
            }
        elif event == "subprocess.Popen":
            argv_index = layout.get("argv", 1)
            argv = args[argv_index] if argv_index < len(args) else []
            try:
                argv_list = [str(item) for item in list(argv)]
            except TypeError:
                argv_list = [str(argv)]
            record = {
                "event": event,
                "paths": [],
                "mode": None,
                "phase": _current_phase(),
                "pid": os.getpid(),
                "argv": argv_list,
            }
        else:
            if "paths" in layout:
                indices = layout["paths"]
            elif "path" in layout:
                indices = [layout["path"]]
            else:
                return
            paths = []
            for index in indices:
                if index >= len(args):
                    continue
                coerced = _coerce_path(args[index])
                if isinstance(coerced, str):
                    coerced = _resolve_relative(event, args, coerced)
                paths.append(coerced)
            record = {
                "event": event,
                "paths": paths,
                "mode": None,
                "phase": _current_phase(),
                "pid": os.getpid(),
            }
        if record is not None:
            with open(_ACTIVE_LOG, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
    except Exception:
        pass
    finally:
        _IN_HOOK = False
