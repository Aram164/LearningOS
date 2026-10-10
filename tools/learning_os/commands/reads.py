"""Bounded, snapshot-bound reads; complete content stays under its Core owner."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import PurePosixPath

from learning_os.derived import DerivedError, evaluate
from learning_os.domain.failures import (
    StaleSnapshot,
    WriteRefused,
    unreadable_refusal,
)
from learning_os.domain.suggest import expansion
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.genout.projection.atlas import STAGE_CONCEPT
from learning_os.loading import FRONTMATTER_RE
from learning_os.ops._legacy_plumbing import (
    SESSION_ID_ENV,
    _evidence_label,
    _fresh_manifest,
    _note_bytes,
    _note_collection,
    _operator_lock,
    _resolve_session_identity,
    _route_material_files,
    _snapshot,
    _use_evidence,
    _window_values,
)
from learning_os.search.index import NoteBlob, build_registry
from learning_os.search.model import POSTINGS_NODE_ID
from learning_os.search.query import candidates

from .support import _root


def _window(args, maximum: int) -> tuple[int, int]:
    """Temporary namespace extraction for unconverted callers (SPEC (bl)).

    Converted handlers pass their request values directly to
    ``_window_values``; this wrapper stays until the last caller converts.
    """
    return _window_values(
        args.offset, args.limit, args.expected_snapshot, maximum)


def _print_stable(root, snapshot, payload) -> int:
    _snapshot(root, snapshot)
    print(json.dumps({"schema_version": 1, "snapshot_id": snapshot, **payload},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


def _refusal(exc) -> int:
    print(f"los: {exc}", file=sys.stderr)
    return 3 if isinstance(exc, StaleSnapshot) else 2


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
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root, snapshot_id=snapshot)
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


#: What the brief's ``pointer_state`` means. A confirmed pointer is the
#: learner's last explicit study action -- where study stopped -- never a
#: recommendation. The note ships in the payload so an agent reading only
#: this page cannot mistake one for the other.
POINTER_STATE_NOTE = "confirmed = where study stopped, not a recommendation"


def _pointer_state(manifest, pointer) -> str:
    """confirmed/missing/invalid for the brief page; the same rule as resume.

    Mirrors ``resume._resolve_stage``'s validity check against the manifest
    instead of the loaded repo, so the brief and resume cannot disagree:
    the pointer counts only when its module, unit, map, and stage all
    resolve and link together. Status plays no part here, exactly as in
    resume -- a pointer to a paused map is still where study stopped.
    """
    if not isinstance(pointer, dict) or not pointer:
        return "missing"
    units = {row.get("id"): row for row in manifest.get("units", [])
             if isinstance(row, dict)}
    maps = {row.get("id"): row for row in manifest.get("study_maps", [])
            if isinstance(row, dict)}
    unit = units.get(str(pointer.get("unit_id") or ""))
    study_map = maps.get(str(pointer.get("study_map_id") or ""))
    stages = study_map.get("stages", []) \
        if isinstance(study_map, dict) else []
    stage_ids = {stage.get("id") for stage in stages
                 if isinstance(stage, dict)}
    if (isinstance(unit, dict) and isinstance(study_map, dict)
            and unit.get("module_id") == pointer.get("module_id")
            and study_map.get("unit_id") == unit.get("id")
            and study_map.get("module_id") == unit.get("module_id")
            and pointer.get("stage_id") in stage_ids):
        return "confirmed"
    return "invalid"


def _recorded_options(manifest) -> list[dict]:
    """Every active track's recorded next action, in id order, unranked.

    Shown regardless of pointer state: the pointer says where study stopped,
    not which active workspace to choose next. Each active workspace's own
    next action carries its id and source path, never a derived ranking. A
    workspace with no recorded action still appears, with an empty action,
    so no track silently drops out of the page.
    """
    options = []
    for record in manifest.get("records", []):
        if not isinstance(record, dict) or record.get("type") != "workspace":
            continue
        if record.get("archived") or record.get("status") != "active":
            continue
        options.append({
            "workspace_id": record.get("id"),
            "next_action": record.get("next_action") or "",
            "source": record.get("path") or "",
        })
    return sorted(options, key=lambda row: str(row["workspace_id"]))


def _brief_deadlines(manifest: dict) -> list[dict]:
    """Brief-visible deadlines: absence of evidence reads as a missing fact.

    The projection says ``unregistered`` for a sitting with no recorded
    attempt; the brief is the surface where that absence is most easily
    misread as a decision, so it says ``registration not recorded``
    instead. ``unrecorded`` (elapsed — the record should exist by now)
    passes through unchanged. Row count and order are preserved.
    """
    rows = []
    for row in manifest.get("academic_deadlines", []):
        if isinstance(row, dict) and row.get("registration_state") == "unregistered":
            row = {**row, "registration_state": "registration not recorded"}
        rows.append(row)
    return rows


def brief_bootstrap(args) -> int:
    """One-page session entry: guards, resume, owed work, deadlines, expands.

    The plan-edit-context-brief shape applied to startup: identities and
    runnable commands, never collections or prose. Owed study maps name the
    units to prep, active maps name the stages to resume, deadlines carry
    the structured exam spine, and every follow-up read is a listed
    command. Single page by construction: paging belongs to --compact.
    """
    if getattr(args, "compact", False):
        return _refusal("bootstrap takes one of --brief, --compact")
    if args.offset:
        return _refusal("bootstrap --brief is a single page; "
                        "page the collections with --compact instead")
    root = _root(args)
    try:
        with _operator_lock(root, shared=True):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root, snapshot_id=snapshot)
            units = sorted(manifest.get("units", []),
                           key=lambda row: row["id"])
            owed = sorted(row["id"] for row in units
                          if row.get("needs_study_map"))
            # Resumable work only: paused maps are shelved tracks, not
            # candidates for the next session. Full bootstrap still lists
            # them; the brief names what can actually start.
            active = sorted(
                ({"id": row["id"], "unit_id": row.get("unit_id"),
                  "status": row.get("status"),
                  "current_stage": row.get("current_stage")}
                 for row in manifest.get("study_maps", [])
                 if row.get("status") in {"active", "ready"}),
                key=lambda row: row["id"])
            deadlines = _brief_deadlines(manifest)
            pointer = manifest.get("resume_pointer", {})
            state = _pointer_state(manifest, pointer)
            session_id, session_source = _resolve_session_identity()
            return _print_stable(root, snapshot, {
                "contract": "bootstrap-brief",
                "session_identity": {
                    "session_id": session_id,
                    "source": session_source,
                    "how_to_set": (
                        f"name it before the first write — export "
                        f"{SESSION_ID_ENV}=<id> when the shell persists, or "
                        f"seal session_id in each write envelope "
                        f"(.venv/bin/python tools/seal_envelope.py --session-id <id>); without "
                        f"either, writes share this channel's ledger"
                    ),
                },
                "resume_pointer": pointer,
                "pointer_state": state,
                "pointer_state_note": POINTER_STATE_NOTE,
                "recorded_options": _recorded_options(manifest),
                "recorded_options_note": (
                    "workspace next actions are recorded options, not current "
                    "priorities; compare with current dates and state"
                ),
                "counts": manifest.get("counts", {}),
                "owed_study_maps": owed,
                "active_study_maps": active,
                "academic_deadlines": deadlines,
                "deadline_count": len(deadlines),
                "domain_atlas": _domain_glance(manifest),
                "expand": {
                    "full_compact": expansion(
                        "bootstrap", "--compact",
                        "--expected-snapshot", snapshot),
                    "continuation": expansion(
                        "bootstrap", "--compact", "--offset", "NEXT_OFFSET",
                        "--expected-snapshot", "SNAPSHOT"),
                    "resume": expansion("resume", "--json"),
                    "inspect": expansion("inspect", "ID"),
                    "coordination": expansion("inspect", "coordination"),
                    "intelligence_scan": expansion(
                        "intelligence-scan", "--brief", "--json"),
                    "note_read": expansion("note-read", "NOTE_ID"),
                    "inbox_list": expansion("inbox-list"),
                    "inbox_read": expansion("inbox-read", "NAME"),
                    "content_search": expansion(
                        "search", "QUERY", "--type", "note", "--content"),
                    "material_context": expansion("material-context", "QUERY"),
                    "ability_context": expansion(
                        "ability-context", "--expected-snapshot", snapshot),
                    "material_span": expansion(
                        "material-span", "UNIT_ID", "ROUTE_ID"),
                    "capability_detail": expansion(
                        "capabilities", "NAME", "--json"),
                    "plan_brief": [expansion(
                        "plan-edit-context", unit_id, "--brief",
                        "--expected-snapshot", snapshot)
                                   for unit_id in owed],
                },
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def empty_search_hint(row_word: str, terms: list[str], hits: list[int]) -> str:
    """One-line stderr disclosure for an empty literal-AND result.

    Names how many rows each term matched on its own, so the caller can
    see which term eliminated the answer. stdout shapes stay untouched.
    """
    shown = [f"{term}={count}"
             for term, count in zip(terms[:20], hits[:20], strict=True)]
    if len(terms) > 20:
        shown.append(f"+{len(terms) - 20} more")
    plural = "s" if len(terms) != 1 else ""
    return (f"no {row_word} matches all {len(terms)} term{plural}; "
            f"per-term {row_word} hits: {' '.join(shown)}")


def flatten_search_values(value) -> list[str]:
    """Every searchable scalar inside a JSON-like value, in stable order.

    THE shared search haystack (F14): metadata search flattens each record
    and content search flattens each note's frontmatter through here, so a
    key name can never match in either path. Every string, number and
    boolean is searchable — ids and paths included — while key names,
    punctuation and nulls are not.
    """
    if isinstance(value, str):
        return [value]
    if isinstance(value, bool):
        return ["true" if value else "false"]
    if isinstance(value, (int, float)):
        return [json.dumps(value, ensure_ascii=False)]
    if isinstance(value, dict):
        found: list[str] = []
        for item in value.values():
            found.extend(flatten_search_values(item))
        return found
    if isinstance(value, (list, tuple)):
        found = []
        for item in value:
            found.extend(flatten_search_values(item))
        return found
    return []


#: A frontmatter mapping key at the start of its line: `key:`, an indented
#: `nested:`, a `- listed:` pair, or a quoted key. Values stay verbatim.
_FRONTMATTER_KEY_RE = re.compile(
    r"^(\s*(?:-\s+)?)"
    r"(?:[A-Za-z0-9_][A-Za-z0-9_.\-]*|\"[^\"]*\"|'[^']*')"
    r"(\s*:)")


def _blank_frontmatter_keys(front: str) -> str:
    """The frontmatter block with every key's `name:` footprint blanked.

    Length-preserving (spaces), so positions in the blanked text are true
    file positions and snippets keep true line numbers. Values — including
    colons and quotes inside them — stay verbatim and searchable.
    """
    out = []
    for line in front.split("\n"):
        match = _FRONTMATTER_KEY_RE.match(line)
        if match:
            end = match.end(2)
            line = " " * end + line[end:]
        out.append(line)
    return "\n".join(out)


def _note_match_text(meta: dict, text: str) -> str:
    """One note's content haystack: frontmatter values plus the verbatim body.

    Values come from the loader-parsed frontmatter through the shared
    flattener, so keys never match; the body is unchanged.
    """
    front = FRONTMATTER_RE.match(text)
    body = text[front.end():] if front else text
    return "\n".join([*flatten_search_values(meta), body])


def _content_term_hits(root, ordered, terms):
    """Per-term note counts for an empty content result, or None.

    Best-effort by design: the search itself already answered [], so a
    read racing the hint must never fail the command.
    """
    try:
        hits = [0] * len(terms)
        for note in ordered:
            text = _note_match_text(
                note.meta, _note_bytes(root, note).decode("utf-8"))
            for index, term in enumerate(terms):
                if term.search(text):
                    hits[index] += 1
        return hits
    except (WriteRefused, OSError, UnicodeError):
        return None


def _match_verified(items, terms):
    """Run the current regex verification over admitted note bytes.

    ``items`` is (note id, title, repo-relative path, raw bytes, parsed
    frontmatter). Pure: every read happened before this call, so the
    indexed path verifies from discovered bytes without re-reading.
    Matching is values-only in frontmatter (the shared flattener over the
    parsed meta) plus the verbatim body; snippet positions come from the
    key-blanked raw text, so they keep true file line numbers.
    """
    matches = []
    for note_id, title, relpath, raw, meta in items:
        text = raw.decode("utf-8")
        found = [term.search(_note_match_text(meta, text)) for term in terms]
        if not all(found):
            continue
        front = FRONTMATTER_RE.match(text)
        blanked = (_blank_frontmatter_keys(text[:front.end()])
                   + text[front.end():]) if front else text
        positions = sorted({match.start() for term in terms
                            if (match := term.search(blanked)) is not None})
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


# MEASURED (S23 cold-search scaling, 2026-09-26): 145 notes 1.02s cold /
# 0.76s warm; 290 notes 1.07s / 0.84s; 725 notes 2.00s / 1.14s. Loader
# dominates (warm tracks cold); no index or rebuild work triggered.
def _exhaustive_content_search(root, ordered, terms):
    """The current implementation, kept as the differential oracle."""
    matches = []
    for note in ordered:
        raw = _note_bytes(root, note)
        matches.extend(_match_verified(
            [(note.id, note.meta.get("title", note.id),
              note.path.relative_to(root).as_posix(), raw, note.meta)], terms))
    return matches


def _indexed_content_search(root, ordered, terms, raw_terms):
    """Indexed path: derived postings narrow candidates, regex verifies.

    Reads every note once with the same admitted reader (identical
    refusals), then verifies only candidates from those bytes. A query
    the prefilter cannot narrow (None) verifies every note instead. The
    prefilter grams the full raw text — keys included — which stays a
    sound superset now that verification narrows to values plus body:
    every true match is still a candidate, and false positives verify out.
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
            [(blob.note_id, blob.title, blob.relpath, blob.raw, note.meta)],
            terms))
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
        with _operator_lock(root, shared=True):
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
            if not matches:
                hint_hits = _content_term_hits(root, ordered, terms)
                if hint_hits is not None:
                    print(f"los: {empty_search_hint('note', raw_terms, hint_hits)}",
                          file=sys.stderr)
            return _print_stable(root, snapshot, {
                "contract": "note-content-search", "items": matches[offset:offset + limit],
                "total": len(matches),
                "next_offset": offset + limit if offset + limit < len(matches) else None,
            })
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


