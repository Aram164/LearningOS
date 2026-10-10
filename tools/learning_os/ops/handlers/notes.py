"""Notes-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.loader import EVIDENCE_SCHEMES, LoaderError, parse_frontmatter
from learning_os.ops._legacy_plumbing import (
    _dump_yaml,
    _read_content_bound_file,
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
