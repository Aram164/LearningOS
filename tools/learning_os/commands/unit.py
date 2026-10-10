"""Units, unit source selection, and the unit-level note."""

from __future__ import annotations

import sys

from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.ops._legacy_plumbing import (
    _fresh_manifest,
    _operator_lock,
    _snapshot,
)

from .reads import _print_stable, _refusal, _window
from .support import (
    _print_rows,
    _root,
)

_UNIT_SUMMARY_FIELDS = ("id", "title", "status", "module_id", "component_id",
                        "order", "current_study_map", "needs_study_map")
_COMPACT_LIMIT_DEFAULT = 20


def _unit_summary(row):
    """The eight discovery fields, with explicit nulls kept and absent dropped."""
    return {key: row[key] for key in _UNIT_SUMMARY_FIELDS if key in row}


#: The unit ``status`` enum from ``system/schema/unit.schema.json``.
#: A test pins this copy against the schema, so the two cannot drift.
#: An unknown filter value refuses with exit 2 instead of answering an
#: empty result, so ``total: 0`` always means "valid filter, no matches".
UNIT_STATUSES = frozenset({
    "needs-map", "not-started", "ready", "active", "paused",
    "ready-to-shelve", "complete",
})


def _component_ids(manifest) -> set[str]:
    """Every known component: declared on a module or named by a unit."""
    ids = set()
    for module in manifest.get("modules", []) or []:
        if not isinstance(module, dict):
            continue
        for component in module.get("components", []) or []:
            if isinstance(component, dict) and component.get("id"):
                ids.add(component["id"])
            elif isinstance(component, str) and component:
                ids.add(component)
    for row in manifest.get("units", []) or []:
        if isinstance(row, dict) and row.get("component_id"):
            ids.add(row["component_id"])
    return ids


def _filtered_units(manifest, args):
    rows = manifest.get("units", [])
    if args.module_id:
        modules = [row.get("id") for row in manifest.get("modules", []) or []
                   if isinstance(row, dict) and row.get("id")]
        if args.module_id not in modules:
            raise WriteRefused(not_found("module", args.module_id, modules))
        rows = [row for row in rows if row.get("module_id") == args.module_id]
    if args.component_id:
        known = _component_ids(manifest)
        if args.component_id not in known:
            raise WriteRefused(not_found("component", args.component_id, known))
        rows = [row for row in rows if row.get("component_id") == args.component_id]
    if args.status:
        if args.status not in UNIT_STATUSES:
            raise WriteRefused(with_suggestions(
                f"unknown status: {args.status}", args.status, UNIT_STATUSES))
        rows = [row for row in rows if row.get("status") == args.status]
    return rows


def _unit_list_compact(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 50)
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root, snapshot_id=snapshot)
            rows = sorted(_filtered_units(manifest, args),

                          key=lambda row: row["id"])
            total = len(rows)
            items = [_unit_summary(row) for row in rows[offset:offset + limit]]
            return _print_stable(root, snapshot, {
                "contract": "unit-list-summary",
                "filters": {key: value for key, value in (
                    ("module_id", args.module_id),
                    ("component_id", args.component_id),
                    ("status", args.status)) if value is not None},
                "items": items, "total": total,
                "next_offset": offset + limit if offset + limit < total else None,
                "detail": "inspect UNIT_ID",
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def cmd_unit_list(args) -> int:
    if getattr(args, "compact", False):
        return _unit_list_compact(args)
    if (getattr(args, "offset", 0) or args.limit != _COMPACT_LIMIT_DEFAULT
            or getattr(args, "expected_snapshot", None) is not None):
        print("los: --offset/--limit/--expected-snapshot need --compact",
              file=sys.stderr)
        return 2
    manifest = _fresh_manifest(_root(args))
    return _print_rows(_filtered_units(manifest, args))
