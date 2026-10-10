"""Notes-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath

import jsonschema

from learning_os import observations
from learning_os.contracts.batch_notes import (
    ANALYSIS_FIELDS,
    ANALYSIS_FIELDS_ORDERED,
    ANALYSIS_HANDLER_OWNED,
    BATCH_FIELDS,
    BATCH_ITEM_FIELDS,
    BATCH_MAX_NOTES,
    BATCH_MIN_NOTES,
)
from learning_os.domain import ids
from learning_os.domain.failures import NotFound, StaleSnapshot, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.garden import garden_id
from learning_os.loader import EVIDENCE_SCHEMES, LoaderError, parse_frontmatter
from learning_os.loading import Repo, load_garden
from learning_os.material_analysis import (
    binding_consistent,
    normalize_binding_spellings,
    observe_local_material,
)
from learning_os.materials_resolution import (
    MATERIAL_RESOURCE_SUFFIXES,
    MATERIAL_SCHEME,
    material_uri_authority,
    resolve_material_target,
)
from learning_os.ops._legacy_plumbing import (
    _bytes_inside_owner,
    _content_envelope,
    _dump_yaml,
    _note_bytes,
    _note_collection,
    _read_content_bound_file,
    _read_structured_file,
    _snapshot,
    _window_values,
    prepare_review_envelope,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.pathing import PathBoundaryError
from learning_os.revisions import artifact_revision
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


def _read_batch_items(bundle: object) -> list[tuple[int, dict, dict, bytes]]:
    """Read and precheck every batch body before the snapshot guard.

    Each item carries its own content-bound body file, so the bytes hashed
    here are the approved bytes even if a file changes before the write.
    Returns (index, analysis, binding, body) per item, in request order.
    """
    if not isinstance(bundle, dict):
        raise WriteRefused("bundle must be an object")
    unknown = set(bundle) - BATCH_FIELDS
    if unknown:
        raise WriteRefused("bundle has unknown fields: "
                           + ", ".join(sorted(str(key) for key in unknown)))
    items = bundle.get("notes")
    if not isinstance(items, list) or len(items) < BATCH_MIN_NOTES:
        raise WriteRefused("bundle must carry a non-empty notes list")
    if len(items) > BATCH_MAX_NOTES:
        raise WriteRefused(f"batch carries {len(items)} notes; "
                           f"at most {BATCH_MAX_NOTES} per batch")
    prepared: list[tuple[int, dict, dict, bytes]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise WriteRefused(f"batch item {index} must be an object")
        unknown = set(item) - BATCH_ITEM_FIELDS
        if unknown:
            raise WriteRefused(f"batch item {index} has unknown fields: "
                               + ", ".join(sorted(str(key) for key in unknown)))
        if not isinstance(item.get("body_file"), str) or not item["body_file"]:
            raise WriteRefused(f"batch item {index} needs a body_file path")
        _, body = _read_content_bound_file(
            item["body_file"], item.get("body_file_sha256"),
            label=f"batch item {index} body file")
        try:
            binding = _precheck_analysis(item.get("analysis"), body)
        except WriteRefused as exc:
            raise WriteRefused(f"batch item {index}: {exc}") from exc
        note_id = item["analysis"]["id"]
        if note_id in seen:
            # Even two identical rows refuse: the transaction needs unique
            # artifact ids, and silently dropping one would lie about what
            # the batch carried.
            raise WriteRefused(
                f"batch carries note id {note_id} twice; refusing")
        seen.add(note_id)
        prepared.append((index, item["analysis"], binding, body))
    return prepared


def _dumps_analysis_save_batch(payload: dict) -> str:
    """The exact batch-save encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


