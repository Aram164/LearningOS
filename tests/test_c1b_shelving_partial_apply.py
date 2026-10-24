"""C1-B finding: a partial shelving apply hides the unapplied remainder.

``review.apply`` exists for exactly the partial case — OPERATOR boundary 9:
"Apply only explicitly selected proposal items" — and the handler keeps every
unselected item in the packet, appliable by a later ``review.apply`` call. But
``shelving_apply`` sets ``shelving["state"] = "applied"`` unconditionally
(tools/learning_os/app/handlers/capture.py), and the decision surface
(``build_review_items``, tools/learning_os/derive/projection/review.py)
publishes a shelving row only while ``state == "proposed"``. After applying a
subset, the still-pending remainder is appliable but invisible: the manifest's
``review_items`` carries no row for it, and nothing else surfaces it.

Expected: while unapplied proposal items remain in the packet, the decision
surface still lists the shelving packet. Observed on base main (d6c47790):
after applying one of two items, ``review_items`` is empty for the unit while
``proposal-beta`` sits unapplied in ``shelving.items``.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from conftest import build_mini_repo  # noqa: F401  (mini_repo lives in conftest)
from gateway_helpers import approved_v2_call, approved_v2_envelope, file_sha256, run_v2_capability
from repo_builders import add_curriculum, run_los

from learning_os.app.validation_service import collect
from learning_os.store.warning_baseline import write_baseline


def _review_categories(root: Path) -> list[str]:
    generated = run_los(root, "generate")
    assert generated.returncode == 0, generated.stdout + generated.stderr
    manifest = json.loads((root / "generated/manifest.json").read_text(encoding="utf-8"))
    return [str(row.get("category")) for row in manifest.get("review_items", [])]


def _shelving(root: Path) -> dict:
    data = yaml.safe_load((root / "curriculum/modules/module-demo/units/"
                           "unit-demo-l01/study-map.yaml").read_text(encoding="utf-8"))
    return data.get("shelving") or {}


def _proposal_items() -> list[dict]:
    def note(ident: str, body: str) -> str:
        return ("---\n"
                f"id: note-probe-{ident}\n"
                "type: note\n"
                f"title: Probe {ident.upper()}\n"
                "created: 2026-10-24\n"
                "sources: [source-demo-book]\n"
                "---\n\n"
                f"{body}\n")

    return [
        {"id": "proposal-alpha", "kind": "durable-note", "title": "Alpha",
         "destination": "knowledge/notes/mathematics/note-probe-a.md",
         "rationale": "probe", "content": note("a", "first"), "selected": True},
        {"id": "proposal-beta", "kind": "durable-note", "title": "Beta",
         "destination": "knowledge/notes/mathematics/note-probe-b.md",
         "rationale": "probe", "content": note("b", "second"), "selected": True},
    ]


def _prepare_two_item_packet(root: Path):
    items_path = root / "work/probe-items.json"
    items_path.parent.mkdir(parents=True, exist_ok=True)
    items_path.write_text(json.dumps({"items": _proposal_items()}), encoding="utf-8")
    envelope = approved_v2_envelope(
        root, capability="review.prepare",
        payload={"unit_id": "unit-demo-l01",
                 "items_file": str(items_path),
                 "items_file_sha256": file_sha256(items_path)},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01"],
        idempotency_key="c1b-shelving-prepare")
    prepared = run_v2_capability(root, envelope)
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr


def test_partial_shelving_apply_keeps_remainder_visible(mini_repo):
    root = mini_repo
    add_curriculum(root)
    signatures, errors = collect(root)
    assert not errors, errors
    write_baseline(root, signatures, "C1-B shelving fixture")

    _prepare_two_item_packet(root)
    assert "shelving" in _review_categories(root)  # the packet is on the queue

    applied = approved_v2_call(
        root, capability="review.apply",
        payload={"unit_id": "unit-demo-l01", "selected": ["proposal-alpha"]},
        artifact_ids=["unit-demo-l01", "study-map-demo-l01", "proposal-alpha"],
        idempotency_key="c1b-shelving-apply-alpha")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert (root / "knowledge/notes/mathematics/note-probe-a.md").exists()
    assert not (root / "knowledge/notes/mathematics/note-probe-b.md").exists()

    shelving = _shelving(root)
    remaining = [item["id"] for item in shelving.get("items", [])]
    # The packet still carries the unapplied item, and a later apply of it is
    # accepted — so the system itself treats the remainder as pending …
    assert "proposal-beta" in remaining
    # … which makes the queue dropping it a silent loss: the unapplied
    # remainder must stay on the decision surface while it remains appliable.
    assert "shelving" in _review_categories(root), (
        "after a partial review.apply, the unapplied proposal item "
        f"({remaining}) is still in the packet and appliable, but the "
        "manifest's review_items no longer lists the shelving packet"
    )
