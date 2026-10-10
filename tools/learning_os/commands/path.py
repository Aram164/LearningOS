"""Ordered learning paths: notes, progress, attachments."""

from __future__ import annotations

import json
import sys

import yaml

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _read_content_bound_file,
)

from .. import observations
from ..domain.failures import WriteRefused
from ..domain.suggest import not_found
from .support import (
    _allocate_attachment_path,
    _expected_ok,
    _expected_revisions_from_args,
    _path_or_error,
    _root,
    _stage_ids,
    _write_transaction,
)


# ---------------------------------------------------------- learning paths
def cmd_path_attach(args) -> int:
    root = _root(args)
    try:
        source, source_bytes = _read_content_bound_file(
            args.file,
            getattr(args, "file_sha256", None),
            label="path attachment",
        )
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
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
            print(f"los: {not_found('stage', args.stage_id, _stage_ids(data))}",
                  file=sys.stderr)
            return 2
        workspace = learning_path.path.parent.parent
        attachment_dir = workspace / "scratch" / "paths" / learning_path.id \
            / "attachments" / stage["id"]
        target = _allocate_attachment_path(attachment_dir, source.name)
        rel = target.relative_to(root).as_posix()
        stage.setdefault("attachments", []).append({
            "path": rel, "label": args.label or source.stem})
        data["updated"] = observations.today().isoformat()
        code, errors, confirmation = _write_transaction(
            root, {
                learning_path.path: yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                target: source_bytes,
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
