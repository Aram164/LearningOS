"""Capture-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

from learning_os.app.context import OpContext
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.handlers._shared import content_envelope as _content_envelope
from learning_os.app.handlers._shared import discovery_row as _discovery_row
from learning_os.app.handlers._shared import inbox_search_rows as _inbox_search_rows
from learning_os.app.handlers._shared import require_unit_map_or_error
from learning_os.app.handlers._shared import window_values as _window_values
from learning_os.app.proposal import InboxCompletion, Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.domain.unit_notes import unit_note_sections
from learning_os.store import observations
from learning_os.store.codec import dump_study_map as _dump_study_map
from learning_os.store.contracts.gateway import (
    current_gateway_request,
    request_artifact_id,
)
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.fs import bytes_inside_owner as _bytes_inside_owner
from learning_os.store.transactions import parse_expected_revisions


def _human_capture(payload: dict) -> str:
    """The exact default-branch prose: the capture line plus the routing note."""
    return (
        f"captured -> {payload['captured']}\n"
        "routing is the operator's job (WORKFLOWS §21); the inbox trends "
        "toward empty"
    )




def _human_garden_seed(payload: dict) -> str:
    """The exact default-branch prose: the created line plus the no-AI note."""
    return (
        f"Garden seed created -> {payload['seed_path']}\n"
        "No classification, routing, harvesting, or AI action was performed."
    )


def _seed_slug(text: str, title: str | None) -> str:
    """Mechanical filename slug; never a semantic classification."""
    source = str(title or "").strip()

    if not source:
        source = next(
            (
                line.strip().lstrip("#").strip()
                for line in text.splitlines()
                if line.strip()
            ),
            "",
        )

    return (
        re.sub(r"[^a-z0-9]+", "-", source.lower())
        .strip("-")[:64]
        or "garden-seed"
    )


def _seed_content(text: str, title: str | None) -> str:
    """Preserve caller text, optionally placing the explicit title above it."""
    body = str(text)

    if title:
        content = f"# {title}\n\n{body}"
    else:
        content = body

    return content if content.endswith("\n") else content + "\n"


@register("capture.create", kind="command", human=_human_capture, effects=OperationEffects.CANONICAL_WRITE)
def capture(ctx: OpContext, req: dict) -> Result:
    """Judgment-free capture into work/inbox/ with a transaction receipt."""
    root = ctx.root
    inbox = root / "work" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")

    if req.get("file"):
        try:
            src, content = _read_content_bound_file(
                req["file"],
                req.get("file_sha256"),
                label="capture file",
            )
        except WriteRefused as exc:
            # Re-raise the caught failure itself: its typed fields are the
            # refusal, and the old wrapper's complaint and return ride along
            # as transcribed metadata (amendment (ac)).
            exc.site = f"{ctx.operation}.bad-file"
            exc.gateway_message = f"los: {exc}"
            exc.exit_code = 2
            raise
        target = inbox / src.name
        if target.exists():
            target = inbox / f"{stamp}-{src.name}"
            # The transaction engine overwrites an existing path, so one
            # fallback name is not enough: loop for a free name with a
            # serial, as the text branch does, so a same-second capture of
            # an already-stamped basename can never replace an earlier
            # capture's bytes.
            serial = 2
            while target.exists():
                target = inbox / f"{stamp}-{src.stem}-{serial}{src.suffix}"
                serial += 1
    else:
        capture_text = req.get("text") if req.get("text") is not None else sys.stdin.read()
        if not capture_text.strip():
            raise WriteRefused(
                "nothing to capture (empty input)",
                site=f"{ctx.operation}.empty-input",
                prefixed=True,
                exit_code=2,
            )
        slug = re.sub(r"[^a-z0-9]+", "-",
                      (req.get("title") or capture_text).lower()).strip("-")[:40] or "capture"
        target = inbox / f"{stamp}-{slug}.md"
        serial = 2
        while target.exists():
            target = inbox / f"{stamp}-{slug}-{serial}.md"
            serial += 1
        content = (f"# {req.get('title')}\n\n{capture_text}\n" if req.get("title")
                   else capture_text.rstrip() + "\n")

    relative = target.relative_to(root).as_posix()
    gateway_request = current_gateway_request()
    artifact_id = (
        request_artifact_id("capture.create", gateway_request.idempotency_key)
        if gateway_request is not None
        else f"capture:{relative}"
    )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "captured": relative},
        proposal=TransactionProposal(
            capability="capture.create",
            writes={target: content},
            artifact_ids=[artifact_id],
            expected_revisions=expected_revisions,
        ),


    )


@register("garden.seed.create", kind="command", human=_human_garden_seed, effects=OperationEffects.CANONICAL_WRITE)
def garden_seed_create(ctx: OpContext, req: dict) -> Result:
    """Create one free-form Markdown seed under knowledge/garden/."""
    root = ctx.root
    text = str(req["text"] or "")

    if not text.strip():
        raise WriteRefused(
            "Garden seed text is empty; nothing was written",
            site=f"{ctx.operation}.empty-text",
            prefixed=True,
            exit_code=2,
        )

    title = str(req.get("title") or "").strip() or None

    ctx.require_snapshot(req.get("expected_snapshot"))

    garden = root / "knowledge" / "garden"
    slug = _seed_slug(text, title)

    # The garden reader skips the readme stem as meta, so a seed named
    # readme.md would be created and receipted yet invisible to every read
    # surface (note.content, search, the Nebula). The writer never produces
    # a stem the reader skips: suffix it, as the collision loop does.
    serial = 2
    if slug.lower() == "readme":
        slug = f"{slug}-{serial}"
        serial += 1

    target = garden / f"{slug}.md"

    while target.exists():
        target = garden / f"{slug}-{serial}.md"
        serial += 1

    relative = target.relative_to(root).as_posix()
    content = _seed_content(text, title)
    gateway_request = current_gateway_request()
    artifact_id = (
        request_artifact_id(
            "garden.seed.create", gateway_request.idempotency_key
        )
        if gateway_request is not None
        else f"garden:{relative}"
    )

    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "seed_path": relative},
        proposal=TransactionProposal(
            capability="garden.seed.create",
            writes={target: content},
            artifact_ids=[artifact_id],
            expected_revisions=expected_revisions,
        ),


    )


@register("inbox.list", kind="tool", effects=OperationEffects.READ)
def inbox_list(ctx: OpContext, req: dict) -> Result:
    """List work/inbox files by name, without reading bytes."""
    root = ctx.root
    try:
        rows = _inbox_search_rows(root)
    except OSError as exc:
        raise WriteRefused(
            f"cannot list work/inbox: {exc}",
            site=f"{ctx.operation}.list-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    now = observations.epoch()
    inbox = root / "work" / "inbox"
    out = []
    for rec in rows:
        row = _discovery_row(rec)
        try:
            row["age_days"] = int((now - observations.mtime(inbox / rec["id"], root)) / 86400)
        except OSError:
            row["age_days"] = None
        out.append(row)
    return Result(out)


def _inbox_folder_envelope(root: Path, name: str) -> dict:
    """A folder drop's file names and the digest inbox-resolve checks.

    Uses the resolve path's own admission, collection and digest, so the
    value a reader is handed is exactly the value the write recomputes.
    """
    inbox = root / "work" / "inbox"
    try:
        files = _collect(inbox, _admit(inbox, name))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return {
        "contract": "inbox-folder", "item": name,
        "path": (inbox / name).relative_to(root).as_posix(),
        "files": sorted(files),
        "drop_sha256": _folder_digest(files),
    }


@register("inbox.content", kind="query", effects=OperationEffects.READ)
def inbox_read(ctx: OpContext, req: dict) -> Result:
    """Read a bounded segment of one work/inbox file by inbox-relative name.

    Inbox drops are addressed by name — they have no registry and no stable
    ids — and may be binary, so non-UTF-8 bytes refuse rather than decode.
    Discovery lists non-dot files (the same rule as the inbox count); an
    exact name reads whatever it addresses, dot-files included. A folder
    drop answers its file names plus ``drop_sha256``, the digest
    ``inbox-resolve`` seals for the whole folder; no other read exposes it.
    """
    root = ctx.root
    try:
        offset, limit = _window_values(
            req["offset"], req["limit"], req.get("expected_snapshot"), 16000)
        name = req["name"]
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise WriteRefused(
                f"inbox name must be relative to work/inbox: {name}",
                site=f"{ctx.operation}.bad-name",
                prefixed=True,
                exit_code=2,
            )
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        target = root / "work" / "inbox" / name
        if target.is_dir() and not target.is_symlink():
            payload = _inbox_folder_envelope(root, name)
            _snapshot(root, snapshot)
            return Result(
                {"schema_version": 1, "snapshot_id": snapshot, **payload},

            )
        if not target.is_symlink() and not target.is_file():
            raise WriteRefused(
                f"inbox item not found: {name}",
                site=f"{ctx.operation}.unknown-item",
                prefixed=True,
                exit_code=2,
            )
        raw = _bytes_inside_owner(
            root, target, root / "work" / "inbox",
            escape=f"inbox item escapes work/inbox: {name}",
            symlink="inbox read refuses symlinks")
        try:
            content = raw.decode("utf-8")
        except UnicodeError as exc:
            raise WriteRefused(
                f"inbox item is not UTF-8 text and has no text read: {name}",
                site=f"{ctx.operation}.not-utf8",
                prefixed=True,
                exit_code=2,
            ) from exc
        payload = _content_envelope(
            "inbox-content", "item", name,
            target.relative_to(root).as_posix(),
            raw, content, offset, limit)
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},

        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            prefixed=True,
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


def _unit_note_packet_sections(root: Path, unit) -> list[dict]:
    """The learner's saved session reasoning, in the order it was recorded.

    `unit-note` owns session reasoning at the unit's working note; shelving used
    to traverse only stage-owned notes, so a saved section stayed safely stored
    and never reached the review packet it was written for (2026-09-05 audit,
    F06). Both models are read here; neither rewrites the learner's wording.
    """
    if unit is None:
        return []
    declared = str(unit.data.get("working_note") or "").strip()
    note = root / declared if declared else unit.path.parent / "notes.md"
    try:
        resolved = note.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return []
    if not resolved.is_file():
        return []
    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return unit_note_sections(text)


def _packet_note_lines(sections: list[dict], stage_titles: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for section in sections:
        stage_ids = [sid for sid in section.get("stage_ids") or [] if sid]
        context = ", ".join(
            f"{stage_titles.get(sid, sid)} (`{sid}`)" for sid in stage_ids
        ) or "no stage named"
        lines.extend([
            f"### {section.get('title') or 'Learning session note'}", "",
            f"*Session note recorded {section.get('recorded_at') or 'at an unrecorded time'}"
            f" — stage context: {context}.*", "",
            section.get("text") or "*(Empty section.)*", "",
        ])
        attachments = section.get("attachments") or []
        if attachments:
            lines.extend([
                "Attachments: " + ", ".join(
                    str(item.get("path")) for item in attachments
                    if isinstance(item, dict) and item.get("path")
                ),
                "",
            ])
    return lines


@register("review.prepare", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def shelving_prepare(ctx: OpContext, req: dict) -> Result:
    """Prepare a review packet; never applies canonical changes."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    items = []
    if req.get("items_file"):
        try:
            _source, item_bytes = _read_content_bound_file(
                req["items_file"],
                req.get("items_file_sha256"),
                label="shelving items file",
            )
            raw = json.loads(item_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, WriteRefused) as exc:
            raise WriteRefused(
                f"cannot read shelving items: {exc}",
                site=f"{ctx.operation}.bad-items-file",
                prefixed=True,
                exit_code=2,
            ) from exc
        items = raw.get("items", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            raise WriteRefused(
                "shelving items file must contain a JSON list",
                site=f"{ctx.operation}.items-not-list",
                prefixed=True,
                exit_code=2,
            )
    proposal_path = study_map.path.parent / "shelving-proposal.md"
    stage_titles = {
        str(stage.get("id")): str(stage.get("title") or stage.get("id"))
        for stage in data.get("stages", []) or []
        if isinstance(stage, dict) and stage.get("id")
    }
    sections = _unit_note_packet_sections(root, unit)
    lines = ["# Shelving proposal review packet", "",
             "> Operational proposal only. No canonical change is applied until selected IDs are explicitly approved.", ""]
    lines.extend(["## Session notes", ""])
    if sections:
        lines.extend(_packet_note_lines(sections, stage_titles))
    else:
        lines.extend(["*(No session note saved for this unit yet.)*", ""])
    seen_stage_notes: set[str] = set()
    for stage in data.get("stages", []) or []:
        note_ref = str(stage.get("working_note", ""))
        note = root / note_ref if note_ref else None
        stage_text = (
            note.read_text(encoding="utf-8", errors="replace")
            if note is not None and note.is_file() else ""
        ).strip()
        attachments = stage.get("attachments") or []
        # A stage with neither recorded text nor attachments would add an
        # empty heading between the sections that do carry reasoning.
        if not stage_text and not attachments:
            continue
        if note_ref and note_ref in seen_stage_notes:
            continue
        if note_ref:
            seen_stage_notes.add(note_ref)
        lines.extend([f"## {stage.get('title', stage.get('id'))}", "",
                      f"*Stage note `{note_ref}`.*" if note_ref else "*Stage note.*",
                      ""])
        lines.append(stage_text or "*(No stage note text; attachments only.)*")
        lines.append("")
        if attachments:
            lines.append("Attachments: " + ", ".join(a["path"] for a in attachments))
            lines.append("")
    shelving = data.setdefault("shelving", {})
    shelving.update({"state": "proposed" if items else "draft",
                      "proposal_path": proposal_path.relative_to(root).as_posix(),
                      "summary": req.get("summary") or "Review stage notes and attachments without rewriting learner wording."})
    if items:
        shelving["items"] = items
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "proposal_path": shelving["proposal_path"],
         "state": shelving["state"]},
        proposal=TransactionProposal(
            capability="review.prepare",
            writes={
                proposal_path: "\n".join(lines).rstrip() + "\n",
                study_map.path: _dump_study_map(study_map, data),
            },
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )




