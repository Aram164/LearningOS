"""Reader for the corpus bundle format used by the evaluation world.

A bundle is one Markdown file holding many items. Each item starts with a
line ``=== KEY`` (optionally ``=== KEY @YYYY-MM-DD`` for an earlier revision
of the same item), followed by YAML header lines, a line containing only
``---``, and then the verbatim body up to the next ``=== `` line or the end of
the file. Lines before the first item are a free-text preamble and ignored.

The format exists so that note bodies are written as plain Markdown, never
as indented YAML block scalars, which keeps authored prose byte-exact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_ITEM = re.compile(r"^=== (?P<key>\S+)(?: @(?P<rev>\d{4}-\d{2}-\d{2}))?\s*$")


@dataclass
class Item:
    key: str
    meta: dict
    body: str
    source: str
    line: int
    revision: str | None = None
    revisions: list[Item] = field(default_factory=list)


class BundleError(ValueError):
    pass


def _finish(key, rev, lines, source, line_no) -> Item:
    try:
        split = lines.index("---")
    except ValueError as exc:
        raise BundleError(f"{source}:{line_no}: item {key!r} has no '---' separator") from exc
    header = "\n".join(lines[:split])
    try:
        meta = yaml.safe_load(header) if header.strip() else {}
    except yaml.YAMLError as exc:
        raise BundleError(f"{source}:{line_no}: item {key!r} header is not YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise BundleError(f"{source}:{line_no}: item {key!r} header must be a mapping")
    body_lines = lines[split + 1:]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    body = "\n".join(body_lines) + "\n" if body_lines else ""
    return Item(key=key, meta=meta, body=body, source=source, line=line_no, revision=rev)


def read_bundle(path: Path) -> list[Item]:
    """Items of one bundle, revisions attached to their final item."""
    text = path.read_text(encoding="utf-8")
    source = path.name
    items: list[Item] = []
    current = None
    for number, raw in enumerate(text.splitlines(), start=1):
        match = _ITEM.match(raw)
        if match:
            if current is not None:
                items.append(_finish(current[0], current[1], current[2], source, current[3]))
            current = [match["key"], match["rev"], [], number]
            continue
        if current is not None:
            current[2].append(raw)
    if current is not None:
        items.append(_finish(current[0], current[1], current[2], source, current[3]))

    finals: dict[str, Item] = {}
    pending: list[Item] = []
    for item in items:
        if item.revision is None:
            if item.key in finals:
                raise BundleError(f"{source}:{item.line}: duplicate item {item.key!r}")
            finals[item.key] = item
        else:
            pending.append(item)
    for rev in pending:
        owner = finals.get(rev.key)
        if owner is None:
            raise BundleError(f"{source}:{rev.line}: revision of unknown item {rev.key!r}")
        owner.revisions.append(rev)
    for item in finals.values():
        item.revisions.sort(key=lambda r: r.revision)
    return list(finals.values())


def read_bundles(directory: Path) -> list[Item]:
    out: list[Item] = []
    seen: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        for item in read_bundle(path):
            if item.key in seen:
                raise BundleError(
                    f"{path.name}:{item.line}: item {item.key!r} already defined in {seen[item.key]}")
            seen[item.key] = path.name
            out.append(item)
    return out