@register("note.analysis.save_batch", kind="command")
def note_analysis_save_batch(ctx: OpContext, req: dict) -> Result:
    """Preserve up to 20 source analyses atomically under one receipt."""
    root = ctx.root
    prepared = _read_batch_items(req["bundle"])
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    writes: dict[Path, bytes] = {}
    created: list[str] = []
    replayed_ids: list[str] = []
    paths: dict[str, str] = {}
    for index, analysis, binding, body in prepared:
        try:
            note_id, path, content = _resolve_note(
                root, repo, analysis, binding, body)
        except WriteRefused as exc:
            raise WriteRefused(
                f"batch item {index} ({analysis['id']}): {exc}") from exc
        paths[note_id] = path.relative_to(root).as_posix()
        if content is None:
            replayed_ids.append(note_id)
        else:
            created.append(note_id)
            writes[path] = content
    if not writes:
        return Result(
            {"ok": True, "replayed": True, "created_note_ids": [],
             "replayed_note_ids": replayed_ids, "note_paths": paths},
            json_dumps=_dumps_analysis_save_batch,
        )
    # The envelope guards every batch id, but only new notes become
    # transaction artifacts: replayed notes keep their revision exactly
    # as a single-note replay does.
    try:
        revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    wanted = set(created)
    expected = {artifact: revision
                for artifact, revision
                in revisions.items()
                if artifact in wanted}

    def finish_analysis_save_batch(confirmation):
        return {**confirmation, "ok": True, "replayed": False,
                "created_note_ids": created,
                "replayed_note_ids": replayed_ids, "note_paths": paths}

    return Result(
        {"ok": True, "replayed": False, "created_note_ids": created,
         "replayed_note_ids": replayed_ids, "note_paths": paths},
        proposal=TransactionProposal(
            capability="note.analysis.save_batch",
            writes=writes,
            artifact_ids=created,
            expected_revisions=expected,
        ),
        finish=finish_analysis_save_batch,
        after_commit="STANDARD",
        json_dumps=_dumps_analysis_save_batch,
    )


def _analysis_safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"analysis save cannot use a symlink: {relative}")
    return path


def _analysis_schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


def _analysis_render_exact_note(meta: dict, body: bytes) -> bytes:
    """Frontmatter plus the body bytes verbatim.

    Unlike the ordinary renderer this never strips leading whitespace: the
    bytes after the frontmatter block are exactly the preserved analysis.
    """
    front = "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n"
    return front.encode("utf-8") + body


def _analysis_destination(root: Path, note_id: str, relpath: object) -> Path:
    if not isinstance(relpath, str) or not relpath:
        raise WriteRefused("analysis path must be a repo-relative note path")
    relative = Path(relpath)
    if relative.is_absolute() or ".." in relative.parts:
        raise WriteRefused("analysis path must stay inside knowledge/notes/")
    if relative.suffix != ".md" or relative.stem != note_id:
        raise WriteRefused("analysis filename must be the note id with .md")
    try:
        relative.relative_to(NOTES_PREFIX)
    except ValueError:
        raise WriteRefused("analysis path must stay inside knowledge/notes/") from None
    path = root / relative
    return _analysis_safe(root, path)


