"""Scoped detours: create and resolve."""

from __future__ import annotations

import copy
import json
import sys

from learning_os.ops._legacy_plumbing import (
    _dump_study_map,
    _dump_yaml,
    _operator_lock,
)

from ..domain.suggest import not_found
from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _stage,
    _unit_map_or_error,
    _write_transaction,
)


def cmd_detour_resolve(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        detour = next((row for row in data.get("detours", []) or []
                       if row.get("id") == args.detour_id), None)
        if detour is None:
            known = [row.get("id") for row in data.get("detours", []) or []
                     if isinstance(row, dict) and row.get("id")]
            print(f"los: {not_found('detour', args.detour_id, known)}",
                  file=sys.stderr)
            return 2
        detour["status"] = "resolved"
        if args.resolution:
            detour["resolution"] = args.resolution
        target_stage = _stage(data, detour["return_to_stage"])
        for other in data.get("stages", []) or []:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        target_stage["status"] = "active"
        data["current_stage"] = target_stage["id"]
        data["status"] = "active"
        unit_data = copy.deepcopy(unit.data)
        unit_data["status"] = "active"
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_study_map(study_map, data), unit.path: _dump_yaml(unit_data)},
            capability="detour.resolve",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "detour_id": args.detour_id,
                      "return_to_stage": target_stage["id"],
                      **confirmation}, ensure_ascii=False))
    return 0
