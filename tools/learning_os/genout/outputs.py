"""Orchestration: build every view, write it out, remove stale files."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath

from ..loader import Repo
from .atlas import build_domain_atlas
from .canvas import build_concept_canvas
from .common import stable_generated_at
from .concepts import (
    build_backlinks,
    build_concept_index,
    build_concept_map,
    build_dependency_report,
)
from .coordination import build_coordination_view, build_health
from .garden import build_nebula
from .library import build_library
from .manifest import build_manifest
from .modules_view import build_module_view
from .reading_room import build_reading_room
from .sources import build_collection_view, build_source_index


def generate_all(repo: Repo, generated_at: str | None = None) -> dict[str, str]:
    """Build all outputs; returns {relative path: content}.

    The default timestamp is the last-commit time (stable_generated_at), so
    repeated generation over the same committed tree is byte-for-byte identical.
    """
    generated_at = generated_at or stable_generated_at(repo.root)
    backlinks = build_backlinks(repo, generated_at)
    manifest = build_manifest(repo, generated_at, backlinks)
    outputs = {
        "manifest.json": json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "backlinks.json": json.dumps(backlinks, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "concept-index.md": build_concept_index(repo, backlinks, generated_at) + "\n",
        "source-index.md": build_source_index(repo, generated_at) + "\n",
        "library.md": build_library(repo, generated_at) + "\n",
        "module-view.md": build_module_view(repo, generated_at) + "\n",
        "coordination-view.md": build_coordination_view(repo, generated_at) + "\n",
        "dependency-report.md": build_dependency_report(repo, backlinks, generated_at) + "\n",
        "concept-map.md": build_concept_map(repo, generated_at) + "\n",
        "domain-atlas.md": build_domain_atlas(repo, generated_at) + "\n",
        "reports/health.md": build_health(repo, generated_at) + "\n",
        "nebula.md": build_nebula(repo, generated_at) + "\n",
        "reading-room.md": build_reading_room(repo, generated_at) + "\n",
        "concept-canvas.canvas": json.dumps(
            build_concept_canvas(repo, generated_at),
            indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    }
    for name in sorted(repo.collections):
        outputs[f"collections/{name}.md"] = build_collection_view(
            repo, name, repo.collections[name], generated_at) + "\n"
    return outputs


_KEEP_NAMES = {".gitkeep", ".DS_Store"}


_KEEP_REPORT_PREFIX = "validation-report"


def write_outputs(repo: Repo, outputs: dict[str, str]) -> None:
    """Write all outputs AND delete stale generated files, so that generated/
    exactly reflects the canonical data (e.g. views of deleted collections
    do not linger)."""
    gen = repo.root / "generated"
    (gen / "reports").mkdir(parents=True, exist_ok=True)
    for rel, content in outputs.items():
        target = gen / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # Never expose a half-written projection to Obsidian. os.replace is an
        # atomic publication step on the same filesystem; manifest.json is
        # published last because it is the versioned interface contract.
        if rel == "manifest.json":
            continue
        tmp = target.with_name(f".{target.name}.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, target)
    if "manifest.json" in outputs:
        target = gen / "manifest.json"
        tmp = target.with_name(".manifest.json.tmp")
        tmp.write_text(outputs["manifest.json"], encoding="utf-8")
        os.replace(tmp, target)
    _remove_stale(gen, outputs)


def _remove_stale(gen: Path, outputs: dict[str, str]) -> None:
    expected = {PurePosixPath(rel) for rel in outputs}
    stale_dirs: list[Path] = []
    for f in sorted(gen.rglob("*")):
        if f.is_dir():
            stale_dirs.append(f)
            continue
        if f.name in _KEEP_NAMES:
            continue
        rel = PurePosixPath(f.relative_to(gen).as_posix())
        if rel.parts and rel.parts[0] == "reports" \
                and f.name.startswith(_KEEP_REPORT_PREFIX):
            continue
        if rel not in expected:
            f.unlink()
    # Prune directories left empty by the deletions (deepest first);
    # rmdir refuses non-empty directories, so this is safe.
    for d in sorted(stale_dirs, reverse=True):
        if d.name == "reports":
            continue
        try:
            d.rmdir()
        except OSError:
            pass
