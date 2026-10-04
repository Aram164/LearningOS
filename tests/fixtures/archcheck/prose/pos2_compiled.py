"""Positive fixture: compiled-pattern searches over suspect text (item 3(ii))."""

import re

SNAPSHOT_RE = re.compile(r"snapshot-\d+")


def has_snapshot(msg: str) -> bool:
    return SNAPSHOT_RE.search(msg) is not None


def snapshot_refs(msg: str) -> list[str]:
    return SNAPSHOT_RE.findall(msg)


def has_snapshot_chained(msg: str) -> bool:
    return re.compile(r"snapshot-\d+").search(msg) is not None
