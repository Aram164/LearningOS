"""The A11 surface snapshot matches the live code (PLAN A11)."""

from __future__ import annotations

import json
from pathlib import Path

import arch_surface

ROOT = Path(__file__).resolve().parent.parent
SURFACE_PATH = ROOT / arch_surface.ARCHITECTURE_DIR / arch_surface.SURFACE_FILENAME
REL = SURFACE_PATH.relative_to(ROOT).as_posix()

FIX = "Surface changes need an approval line (PLAN A11)."


def test_surface_snapshot_is_in_canonical_form():
    recorded_text = SURFACE_PATH.read_text(encoding="utf-8")
    recorded = json.loads(recorded_text)
    assert recorded_text == arch_surface.dump_surface(recorded), (
        f"A11 {REL}:1: stored snapshot is not canonical "
        f"(sorted keys, indent 1); regenerate it — {FIX}"
    )


def test_surface_snapshot_matches_live_code():
    recorded = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
    live = arch_surface.build_surface(ROOT)
    if live == recorded:
        return
    recorded_flat = arch_surface.flatten_surface(recorded)
    live_flat = arch_surface.flatten_surface(live)
    diff = arch_surface.diff_keys(recorded_flat, live_flat)
    recorded_text = SURFACE_PATH.read_text(encoding="utf-8")
    live_text = arch_surface.dump_surface(live)
    lines = []
    for key in sorted(diff):
        text = live_text if key not in recorded_flat else recorded_text
        lineno = arch_surface.locate_line(text, key)
        lines.append(f"A11 {key}: {diff[key]} — {REL}:{lineno} — {FIX}")
    raise AssertionError("surface drift:\n" + "\n".join(lines))
