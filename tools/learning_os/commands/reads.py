"""Bounded, snapshot-bound reads; complete content stays under its Core owner."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import PurePosixPath

from learning_os.derived import DerivedError, evaluate
from learning_os.errors import unreadable_refusal
from learning_os.fingerprint import canonical_fingerprint
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.loader import load_repo
from learning_os.loading import Repo, load_notes
from learning_os.material_analysis import observe_local_material
from learning_os.search.index import NoteBlob, build_registry
from learning_os.search.model import POSTINGS_NODE_ID
from learning_os.search.query import candidates

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


def _match_verified(items, terms):
    """Run the current regex verification over admitted note bytes.

    ``items`` is (note id, title, repo-relative path, raw bytes). Pure:
    every read happened before this call, so the indexed path verifies
    from discovered bytes without re-reading.
    """
    matches = []
    for note_id, title, relpath, raw in items:
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
        matches.append({"id": note_id, "type": "note", "title": title,
                        "path": relpath,
                        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                        "snippets": snippets})
    return matches


def _exhaustive_content_search(root, ordered, terms):
    """The current implementation, kept as the differential oracle."""
    matches = []
    for note in ordered:
        raw = _note_bytes(root, note)
        matches.extend(_match_verified(
            [(note.id, note.meta.get("title", note.id),
              note.path.relative_to(root).as_posix(), raw)], terms))
    return matches


def _indexed_content_search(root, ordered, terms, raw_terms):
    """Indexed path: derived postings narrow candidates, regex verifies.

    Reads every note once with the same admitted reader (identical
    refusals), then verifies only candidates from those bytes. A query
    the prefilter cannot narrow (None) verifies every note instead.
    """
    blobs = {}
    for note in ordered:
        blobs[note.id] = NoteBlob(
            note_id=note.id,
            relpath=note.path.relative_to(root).as_posix(),
            title=note.meta.get("title", note.id),
            raw=_note_bytes(root, note))
    registry, inputs = build_registry(list(blobs.values()))
    postings = evaluate(root, POSTINGS_NODE_ID, registry=registry, inputs=inputs).value
    shortlist = candidates(root, postings, raw_terms)
    if shortlist is None:
        selected = ordered
    else:
        wanted = set(shortlist)
        selected = [note for note in ordered if note.id in wanted]
    matches = []
    for note in selected:
        blob = blobs[note.id]
        matches.extend(_match_verified(
            [(blob.note_id, blob.title, blob.relpath, blob.raw)], terms))
    return matches


def content_search(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 100)
        if args.type not in (None, "note"):
            raise WriteRefused("--content currently supports durable notes; use --type note")
        raw_terms = args.query.split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
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
            ordered = sorted(repo.notes.values(), key=lambda row: row.id)
            try:
                matches = _indexed_content_search(root, ordered, terms, raw_terms)
            except DerivedError:
                # The index is a pure accelerator: any cache failure
                # (tampering already self-healed before raising) falls
                # back to the exhaustive implementation, never to a
                # partial answer. Bytes/symlink refusals are not
                # DerivedError and still propagate unchanged.
                matches = _exhaustive_content_search(root, ordered, terms)
            return _print_stable(root, snapshot, {
                "contract": "note-content-search", "items": matches[offset:offset + limit],
                "total": len(matches),
                "next_offset": offset + limit if offset + limit < len(matches) else None,
            })
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


# ------------------------------------------------------- material context
ASSESSMENT_TEXT_FIELDS = ("contribution", "assumptions", "notation",
                          "exercise_value", "best_for", "limitations",
                          "locator")


def _resolve_concept(repo, raw):
    """A concept id or declared alias, matched case-insensitively."""
    if raw in repo.concepts:
        return raw
    lowered = raw.casefold()
    hits = [cid for cid, concept in repo.concepts.items()
            if isinstance(concept, dict)
            and any(str(alias).casefold() == lowered
                    for alias in (concept.get("aliases") or []))]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise WriteRefused(f"unknown concept: {raw!r} matches no id or declared alias")
    raise WriteRefused(f"concept {raw!r} is ambiguous across {len(hits)} concepts; use an id")


def _analysis_notes(repo):
    return sorted((note for note in repo.notes.values()
                   if isinstance(note.meta.get("material_analysis"), dict)),
                  key=lambda note: note.id)


def _approved_assessments(repo):
    found = []
    for synthesis_id in sorted(repo.unit_material_syntheses):
        data = repo.unit_material_syntheses[synthesis_id]
        if not isinstance(data, dict) or data.get("status") != "approved":
            continue
        unit_id = data.get("unit_id")
        assessments = data.get("route_assessments")
        if not isinstance(assessments, list):
            continue
        for assessment in assessments:
            if isinstance(assessment, dict):
                found.append((synthesis_id, unit_id, assessment))
    found.sort(key=lambda row: (row[1] or "", row[2].get("route_id") or ""))
    return found


def _freshness_label(root, binding):
    """Live source freshness: current, stale, or unreadable. Never inferred."""
    observation = observe_local_material(
        root.parent / "materials", str(binding.get("material") or ""),
        str(binding.get("recorded_source_digest") or ""))
    status = observation["status"]
    if status in ("current", "stale"):
        return status
    return "unreadable"


def _note_purpose_hit(binding, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    anchors = binding.get("anchors")
    if not isinstance(anchors, list):
        return False
    return any(wanted in str(anchor.get("purpose", "")).casefold()
               for anchor in anchors if isinstance(anchor, dict))


def _assessment_purpose_hit(assessment, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    return any(wanted in str(assessment.get(field) or "").casefold()
               for field in ("best_for", "exercise_value"))


def cmd_material_context(args) -> int:
    """Find saved explanations from an explanation need.

    Corpus: durable analysis notes plus the route assessments of approved
    unit syntheses. Matching is deterministic lexical AND over terms, with
    declared concept aliases, purpose substrings, and unit scope as filters.
    Order is stable (notes by id, then assessments by unit and route).
    Freshness is observed live per result; review state and resolution are
    reported, never inferred. An empty result describes the searched
    records only — never proof that no source explains the topic.
    """
    root = _root(args)
    try:
        offset, limit = _window(args, 20)
        raw_terms = (args.query or "").split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        if not terms:
            raise WriteRefused("material context requires a nonempty query")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            note_dir = root / "knowledge" / "notes"
            note_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.is_relative_to(note_dir)
            ]
            if note_failures:
                raise WriteRefused(unreadable_refusal(root, note_failures, "context"))
            synthesis_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.name == "material-synthesis.yaml"
            ]
            if synthesis_failures:
                raise WriteRefused(unreadable_refusal(root, synthesis_failures, "context"))
            concept_id = _resolve_concept(repo, args.concept) \
                if args.concept else None
            if args.unit and args.unit not in repo.units:
                raise WriteRefused(f"unknown unit: {args.unit!r}")
            assessments = _approved_assessments(repo)
            if args.unit:
                assessments = [row for row in assessments if row[1] == args.unit]
                unit_sources = {row[2].get("source_id") for row in assessments}
                notes = [note for note in _analysis_notes(repo)
                         if note.meta["material_analysis"].get("source_id") in unit_sources]
            else:
                notes = _analysis_notes(repo)
            if concept_id is not None:
                notes = [note for note in notes
                         if concept_id in (note.meta.get("concepts") or [])]
                assessments = [row for row in assessments
                               if concept_id in (row[2].get("concept_ids") or [])]
            notes = [note for note in notes
                     if _note_purpose_hit(note.meta["material_analysis"], args.purpose)]
            assessments = [row for row in assessments
                           if _assessment_purpose_hit(row[2], args.purpose)]
            pool = {
                "analysis_notes": len(notes),
                "assessments": len(assessments),
                "analysis_by_resolution": {},
                "analysis_unreviewed": 0,
            }
            for note in notes:
                binding = note.meta["material_analysis"]
                resolution = binding.get("resolution")
                pool["analysis_by_resolution"][resolution] = \
                    pool["analysis_by_resolution"].get(resolution, 0) + 1
                if note.meta.get("semantic_review") == "unreviewed":
                    pool["analysis_unreviewed"] += 1
            items = []
            for note in notes:
                raw = _note_bytes(root, note)
                text = raw.decode("utf-8")
                matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
                           if regex.search(text)]
                if len(matched) != len(raw_terms):
                    continue
                binding = note.meta["material_analysis"]
                inspected = binding.get("inspected_range") or {}
                verified = _match_verified(
                    [(note.id, note.meta.get("title", note.id),
                      note.path.relative_to(root).as_posix(), raw)], terms)
                reasons = {"terms": matched}
                if concept_id is not None:
                    reasons["concept"] = concept_id
                if args.purpose:
                    reasons["purpose"] = args.purpose
                if args.unit:
                    reasons["unit"] = args.unit
                items.append({
                    "origin": "analysis-note",
                    "id": note.id, "title": note.meta.get("title", note.id),
                    "path": note.path.relative_to(root).as_posix(),
                    "match": {**reasons,
                              "snippets": verified[0]["snippets"] if verified else []},
                    "source": {
                        "ref": binding.get("material"),
                        "pages": [inspected.get("start"), inspected.get("end")],
                        "freshness": _freshness_label(root, binding),
                    },
                    "review": {
                        "semantic_review": note.meta.get("semantic_review"),
                        "resolution": binding.get("resolution"),
                    },
                    "anchors": binding.get("anchors") or [],
                })
            for synthesis_id, unit_id, assessment in assessments:
                joined = "\n".join(str(assessment.get(field) or "")
                                   for field in ASSESSMENT_TEXT_FIELDS)
                matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
                           if regex.search(joined)]
                if len(matched) != len(raw_terms):
                    continue
                excerpts = []
                for field in ASSESSMENT_TEXT_FIELDS:
                    if len(excerpts) >= 3:
                        break
                    value = str(assessment.get(field) or "")
                    if value and any(regex.search(value) for regex in terms):
                        excerpts.append({"field": field, "text": value[:200]})
                reasons = {"terms": matched}
                if concept_id is not None:
                    reasons["concept"] = concept_id
                if args.purpose:
                    reasons["purpose"] = args.purpose
                if args.unit:
                    reasons["unit"] = args.unit
                origin = repo.unit_material_synthesis_origins.get(synthesis_id)
                items.append({
                    "origin": "unit-assessment",
                    "unit_id": unit_id, "synthesis_id": synthesis_id,
                    "route_id": assessment.get("route_id"),
                    "source_id": assessment.get("source_id"),
                    "locator": assessment.get("locator"),
                    "review_status": assessment.get("review_status"),
                    "concept_ids": assessment.get("concept_ids") or [],
                    "match": {**reasons, "excerpts": excerpts},
                    "open": {
                        "synthesis": origin.relative_to(root).as_posix()
                        if origin is not None else None,
                        "route_id": assessment.get("route_id"),
                    },
                })
            payload = {
                "contract": "material-context", "items": items[offset:offset + limit],
                "total": len(items),
                "next_offset": offset + limit if offset + limit < len(items) else None,
                "searched": {
                    "query_terms": raw_terms, "concept": concept_id,
                    "purpose": args.purpose, "unit": args.unit,
                    "analysis_notes": len(_analysis_notes(repo)),
                    "assessments": len(_approved_assessments(repo)),
                },
                "pool": pool,
            }
            if not items:
                payload["empty"] = (
                    "no match in the searched records; this never proves "
                    "no source explains the topic")
            return _print_stable(root, snapshot, payload)
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)
