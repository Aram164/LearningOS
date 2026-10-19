"""Prefixed refusals carry the ``los: `` gateway prefix (P6-02 Task 2)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from learning_os.domain.failures import StaleSnapshot, Unconfirmed, WriteRefused

ROOT = Path(__file__).resolve().parent.parent


def _parts(node: ast.AST) -> list[tuple[str, str]]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [("lit", node.value)]
    if isinstance(node, ast.JoinedStr):
        out: list[tuple[str, str]] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                out.append(("lit", value.value))
            elif isinstance(value, ast.FormattedValue):
                inner = value.value
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "str"
                    and len(inner.args) == 1
                    and not inner.keywords
                ):
                    out.append(("expr", ast.unparse(inner.args[0])))
                else:
                    out.append(("expr", ast.unparse(inner)))
            else:
                out.append(("expr", ast.unparse(value)))
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _parts(node.left) + _parts(node.right)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "str"
        and len(node.args) == 1
        and not node.keywords
    ):
        return [("expr", ast.unparse(node.args[0]))]
    return [("expr", ast.unparse(node))]


def _merged(parts: list[tuple[str, str]]) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    for kind, value in parts:
        if kind == "lit" and merged and merged[-1][0] == "lit":
            merged[-1] = ("lit", merged[-1][1] + value)
        else:
            merged.append((kind, value))
    return merged


def _is_prefixed_pattern(call: ast.Call) -> bool:
    if not call.args:
        return False
    gateway = None
    for keyword in call.keywords:
        if keyword.arg == "gateway_message":
            gateway = keyword.value
            break
    if gateway is None:
        return False
    gateway_parts = _merged(_parts(gateway))
    expected = _merged([("lit", "los: ")] + _parts(call.args[0]))
    return gateway_parts == expected


def test_prefixed_write_refused():
    assert WriteRefused("x", prefixed=True).gateway_message == "los: x"


def test_prefixed_subclasses():
    assert StaleSnapshot("x", prefixed=True).gateway_message == "los: x"
    assert Unconfirmed("x", prefixed=True).gateway_message == "los: x"


def test_prefixed_non_string_message():
    assert WriteRefused(ValueError("boom"), prefixed=True).gateway_message == "los: boom"


def test_prefixed_and_gateway_message_are_exclusive():
    with pytest.raises(
        TypeError, match="prefixed and gateway_message are exclusive"
    ):
        WriteRefused("x", gateway_message="los: x", prefixed=True)


def test_prefixed_needs_exactly_one_message_argument():
    with pytest.raises(TypeError, match="prefixed needs exactly one message argument"):
        WriteRefused(prefixed=True)
    with pytest.raises(TypeError, match="prefixed needs exactly one message argument"):
        WriteRefused("a", "b", prefixed=True)


def test_no_gateway_message_matches_prefixed_pattern():
    count = 0
    base = ROOT / "tools" / "learning_os"
    for path in sorted(base.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_prefixed_pattern(node):
                count += 1
    assert count == 0
