"""T07 — The UI consuming a canvas world.

The seam analysis so far was static: the UI's client names no note-reading
command, and the projection carries 2.5 % of the corpus text. This suite
makes it *runtime*:

  1. build a synthetic world with a synthetic durable note,
  2. point the UI's own "real projection" pass at that world's
     projection instead of the Core checkout's,
  3. run the UI's own library-finder against it,
  4. measure what the UI can reach of that note.

The UI's test suite reads `../repository/generated/manifest.json` — the
sibling Core checkout's projection. Swapping in a canvas world's projection
makes the UI consume synthetic data through its own code.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

CORE_MANIFEST = C.CORE_CLONE / "generated" / "manifest.json"
UI_TESTS = C.UI_CLONE / "tests"


def main() -> int:
    world = C.build_world(WORLDS, "t07")
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # ---- 1. a synthetic durable note in a synthetic world ----------------
    def synthetic_note() -> dict:
        # The UI's library tree is organised by thematic group; the bare
        # characterization fixture has none (its repair step removes the
        # file). Give the canvas world one so the tree has domains.
        groups = world.root / "curriculum/thematic-groups.yaml"
        groups.parent.mkdir(parents=True, exist_ok=True)
        groups.write_text(
            "thematic_groups:\n"
            "- id: thematic-group-probe\n"
            '  title: "Probe Domain"\n'
            '  description: "The synthetic corpus\'s one domain."\n'
            "  order: 1\n",
            encoding="utf-8")
        body = world.scratch("canvas-note.md")
        body.write_text(
            "# Synthetic — The Cartographic Interlude\n\n"
            "The opening paragraph, which the projection summarises.\n\n"
            "## The part only the body carries\n\n"
            "MARKER-BODY-ONLY-SENTINEL: this sentence appears nowhere in the "
            "projection.\n",
            encoding="utf-8")
        seal, apply = world.write("note.create", {
            "body_file": str(body),
            "body_file_sha256":
                "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest(),
            "note": {
                "id": "note-canvas-interlude",
                "path": "knowledge/notes/mathematics/note-canvas-interlude.md",
                "title": "Synthetic — The Cartographic Interlude",
                "role": "synthesis",
                "concepts": ["concept-variance"],
                "sources": ["source-demo-book"],
                "contexts": ["workspace-demo"],
            },
        }, "t07-note")
        generate = world.los_tool("generate.py")
        manifest = json.loads(
            (world.root / "generated/manifest.json").read_text(encoding="utf-8"))
        record = next((r for r in manifest.get("records", [])
                       if isinstance(r, dict)
                       and r.get("id") == "note-canvas-interlude"), None)
        detail = {
            "write_exit": apply.exit_code,
            "generate_exit": generate.exit_code,
            "note_in_projection": record is not None,
            "projection_keys": sorted(record.keys()) if record else None,
            "has_body_key": bool(record and "body" in record),
            "summary": (record or {}).get("summary"),
        }
        detail["ok"] = apply.exit_code == 0 and record is not None
        return detail

    add("u1-synthetic-note-in-the-projection",
        "Build a synthetic world and file a synthetic durable note in it.",
        synthetic_note, ["ui", "runtime"])

    # ---- 2. the UI consumes the canvas world ----------------------------
    def ui_consumes() -> dict:
        backup = CORE_MANIFEST.with_suffix(".json.t07-backup")
        CORE_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        if CORE_MANIFEST.exists():
            shutil.copy2(CORE_MANIFEST, backup)
        try:
            shutil.copy2(world.root / "generated/manifest.json",
                         CORE_MANIFEST)
            run = subprocess.run(
                ["node", str(UI_TESTS / "test-library-finder.js")],
                capture_output=True, text=True, cwd=str(C.UI_CLONE),
                timeout=600)
        finally:
            if backup.exists():
                shutil.move(str(backup), str(CORE_MANIFEST))
            elif CORE_MANIFEST.exists():
                CORE_MANIFEST.unlink()
        output = (run.stdout + run.stderr)
        detail = {
            "exit_code": run.returncode,
            "output_tail": output.strip()[-900:],
            "consumed_canvas_world": "core projection OK" in output,
            "note": ("the UI's own library-finder passed over the canvas "
                     "world's projection; the real checkout's projection was "
                     "restored afterwards"),
        }
        detail["ok"] = run.returncode == 0 and "core projection OK" in output
        return detail

    add("u2-the-ui-consumes-the-canvas-world",
        "Run the UI's own projection pass against the canvas world.",
        ui_consumes, ["ui", "runtime"])

    # ---- 3. what the UI can reach of that note ---------------------------
    def reachable() -> dict:
        manifest = json.loads(
            (world.root / "generated/manifest.json").read_text(encoding="utf-8"))
        record = next(r for r in manifest["records"]
                      if r.get("id") == "note-canvas-interlude")
        body = (world.root / record["path"]).read_text(encoding="utf-8")
        raw = json.dumps(manifest)
        # What the UI's own source reads for a note.
        atlas = (C.UI_CLONE / "src/features/atlas/domains.ts").read_text(
            encoding="utf-8")
        rendered = [f for f in ("Authorship", "Lifecycle", "Semantic review",
                                "Recorded sources", "material_analysis",
                                "Recorded evidence")
                    if f in atlas]
        detail = {
            "note_body_chars": len(body),
            "summary_chars": len(record.get("summary") or ""),
            "share_reachable": round(
                len(record.get("summary") or "") / max(len(body), 1), 3),
            "body_string_present_in_projection":
                "MARKER-BODY-ONLY-SENTINEL" in raw,
            "summary_present_in_projection":
                "opening paragraph" in raw,
            "ui_rendered_note_facts": rendered,
            "note": ("the projection carries the note's identity, summary "
                     "and provenance; the prose itself is not in it, so a "
                     "UI-only consumer cannot read what the librarian wrote"),
        }
        detail["ok"] = not detail["body_string_present_in_projection"]
        return detail

    add("u3-what-the-ui-can-reach-of-the-note",
        "Measure what a UI-only consumer can see of the synthetic note.",
        reachable, ["ui", "seam", "runtime"])

    # ---- 4. the UI's own suite, for the record --------------------------
    def ui_suite() -> dict:
        run = subprocess.run(["npm", "test"], capture_output=True, text=True,
                              cwd=str(C.UI_CLONE), timeout=3600)
        output = run.stdout
        marks = [line for line in output.splitlines()
                 if "OK" in line or "passed" in line or "✔" in line]
        detail = {
            "exit_code": run.returncode,
            "highlights": marks[-14:],
            "note": ("the UI's own suite, run in the isolated clone with "
                     "node_modules present"),
        }
        detail["ok"] = run.returncode == 0
        return detail

    add("u4-the-ui-suite",
        "Run the UI's own test suite in the clone.",
        ui_suite, ["ui", "verification"])

    outcomes = run_cases(cases, REPORTS / "t07",
                         "T07 — The UI consuming a canvas world")
    print()
    print(f"T07: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