# ------------------------------------------------------- material context
# The declared source-feedback vocabulary, grouped for ranking. Positive
# values say the source served; mismatch values say it did not fit this
# use. "skipped" is recorded evidence about the stage, not about the
# source, so it is reported and never ranks.
def _use_evidence_from_manifest(manifest: dict) -> dict[str, dict[str, int]]:
    """Recorded stage-use evidence per source id, read from the manifest.

    The same tally `_use_evidence` computes from the loaded repo: every
    study map is projected and projected stages keep `source_feedback`
    verbatim, so the two agree exactly. Lets `related` skip the repo load
    on the manifest-reuse fast path (#83).
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        for stage in study_map.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


#: Declared-edge fields walked from the record itself, in stable order.
RELATED_LIST_FIELDS = ("concepts", "sources", "contexts", "notes",
                       "program_ids", "module_ids", "unit_ids", "unit_order",
                       "related_module_ids")
RELATED_SCALAR_FIELDS = ("workspace_id", "area_id", "module_id", "unit_id",
                         "current_study_map")

#: Backlink tables walked in both directions. Every table maps an owner to
#: its members; the walk answers the direct lookup and the inverse scan, so
#: membership in one direction always implies the reverse edge (JF-15). The
#: differently-shaped concept_relations table stays out: concept relations
#: are already walked both ways from the manifest relations list.
RELATED_BACKLINK_TABLES = ("concept_to_notes", "source_to_notes",
                           "workspace_to_notes", "module_to_workspaces",
                           "unit_to_workspaces", "module_to_units",
                           "source_to_units", "note_incoming")

#: The read-time label for a note→source analysis edge (#81). The edge says
#: "this note analyses pages of that source", not "this note cites it".
ANALYSES_VIA = "analyses"


def _analysis_source_of(record) -> str | None:
    """The registered source a record's resolved analysis binds, or None."""
    binding = record.get("material_analysis") if isinstance(record, dict) else None
    if not isinstance(binding, dict) or binding.get("resolution") != "resolved":
        return None
    source_id = binding.get("source_id")
    return source_id if isinstance(source_id, str) else None


