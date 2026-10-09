"""Stage-bound work: notes, progress, attachments."""

from __future__ import annotations

import copy
import json
import sys

from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.ops._legacy_plumbing import (
    _dump_study_map,
    _operator_lock,
    _read_content_bound_file,
)

from .support import (
    _allocate_attachment_path,
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _stage,
    _stage_ids,
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
            print(f"los: {not_found('stage', args.stage_id, _stage_ids(study_map.data))}",
                  file=sys.stderr)
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
            print(f"los: {not_found('stage', args.stage_id, _stage_ids(data))}",
                  file=sys.stderr)
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
