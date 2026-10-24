"""Workflow-policy tests for the release-hardening plan's paired CI (Phase 8/9).

No Core workflow test file existed before this plan. These read the checked-in
YAML as text and structure — they never dispatch a real workflow run, which is
what Phase 12/13's live push-and-watch steps are for.
"""

from __future__ import annotations

import json
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


def test_ordinary_ci_runs_every_gate_stage():
    """The sharded gate runs every stage the local `make system-check` runs.

    The suite is split over shard jobs (see the manifest partition test
    below); the static gates and the paired UI check stay whole. This pins
    the stage list so a shard redesign cannot quietly drop one: ruff and
    reachability, mypy, validate, the warning baseline, the complete UI
    `npm run check`, and the collection-vs-shards completeness proof.
    """
    runs = "\n".join(_all_run_steps(_load(VALIDATE)))
    for stage in (
        "ruff check tools tests",
        "tools/code_reachability.py",
        "-m mypy",
        "tools/validate.py --no-report",
        "tools/warning_baseline.py --check",
        "npm run check",
        "--collect-only",
    ):
        assert stage in runs, f"validate.yml lost gate stage: {stage}"
    # A lesser target must never stand in for the full gate.
    assert "make check\n" not in runs


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


def _pytest_leg_steps(doc: dict) -> list[dict]:
    """Steps that run one suite shard: pytest writing JUnit results."""
    return [step for job in doc.get("jobs", {}).values()
            for step in job.get("steps", [])
            if "-m pytest" in step.get("run", "")
            and "--junitxml" in step.get("run", "")]


def test_ci_deselects_only_live_installation_tests():
    """Every suite shard drops exactly the `live_install` marker.

    Those tests need state no checkout carries. Anything broader — `not
    full_repo`, a `-k` filter, a second marker — would quietly shrink what
    a green run proves, so the selection is pinned exactly per shard; the
    gate job's completeness proof re-derives the expected total from a
    fresh full collection carrying the same deselection, so a shard that
    selected less would fail that proof, not pass silently.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        legs = _pytest_leg_steps(_load(workflow))
        assert legs, workflow.name
        for step in legs:
            env = step.get("env", {})
            assert env.get("PYTEST_ADDOPTS") == '-m "not live_install"', (
                workflow.name, step.get("name"))
            assert set(env) <= {"PYTEST_ADDOPTS", "LOS_RATCHET_BASE",
                                "SHARD", "PICKED"}, (workflow.name, sorted(env))
            assert "-k " not in step["run"], (
                workflow.name, step.get("name"),
                "a shard leg must not select tests itself")


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

    Without Scrut, ``tests/test_procedures.py`` fails inside its shard;
    each workflow therefore installs the pinned archive, checks its digest,
    and hands the binary to the shard through ``$GITHUB_ENV`` before any
    suite-shard step runs.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        legs = _pytest_leg_steps(doc)
        assert legs, workflow.name
        leg_scripts = {id(step) for step in legs}
        for job in doc["jobs"].values():
            steps = job.get("steps", [])
            job_legs = [index for index, step in enumerate(steps)
                        if id(step) in leg_scripts]
            if not job_legs:
                continue
            installs = [index for index, step in enumerate(steps)
                        if SCRUT_ARCHIVE in step.get("run", "")]
            assert len(installs) == 1 and installs[0] < job_legs[0], (
                workflow.name)
            script = steps[installs[0]]["run"]
            assert f"{SCRUT_SHA256}  " in script, workflow.name
            assert "sha256sum -c -" in script, workflow.name
            assert 'LOS_SCRUT_BIN=$bin" >> "$GITHUB_ENV"' in script, (
                workflow.name)


def test_setup_installs_the_same_pinned_scrut():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert '$(MAKE) scrut' in makefile
    assert SCRUT_SHA256 in makefile


# ---- landing environment repair (SPEC (bm)) -------------------------------

#: The interpreter patch the accepted campaign verified (SPEC (bm)).
PINNED_PYTHON = "3.14.4"


def test_ci_pins_the_verified_interpreter_patch():
    """Every Python job installs exactly the interpreter the campaign
    verified, at most one setup per job.

    Argparse renders invalid-choice diagnostics differently across patches
    (landing CI on 3.14.8 quoted the choice the 3.14.4 recordings leave
    bare); the recordings pin one rendering, so every job that runs the
    suite or the tools must not silently select a new patch.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        text = workflow.read_text(encoding="utf-8")
        any_setup = False
        for name, job in doc["jobs"].items():
            setups = [step for step in job.get("steps", [])
                      if str(step.get("uses", "")).startswith(
                          "actions/setup-python@")]
            assert len(setups) <= 1, (workflow.name, name)
            for step in setups:
                assert step["with"]["python-version"] == PINNED_PYTHON, (
                    workflow.name, name)
                any_setup = True
        assert any_setup, workflow.name
        assert not re.search(r'python-version:\s*"3\.14"', text), workflow.name


