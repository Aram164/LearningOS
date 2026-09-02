"""Code-only architecture checks; no canonical records or materials are read."""

from __future__ import annotations

import tomllib
from pathlib import Path

from code_reachability import analyse

from learning_os import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_core_modules_are_statically_classified():
    report = analyse(ROOT / "tools")
    assert report.ok, report.as_dict()


def test_gate_detects_and_can_explicitly_classify_an_unreachable_module(tmp_path: Path):
    tools = tmp_path / "tools"
    package = tools / "demo"
    package.mkdir(parents=True)
    (tools / "entry.py").write_text("from demo import live\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "live.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "dead.py").write_text("VALUE = 2\n", encoding="utf-8")

    report = analyse(
        tools,
        entrypoints=("entry.py",),
        package_roots={"demo": "demo"},
        allowlist={},
    )
    assert report.unreachable_modules == ("demo.dead",)
    assert not report.ok

    classified = analyse(
        tools,
        entrypoints=("entry.py",),
        package_roots={"demo": "demo"},
        allowlist={"demo.dead": "synthetic extension loaded outside the static graph"},
    )
    assert classified.ok
    assert classified.allowed_unreachable == ("demo.dead",)


def test_gate_rejects_a_reachable_dependency_cycle(tmp_path: Path):
    tools = tmp_path / "tools"
    package = tools / "demo"
    package.mkdir(parents=True)
    (tools / "entry.py").write_text("from demo import first\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "first.py").write_text("from . import second\n", encoding="utf-8")
    (package / "second.py").write_text("from . import first\n", encoding="utf-8")

    report = analyse(
        tools,
        entrypoints=("entry.py",),
        package_roots={"demo": "demo"},
        allowlist={},
    )

    assert report.dependency_cycles == (("demo.first", "demo.second"),)
    assert not report.ok


def test_gate_rejects_a_package_importing_an_executable_entrypoint(tmp_path: Path):
    tools = tmp_path / "tools"
    package = tools / "demo"
    package.mkdir(parents=True)
    (tools / "entry.py").write_text("from demo import live\n", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "live.py").write_text("import entry\n", encoding="utf-8")

    report = analyse(
        tools,
        entrypoints=("entry.py",),
        package_roots={"demo": "demo"},
        allowlist={},
    )

    assert report.package_entrypoint_imports == ("demo.live -> entry",)
    assert not report.ok


def test_pyproject_is_the_version_and_dependency_authority():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    assert __version__ == project["version"]

    compatibility_lines = [
        line.strip()
        for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert compatibility_lines == ["-e .[dev]"]
