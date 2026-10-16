"""Control for the health scenarios' external Time Machine input (SPEC (bm)).

Disposition 3 scopes a controlled `tmutil` to exactly the two
health-report operations: scenario observations must not depend on whether
the host carries macOS backup tooling or a configured backup. These tests
prove, with real launched children, that a health child observes the scoped
fake producing the recorded no-destination input, and that an unrelated
operation's PATH is byte-identical to the host's.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
import scenario_harness


def _ctx(tmp_path: Path, operation: str) -> scenario_harness._CaseContext:
    workdir = tmp_path / "case"
    root = workdir / "fx" / "root"
    root.mkdir(parents=True)
    return scenario_harness._CaseContext(
        root=root, workdir=workdir,
        observations_path=workdir / "observations.json",
        operation=operation, case_id="shim-control")


@pytest.mark.parametrize("operation", ["health.report", "health.report"])
def test_health_child_observes_the_scoped_tmutil(tmp_path: Path, operation: str):
    """A real health child runs the case-scoped fake, not the host tool."""
    ctx = _ctx(tmp_path, operation)
    env = scenario_harness._launch_env(ctx, "shim-token", None)
    bindir = ctx.workdir / "health-bin"
    assert env["PATH"].split(os.pathsep)[0] == str(bindir)
    shim = bindir / "tmutil"
    assert shim.is_file() and not shim.is_symlink()
    assert shim.stat().st_mode & stat.S_IXUSR
    assert shim.read_text(encoding="utf-8") == scenario_harness._TMUTIL_SHIM
    assert bindir.parent == ctx.workdir  # under the case workdir ...
    assert ctx.root not in shim.parents  # ... outside the fixture root
    assert sorted(entry.name for entry in bindir.iterdir()) == ["tmutil"]
    which = scenario_harness.launch(ctx, ["sh", "-c", "command -v tmutil"])
    assert which.returncode == 0
    assert which.stdout.strip() == str(shim)
    info = scenario_harness.launch(ctx, ["tmutil", "destinationinfo"])
    assert info.returncode == 1
    assert "No destinations configured" in info.stderr


@pytest.mark.parametrize("operation", [
    "backup.manifest",  # a real unrelated operation, unmodified
    "health.reports",  # a near-miss name: the scope is exactly the two
])
def test_unrelated_operation_path_is_unchanged(tmp_path: Path, operation: str):
    """Any other operation launches with the host PATH and no shim."""
    ctx = _ctx(tmp_path, operation)
    env = scenario_harness._launch_env(ctx, "shim-token", None)
    assert env.get("PATH", "") == os.environ.get("PATH", "")
    assert not (ctx.workdir / "health-bin").exists()
    assert [path for path in ctx.workdir.rglob("*")
            if path.name == "tmutil"] == []
    proc = scenario_harness.launch(ctx, ["sh", "-c", "command -v tmutil || true"])
    assert ctx.workdir.as_posix() not in proc.stdout