def related_records(manifest: dict, raw_id: str, repo=None, *, tallies=None) -> list[dict]:
    """Ranked one-hop connections for one record id.

    Pure over the manifest (plus recorded use-evidence tallied from the
    repo when given, or the precomputed `tallies` when the caller read
    them from the manifest instead): the record's own declared edges,
    every backlink table in both directions, concept relations both ways,
    project relationships both ways, and the published module-concept
    edges between a concept and the units whose stages tag it (each edge
    reasoned by its stage, `stage-concept:<stage-id>`). Unknown ids
    answer [] — the caller owns the not-found error. Aliases resolve
    through project_aliases.

    Ranking is deterministic: more distinct edges first, then recorded
    stage use-evidence per source exactly as material-context ranks it
    (positive counts first, mismatch counts last), then stable id order.
    Each result names the edges that produced it in `via`. A source↔note
    edge through `source_to_notes` gains the additional `analyses` token
    when the note's resolved material analysis binds that source (#81).
    """
    by_id = {r.get("id"): r for r in manifest.get("records", [])}
    resolved = (manifest.get("project_aliases") or {}).get(raw_id, raw_id)
    rec = by_id.get(resolved)
    if rec is None:
        return []
    reasons: dict[str, set[str]] = {}

    def link(rid, why):
        if isinstance(rid, str) and rid in by_id:
            reasons.setdefault(rid, set()).add(why)

    for key in RELATED_LIST_FIELDS:
        for rid in rec.get(key, []) or []:
            link(rid, key)
    for key in RELATED_SCALAR_FIELDS:
        if rec.get(key):
            link(rec[key], key)
    backlinks = manifest.get("backlinks", {}) or {}
    for table in RELATED_BACKLINK_TABLES:
        members = (backlinks.get(table) or {}).get(resolved, []) or []
        for rid in members:
            link(rid, f"backlink:{table}")
            if table == "source_to_notes" \
                    and _analysis_source_of(by_id.get(rid)) == resolved:
                link(rid, ANALYSES_VIA)
        for owner, owned in ((backlinks.get(table) or {}).items()):
            if isinstance(owned, list) and resolved in owned:
                link(owner, f"inverse:{table}")
                if table == "source_to_notes" \
                        and _analysis_source_of(by_id.get(resolved)) == owner:
                    link(owner, ANALYSES_VIA)
    for relation in manifest.get("relations", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from") == resolved:
            link(relation.get("to"), "relation")
        if relation.get("to") == resolved:
            link(relation.get("from"), "relation")
    # Stage concept tags ride the published module-concept edges (#97): a
    # concept links to the units whose stages tag it, and a unit links to
    # its stages' concepts, each edge reasoned by its exact stage. Stages
    # are structural sub-ids, not records, so they reason the edge rather
    # than row in it. Knowledge-node evidence stays out: the edge kind and
    # the issue scope are stage tags only.
    for edge in manifest.get("module_concept_edges", []) or []:
        if not isinstance(edge, dict):
            continue
        concept_id = edge.get("concept_id")
        for evidence in edge.get("evidence") or []:
            if not isinstance(evidence, dict):
                continue
            if evidence.get("kind") != STAGE_CONCEPT:
                continue
            unit_id = evidence.get("unit_id")
            stage_id = evidence.get("stage_id")
            if not unit_id or not stage_id:
                continue
            reason = f"{STAGE_CONCEPT}:{stage_id}"
            if resolved == concept_id:
                link(unit_id, reason)
            if resolved == unit_id:
                link(concept_id, reason)
    for relation in manifest.get("project_relationships", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from_project_id") == resolved:
            link(relation.get("to_id"), "project_relationship")
        if relation.get("to_id") == resolved:
            link(relation.get("from_project_id"), "project_relationship")
    if repo is not None:
        tallies = _use_evidence(repo)
    elif tallies is None:
        tallies = {}
    ranked = []
    for rid, whys in reasons.items():
        tally = tallies.get(rid, {}) if by_id[rid].get("type") == "source" else {}
        label = _evidence_label(tally)
        ranked.append((-len(whys), -label["positive"], label["mismatch"], rid))
    ranked.sort()
    return [{"id": rid, "type": by_id[rid].get("type"),
             "title": by_id[rid].get("title"), "path": by_id[rid].get("path"),
             "via": sorted(reasons[rid])}
            for _, _, _, rid in ranked]


def _route_material_file(repo, source_id, route) -> str | None:
    """The materials-relative file one route reads, or None when unprovable.

    Single-file view of `_route_material_files`: exactly one proven file
    returns it, zero or several prove no single file.
    """
    files = _route_material_files(repo, source_id, route)
    return next(iter(files)) if len(files) == 1 else None


#: How many stage hops one concept match explains itself with. The join
#: is concept -> stage -> route -> source, all declared edges; the list is
#: sorted stage ids, so the cap only trims the tail of a long join.
