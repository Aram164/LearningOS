"""Notes-area converted handlers (PLAN D4)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import jsonschema

from learning_os.app.context import OpContext
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.handlers._shared import NOTES_PREFIX
from learning_os.app.handlers._shared import content_envelope as _content_envelope
from learning_os.app.handlers._shared import discovery_row as _discovery_row
from learning_os.app.handlers._shared import inbox_search_rows as _inbox_search_rows
from learning_os.app.handlers._shared import window_values as _window_values
from learning_os.app.projection import fresh_manifest as _fresh_manifest
from learning_os.app.proposal import Presentation, Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.garden import garden_id
from learning_os.derive.search.index import NoteBlob, build_registry
from learning_os.derive.search.model import POSTINGS_NODE_ID
from learning_os.derive.search.query import candidates
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused, unreadable_refusal
from learning_os.domain.snapshot import Repo
from learning_os.domain.suggest import expansion, not_found, suggest
from learning_os.domain.vocabulary import EVIDENCE_SCHEMES, FRONTMATTER_RE
from learning_os.store import observations
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.derived import DerivedError, evaluate
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.fs import bytes_inside_owner as _bytes_inside_owner
from learning_os.store.fs import note_bytes as _note_bytes
from learning_os.store.loader import LoaderError, parse_frontmatter
from learning_os.store.loading import load_garden, load_notes
from learning_os.store.transactions import parse_expected_revisions


def _render_frontmatter(meta: dict, body: str) -> str:
    """Frontmatter plus body, the commands.support formula.

    The shared original stays for unconverted callers; an upward import
    is not available here, so its one-line formula over the downward
    ``_dump_yaml`` is repeated verbatim.
    """
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


@register("note.evidence.add", kind="command")
def note_evidence(ctx: OpContext, req: dict) -> Result:
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
    if not req["ref"].startswith(EVIDENCE_SCHEMES):
        raise WriteRefused(
            f"evidence ref '{req['ref']}' uses no valid URI scheme",
            site=f"{ctx.operation}.bad-scheme",
            extra_stderr=("     expected one of: " + ", ".join(EVIDENCE_SCHEMES),),
            gateway_message=(
                f"los: evidence ref '{req['ref']}' uses no valid URI scheme\n"
                "     expected one of: " + ", ".join(EVIDENCE_SCHEMES)
            ),
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    note = repo.notes.get(req["note_id"])
    if note is None:
        message = not_found("note", req["note_id"], repo.notes)
        raise NotFound(
            "note", req["note_id"], repo.notes,
            site=f"{ctx.operation}.unknown-note",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    content = note.path.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(content, note.path)
    except LoaderError as exc:
        raise WriteRefused(
            f"cannot read note frontmatter: {exc}",
            site=f"{ctx.operation}.unreadable-frontmatter",
            prefixed=True,
            exit_code=2,
        ) from exc
    existing = list(meta.get("evidence") or [])
    entry = {"type": req["evidence_type"], "ref": req["ref"]}
    if any(e.get("type") == entry["type"] and e.get("ref") == entry["ref"]
           for e in existing):
        raise WriteRefused(
            "that evidence is already recorded on this note",
            site=f"{ctx.operation}.already-recorded",
            prefixed=True,
            exit_code=2,
        )
    meta["evidence"] = existing + [entry]
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "note_id": req["note_id"],
         "path": note.path.relative_to(ctx.root).as_posix(),
         "evidence": entry,
         "evidence_count": len(meta["evidence"]),
         "scheme": req["ref"].split("://", 1)[0]},
        proposal=TransactionProposal(
            capability="note.evidence.add",
            writes={note.path: _render_frontmatter(meta, body)},
            artifact_ids=[req["note_id"]],
            expected_revisions=expected_revisions,
        ),


    )




@register("note.revise", kind="command")
def note_revise(ctx: OpContext, req: dict) -> Result:
    """Replace one existing note after explicit, reviewable approval.

    IDs, paths, and roles are held stable; this is a semantic revision gateway,
    not a rename, move, role change, merge, or split operation.
    """
    if not req.get("approve"):
        raise WriteRefused(
            "note revision requires --approve after reviewing the full replacement",
            site=f"{ctx.operation}.needs-approve",
            prefixed=True,
            exit_code=2,
        )
    try:
        source, content_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="revised note file",
        )
        content = content_bytes.decode("utf-8")
    except (UnicodeDecodeError, WriteRefused) as exc:
        raise WriteRefused(
            f"cannot read revised note: {exc}",
            site=f"{ctx.operation}.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    note = repo.notes.get(req["note_id"])
    if note is None:
        message = not_found("note", req["note_id"], repo.notes)
        raise NotFound(
            "note", req["note_id"], repo.notes,
            site=f"{ctx.operation}.unknown-note",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    try:
        meta, _ = parse_frontmatter(content, source)
    except LoaderError as exc:
        raise WriteRefused(
            f"invalid revised note: {exc}",
            site=f"{ctx.operation}.invalid-note",
            prefixed=True,
            exit_code=2,
        ) from exc
    if meta.get("id") != req["note_id"] or meta.get("type") != "note":
        raise WriteRefused(
            "revised note must preserve the requested note id and type",
            site=f"{ctx.operation}.id-mismatch",
            prefixed=True,
            exit_code=2,
        )
    if meta.get("role") != note.meta.get("role"):
        raise WriteRefused(
            "note-revise cannot change a note role",
            site=f"{ctx.operation}.role-change",
            prefixed=True,
            exit_code=2,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "note_id": req["note_id"],
         "path": note.path.relative_to(ctx.root).as_posix()},
        proposal=TransactionProposal(
            capability="note.revise",
            writes={note.path: content.rstrip() + "\n"},
            artifact_ids=[req["note_id"]],
            expected_revisions=expected_revisions,
        ),


    )


#: Caller-supplied fields of the ``note`` object, in published order;
#: anything else refuses. Authorship, review state, timestamps, bindings,
#: and evidence are owned by the handler and can never be supplied —
#: mirroring note.analysis.save.
NOTE_FIELDS_ORDERED = (
    "id", "title", "path", "role", "concepts", "sources", "contexts",
    "supersedes",
)
NOTE_FIELDS = frozenset(NOTE_FIELDS_ORDERED)

#: Stored-record fields the handler sets on every created note. An agent
#: that reads ``system/schema/note.schema.json`` meets them as required;
#: sending them refuses, so the refusal names them alongside the accepted
#: input fields instead of leaving the schema to mislead.
NOTE_HANDLER_OWNED = ("type", "created", "state", "authorship", "semantic_review")

#: Roles with a dedicated authoring capability keep it. A general creation
#: path must not mint reference notes without a material_analysis binding
#: or question notes without the Atlas wording/target preservation.
RESERVED_ROLES = {
    "reference": "note.analysis.save",
    "question": "atlas.question.save",
}


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(
                f"note create cannot use a symlink: {relative}",
                site="note.create.symlink-path",
            )
    return path


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(
            f"{name}: {exc.message}",
            site="note.create.bad-note-schema",
        ) from exc


def _render_exact_note(meta: dict, body: bytes) -> bytes:
    """Frontmatter plus the body bytes verbatim.

    Unlike the evidence renderer this never strips leading whitespace: the
    bytes after the frontmatter block are exactly the approved capture.
    """
    front = "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n"
    return front.encode("utf-8") + body


def _destination(root: Path, note_id: str, relpath: object) -> Path:
    if not isinstance(relpath, str) or not relpath:
        raise WriteRefused(
            "note path must be a repo-relative note path",
            site="note.create.bad-path",
        )
    relative = Path(relpath)
    if relative.is_absolute() or ".." in relative.parts:
        raise WriteRefused(
            "note path must stay inside knowledge/notes/",
            site="note.create.path-escape",
        )
    if relative.suffix != ".md" or relative.stem != note_id:
        raise WriteRefused(
            "note filename must be the note id with .md",
            site="note.create.bad-filename",
        )
    try:
        relative.relative_to(NOTES_PREFIX)
    except ValueError:
        raise WriteRefused(
            "note path must stay inside knowledge/notes/",
            site="note.create.path-outside-notes",
        ) from None
    return _safe(root, root / relative)


def _id_list(note: dict, field: str) -> list[str]:
    value = note.get(field)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise WriteRefused(
            f"note {field} must be a list of ids",
            site="note.create.bad-id-list",
        )
    return value


def _precheck_note(note: object, body: bytes) -> dict:
    """Record shape and frozen-byte agreement, before the snapshot guard.

    Everything needing the loaded repository — id collision, reference
    registration, supersedes existence — stays in `_resolve_note_create`,
    inside the guard.
    """
    if not isinstance(note, dict):
        raise WriteRefused(
            "note must be an object",
            site="note.create.not-an-object",
        )
    unknown = set(note) - NOTE_FIELDS
    if unknown:
        raise WriteRefused(
            "note has unknown fields: " + ", ".join(sorted(unknown))
            + f" (accepted: {', '.join(NOTE_FIELDS_ORDERED)}; "
            + f"{'/'.join(NOTE_HANDLER_OWNED)} are set by the handler)",
            site="note.create.unknown-fields",
        )
    if not isinstance(note.get("id"), str):
        raise WriteRefused(
            "note needs a string id",
            site="note.create.id-not-string",
        )
    if not body:
        raise WriteRefused(
            "note body is empty",
            site="note.create.empty-body",
        )
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        raise WriteRefused(
            "note body is not valid UTF-8",
            site="note.create.body-not-utf8",
        ) from None
    role = note.get("role", "synthesis")
    if not isinstance(role, str):
        raise WriteRefused(
            "note role must be a string",
            site="note.create.role-not-string",
        )
    if role in RESERVED_ROLES:
        raise WriteRefused(
            f"role {role!r} keeps its dedicated capability; use {RESERVED_ROLES[role]}",
            site="note.create.reserved-role",
        )
    if not isinstance(note.get("title"), str) or not note["title"].strip():
        raise WriteRefused(
            "new notes require a title",
            site="note.create.blank-title",
        )
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
            f"note id {note_id!r} already exists; revise it with note.revise",
            site="note.create.id-collision",
        )
    path = _destination(root, note_id, note.get("path"))
    if path.exists():
        raise WriteRefused(
            "note destination already exists",
            site="note.create.destination-exists",
        )
    for concept_id in _id_list(note, "concepts"):
        if concept_id not in repo.concepts:
            raise WriteRefused(
                f"note concept is not registered: {concept_id!r}",
                site="note.create.unknown-concept",
            )
    for source_id in _id_list(note, "sources"):
        if source_id not in repo.sources:
            raise WriteRefused(
                f"note source is not registered: {source_id!r}",
                site="note.create.unknown-source",
            )
    for context_id in _id_list(note, "contexts"):
        if context_id not in repo.workspaces:
            raise WriteRefused(
                f"note context is not a workspace: {context_id!r}",
                site="note.create.unknown-context",
            )
    supersedes = _id_list(note, "supersedes")
    if note_id in supersedes:
        raise WriteRefused(
            "a note cannot supersede itself",
            site="note.create.self-supersedes",
        )
    for old_id in supersedes:
        if old_id not in repo.notes:
            raise WriteRefused(
                f"superseded note does not exist: {old_id!r}",
                site="note.create.unknown-supersedes",
            )
    meta = {"id": note_id, "type": "note", "role": note.get("role", "synthesis"),
            "title": note["title"], "created": observations.today().isoformat(),
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
                f"cannot read superseded note {old_id!r}: {exc}",
                site="note.create.unreadable-superseded",
            ) from exc
        if old_meta.get("state") != "deprecated":
            old_meta["state"] = "deprecated"
            deprecations[old.path] = _render_frontmatter(old_meta, old_body)
    return note_id, path, _render_exact_note(meta, body), deprecations


@register("note.create", kind="command")
def note_create(ctx: OpContext, req: dict) -> Result:
    """Create one durable note from approved bytes.

    The governed form of WORKFLOWS §3: capture and scratch become durable
    understanding only through this capability (or the semantically narrower
    note.analysis.save, atlas.question.save, and shelving review.apply).
    Authorship and review defaults are owned by this handler; the body is
    preserved verbatim and bound to the approved SHA-256. A successor note
    declares `supersedes` and deprecates its predecessors atomically; the
    reverse link stays generated, never stored (ARCHITECTURE §5.5).
    """
    root = ctx.root
    try:
        _, body = _read_content_bound_file(
            req["body_file"], req.get("body_file_sha256"),
            label="note body file")
    except WriteRefused as exc:
        exc.site = "note.create.bad-body-file"
        raise
    note = _precheck_note(req["note"], body)
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    note_id, path, content, deprecations = _resolve_note_create(
        root, repo, note, body)
    writes: dict[Path, str | bytes] = {path: content}
    writes.update(deprecations)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="note.create.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "note_id": note_id,
         "note_path": path.relative_to(root).as_posix(),
         "deprecated": sorted(old.relative_to(root).as_posix()
                              for old in deprecations)},
        proposal=TransactionProposal(
            capability="note.create",
            writes=writes,
            artifact_ids=[note_id, *_id_list(note, "supersedes")],
            expected_revisions=expected_revisions,
        ),


    )


def _garden_notes(root):
    """(stable id, note) pairs for every garden seed.

    Loaded lazily on a durable-note miss, so the registered-note path —
    including its parse-only-notes budget — never pays for the garden.
    Identity is the same ``garden_id`` the manifest projects, so search
    rows and this read cannot disagree about what an id names.
    """
    repo = Repo(root=root)
    load_garden(repo, root)
    garden_root = root / "knowledge" / "garden"
    return [(garden_id(garden_root, note.path), note)
            for note in repo.garden_notes]


@register("note.content", kind="query")
def note_read(ctx: OpContext, req: dict) -> Result:
    """Read a bounded segment of a durable note or garden seed by stable ID."""
    root = ctx.root
    try:
        offset, limit = _window_values(
            req["offset"], req["limit"], req.get("expected_snapshot"), 16000)
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        repo = _note_collection(root)
        note = repo.notes.get(req["note_id"])
        if note is None:
            seeds = _garden_notes(root)
            garden = next((seed for stable_id, seed in seeds
                           if stable_id == req["note_id"]), None)
            if garden is None:
                candidates = [*repo.notes, *[stable_id for stable_id, _ in seeds]]
                message = not_found("note", req["note_id"], candidates)
                raise NotFound(
                    "note", req["note_id"], candidates,
                    site="note.content.unknown-note",
                    gateway_message=f"los: {message}",
                    exit_code=2,
                )
            raw = _bytes_inside_owner(
                root, garden.path, root / "knowledge" / "garden",
                escape="garden path escapes its garden owner",
                symlink="garden read refuses symlinks")
            content = raw.decode("utf-8")
            payload = _content_envelope(
                "note-content", "note_id", req["note_id"],
                garden.path.relative_to(root).as_posix(),
                raw, content, offset, limit)
            _snapshot(root, snapshot)
            return Result(
                {"schema_version": 1, "snapshot_id": snapshot, **payload},

            )
        raw = _note_bytes(root, note)
        content = raw.decode("utf-8")
        payload = _content_envelope(
            "note-content", "note_id", note.id,
            note.path.relative_to(root).as_posix(),
            raw, content, offset, limit)
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site="note.content.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="note.content.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    except UnicodeError as exc:
        raise WriteRefused(
            str(exc),
            site="note.content.bad-encoding",
            prefixed=True,
            exit_code=2,
        ) from exc


#: Every record family ``search --type`` accepts: the manifest's
#: record types plus the two virtual discovery rows (garden seeds and
#: inbox files). An unknown value refuses with exit 2 instead of
#: answering an empty result, so ``total: 0`` always means "valid
#: filter, no matches". A test pins this set against the live
#: manifest's types, so a new record family updates it explicitly.
VALID_RECORD_TYPES = frozenset({
    "collection", "compatibility-alias", "concept", "coordination",
    "garden-note", "inbox-item", "module", "module-source-map", "note",
    "program", "project", "project-relationship", "source", "study-map",
    "topic-pack", "unit", "unit-material-synthesis", "workspace",
})


def _unknown_record_type(value: str) -> str:
    """Refusal for a mistyped ``--type``: suggestions plus the valid list."""
    hints = suggest(value, VALID_RECORD_TYPES)
    message = f"unknown record type: {value}"
    if hints:
        return (f"{message} (did you mean: {', '.join(hints)}? "
                f"valid types: {', '.join(sorted(VALID_RECORD_TYPES))})")
    return f"{message} (valid types: {', '.join(sorted(VALID_RECORD_TYPES))})"


def _array_window(req) -> tuple[int, int]:
    """Offset/limit check for the legacy array response: unbounded, valid only."""
    offset, limit = req["offset"], req["limit"]
    if offset < 0 or limit < 1:
        raise WriteRefused("offset must be nonnegative and limit at least 1")
    return offset, limit


def _metadata_matches(root: Path, req, snapshot: str) -> tuple[list[dict], list[str], list[int]]:
    """Literal-AND metadata matches in deterministic manifest order.

    Shared by the legacy array response and the opt-in page packet, so the
    two cannot disagree about what matches. An inbox listing failure refuses
    here: discovery must not silently omit drops. The caller's snapshot is
    shared with the manifest read so one search hashes once, not twice.
    """
    manifest = _fresh_manifest(root, snapshot_id=snapshot)
    words = [w for w in req["query"].lower().split() if w]
    rows = list(manifest["records"])
    if not req["type"] or req["type"] == "garden-note":
        rows.extend(manifest.get("garden_entries", []) or [])
    if not req["type"] or req["type"] == "inbox-item":
        try:
            rows.extend(_inbox_search_rows(root))
        except OSError as exc:
            raise WriteRefused(f"cannot list work/inbox: {exc}") from exc
    matches = []
    hits = [0] * len(words)
    for rec in rows:
        if req["type"] and rec.get("type") != req["type"]:
            continue
        hay = "\n".join(flatten_search_values(rec)).lower()
        found = [word in hay for word in words]
        for index, hit in enumerate(found):
            if hit:
                hits[index] += 1
        if all(found):
            matches.append(_discovery_row(rec))
    return matches, words, hits


def _metadata_next_command(req, limit: int, next_offset: int, snapshot: str) -> str:
    parts = ["search", req["query"]]
    if req["type"]:
        parts += ["--type", req["type"]]
    parts += ["--page", "--limit", str(limit), "--offset", str(next_offset),
              "--expected-snapshot", snapshot]
    return expansion(*parts)


def _metadata_search_page(ctx: OpContext, req: dict) -> Result:
    """Opt-in paged metadata packet: totals and a snapshot-bound continuation."""
    root = ctx.root
    try:
        offset, limit = _window_values(
            req["offset"], req["limit"], req.get("expected_snapshot"), 100)
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        matches, words, hits = _metadata_matches(root, req, snapshot)
        notices = []
        if not matches and words:
            notices.append(
                f"los: {empty_search_hint('record', words, hits)}")
        total = len(matches)
        items = matches[offset:offset + limit]
        next_offset = offset + limit if offset + limit < total else None
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "metadata-search-page",
             "items": items, "total": total,
             "offset": offset, "returned": len(items),
             "next_offset": next_offset,
             "has_more": next_offset is not None,
             "expand": {"next": _metadata_next_command(req, limit, next_offset, snapshot)
                        if next_offset is not None else None}},
            human_view=Presentation(notices=tuple(notices)),

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site="note.search.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="note.search.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


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


def _note_collection(root):
    """Load only the note registry for note reads/search, not a complete Repo.

    The partial model stays inside these note-only paths. Full canonical
    fingerprints still guard the read before and after, including continuation.
    """
    repo = Repo(root=root)
    load_notes(repo, root)
    return repo


def _content_search(ctx: OpContext, req: dict) -> Result:
    root = ctx.root
    try:
        offset, limit = _window_values(
            req["offset"], req["limit"], req.get("expected_snapshot"), 100)
        if req["type"] not in (None, "note"):
            raise WriteRefused(
                "--content currently supports durable notes; use --type note")
        raw_terms = req["query"].split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        if not terms:
            raise WriteRefused("content search requires a nonempty query")
        snapshot = _snapshot(root, req.get("expected_snapshot"))
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
        notices = []
        if not matches:
            hint_hits = _content_term_hits(root, ordered, terms)
            if hint_hits is not None:
                notices.append(
                    f"los: {empty_search_hint('note', raw_terms, hint_hits)}")
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot,
             "contract": "note-content-search",
             "items": matches[offset:offset + limit],
             "total": len(matches),
             "next_offset": offset + limit if offset + limit < len(matches) else None},
            human_view=Presentation(notices=tuple(notices)),

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site="note.search.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="note.search.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    except UnicodeError as exc:
        raise WriteRefused(
            str(exc),
            site="note.search.bad-encoding",
            prefixed=True,
            exit_code=2,
        ) from exc


@register("note.search", kind="query")
def search(ctx: OpContext, req: dict) -> Result:
    """Search records, garden seeds, and inbox filenames; empty query lists rows."""
    if req["type"] is not None and req["type"] not in VALID_RECORD_TYPES:
        raise WriteRefused(_unknown_record_type(req["type"]))
    if req.get("content"):
        if req.get("page"):
            raise WriteRefused(
                "--page pages metadata search; --content already paginates",
                site="note.search.page-content",
                prefixed=True,
                exit_code=2,
            )
        return _content_search(ctx, req)
    if req.get("page"):
        return _metadata_search_page(ctx, req)
    root = ctx.root
    try:
        offset, limit = _array_window(req)
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        matches, words, hits = _metadata_matches(root, req, snapshot)
        _snapshot(root, snapshot)
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site="note.search.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="note.search.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    notices = []
    if not matches and words:
        notices.append(f"los: {empty_search_hint('record', words, hits)}")
    shown = matches[offset:offset + limit]
    if len(matches) > offset + limit:
        notices.append(
            f"los: showing {len(shown)} of {len(matches)} matches; "
            f"continue with --offset {offset + limit}, or use --page for "
            "totals and a snapshot-bound continuation")
    return Result(
        shown,
        human_view=Presentation(notices=tuple(notices)),

    )
