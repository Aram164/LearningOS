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
SHARD_ACTION = ".github/actions/core-test-shard"
SHARD_ACTION_USES = {f"./repository/{SHARD_ACTION}", f"./ci-workflow/{SHARD_ACTION}"}

HEX40 = r"[0-9a-f]{40}"
FULL_SHA_RE = re.compile(rf"^{HEX40}$")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(doc: dict) -> dict:
    """The `on:` block, working around PyYAML (YAML 1.1) parsing the bare
    key `on` as the boolean `True` rather than the string "on"."""
    return doc.get("on", doc.get(True, {}))


def _job_steps(job: dict) -> list[dict]:
    """Include the shared shard action in the policy checks on its callers."""
    steps = []
    for step in job.get("steps", []):
        if step.get("uses") in SHARD_ACTION_USES:
            steps.extend(_load(ROOT / SHARD_ACTION / "action.yml")["runs"]["steps"])
        else:
            steps.append(step)
    return steps


def _all_run_steps(doc: dict) -> list[str]:
    steps = []
    for job in doc.get("jobs", {}).values():
        for step in _job_steps(job):
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
        "tools/check_shard_completeness.py --junit-dir ../junit-in",
    ):
        assert stage in runs, f"validate.yml lost gate stage: {stage}"
    # A lesser target must never stand in for the full gate.
    assert "make check\n" not in runs
    # Collection now belongs to the shared checker, invoked above. Its owning
    # tests exercise identity equality, including duplicate-plus-omission.
    checker = (ROOT / "tools/check_shard_completeness.py").read_text(encoding="utf-8")
    assert '"--collect-only"' in checker
    assert "--zero-skip-junit" in checker
    assert "not live_install" not in checker


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
    assert "tests/test_ui_phase3_live_writes.py" in makefile
    assert "live-writes-harness.js" in makefile
    assert "tests/test_operations_gate.py" in makefile
    assert "operations-gate-harness.js" in makefile


def test_workflows_clear_fallback_and_missing_core_overrides():
    for workflow in (VALIDATE, RELEASE_PAIR):
        env = _load(workflow).get("env", {})
        assert env.get("LEARNINGOS_ALLOW_FALLBACK") == "", workflow.name
        assert env.get("LEARNINGOS_ALLOW_MISSING_CORE") == "", workflow.name
        assert env.get("PYTEST_ADDOPTS") == "", workflow.name


def test_workflows_generate_full_scale_manifest_and_require_witness_prefixes():
    action_runs = "\n".join(
        step.get("run", "")
        for step in _load(ROOT / SHARD_ACTION / "action.yml")["runs"]["steps"]
        if "run" in step
    )
    assert ".venv/bin/python tools/generate.py" in action_runs
    assert "tests/test_contract_differential.py" in action_runs
    for workflow in (VALIDATE, RELEASE_PAIR):
        gate_runs = "\n".join(
            step.get("run", "")
            for step in _load(workflow)["jobs"]["gate"]["steps"]
            if "run" in step
        )
        for prefix in (
            "tests/test_ui_phase3_live_writes.py::",
            "tests/test_ui_gateway_recovery.py::",
            "tests/test_operations_gate.py::",
            "tests/test_contract_differential.py::",
        ):
            assert f"--require-passed-prefix {prefix}" in gate_runs, (
                workflow.name, prefix
            )


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
    """Steps that run one suite shard: pytest writing shard JUnit results."""
    return [step for job_id, job in doc.get("jobs", {}).items()
            if job_id != "seatbelt-macos"
            for step in _job_steps(job)
            if "-m pytest" in step.get("run", "")
            and "--junitxml" in step.get("run", "")]


