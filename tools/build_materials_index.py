#!/usr/bin/env python3
"""Build a human-browsable CATALOGUE of the materials tree + the source registry.

RETIRED SURFACE (2026-08-03, ADR-006 addendum 4): ``INDEX.html`` is no longer
written. Browsing sources is the interface layer's job — the Obsidian UI's
Source Explorer reads the same facts out of ``generated/manifest.json`` (which
now carries ``url``, ``material_path``, ``roles`` and ``evaluations``), with
search, facets, evaluations and one-click open. Keeping a second, separately
built browser meant two implementations of "how do I find a source". The
generator below still exists and can emit the page again with
``--html`` if the interface ever regresses; ``README.md`` and ``FILES.txt``
remain as the plain-text/grep surfaces.

Emits into ``LearningOS/materials/``:

* ``INDEX.html`` (only with ``--html``) — a self-contained, searchable page
  with TWO switchable views:
    - **Sources** (default): source-first. Each domain lists its registered
      sources directly as clean, collapsed cards (the ``course/practice-extern``
      storage scaffolding is flattened away); expand a card to see its files.
      Online sources and "Missing URLs" (registered, no link yet) sit in their
      own labelled groups, and loose/unregistered files in another.
    - **Files**: the raw local filesystem tree, for seeing exactly what is on
      disk. Support assets (css/js/fonts/images from web mirrors) are hidden
      until you tick "Show supporting files"; archived folders are badged.
  Domains open by default, everything inside collapsed — the landing screen is
  a scannable map, not a wall.

  Search shows a FLAT, relevance-ranked result list with breadcrumbs (it does
  not explode the tree). Space-separated terms are ANDed; matches are
  highlighted; results page in 200 at a time. Keyboard: ``/`` or ``⌘K`` focus,
  ``↑``/``↓`` move, ``⏎`` open (``⌘⏎`` new tab), ``Esc`` clear. Type chips are
  multi-select; "Online only", "Support files" and "Hide archived" are
  independent toggles. Local links are RELATIVE to this file — keep INDEX.html
  in ``materials/`` or the file links break.
* ``README.md`` — a plain-text / grep-able map of the same content.
* ``FILES.txt`` — names-only listing of every UNREGISTERED file (ADR-005), so
  "do I own something on X?" is grep-able without registering archive dumps.

Neither is canonical. They are pure VIEWS over what is physically on disk plus
the registered sources in ``sources/``. Rebuild any time:

    python tools/build_materials_index.py      # or: make materials

Files are never moved, so ``material://`` URIs, the registry and the .flat farm
keep working. No third-party deps beyond PyYAML (already a repo dependency).
"""
from __future__ import annotations

from materials_index import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