def _normalize_binding_material_uri(repo, binding: dict) -> dict:
    """Resolve a ``material://`` binding to its materials-relative path.

    The URI authority must equal the binding's ``source_id``: naming a
    registered source's file while withholding (or mismatching) the source
    claim is incoherent. Resolution prefers the id-alias tree
    (``materials/.flat``), which maps the authority to the physical folder;
    without it the REL resolves under the source's registered material
    folder. An unresolvable URI still normalizes lexically, so the
    observability check below can diagnose it honestly.
    """
    material = binding.get("material")
    if not isinstance(material, str) or not material.startswith(MATERIAL_SCHEME):
        return binding
    source_id = binding.get("source_id")
    authority = material_uri_authority(material)
    if authority is None:
        raise WriteRefused(
            f"binding.material is not a safe material:// URI: {material!r} "
            "(expected material://SOURCE_ID/REL)")
    if source_id is None:
        raise WriteRefused(
            "binding.material is a material:// URI but the binding names no "
            f"source_id; use the materials-relative path instead, or resolve "
            f"against {authority!r}")
    if authority != source_id:
        raise WriteRefused(
            f"binding.material authority {authority!r} must equal "
            f"binding.source_id {source_id!r}")
    parts = PurePosixPath(material[len(MATERIAL_SCHEME):]).parts
    if len(parts) < 2:
        raise WriteRefused(
            f"binding.material names no file: {material!r} "
            "(expected material://SOURCE_ID/REL)")
    # Canonical recognition is separate from the legacy safety diagnostics.
    if ids.is_valid("material-uri", material):
        material = ids.parse("material-uri", material)
        parts = PurePosixPath(material[len(MATERIAL_SCHEME):]).parts
    rel = "/".join(parts[1:])
    materials_dir = repo.learningos_root / "materials"
    try:
        target = resolve_material_target(
            material, resolution_root=repo.materials_root,
            boundary_root=materials_dir)
    except (PathBoundaryError, FileNotFoundError, OSError):
        target = None
    if target is not None:
        relative = target.resolve().relative_to(materials_dir.resolve())
        return {**binding, "material": relative.as_posix()}
    registered = (repo.sources.get(source_id) or {}).get("material")
    if material_uri_authority(registered) is None:
        raise WriteRefused(
            f"source {source_id!r} registers no local material; cannot resolve "
            f"binding.material {material!r}")
    folder = str(registered)[len(MATERIAL_SCHEME):].rstrip("/")
    if PurePosixPath(folder).suffix.lower() in MATERIAL_RESOURCE_SUFFIXES:
        folder = PurePosixPath(folder).parent.as_posix()
    candidate = f"{folder}/{rel}" if folder not in ("", ".") else rel
    return {**binding, "material": candidate}


def _verify_resolved_material(root: Path, repo, binding: dict) -> None:
    """A resolved binding claims live registered bytes: observe them.

    Digest agreement proves the agent's story is coherent; this proves it
    is true. The material must exist and hash to the claimed live digest
    right now, and it must be the source's registered file or lie under
    the source's registered directory — compared as resolved filesystem
    locations so `.flat` id-aliases match their physical targets.

    Each unobservable state names itself: `stale` only when the observed
    bytes genuinely differ, a missing file as not resolving, an escaping
    path as not materials-relative.
    """
    materials = root.parent / "materials"
    observation = observe_local_material(
        materials, str(binding.get("material") or ""),
        str(binding.get("live_source_digest") or ""))
    if observation["status"] == "stale":
        raise WriteRefused(
            "resolved material is not observable at its claimed live "
            "digest (stale)")
    if observation["status"] == "missing":
        raise WriteRefused(
            f"resolved material does not resolve: {binding.get('material')!r} "
            "names no readable file under materials/ (expected a "
            "materials-relative path like 'course/deck.pdf', a "
            "material://SOURCE_ID/REL URI, or a leading materials/ path)")
    if observation["status"] != "current":
        raise WriteRefused(
            "resolved material is not a materials-relative path: "
            f"{binding.get('material')!r} (expected a path under materials/ "
            "without a leading '/' or '..')")
    registered = (repo.sources.get(binding.get("source_id")) or {}).get("material")
    if material_uri_authority(registered) is None:
        raise WriteRefused("resolved source registers no local material")
    try:
        boundary = materials.resolve()
        base = (repo.materials_root / str(registered)[len(MATERIAL_SCHEME):]).resolve()
        target = (materials / str(binding.get("material"))).resolve()
        base.relative_to(boundary)
        target.relative_to(boundary)
    except (OSError, ValueError):
        raise WriteRefused(
            "resolved material escapes the materials tree") from None
    if target != base and base not in target.parents:
        raise WriteRefused(
            "resolved material is not the source's registered file or "
            "under its registered directory")


