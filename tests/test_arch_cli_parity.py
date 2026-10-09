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


#: SPEC (bf) item 1: pilot (subcommand, dest) pairs whose baseline help
#: (None: the placeholder suppresses help) normalizes to the live
#: request-schema description, as (u) item 2 does for handler bindings.
BF_HELP_PAIRS: dict[str, set[str]] = {
    "route-patch": {"unit_id", "route_id", "changes", "check",
                    "expected_snapshot"},
    "stage-progress": {"unit_id", "stage_id", "status",
                       "expected_snapshot"},
    "ai-action-apply-delivery": {"delivery_id", "expected_snapshot"},
    "inspect": {"id"},
}

#: The request-schema operation behind each normalized subcommand.
_BF_HELP_OPERATIONS: dict[str, str] = {
    "route-patch": "route.patch",
    "stage-progress": "stage.progress.update",
    "ai-action-apply-delivery": "ai-action.delivery.apply",
    "inspect": "cli.inspect",
}


def _normalize_bf_help(expected: dict) -> dict:
    """Baseline help at exactly the (bf) pairs becomes the live text."""
    normalized = copy.deepcopy(expected)
    for subcommand, dests in BF_HELP_PAIRS.items():
        operation = _BF_HELP_OPERATIONS[subcommand]
        doc = json.loads((REQUESTS_DIR / f"{operation}.schema.json")
                         .read_text(encoding="utf-8"))
        assert doc["x-los-cli-command"]["name"] == subcommand, subcommand
        properties = doc.get("properties", {})
        for action in normalized["subparsers"][subcommand]["actions"]:
            if action["dest"] in dests:
                action["help"] = properties[action["dest"]]["description"]
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
    if normalized["parser_class"] == "learning_os.adapters.cli_parser._LosArgumentParser":
        normalized["parser_class"] = "los._LosArgumentParser"
    for sub in normalized.get("subparsers", {}).values():
        defaults = sub.get("defaults", {})
        if defaults.get("_parser_factory") == "learning_os.adapters.cli_parser.build_parser":
            defaults["_parser_factory"] = "los.build_parser"
    return normalized


