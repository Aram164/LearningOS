"""Scoped detours: create and resolve."""

from __future__ import annotations

import copy
import json
import re
import sys
from .support import _dump_yaml, _expected_ok, _expected_revisions_from_args, _operator_lock, _root, _stage, _unit_map_or_error, _write_transaction

def cmd_detour_create(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        base = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "gap"
        did = f"detour-{base}"
        existing = {row.get("id") for row in data.get("detours", []) or []}
        if did in existing:
            suffix = 2
            while f"{did}-{suffix}" in existing:
                suffix += 1
            did = f"{did}-{suffix}"
        detour = {"id": did, "title": args.title, "spawned_by_stage": args.stage_id,
                  "classification": args.classification, "status": "open",
                  "return_to_stage": args.stage_id}
        data.setdefault("detours", []).append(detour)
        stage["detour_id"] = did
        if args.classification == "required-now":
            stage["status"] = "paused"
            data["status"] = "paused"
            unit_data = copy.deepcopy(unit.data)
            unit_data["status"] = "paused"
        else:
            unit_data = unit.data
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)},
            capability="detour.create",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "detour": detour}, ensure_ascii=False))
    return 0


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
            print(f"los: detour not found: {args.detour_id}", file=sys.stderr)
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
            root, {study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)},
            capability="detour.resolve",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "detour_id": args.detour_id,
                      "return_to_stage": target_stage["id"]}, ensure_ascii=False))
    return 0
