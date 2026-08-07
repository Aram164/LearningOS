"""Canonical note revision."""

from __future__ import annotations

import json
import sys
from learning_os.loader import load_repo, parse_frontmatter
from pathlib import Path
from .support import _expected_ok, _expected_revisions_from_args, _operator_lock, _root, _write_transaction

def cmd_note_revise(args) -> int:
    """Replace one existing note after explicit, reviewable approval.

    IDs, paths, and roles are held stable; this is a semantic revision gateway,
    not a rename, move, role change, merge, or split operation.
    """
    if not args.approve:
        print("los: note revision requires --approve after reviewing the full replacement",
              file=sys.stderr)
        return 2
    root = _root(args)
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"los: no such revised note file: {source}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note = repo.notes.get(args.note_id)
        if note is None:
            print(f"los: note not found: {args.note_id}", file=sys.stderr)
            return 2
        content = source.read_text(encoding="utf-8")
        try:
            meta, _ = parse_frontmatter(content, source)
        except Exception as exc:  # LoaderError is intentionally presented as usage failure.
            print(f"los: invalid revised note: {exc}", file=sys.stderr)
            return 2
        if meta.get("id") != args.note_id or meta.get("type") != "note":
            print("los: revised note must preserve the requested note id and type", file=sys.stderr)
            return 2
        if meta.get("role") != note.meta.get("role"):
            print("los: note-revise cannot change a note role", file=sys.stderr)
            return 2
        code, errors, confirmation = _write_transaction(
            root, {note.path: content.rstrip() + "\n"},
            capability="note.revise",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.note_id],
        )
        if code:
            print("los: note revision rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "note_id": args.note_id,
                      "path": note.path.relative_to(root).as_posix()}, ensure_ascii=False))
    return 0
