"""The ref-aware pre-push gate and its verified-pair memo (#106, #113).

A scripted Core/UI fixture pair (real git, real hook, stubbed `make`/`npm`)
proves: deletions skip the gate, non-main refs run the lighter local gate,
main keeps the full `system-check`, an exact stamped pair skips with the
stamp named, and any new commit or dirty tree re-runs the gate. Since #113
the gate also refuses pushed SHAs that are not the checkout, diffs review
pushes against the last stamped pair, deselects live_install outside the
live root, and runs only the UI check plus the paired-contract tests when
Core is unchanged.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ZERO_SHA = "0" * 40
#: A well-formed SHA that is never the fixture's HEAD (the refusal tests').
HEAD_SHA = "1" * 40


@pytest.fixture()
def pair(tmp_path: Path, monkeypatch):
    """A `repository` + `obsidian-ui` fixture pair with the real hook."""
    root = tmp_path / "pair"
    core = root / "repository"
    ui = root / "obsidian-ui"
    for repo in (core, ui):
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"],
                       cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Tests"], cwd=repo, check=True)
        subprocess.run(["git", "config", "commit.gpgsign", "false"],
                       cwd=repo, check=True)
    (core / "core.txt").write_text("core\n", encoding="utf-8")
    (ui / "ui.txt").write_text("ui\n", encoding="utf-8")
    # The canonical gate, memo, and live-root detector under test, verbatim.
    (core / "tools" / "hooks").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "tools" / "hooks" / "pre-push",
                core / "tools" / "hooks" / "pre-push")
    shutil.copy(REPO_ROOT / "tools" / "verified_pairs.py",
                core / "tools" / "verified_pairs.py")
    (core / "tools" / "learning_os" / "contracts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "tools" / "learning_os" / "contracts" / "perimeter.py",
                core / "tools" / "learning_os" / "contracts" / "perimeter.py")
    (core / "system" / "contracts").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "system" / "contracts" / "perimeter.yaml",
                core / "system" / "contracts" / "perimeter.yaml")
    # Deterministic interpreter for the hook's memo lookup.
    venv_bin = core / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_bin.joinpath("python").symlink_to(Path(sys.executable))
    subprocess.run(["git", "add", "-A"], cwd=core, check=True)
    subprocess.run(["git", "commit", "-qm", "core baseline"], cwd=core, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ui, check=True)
    subprocess.run(["git", "commit", "-qm", "ui baseline"], cwd=ui, check=True)
    # Installed copies, as `make hooks` leaves them.
    for repo in (core, ui):
        shutil.copy(core / "tools" / "hooks" / "pre-push",
                    repo / ".git" / "hooks" / "pre-push")

    log = tmp_path / "gate.log"
    log.write_text("", encoding="utf-8")
    env_log = tmp_path / "gate-env.log"
    env_log.write_text("", encoding="utf-8")
    stub_bin = tmp_path / "stub-bin"
    stub_bin.mkdir()
    for name in ("make", "npm"):
        stub = stub_bin / name
        stub.write_text(
            f'#!/bin/sh\necho "{name} $*" >> "$GATE_LOG"\n'
            'echo "PYTEST_ADDOPTS=${PYTEST_ADDOPTS:-<unset>}" >> "$GATE_ENV_LOG"\n',
            encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("GATE_LOG", str(log))
    monkeypatch.setenv("GATE_ENV_LOG", str(env_log))
    monkeypatch.setenv("PATH", str(stub_bin) + os.pathsep + os.environ["PATH"])
    # The hook inherits this from the runner; the deselection tests set it
    # explicitly, and every other test needs the unset deterministic path.
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    # The fixture python is a symlink, which does not activate the venv, so
    # the hook's live-root detector (which needs PyYAML) runs with the
    # runner's own site-packages on the path instead.
    monkeypatch.setenv("PYTHONPATH", sysconfig.get_paths()["purelib"])
    return {"root": root, "core": core, "ui": ui, "log": log, "env_log": env_log}


def _run_hook(repo: Path, stdin: str):
    hook = repo / ".git" / "hooks" / "pre-push"
    return subprocess.run([str(hook)], cwd=repo, input=stdin,
                          capture_output=True, text=True, timeout=120)


def _invocations(log: Path) -> list[str]:
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


def _head(repo: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True, check=True, timeout=60)
    return proc.stdout.strip()


def _commit(repo: Path, name: str, message: str) -> str:
    (repo / name).write_text("new\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=repo, check=True)
    return _head(repo)


def _stamp(core: Path):
    # The hook resolves its interpreter to the Core venv; the stamp must be
    # taken under that same interpreter, exactly as `make system-check` does
    # with $(PY) in a real checkout. (A symlinked python does not activate a
    # venv, so stamping here with the test runner's own binary would record a
    # different toolchain than the hook's lookup computes.)
    return subprocess.run(
        [str(core / ".venv" / "bin" / "python"),
         str(core / "tools" / "verified_pairs.py"), "stamp"],
        cwd=core, capture_output=True, text=True, timeout=120,
    )


def _base(core: Path):
    return subprocess.run(
        [str(core / ".venv" / "bin" / "python"),
         str(core / "tools" / "verified_pairs.py"), "base"],
        cwd=core, capture_output=True, text=True, timeout=120,
    )


def test_branch_deletion_skips_the_gate(pair):
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/feature {HEAD_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "deletion" in result.stdout
    assert _invocations(pair["log"]) == []


def test_branch_deletion_skips_the_gate_even_when_dirty(pair):
    (pair["core"] / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/feature {HEAD_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == []


def test_branch_deletion_skips_the_gate_with_unborn_head(pair):
    subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/unborn"],
                   cwd=pair["core"], check=True)
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/feature {HEAD_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == []


def test_non_main_push_runs_the_lighter_local_gate(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "lighter local gate" in result.stdout
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} check",
        f"make -C {pair['core']} test-affected",
        f"npm --prefix {pair['ui']} run check",
    ]


def test_main_push_runs_the_full_gate(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [f"make -C {pair['core']} system-check"]


def test_mixed_deletion_and_update_still_runs_the_gate(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/old {HEAD_SHA}\n"
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) != []


def test_stamped_pair_skips_the_full_gate_and_names_the_stamp(pair):
    stamped = _stamp(pair["core"])
    assert stamped.returncode == 0, stamped.stderr
    stamp_file = pair["core"] / ".git" / "learningos-verified-pairs.jsonl"
    assert stamp_file.is_file()
    row = json.loads(stamp_file.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["core_sha"] and row["ui_sha"] and row["toolchain"]["digest"]

    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "stamped pair" in result.stdout
    assert _invocations(pair["log"]) == []


def test_new_commit_after_stamp_re_runs_the_gate(pair):
    assert _stamp(pair["core"]).returncode == 0
    head = _commit(pair["core"], "after-stamp.txt", "after stamp")

    result = _run_hook(
        pair["core"],
        f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [f"make -C {pair['core']} system-check"]


def test_dirty_tree_blocks_despite_the_stamp(pair):
    assert _stamp(pair["core"]).returncode == 0
    (pair["core"] / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert "clean" in result.stderr
    assert _invocations(pair["log"]) == []


def test_stamp_refuses_dirty_trees(pair):
    (pair["ui"] / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
    stamped = _stamp(pair["core"])
    assert stamped.returncode == 0
    assert "not stamping" in stamped.stderr
    assert not (pair["core"] / ".git" / "learningos-verified-pairs.jsonl").exists()


def test_stale_installed_hook_still_fails(pair):
    installed = pair["core"] / ".git" / "hooks" / "pre-push"
    with installed.open("a", encoding="utf-8") as handle:
        handle.write("\n# stale\n")
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {HEAD_SHA} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert "stale" in result.stderr
    assert "make" in result.stderr and "hooks" in result.stderr
    assert _invocations(pair["log"]) == []


def test_hook_also_runs_from_the_ui_checkout(pair):
    head = _head(pair["ui"])
    result = _run_hook(
        pair["ui"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} check",
        f"make -C {pair['core']} test-affected",
        f"npm --prefix {pair['ui']} run check",
    ]


# ---- #113: the gate verifies the pushed SHAs, not the checkout -------------


def test_pushing_a_non_head_sha_refuses_naming_both(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/other {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert HEAD_SHA in result.stderr
    assert head in result.stderr
    assert "check out the commit you are pushing" in result.stderr
    assert _invocations(pair["log"]) == []


def test_one_non_head_line_among_matching_lines_still_refuses(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/ok {head} refs/heads/ok {ZERO_SHA}\n"
        f"refs/heads/sneaky {HEAD_SHA} refs/heads/sneaky {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert HEAD_SHA in result.stderr
    assert head in result.stderr
    assert _invocations(pair["log"]) == []


def test_a_non_head_push_to_main_is_refused_not_verified(pair):
    """`git push origin other-branch:main` from a clean stamped checkout must
    not silently verify the checkout (or skip on its stamp)."""
    assert _stamp(pair["core"]).returncode == 0
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/other {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert HEAD_SHA in result.stderr
    assert head in result.stderr
    assert _invocations(pair["log"]) == []


# ---- #113: review pushes diff against the last stamped pair -----------------


def test_base_reports_the_last_stamped_core_sha(pair):
    core = pair["core"]
    assert _base(core).returncode == 1
    first = _head(core)
    assert _stamp(core).returncode == 0
    assert _base(core).stdout.strip() == first
    second = _commit(core, "second.txt", "second")
    assert second != first
    assert _stamp(core).returncode == 0
    assert _base(core).stdout.strip() == second


def test_review_push_diffs_against_the_last_stamped_pair(pair):
    old = _head(pair["core"])
    assert _stamp(pair["core"]).returncode == 0
    head = _commit(pair["core"], "review-change.txt", "review change")
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert old in result.stdout
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} check",
        f"make -C {pair['core']} test-affected BASE={old}",
        f"npm --prefix {pair['ui']} run check",
    ]


def test_ui_only_change_runs_only_paired_tests_and_ui_check(pair):
    assert _stamp(pair["core"]).returncode == 0
    ui_head = _commit(pair["ui"], "fix.txt", "one-line UI fix")
    result = _run_hook(
        pair["ui"],
        f"refs/heads/feature {ui_head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "paired-contract" in result.stdout
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} test-paired",
        f"npm --prefix {pair['ui']} run check",
    ]


def test_changed_toolchain_cannot_reuse_the_core_baseline(pair):
    assert _stamp(pair["core"]).returncode == 0
    path = pair["core"] / ".git" / "learningos-verified-pairs.jsonl"
    row = json.loads(path.read_text())
    row["toolchain"]["digest"] = "0" * 64
    path.write_text(json.dumps(row) + "\n")
    ui_head = _commit(pair["ui"], "fix.txt", "UI fix after toolchain change")
    result = _run_hook(
        pair["ui"],
        f"refs/heads/feature {ui_head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} system-check",
    ]


def test_affected_test_discovery_failure_blocks_the_gate(tmp_path):
    shutil.copy(REPO_ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "affected_tests.py").write_text(
        "raise SystemExit(7)\n", encoding="utf-8")
    result = subprocess.run(
        ["make", "--silent", "test-affected", f"PY={sys.executable}"], cwd=tmp_path,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode != 0
    assert "no changes detected" not in result.stdout


# ---- #113: live_install deselection outside the live root -------------------


def test_hook_deselects_live_install_outside_the_live_root(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "deselecting live_install" in result.stdout
    env_lines = _invocations(pair["env_log"])
    assert len(env_lines) == 3
    assert all("not live_install" in line for line in env_lines)


def test_hook_keeps_existing_pytest_addopts_when_it_names_live_install(
        pair, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", '-m "not live_install"')
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "keeping the existing PYTEST_ADDOPTS" in result.stdout
    env_lines = _invocations(pair["env_log"])
    assert env_lines and all('not live_install' in line for line in env_lines)


def test_hook_keeps_full_selection_in_the_live_root(pair):
    wrapper = pair["core"].resolve().parent.parent
    for anchor in ("LearningOS/obsidian-ui", "LearningOS/workbench",
                   "LearningOS/archive"):
        (wrapper / anchor).mkdir(parents=True, exist_ok=True)
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "live_install" not in result.stdout
    assert _invocations(pair["env_log"]) == ["PYTEST_ADDOPTS=<unset>"] * 3


# ---- #113: the paired marker covers the Core/UI boundary --------------------

#: A read of the live sibling checkout through a parent-joined UI path.
#: Synthetic anchors (`"LearningOS/obsidian-ui"`) and fixture copies made
#: from a tmp path do not match.
_LIVE_UI_READ = re.compile(
    r"\.parents?\[\d+\]\s*/\s*\"obsidian-ui|"
    r"\bparent\s*/\s*\"obsidian-ui")

_PAIRED_BOUNDARY = [
    "test_causal_resolver.py",
    "test_contract_differential.py",
    "test_operations_gate.py",
    "test_trace_context.py",
    "test_ui_gateway_recovery.py",
    "test_vnext_boundaries.py",
]


def test_paired_marks_cover_every_live_ui_reader():
    """The hook's UI-only path is sound only if every Core test that reads
    the sibling checkout carries the paired mark. A new UI reader fails here
    until it is marked (or the boundary set is deliberately extended)."""
    tests_dir = REPO_ROOT / "tests"
    readers = sorted(
        path.name for path in tests_dir.glob("test_*.py")
        if _LIVE_UI_READ.search(path.read_text(encoding="utf-8")))
    assert readers == _PAIRED_BOUNDARY
    for name in readers:
        text = (tests_dir / name).read_text(encoding="utf-8")
        assert "mark.paired" in text, (
            f"{name} reads the live UI checkout but carries no paired mark")


def test_nothing_outside_the_boundary_carries_the_paired_mark():
    """The converse: a paired mark outside the boundary would run Core-only
    tests on every UI-only push."""
    tests_dir = REPO_ROOT / "tests"
    # The short substring (not the full decorator) so this file's own
    # assertions do not count as marks.
    marked = sorted(
        path.name for path in tests_dir.glob("test_*.py")
        if path.name != "test_pre_push_hook.py"
        and "pytest.mark.paired" in path.read_text(encoding="utf-8"))
    assert marked == _PAIRED_BOUNDARY