def _approved_destination(root: Path, item: dict) -> Path | None:
    rel = str(item.get("destination", ""))
    target = (root / rel).resolve()
    allowed = (root / "knowledge" / "notes").resolve(), (root / "knowledge" / "garden").resolve()
    if not any(parent == target or parent in target.parents for parent in allowed):
        return None
    return target


@register("review.apply", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def shelving_apply(ctx: OpContext, req: dict) -> Result:
    """Apply only explicitly approved proposal IDs."""
    if not req.get("approve"):
        raise WriteRefused(
            "shelving apply requires --approve and explicit selected proposal IDs",
            site=f"{ctx.operation}.needs-approve",
            prefixed=True,
            exit_code=2,
        )
    root = ctx.root
    selected = set(req["selected"])
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    shelving = data.get("shelving") or {}
    packet_items = shelving.get("items", []) or []
    items = [item for item in packet_items if item.get("id") in selected]
    if not items or {item.get("id") for item in items} != selected:
        raise WriteRefused(
            "every selected ID must exist in the current proposal",
            site=f"{ctx.operation}.unknown-selected",
            prefixed=True,
            exit_code=2,
        )
    writes: dict[Path, str] = {}
    for item in items:
        target = _approved_destination(root, item)
        if target is None or target.exists():
            raise WriteRefused(
                f"unsafe or existing shelving destination: {item.get('destination')}",
                site=f"{ctx.operation}.bad-destination",
                prefixed=True,
                exit_code=2,
            )
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            raise WriteRefused(
                f"proposal item {item.get('id')} has no reviewable content",
                site=f"{ctx.operation}.empty-content",
                prefixed=True,
                exit_code=2,
            )
        writes[target] = content.rstrip() + "\n"
    # Applied items leave the packet — their receipts record them — and the
    # packet keeps state "proposed" while unapplied items remain, so the
    # review queue (which lists shelving only at "proposed") keeps showing
    # the remainder that still awaits a decision.
    remaining = [item for item in packet_items if item.get("id") not in selected]
    shelving["items"] = remaining
    shelving["state"] = "proposed" if remaining else "applied"
    writes[study_map.path] = _dump_study_map(study_map, data)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "applied": sorted(selected)},
        proposal=TransactionProposal(
            capability="review.apply",
            writes=writes,
            artifact_ids=[req["unit_id"], study_map.id, *sorted(selected)],
            expected_revisions=expected_revisions,
        ),


    )