def _precheck_analysis(analysis: object, body: bytes) -> dict:
    """Record shape, binding coherence, and frozen-byte agreement.

    Shared by single and batch saves so both refuse the same bytes for the
    same reason. Everything needing the loaded repository — source
    registration, live-byte observation, replay classification — stays in
    `_resolve_note`, inside the snapshot guard.
    """
    if not isinstance(analysis, dict):
        raise WriteRefused("analysis must be an object")
    unknown = set(analysis) - ANALYSIS_FIELDS
    if unknown:
        raise WriteRefused(
            "analysis has unknown fields: " + ", ".join(sorted(unknown))
            + f" (accepted: {', '.join(ANALYSIS_FIELDS_ORDERED)}; "
            + f"{'/'.join(ANALYSIS_HANDLER_OWNED)} are set by the handler)")
    if not isinstance(analysis.get("id"), str):
        raise WriteRefused("analysis needs a string id")
    if not body:
        raise WriteRefused("analysis body is empty")
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        raise WriteRefused("analysis body is not valid UTF-8") from None
    binding = analysis.get("binding")
    if isinstance(binding, dict):
        # The read surface's own spellings normalize before any check, so a
        # sha256:-prefixed digest compares equal to its bare twin below.
        spelling = normalize_binding_spellings(binding)
        if spelling is not None:
            raise WriteRefused(spelling)
    problem = binding_consistent(binding if isinstance(binding, dict) else {})
    if problem is not None:
        raise WriteRefused(problem)
    missing = [field for field in ("frozen_input_sha256", "frozen_input_bytes")
               if field not in binding]
    if missing:
        # A typed refusal, not a KeyError surfacing as INTERNAL_FAILURE (which
        # operations must then treat as an ambiguous, possibly-committed write).
        raise WriteRefused(
            f"analysis binding lacks {', '.join(missing)}; note-analysis-prepare "
            "derives both from the body bytes (one note is a batch of one)")
    frozen = hashlib.sha256(body).hexdigest()
    if binding["frozen_input_sha256"] != frozen:
        raise WriteRefused("analysis body does not match frozen_input_sha256")
    if binding["frozen_input_bytes"] != len(body):
        raise WriteRefused("analysis body does not match frozen_input_bytes")
    return binding


def _resolve_note(root: Path, repo, analysis: dict, binding: dict,
                  body: bytes) -> tuple[str, Path, bytes | None]:
    """Classify one prechecked analysis against the loaded repository.

    Returns (note_id, destination, rendered_bytes); rendered_bytes is None
    when the request replays an identical note. Any collision, unregistered
    source, or unobservable resolved material refuses. Callers commit every
    returned write in one transaction.

    A material:// URI resolves here — this is the first point with the
    loaded repository — before any check that could misdiagnose it. The
    normalized binding replaces the request's, so the envelope, the intent
    hash, and the stored frontmatter all carry the canonical form.
    """
    binding = _normalize_binding_material_uri(repo, binding)
    analysis["binding"] = binding
    note_id = analysis["id"]
    if binding["resolution"] == "resolved":
        if binding.get("source_id") not in repo.sources:
            raise WriteRefused("resolved source is not registered")
        _verify_resolved_material(root, repo, binding)
    existing = repo.notes.get(note_id)
    path = _analysis_destination(root, note_id, analysis.get("path"))
    if existing:
        if "material_analysis" not in existing.meta:
            raise WriteRefused("this note id is not a source analysis")
        # The loader strips leading body whitespace on read, so replay
        # compares exact on-disk bytes: the body is the file's last N
        # bytes where N is the stored frozen_input_bytes.
        stored = existing.meta["material_analysis"].get("frozen_input_bytes")
        try:
            stored_body = existing.path.read_bytes()[-stored:] \
                if isinstance(stored, int) else None
        except OSError:
            stored_body = None
        same = (
            existing.meta.get("title") == analysis.get("title")
            and existing.meta.get("material_analysis") == binding
            and stored_body == body
            and existing.path == path
        )
        if not same:
            raise WriteRefused(
                "note id collides with a different analysis; refusing")
        return note_id, path, None
    if not isinstance(analysis.get("title"), str) or not analysis["title"].strip():
        raise WriteRefused("new analyses require a title")
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": analysis["title"], "created": observations.today().isoformat(),
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": copy.deepcopy(binding)}
    # Validate id before it can be used as a filename.
    _analysis_schema(root, "note", meta)
    if path.exists():
        raise WriteRefused("analysis destination already exists")
    return note_id, path, _analysis_render_exact_note(meta, body)


