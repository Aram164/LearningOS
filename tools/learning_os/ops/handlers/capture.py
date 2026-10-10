"""Capture-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json
import re
import sys

from learning_os import observations
from learning_os.contracts.gateway import (
    current_gateway_request,
    request_artifact_id,
)
from learning_os.domain.failures import WriteRefused
from learning_os.ops._legacy_plumbing import _read_content_bound_file
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
