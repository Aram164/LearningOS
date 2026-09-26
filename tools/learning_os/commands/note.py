"""Canonical note creation, revision, and evidence recording."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import jsonschema

from learning_os.loader import EVIDENCE_SCHEMES, LoaderError, load_repo, parse_frontmatter

from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_content_bound_file,
    _render_frontmatter,
    _root,
    _write_transaction,
)

NOTES_PREFIX = Path("knowledge/notes")

#: Caller-supplied fields of the ``note`` object; anything else refuses.
#: Authorship, review state, timestamps, bindings, and evidence are owned by
#: the handler and can never be supplied — mirroring note.analysis.save.
NOTE_FIELDS = frozenset({
    "id", "title", "path", "role", "concepts", "sources", "contexts",
    "supersedes",
})

#: Roles with a dedicated authoring capability keep it. A general creation
#: path must not mint reference notes without a material_analysis binding
#: or question notes without the Atlas wording/target preservation.
RESERVED_ROLES = {
    "reference": "note.analysis.save",
    "question": "atlas.question.save",
}


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
    try:
        source, content_bytes = _read_content_bound_file(
            args.file,
            getattr(args, "file_sha256", None),
            label="revised note file",
        )
        content = content_bytes.decode("utf-8")
    except (UnicodeDecodeError, WriteRefused) as exc:
        print(f"los: cannot read revised note: {exc}", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note = repo.notes.get(args.note_id)
        if note is None:
            print(f"los: note not found: {args.note_id}", file=sys.stderr)
            return 2
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


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"note create cannot use a symlink: {relative}")
    return path


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


def _render_exact_note(meta: dict, body: bytes) -> bytes:
    """Frontmatter plus the body bytes verbatim.

    Unlike the evidence renderer this never strips leading whitespace: the
    bytes after the frontmatter block are exactly the approved capture.
    """
    front = "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n"
    return front.encode("utf-8") + body


def _destination(root: Path, note_id: str, relpath: object) -> Path:
    if not isinstance(relpath, str) or not relpath:
        raise WriteRefused("note path must be a repo-relative note path")
    relative = Path(relpath)
    if relative.is_absolute() or ".." in relative.parts:
        raise WriteRefused("note path must stay inside knowledge/notes/")
    if relative.suffix != ".md" or relative.stem != note_id:
        raise WriteRefused("note filename must be the note id with .md")
    try:
        relative.relative_to(NOTES_PREFIX)
    except ValueError:
        raise WriteRefused("note path must stay inside knowledge/notes/") from None
    return _safe(root, root / relative)


def _id_list(note: dict, field: str) -> list[str]:
    value = note.get(field)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise WriteRefused(f"note {field} must be a list of ids")
    return value


def _precheck_note(note: object, body: bytes) -> dict:
    """Record shape and frozen-byte agreement, before the snapshot guard.

    Everything needing the loaded repository — id collision, reference
    registration, supersedes existence — stays in `_resolve_note_create`,
    inside the guard.
    """
    if not isinstance(note, dict):
        raise WriteRefused("note must be an object")
    unknown = set(note) - NOTE_FIELDS
    if unknown or not isinstance(note.get("id"), str):
        raise WriteRefused("note has unknown fields or no note id")
    if not body:
        raise WriteRefused("note body is empty")
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        raise WriteRefused("note body is not valid UTF-8") from None
    role = note.get("role", "synthesis")
    if not isinstance(role, str):
        raise WriteRefused("note role must be a string")
    if role in RESERVED_ROLES:
        raise WriteRefused(
            f"role {role!r} keeps its dedicated capability; use {RESERVED_ROLES[role]}")
    if not isinstance(note.get("title"), str) or not note["title"].strip():
        raise WriteRefused("new notes require a title")
    return note


def _resolve_note_create(root: Path, repo, note: dict,
                         body: bytes) -> tuple[str, Path, bytes, dict[Path, str]]:
    """Classify one prechecked note against the loaded repository.

    Returns (note_id, destination, rendered_bytes, deprecations) where
    deprecations maps each newly-superseded note path to its re-rendered
    content. Any id collision, dangling reference, or unknown supersedes
    target refuses. Callers commit every returned write in one transaction.
    """
    note_id = note["id"]
    if note_id in repo.notes:
        raise WriteRefused(
            f"note id {note_id!r} already exists; revise it with note.revise")
    path = _destination(root, note_id, note.get("path"))
    if path.exists():
        raise WriteRefused("note destination already exists")
    for concept_id in _id_list(note, "concepts"):
        if concept_id not in repo.concepts:
            raise WriteRefused(f"note concept is not registered: {concept_id!r}")
    for source_id in _id_list(note, "sources"):
        if source_id not in repo.sources:
            raise WriteRefused(f"note source is not registered: {source_id!r}")
    for context_id in _id_list(note, "contexts"):
        if context_id not in repo.workspaces:
            raise WriteRefused(f"note context is not a workspace: {context_id!r}")
    supersedes = _id_list(note, "supersedes")
    if note_id in supersedes:
        raise WriteRefused("a note cannot supersede itself")
    for old_id in supersedes:
        if old_id not in repo.notes:
            raise WriteRefused(f"superseded note does not exist: {old_id!r}")
    meta = {"id": note_id, "type": "note", "role": note.get("role", "synthesis"),
            "title": note["title"], "created": date.today().isoformat(),
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed"}
    for field in ("concepts", "sources", "contexts", "supersedes"):
        if note.get(field):
            meta[field] = list(note[field])
    # Validate id before it can be used as a filename.
    _schema(root, "note", meta)
    deprecations: dict[Path, str] = {}
    for old_id in supersedes:
        old = repo.notes[old_id]
        try:
            old_meta, old_body = parse_frontmatter(
                old.path.read_text(encoding="utf-8"), old.path)
        except (LoaderError, OSError) as exc:
            raise WriteRefused(
                f"cannot read superseded note {old_id!r}: {exc}") from exc
        if old_meta.get("state") != "deprecated":
            old_meta["state"] = "deprecated"
            deprecations[old.path] = _render_frontmatter(old_meta, old_body)
    return note_id, path, _render_exact_note(meta, body), deprecations


def cmd_note_create(args) -> int:
    """Create one durable note from approved bytes.

    The governed form of WORKFLOWS §3: capture and scratch become durable
    understanding only through this capability (or the semantically narrower
    note.analysis.save, atlas.question.save, and shelving review.apply).
    Authorship and review defaults are owned by this handler; the body is
    preserved verbatim and bound to the approved SHA-256. A successor note
    declares `supersedes` and deprecates its predecessors atomically; the
    reverse link stays generated, never stored (ARCHITECTURE §5.5).
    """
    root = _root(args)
    _, body = _read_content_bound_file(
        args.body_file, getattr(args, "body_file_sha256", None),
        label="note body file")
    note = _precheck_note(args.note, body)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        note_id, path, content, deprecations = _resolve_note_create(
            root, repo, note, body)
        writes: dict[Path, str | bytes] = {path: content}
        writes.update(deprecations)
        code, errors, confirmation = _write_transaction(
            root, writes,
            capability="note.create",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[note_id, *_id_list(note, "supersedes")],
        )
        if code:
            raise WriteRefused("; ".join(str(issue) for issue in errors[:12]))
        print(json.dumps({"ok": True, "note_id": note_id,
                          "note_path": path.relative_to(root).as_posix(),
                          "deprecated": sorted(old.relative_to(root).as_posix()
                                               for old in deprecations),
                          **confirmation}, ensure_ascii=False))
        return 0
