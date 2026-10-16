"""S14 --json everywhere: (b) additions are only the no-op flag.

SPEC 9.4 classifies every subcommand: (a) already has --json, (b) lacks it
with JSON-by-default success output, (c) lacks it with human-text output.
Amendment (t) approves each (b) change as a paired ``cli.<subcommand>`` +
``request_schemas.<file>`` entry (plan_ref PLAN D16). The (c) commands
(``generate``, ``validate``) are NEEDS-DECISION and keep no flag.

Amendment (bb): approvals are single-use (SPEC 2.3 step 4). Only the D16
entries that are new relative to the ratchet base (``$LOS_RATCHET_BASE``,
default ``main``) still authorize their diff; consumed entries assert
nothing further. Hence, against the base:
- the surface entry and request-schema file "only the ``json`` item" checks
  apply to new entries only (vacuous when none are new);
- the partition classifies a subcommand as (b) when its D16 approval is
  new, as (a) when it has --json at the base, keeping (c) as before;
- the flag-parses and no-handler-reads checks apply to every D16-approved
  subcommand, new or consumed.
"""

from __future__ import annotations

import ast
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import arch_surface
import pytest
import yaml
from arch_schema_deltas import (
    _strip_approved_owner_metadata,
    _strip_bf_description_updates,
)
from repo_builders import run_los

import los

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "tests/architecture"
REQUESTS_DIR = ROOT / "system/schema/requests"
APPROVALS_PATH = ARCH / "surface-approvals.yaml"
CORPUS_PATH = ARCH / "cli-parity-corpus.json"

BASE_ENV = "LOS_RATCHET_BASE"
DEFAULT_BASE = "main"

#: Amendment (bb) proof contexts: accepted S13 Core (pre-D16: every D16
#: approval is new) and accepted S14 Core (post-D16: none is new).
S13_BASE = "4f7628e38acb3b35d13b0cb80a07b9f20f382b68"
S14_BASE = "e437c2783fd37933ab9ddf61cc3514aacb84656e"

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