DRAFTS_FIELDS = frozenset({"notes"})
DRAFT_ITEM_FIELDS = frozenset({"id", "title", "path", "binding", "body"})
DRAFT_FROZEN_REFUSED = ("frozen_input_sha256", "frozen_input_bytes")


def _read_drafts_file(value: object) -> dict:
    """Read the UTF-8 JSON drafts file, or stdin JSON when given `-`.

    JSON is the only accepted format: bodies are JSON strings, so what the
    author writes is codepoint-exactly what prep stages — no folding style
    can silently mangle whitespace the way a YAML block choice could.
    """
    if value == "-":
        return _read_structured_file("-", label="batch drafts")
    if not isinstance(value, str) or not value:
        raise WriteRefused("drafts must be a UTF-8 JSON file (.json)")
    if Path(value).suffix.lower() != ".json":
        raise WriteRefused("drafts must be a UTF-8 JSON file (.json)")
    return _read_structured_file(value, label="batch drafts")


def _read_draft_items(drafts: object) -> list[tuple[dict, dict, bytes]]:
    """Validate drafts and derive every hash. No repository state needed.

    Returns (analysis, binding, body_bytes) per item, in draft order.
    Drafts carry no derived hashes: a precomputed frozen value refuses
    rather than being silently recomputed, since a stale one signals
    confusion about which bytes were approved.
    """
    if not isinstance(drafts, dict):
        raise WriteRefused("drafts must be an object")
    unknown = set(drafts) - DRAFTS_FIELDS
    if unknown:
        raise WriteRefused("drafts has unknown fields: "
                           + ", ".join(sorted(str(key) for key in unknown)))
    notes = drafts.get("notes")
    if not isinstance(notes, list) or len(notes) < BATCH_MIN_NOTES:
        raise WriteRefused("drafts must carry a non-empty notes list")
    if len(notes) > BATCH_MAX_NOTES:
        raise WriteRefused(f"drafts carry {len(notes)} notes; "
                           f"at most {BATCH_MAX_NOTES} per batch")
    prepared: list[tuple[dict, dict, bytes]] = []
    seen: set[str] = set()
    for index, item in enumerate(notes):
        if not isinstance(item, dict):
            raise WriteRefused(f"draft {index} must be an object")
        unknown = set(item) - DRAFT_ITEM_FIELDS
        if unknown:
            raise WriteRefused(f"draft {index} has unknown fields: "
                               + ", ".join(sorted(str(key) for key in unknown)))
        for field in ("id", "title", "path"):
            if not isinstance(item.get(field), str) or not item[field]:
                raise WriteRefused(f"draft {index} needs a non-empty {field}")
        binding = item.get("binding")
        if not isinstance(binding, dict):
            raise WriteRefused(f"draft {index} needs a binding object")
        for derived in DRAFT_FROZEN_REFUSED:
            if derived in binding:
                raise WriteRefused(
                    f"draft {index} must not precompute {derived}; "
                    f"prep derives it from the body")
        body = item.get("body")
        if not isinstance(body, str) or not body:
            raise WriteRefused(f"draft {index} needs a non-empty body string")
        body_bytes = body.encode("utf-8")
        completed = dict(binding)
        completed["frozen_input_sha256"] = hashlib.sha256(body_bytes).hexdigest()
        completed["frozen_input_bytes"] = len(body_bytes)
        analysis = {"id": item["id"], "title": item["title"],
                    "path": item["path"], "binding": completed}
        try:
            checked = _precheck_analysis(analysis, body_bytes)
        except WriteRefused as exc:
            raise WriteRefused(f"draft {index}: {exc}") from exc
        if item["id"] in seen:
            raise WriteRefused(
                f"drafts carry note id {item['id']} twice; refusing")
        seen.add(item["id"])
        prepared.append((analysis, checked, body_bytes))
    return prepared


