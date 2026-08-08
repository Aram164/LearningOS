"""Judgment-free Garden seed creation.

Planting a seed records the learner's text in the exploratory Garden. It does
not classify, route, interpret, harvest, or invoke AI.
"""

from __future__ import annotations

import json
import re
import sys

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
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


def cmd_garden_seed_create(args) -> int:
    """Create one free-form Markdown seed under knowledge/garden/."""
    root = _root(args)
    text = str(args.text or "")

    if not text.strip():
        print("los: Garden seed text is empty; nothing was written", file=sys.stderr)
        return 2

    title = str(args.title or "").strip() or None

    with _operator_lock(root):
        if not _expected_ok(
            root,
            getattr(args, "expected_snapshot", None),
        ):
            return 3

        garden = root / "knowledge" / "garden"
        slug = _seed_slug(text, title)

        target = garden / f"{slug}.md"
        serial = 2

        while target.exists():
            target = garden / f"{slug}-{serial}.md"
            serial += 1

        relative = target.relative_to(root).as_posix()
        content = _seed_content(text, title)

        code, errors, confirmation = _write_transaction(
            root,
            {target: content},
            capability="garden.seed.create",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[f"garden:{relative}"],
        )

        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code

    result = {
        "ok": True,
        "seed_path": relative,
        **confirmation,
    }

    if getattr(args, "json", False):
        print(json.dumps(result, ensure_ascii=False))
        return 0

    print(f"Garden seed created -> {relative}")
    print("No classification, routing, harvesting, or AI action was performed.")
    return 0
