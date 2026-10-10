"""Capture-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from learning_os import observations
from learning_os.contracts.gateway import (
    current_gateway_request,
    request_artifact_id,
)
from learning_os.domain.failures import StaleSnapshot, WriteRefused
from learning_os.ops._legacy_plumbing import (
    _admit,
    _bytes_inside_owner,
    _collect,
    _content_envelope,
    _discovery_row,
    _folder_digest,
    _inbox_search_rows,
    _json_layout,
    _read_content_bound_file,
    _snapshot,
    _window_values,
)
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions


def _dumps_capture(payload: dict) -> str:
    """The exact capture encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


def _human_capture(payload: dict) -> str:
    """The exact default-branch prose: the capture line plus the routing note."""
    return (
        f"captured -> {payload['captured']}\n"
        "routing is the operator's job (WORKFLOWS §21); the inbox trends "
        "toward empty"
    )


def _on_commit_refused(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


def _dumps_garden_seed(payload: dict) -> str:
    """The exact garden-seed JSON encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


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


@register("capture.create", kind="command", human=_human_capture)
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
    else:
        capture_text = req.get("text") if req.get("text") is not None else sys.stdin.read()
        if not capture_text.strip():
            raise WriteRefused(
                "nothing to capture (empty input)",
                site=f"{ctx.operation}.empty-input",
                gateway_message="los: nothing to capture (empty input)",
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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_capture,
    )


@register("garden.seed.create", kind="command", human=_human_garden_seed)
def garden_seed_create(ctx: OpContext, req: dict) -> Result:
    """Create one free-form Markdown seed under knowledge/garden/."""
    root = ctx.root
    text = str(req["text"] or "")

    if not text.strip():
        raise WriteRefused(
            "Garden seed text is empty; nothing was written",
            site=f"{ctx.operation}.empty-text",
            gateway_message="los: Garden seed text is empty; nothing was written",
            exit_code=2,
        )

    title = str(req.get("title") or "").strip() or None

    ctx.require_snapshot(req.get("expected_snapshot"))

    garden = root / "knowledge" / "garden"
    slug = _seed_slug(text, title)

    target = garden / f"{slug}.md"
    serial = 2

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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_garden_seed,
    )


def _dumps_inbox_list(payload: list) -> str:
    """The exact inbox-list JSON encoder: terminal layout, sorted, unescaped."""
    return json.dumps(payload, **_json_layout(), sort_keys=True, ensure_ascii=False)


@register("cli.inbox-list", kind="tool")
@register("inbox.list", kind="tool")
def inbox_list(ctx: OpContext, req: dict) -> Result:
    """List work/inbox files by name, without reading bytes."""
    root = ctx.root
    try:
        rows = _inbox_search_rows(root)
    except OSError as exc:
        raise WriteRefused(
            f"cannot list work/inbox: {exc}",
            site=f"{ctx.operation}.list-failed",
            gateway_message=f"los: cannot list work/inbox: {exc}",
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
    return Result(out, json_dumps=_dumps_inbox_list)


def _dumps_inbox_read(payload: dict) -> str:
    """The exact inbox-read JSON encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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


@register("cli.inbox-read", kind="query")
@register("inbox.content", kind="query")
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
                gateway_message=f"los: inbox name must be relative to work/inbox: {name}",
                exit_code=2,
            )
        snapshot = _snapshot(root, req.get("expected_snapshot"))
        target = root / "work" / "inbox" / name
        if target.is_dir() and not target.is_symlink():
            payload = _inbox_folder_envelope(root, name)
            _snapshot(root, snapshot)
            return Result(
                {"schema_version": 1, "snapshot_id": snapshot, **payload},
                json_dumps=_dumps_inbox_read,
            )
        if not target.is_symlink() and not target.is_file():
            raise WriteRefused(
                f"inbox item not found: {name}",
                site=f"{ctx.operation}.unknown-item",
                gateway_message=f"los: inbox item not found: {name}",
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
                gateway_message=(
                    f"los: inbox item is not UTF-8 text and has no text read: {name}"
                ),
                exit_code=2,
            ) from exc
        payload = _content_envelope(
            "inbox-content", "item", name,
            target.relative_to(root).as_posix(),
            raw, content, offset, limit)
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **payload},
            json_dumps=_dumps_inbox_read,
        )
    except StaleSnapshot as exc:
        raise StaleSnapshot(
            str(exc),
            site=f"{ctx.operation}.stale-snapshot",
            gateway_message=f"los: {exc}",
            exit_code=3,
        ) from exc
    except OSError as exc:
        raise WriteRefused(
            str(exc),
            site=f"{ctx.operation}.read-failed",
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
