"""Code-only architecture checks; no canonical records or materials are read."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from code_reachability import UNREACHABLE_ALLOWLIST, analyse
from group_map import groups_for_paths
from group_map import tests_for_groups as selected_tests

from learning_os import __version__

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("source", "regression"), [
    ("derive/material_synthesis.py", "test_synthesis_analysis_refs.py"),
    ("store/material_analysis.py", "test_synthesis_analysis_refs.py"),
    ("commands/analysis.py", "test_material_analysis_save.py"),
    ("commands/reads.py", "test_material_context.py"),
    ("commands/material.py", "test_plan_edit_brief.py"),
])
def test_affected_selection_includes_owning_regressions(source, regression):
    selected = selected_tests(groups_for_paths([f"tools/learning_os/{source}"]))
    assert f"tests/{regression}" in selected


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


# --------------------------------- generated handler edges (S12 correction 1)
#
# SPEC (aq): schema-declared handler imports are edges FROM the generated
# parser, never extra reachability roots.


def _binding(name, handler="learning_os.commands.query.cmd_synth"):
    return {"x-los-cli-command": {"name": name, "handler": handler}}


def _handler_tree(tmp_path: Path, *, entry_import: str, order,
                  schemas: dict, query_imports: str = "",
                  extra: dict | None = None):
    tools = tmp_path / "tools"
    package = tools / "learning_os"
    adapters = package / "adapters"
    commands = package / "commands"
    adapters.mkdir(parents=True)
    commands.mkdir(parents=True)
    (tools / "entry.py").write_text(entry_import, encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (adapters / "__init__.py").write_text("", encoding="utf-8")
    (commands / "__init__.py").write_text("", encoding="utf-8")
    (adapters / "cli_parser.py").write_text(
        f"_SUBCOMMAND_ORDER = {order!r}\n", encoding="utf-8")
    (commands / "query.py").write_text(
        f"{query_imports}def cmd_synth(args):\n    return 0\n",
        encoding="utf-8")
    for relative, content in (extra or {}).items():
        path = tools / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    requests = tmp_path / "system/schema/requests"
    requests.mkdir(parents=True)
    for name, doc in schemas.items():
        text = doc if isinstance(doc, str) else json.dumps(doc)
        (requests / name).write_text(text, encoding="utf-8")
    return tools


def _analyse_tree(tools: Path):
    return analyse(
        tools,
        entrypoints=("entry.py",),
        package_roots={"learning_os": "learning_os"},
        allowlist={},
    )


def test_connected_parser_makes_its_handler_reachable(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os.adapters import cli_parser\n",
        order=("synth",), schemas={"synth.schema.json": _binding("synth")})
    report = _analyse_tree(tools)
    assert report.configuration_errors == ()
    assert "learning_os.commands.query" in report.reachable_modules
    assert report.unreachable_modules == ()
    assert report.ok


def test_disconnected_parser_leaves_its_handler_unreachable(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os import lonely\n",
        order=("synth",), schemas={"synth.schema.json": _binding("synth")},
        extra={"learning_os/lonely.py": "VALUE = 1\n"})
    report = _analyse_tree(tools)
    # Valid metadata, but the parser is not imported: no silent blessing.
    assert report.configuration_errors == ()
    assert "learning_os.adapters.cli_parser" in report.unreachable_modules
    assert "learning_os.commands.query" in report.unreachable_modules
    assert not report.ok


def test_invoke_handler_binds_the_adapter_module(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os.adapters import cli_parser\n",
        order=("synth",), schemas={"synth.schema.json": _binding(
            "synth", "learning_os.adapters.cli.invoke:cli.synth")},
        extra={"learning_os/adapters/cli.py":
               "def invoke(args):\n    return 0\n"})
    report = _analyse_tree(tools)
    assert report.configuration_errors == ()
    assert "learning_os.adapters.cli" in report.reachable_modules
    # The unbound handler module stays unreachable: edges, not roots.
    assert report.unreachable_modules == (
        "learning_os.commands", "learning_os.commands.query")


def test_missing_handler_module_fails_configuration(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os.adapters import cli_parser\n",
        order=("synth",), schemas={"synth.schema.json": _binding(
            "synth", "learning_os.commands.missing.cmd_x")})
    report = _analyse_tree(tools)
    assert len(report.configuration_errors) == 1
    assert "synth.schema.json" in report.configuration_errors[0]
    assert "handler module is not owned" in report.configuration_errors[0]
    assert not report.ok


def test_missing_handler_function_fails_configuration(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os.adapters import cli_parser\n",
        order=("synth",), schemas={"synth.schema.json": _binding(
            "synth", "learning_os.commands.query.cmd_nope")})
    report = _analyse_tree(tools)
    assert len(report.configuration_errors) == 1
    assert "handler function does not exist" in report.configuration_errors[0]
    assert not report.ok


def test_unknown_duplicate_and_missing_bindings_fail(tmp_path: Path):
    entry = "from learning_os.adapters import cli_parser\n"
    ghost = _handler_tree(
        tmp_path / "ghost",
        entry_import=entry, order=("synth",),
        schemas={"ghost.schema.json": _binding("ghost")})
    assert any("unknown or duplicate CLI binding" in error
               for error in _analyse_tree(ghost).configuration_errors)
    assert not _analyse_tree(ghost).ok
    double = _handler_tree(
        tmp_path / "double",
        entry_import=entry, order=("synth",),
        schemas={"synth.schema.json": _binding("synth"),
                 "synth2.schema.json": _binding("synth")})
    assert any("unknown or duplicate CLI binding" in error
               for error in _analyse_tree(double).configuration_errors)
    assert not _analyse_tree(double).ok
    short = _handler_tree(
        tmp_path / "short",
        entry_import=entry, order=("synth", "ghost"),
        schemas={"synth.schema.json": _binding("synth")})
    assert any("missing generated CLI bindings" in error
               for error in _analyse_tree(short).configuration_errors)
    assert not _analyse_tree(short).ok


def test_malformed_request_fails_configuration(tmp_path: Path):
    entry = "from learning_os.adapters import cli_parser\n"
    not_object = _handler_tree(
        tmp_path / "not-object",
        entry_import=entry, order=("synth",),
        schemas={"synth.schema.json": json.dumps([{"x-los-cli-command": {}}])})
    assert any("request document is not an object" in error
               for error in _analyse_tree(not_object).configuration_errors)
    assert not _analyse_tree(not_object).ok
    no_handler = _handler_tree(
        tmp_path / "no-handler",
        entry_import=entry, order=("synth",),
        schemas={"synth.schema.json": {"x-los-cli-command": {"name": "synth"}}})
    assert len(_analyse_tree(no_handler).configuration_errors) == 1
    assert not _analyse_tree(no_handler).ok


def test_schema_edge_participates_in_cycle_detection(tmp_path: Path):
    tools = _handler_tree(
        tmp_path, entry_import="from learning_os.adapters import cli_parser\n",
        order=("synth",), schemas={"synth.schema.json": _binding("synth")},
        query_imports="from learning_os.adapters import cli_parser\n")
    report = _analyse_tree(tools)
    assert report.dependency_cycles == (
        ("learning_os.adapters.cli_parser", "learning_os.commands.query"),)
    assert not report.ok


def test_production_edges_are_clean_with_no_allowlist_growth():
    report = analyse(ROOT / "tools")
    assert report.configuration_errors == ()
    assert report.ok
    assert set(UNREACHABLE_ALLOWLIST) == {
        "learning_os.contracts.migration_lifecycle",
        "migrations.curriculum_v2",
        "migrations.job_quarantine_collapse",
        "migrations.library_taxonomy_v1",
        "migrations.lift_angle_out_of_locator",
        "migrations.projects_v1",
        "migrations.registry_partition_v1",
        "migrations.route_identity_v13",
        "migrations.standardize_job_plans_v1",
        "migrations.standardize_plan_template_v10",
        "migrations.summaries_to_notes_v1",
    }
    assert set(report.allowed_unreachable) == set(UNREACHABLE_ALLOWLIST)


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
