"""Stage-bound work: notes, progress, attachments."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import sys
from pathlib import Path
from .support import _dump_yaml, _expected_ok, _expected_revisions_from_args, _operator_lock, _root, _stage, _unit_map_or_error, _write_transaction

def cmd_stage_note(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        stage = _stage(study_map.data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        target = root / str(stage.get("working_note", ""))
        if not stage.get("working_note"):
            print("los: stage has no working_note", file=sys.stderr)
            return 2
        value = args.text if args.text is not None else sys.stdin.read()
        if not value.strip():
            # `--replace --text ""` used to truncate an existing note to zero
            # bytes and report success. Emptying a note is a deliberate edit,
            # not something a save button should ever do.
            print("los: refusing to write an empty note — pass real text",
                  file=sys.stderr)
            return 2
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if args.replace:
            updated = value.rstrip() + ("\n" if value.strip() else "")
        else:
            divider = "\n" if old and not old.endswith("\n\n") else ""
            updated = old + divider + value.rstrip() + "\n"
        code, errors, confirmation = _write_transaction(
            root, {target: updated}, capability="stage.note.write",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "working_note": stage["working_note"]},
                     ensure_ascii=False))
    return 0


def cmd_stage_progress(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None or unit is None:
            return 2
        data = copy.deepcopy(study_map.data)
        unit_data = copy.deepcopy(unit.data)
        stages = data.get("stages", []) or []
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        action = args.status
        if action in {"active", "revisit"}:
            for other in stages:
                if other.get("status") in {"active", "paused"}:
                    other["status"] = "pending"
            stage["status"] = "active"
            stage.pop("completed", None)
            data["current_stage"] = stage["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        elif action == "paused":
            stage["status"] = "paused"
            data["current_stage"] = stage["id"]
            data["status"] = "paused"
            unit_data["status"] = "paused"
        else:
            if stage.get("status") != "active":
                print("los: complete/skip applies only to the active stage; activate it first",
                      file=sys.stderr)
                return 2
            stage["status"] = "complete" if action == "complete" else "skipped"
            if action == "complete":
                stage["completed"] = _dt.date.today().isoformat()
            following = next((row for row in stages[stages.index(stage) + 1:]
                              if row.get("status") == "pending"), None)
            if following:
                following["status"] = "active"
                data["current_stage"] = following["id"]
                data["status"] = "active"
                unit_data["status"] = "active"
            else:
                data["status"] = "ready-to-shelve"
                data.setdefault("shelving", {})["state"] = "draft"
                unit_data["status"] = "ready-to-shelve"
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_yaml(data), unit.path: _dump_yaml(unit_data)},
            capability="stage.progress.update",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id, "stage_id": args.stage_id,
                      "status": action, "map_status": data["status"],
                      "current_stage": data["current_stage"]}, ensure_ascii=False))
    return 0


def cmd_stage_attach(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        note_path = root / stage["working_note"]
        attachment_dir = note_path.parent / "attachments"
        target = attachment_dir / source.name
        if target.exists():
            stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            target = attachment_dir / f"{stamp}-{source.name}"
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({"path": rel, "label": args.label or source.stem})
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_yaml(data), target: source.read_bytes()},
            capability="stage.attachment.add",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "attachment": rel}, ensure_ascii=False))
    return 0
