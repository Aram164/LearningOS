"""Bounded, snapshot-bound reads; complete content stays under its Core owner."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import PurePosixPath

from learning_os.errors import unreadable_refusal
from learning_os.fingerprint import canonical_fingerprint
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.loading import Repo, load_notes

from .support import (
    WriteRefused,
    _fresh_manifest,
    _operator_lock,
    _root,
)


def _window(args, maximum: int) -> tuple[int, int]:
    offset, limit = args.offset, args.limit
    if offset < 0 or not 1 <= limit <= maximum:
        raise WriteRefused(f"offset must be nonnegative and limit between 1 and {maximum}")
    if offset and not args.expected_snapshot:
        raise WriteRefused("continuation requires --expected-snapshot from the previous response")
    return offset, limit


def _snapshot(root, expected=None) -> str:
    actual = f"sha256:{canonical_fingerprint(root)}"
    if expected is not None and expected != actual:
        raise WriteRefused("snapshot changed; restart this read before continuing")
    return actual


def _print_stable(root, snapshot, payload) -> int:
    _snapshot(root, snapshot)
    print(json.dumps({"schema_version": 1, "snapshot_id": snapshot, **payload},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


def _refusal(exc) -> int:
    print(f"los: {exc}", file=sys.stderr)
    return 3 if "snapshot" in str(exc) else 2


def record_payload(manifest, record_id):
    resolved_id = (manifest.get("project_aliases") or {}).get(record_id, record_id)
    record = next((row for row in manifest["records"] if row.get("id") == resolved_id), None)
    if record is None:
        return None
    payload = dict(record)
    if resolved_id != record_id:
        payload["resolved_from"] = record_id
    return payload


def inspect_batch(args) -> int:
    """Resolve a requested batch once; never return a partial or mixed read."""
    ids = [args.id, *args.more_ids]
    if len(ids) > 20:
        return _refusal("inspect accepts at most 20 IDs per batch")
    root = _root(args)
    try:
        with _operator_lock(root):
            snapshot = _snapshot(root)
            manifest = _fresh_manifest(root)
            records = []
            for record_id in ids:
                record = record_payload(manifest, record_id)
                if record is None:
                    raise WriteRefused(f"record not found: {record_id}")
                records.append(record)
            return _print_stable(root, snapshot, {
                "contract": "record-batch", "requested_ids": ids, "records": records,
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def _domain_glance(manifest):
    """Summarize the complete projection, independently of record pagination."""
    domains = {domain: {"domain": domain, "notes": 0, "crosswalks": 0,
                        "shelves": 0, "entries": 0}
               for domain in ATLAS_DOMAINS}
    for record in manifest.get("records", []):
        kind = record.get("type")
        if kind not in {"note", "collection", "topic-pack"}:
            continue
        domain = record.get("domain") or "cross-domain"
        if kind == "note" and record.get("path"):
            # The Domain atlas groups by the first directory under notes;
            # a record's domain can instead name a deeper subject folder.
            try:
                parts = PurePosixPath(record["path"]).relative_to("knowledge/notes").parts
                domain = parts[0] if len(parts) > 1 else "cross-domain"
            except ValueError:
                domain = "cross-domain"
        row = domains.setdefault(domain, {"domain": domain, "notes": 0,
                                         "crosswalks": 0, "shelves": 0, "entries": 0})
        if kind == "note":
            row["notes"] += 1
            row["crosswalks"] += record.get("role") == "crosswalk"
        else:
            row["shelves"] += 1
            row["entries"] += len(record.get("entries") or [])
    order = [*ATLAS_DOMAINS, *sorted(set(domains) - set(ATLAS_DOMAINS))]
    return [domains[domain] for domain in order]


def compact_bootstrap(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 50)
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root)
            fields = ("id", "title", "status", "module_id", "program_id", "unit_id",
                      "current_study_map", "current_stage", "needs_study_map")
            collections = {}
            for name in ("programs", "modules", "projects", "units", "study_maps"):
                rows = sorted(manifest.get(name, []), key=lambda row: row["id"])
                items = [{key: row[key] for key in fields if key in row}
                         for row in rows[offset:offset + limit]]
                collections[name] = {"items": items, "total": len(rows),
                                     "next_offset": offset + limit if offset + limit < len(rows) else None}
            return _print_stable(root, snapshot, {
                "contract": "bootstrap-summary", "collections": collections,
                "resume_pointer": manifest.get("resume_pointer", {}),
                "counts": manifest.get("counts", {}),
                "domain_atlas": _domain_glance(manifest),
                "detail": {"record": "inspect ID", "notes": "note-read NOTE_ID",
                           "content_search": "search QUERY --type note --content",
                           "capabilities": "capabilities --compact --json",
                           "continuation": "bootstrap --compact --offset NEXT_OFFSET --expected-snapshot SNAPSHOT"},
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def _note_bytes(root, note):
    path = note.path
    owner = root / "knowledge" / "notes"
    try:
        path.resolve(strict=True).relative_to(owner.resolve(strict=True))
    except (ValueError, OSError) as exc:
        raise WriteRefused("note path escapes its knowledge owner") from exc
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise WriteRefused("note read refuses symlinks")
    return path.read_bytes()


def _note_collection(root):
    """Load only the note registry for note reads/search, not a complete Repo.

    The partial model stays inside these note-only paths. Full canonical
    fingerprints still guard the read before and after, including continuation.
    """
    repo = Repo(root=root)
    load_notes(repo, root)
    return repo


def cmd_note_read(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 16000)
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = _note_collection(root)
            note = repo.notes.get(args.note_id)
            if note is None:
                raise WriteRefused(f"note not found: {args.note_id}")
            raw = _note_bytes(root, note)
            content = raw.decode("utf-8")
            return _print_stable(root, snapshot, {
                "contract": "note-content", "note_id": note.id,
                "path": note.path.relative_to(root).as_posix(),
                "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "offset": offset, "offset_unit": "unicode_characters",
                "total_characters": len(content), "start_line": content.count("\n", 0, offset) + 1,
                "content": content[offset:offset + limit],
                "next_offset": offset + limit if offset + limit < len(content) else None,
            })
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


def content_search(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 100)
        if args.type not in (None, "note"):
            raise WriteRefused("--content currently supports durable notes; use --type note")
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in args.query.split()]
        if not terms:
            raise WriteRefused("content search requires a nonempty query")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = _note_collection(root)
            # A read refuses when the failures bear on the answer it is about to
            # give, and this search is over notes: an unreadable note may be a
            # hit that never appears, while an unreadable project cannot be.
            # Refusal rather than a partial answer, because the bounded-read
            # envelope is a closed contract — a short answer here would have to
            # report itself as total.
            note_dir = root / "knowledge" / "notes"
            note_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.is_relative_to(note_dir)
            ]
            if note_failures:
                raise WriteRefused(unreadable_refusal(root, note_failures, "search"))
            matches = []
            for note in sorted(repo.notes.values(), key=lambda row: row.id):
                raw = _note_bytes(root, note)
                text = raw.decode("utf-8")
                found = [term.search(text) for term in terms]
                if not all(found):
                    continue
                positions = sorted({match.start() for match in found if match})
                snippets = []
                for position in positions[:8]:
                    start = max(text.rfind("\n", 0, position) + 1, position - 100)
                    end = text.find("\n", position)
                    end = min(end if end >= 0 else len(text), position + 180)
                    snippets.append({"line": text.count("\n", 0, position) + 1,
                                     "text": text[start:end]})
                matches.append({"id": note.id, "type": "note", "title": note.meta.get("title", note.id),
                                "path": note.path.relative_to(root).as_posix(),
                                "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                                "snippets": snippets})
            return _print_stable(root, snapshot, {
                "contract": "note-content-search", "items": matches[offset:offset + limit],
                "total": len(matches),
                "next_offset": offset + limit if offset + limit < len(matches) else None,
            })
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)
