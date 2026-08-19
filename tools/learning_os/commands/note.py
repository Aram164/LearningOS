"""Canonical note revision and evidence recording."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from learning_os.loader import EVIDENCE_SCHEMES, LoaderError, load_repo, parse_frontmatter

from .support import (_expected_ok, _expected_revisions_from_args, _operator_lock,
                      _render_frontmatter, _root, _write_transaction)

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
        except LoaderError as exc:
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
                      "path": note.path.relative_to(root).as_posix(),
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_note_evidence(args) -> int:
    """Append one evidence pointer to a note without touching its body.

    Evidence answers "have I actually worked through this?" (PHILOSOPHY §3.6).
    It is deliberately a pointer, not a verdict: the command records that a
    derivation, explanation, implementation, exercise or exam artifact exists
    and where it is. It never scores, ranks, or concludes anything about
    understanding — retrieval surfaces show the trail or its documented absence.

    The note body is passed through untouched; only the frontmatter is
    re-rendered. Entries are append-only, so an existing trail can never be
    silently rewritten or dropped by recording a new one.

    A trail is addressed by typed URI, never by bare path, so it survives the
    file moving. The scheme is checked here rather than left to REF-EVIDENCE
    so the failure names the allowed vocabulary instead of arriving as a
    validation rejection after the transaction has been assembled.
    """
    if not args.ref.startswith(EVIDENCE_SCHEMES):
        print(f"los: evidence ref '{args.ref}' uses no valid URI scheme", file=sys.stderr)
        print("     expected one of: " + ", ".join(EVIDENCE_SCHEMES), file=sys.stderr)
        return 2
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note = repo.notes.get(args.note_id)
        if note is None:
            print(f"los: note not found: {args.note_id}", file=sys.stderr)
            return 2
        content = note.path.read_text(encoding="utf-8")
        try:
            meta, body = parse_frontmatter(content, note.path)
        except LoaderError as exc:
            print(f"los: cannot read note frontmatter: {exc}", file=sys.stderr)
            return 2
        existing = list(meta.get("evidence") or [])
        entry = {"type": args.evidence_type, "ref": args.ref}
        if any(e.get("type") == entry["type"] and e.get("ref") == entry["ref"]
               for e in existing):
            print("los: that evidence is already recorded on this note", file=sys.stderr)
            return 2
        meta["evidence"] = existing + [entry]
        code, errors, confirmation = _write_transaction(
            root, {note.path: _render_frontmatter(meta, body)},
            capability="note.evidence.add",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.note_id],
        )
        if code:
            print("los: evidence rejected by validation", file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "note_id": args.note_id,
                      "path": note.path.relative_to(root).as_posix(),
                      "evidence": entry,
                      "evidence_count": len(meta["evidence"]),
                      "scheme": args.ref.split("://", 1)[0],
                      **confirmation},
                     ensure_ascii=False))
    return 0
