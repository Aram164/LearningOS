#!/usr/bin/env python3
"""Rewrite physical-path ``material://`` URIs into the id-based canonical form.

    python tools/normalise_material_uris.py           # report what would change
    python tools/normalise_material_uris.py --apply

WHY
---
The canonical reference form is ``material://source-<id>/<path-inside-source>``,
resolved through the ``materials/.flat/`` symlink farm. That indirection exists
so the physical topic tree can be reorganised without touching a single
reference. A URI that names the physical path directly
(``material://Math/Analysis/course/…``) bypasses it and breaks silently the next
time the folder is re-homed — which ADR-007 is about to do deliberately.

This tool resolves each physical-form URI back through the ``.flat/`` farm to the
source that owns it and rewrites the reference. It never invents a mapping: a URI
whose file is not inside any registered source folder is reported and left alone,
because that case needs a human decision (usually: register the source first).

Filenames under materials/ contain spaces, so the delimited forms (code spans and
markdown links) are matched before bare whitespace-delimited ones — see
learning_os.rules.materials for the same reasoning.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATERIALS = ROOT.parent / "materials"
FLAT = MATERIALS / ".flat"
CANONICAL_TREES = ("knowledge", "sources", "records", "work", "curriculum", "projects")
TEXT_SUFFIXES = {".md", ".yaml", ".yml"}

def source_prefixes() -> list[tuple[str, str]]:
    """[(physical prefix, source-id)] sorted longest-first for greedy matching."""
    pairs = []
    if not FLAT.is_dir():
        return pairs
    for link in FLAT.iterdir():
        if not link.is_symlink():
            continue
        try:
            target = link.resolve().relative_to(MATERIALS.resolve()).as_posix()
        except (OSError, ValueError):
            continue
        pairs.append((target, link.name))
    return sorted(pairs, key=lambda row: -len(row[0]))


def rewrite_payload(payload: str, prefixes: list[tuple[str, str]]) -> str | None:
    """physical path -> ``source-<id>/rest``; None when no source owns it."""
    if payload.startswith("source-"):
        return None  # already canonical
    clean = payload.strip().strip("/")
    for physical, source_id in prefixes:
        if clean == physical:
            return source_id
        if clean.startswith(physical + "/"):
            return f"{source_id}/{clean[len(physical) + 1:]}"
    return None


def process_text(text: str, prefixes):
    """Return (new_text, [(old, new)], [unmapped])."""
    from learning_os.rules.materials import (MATERIAL_URI_BARE,
                                             MATERIAL_URI_DELIMITED)

    changes: list[tuple[str, str]] = []
    unmapped: list[str] = []

    def replace(match):
        payload = match.group(1)
        new = rewrite_payload(payload.split("#", 1)[0], prefixes)
        if new is None:
            if not payload.startswith("source-"):
                unmapped.append(payload)
            return match.group(0)
        fragment = payload[len(payload.split("#", 1)[0]):]
        changes.append((payload, new + fragment))
        return match.group(0).replace(f"material://{payload}",
                                      f"material://{new}{fragment}")

    for pattern in MATERIAL_URI_DELIMITED:
        text = pattern.sub(replace, text)
    text = MATERIAL_URI_BARE.sub(replace, text)
    return text, changes, unmapped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="write the rewritten files (default: report only)")
    args = parser.parse_args()

    prefixes = source_prefixes()
    if not prefixes:
        print(f"no {FLAT} symlink farm — run tools/build_materials_tree.py first",
              file=sys.stderr)
        return 2

    total, unmapped_all, touched = 0, [], []
    for tree in CANONICAL_TREES:
        base = ROOT / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "material://" not in text:
                continue
            new_text, changes, unmapped = process_text(text, prefixes)
            unmapped_all.extend((path, u) for u in unmapped)
            if not changes:
                continue
            total += len(changes)
            touched.append((path, len(changes)))
            if args.apply:
                path.write_text(new_text, encoding="utf-8")

    for path, count in touched:
        print(f"{'rewrote' if args.apply else 'would rewrite'} {count:4d}  "
              f"{path.relative_to(ROOT)}")
    print(f"\n{total} reference(s) in {len(touched)} file(s)"
          f"{'' if args.apply else ' — rerun with --apply'}")

    if unmapped_all:
        print(f"\n{len(unmapped_all)} reference(s) point outside every registered "
              "source folder and were left alone:")
        for path, payload in unmapped_all[:10]:
            print(f"  {path.relative_to(ROOT)}: material://{payload}")
        print("  (register the owning source, then rerun)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
