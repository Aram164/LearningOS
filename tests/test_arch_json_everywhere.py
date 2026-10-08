"""S14 --json everywhere: (b) additions are only the no-op flag.

SPEC 9.4 classifies every subcommand: (a) already has --json, (b) lacks it
with JSON-by-default success output, (c) lacks it with human-text output.
Amendment (t) approves each (b) change as a paired ``cli.<subcommand>`` +
``request_schemas.<file>`` entry (plan_ref PLAN D16). The (c) commands
(``generate``, ``validate``) are NEEDS-DECISION and keep no flag.

These tests derive the (b) set from the D16 approvals and prove, against the
ratchet base (``$LOS_RATCHET_BASE``, default ``main``):
- the surface entry and request-schema file each gain only the ``json`` item;
- the flag parses on every (b) command with namespace delta exactly ``json``;
- no (b) handler reads that attribute, so success output is byte-identical;
- every other subcommand is (a) or (c): the partition is closed.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import arch_surface
import yaml
from repo_builders import run_los

import los

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "tests/architecture"
REQUESTS_DIR = ROOT / "system/schema/requests"
APPROVALS_PATH = ARCH / "surface-approvals.yaml"
CORPUS_PATH = ARCH / "cli-parity-corpus.json"

BASE_ENV = "LOS_RATCHET_BASE"
DEFAULT_BASE = "main"

D16_PLAN_REF = "PLAN D16"
D16_APPROVED_BY = "Aram 2026-10-03: accepted PLAN revision 4"

#: SPEC 9.4 (c): human-text success output; NEEDS-DECISION, no flag.
C_SUBCOMMANDS = frozenset({"generate", "validate"})

#: The surface form of the no-op flag (arch_surface action description).
JSON_ACTION = {
    "action": "store_true",
    "choices": None,
    "default_repr": "False",
    "dest": "json",
    "metavar": None,
    "nargs": 0,
    "option_strings": ["--json"],
    "required": False,
    "type": None,
}


def _git_show(base: str, relpath: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{base}:{relpath}"],
        capture_output=True, text=True)
    assert proc.returncode == 0, f"no {relpath} at base {base}"
    return proc.stdout


def _base() -> str:
    return os.environ.get(BASE_ENV, DEFAULT_BASE)


def _d16_approvals() -> tuple[dict[str, str], dict[str, str]]:
    """(cli.<sub> -> sub, request_schemas.<file> -> file) for PLAN D16."""
    data = yaml.safe_load(APPROVALS_PATH.read_text(encoding="utf-8"))
    cli: dict[str, str] = {}
    schemas: dict[str, str] = {}
    for entry in data.get("approvals", []):
        if entry.get("plan_ref") != D16_PLAN_REF:
            continue
        assert entry.get("change") == "changed", entry
        assert entry.get("pre_approved_by") == D16_APPROVED_BY, entry
        key = entry["key"]
        if key.startswith("cli."):
            cli[key] = key[len("cli."):]
        elif key.startswith("request_schemas."):
            schemas[key] = key[len("request_schemas."):]
        else:  # pragma: no cover
            raise AssertionError(f"D16 approval outside cli/request_schemas: {key}")
    assert cli, "no D16 cli.* approvals: (b) set would be vacuous"
    return cli, schemas


def _parser():
    return los.build_parser()


def _subcommands(parser) -> dict:
    for action in parser._actions:
        if type(action).__name__ == "_SubParsersAction":
            return action.choices
    raise AssertionError("no subparsers action")


def _schema_for_subcommand(subcommand: str) -> tuple[str, dict]:
    """(file name, live document) governing ``subcommand``."""
    for path in sorted(REQUESTS_DIR.glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cmd = data.get("x-los-cli-command") or {}
        if cmd.get("name") == subcommand:
            return path.name, data
    raise AssertionError(f"no request schema governs {subcommand}")


def test_d16_approvals_pair_cli_with_governing_schema():
    cli, schemas = _d16_approvals()
    assert len(cli) == len(schemas), (len(cli), len(schemas))
    for key, sub in sorted(cli.items()):
        assert sub not in C_SUBCOMMANDS, sub
        fname, _ = _schema_for_subcommand(sub)
        assert f"request_schemas.{fname}" in schemas, (key, fname)
    governed = {key for key in schemas if key.endswith(".schema.json")}
    assert governed == set(schemas), set(schemas) - governed
    for key, fname in sorted(schemas.items()):
        data = json.loads((REQUESTS_DIR / fname).read_text(encoding="utf-8"))
        cmd = data.get("x-los-cli-command") or {}
        assert f"cli.{cmd.get('name')}" in cli, key


def test_only_json_added_to_surface_entries():
    cli, _ = _d16_approvals()
    base = json.loads(_git_show(_base(), "tests/architecture/surface.json"))
    live = json.loads((ARCH / "surface.json").read_text(encoding="utf-8"))
    base_flat = arch_surface.flatten_surface(base)
    live_flat = arch_surface.flatten_surface(live)
    for key in sorted(cli):
        assert key in base_flat and key in live_flat, key
        old = {json.dumps(a, sort_keys=True) for a in base_flat[key]}
        new = {json.dumps(a, sort_keys=True) for a in live_flat[key]}
        assert old < new, f"{key}: not a pure addition"
        assert new - old == {json.dumps(JSON_ACTION, sort_keys=True)}, key


def test_only_json_added_to_request_schemas():
    _, schemas = _d16_approvals()
    for key in sorted(schemas):
        fname = schemas[key]
        rel = f"system/schema/requests/{fname}"
        old = json.loads(_git_show(_base(), rel))
        new = json.loads((REQUESTS_DIR / fname).read_text(encoding="utf-8"))
        assert set(new) == set(old), (key, set(new) ^ set(old))
        for top in old:
            if top != "properties":
                assert new[top] == old[top], (key, top)
        assert set(new["properties"]) == set(old["properties"]) | {"json"}, key
        for prop in old["properties"]:
            assert new["properties"][prop] == old["properties"][prop], (key, prop)
        assert "json" not in new.get("required", []), key
        fragment = new["properties"]["json"]
        assert fragment["type"] == "boolean", key
        assert fragment["description"] == "no-op: this command always prints JSON", key
        x = fragment["x-los-cli"]
        assert x["flags"] == ["--json"], key
        assert x["action"] == "store_true" and x["default"] is False, key
        assert x["const"] is True and x["nargs"] == 0, key
        assert x["transport_only"] is True and x["envelope_owned"] is False, key
        assert x["required"] is False and x["stdin"] is False, key


def _corpus_success_argv() -> dict[str, list[str]]:
    """First success-case argv per subcommand, from the parity corpus."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for case in corpus["cases"]:
        result = case["result"]
        if "namespace" not in result:
            continue
        sub = result["namespace"].get("command")
        if sub is not None and sub not in out:
            out[sub] = case["argv"]
    return out