def test_ci_runs_full_collected_suite_and_dynamic_ratchet_base():
    """Every shard leg runs the full collected suite with a dynamic base.

    No marker deselections (like the retired `live_install`) shrink coverage,
    and `LOS_RATCHET_BASE` is resolved dynamically rather than hardcoded to
    `origin/main` (which compares HEAD against HEAD on push/dispatch to main).
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        legs = _pytest_leg_steps(doc)
        assert legs, workflow.name
        for step in legs:
            env = step.get("env", {})
            assert "PYTEST_ADDOPTS" not in env, (workflow.name, step.get("name"))
            assert env.get("LOS_RATCHET_BASE") in {
                "${{ steps.ratchet.outputs.base }}", "${{ inputs.ratchet_base }}",
            }, (
                workflow.name, step.get("name"))
            assert set(env) == {"LOS_RATCHET_BASE", "SHARD", "PICKED"}, (
                workflow.name, sorted(env))
            assert "-k " not in step["run"], (
                workflow.name, step.get("name"),
                "a shard leg must not select tests itself")
        text = workflow.read_text(encoding="utf-8")
        assert "not live_install" not in text, workflow.name
        assert "LOS_RATCHET_BASE: origin/main" not in text, workflow.name


def test_both_workflows_run_the_same_core_shard_recipe_after_checkout():
    for workflow, recipe_checkout in ((VALIDATE, "repository"), (RELEASE_PAIR, "ci-workflow")):
        job = _load(workflow)["jobs"]["pytest-shards"]
        steps = job["steps"]
        calls = [step for step in steps if step.get("uses") in SHARD_ACTION_USES]
        assert len(calls) == 1
        call = calls[0]
        assert call["uses"] == f"./{recipe_checkout}/{SHARD_ACTION}"
        assert call["with"] == {
            "shard": "${{ matrix.shard }}",
            "ratchet_base": "${{ steps.ratchet.outputs.base }}",
        }
        setup = steps[:steps.index(call)]
        checkouts = {step["with"]["path"]: step["with"] for step in setup
                     if str(step.get("uses", "")).startswith("actions/checkout@")}
        assert {"repository", "obsidian-ui", recipe_checkout} <= checkouts.keys()
        assert any(step.get("id") == "ratchet" for step in setup)
        if workflow == RELEASE_PAIR:
            assert checkouts["repository"]["ref"] == "${{ steps.inputs.outputs.core_sha }}"
            assert checkouts["obsidian-ui"]["ref"] == "${{ steps.inputs.outputs.ui_sha }}"
            assert checkouts[recipe_checkout]["ref"] == "${{ github.workflow_sha }}"

        shard_steps = _pytest_leg_steps({"jobs": {"pytest-shards": job}})
        assert len(shard_steps) == 1
        assert shard_steps[0]["env"]["LOS_RATCHET_BASE"] == "${{ inputs.ratchet_base }}"
        assert shard_steps[0]["env"]["SHARD"] == "${{ inputs.shard }}"


def test_hosted_gates_run_macos_seatbelt_without_skips():
    """Both workflows verify Seatbelt sandboxing natively on Darwin with zero skips."""
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        jobs = doc.get("jobs", {})
        assert "seatbelt-macos" in jobs, workflow.name
        sb = jobs["seatbelt-macos"]
        assert sb.get("runs-on") == "macos-15", workflow.name
        runs = "\n".join(s.get("run", "") for s in sb.get("steps", []))
        assert "tests/test_study_launch.py" in runs, workflow.name
        assert "--junitxml=../seatbelt-out/seatbelt.xml" in runs, workflow.name
        assert "--zero-skip-junit ../seatbelt-out/seatbelt.xml" in runs, workflow.name
        gate = jobs["gate"]
        assert "seatbelt-macos" in gate.get("needs", []), workflow.name
        gate_runs = "\n".join(s.get("run", "") for s in gate.get("steps", []))
        assert "--zero-skip-junit ../seatbelt-in/seatbelt.xml" in gate_runs, workflow.name


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
    assert {"core_sha", "ui_sha"}.issubset(inputs)
    assert set(inputs) <= {"core_sha", "ui_sha", "core_ratchet_base"}
    assert inputs["core_sha"].get("required") is True
    assert inputs["ui_sha"].get("required") is True
    if "core_ratchet_base" in inputs:
        assert inputs["core_ratchet_base"].get("required") is False
    text = RELEASE_PAIR.read_text(encoding="utf-8")
    assert (
        text.count(
            "CORE_RATCHET_BASE_INPUT: ${{ github.event.inputs.core_ratchet_base }}"
        )
        == 2
    )


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
        assert _pytest_leg_steps(doc), workflow.name
        for name, job in doc["jobs"].items():
            if name == "seatbelt-macos":
                continue
            steps = _job_steps(job)
            job_legs = [index for index, step in enumerate(steps)
                        if "-m pytest" in step.get("run", "")
                        and "--junitxml" in step.get("run", "")]
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
            setups = [step for step in _job_steps(job)
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
            installs = [step for step in _job_steps(job)
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


#: The one shard manifest (C3-F): both workflows load this file, and the
#: tests below read the same one — never a second copy that could drift.
SHARD_MANIFEST_PATH = ROOT / ".github" / "shard-manifest.json"


def _shard_manifest() -> dict:
    return json.loads(SHARD_MANIFEST_PATH.read_text(encoding="utf-8"))


def _matrix_legs(job: dict) -> list:
    return job.get("strategy", {}).get("matrix", {}).get("shard", [])


def _jobs_by_leg(doc: dict) -> dict[str, str]:
    """leg id -> the id of the job whose matrix carries it."""
    carriers: dict[str, str] = {}
    for job_id, job in doc.get("jobs", {}).items():
        for leg_id in _matrix_legs(job):
            assert leg_id not in carriers, (
                f"leg {leg_id!r} appears in more than one job matrix")
            carriers[leg_id] = job_id
    return carriers


def test_both_workflows_read_the_one_shard_manifest():
    """The shard manifest is a file both workflows load, never a paste.

    The partition used to live as a pasted env block in each workflow;
    two copies could drift apart. Both CI jobs and these tests now read
    the same file, and no workflow may resurrect the env copy.
    """
    for workflow in (VALIDATE, RELEASE_PAIR):
        runs = "\n".join(_all_run_steps(_load(workflow)))
        assert ".github/shard-manifest.json" in runs, (
            f"{workflow.name} no longer reads .github/shard-manifest.json")
        assert "SHARD_MANIFEST" not in workflow.read_text(encoding="utf-8"), (
            f"{workflow.name} still mentions SHARD_MANIFEST — the pasted "
            "manifest copy was removed so one file is the whole truth")


def test_shard_manifest_partitions_the_suite():
    """CI's shards are exactly the suite: a partition of tests/test_*.py.

    A file missing from the manifest would never run in CI; a file in
    more legs than its node_shards count would run twice and double-count
    in the gate's completeness proof; a node-shared file whose carrier
    legs disagree with its node_shards legs would run some tests twice
    and others never. Which leg a file rides no longer constrains the
    witness population (C3-F): every suite leg uploads its session
    witness file, sidecar and audit dir, and the zz legs merge all of
    them, so a witness-writing test is asserted over wherever it runs —
    the hand-kept list of witness-producer files is gone by design.
    """
    from collections import Counter

    manifest = _shard_manifest()
    legs = manifest["legs"]
    node_shards = manifest.get("node_shards", {})
    disk = sorted(f"tests/{p.name}"
                  for p in (ROOT / "tests").glob("test_*.py"))
    covered = Counter(f for leg in legs.values() for f in leg)
    for name, count in sorted(covered.items()):
        expected = node_shards.get(name, {}).get("count", 1)
        assert count == expected, (
            f"{name} appears in {count} legs, expected {expected}")
    assert sorted(covered) == disk, (
        f"{SHARD_MANIFEST_PATH.name} does not partition tests/: "
        f"missing={sorted(set(disk) - set(covered))} "
        f"extra={sorted(set(covered) - set(disk))}")
    for name, spec in sorted(node_shards.items()):
        carriers = sorted(leg_id for leg_id, leg in legs.items()
                          if name in leg)
        assert carriers == sorted(spec["legs"]), (
            f"node-shared {name} carried by {carriers}, "
            f"node_shards names {sorted(spec['legs'])}")


def test_workflow_matrices_and_population_flow_match_the_manifest():
    """Matrices, artifact flow and merge order follow the manifest.

    The suite phase runs one matrix job over the non-zz legs and the
    population phase another over the zz legs; a leg in the manifest but
    no matrix never runs, and a matrix leg missing from the manifest
    fails its pick step mid-run — both pinned here locally instead of
    30 minutes into CI. Every suite leg uploads its population artifact
    unconditionally (a shard-name condition is exactly the hand-kept
    producer list C3-F removed), the upload names the session fixtures'
    own basetemp locations (a broad basetemp glob would sweep private
    witness files some tests create under their per-test tmp dirs into
    the population), the zz job downloads and merges all of them, and it
    runs only after the suite job — otherwise the merge would race the
    producers and assert over a partial population.
    """
    manifest = _shard_manifest()
    all_legs = set(manifest["legs"])
    zz_legs = {leg for leg in all_legs if leg.startswith("zz-")}
    suite_legs = all_legs - zz_legs
    for workflow in (VALIDATE, RELEASE_PAIR):
        doc = _load(workflow)
        carriers = _jobs_by_leg(doc)
        assert set(carriers) == all_legs, (
            f"{workflow.name}: matrix legs {sorted(carriers)} != manifest "
            f"legs {sorted(all_legs)}")
        suite_jobs = {carriers[leg] for leg in suite_legs}
        zz_jobs = {carriers[leg] for leg in zz_legs}
        assert len(suite_jobs) == 1, (
            f"{workflow.name}: suite legs split over jobs {sorted(suite_jobs)}")
        assert len(zz_jobs) == 1, (
            f"{workflow.name}: zz legs split over jobs {sorted(zz_jobs)}")
        suite_job_id = next(iter(suite_jobs))
        zz_job_id = next(iter(zz_jobs))
        suite_job = doc["jobs"][suite_job_id]
        zz_job = doc["jobs"][zz_job_id]

        assert suite_job_id in zz_job.get("needs", []), (
            f"{workflow.name}: zz job {zz_job_id!r} must run after the "
            f"suite job {suite_job_id!r}")

        uploads = [step for step in _job_steps(suite_job)
                   if str(step.get("uses", "")).startswith(
                       "actions/upload-artifact")
                   and step.get("with", {}).get("name")
                   == "population-${{ inputs.shard }}"]
        assert len(uploads) == 1, (
            f"{workflow.name}: expected exactly one population upload "
            "step, run by every suite leg")
        assert uploads[0].get("if") == "always()", (
            f"{workflow.name}: the population upload must run even when "
            "the leg's tests fail, and must not filter legs by name")
        assert uploads[0].get("with", {}).get(
                "follow-symbolic-links") is False, (
            f"{workflow.name}: the population upload must declare that it "
            "never follows symlinks. The upload materializes pytest's "
            "<name>current aliases beside the session dirs anyway, so the "
            "merge's byte-identical dedupe is the load-bearing half — "
            "this pin keeps the two halves from drifting apart")
        paths = str(uploads[0].get("with", {}).get("path", ""))
        assert "pytesttmp/site-witness*/sites.jsonl" in paths, (
            f"{workflow.name}: the population upload must name the session "
            "witness file's own location, never a broad basetemp glob")

        downloads = [step for step in zz_job.get("steps", [])
                     if str(step.get("uses", "")).startswith(
                         "actions/download-artifact")
                     and step.get("with", {}).get("pattern") == "population-*"]
        assert len(downloads) == 1, (
            f"{workflow.name}: expected exactly one population download "
            "step, taking every suite leg's artifact")
