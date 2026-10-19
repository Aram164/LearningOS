"""Positive fixture: regex match against a message (rule c)."""

import re


def has_snapshot(msg: str) -> bool:
    return re.search(r"snapshot-\d+", msg) is not None
