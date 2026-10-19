"""The tool entrypoint contract (#113): --help and unknown flags never write.

Every ``tools/*.py`` entrypoint parses arguments: ``--help`` prints usage and
exits 0, an unknown flag exits 2, both before any write. Each tool runs in a
scratch copy of the repository, so a regressed tool can only dirty the copy —
never the checkout, and never the external materials tree (which resolves
beside the copy, not beside the checkout).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"

#: ``tools/*.py`` files that are helpers, not entrypoints (no ``__main__``
#: guard), and why. Empty is the goal: a file lands here only when running it
#: directly is meaningless.
NON_ENTRYPOINTS: dict[str, str] = {}

#: Entrypoints whose ``--help`` legitimately cannot run in a scratch copy
#: (needs the live wrapper root on disk, or the network), and why. Empty is
#: the goal: ``--help`` must parse and exit before touching anything, so an
#: entry here is a contract gap, not a convenience skip.
SCRATCH_EXCEPTIONS: dict[str, str] = {}

_BAD_FLAG = "--no-such-flag-xyz"

_COPY_IGNORE = shutil.ignore_patterns(
    ".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache")


def _entrypoints() -> list[str]:
    """Every ``tools/*.py`` with a ``__main__`` guard, sorted by name."""
    names = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if '__name__' in text and '__main__' in text:
            names.append(path.name)
    return names


def _snapshot(tree: Path) -> dict[str, str]:
    """Every file under ``tree`` (the copy plus anything beside it)."""
    out: dict[str, str] = {}
    for path in sorted(tree.rglob("*")):
        if not path.is_file() or path.is_symlink():
            if path.is_symlink():
                out[str(path.relative_to(tree))] = f"link->{path.readlink()}"
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        out[str(path.relative_to(tree))] = digest
    return out


def _run(tool: str, args: list[str], scratch: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONPATH=str(scratch / "tools"),
               PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, f"tools/{tool}.py", *args],
        cwd=scratch, env=env, capture_output=True, text=True, timeout=180)


@pytest.fixture(scope="module")
def scratch_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A scratch copy of the repository; the external trees resolve beside it.

    ``tools/*.py`` derive every path from ``__file__``, so running the copy's
    tools can only touch the copy (and a scratch ``materials/`` beside it).
    """
    wrapper = tmp_path_factory.mktemp("tool-contract")
    shutil.copytree(REPO_ROOT, wrapper / "repository", ignore=_COPY_IGNORE)
    return wrapper / "repository"


def test_every_tool_is_a_classified_entrypoint():
    on_disk = sorted(path.name for path in TOOLS_DIR.glob("*.py"))
    assert on_disk, "no tools/*.py found"
    helpers = [name for name in on_disk if name not in _entrypoints()]
    assert sorted(helpers) == sorted(NON_ENTRYPOINTS), (
        "unclassified tools/*.py helpers: add them to NON_ENTRYPOINTS with a "
        f"reason, or give them a __main__ guard: {helpers}")
    stale = [name for name in NON_ENTRYPOINTS if name not in on_disk]
    assert not stale, f"NON_ENTRYPOINTS names files that no longer exist: {stale}"
    stale_exc = [name for name in SCRATCH_EXCEPTIONS if name not in _entrypoints()]
    assert not stale_exc, (
        f"SCRATCH_EXCEPTIONS names non-entrypoints: {stale_exc}")


def test_help_prints_usage_and_writes_nothing(scratch_repo: Path):
    tools = [name[:-len(".py")] for name in _entrypoints()
             if name not in SCRATCH_EXCEPTIONS]
    assert tools, "no entrypoints found"
    assert not SCRATCH_EXCEPTIONS, (
        "contract gap: these entrypoints cannot run --help in scratch: "
        + ", ".join(f"{name} ({SCRATCH_EXCEPTIONS[name]})"
                    for name in sorted(SCRATCH_EXCEPTIONS)))
    wrapper = scratch_repo.parent
    before = _snapshot(wrapper)
    for tool in tools:
        proc = _run(tool, ["--help"], scratch_repo)
        assert proc.returncode == 0, (
            f"{tool}.py --help exited {proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
        assert "usage" in proc.stdout.lower(), (
            f"{tool}.py --help printed no usage\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    assert _snapshot(wrapper) == before, (
        "a --help run wrote into the scratch tree")


def test_unknown_flags_refuse_before_any_write(scratch_repo: Path):
    tools = [name[:-len(".py")] for name in _entrypoints()
             if name not in SCRATCH_EXCEPTIONS]
    wrapper = scratch_repo.parent
    before = _snapshot(wrapper)
    for tool in tools:
        proc = _run(tool, [_BAD_FLAG], scratch_repo)
        assert proc.returncode == 2, (
            f"{tool}.py {_BAD_FLAG} exited {proc.returncode}, want 2\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    assert _snapshot(wrapper) == before, (
        "an unknown-flag run wrote into the scratch tree")


def test_capability_schemas_check_reports_drift_without_writing(scratch_repo: Path):
    """``--check`` is the drift test as a command: exit 1 naming drifted files."""
    wrapper = scratch_repo.parent
    before = _snapshot(wrapper)
    clean = _run("generate_capability_schemas", ["--check"], scratch_repo)
    assert clean.returncode == 0, (
        f"--check on a clean tree exited {clean.returncode}\n"
        f"--- stdout ---\n{clean.stdout}\n--- stderr ---\n{clean.stderr}")
    target = scratch_repo / "system" / "schema" / "capabilities"
    victim = sorted(target.glob("*.schema.json"))[0]
    original = victim.read_bytes()
    victim.write_bytes(original.replace(b'"title"', b'"title_drifted"', 1))
    try:
        drifted = _run("generate_capability_schemas", ["--check"], scratch_repo)
        assert drifted.returncode == 1, (
            f"--check on a drifted tree exited {drifted.returncode}, want 1\n"
            f"--- stdout ---\n{drifted.stdout}\n--- stderr ---\n{drifted.stderr}")
        assert victim.name in drifted.stdout, (
            f"--check did not name the drifted file\n--- stdout ---\n{drifted.stdout}")
    finally:
        victim.write_bytes(original)
    assert victim.read_bytes() == original
    assert _snapshot(wrapper) == before, "--check wrote into the scratch tree"


def test_materials_index_html_flag_reaches_the_builder(monkeypatch):
    """The entrypoint owns ``--html``; the package keeps its default for callers."""
    import build_materials_index
    from materials_index import cli

    seen: dict = {}

    def fake_main(html=None):
        seen["html"] = html
        return 0

    monkeypatch.setattr(cli, "main", fake_main)
    assert build_materials_index.main(["--html"]) == 0
    assert seen == {"html": True}
    assert build_materials_index.main([]) == 0
    assert seen == {"html": False}
    with pytest.raises(SystemExit) as excinfo:
        build_materials_index.main(["--help"])
    assert excinfo.value.code == 0


def test_codex_wrapper_still_refuses_an_empty_prompt(monkeypatch, capsys):
    """The argparse conversion keeps the wrapper's exact refusal (exit 2)."""
    import codex_obsidian

    monkeypatch.setattr(sys, "argv", ["codex_obsidian.py"])
    assert codex_obsidian.main() == 2
    assert "expected one prompt argument" in capsys.readouterr().err
    monkeypatch.setattr(sys, "argv", ["codex_obsidian.py", "   "])
    assert codex_obsidian.main() == 2
    assert "expected one prompt argument" in capsys.readouterr().err
