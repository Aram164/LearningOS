"""Child-process audit hook entry (SPEC §3.2c)."""
import json
import os
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_tests = _here.parent
if str(_tests) not in sys.path:
    sys.path.insert(0, str(_tests))

_log = os.environ.get("LOS_ARCH_AUDIT_LOG")
if _log:
    _witness = {"event": "installed", "pid": os.getpid(), "argv": list(sys.argv)}
    with open(_log, "a", encoding="utf-8") as _handle:
        _handle.write(json.dumps(_witness) + "\n")
    import arch_audit_hook

    arch_audit_hook.install(_log)
