"""The ref-aware pre-push gate and its verified-pair memo (#106).

A scripted Core/UI fixture pair (real git, real hook, stubbed `make`/`npm`)
proves: deletions skip the gate, non-main refs run the lighter local gate,
main keeps the full `system-check`, an exact stamped pair skips with the
stamp named, and any new commit or dirty tree re-runs the gate.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ZERO_SHA = "0" * 40
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
    # The canonical gate and memo under test, copied verbatim.
    (core / "tools" / "hooks").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "tools" / "hooks" / "pre-push",
                core / "tools" / "hooks" / "pre-push")
    shutil.copy(REPO_ROOT / "tools" / "verified_pairs.py",
                core / "tools" / "verified_pairs.py")
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
    stub_bin = tmp_path / "stub-bin"
    stub_bin.mkdir()
    for name in ("make", "npm"):
        stub = stub_bin / name
        stub.write_text(f'#!/bin/sh\necho "{name} $*" >> "$GATE_LOG"\n',
                        encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("GATE_LOG", str(log))
    monkeypatch.setenv("PATH", str(stub_bin) + os.pathsep + os.environ["PATH"])
    return {"root": root, "core": core, "ui": ui, "log": log}


def _run_hook(repo: Path, stdin: str):
    hook = repo / ".git" / "hooks" / "pre-push"
    return subprocess.run([str(hook)], cwd=repo, input=stdin,
                          capture_output=True, text=True, timeout=120)


def _invocations(log: Path) -> list[str]:
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


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


def test_non_main_push_runs_the_lighter_local_gate(pair):
    result = _run_hook(
        pair["core"],
        f"refs/heads/feature {HEAD_SHA} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "lighter local gate" in result.stdout
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} check",
        f"make -C {pair['core']} test-affected",
        f"npm --prefix {pair['ui']} run check",
    ]


def test_main_push_runs_the_full_gate(pair):
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [f"make -C {pair['core']} system-check"]


def test_mixed_deletion_and_update_still_runs_the_gate(pair):
    result = _run_hook(
        pair["core"],
        f"(delete) {ZERO_SHA} refs/heads/old {HEAD_SHA}\n"
        f"refs/heads/feature {HEAD_SHA} refs/heads/feature {ZERO_SHA}\n",
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

    result = _run_hook(
        pair["core"],
        f"refs/heads/main {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert "stamped pair" in result.stdout
    assert _invocations(pair["log"]) == []


def test_new_commit_after_stamp_re_runs_the_gate(pair):
    assert _stamp(pair["core"]).returncode == 0
    (pair["core"] / "after-stamp.txt").write_text("new\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=pair["core"], check=True)
    subprocess.run(["git", "commit", "-qm", "after stamp"], cwd=pair["core"], check=True)

    result = _run_hook(
        pair["core"],
        f"refs/heads/main {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [f"make -C {pair['core']} system-check"]


def test_dirty_tree_blocks_despite_the_stamp(pair):
    assert _stamp(pair["core"]).returncode == 0
    (pair["core"] / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")
    result = _run_hook(
        pair["core"],
        f"refs/heads/main {HEAD_SHA} refs/heads/main {ZERO_SHA}\n",
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
    result = _run_hook(
        pair["ui"],
        f"refs/heads/feature {HEAD_SHA} refs/heads/feature {ZERO_SHA}\n",
    )
    assert result.returncode == 0, result.stderr
    assert _invocations(pair["log"]) == [
        f"make -C {pair['core']} check",
        f"make -C {pair['core']} test-affected",
        f"npm --prefix {pair['ui']} run check",
    ]
