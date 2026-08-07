"""Ordered learning paths: notes, progress, attachments."""

from __future__ import annotations

import datetime as _dt
import json
import sys
import yaml
from pathlib import Path
from .support import _expected_ok, _expected_revisions_from_args, _operator_lock, _path_or_error, _root, _write_transaction

# ---------------------------------------------------------- learning paths
def cmd_path_note(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        stage = next((s for s in learning_path.data.get("stages", [])
                      if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        note_ref = stage.get("notes_path")
        if not note_ref:
            print(f"los: stage has no notes_path: {args.stage_id}", file=sys.stderr)
            return 2
        text_value = args.text if args.text is not None else sys.stdin.read()
        if not text_value.strip():
            print("los: refusing to write an empty note — pass real text",
                  file=sys.stderr)
            return 2
        target = root / str(note_ref)
        old = target.read_text(encoding="utf-8") if target.is_file() else ""
        if args.replace:
            updated = text_value.rstrip() + ("\n" if text_value.strip() else "")
        else:
            divider = "\n" if old and not old.endswith("\n\n") else ""
            updated = old + divider + text_value.rstrip() + "\n"
        code, errors, confirmation = _write_transaction(
            root, {target: updated}, capability="path.note.write",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.path_id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "notes_path": note_ref,
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_path_progress(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        data = learning_path.data
        stages = data.get("stages", []) or []
        stage = next((s for s in stages if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        if args.status in {"complete", "skipped"} and stage.get("status") != "active":
            print("los: only the active stage can be completed or skipped; activate it first",
                  file=sys.stderr)
            return 2
        if args.status == "active":
            for other in stages:
                if other.get("status") == "active":
                    other["status"] = "pending"
            stage["status"] = "active"
            stage.pop("completed", None)
            data["current_stage"] = stage["id"]
            data["status"] = "active"
        else:
            stage["status"] = args.status
            if args.status == "complete":
                stage["completed"] = _dt.date.today().isoformat()
            following = next((s for s in stages[stages.index(stage) + 1:]
                              if s.get("status") == "pending"), None)
            if following:
                following["status"] = "active"
                data["current_stage"] = following["id"]
                data["status"] = "active"
            else:
                data["status"] = "ready-to-shelve"
                shelving = data.setdefault("shelving", {})
                shelving["state"] = "draft"
        data["updated"] = _dt.date.today().isoformat()
        rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        code, errors, confirmation = _write_transaction(
            root, {learning_path.path: rendered}, capability="path.progress.update",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.path_id],
        )
        if code:
            print("los: path update rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "status": args.status,
                      "path_status": data["status"],
                      "current_stage": data["current_stage"],
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_path_attach(args) -> int:
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, learning_path = _path_or_error(root, args.path_id)
        if learning_path is None:
            return 2
        data = learning_path.data
        stage = next((s for s in data.get("stages", [])
                      if s.get("id") == args.stage_id), None)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        workspace = learning_path.path.parent.parent
        attachment_dir = workspace / "scratch" / "paths" / learning_path.id \
            / "attachments" / stage["id"]
        target = attachment_dir / source.name
        if target.exists():
            stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            target = attachment_dir / f"{stamp}-{source.name}"
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({
            "path": rel, "label": args.label or source.stem})
        data["updated"] = _dt.date.today().isoformat()
        code, errors, confirmation = _write_transaction(
            root, {
                learning_path.path: yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                target: source.read_bytes(),
            },
            capability="path.attachment.add",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.path_id],
        )
        if code:
            print("los: attachment rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "path_id": args.path_id,
                      "stage_id": args.stage_id, "attachment": rel,
                      **confirmation}, ensure_ascii=False))
    return 0