def test_only_the_documented_relocation_normalizes():
    """SPEC (ap): arbitrary class/factory changes fail the real comparison."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    expected = _normalize_describe(baseline)
    # Positive control: the exact relocation maps onto the old bytes.
    moved = copy.deepcopy(baseline)
    moved["parser_class"] = (
        "learning_os.adapters.cli_parser._LosArgumentParser")
    for sub in moved["subparsers"].values():
        if "_parser_factory" in sub.get("defaults", {}):
            sub["defaults"]["_parser_factory"] = (
                "learning_os.adapters.cli_parser.build_parser")
    assert _normalize_describe(moved) == expected
    # Arbitrary changes survive normalization, so the comparison fails.
    for parser_class in ("argparse.ArgumentParser",
                         "learning_os.adapters.cli_parser.Parser",
                         "los.ArgumentParser"):
        wrong = copy.deepcopy(baseline)
        wrong["parser_class"] = parser_class
        assert _normalize_describe(wrong)["parser_class"] == parser_class
        assert _normalize_describe(wrong) != expected
    name = next(iter(baseline["subparsers"]))
    for factory in ("other.build_parser",
                    "learning_os.adapters.cli_parser.build_parser2",
                    "x.learning_os.adapters.cli_parser.build_parser"):
        wrong = copy.deepcopy(baseline)
        wrong["subparsers"][name].setdefault("defaults", {})[
            "_parser_factory"] = factory
        normalized = _normalize_describe(wrong)
        assert normalized["subparsers"][name]["defaults"][
            "_parser_factory"] == factory
        assert normalized != expected


def test_namespace_normalization_accepts_only_the_exact_factory():
    assert _normalize_namespace(
        {"_parser_factory":
         "learning_os.adapters.cli_parser.build_parser"}) == \
        {"_parser_factory": "los.build_parser"}
    # The old bytes and anything else pass through untouched.
    for factory in ("los.build_parser", "other.build_parser",
                    "learning_os.adapters.cli_parser.build_parser2"):
        assert _normalize_namespace(
            {"command": "inspect",
             "_parser_factory": factory}) == {
                 "command": "inspect", "_parser_factory": factory}


def test_registered_normalization_with_invoke_binding_and_root_options(
        tmp_path, monkeypatch):
    """Future (u) rule against an actual synthetic invoke binding.

    Root options precede the subcommand, so the first non-dash token is
    the root value, not the subcommand: selection must use the recorded
    namespace's ``command``. Every unrelated value is kept.
    """
    directory = tmp_path / "requests"
    directory.mkdir()
    (directory / "cli.inspect.schema.json").write_text(json.dumps({
        "x-los-cli-command": {
            "name": "inspect",
            "handler": "learning_os.adapters.cli.invoke:cli.inspect",
        },
    }), encoding="utf-8")
    monkeypatch.setattr("test_arch_cli_parity.REQUESTS_DIR", directory)
    argv = ["--root", "/tmp/x", "inspect", "note-demo"]
    recorded = {"namespace": {
        "command": "inspect", "id": "note-demo",
        "func": "learning_os.commands.query.cmd_inspect",
        "_parser_factory": "los.build_parser", "root": "/tmp/x",
    }}
    naive_first_token = next(
        token for token in argv if not token.startswith("-"))
    assert naive_first_token == "/tmp/x"
    subcommand = recorded.get("namespace", {}).get("command")
    assert subcommand == "inspect"
    handler = _handler_for_subcommand(subcommand)
    assert handler == "learning_os.adapters.cli.invoke:cli.inspect"
    normalized = _normalize_registered_namespace(
        _normalize_namespace(recorded["namespace"]), handler)
    assert normalized == {
        "command": "inspect", "id": "note-demo",
        "func": "learning_os.adapters.cli.invoke",
        "_operation": "cli.inspect",
        "_parser_factory": "los.build_parser", "root": "/tmp/x",
    }
    normalized_defaults = _normalize_registered_defaults(
        {"func": "learning_os.commands.query.cmd_inspect",
         "_parser_factory": "los.build_parser"}, handler)
    assert normalized_defaults == {
        "func": "learning_os.adapters.cli.invoke",
        "_operation": repr("cli.inspect"),
        "_parser_factory": "los.build_parser",
    }


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
    # SPEC (bf) item 1: pilot descriptions became argparse help.
    expected = _normalize_bf_help(expected)
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


def test_bf_help_normalization_touches_only_the_listed_pairs():
    """A help change anywhere else still fails the gate (SPEC (bf) 1)."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    normalized = _normalize_bf_help(baseline)
    changed = []
    for subcommand, sub in baseline["subparsers"].items():
        live_doc = None
        if subcommand in BF_HELP_PAIRS:
            operation = _BF_HELP_OPERATIONS[subcommand]
            live_doc = json.loads(
                (REQUESTS_DIR / f"{operation}.schema.json")
                .read_text(encoding="utf-8"))
        norm_actions = normalized["subparsers"][subcommand]["actions"]
        for base_action, norm_action in zip(sub["actions"], norm_actions,
                                                 strict=True):
            listed = (subcommand in BF_HELP_PAIRS
                      and base_action["dest"] in BF_HELP_PAIRS[subcommand])
            if listed:
                want = live_doc["properties"][base_action["dest"]][
                    "description"]
                assert norm_action["help"] == want, (
                    subcommand, base_action["dest"])
                assert norm_action["help"] != base_action["help"], (
                    subcommand, base_action["dest"])
                rest_base = {k: v for k, v in base_action.items()
                             if k != "help"}
                rest_norm = {k: v for k, v in norm_action.items()
                             if k != "help"}
                assert rest_norm == rest_base, (
                    subcommand, base_action["dest"])
                changed.append((subcommand, base_action["dest"]))
            else:
                assert norm_action == base_action, (
                    subcommand, base_action["dest"])
    assert sorted(changed) == sorted(
        (sub, dest) for sub, dests in BF_HELP_PAIRS.items()
        for dest in dests), changed
    assert len(changed) == 12, changed


def _normalize_namespace(namespace: dict) -> dict:
    normalized = dict(namespace)
    for key, value in list(normalized.items()):
        if key == "_parser_factory" and value == "learning_os.adapters.cli_parser.build_parser":
            normalized[key] = "los.build_parser"
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
                return {"error": {"exit": code, "first_line": first,
                                  "stderr": stderr},
                        "stdout": stdout_buf.getvalue()}
    data = dict(vars(namespace))
    for key, value in list(data.items()):
        if callable(value):
            module = getattr(value, "__module__", "") or ""
            qualname = getattr(value, "__qualname__", "") \
                or getattr(value, "__name__", "")
            data[key] = f"{module}.{qualname}" if module else str(qualname)
    return {"namespace": _normalize_namespace(data),
            "stdout": stdout_buf.getvalue()}


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
        subcommand = recorded.get("namespace", {}).get("command")
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
            if recorded["error"].get("stderr") != actual["error"]["stderr"]:
                failures.append(f"case {index} argv={argv}: full stderr differs")
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


def test_actual_old_source_supplement_parity():
    """Additional old-source observations retain full stdout and stderr."""
    import los

    corpus = json.loads((ROOT / "tests/architecture/cli-parity-supplement.json")
                        .read_text(encoding="utf-8"))
    assert sum(row["count"] for row in corpus["sources"].values()) == 265
    assert len(corpus["cases"]) == 265
    parser = los.build_parser()
    for row in corpus["cases"]:
        recorded = copy.deepcopy(row["result"])
        if "namespace" in recorded:
            namespace = _normalize_namespace(recorded["namespace"])
            handler = _handler_for_subcommand(namespace.get("command"))
            if handler and handler.startswith("learning_os.adapters.cli.invoke:"):
                namespace = _normalize_registered_namespace(namespace, handler)
            recorded["namespace"] = namespace
        assert _run(parser, row["argv"]) == recorded, row["source"]
