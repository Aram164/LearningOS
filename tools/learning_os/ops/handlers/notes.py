"""Notes-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from learning_os import observations
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.garden import garden_id
from learning_os.loader import EVIDENCE_SCHEMES, LoaderError, parse_frontmatter
from learning_os.loading import Repo, load_garden
from learning_os.ops._legacy_plumbing import (
    _bytes_inside_owner,
    _content_envelope,
    _dump_yaml,
    _note_bytes,
    _note_collection,
    _precheck_analysis,
    _read_content_bound_file,
    _resolve_note,
    _snapshot,
    _window_values,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions


def _dumps_evidence(payload: dict) -> str:
    """The exact evidence encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


def _on_commit_refused_evidence(errors: list) -> list[str]:
    """The exact commit-refusal lines: the header plus the engine issues, verbatim."""
    return ["los: evidence rejected by validation", *errors[:12]]


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
            gateway_message=f"los: cannot read note frontmatter: {exc}",
            exit_code=2,
        ) from exc
    existing = list(meta.get("evidence") or [])
    entry = {"type": req["evidence_type"], "ref": req["ref"]}
    if any(e.get("type") == entry["type"] and e.get("ref") == entry["ref"]
           for e in existing):
        raise WriteRefused(
            "that evidence is already recorded on this note",
            site=f"{ctx.operation}.already-recorded",
            gateway_message="los: that evidence is already recorded on this note",
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
        on_commit_refused=_on_commit_refused_evidence,
        json_dumps=_dumps_evidence,
    )


def _dumps_revise(payload: dict) -> str:
    """The exact revise encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


def _on_commit_refused_revise(errors: list) -> list[str]:
    """The exact commit-refusal lines: the header plus the engine issues, verbatim."""
    return ["los: note revision rejected by validation", *errors[:12]]


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
            gateway_message=(
                "los: note revision requires --approve after reviewing "
                "the full replacement"
            ),
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
            gateway_message=f"los: cannot read revised note: {exc}",
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
            gateway_message=f"los: invalid revised note: {exc}",
            exit_code=2,
        ) from exc
    if meta.get("id") != req["note_id"] or meta.get("type") != "note":
        raise WriteRefused(
            "revised note must preserve the requested note id and type",
            site=f"{ctx.operation}.id-mismatch",
            gateway_message=(
                "los: revised note must preserve the requested note id and type"
            ),
            exit_code=2,
        )
    if meta.get("role") != note.meta.get("role"):
        raise WriteRefused(
            "note-revise cannot change a note role",
            site=f"{ctx.operation}.role-change",
            gateway_message="los: note-revise cannot change a note role",
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
        on_commit_refused=_on_commit_refused_revise,
        json_dumps=_dumps_revise,
    )


NOTES_PREFIX = Path("knowledge/notes")

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


def _dumps_create(payload: dict) -> str:
    """The exact create encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


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
        after_commit="STANDARD",
        json_dumps=_dumps_create,
    )


def _dumps_analysis_save(payload: dict) -> str:
    """The exact analysis-save encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


@register("note.analysis.save", kind="command")
def note_analysis_save(ctx: OpContext, req: dict) -> Result:
    """Preserve one source analysis as a durable reference note."""
    root = ctx.root
    _, body = _read_content_bound_file(
        req["body_file"], req.get("body_file_sha256"),
        label="analysis body file")
    binding = _precheck_analysis(req["analysis"], body)
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    note_id, path, content = _resolve_note(
        root, repo, req["analysis"], binding, body)
    if content is None:
        return Result(
            {"ok": True, "replayed": True, "note_id": note_id,
             "note_path": path.relative_to(root).as_posix()},
            json_dumps=_dumps_analysis_save,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return Result(
        {"ok": True, "replayed": False, "note_id": note_id,
         "note_path": path.relative_to(root).as_posix()},
        proposal=TransactionProposal(
            capability="note.analysis.save",
            writes={path: content},
            artifact_ids=[note_id],
            expected_revisions=expected_revisions,
        ),
        after_commit="STANDARD",
        json_dumps=_dumps_analysis_save,
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


def _dumps_read(payload: dict) -> str:
    """The exact note-read JSON encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


@register("cli.note-read", kind="query")
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
                    site="cli.note-read.unknown-note",
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
                json_dumps=_dumps_read,
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
            json_dumps=_dumps_read,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site="cli.note-read.stale-snapshot",
            gateway_message=f"los: {exc}",
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="cli.note-read.read-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    except UnicodeError as exc:
        raise WriteRefused(
            str(exc),
            site="cli.note-read.bad-encoding",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
