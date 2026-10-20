"""T04 — The consumption seam.

The previous review claimed a specific seam: *"the UI has no path to
`note.content` or `note.search`"*, and therefore *"you can consume the
library, but you cannot audit the librarian's filing in the place where
you consume"*.

This file tests that claim mechanically rather than by inspection:

  1. Extract every Core command the Obsidian UI's gateway client can
     actually invoke, from the client's own source.
  2. Intersect it with the Core's declared capability catalog.
  3. Measure what a projection-only consumer (the UI) can see of a durable
     note, against what the note corpus actually contains.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

#: Core's declared read-side queries (from `los capabilities --compact --json`).
NOTE_READING_QUERIES = {"note.content", "note.search"}
NOTE_READING_COMMANDS = {"note-read"}


def ui_source() -> str:
    files = sorted((C.UI_CLONE / "src").rglob("*.ts"))
    return "\n".join(f.read_text(encoding="utf-8", errors="replace")
                     for f in files)


def ui_commands(source: str) -> set[str]:
    """Every CLI verb the UI can name as a `los` argument."""
    verbs: set[str] = set()
    verbs |= set(re.findall(r"\[\s*'([a-z][a-z0-9-]{2,30})'", source))
    verbs |= set(re.findall(r"args\s*=\s*\[\s*'([a-z][a-z0-9-]{2,30})'", source))
    verbs |= set(re.findall(r"this\.call\(\[\s*'([a-z][a-z0-9-]{2,30})'", source))
    verbs |= set(re.findall(r"this\.capability\(\s*'([a-z][a-z0-9.-]+)'", source))
    return verbs


def main() -> int:
    world = C.build_world(WORLDS, "t04")
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # ---- 1. the UI's reachable surface ---------------------------------
    def ui_surface() -> dict:
        source = ui_source()
        verbs = ui_commands(source)
        catalog = world.los("capabilities", "--compact", "--json").json or {}
        declared_queries = set(catalog.get("queries", {}))
        declared_commands = set(catalog.get("commands", {}))
        reachable_queries = sorted(verbs & declared_queries)
        reachable_commands = sorted(verbs & declared_commands)
        detail = {
            "ui_source_files": len(list((C.UI_CLONE / "src").rglob("*.ts"))),
            "ui_verbs_named": len(verbs),
            "core_declared_queries": len(declared_queries),
            "core_declared_commands": len(declared_commands),
            "reachable_queries": reachable_queries,
            "reachable_write_capabilities": reachable_commands,
            "note_reading_reachable": sorted(
                verbs & (NOTE_READING_QUERIES | NOTE_READING_COMMANDS)),
            "note_queries_declared_but_unreachable": sorted(
                NOTE_READING_QUERIES - set(reachable_queries)),
        }
        detail["ok"] = not detail["note_reading_reachable"]
        return detail

    add("s1-ui-reachable-surface",
        "Which Core capabilities can the Obsidian UI actually invoke?",
        ui_surface, ["seam", "ui"])

    # ---- 2. what a projection-only consumer sees of a note --------------
    def projection_view() -> dict:
        world.los_tool("generate.py")
        manifest = json.loads(
            (world.root / "generated/manifest.json").read_text(encoding="utf-8"))
        records = [r for r in manifest.get("records", [])
                   if isinstance(r, dict) and r.get("type") == "note"]
        rows = []
        for record in records:
            note_id = record.get("id")
            path = world.root / (record.get("path") or "")
            body = path.read_text(encoding="utf-8") if path.exists() else ""
            summary = record.get("summary") or ""
            rows.append({
                "note_id": note_id,
                "projection_keys": sorted(record.keys()),
                "body_chars": len(body),
                "summary_chars": len(summary),
                "visible_fraction": (round(len(summary) / len(body), 3)
                                     if body else None),
                "has_body_key": "body" in record,
            })
        # What the gateway would give the same note.
        if records:
            note_id = records[0].get("id")
            read = world.los("note-read", note_id)
            body_payload = read.json or {}
        else:
            body_payload = {}
        detail = {
            "notes_in_projection": len(records),
            "rows": rows,
            "gateway_note_read_bytes": len(json.dumps(body_payload)),
            "note": ("the projection carries a note's identity, summary and "
                     "provenance; the body only travels through note.content"),
        }
        detail["ok"] = bool(rows) and all(not r["has_body_key"] for r in rows)
        return detail

    add("s2-projection-vs-note-body",
        "What does a projection-only consumer see of a durable note?",
        projection_view, ["seam", "projection"])

    # ---- 3. can the corpus be searched from the UI's surface? -----------
    def search_surface() -> dict:
        listing = world.los("search", "expected", "--content")
        body = listing.json
        detail = {
            "search_content_exit": listing.exit_code,
            "matches": (body.get("matches") if isinstance(body, dict) else None),
            "keys": sorted(body.keys())[:20] if isinstance(body, dict) else None,
            "note": ("`search --content` reaches the full text of durable "
                     "notes, and it is a CLI command the UI never names"),
        }
        detail["ok"] = listing.exit_code == 0
        return detail

    add("s3-note-corpus-search",
        "The durable-note corpus is searchable — but only from the CLI.",
        search_surface, ["seam", "note-corpus"])

    # ---- 4. the UI's own knowledge surface ------------------------------
    def ui_note_views() -> dict:
        source = ui_source()
        atlas_notes = "collection: 'notes'" in source or "'notes'" in source
        detail = {
            "ui_has_a_notes_collection": atlas_notes,
            "ui_note_body_reads": len(re.findall(
                r"note-read|note\.content|note\.search", source)),
            "note": ("the Atlas surface filters note *records*; no UI code "
                     "path reads a note body"),
        }
        detail["ok"] = detail["ui_note_body_reads"] == 0
        return detail

    add("s4-ui-has-no-note-body-path",
        "Does any UI code path read a durable note's body?",
        ui_note_views, ["seam", "ui"])

    # ---- 5. what the UI actually renders about a note --------------------
    def ui_rendered_note_facts() -> dict:
        """The Atlas surface renders a note's provenance facts.

        The previous review claimed the UI gives no way to audit the
        librarian's filing. That is wrong about the *bindings*: the UI
        renders authorship, lifecycle, sources, the material_analysis
        provenance and every recorded evidence ref. What it does not
        render is the note's body.
        """
        atlas = (C.UI_CLONE / "src/features/atlas/domains.ts").read_text(
            encoding="utf-8")
        rendered = {}
        for label, needle in (
            ("summary", "prose(note.summary)"),
            ("authorship", "Authorship"),
            ("lifecycle", "Lifecycle"),
            ("semantic_review", "Semantic review"),
            ("reviewed", "Reviewed"),
            ("recorded_sources", "Recorded sources"),
            ("material_analysis", "note.material_analysis"),
            ("analysis_resolution", "analysis.resolution"),
            ("inspected_range", "analysis.inspected_range"),
            ("recorded_evidence", "note.evidence"),
        ):
            rendered[label] = needle in atlas
        detail = {
            "rendered_facts": rendered,
            "renders_note_body": "note.body" in atlas or "note.content" in atlas,
            "renders_evidence_refs": "item.ref" in atlas,
            "resolves_evidence_refs": "resolve" in atlas.lower() and "evidence" in atlas.lower(),
            "note": ("the UI shows the bindings and the refs, but not the "
                     "body, and it does not resolve a ref against the "
                     "corpus"),
        }
        detail["ok"] = all(rendered.values()) and not detail["renders_note_body"]
        return detail

    add("s5-ui-renders-note-provenance",
        "Does the UI render a note's provenance, or only its summary?",
        ui_rendered_note_facts, ["seam", "ui", "correction"])

    outcomes = run_cases(cases, REPORTS / "t04", "T04 — The consumption seam")
    print()
    print(f"T04: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