def test_b_subcommands_accept_json_with_only_that_delta():
    cli, _ = _d16_approvals()
    parser = _parser()
    argv_by_sub = _corpus_success_argv()
    for key in sorted(cli):
        sub = cli[key]
        argv = argv_by_sub[sub]
        assert "--json" not in argv, (sub, argv)
        flagged = list(argv)
        flagged.insert(argv.index(sub) + 1, "--json")
        want = parser.parse_args(argv)
        got = parser.parse_args(flagged)
        assert got.json is True, sub
        assert vars(got) == {**vars(want), "json": True}, sub


def _closure_source(module_path: Path, func_name: str) -> list[tuple[str, object]]:
    """(function name, AST node) for a handler and its same-module callees."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert func_name in funcs, (module_path, func_name)
    seen: set[str] = set()
    stack = [func_name]
    out: list[tuple[str, object]] = []
    while stack:
        current = stack.pop()
        if current in seen or current not in funcs:
            continue
        seen.add(current)
        node = funcs[current]
        out.append((current, node))
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in funcs and child.func.id != current:
                    stack.append(child.func.id)
    return out


def test_no_b_handler_reads_the_json_flag():
    """The (b) no-op proof: the only namespace delta is an unread attribute.

    A handler is a pure function of (namespace, filesystem). The previous
    test shows --json changes only the ``json`` attribute; this test shows no
    (b) handler closure reads it (directly, via getattr, or via vars()/dict
    introspection), so success output cannot differ with the flag.
    """
    cli, _ = _d16_approvals()
    parser = _parser()
    choices = _subcommands(parser)
    for key in sorted(cli):
        sub = cli[key]
        func = choices[sub].get_default("func")
        module = sys.modules[func.__module__]
        path = Path(module.__file__)
        assert path.is_relative_to(ROOT / "tools"), (sub, path)
        for func_name, node in _closure_source(path, func.__name__):
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and child.attr == "json":
                    raise AssertionError(
                        f"{sub}: {func_name} reads .json "
                        f"({path.name}:{child.lineno})")
                if isinstance(child, ast.Attribute) and child.attr == "__dict__":
                    raise AssertionError(
                        f"{sub}: {func_name} reads __dict__ "
                        f"({path.name}:{child.lineno})")
                if isinstance(child, ast.Call) and getattr(
                        child.func, "id", "") == "getattr" and len(child.args) >= 2:
                    name = child.args[1]
                    if isinstance(name, ast.Constant) and name.value == "json":
                        raise AssertionError(
                            f"{sub}: {func_name} getattr(..., 'json') "
                            f"({path.name}:{child.lineno})")
                if isinstance(child, ast.Call) and getattr(
                        child.func, "id", "") == "vars":
                    raise AssertionError(
                        f"{sub}: {func_name} calls vars() "
                        f"({path.name}:{child.lineno})")


def test_every_subcommand_is_a_b_or_c():
    """Closed world: no subcommand silently gains or misses the flag."""
    cli, _ = _d16_approvals()
    b = set(cli.values())
    parser = _parser()
    choices = _subcommands(parser)
    base = _base()
    for sub in sorted(choices):
        subparser = choices[sub]
        fname, live = _schema_for_subcommand(sub)
        has_flag = "--json" in subparser._option_string_actions
        if has_flag:
            assert "json" in live["properties"], sub
            base_doc = json.loads(_git_show(base, f"system/schema/requests/{fname}"))
            had = "json" in base_doc["properties"]
            assert had != (sub in b), f"{sub}: had={had} b={sub in b}"
        else:
            assert sub in C_SUBCOMMANDS, f"{sub}: jsonless and not (c)"
            assert "json" not in live["properties"], sub
            assert sub not in b, sub


def test_json_flag_keeps_b_success_bytes_identical(mini_repo, tmp_path):
    """Live sample: session-end, the (b) command with passthrough output.

    session-end echoes subprocess stdout on failure paths; both runs take the
    JSON-only success path, in twin fixtures so the first run's publish
    cannot perturb the second.
    """
    from conftest import build_mini_repo

    second = build_mini_repo(tmp_path / "twin")
    plain = run_los(mini_repo, "session-end")
    flagged = run_los(second, "session-end", "--json")
    assert plain.returncode == 0, plain.stderr
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout
    assert flagged.stderr == plain.stderr
