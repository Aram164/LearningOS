"""Child-process audit hook entry (SPEC §3.2c)."""
import json
import os
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_tests = _here.parent
# The audit installer imports production modules before Python starts the
# requested script. Pin this harness's checkout first: a shared editable venv
# may otherwise preload a different worktree and invalidate every witness.
_tools = _tests.parent / "tools"
if str(_tools) in sys.path:
    sys.path.remove(str(_tools))
sys.path.insert(0, str(_tools))
if str(_tests) not in sys.path:
    sys.path.insert(0, str(_tests))

_log = os.environ.get("LOS_ARCH_AUDIT_LOG")
if _log:
    # Step 1: read this launch's token.
    _token = os.environ.get("LOS_ARCH_LAUNCH_TOKEN")
    try:
        # Test-only forced failure, honoured before install (fixture 9).
        if os.environ.get("LOS_ARCH_AUDIT_FORCE_FAIL") == "1":
            raise RuntimeError("LOS_ARCH_AUDIT_FORCE_FAIL=1")
        # Step 2: install. On any exception, record install_failed and stop.
        import arch_audit_hook

        arch_audit_hook.install(_log)
    except Exception as _exc:
        _failed = {
            "event": "install_failed",
            "pid": os.getpid(),
            "token": _token,
            "error": f"{type(_exc).__name__}: {_exc}",
        }
        try:
            with open(_log, "a", encoding="utf-8") as _handle:
                _handle.write(json.dumps(_failed) + "\n")
        except Exception:
            pass
    else:
        # Bind operational evidence to the world this child actually uses.
        # los-fixture has no world yet; its construction I/O is scaffolding.
        _root_arg = os.environ.get("LOS_FX")
        if "--root" in sys.argv:
            _root_index = sys.argv.index("--root") + 1
            if _root_index < len(sys.argv):
                _root_arg = sys.argv[_root_index]
        _world_root = str(Path(_root_arg).resolve()) if _root_arg else None
        _state_dir = None
        _state_anchored = False
        if _world_root:
            import tempfile

            _anchor = Path(_world_root) / ".git"
            _git_dir = _anchor if _anchor.is_dir() else None
            if _anchor.is_file():
                try:
                    _git_text = _anchor.read_text().strip()
                    if _git_text.startswith("gitdir:"):
                        _candidate = Path(_git_text[7:].strip())
                        _git_dir = (_candidate if _candidate.is_absolute()
                                    else Path(_world_root) / _candidate)
                except OSError:
                    pass
            if _git_dir is not None and _git_dir.is_dir():
                _state_dir = str((_git_dir / "learningos").resolve())
                _state_anchored = True
            else:
                _state_dir = str(Path(tempfile.gettempdir()).resolve())
        _tx_dir = Path(_world_root) / "operations/transactions" if _world_root else None
        _receipts_before = sorted(p.name for p in _tx_dir.glob("transaction-*.yaml")) if _tx_dir else []

        # Step 3: the witness, only after install succeeded.
        _witness = {
            "event": "installed",
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "token": _token,
            "argv": list(sys.argv),
            "root": _world_root,
            "state_dir": _state_dir,
            "state_anchored": _state_anchored,
            "receipts_before": _receipts_before,
        }
        with open(_log, "a", encoding="utf-8") as _handle:
            _handle.write(json.dumps(_witness) + "\n")
        # Step 4: this process's own children get a distinct token.
        os.environ["LOS_ARCH_LAUNCH_TOKEN"] = (
            f"{_token or 'root'}/{os.getpid()}"
        )

        # Step 5: completion witness at exit.
        import atexit

        _me = os.getpid()
        _done = arch_audit_hook.capture_ok

        def _completed(
            _log_path=_log,
            _pid=_me,
            _launch_token=_token,
            _capture_ok=_done,
            _root=_world_root,
            _before=tuple(_receipts_before),
        ):
            _record = {
                "event": "completed",
                "pid": _pid,
                "token": _launch_token,
                "capture_ok": _capture_ok(),
            }
            try:
                # Retain real same-command receipt bytes before Scrut removes
                # its fixture. Existing receipts never establish ownership.
                _record["root"] = _root
                _record["new_receipts"] = []
                if _root:
                    import hashlib
                    for _path in sorted((Path(_root) / "operations/transactions").glob("transaction-*.yaml")):
                        if _path.name not in _before:
                            _raw = _path.read_bytes()
                            _record["new_receipts"].append({
                                "path": _path.name,
                                "sha256": hashlib.sha256(_raw).hexdigest(),
                                "text": _raw.decode("utf-8"),
                            })
                with open(_log_path, "a", encoding="utf-8") as _handle:
                    _handle.write(json.dumps(_record) + "\n")
            except Exception:
                pass

        atexit.register(_completed)
