"""Shared JSON encoders (PLAN 6.A.1 OD4a)."""

from __future__ import annotations

import json

from learning_os.ops._legacy_plumbing import _json_layout
from learning_os.ops.proposal import JsonFormat


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
