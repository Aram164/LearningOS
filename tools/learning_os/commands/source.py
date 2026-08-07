"""Source feedback recorded against an exact unit/stage/source."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import sys
from .support import _dump_yaml, _expected_ok, _expected_revisions_from_args, _operator_lock, _root, _stage, _unit_map_or_error, _write_transaction

def cmd_source_feedback(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        if args.source_id not in repo.sources:
            print(f"los: source not found: {args.source_id}", file=sys.stderr)
            return 2
        data = copy.deepcopy(study_map.data)
        stage = _stage(data, args.stage_id)
        if stage is None:
            print(f"los: stage not found: {args.stage_id}", file=sys.stderr)
            return 2
        entry = {"source_id": args.source_id, "feedback": args.feedback,
                 "recorded": _dt.date.today().isoformat()}
        if args.note:
            entry["note"] = args.note
        stage.setdefault("source_feedback", []).append(entry)
        code, errors, confirmation = _write_transaction(
            root, {study_map.path: _dump_yaml(data)},
            capability="source.feedback.record",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "stage_id": args.stage_id, "feedback": entry}, ensure_ascii=False))
    return 0