def _file_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def prune_empty_dirs(inbox: Path, target: Path) -> None:
    """Remove directories the move just emptied, up to (not incl.) the inbox.

    Best-effort structural cleanup after a committed move: empty
    directories carry no canonical content (Git does not track them, the
    fingerprint walks files), so a redir that fills again concurrently
    simply stops the prune. Never touches the inbox itself.
    """
    cursor = target if target.is_dir() else target.parent
    while cursor != inbox and inbox in cursor.parents:
        try:
            if any(cursor.iterdir()):
                return
            cursor.rmdir()
        except OSError:
            return
        cursor = cursor.parent


def _folder_digest(files: dict[str, bytes]) -> str:
    """One digest for a folder drop: SHA-256 over the sorted name->sha map.

    Canonical JSON over parsed digests, never raw bytes, so the value is
    stable regardless of read order and re-derivable by any caller holding
    the same files.
    """
    manifest = {name: hashlib.sha256(files[name]).hexdigest()
                for name in sorted(files)}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _admit(inbox: Path, name: str) -> Path:
    """The inbox path ``name`` addresses, or raise with a refusal message."""
    if not name or name in {".", "./"} or Path(name).is_absolute() \
            or ".." in Path(name).parts:
        raise ValueError(f"inbox name must be relative to work/inbox: {name}")
    target = inbox / name
    try:
        target.resolve(strict=True).relative_to(inbox.resolve(strict=True))
    except OSError as exc:
        raise ValueError(f"inbox item not found: {name}") from exc
    cursor: Path | None = target
    while cursor is not None and cursor != inbox and inbox in cursor.parents:
        if cursor.is_symlink():
            raise ValueError("inbox resolve refuses symlinks")
        cursor = cursor.parent if cursor != cursor.parent else None
    return target


