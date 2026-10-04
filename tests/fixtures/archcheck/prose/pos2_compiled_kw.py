"""Positive fixture: compiled-pattern search with the string= keyword (C7)."""

import re

SNAPSHOT_RE = re.compile(r"snapshot-\d+")


def has_snapshot(msg: str) -> bool:
    return SNAPSHOT_RE.search(string=msg) is not None
