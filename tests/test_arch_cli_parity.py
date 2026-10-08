"""CLI parity: generated parser equals the old parser (PLAN D2, SPEC 10.7).

Also enforces ``system/contracts/cli-operations.yaml`` (SPEC 10.8).
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
from pathlib import Path
from unittest import mock

import arch_cli_describe
import yaml

ROOT = Path(__file__).resolve().parent.parent
CLI_OPS_PATH = ROOT / "system/contracts/cli-operations.yaml"
BASELINE_PATH = ROOT / "tests/architecture/cli-parity-baseline.json"
CORPUS_PATH = ROOT / "tests/architecture/cli-parity-corpus.json"
REQUESTS_DIR = ROOT / "system/schema/requests"

FIX = "Generated parser drifted from the recorded CLI surface (PLAN D2)."


def test_cli_operations_lists_every_cli_primary():
    data = yaml.safe_load(CLI_OPS_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1
    operations = data.get("operations", {})
    assert len(operations) == 41, len(operations)
    for name, entry in sorted(operations.items()):
        assert name.startswith("cli."), name
        assert entry.get("cli_command") == name[len("cli."):], name
        assert entry.get("kind") in {"query", "command", "porcelain", "tool"}, name


def _handler_for_subcommand(subcommand: str) -> str | None:
    for path in REQUESTS_DIR.glob("*.schema.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cmd = data.get("x-los-cli-command")
        if cmd is not None and cmd.get("name") == subcommand:
            handler = cmd.get("handler", "")
            return handler if isinstance(handler, str) else None
    return None


def _normalize_registered_namespace(recorded: dict, handler: str) -> dict:
    """Amendment (u) item 2: baseline namespace for a converted subcommand."""
    prefix = "learning_os.adapters.cli.invoke:"
    assert handler.startswith(prefix), handler
    operation = handler[len(prefix):]
    normalized = dict(recorded)
    normalized["func"] = "learning_os.adapters.cli.invoke"
    normalized["_operation"] = operation
    return normalized


def _normalize_registered_defaults(baseline_defaults: dict, handler: str) -> dict:
    prefix = "learning_os.adapters.cli.invoke:"
    assert handler.startswith(prefix), handler
    operation = handler[len(prefix):]
    normalized = dict(baseline_defaults)
    normalized["func"] = "learning_os.adapters.cli.invoke"
    normalized["_operation"] = repr(operation)
    return normalized


def test_registered_normalization_with_synthetic_handler():
    # No production registration exists in S12; prove the future rule.
    handler = "learning_os.adapters.cli.invoke:cli.inspect"
    recorded = {"func": "learning_os.commands.query.cmd_inspect", "id": "X"}
    normalized = _normalize_registered_namespace(recorded, handler)
    assert normalized["func"] == "learning_os.adapters.cli.invoke"
    assert normalized["_operation"] == "cli.inspect"
    assert normalized["id"] == "X"
    defaults = {"func": "learning_os.commands.query.cmd_inspect"}
    normalized_defaults = _normalize_registered_defaults(defaults, handler)
    assert normalized_defaults["func"] == "learning_os.adapters.cli.invoke"
    assert normalized_defaults["_operation"] == repr("cli.inspect")


def _normalize_describe(doc: dict) -> dict:
    normalized = copy.deepcopy(doc)
    # The moved parser class keeps its code but not its module.
    normalized["parser_class"] = "NORMALIZED_PARSER_CLASS"
    for sub in normalized.get("subparsers", {}).values():
        defaults = sub.get("defaults", {})
        if "_parser_factory" in defaults:
            defaults["_parser_factory"] = "NORMALIZED_FACTORY"
    return normalized


def test_generated_parser_matches_baseline_structure():
    import los

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    live = _normalize_describe(arch_cli_describe.describe(los.build_parser()))
    expected = _normalize_describe(baseline)
    # Future registered subcommands (none yet) normalize per (u) item 2.
    for name, sub in expected.get("subparsers", {}).items():
        handler = _handler_for_subcommand(name)
        if handler is not None and handler.startswith(
                "learning_os.adapters.cli.invoke:"):
            sub["defaults"] = _normalize_registered_defaults(
                sub.get("defaults", {}), handler)
    assert live["order"] == expected["order"], f"{FIX} order"
    assert live["parser_class"] == expected["parser_class"]
    assert live["prog"] == expected["prog"], f"{FIX} prog"
    assert live["description"] == expected["description"], f"{FIX} description"
    assert live["formatter_class"] == expected["formatter_class"], f"{FIX} formatter"
    assert live["root_options"] == expected["root_options"], f"{FIX} root options"
    assert set(live["subparsers"]) == set(expected["subparsers"]), f"{FIX} subcommands"
    for name in expected["order"]:
        assert live["subparsers"][name] == expected["subparsers"][name], \
            f"{FIX} subcommand {name}"


def _normalize_namespace(namespace: dict) -> dict:
    normalized = dict(namespace)
    for key, value in list(normalized.items()):
        if key == "_parser_factory" and isinstance(value, str) \
                and value.endswith("build_parser"):
            normalized[key] = "NORMALIZED_FACTORY"
    return normalized


def _run(parser, argv: list[str]) -> dict:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with mock.patch.object(sys, "argv", ["los", *argv]):
        with contextlib.redirect_stdout(stdout_buf), \
                contextlib.redirect_stderr(stderr_buf):
            try:
                namespace = parser.parse_args(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
                stderr = stderr_buf.getvalue()
                first = stderr.strip().splitlines()[0] if stderr.strip() else ""
                return {"error": {"exit": code, "first_line": first}}
    data = dict(vars(namespace))
    for key, value in list(data.items()):
        if callable(value):
            module = getattr(value, "__module__", "") or ""
            qualname = getattr(value, "__qualname__", "") \
                or getattr(value, "__name__", "")
            data[key] = f"{module}.{qualname}" if module else str(qualname)
    return {"namespace": _normalize_namespace(data)}


def test_corpus_parity():
    import los

    parser = los.build_parser()
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []
    for index, entry in enumerate(corpus["cases"]):
        argv = entry["argv"]
        recorded = entry["result"]
        actual = _run(parser, argv)
        # Registered-subcommand normalization (none yet; see unit test).
        subcommand = None
        for token in argv:
            if not token.startswith("-"):
                subcommand = token
                break
        if subcommand is not None and "namespace" in recorded:
            handler = _handler_for_subcommand(subcommand)
            if handler is not None and handler.startswith(
                    "learning_os.adapters.cli.invoke:"):
                recorded = {"namespace": _normalize_registered_namespace(
                    _normalize_namespace(recorded["namespace"]), handler)}
            else:
                recorded = {"namespace": _normalize_namespace(recorded["namespace"])} \
                    if "namespace" in recorded else recorded
        elif "namespace" in recorded:
            recorded = {"namespace": _normalize_namespace(recorded["namespace"])}
        if "namespace" in recorded and "namespace" in actual:
            if recorded["namespace"] != actual["namespace"]:
                failures.append(f"case {index} argv={argv}: namespace differs")
        elif "error" in recorded and "error" in actual:
            if recorded["error"]["exit"] != actual["error"]["exit"] or \
                    recorded["error"]["first_line"] != actual["error"]["first_line"]:
                failures.append(
                    f"case {index} argv={argv}: error differs "
                    f"(want {recorded['error']['exit']} "
                    f"{recorded['error']['first_line']!r}, got "
                    f"{actual['error']['exit']} {actual['error']['first_line']!r})")
        else:
            failures.append(f"case {index} argv={argv}: success/error differs")
        if len(failures) >= 10:
            break
    assert not failures, f"{FIX}\n" + "\n".join(failures)


def test_capability_schema_check_passes():
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import generate_capability_schemas
    finally:
        del sys.path[0]
    assert generate_capability_schemas.main(["--check"]) == 0, FIX
