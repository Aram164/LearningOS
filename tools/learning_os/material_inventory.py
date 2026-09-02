"""Canonical byte rendering for the external-material inventory record.

The executable inventory tool and the preserved Job-collapse planner both need
this one serialization rule. Keeping it in a dependency-light Core leaf avoids
making a package module import a command-line entrypoint.
"""

from __future__ import annotations

import yaml

MANIFEST_WIDTH = 100

_HEADER = """\
# Generated — do not hand-edit. Rebuild with:
#     python tools/materials_manifest.py --build
#
# The repository's durable record of the external materials/ tree, which is
# tracked by no Git repository. `make check` uses it to tell "the drive is
# offline" apart from "a referenced file is actually gone", and
# `--against <path>` uses it to prove a restored backup is complete.
#
# Excludes symlinks (.flat/), .DS_Store, the generated catalogue
# (README.md, FILES.txt, INDEX.html) and the per-folder SOURCES.md indexes.
"""


def render_manifest(manifest: dict) -> str:
    """Render the inventory to the one byte form shared by every writer."""
    ordered = dict(manifest)
    files = ordered.get("files")
    if isinstance(files, dict):
        ordered["files"] = dict(sorted(files.items()))
    return _HEADER + yaml.safe_dump(
        ordered,
        sort_keys=False,
        allow_unicode=True,
        width=MANIFEST_WIDTH,
    )