def _prepare_out_dir(root: Path, value: object) -> Path:
    """Resolve the staging dir, which must stay outside the repository.

    Prep writes no canonical data, so staging lives out-of-tree by
    contract, like every other draft. ``bodies/`` is prep-owned and
    rebuilt every run, so a re-prep with fewer notes leaves no stale
    body files behind.
    """
    if not isinstance(value, str) or not value or value == "-":
        raise WriteRefused(
            "--out must be a staging directory outside the repository")
    out = Path(value).expanduser()
    if not out.is_absolute():
        out = Path.cwd() / out
    try:
        resolved = out.resolve()
    except OSError as exc:
        raise WriteRefused(f"cannot use staging dir {value}: {exc}") from exc
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        pass
    else:
        raise WriteRefused("staging dir must stay outside the repository")
    bodies = resolved / "bodies"
    try:
        if bodies.exists():
            if not bodies.is_dir() or bodies.is_symlink():
                raise WriteRefused(
                    f"staging bodies path is not a directory: {bodies}")
            shutil.rmtree(bodies)
        bodies.mkdir(parents=True)
    except OSError as exc:
        raise WriteRefused(f"cannot stage into {resolved}: {exc}") from exc
    return resolved


def _dumps_analysis_prepare(payload: dict) -> str:
    """The exact prepare encoder: indented, unescaped."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


@register("cli.note-analysis-prepare", kind="tool")
def note_analysis_prepare(ctx: OpContext, req: dict) -> Result:
    """Drafts in, reviewable staging plus the exact envelope out.

    Read-only against the repository: no operator lock, no canonical
    writes, no publication. Every check runs before a single staged byte,
    so a refused prep stages no body files and no envelope.
    Review the staged files, then submit the envelope unchanged through
    ``note.analysis.save_batch``; the content hashes and intent binding
    refuse anything altered after review.
    """
    root = ctx.root
    prepared = _read_draft_items(_read_drafts_file(req["drafts"]))
    out = _prepare_out_dir(root, req["out"])
    repo = ctx.repo()
    snapshot = ctx.snapshot_id()
    staged: list[tuple[str, str, bytes, dict, bool]] = []
    for index, (analysis, binding, body_bytes) in enumerate(prepared):
        try:
            note_id, path, content = _resolve_note(
                root, repo, analysis, binding, body_bytes)
        except WriteRefused as exc:
            raise WriteRefused(
                f"draft {index} ({analysis['id']}): {exc}") from exc
        staged.append((note_id, path.relative_to(root).as_posix(),
                       body_bytes, analysis, content is not None))
    bundle_notes = []
    report = []
    try:
        for note_id, relpath, body_bytes, analysis, predicted_new in staged:
            body_path = out / "bodies" / f"{note_id}.bin"
            body_path.write_bytes(body_bytes)
            digest = hashlib.sha256(body_bytes).hexdigest()
            bundle_notes.append({
                "analysis": analysis,
                "body_file": str(body_path),
                "body_file_sha256": f"sha256:{digest}",
            })
            report.append({
                "note_id": note_id,
                "note_path": relpath,
                "predicted_new": predicted_new,
                "frozen_input_sha256": digest,
                "body_file": str(body_path),
            })
        revisions = {note_id: artifact_revision(root, note_id)
                     for note_id, _, _, _, _ in staged}
        envelope = prepare_review_envelope(
            "note.analysis.save_batch", {"bundle": {"notes": bundle_notes}},
            snapshot, revisions)
        envelope_path = out / "envelope.json"
        envelope_path.write_text(
            json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"cannot write staging dir {out}: {exc}") from exc
    submit = (f".venv/bin/python tools/los.py capability note.analysis.save_batch "
              f"--payload-file {envelope_path}")
    return Result(
        {"ok": True, "out_dir": str(out),
         "envelope": str(envelope_path),
         "expected_snapshot": snapshot,
         "expected_revisions": revisions,
         "notes": report, "submit": submit},
        json_dumps=_dumps_analysis_prepare,
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