def test_ci_installs_core_dependencies_into_the_project_venv():
    """Every CI job's dependency install reproduces the documented project
    environment, one per job.

    Parser diagnostics are characterized bytes pinned to the 3.14.4
    interpreter, and the procedure transcripts invoke
    ``$LOS_REPO/.venv/bin/python`` — so each job that needs Python builds
    that venv with the pinned interpreter and installs into it, never into
    the runner's interpreter. Every other Core Python invocation in CI then
    uses the venv that owns the install.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        for job in doc["jobs"].values():
            installs = [step for step in job.get("steps", [])
                        if step.get("name") == "Install Core development dependencies"]
            assert len(installs) <= 1, workflow.name
            for install in installs:
                script = install["run"]
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


def test_every_job_carries_a_bounded_timeout():
    """Every job declares a finite timeout of at most 45 minutes.

    The unsharded gate needed 180 minutes of pytest alone; the sharded
    gate's whole point (C3, 2026-10-24) is that no leg — and no join job —
    may run past the 40-minute target plus margin. A job without a bound
    can queue forever; a job above 45 minutes means the shard balance has
    rotted and must be regenerated from fresh CI durations.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        for name, job in _load(workflow)["jobs"].items():
            timeout = job.get("timeout-minutes")
            assert isinstance(timeout, int) and timeout <= 45, (
                workflow.name, name)


def _shard_manifest(path: Path) -> dict:
    doc = _load(path)
    raw = doc.get("env", {}).get("SHARD_MANIFEST")
    assert raw, f"{path.name}: SHARD_MANIFEST env is missing"
    return json.loads(raw)


#: The files whose witness and audit population the two zz files assert
#: over. Their session-artifact writers (tests/conftest.py's fixtures,
#: scenario_harness's case runs, the procedure runner) live in witness-*
#: CI legs; the assertions themselves live in zz-* legs over the merged
#: artifacts (conftest premerged mode). Every other suite file that
#: touches the witness machinery uses private files it creates itself.
WITNESS_BLOCK = frozenset({
    "test_procedures.py",
    "test_scenarios.py",
    "test_scenarios_effects.py",
    "test_scenarios_health_shim.py",
    "test_scenarios_recovery.py",
    "test_scenarios_session.py",
    "test_scenarios_zz_operational_owners.py",
    "test_scenarios_zz_refusal_sites.py",
})


def test_shard_manifest_partitions_the_suite():
    """CI's shards are exactly the suite: a partition of tests/test_*.py.

    A file missing from the manifest would never run in CI; a file in
    more legs than its node_shards count would run twice and double-count
    in the gate's completeness proof; a node-shared file whose carrier
    legs disagree with its node_shards legs would run some tests twice
    and others never. Witness-block files may only ride witness-*/zz-*
    legs: witness legs upload the session population, zz legs merge it
    (tests/conftest.py premerged mode rebuilds A9's process-local
    attribution from the sidecars) and assert over it — a witness file
    in any other leg would be silently unasserted, and A9/A19's
    population checks would see a partial suite (SPEC §3.3 A9, §3.6 A19).
    """
    from collections import Counter

    disk = sorted(f"tests/{p.name}"
                  for p in (ROOT / "tests").glob("test_*.py"))
    for workflow in (VALIDATE, RELEASE_PAIR):
        manifest = _shard_manifest(workflow)
        legs = manifest["legs"]
        node_shards = manifest.get("node_shards", {})
        covered = Counter(f for leg in legs.values() for f in leg)
        for name, count in sorted(covered.items()):
            expected = node_shards.get(name, {}).get("count", 1)
            assert count == expected, (
                f"{workflow.name}: {name} appears in {count} legs, "
                f"expected {expected}")
        assert sorted(covered) == disk, (
            f"{workflow.name}: SHARD_MANIFEST does not partition tests/: "
            f"missing={sorted(set(disk) - set(covered))} "
            f"extra={sorted(set(covered) - set(disk))}")
        for name, spec in sorted(node_shards.items()):
            carriers = sorted(leg_id for leg_id, leg in legs.items()
                              if name in leg)
            assert carriers == sorted(spec["legs"]), (
                f"{workflow.name}: node-shared {name} carried by "
                f"{carriers}, node_shards names {sorted(spec['legs'])}")
        for leg_id, leg in legs.items():
            for name in leg:
                if name.rsplit("/", 1)[-1] in WITNESS_BLOCK:
                    assert leg_id.startswith(("witness-", "zz-")), (
                        f"{workflow.name}: witness-block file {name} in "
                        f"non-witness leg {leg_id!r}")


def test_zz_legs_run_after_the_witness_legs():
    """The zz legs' job depends on the job that runs the witness legs.

    The zz population files assert over the merged witness artifacts of
    the producer legs; if they ever ran beside them instead of after
    them, the merge would race the producers and the population checks
    would assert over a partial suite or nothing.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        legs = _shard_manifest(workflow)["legs"]
        carrier_jobs = {}
        for job_id, job in doc["jobs"].items():
            matrix = job.get("strategy", {}).get("matrix", {}).get("shard", [])
            for leg_id in matrix:
                carrier_jobs[leg_id] = job_id
        witness_jobs = {carrier_jobs[leg_id]
                        for leg_id in legs if leg_id.startswith("witness-")}
        for leg_id in legs:
            if leg_id.startswith("zz-"):
                needs = set(doc["jobs"][carrier_jobs[leg_id]].get("needs", []))
                assert needs & witness_jobs, (
                    f"{workflow.name}: zz leg {leg_id!r} does not depend on "
                    f"a witness-leg job ({sorted(witness_jobs)})")
