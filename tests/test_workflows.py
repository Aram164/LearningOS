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


def test_ci_deselects_only_live_installation_tests():
    """Both workflows drop exactly the `live_install` marker from the gate.

    Those tests need state no checkout carries. Anything broader — `not
    full_repo`, a `-k` filter, a second marker — would quietly shrink what a
    green run proves, so the selection is pinned exactly. The gate step may
    also carry `LOS_RATCHET_BASE` (SPEC §2.3), which selects no tests.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        gates = [step for job in _load(workflow)["jobs"].values()
                 for step in job["steps"]
                 if "make system-check" in step.get("run", "")]
        assert len(gates) == 1, workflow.name
        env = gates[0].get("env", {})
        assert env.get("PYTEST_ADDOPTS") == '-m "not live_install"', workflow.name
        assert set(env) <= {"PYTEST_ADDOPTS", "LOS_RATCHET_BASE"}, (
            workflow.name, sorted(env))


def test_workflow_run_scripts_never_interpolate_github_expressions():
    """Expressions are data, not shell source; steps receive them through env."""
    for workflow in (VALIDATE, RELEASE_PAIR):
        for script in _all_run_steps(_load(workflow)):
            assert "${{" not in script, (
                f"{workflow.name} interpolates a GitHub expression into run-shell code"
            )


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
    assert 'echo "core_sha=$core_sha" >> "$GITHUB_OUTPUT"' in text
    assert 'echo "ui_sha=$ui_sha" >> "$GITHUB_OUTPUT"' in text
    assert "ref: ${{ steps.inputs.outputs.core_sha }}" in text
    assert "ref: ${{ steps.inputs.outputs.ui_sha }}" in text


def test_release_pair_workflow_is_manual_only_and_read_only():
    doc = _load(RELEASE_PAIR)
    assert set(_triggers(doc)) == {"workflow_dispatch"}, (
        "the exact-pair workflow must never trigger on push/pull_request/schedule"
    )
    assert doc.get("permissions") == {"contents": "read"}


#: The Linux Scrut archive CI installs, and its GitHub-published SHA-256.
SCRUT_ARCHIVE = "scrut-v0.5.0-linux-x86_64.tar.gz"
SCRUT_SHA256 = "5c373d077a73dc4a5d4b43f3474e0f443dc72fb42f89b312ef55f934e6e6ba15"


def test_ci_installs_the_pinned_scrut_before_the_gate():
    """The transcript gate (PLAN D11) cannot silently lose its binary in CI.

    Without Scrut, ``tests/test_procedures.py`` fails inside the paired gate;
    each workflow therefore installs the pinned archive, checks its digest,
    and hands the binary to the gate through ``$GITHUB_ENV``.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        for job in _load(workflow)["jobs"].values():
            steps = job.get("steps", [])
            gates = [index for index, step in enumerate(steps)
                     if re.search(r"\bmake system-check\b", step.get("run", ""))]
            if not gates:
                continue
            installs = [index for index, step in enumerate(steps)
                        if SCRUT_ARCHIVE in step.get("run", "")]
            assert len(installs) == 1 and installs[0] < gates[0], workflow.name
            script = steps[installs[0]]["run"]
            assert f"{SCRUT_SHA256}  " in script, workflow.name
            assert "sha256sum -c -" in script, workflow.name
            assert 'LOS_SCRUT_BIN=$bin" >> "$GITHUB_ENV"' in script, workflow.name


def test_setup_installs_the_same_pinned_scrut():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert '$(MAKE) scrut' in makefile
    assert SCRUT_SHA256 in makefile


# ---- landing environment repair (SPEC (bm)) -------------------------------

#: The interpreter patch the accepted campaign verified (SPEC (bm)).
PINNED_PYTHON = "3.14.4"


def test_ci_pins_the_verified_interpreter_patch():
    """Both workflows install exactly the interpreter the campaign verified.

    Argparse renders invalid-choice diagnostics differently across patches
    (landing CI on 3.14.8 quoted the choice the 3.14.4 recordings leave
    bare); the recordings pin one rendering, so CI must not silently select
    a new patch.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        setups = [step for job in _load(workflow)["jobs"].values()
                  for step in job["steps"]
                  if str(step.get("uses", "")).startswith("actions/setup-python@")]
        assert len(setups) == 1, workflow.name
        assert setups[0]["with"]["python-version"] == PINNED_PYTHON, workflow.name
        text = workflow.read_text(encoding="utf-8")
        assert len(re.findall(r'python-version:\s*"3\.14\.4"', text)) == 1, (
            workflow.name)
        assert not re.search(r'python-version:\s*"3\.14"', text), workflow.name


def test_ci_installs_core_dependencies_into_the_project_venv():
    """The dependency install reproduces the documented project environment.

    Parser diagnostics are characterized bytes pinned to the 3.14.4
    interpreter, and the procedure transcripts invoke
    ``$LOS_REPO/.venv/bin/python`` — so CI builds that venv with the pinned
    interpreter and installs into it, never into the runner's interpreter.
    Every other Core Python invocation in CI then uses the venv that owns
    the install; the gate itself resolves it through the Makefile.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        installs = [step for job in doc["jobs"].values()
                    for step in job["steps"]
                    if step.get("name") == "Install Core development dependencies"]
        assert len(installs) == 1, workflow.name
        script = installs[0]["run"]
        venv_at = script.find("python -m venv .venv")
        assert venv_at >= 0, workflow.name
        pip_at = script.find('.venv/bin/python -m pip install -e ".[dev]"')
        assert pip_at > venv_at, workflow.name
        for script in _all_run_steps(doc):
            for line in script.splitlines():
                if "pip install" in line:
                    assert ".venv/bin/python -m pip install" in line, (
                        workflow.name, line)
                if re.search(r"(^|\s)python[\d.]*\s+tools/", line):
                    assert ".venv/bin/python" in line, (workflow.name, line)


def test_paired_gate_jobs_carry_the_90_minute_bound():
    """Every job running the paired gate allows it exactly 90 minutes.

    The observed landing gate took 42:51; an unbounded job hides a hang and
    a shorter cap cancels the suite mid-run.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        found = False
        for name, job in _load(workflow)["jobs"].items():
            if any("make system-check" in step.get("run", "")
                   for step in job.get("steps", [])):
                found = True
                assert job.get("timeout-minutes") == 90, (workflow.name, name)
        assert found, workflow.name
