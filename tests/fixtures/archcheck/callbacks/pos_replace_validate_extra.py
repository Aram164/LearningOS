"""Positive population fixture: a hook-carrying replace counts (item 11.3).

AST-scanned only, never imported by the (a) test. The
``replace(proposal, validate_extra=...)`` call counts once in path
form; the ``str.replace("a", "b")`` call passes no hook keyword and
never counts.
"""

from dataclasses import replace


def _validate(root, writes):
    return []


def finish(proposal):
    _squashed = "a".replace("a", "b")
    return replace(proposal, validate_extra=_validate), _squashed
