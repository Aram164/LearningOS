"""The FLOWS.md sibling-commit pin must stay reachable in the UI checkout.

FLOWS.md pins the UI boundary trace to a specific sibling commit, and before
2026-11-05 nothing read that pin: a rewritten or garbage-collected sibling
history could silently strand the trace with every Core gate green (the
symbol-checked-not-behavior-checked gap). This test makes the pin
load-bearing: it must name a commit the sibling checkout actually contains,
and one that is an ancestor of (or equal to) its HEAD — a fast-forward keeps
the pin true, while a rebase that drops the traced commit fails here loudly.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

CORE_ROOT = Path(__file__).resolve().parent.parent
UI_ROOT = CORE_ROOT.parent / "obsidian-ui"
FLOWS = CORE_ROOT / "system" / "developer" / "FLOWS.md"

#: Repository routing Git exports to hooks. Each call below names its
#: repository with ``-C``; an inherited GIT_DIR would override that and read
#: Core's index and HEAD for the UI (verified_pairs.GIT_ROUTING, #24).
GIT_ROUTING = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
               "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
               "GIT_NAMESPACE", "GIT_PREFIX")


def _git(repo: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=30,
            env={key: value for key, value in os.environ.items()
                 if key not in GIT_ROUTING},
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


@pytest.mark.paired
def test_flows_ui_pin_is_reachable_in_the_sibling_checkout():
    if not UI_ROOT.is_dir():
        pytest.skip("no sibling obsidian-ui checkout")
    pins = re.findall(r"at\s+UI\s+`([0-9a-f]{7,40})`",
                      FLOWS.read_text(encoding="utf-8"))
    assert pins, "FLOWS.md no longer names a pinned UI commit — update this test"
    for pin in pins:
        kind = _git(UI_ROOT, "cat-file", "-t", pin)
        assert kind in ("commit", "tag"), (
            f"FLOWS.md pins UI {pin}, which the sibling checkout does not "
            f"contain — re-trace the boundary and re-pin (FLOWS.md)")
        # --is-ancestor prints nothing: success is the empty string, failure
        # (including an unreachable commit) is None.
        assert _git(UI_ROOT, "merge-base", "--is-ancestor", pin, "HEAD") is not None, (
            f"FLOWS.md pins UI {pin}, which is not an ancestor of the sibling "
            f"HEAD — the traced commit left the UI history; re-trace and re-pin")
