"""Workflow-policy tests for the release-hardening plan's paired CI (Phase 8/9).

No Core workflow test file existed before this plan. These read the checked-in
YAML as text and structure — they never dispatch a real workflow run, which is
what Phase 12/13's live push-and-watch steps are for.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
VALIDATE = WORKFLOWS / "validate.yml"
RELEASE_PAIR = WORKFLOWS / "release-pair.yml"

HEX40 = r"[0-9a-f]{40}"
FULL_SHA_RE = re.compile(rf"^{HEX40}$")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(doc: dict) -> dict:
    """The `on:` block, working around PyYAML (YAML 1.1) parsing the bare
    key `on` as the boolean `True` rather than the string "on"."""
    return doc.get("on", doc.get(True, {}))


def _all_run_steps(doc: dict) -> list[str]:
    steps = []
    for job in doc.get("jobs", {}).values():
        for step in job.get("steps", []):
            if "run" in step:
                steps.append(step["run"])
    return steps


# ---- ordinary Core CI (validate.yml) ---------------------------------------

def test_validate_workflow_is_readable_yaml():
    assert _load(VALIDATE)["name"] == "validate"


def test_ordinary_ci_installs_both_dependency_sets():
    runs = "\n".join(_all_run_steps(_load(VALIDATE)))
    assert re.search(r"pip install", runs)
    assert "npm ci" in runs


def test_ordinary_ci_invokes_the_real_system_check():
    runs = "\n".join(_all_run_steps(_load(VALIDATE)))
    assert re.search(r"\bmake system-check\b", runs), (
        "ordinary CI must run the exact local paired gate, not a partial duplicate"
    )
    # A lesser target must never stand in for it — `make check` alone skips
    # the mandatory paired recovery harness and the UI's own npm run check.
    assert "make check\n" not in runs.replace("make system-check", "")


def test_ordinary_ci_cannot_silently_omit_the_recovery_harness():
    """`make system-check` itself refuses to run without the harness present
    (see tests/test_ui_gateway_recovery.py::test_the_paired_gate_requires_this_harness).
    This test pins the other half of that guarantee: CI must actually invoke
    the target that enforces it, which the previous test already established —
    this additionally proves the Makefile's own enforcement text still exists,
    so a change to system-check cannot quietly drop the check without also
    changing text this test reads.
    """
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "tests/test_ui_gateway_recovery.py" in makefile
    assert "gateway-recovery-harness.js" in makefile


def test_ordinary_ci_permissions_are_read_only():
    doc = _load(VALIDATE)
    assert doc.get("permissions") == {"contents": "read"}


def test_ordinary_ci_does_not_claim_immutable_pairing():
    """Branch-based CI is useful but mutable — it must never look like the
    exact-pair guarantee release-pair.yml exists to provide.
    """
    text = VALIDATE.read_text(encoding="utf-8")
    # No literal 40-character commit SHA is pinned anywhere in the ordinary
    # workflow; the UI side is always resolved by branch name at run time.
    assert not re.search(rf"\b{HEX40}\b", text.lower()), (
        "ordinary CI must resolve the UI by branch, never by a pinned commit"
    )
    assert "workflow_dispatch" in text  # still triggerable, not release-only
    assert "consumer-ref" in text  # the same-branch-or-main resolution step


def test_ordinary_ci_does_not_run_full_stress():
    """The checkout provisions neither repository's external materials tree,
    so `make stress` (which includes the online/production/fuzz sweep) has no
    place in ordinary CI — only the scheduled, separate online audit does.
    """
    runs = "\n".join(_all_run_steps(_load(VALIDATE)))
    assert "make stress" not in runs
    assert "stress_check.py" not in runs


# ---- immutable exact-pair CI (release-pair.yml) ----------------------------

def test_release_pair_workflow_declares_exact_sha_inputs():
    inputs = _triggers(_load(RELEASE_PAIR))["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"core_sha", "ui_sha"}
    assert all(spec.get("required") for spec in inputs.values())


def test_release_pair_workflow_validates_and_uses_full_sha_format():
    text = RELEASE_PAIR.read_text(encoding="utf-8")
    # The format check itself is anchored to exactly 40 lowercase hex chars —
    # a 12-character short SHA or an uppercase one must not slip past it.
    assert re.search(r"\^\[0-9a-f\]\{40\}\$", text)
    assert "core_sha" in text and "ui_sha" in text


def test_release_pair_workflow_is_manual_only_and_read_only():
    doc = _load(RELEASE_PAIR)
    assert set(_triggers(doc)) == {"workflow_dispatch"}, (
        "the exact-pair workflow must never trigger on push/pull_request/schedule"
    )
    assert doc.get("permissions") == {"contents": "read"}
