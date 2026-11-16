"""The ref-aware pre-push gate (#106, #113).

A scripted Core/UI fixture pair (real git, real hook, stubbed `make`/`npm`)
proves that eligible updates delegate verification upstream and never invoke
make or npm. The hook still checks the refs and both checkouts.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
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
    # Real checkouts ignore bytecode caches; the gate's own interpreter
    # writes them mid-run, and a serialized second push must not see dirt.
    for repo in (core, ui):
        (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    # The canonical gate under test, verbatim.
    (core / "tools" / "hooks").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "tools" / "hooks" / "pre-push",
                core / "tools" / "hooks" / "pre-push")
    # Deterministic interpreter for hook checks.
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
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
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


def test_non_main_push_defers_to_upstream(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "release verification runs upstream" in result.stdout
    assert _invocations(pair["log"]) == []


def test_main_push_defers_to_upstream(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "release verification runs upstream" in result.stdout
    assert _invocations(pair["log"]) == []


def test_mixed_deletion_and_update_defers_to_upstream(pair):
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/old {HEAD_SHA}\n"
        f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "release verification runs upstream" in result.stdout
    assert _invocations(pair["log"]) == []


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
    assert _invocations(pair["log"]) == []


# ---- #24: a hook inherits Git's routing for the pushing repository --------


def test_inherited_git_dir_does_not_route_the_ui_check_to_core(pair):
    """Git exports an absolute GIT_DIR to a hook; `git -C <ui>` must still
    read the UI. Before #24 the clean UI looked dirty: Core's index listed
    ui.txt as untracked and core.txt as deleted."""
    head = _head(pair["core"])
    hook = pair["core"] / ".git" / "hooks" / "pre-push"
    result = subprocess.run(
        [str(hook)], cwd=pair["core"],
        input=f"refs/heads/feature {head} refs/heads/feature {ZERO_SHA}\n",
        env={**os.environ, "GIT_DIR": str(pair["core"] / ".git")},
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert "requires clean Core and UI" not in result.stderr
    assert "release verification runs upstream" in result.stdout


def test_a_push_from_a_linked_worktree_passes_the_clean_pair_gate(pair, tmp_path):
    """The real route: `git push` from a linked Core worktree beside a UI
    clone runs the installed hook with Git's own environment."""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    linked = tmp_path / "linked-pair"
    linked.mkdir()
    subprocess.run(["git", "-C", str(pair["core"]), "worktree", "add", "-q",
                    "-b", "feature", str(linked / "repository")], check=True)
    subprocess.run(["git", "clone", "-q", str(pair["ui"]),
                    str(linked / "obsidian-ui")], check=True)
    pushed = subprocess.run(
        ["git", "-C", str(linked / "repository"), "push", "-q", str(remote),
         "feature"], capture_output=True, text=True, timeout=120)
    assert pushed.returncode == 0, pushed.stderr
    assert _invocations(pair["log"]) == []


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
    """`git push origin other-branch:main` from a clean checkout must
    not silently verify the checkout."""
    head = _head(pair["core"])
    result = _run_hook(
        pair["core"],
        f"refs/heads/other {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 1
    assert HEAD_SHA in result.stderr
    assert head in result.stderr
    assert _invocations(pair["log"]) == []


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


# ---- #113: the paired marker covers the Core/UI boundary --------------------

#: A read of the live sibling checkout through a parent-joined UI path.
#: Synthetic anchors (`"LearningOS/obsidian-ui"`) and fixture copies made
#: from a tmp path do not match.
_LIVE_UI_READ = re.compile(
    r"\.parents?\[\d+\]\s*/\s*\"obsidian-ui|"
    r"\bparent\s*/\s*\"obsidian-ui")

_PAIRED_BOUNDARY = [
    "test_arch_prose.py",
    "test_causal_resolver.py",
    "test_contract_differential.py",
    "test_flows_pin.py",
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


@pytest.mark.parametrize("selection", ["empty", "failure", "selected"])
def test_commit_check_preserves_affected_selection_contract(tmp_path, selection):
    """Empty selection skips; discovery failure blocks; selected tests run."""
    import shlex

    shutil.copy(REPO_ROOT / "Makefile", tmp_path / "Makefile")
    venv = tmp_path / ".venv/bin"
    venv.mkdir(parents=True)
    imports = venv / "lint-imports"
    imports.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    imports.chmod(0o755)
    calls = tmp_path / "calls.jsonl"
    driver = tmp_path / "probe_python.py"
    driver.write_text(
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "args=sys.argv[1:]\n"
        "with Path(os.environ['SELECTION_LOG']).open('a') as out: "
        "out.write(json.dumps(args)+'\\n')\n"
        "if args and args[0]=='tools/affected_tests.py':\n"
        "    mode=os.environ['SELECTION_MODE']\n"
        "    if mode=='failure': raise SystemExit(7)\n"
        "    if mode=='selected': print('tests/test_selected.py')\n",
        encoding="utf-8")
    env = dict(os.environ, SELECTION_LOG=str(calls), SELECTION_MODE=selection)
    result = subprocess.run(
        ["make", "--silent", "commit-check", "BASE=reviewed-base",
         "PY=" + shlex.join([sys.executable, str(driver)])],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    invocations = [json.loads(line) for line in calls.read_text().splitlines()]
    assert ["tools/affected_tests.py", "--base", "reviewed-base"] in invocations
    assert ["-m", "pytest", "-q"] not in invocations
    selected = ["-m", "pytest", "-q", "tests/test_selected.py"]
    assert (selected in invocations) == (selection == "selected")
    assert (result.returncode != 0) == (selection == "failure"), result.stderr


def _ci_bootstrap_intent(pair, *, trailer=True):
    core = pair["core"]
    subprocess.run(["git", "switch", "-qc", "feat"], cwd=core, check=True)
    if trailer:
        subprocess.run([
            "git", "commit", "--allow-empty", "-qm",
            "Submit this exact feature head to hosted CI.\n\nLOS-CI-Bootstrap: feat",
        ], cwd=core, check=True)
    return _head(core)


def test_ci_bootstrap_accepts_clean_non_main_head(pair, monkeypatch):
    head = _ci_bootstrap_intent(pair)
    monkeypatch.setenv("LOS_CI_BOOTSTRAP", "feat")
    result = _run_hook(pair["core"], f"refs/heads/feat {head} refs/heads/feat {ZERO_SHA}\n")
    assert result.returncode == 0
    assert f"CI-bootstrap branch=feat sha={head}" in result.stderr
    assert "UNVERIFIED" in result.stderr
    assert _invocations(pair["log"]) == []  # no local gate


def test_ci_bootstrap_refuses_main(pair, monkeypatch):
    head = _ci_bootstrap_intent(pair)
    monkeypatch.setenv("LOS_CI_BOOTSTRAP", "feat")
    result = _run_hook(pair["core"], f"refs/heads/main {head} refs/heads/main {ZERO_SHA}\n")
    assert result.returncode == 1
    assert "protected refs" in result.stderr


@pytest.mark.parametrize("invalid", [
    "boolean", "wrong-branch", "missing-trailer", "wrong-remote", "multiple-refs", "detached", "tag",
])
def test_ci_bootstrap_refuses_unbound_submission_intent(pair, monkeypatch, invalid):
    head = _ci_bootstrap_intent(pair, trailer=invalid != "missing-trailer")
    value = "1" if invalid == "boolean" else "other" if invalid == "wrong-branch" else "feat"
    monkeypatch.setenv("LOS_CI_BOOTSTRAP", value)
    remote = "refs/heads/other" if invalid == "wrong-remote" else "refs/heads/feat"
    if invalid == "tag":
        remote = "refs/tags/release"
    if invalid == "detached":
        subprocess.run(["git", "checkout", "--detach", "-q", head], cwd=pair["core"], check=True)
    refs = f"refs/heads/feat {head} {remote} {ZERO_SHA}\n"
    if invalid == "multiple-refs":
        refs += f"refs/heads/feat {head} refs/heads/other {ZERO_SHA}\n"
    result = _run_hook(pair["core"], refs)
    assert result.returncode == 1
    assert _invocations(pair["log"]) == []


def _hooks_checkout(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parent.parent
    checkout = tmp_path / "repository"
    (checkout / "tools" / "hooks").mkdir(parents=True)
    shutil.copy(root / "Makefile", checkout / "Makefile")
    for hook in ("pre-commit", "post-commit", "pre-push"):
        shutil.copy(root / "tools" / "hooks" / hook, checkout / "tools" / "hooks" / hook)
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    return checkout


def test_make_hooks_is_idempotent_when_core_runs_the_canonical_directory(tmp_path):
    checkout = _hooks_checkout(tmp_path)
    ui_hooks = tmp_path / "obsidian-ui" / ".git" / "hooks"
    ui_hooks.mkdir(parents=True)
    subprocess.run(["git", "config", "core.hooksPath", str(checkout / "tools" / "hooks")],
                   cwd=checkout, check=True)
    result = subprocess.run(["make", "hooks"], cwd=checkout, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    # Reaching the UI step is what the same-file failure used to prevent.
    assert (ui_hooks / "pre-push").read_bytes() == (checkout / "tools" / "hooks" / "pre-push").read_bytes()


def test_make_hooks_still_copies_to_a_distinct_hooks_directory(tmp_path):
    checkout = _hooks_checkout(tmp_path)
    result = subprocess.run(["make", "hooks"], cwd=checkout, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for hook in ("pre-commit", "post-commit", "pre-push"):
        installed = checkout / ".git" / "hooks" / hook
        assert installed.read_bytes() == (checkout / "tools" / "hooks" / hook).read_bytes()
        assert os.access(installed, os.X_OK)
