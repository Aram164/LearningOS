"""Orchestration: build every view, write it out, remove stale files."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath

from ..errors import TransactionFailure
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
from .study_plan import build_study_plan_view


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
        "study-plans.md": build_study_plan_view(repo, generated_at) + "\n",
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
    if gen.is_symlink():
        raise TransactionFailure("generated output root may not be a symbolic link")
    gen.mkdir(parents=True, exist_ok=True)
    try:
        gen.resolve().relative_to(repo.root.resolve())
    except ValueError as exc:
        raise TransactionFailure("generated output root escapes the repository") from exc
    _preflight_generated_tree(gen)
    _checked_output_path(gen, PurePosixPath("reports/.keep"), create_parent=True)
    for rel, content in outputs.items():
        relative = PurePosixPath(rel)
        target = _checked_output_path(gen, relative, create_parent=True)
        # Never expose a half-written projection to Obsidian. os.replace is an
        # atomic publication step on the same filesystem; manifest.json is
        # published last because it is the versioned interface contract.
        if rel == "manifest.json":
            continue
        tmp = target.with_name(f".{target.name}.tmp")
        _refuse_link(tmp, gen)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, target)
    if "manifest.json" in outputs:
        target = _checked_output_path(
            gen, PurePosixPath("manifest.json"), create_parent=True
        )
        tmp = target.with_name(".manifest.json.tmp")
        _refuse_link(tmp, gen)
        tmp.write_text(outputs["manifest.json"], encoding="utf-8")
        os.replace(tmp, target)
    _remove_stale(gen, outputs)


def _refuse_link(path: Path, gen: Path) -> None:
    if path.is_symlink():
        raise TransactionFailure(
            f"generated output path is a symbolic link: {path.relative_to(gen)}"
        )


def _preflight_generated_tree(gen: Path) -> None:
    """Refuse every existing link before publishing even one new output."""
    for path in sorted(gen.rglob("*")):
        if path.is_symlink():
            raise TransactionFailure(
                "generated output path is a symbolic link: "
                f"{path.relative_to(gen)}"
            )


def _checked_output_path(
    gen: Path,
    relative: PurePosixPath,
    *,
    create_parent: bool,
) -> Path:
    if relative.is_absolute() or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise TransactionFailure(f"unsafe generated output path: {relative}")
    current = gen
    for part in relative.parts[:-1]:
        current = current / part
        _refuse_link(current, gen)
        if current.exists() and not current.is_dir():
            raise TransactionFailure(
                f"generated output parent is not a directory: {current.relative_to(gen)}"
            )
        if create_parent:
            current.mkdir(exist_ok=True)
    target = current / relative.name
    _refuse_link(target, gen)
    try:
        target.parent.resolve().relative_to(gen.resolve())
    except ValueError as exc:
        raise TransactionFailure(f"generated output escapes root: {relative}") from exc
    return target


def _remove_stale(gen: Path, outputs: dict[str, str]) -> None:
    expected = {PurePosixPath(rel) for rel in outputs}
    stale_dirs: list[Path] = []
    for f in sorted(gen.rglob("*")):
        if f.is_symlink():
            rel = PurePosixPath(f.relative_to(gen).as_posix())
            raise TransactionFailure(
                f"generated output path is a symbolic link: {rel}"
            )
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
