"""Offline/online validation as application data, shared by CLI and session close."""
from pathlib import Path

from learning_os.derive.validation import render_report, validate
from learning_os.store import observations
from learning_os.store.fingerprint import seed_source_fingerprint
from learning_os.store.fs import atomic_text
from learning_os.store.loader import load_repo
from learning_os.store.validation_cache import (
    discard_unreadable_cache,
    observe_pins,
    write_static_cache,
)


def validation_run(root: Path, *, online: bool = False) -> dict:
    pins = None
    if not online:
        discard_unreadable_cache(root)
        pins = observe_pins(root)
    repo = load_repo(root)
    if pins is not None:
        seed_source_fingerprint(repo, f"sha256:{pins['canonical_fingerprint']}")
    issues = validate(repo, online=online)
    atomic_text(root / "generated/reports/validation-report.md",
                render_report(issues, observations.now().isoformat(timespec="seconds")))
    if pins is not None:
        try:
            write_static_cache(root, issues, pins)
        except OSError:
            pass
    return {"errors": sum(i.severity == "E" for i in issues),
            "warnings": sum(i.severity == "W" for i in issues),
            "issues": list(map(str, issues))}