def _collect(inbox: Path, target: Path) -> dict[str, bytes]:
    """Every regular file under ``target`` as inbox-relative name -> bytes."""
    if target.is_file() and not target.is_symlink():
        return {target.relative_to(inbox).as_posix(): target.read_bytes()}
    if not target.is_dir() or target.is_symlink():
        raise ValueError(f"inbox item is not a regular file or folder: {target.name}")
    files: dict[str, bytes] = {}
    for path in sorted(target.rglob("*")):
        if path.is_symlink():
            raise ValueError("inbox resolve refuses symlinks")
        if not path.is_file():
            continue
        files[path.relative_to(inbox).as_posix()] = path.read_bytes()
    if not files:
        raise ValueError(f"inbox item has no files to archive: {target.name}")
    return files


@register("inbox.resolve", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def inbox_resolve(ctx: OpContext, req: dict) -> Result:
    """Resolve one routed inbox drop to the archive.

    The drop's SHA-256 must match the bytes read (a changed drop
    refuses), ``routed_to`` names every destination that received it (a
    missing destination refuses), and the receipt names both endpoints
    plus ``routed_to``. The archive never overwrites: a collision
    refuses rather than merging histories. Directories the move empties
    are pruned after the commit lands.
    """
    root = ctx.root
    if current_gateway_request() is None:
        message = ("inbox resolve requires GatewayEnvelopeV2; "
                   "direct CLI application is disabled")
        raise WriteRefused(
            message,
            site="inbox.resolve.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    try:
        inbox = root / "work" / "inbox"
        try:
            target = _admit(inbox, req["name"])
            files = _collect(inbox, target)
        except ValueError as exc:
            raise WriteRefused(
                str(exc),
                site="inbox.resolve.bad-name",
                prefixed=True,
                exit_code=2,
            ) from exc
        if target.is_file():
            actual = _file_digest(next(iter(files.values())))
        else:
            actual = _folder_digest(files)
        if actual != req["drop_sha256"]:
            message = (
                f"inbox drop changed since read: {req['name']} "
                f"(re-read it with `inbox-read {req['name']}` and re-seal)")
            raise WriteRefused(
                message,
                site="inbox.resolve.drop-changed",
                prefixed=True,
                exit_code=2,
            )
        routed_to = [str(entry).strip() for entry in (req["routed_to"] or [])]
        if not routed_to or any(not entry for entry in routed_to):
            message = ("inbox resolve needs a non-empty routed_to list "
                       "naming where the drop went")
            raise WriteRefused(
                message,
                site="inbox.resolve.missing-routed-to",
                prefixed=True,
                exit_code=2,
            )
        year = str(observations.today().year)
        writes: dict[Path, bytes] = {}
        deletes: list[Path] = []
        for rel, data in files.items():
            destination = root / "archive" / "inbox" / year / rel
            if destination.exists() or destination.is_symlink():
                message = (
                    f"archive already holds "
                    f"{destination.relative_to(root).as_posix()}; "
                    "the archive never overwrites")
                raise WriteRefused(
                    message,
                    site="inbox.resolve.archive-collision",
                    prefixed=True,
                    exit_code=2,
                )
            writes[destination] = data
            deletes.append(inbox / rel)
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site="inbox.resolve.read-failed",
            prefixed=True,
            exit_code=2,
        ) from exc
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc),
            site="inbox.resolve.bad-expected-revision",
            gateway_message=str(exc),
            exit_code=2,
        ) from exc

    return Result(
        {"ok": True, "resolved": req["name"],
         "archived": sorted(path.relative_to(root).as_posix()
                            for path in writes),
         "routed_to": routed_to},
        proposal=TransactionProposal(
            capability="inbox.resolve",
            completion=InboxCompletion(inbox, target),
            writes=writes,
            artifact_ids=(),
            deletes=deletes,
            metadata={"routed_to": routed_to},
            expected_revisions=expected_revisions,
        ),



    )
