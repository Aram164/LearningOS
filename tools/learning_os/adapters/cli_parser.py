"""Generated CLI parser from request schemas (PLAN D2)."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

from learning_os.adapters.cli_types import CONVERTERS

_LOS_DESCRIPTION = """Learning OS CLI — the stable machine gateway for interface layers (ADR-006).

Agents start here (system/OPERATOR.md):

    .venv/bin/python tools/los.py capabilities --compact --json  # what exists
    .venv/bin/python tools/los.py bootstrap --brief              # session entry, one page
    .venv/bin/python tools/los.py capabilities NAME --json       # one capability + payload schema
    .venv/bin/python tools/los.py inspect ID [ID ...]            # records, one fresh projection
    .venv/bin/python tools/los.py status                         # one-screen repository state

`bootstrap` without --brief/--compact prints the complete projection
(megabytes): a bulk read, never a session start.

Every canonical write is a capability applied as a GatewayEnvelopeV2 through
`capability NAME --payload-file ENVELOPE.json` (WORKFLOWS §25c). Run bare, a
named write command only preflights (`--check`) or refuses. `validate` and
`generate` delegate to tools/validate.py and tools/generate.py, so there is
exactly one implementation of every rule.

Interface layers (the Obsidian UI project, scripts, agents) call THESE
commands instead of parsing YAML or reimplementing rules. Exit codes: 0 ok ·
1 validation errors · 2 usage/environment error · 3 optimistic-concurrency
conflict.
"""

# Physical subparser order of the old parser, preserved so `los --help`
# lists subcommands identically. Request schemas carry no order.
_SUBCOMMAND_ORDER = (
    "status",
    "capabilities",
    "bootstrap",
    "material-context",
    "ability-context",
    "material-span",
    "search",
    "intelligence-scan",
    "goal",
    "resume",
    "dossier",
    "semantic",
    "note-read",
    "inbox-read",
    "inbox-list",
    "inspect",
    "projection-observe",
    "related",
    "program-list",
    "plan-template",
    "module-list",
    "unit-list",
    "project-list",
    "capability",
    "validate",
    "generate",
    "ai-action-list",
    "ai-action-prepare",
    "ai-action-append-slices",
    "ai-action-import-delivery",
    "ai-action-validate-delivery",
    "ai-action-apply-delivery",
    "ai-action-status",
    "unit-material-synthesis-publish",
    "legacy-archive-inspect",
    "legacy-archive-status",
    "legacy-archive-lock-publish",
    "masters-planning-dashboard",
    "masters-planning-catalog-update",
    "masters-planning-comparison-publish",
    "health-report",
    "backup-manifest",
    "backup-verify",
    "capture",
    "inbox-resolve",
    "garden-seed-create",
    "atlas-context",
    "concept-relations-change",
    "atlas-question-save",
    "note-analysis-save",
    "note-analysis-save-batch",
    "note-analysis-prepare",
    "plan-edit-context",
    "route-patch",
    "module-materials-compact",
    "unit-map-import",
    "module-plan-import",
    "module-attempt",
    "module-sitting",
    "unit-plan-revise",
    "lineage-restamp",
    "note-create",
    "note-revise",
    "note-evidence",
    "runtime-session",
    "observation-append",
    "stage-result",
    "ability-observation-append",
    "ability-candidate-append",
    "observe",
    "unit-note",
    "unit-source-selection",
    "stage-note",
    "stage-progress",
    "stage-attach",
    "source-feedback",
    "source-intake",
    "collection-entry-revise",
    "collection-create",
    "module-create",
    "program-semester-update",
    "source-revise",
    "detour-create",
    "detour-resolve",
    "shelving-prepare",
    "shelving-apply",
    "session-end",
    "path-note",
    "path-progress",
    "coordination-section-revise",
    "workspace-next-action",
    "path-attach",
    "operations",
)

_PLACEHOLDER_MARK = "(no description in the parser yet)"


def _first_subcommand(choices) -> str | None:
    """The valid subcommand this command line names, if any.

    Skips the root value options (`--root X`, `--lock-timeout X`, in either
    spelling) and every other dash-led token; the first remaining token is
    what argparse itself took as the subcommand position.
    """
    argv = sys.argv[1:]
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in ("--root", "--lock-timeout"):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token if token in choices else None
    return None


class _LosArgumentParser(argparse.ArgumentParser):
    """Root parser that blames the subcommand, not the 93-command list.

    Argparse reports unrecognized arguments at the parser owning the
    subparsers action — the root — so ``los inspect X --bogus`` dumped the
    whole command list before the error. When the command line names a
    valid subcommand, its own usage plus the error is the answer; anything
    else keeps the root usage. Exit code stays 2 either way.
    """

    def error(self, message):
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                name = _first_subcommand(action.choices)
                if name is not None:
                    action.choices[name].error(message)
                break
        super().error(message)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _help_for(description: str | None):
    if description == "==SUPPRESS==":
        return argparse.SUPPRESS
    if description is None or _PLACEHOLDER_MARK in description:
        return None
    return description


def _resolve_handler(dotted: str):
    # Converted operations (SPEC 12 step 4) bind to the invoke adapter.
    if dotted.startswith("learning_os.adapters.cli.invoke:"):
        from learning_os.adapters import cli as cli_adapter

        return cli_adapter.invoke
    module_name, _, qualname = dotted.rpartition(".")
    module = importlib.import_module(module_name)
    target = module
    for part in qualname.split("."):
        target = getattr(target, part)
    return target


def _add_property(target, dest: str, schema: dict) -> None:
    cli = schema["x-los-cli"]
    flags = list(cli["flags"])
    action = cli["action"]
    default = cli["default"]
    if default == "__SUPPRESS__":
        default = argparse.SUPPRESS
    help_value = _help_for(schema.get("description"))
    metavar = cli.get("metavar")
    if isinstance(metavar, list):
        metavar = tuple(metavar)
    kwargs = {"action": action, "default": default, "help": help_value}
    if flags:
        kwargs.update(dest=dest, required=bool(cli["required"]))
    if action in ("store_const", "append_const"):
        kwargs["const"] = cli.get("const")
    elif action not in ("store_true", "store_false", "count"):
        type_name = cli.get("type")
        kwargs.update(nargs=cli.get("nargs"), const=cli.get("const"),
                      type=CONVERTERS[type_name] if type_name is not None else None,
                      choices=cli.get("choices"), metavar=metavar)
    target.add_argument(*(flags or [dest]), **kwargs)


def build_parser() -> argparse.ArgumentParser:
    """The complete CLI surface, generated from request schemas."""
    parser = _LosArgumentParser(
        prog="los", description=_LOS_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--lock-timeout", type=float, default=None,
                        metavar="SECONDS",
                        help="bound the operator-lock wait; on expiry exit 2 "
                             "naming the holder (same as LOS_LOCK_TIMEOUT; "
                             "default: wait as long as needed, announced)")
    sub = parser.add_subparsers(dest="command", required=True)
    requests_dir = _repository_root() / "system/schema/requests"
    by_name: dict[str, tuple[str, dict]] = {}
    for path in sorted(requests_dir.glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cmd = data.get("x-los-cli-command")
        if cmd is None:
            continue
        if cmd["name"] in by_name:
            raise ValueError(f"duplicate CLI binding: {cmd['name']}")
        by_name[cmd["name"]] = (path.name[: -len(".schema.json")], data)
    if set(by_name) != set(_SUBCOMMAND_ORDER):
        missing = sorted(set(_SUBCOMMAND_ORDER) - set(by_name))
        extra = sorted(set(by_name) - set(_SUBCOMMAND_ORDER))
        raise ValueError(f"subcommand order mismatch: missing={missing} extra={extra}")
    for name in _SUBCOMMAND_ORDER:
        operation, data = by_name[name]
        cmd = data["x-los-cli-command"]
        p = sub.add_parser(cmd["name"], help=cmd["help"],
                           description=cmd["description"], epilog=cmd["epilog"])
        group_for: dict[str, argparse._MutuallyExclusiveGroup] = {}
        for group in cmd.get("mutually_exclusive", []):
            created = p.add_mutually_exclusive_group(required=bool(group["required"]))
            for dest in group["dests"]:
                group_for[dest] = created
        properties = data.get("properties", {})
        # File order is the old code order (bootstrap preserves _actions
        # order), so adding in file order reproduces usage/help order.
        # Converted operations carry _operation (SPEC 12 step 4); it is a
        # parser default, never a request property.
        for dest, schema in properties.items():
            _add_property(group_for.get(dest, p), dest, schema)
        p.set_defaults(**cmd.get("defaults", {}))
        if "operation_kind" in cmd:
            p.set_defaults(_operation_kind=cmd["operation_kind"])
        handler = cmd["handler"]
        func = _resolve_handler(handler)
        if handler.startswith("learning_os.adapters.cli.invoke:"):
            invoked = handler.split(":", 1)[1]
            if cmd.get("parser_factory"):
                p.set_defaults(func=func, _operation=invoked,
                               _parser_factory=build_parser)
            else:
                p.set_defaults(func=func, _operation=invoked)
        elif cmd.get("parser_factory"):
            p.set_defaults(func=func, _parser_factory=build_parser)
        else:
            p.set_defaults(func=func)
    return parser
