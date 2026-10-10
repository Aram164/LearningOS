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
