"""Build the frozen CLI/catalog surface snapshot (PLAN A11, A17).

The snapshot shape is fixed by SPEC §3.3 A11 and §3.4 A17; the flattening of the snapshot
into approval keys is fixed by the S01 kickoff. This module holds the builder
plus the shared flatten/diff/approval helpers used by ``test_arch_surface.py``
(current snapshot matches the live code) and ``test_arch_ratchets.py`` (every
diff against the base carries an approval).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import inspect
import json
import sys
from pathlib import Path

import yaml

ARCHITECTURE_DIR = "tests/architecture"
SURFACE_FILENAME = "surface.json"
APPROVALS_FILENAME = "surface-approvals.yaml"
RATCHETS_FILENAME = "ratchets.yaml"

#: The one tools entrypoint in the SPEC §3.3 surface shape.
SURFACE_TOOLS = ("seal_envelope.py",)

#: Conventional names for the argparse actions the surface records. Anything
#: outside this table falls back to the action class name, so a new action
#: kind can never silently merge with an old one.
_ACTION_NAMES = {
    "_StoreAction": "store",
    "_StoreConstAction": "store_const",
    "_StoreTrueAction": "store_true",
    "_StoreFalseAction": "store_false",
    "_AppendAction": "append",
    "_AppendConstAction": "append_const",
    "_CountAction": "count",
    "_HelpAction": "help",
    "_VersionAction": "version",
    "_ExtendAction": "extend",
}


def _action_name(action: argparse.Action) -> str:
    return _ACTION_NAMES.get(type(action).__name__, type(action).__name__)


def _choices(action: argparse.Action) -> list | None:
    if action.choices is None:
        return None
    values = list(action.choices)
    try:
        return sorted(values)
    except TypeError:
        return values


def _action_shape(action: argparse.Action) -> dict:
    """One SPEC §3.3 option record. Help text is deliberately not recorded."""
    metavar = action.metavar
    if isinstance(metavar, tuple):
        metavar = list(metavar)
    return {
        "option_strings": sorted(action.option_strings),
        "dest": action.dest,
        "nargs": action.nargs,
        "required": bool(action.required),
        "default_repr": repr(action.default),
        "choices": _choices(action),
        "action": _action_name(action),
        "metavar": metavar,
        "type": action.type.__name__ if action.type is not None else None,
    }


def _parser_options(parser: argparse.ArgumentParser) -> list[dict]:
    """Every action of one parser except the subcommand dispatcher itself."""
    shapes = [
        _action_shape(action)
        for action in parser._actions
        if not isinstance(action, argparse._SubParsersAction)
    ]
    shapes.sort(key=lambda e: (e["option_strings"], e["dest"]))
    return shapes


def build_surface(root: Path | str) -> dict:
    """Build the SPEC §3.3 A11 surface for the repository at ``root``.

    The catalog and request schemas are read from ``root`` on disk. The CLI
    and tools parsers come from the imported ``los`` and ``seal_envelope``
    modules, so callers must run with that root's ``tools/`` on ``sys.path``
    (true whenever pytest runs inside the target checkout).
    """
    root = Path(root)
    catalog_raw = yaml.safe_load(
        (root / "system/contracts/capabilities.yaml").read_text(encoding="utf-8"))
    commands = {
        cid: {
            "handler": entry.get("handler"),
            "cli_command": entry.get("cli_command"),
            "admission": entry.get("admission"),
            "writes": entry.get("writes"),
        }
        for cid, entry in (catalog_raw.get("commands") or {}).items()
    }
    queries = {
        qid: {
            "handler": entry.get("handler"),
            "cli_command": entry.get("cli_command"),
        }
        for qid, entry in (catalog_raw.get("queries") or {}).items()
    }
    domain_capabilities = sorted((catalog_raw.get("domain_capabilities") or {}).keys())
    internal_commands = sorted((catalog_raw.get("internal_commands") or {}).keys())

    import seal_envelope  # noqa: E402  (imports the parser, not a command)

    import los  # noqa: E402  (imports the parser, not a command)
    from learning_os.contracts.payloads import subparsers

    try:
        from learning_os.app.context import OpContext
    except ImportError:
        OpContext = None

    root_parser = los.build_parser()
    cli = {"__root__": _parser_options(root_parser)}
    for name, sub in sorted(subparsers(root_parser).items()):
        cli[name] = _parser_options(sub)
    tools = {
        "seal_envelope.py": _parser_options(seal_envelope.build_parser()),
    }
    assert set(tools) == set(SURFACE_TOOLS)

    request_schemas: dict[str, str] = {}
    requests_dir = root / "system/schema/requests"
    if requests_dir.is_dir():
        for path in sorted(requests_dir.glob("*.schema.json")):
            request_schemas[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

    surface = {
        "catalog": {
            "commands": commands,
            "queries": queries,
            "domain_capabilities": domain_capabilities,
            "internal_commands": internal_commands,
        },
        "cli": cli,
        "tools": tools,
        "request_schemas": request_schemas,
    }
    if OpContext is not None:
        opcontext: dict[str, str] = {}
        for field in dataclasses.fields(OpContext):
            ftype = field.type
            opcontext[field.name] = (
                f"field: {ftype if isinstance(ftype, str) else repr(ftype)}"
            )
        for name, member in vars(OpContext).items():
            if name.startswith("_") or not callable(member):
                continue
            opcontext[name] = f"method: {inspect.signature(member)}"
        surface["opcontext"] = opcontext
    return surface


def flatten_surface(surface: dict) -> dict[str, object]:
    """Flatten a surface into ``key -> JSON value`` per the S01 kickoff."""
    flat: dict[str, object] = {}
    catalog = surface.get("catalog", {})
    for section in ("commands", "queries", "domain_capabilities", "internal_commands"):
        entries = catalog.get(section, {})
        if isinstance(entries, dict):
            for cid, value in entries.items():
                flat[f"catalog.{section}.{cid}"] = value
        else:
            for cid in entries:
                flat[f"catalog.{section}.{cid}"] = cid
    for area in ("cli", "tools", "request_schemas"):
        for name, value in surface.get(area, {}).items():
            flat[f"{area}.{name}"] = value
    for name, value in surface.get("opcontext", {}).items():
        flat[f"opcontext.{name}"] = value
    return flat


def diff_keys(base: dict[str, object], current: dict[str, object]) -> dict[str, str]:
    """Map each differing flattened key to added | removed | changed."""
    diff: dict[str, str] = {}
    for key in base.keys() | current.keys():
        if key not in current:
            diff[key] = "removed"
        elif key not in base:
            diff[key] = "added"
        elif base[key] != current[key]:
            diff[key] = "changed"
    return diff


def approval_covers(approval: dict, key: str, change: str) -> bool:
    """Whether one surface-approvals.yaml entry covers a diff (SPEC §2.2)."""
    pattern = approval.get("key", "")
    if pattern.endswith(".*"):
        covered = key.startswith(pattern[:-1])
    else:
        covered = key == pattern
    return covered and approval.get("change") == change


def dump_surface(surface: dict) -> str:
    """The canonical on-disk form: sorted keys, indent 1, trailing newline."""
    return json.dumps(surface, indent=1, sort_keys=True) + "\n"


def locate_line(text: str, key: str) -> int:
    """First JSON line mentioning the key's entry, for failure messages."""
    parts = key.split(".")
    for start in range(1, len(parts)):
        needle = json.dumps(".".join(parts[start:]))
        for lineno, line in enumerate(text.splitlines(), 1):
            if needle in line:
                return lineno
    return 1


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    tools_dir = str(root / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    surface = build_surface(root)
    path = root / ARCHITECTURE_DIR / SURFACE_FILENAME
    path.write_text(dump_surface(surface), encoding="utf-8")
    print(f"wrote {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
