"""Read-only commands. Nothing here writes: status, bootstrap, search, inspect, related,
and the thin delegations to validate.py / generate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import expansion, suggest
from learning_os.ops._legacy_plumbing import (
    _discovery_row,
    _fresh_manifest,
    _inbox_search_rows,
    _json_layout,
    _operator_lock,
    _publish,
    _snapshot,
)

from .reads import (
    _print_stable,
    _refusal,
    _window,
    content_search,
    empty_search_hint,
    flatten_search_values,
)
from .support import (
    _delegate,
    _root,
)

#: Every record family ``search --type`` accepts: the manifest's
#: record types plus the two virtual discovery rows (garden seeds and
#: inbox files). An unknown value refuses with exit 2 instead of
#: answering an empty result, so ``total: 0`` always means "valid
#: filter, no matches". A test pins this set against the live
#: manifest's types, so a new record family updates it explicitly.
VALID_RECORD_TYPES = frozenset({
    "collection", "compatibility-alias", "concept", "coordination",
    "garden-note", "inbox-item", "module", "module-source-map", "note",
    "program", "project", "project-relationship", "source", "study-map",
    "topic-pack", "unit", "unit-material-synthesis", "workspace",
})


def _unknown_record_type(value: str) -> str:
    """Refusal for a mistyped ``--type``: suggestions plus the valid list."""
    hints = suggest(value, VALID_RECORD_TYPES)
    message = f"unknown record type: {value}"
    if hints:
        return (f"{message} (did you mean: {', '.join(hints)}? "
                f"valid types: {', '.join(sorted(VALID_RECORD_TYPES))})")
    return f"{message} (valid types: {', '.join(sorted(VALID_RECORD_TYPES))})"


def _array_window(args) -> tuple[int, int]:
    """Offset/limit check for the legacy array response: unbounded, valid only."""
    offset, limit = args.offset, args.limit
    if offset < 0 or limit < 1:
        raise WriteRefused("offset must be nonnegative and limit at least 1")
    return offset, limit


def _metadata_matches(root: Path, args, snapshot: str) -> tuple[list[dict], list[str], list[int]]:
    """Literal-AND metadata matches in deterministic manifest order.

    Shared by the legacy array response and the opt-in page packet, so the
    two cannot disagree about what matches. An inbox listing failure refuses
    here: discovery must not silently omit drops. The caller's snapshot is
    shared with the manifest read so one search hashes once, not twice.
    """
    manifest = _fresh_manifest(root, snapshot_id=snapshot)
    words = [w for w in args.query.lower().split() if w]
    rows = list(manifest["records"])
    if not args.type or args.type == "garden-note":
        rows.extend(manifest.get("garden_entries", []) or [])
    if not args.type or args.type == "inbox-item":
        try:
            rows.extend(_inbox_search_rows(root))
        except OSError as exc:
            raise WriteRefused(f"cannot list work/inbox: {exc}") from exc
    matches = []
    hits = [0] * len(words)
    for rec in rows:
        if args.type and rec.get("type") != args.type:
            continue
        hay = "\n".join(flatten_search_values(rec)).lower()
        found = [word in hay for word in words]
        for index, hit in enumerate(found):
            if hit:
                hits[index] += 1
        if all(found):
            matches.append(_discovery_row(rec))
    return matches, words, hits


def _metadata_next_command(args, limit: int, next_offset: int, snapshot: str) -> str:
    parts = ["search", args.query]
    if args.type:
        parts += ["--type", args.type]
    parts += ["--page", "--limit", str(limit), "--offset", str(next_offset),
              "--expected-snapshot", snapshot]
    return expansion(*parts)


def _metadata_search_page(args) -> int:
    """Opt-in paged metadata packet: totals and a snapshot-bound continuation."""
    root = _root(args)
    try:
        offset, limit = _window(args, 100)
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            matches, words, hits = _metadata_matches(root, args, snapshot)
            if not matches and words:
                print(f"los: {empty_search_hint('record', words, hits)}",
                      file=sys.stderr)
            total = len(matches)
            items = matches[offset:offset + limit]
            next_offset = offset + limit if offset + limit < total else None
            return _print_stable(root, snapshot, {
                "contract": "metadata-search-page",
                "items": items, "total": total,
                "offset": offset, "returned": len(items),
                "next_offset": next_offset,
                "has_more": next_offset is not None,
                "expand": {"next": _metadata_next_command(args, limit, next_offset, snapshot)
                           if next_offset is not None else None},
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def cmd_search(args) -> int:
    if args.type is not None and args.type not in VALID_RECORD_TYPES:
        return _refusal(WriteRefused(_unknown_record_type(args.type)))
    if getattr(args, "content", False):
        if getattr(args, "page", False):
            print("los: --page pages metadata search; --content already paginates",
                  file=sys.stderr)
            return 2
        return content_search(args)
    if getattr(args, "page", False):
        return _metadata_search_page(args)
    root = _root(args)
    try:
        offset, limit = _array_window(args)
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            matches, words, hits = _metadata_matches(root, args, snapshot)
            _snapshot(root, snapshot)
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)
    if not matches and words:
        print(f"los: {empty_search_hint('record', words, hits)}", file=sys.stderr)
    shown = matches[offset:offset + limit]
    if len(matches) > offset + limit:
        print(f"los: showing {len(shown)} of {len(matches)} matches; "
              f"continue with --offset {offset + limit}, or use --page for "
              "totals and a snapshot-bound continuation", file=sys.stderr)
    print(json.dumps(shown, **_json_layout(), sort_keys=True, ensure_ascii=False))
    return 0


def cmd_validate(args) -> int:
    return _delegate("validate.py", ["--online"] if args.online else [], args)


def cmd_generate(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        _publish(root)
    print("published generated/manifest.json (atomic contract snapshot)")
    return 0
