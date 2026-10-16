"""Structural CLI description for parser parity (PLAN D2).

Used by the S12 parity baselines and by ``tests/test_arch_cli_parity.py``.
``describe`` captures everything the generated parser must reproduce:
root parser identity, subparser order, per-subparser help/defaults/groups
and every action attribute the bootstrap reads.
"""

from __future__ import annotations

import argparse

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


def _dotted(func) -> str:
    module = getattr(func, "__module__", "") or ""
    qualname = getattr(func, "__qualname__", "") or getattr(func, "__name__", "")
    if module:
        return f"{module}.{qualname}"
    return str(qualname)


def _action_shape(action: argparse.Action) -> dict:
    metavar = action.metavar
    if isinstance(metavar, tuple):
        metavar = list(metavar)
    choices = getattr(action, "choices", None)
    if choices is not None and not isinstance(choices, dict):
        try:
            choices_list = list(choices)
        except TypeError:
            choices_list = None
    else:
        choices_list = None
    action_type = getattr(action, "type", None)
    if action_type is None:
        type_name = None
    else:
        type_name = getattr(action_type, "__name__", repr(action_type))
    const = getattr(action, "const", None)
    try:
        const_repr = repr(const)
    except Exception:
        const_repr = "<unrepresentable>"
    try:
        default_repr = repr(action.default)
    except Exception:
        default_repr = "<unrepresentable>"
    help_value = action.help
    return {
        "option_strings": list(action.option_strings),
        "dest": action.dest,
        "nargs": action.nargs,
        "const_repr": const_repr,
        "default_repr": default_repr,
        "type": type_name,
        "choices": choices_list,
        "required": bool(action.required),
        "help": help_value,
        "metavar": metavar,
        "action": _action_name(action),
    }


def _sub_help(root: argparse.ArgumentParser, name: str) -> str | None:
    for action in root._actions:
        if isinstance(action, argparse._SubParsersAction):
            for pseudo in getattr(action, "_choices_actions", []):
                if getattr(pseudo, "dest", None) == name:
                    return pseudo.help
    return None


def describe(parser: argparse.ArgumentParser) -> dict:
    """Describe the parser structurally (JSON-serializable)."""
    from learning_os.store.contracts.payloads import subparsers

    subs = subparsers(parser)
    order = list(subs.keys())
    root_options = [
        _action_shape(action)
        for action in parser._actions
        if not isinstance(action, argparse._SubParsersAction)
    ]
    parser_class = f"{type(parser).__module__}.{type(parser).__name__}"
    formatter = getattr(parser, "formatter_class", None)
    if formatter is not None:
        formatter_name = f"{formatter.__module__}.{formatter.__name__}"
    else:
        formatter_name = None
    subparsers_desc: dict[str, dict] = {}
    for name in order:
        sub = subs[name]
        groups = []
        for group in getattr(sub, "_mutually_exclusive_groups", []):
            groups.append(
                {
                    "required": bool(group.required),
                    "dests": [a.dest for a in group._group_actions],
                }
            )
        defaults: dict[str, str] = {}
        for key, value in sorted(getattr(sub, "_defaults", {}).items()):
            if callable(value):
                defaults[key] = _dotted(value)
            else:
                try:
                    defaults[key] = repr(value)
                except Exception:
                    defaults[key] = "<unrepresentable>"
        actions = [_action_shape(a) for a in sub._actions]
        subparsers_desc[name] = {
            "help": _sub_help(parser, name),
            "description": sub.description,
            "epilog": sub.epilog,
            "prog": sub.prog,
            "defaults": defaults,
            "groups": groups,
            "actions": actions,
        }
    return {
        "parser_class": parser_class,
        "prog": parser.prog,
        "description": parser.description,
        "formatter_class": formatter_name,
        "root_options": root_options,
        "order": order,
        "subparsers": subparsers_desc,
    }
