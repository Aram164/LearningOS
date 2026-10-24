"""C1-D finding: material.context turns an explicit ``--limit 0`` into 20.

The request contract bounds the page: "page size from 1 to 20 items"
(system/schema/requests/material.context.schema.json), and the shared window
helper refuses anything outside 1..maximum (``_window_values``). But
``material_context`` reads the page as ``req.get("limit") or 20`` first, so an
explicit zero — falsy — never reaches the check: it silently becomes the
maximum page of 20. ``inbox.content`` takes ``req["limit"]`` verbatim and
refuses 0; ``material.context`` is the odd one out.

Expected: ``--limit 0`` is refused, or the response carries at most the
requested zero items. Observed on base main (d6c47790): the query succeeds and
returns the full 20-item page.
"""

from __future__ import annotations

import json
from pathlib import Path

from repo_builders import run_los


def _seed_one_match(root: Path) -> None:
    import hashlib

    import yaml

    material = root.parent / "materials" / "deck.pdf"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_bytes(b"live bytes")
    digest = hashlib.sha256(b"live bytes").hexdigest()

    body = ("# Density intuition\n\n"
            "The density chapter explains probability mass spreading over "
            "intervals.\n"
            "A worked example integrates the uniform density step by step.\n")
    binding = {
        "resolution": "resolved",
        "material": "deck.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": digest,
        "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(body.encode("utf-8")),
    }
    meta = {"id": "note-context-density-pp001-003", "type": "note",
            "role": "reference", "title": "Planted analysis",
            "created": "2026-09-21", "state": "rough",
            "authorship": "operator-drafted", "semantic_review": "unreviewed",
            "material_analysis": binding}
    path = root / "knowledge/notes/mathematics/note-context-density-pp001-003.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))


def test_zero_limit_is_refused_not_silently_widened(mini_repo: Path):
    _seed_one_match(mini_repo)
    proc = run_los(mini_repo, "material-context", "density worked example",
                   "--limit", "0")
    data = json.loads(proc.stdout) if proc.returncode == 0 else None
    # Fix-agnostic: refused, or the page honors the requested zero-item size.
    assert proc.returncode != 0 or not (data or {}).get("items"), (
        f"--limit 0 returned {len((data or {}).get('items') or [])} item(s) "
        f"(total={(data or {}).get('total')}); the request contract bounds the "
        "page size to 1..20 and _window_values refuses out-of-range limits, "
        "but material_context's 'or 20' fallback widens an explicit zero to a "
        "full maximum page instead of refusing it"
    )
