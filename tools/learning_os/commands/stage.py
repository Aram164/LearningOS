"""Stage-bound work: notes, progress, attachments."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import sys

from learning_os.learning_runtime import requirement_id_for

from .support import (
    WriteRefused,
    _allocate_attachment_path,
    _dump_study_map,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_content_bound_file,
    _resume_pointer_write,
    _root,
    _stage,
    _unit_map_or_error,
    _write_transaction,
)


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
                      "stage_id": args.stage_id, "working_note": stage["working_note"],
                      **confirmation},
                     ensure_ascii=False))
    return 0


def _observe_offer(unit_id: str, stage: dict) -> dict:
    """The observation verb for one stage's requirement, or nothing.

    Pure and read-only: when the stage authors a runtime requirement, name
    the exact ``los observe`` invocation that would record evidence against
    it. Otherwise return no keys. Suggesting never writes — the ledger
    still moves only through ``los observe``.
    """
    target = stage.get("runtime_target")
    if not isinstance(target, dict):
        return {}
    requirement_id = requirement_id_for(unit_id, str(stage.get("id", "")))
    # Name the conditions this target actually declares. The offer used to
    # stop at activity and result, so the command it taught could not produce
    # evidence the interpreter would credit, and a difficulty reported through
    # it could not be read as a failure of this target at all (audit
    # `synthetic-learner-2026-09-12`, F02). The flags are prompts to state what
    # happened, never defaults to accept — an unmet condition is dropped, not
    # asserted.
    conditions = [str(name) for name in (target.get("conditions") or [])
                  if str(name).strip()]
    flags = "".join(f" --condition {name}" for name in conditions)
    offer = {
        "observe_requirement": requirement_id,
        "observe_next": f"los observe {requirement_id} --activity <what-you-did> "
                        f"--result <correct|incorrect|partial|abandoned>{flags}",
    }
    if conditions:
        offer["observe_conditions"] = conditions
        offer["observe_note"] = (
            "keep only the conditions that actually held; an omitted one is "
            "read as unknown, never as met"
        )
    return offer


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
        # One rule for every branch: the destination is the stage this action
        # just made current. Activate or revisit and you return to it; pause it
        # and you return to the thing you paused, which is what pausing means;
        # complete or skip and you return to the stage that became current
        # after it, or — when the map has run out of stages — to the finished
        # one, where `resume` can honestly say it is ready to shelve. Other
        # units keep their own active maps; this names where *he* is, not what
        # is open.
        resume_stage = str(data.get("current_stage") or stage["id"])
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_study_map(study_map, data),
                   unit.path: _dump_yaml(unit_data),
                   **_resume_pointer_write(
                       root, module_id=unit.module_id, unit_id=args.unit_id,
                       study_map_id=study_map.id, stage_id=resume_stage)},
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
                      "current_stage": data["current_stage"],
                      **_observe_offer(args.unit_id, stage),
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_stage_attach(args) -> int:
    root = _root(args)
    try:
        source, source_bytes = _read_content_bound_file(
            args.file,
            getattr(args, "file_sha256", None),
            label="stage attachment",
        )
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
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
        target = _allocate_attachment_path(attachment_dir, source.name)
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({"path": rel, "label": args.label or source.stem})
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_study_map(study_map, data), target: source_bytes},
            capability="stage.attachment.add",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "attachment": rel,
                      **confirmation}, ensure_ascii=False))
    return 0
