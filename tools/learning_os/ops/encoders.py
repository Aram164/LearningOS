"""Shared JSON encoders (PLAN 6.A.1 OD4a)."""

from __future__ import annotations

import json
import sys

from learning_os.ops.proposal import JsonFormat


def _json_layout(stream=None) -> dict:
    """Indented JSON for a person at a terminal, compact JSON on a pipe.

    Agents and the UI read through pipes, where indentation was 15-22% of
    the bytes of inspect, resume, search and semantic output and carried no
    information (measured 2026-09-22). Any JSON parser reads both forms.
    """
    if stream is None:
        stream = sys.stdout
    try:
        interactive = stream.isatty()
    except (AttributeError, ValueError):
        interactive = False
    return {"indent": 2} if interactive else {"separators": (",", ":")}


def dumps_unescaped(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def dumps_compact(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def dumps_indented(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def dumps_ascii(payload) -> str:
    return json.dumps(payload)


def dumps_sorted(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def dumps_indented_sorted(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def dumps_layout_sorted(payload) -> str:
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


def encode_json(payload, option: JsonFormat) -> str:
    encoders = {
        "ascii": dumps_ascii,
        "compact": dumps_compact,
        "indented": dumps_indented,
        "indented_sorted": dumps_indented_sorted,
        "layout_sorted": dumps_layout_sorted,
        "sorted": dumps_sorted,
        "unescaped": dumps_unescaped,
    }
    return encoders[option](payload)