def _git_show_optional(base: str, relpath: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{base}:{relpath}"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        return None
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


def _new_d16_approvals(base: str) -> tuple[dict[str, str], dict[str, str]]:
    """D16 approvals new relative to ``base`` (amendment (bb), single-use).

    A live D16 entry is new when its whole entry is absent from the base's
    ``surface-approvals.yaml`` (SPEC 2.3 step 4). A base without the file
    has seen none of them, so all are new.
    """
    cli, schemas = _d16_approvals()
    base_text = _git_show_optional(base, "tests/architecture/surface-approvals.yaml")
    if base_text is None:
        return dict(cli), dict(schemas)
    base_entries = {
        json.dumps(entry, sort_keys=True)
        for entry in yaml.safe_load(base_text).get("approvals", [])
    }
    live = yaml.safe_load(APPROVALS_PATH.read_text(encoding="utf-8"))
    new_keys = set()
    for entry in live.get("approvals", []):
        if entry.get("plan_ref") != D16_PLAN_REF:
            continue
        if json.dumps(entry, sort_keys=True) not in base_entries:
            new_keys.add(entry["key"])
    new_cli = {key: sub for key, sub in cli.items() if key in new_keys}
    new_schemas = {key: fname for key, fname in schemas.items()
                   if key in new_keys}
    return new_cli, new_schemas


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


def _assert_only_json_added_to_surface_entries(
        base_flat: dict, live_flat: dict, new_cli: dict[str, str]) -> None:
    """New (b) surface entries gain only the no-op flag (else vacuous)."""
    for key in sorted(new_cli):
        assert key in base_flat and key in live_flat, key
        old = {json.dumps(a, sort_keys=True) for a in base_flat[key]}
        new = {json.dumps(a, sort_keys=True) for a in live_flat[key]}
        assert old < new, f"{key}: not a pure addition"
        assert new - old == {json.dumps(JSON_ACTION, sort_keys=True)}, key


def _surface_flats(base: str) -> tuple[dict, dict]:
    base_doc = json.loads(_git_show(base, "tests/architecture/surface.json"))
    live_doc = json.loads((ARCH / "surface.json").read_text(encoding="utf-8"))
    return arch_surface.flatten_surface(base_doc), arch_surface.flatten_surface(live_doc)


def test_only_json_added_to_surface_entries():
    base = _base()
    new_cli, _ = _new_d16_approvals(base)
    base_flat, live_flat = _surface_flats(base)
    _assert_only_json_added_to_surface_entries(base_flat, live_flat, new_cli)


def _assert_cli_command_only_handler_rebound(key: str, fname: str,
                                             old_cmd: dict, new_cmd: dict) -> None:
    """A converted operation rebinds only its handler line (amendment (u)).

    Every other ``x-los-cli-command`` field must still match; the new
    handler must be exactly the invoke binding for a registered operation,
    so a smuggled change on an unconverted operation still fails.
    """
    if new_cmd == old_cmd:
        return
    assert set(new_cmd) == set(old_cmd), (key, set(new_cmd) ^ set(old_cmd))
    for field in old_cmd:
        if field != "handler":
            assert new_cmd[field] == old_cmd[field], (key, field)
    operation = fname.removesuffix(".schema.json")
    import learning_os.app.handlers  # noqa: F401  (registration side effect)
    from learning_os.app.registry import REGISTRY

    if operation == "cli.capability":
        assert new_cmd["handler"] == "learning_os.adapters.capability.cmd_capability", (key, new_cmd)
        return  # SPEC (cx) D9: the transport facade belongs to its adapter.
    assert operation in REGISTRY, (key, operation)
    assert new_cmd["handler"] == f"learning_os.adapters.cli.invoke:{operation}", (
        key, new_cmd["handler"])


def _assert_only_json_added_to_request_schemas(
        base: str, new_schemas: dict[str, str]) -> None:
    """New (b) request schemas gain only the ``json`` property (else vacuous).

    SPEC (bf) item 7: the request-schema comparison first applies the two
    existing strips (the (ay) owner metadata and the (bf) item 1
    descriptions) to ``(old, new)`` before any comparison.
    """
    for key in sorted(new_schemas):
        fname = new_schemas[key]
        rel = f"system/schema/requests/{fname}"
        operation = fname.removesuffix(".schema.json")
        old = json.loads(_git_show(base, rel))
        new = json.loads((REQUESTS_DIR / fname).read_text(encoding="utf-8"))
        old, new = _strip_approved_owner_metadata(operation, old, new)
        old, new = _strip_bf_description_updates(operation, old, new)
        assert set(new) == set(old), (key, set(new) ^ set(old))
        for top in old:
            if top == "x-los-cli-command":
                _assert_cli_command_only_handler_rebound(key, fname, old[top], new[top])
            elif top != "properties":
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


def test_only_json_added_to_request_schemas():
    base = _base()
    _, new_schemas = _new_d16_approvals(base)
    _assert_only_json_added_to_request_schemas(base, new_schemas)


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


def _assert_b_subcommands_accept_json_with_only_that_delta(
        cli: dict[str, str]) -> None:
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


def test_b_subcommands_accept_json_with_only_that_delta():
    cli, _ = _d16_approvals()
    _assert_b_subcommands_accept_json_with_only_that_delta(cli)


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


def _assert_no_b_handler_reads_the_json_flag(cli: dict[str, str]) -> None:
    """The (b) no-op proof: the only namespace delta is an unread attribute.

    A handler is a pure function of (namespace, filesystem). The parse
    check shows --json changes only the ``json`` attribute; this shows no
    (b) handler closure reads it (directly, via getattr, or via vars()/dict
    introspection), so success output cannot differ with the flag.
    """
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


def test_no_b_handler_reads_the_json_flag():
    cli, _ = _d16_approvals()
    _assert_no_b_handler_reads_the_json_flag(cli)


def _assert_every_subcommand_is_a_b_or_c(base: str, new_cli: dict[str, str]) -> None:
    """Closed world: (b) is new, (a) has the flag at the base, (c) is kept."""
    b = set(new_cli.values())
    parser = _parser()
    choices = _subcommands(parser)
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


def test_every_subcommand_is_a_b_or_c():
    base = _base()
    new_cli, _ = _new_d16_approvals(base)
    _assert_every_subcommand_is_a_b_or_c(base, new_cli)


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


def test_s13_base_marks_every_d16_approval_new():
    """Amendment (bb) context 1: at accepted S13 all 53 approvals are new."""
    new_cli, new_schemas = _new_d16_approvals(S13_BASE)
    assert len(new_cli) == 53, len(new_cli)
    assert len(new_schemas) == 53, len(new_schemas)
    base_flat, live_flat = _surface_flats(S13_BASE)
    _assert_only_json_added_to_surface_entries(base_flat, live_flat, new_cli)
    _assert_only_json_added_to_request_schemas(S13_BASE, new_schemas)
    _assert_every_subcommand_is_a_b_or_c(S13_BASE, new_cli)
    cli, _ = _d16_approvals()
    _assert_b_subcommands_accept_json_with_only_that_delta(cli)
    _assert_no_b_handler_reads_the_json_flag(cli)


def test_s14_base_marks_no_d16_approval_new():
    """Amendment (bb) context 2: at accepted S14 none is new; all pass."""
    new_cli, new_schemas = _new_d16_approvals(S14_BASE)
    assert new_cli == {}, new_cli
    assert new_schemas == {}, new_schemas
    base_flat, live_flat = _surface_flats(S14_BASE)
    _assert_only_json_added_to_surface_entries(base_flat, live_flat, new_cli)
    _assert_only_json_added_to_request_schemas(S14_BASE, new_schemas)
    _assert_every_subcommand_is_a_b_or_c(S14_BASE, new_cli)
    cli, _ = _d16_approvals()
    _assert_b_subcommands_accept_json_with_only_that_delta(cli)
    _assert_no_b_handler_reads_the_json_flag(cli)


def test_mutated_surface_entry_for_a_new_approval_still_fails():
    """Amendment (bb) negative: an extra option on a new approval fails."""
    new_cli, _ = _new_d16_approvals(S13_BASE)
    assert new_cli, "S13 context must leave new approvals to mutate"
    key = sorted(new_cli)[0]
    base_flat, live_flat = _surface_flats(S13_BASE)
    mutated = copy.deepcopy(live_flat)
    extra = dict(JSON_ACTION)
    extra["option_strings"] = ["--json-extra"]
    extra["dest"] = "json_extra"
    mutated[key] = [*mutated[key], extra]
    with pytest.raises(AssertionError):
        _assert_only_json_added_to_surface_entries(base_flat, mutated, new_cli)


def test_other_property_change_on_a_converted_pilot_still_fails(
        tmp_path, monkeypatch):
    """SPEC (bf) item 7 negative: the strips excuse nothing else.

    In the S13 context, any other property change on a converted pilot
    (here ``route.patch``: an added keyword beside the stripped
    description) still fails the request-schema comparison.
    """
    key = "request_schemas.route.patch.schema.json"
    _, new_schemas = _new_d16_approvals(S13_BASE)
    assert key in new_schemas, "route.patch must be a new D16 approval at S13"
    live = json.loads(
        (REQUESTS_DIR / "route.patch.schema.json").read_text(encoding="utf-8"))
    live["properties"]["unit_id"]["minLength"] = 1
    shadow = tmp_path / "requests"
    shadow.mkdir()
    (shadow / "route.patch.schema.json").write_text(
        json.dumps(live), encoding="utf-8")
    monkeypatch.setattr("test_arch_json_everywhere.REQUESTS_DIR", shadow)
    with pytest.raises(AssertionError):
        _assert_only_json_added_to_request_schemas(S13_BASE, {key: new_schemas[key]})
