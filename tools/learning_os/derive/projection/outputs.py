"""Orchestration: build every view, write it out, remove stale files."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path, PurePosixPath

from learning_os.derive.projection.atlas import build_domain_atlas
from learning_os.derive.projection.canvas import build_concept_canvas
from learning_os.derive.projection.common import stable_generated_at
from learning_os.derive.projection.concepts import (
    build_backlinks,
    build_concept_index,
    build_concept_map,
    build_dependency_report,
)
from learning_os.derive.projection.coordination import build_coordination_view, build_health
from learning_os.derive.projection.garden import build_nebula
from learning_os.derive.projection.learner_interpreter import (
    build_learner_interpretations_json,
    build_learner_interpretations_md,
)
from learning_os.derive.projection.learning_runtime import (
    build_learning_requirements_json,
    build_learning_requirements_md,
)
from learning_os.derive.projection.library import build_library
from learning_os.derive.projection.manifest import build_manifest
from learning_os.derive.projection.modules_view import build_module_view
from learning_os.derive.projection.reading_room import build_reading_room
from learning_os.derive.projection.sources import build_collection_view, build_source_index
from learning_os.derive.projection.study_plan import build_study_plan_view
from learning_os.domain.failures import TransactionFailure
from learning_os.domain.snapshot import Repo
from learning_os.store.contracts.tree_contract import generated_keep_directories
from learning_os.store.manifest_identity import (
    IDENTITY_FILENAME,
    build_identity,
    manifest_text,
    observe_inputs,
)


def generate_all(repo: Repo, generated_at: str | None = None, *,
                 backlinks: dict | None = None,
                 manifest: dict | None = None,
                 inputs_before: dict | None = None) -> dict[str, str]:
    """Build all outputs; returns {relative path: content}.

    The default timestamp is the last-commit time (stable_generated_at), so
    repeated generation over the same committed tree is byte-for-byte identical.

    A read that has just rebuilt the projection passes the ``backlinks`` and
    ``manifest`` it built from this same ``repo`` and ``generated_at``, so
    publishing them does not build them twice. Both or neither: they are one
    build, and a pair stamped with another timestamp is refused.

    Non-canonical manifest inputs (materials, operations sidecars, code, clock)
    are observed before building when the caller did not already observe them
    before ``load_repo``; the identity sidecar is emitted only when before and
    after observations still match, so an input moving mid-build forces a
    fresh rebuild instead of stamping a stale build as current (D-19).
    """
    generated_at = generated_at or stable_generated_at(repo.root)
    if (backlinks is None) != (manifest is None):
        raise ValueError("generate_all takes a prebuilt backlinks and manifest together")
    observed_before = inputs_before if inputs_before is not None else observe_inputs(repo.root)
    if manifest is None:
        backlinks = build_backlinks(repo, generated_at)
        manifest = build_manifest(repo, generated_at, backlinks)
    elif (backlinks.get("_generated", {}).get("generated_at") != generated_at
          or manifest.get("_generated", {}).get("generated_at") != generated_at):
        raise ValueError("prebuilt projection was stamped with another generated_at")
    identity = build_identity(repo.root, manifest)
    outputs = {
        # These are machine projections. Keep their complete data and stable
        # key order without paying for indentation on every read/publication.
        "manifest.json": manifest_text(manifest),
        "backlinks.json": json.dumps(backlinks, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n",
        "learning-requirements.json": build_learning_requirements_json(repo, generated_at) + "\n",
        "learning-requirements.md": build_learning_requirements_md(repo),
        "learner-interpretations.json": build_learner_interpretations_json(repo, generated_at) + "\n",
        "learner-interpretations.md": build_learner_interpretations_md(repo),
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
            separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n",
    }
    if all(identity.get(key) == value for key, value in observed_before.items()):
        # Emit the reuse sidecar only when pre-load/pre-build inputs still
        # match post-build state (#83 / D-19).
        outputs[IDENTITY_FILENAME] = json.dumps(
            identity, separators=(",", ":"), sort_keys=True, ensure_ascii=False,
        ) + "\n"
    from learning_os.derive.projection.atlas_boards import build_atlas_boards
    _catalog, board_files = build_atlas_boards(repo, manifest["indexes"], generated_at)
    for rel_path, text in sorted(board_files.items()):
        outputs[rel_path.removeprefix("generated/")] = text
    for name in sorted(repo.collections):
        outputs[f"collections/{name}.md"] = build_collection_view(
            repo, name, repo.collections[name], generated_at) + "\n"
    return outputs


_KEEP_NAMES = {".gitkeep", ".DS_Store"}

#: Sibling producers the publisher must not garbage-collect. The page-text
#: cache, the dossier cache, the derived-state cache, the search index and the
#: outline-section cache live under generated/ (gitignored, disposable) with
#: ``rebuildable: false`` in system/contracts/tree-contract.yaml, owned by
#: their own tools with their own invalidation; a rebuild of the projection
#: must leave them alone.
_KEEP_TOP_DIRS = generated_keep_directories()


_KEEP_REPORT_PREFIX = "validation-report"

#: Pre-4.3 cache sidecars, retired from active use (their families now live
#: in derived-state). Excluded from the reports keep-rule so projection GC
#: reclaims them; `diagnostics_prune --derived-state` reclaims them too.
_OBSOLETE_REPORT_CACHES = frozenset({
    "validation-report.cache.json",
    "validation-report-receipts.cache.json",
})


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
    # Keep one publication path, with the manifest last even if it was the
    # first output constructed. An identical projection needs no replacement.
    for rel in sorted(outputs, key=lambda name: name == "manifest.json"):
        content = outputs[rel].encode("utf-8")
        relative = PurePosixPath(rel)
        target = _checked_output_path(gen, relative, create_parent=True)
        # Never expose a half-written projection to Obsidian. Unique sibling
        # staging files avoid inode collisions, and os.replace is atomic on the
        # same filesystem; manifest.json is published last because it is the
        # versioned interface contract.
        try:
            if target.read_bytes() == content:
                continue
        except FileNotFoundError:
            pass
        except IsADirectoryError:
            _recover_output_dir(gen, relative)
        fd, tmp_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp",
        )
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
            os.replace(tmp, target)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    _remove_stale(gen, outputs)


def _recover_output_dir(gen: Path, relative: PurePosixPath) -> None:
    """Clear an empty directory blocking one output path, else refuse.

    generated/ is disposable: an empty directory where a view belongs is
    residue a rebuild may clear. Anything inside it is not ours to
    delete — refuse with the manual recovery instead of a traceback.
    """
    try:
        (gen / relative).rmdir()
    except OSError as exc:
        raise TransactionFailure(
            f"generated/{relative.as_posix()} is a non-empty directory, not the "
            "published view — move its contents away, delete it, and rebuild "
            "(`make views`)"
        ) from exc


def _refuse_link(path: Path, gen: Path) -> None:
    if path.is_symlink():
        raise TransactionFailure(
            f"generated output path is a symbolic link: {path.relative_to(gen)}"
        )


def _publisher_entries(gen: Path) -> list[Path]:
    """Every path under ``generated/`` the publisher can write or delete.

    A kept sibling cache is checked at its own top-level entry and never
    entered: the publisher neither writes nor removes anything inside it, and
    its producer guards its interior. Entering it cost two full walks per
    publication — about 2 s of a 7.8 s stage-progress write with the page-text
    cache at 72,711 files (measured 2026-09-22).
    """
    entries: list[Path] = []
    for child in sorted(gen.iterdir()):
        entries.append(child)
        if child.name in _KEEP_TOP_DIRS or child.is_symlink() or not child.is_dir():
            continue
        entries.extend(sorted(child.rglob("*")))
    return entries


def _preflight_generated_tree(gen: Path) -> None:
    """Refuse every existing link before publishing even one new output."""
    def walk(directory: Path):
        # Sorting each directory gives the same Path order as sorted(rglob),
        # while scandir avoids Path/stat work for the large kept caches.
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                yield path, entry
                if entry.is_dir(follow_symlinks=False):
                    yield from walk(path)

    for path, entry in walk(gen):
        if entry.is_symlink():
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


def _is_declared_output_temp(rel: PurePosixPath, expected: set[PurePosixPath]) -> bool:
    """Whether ``rel`` is a sibling temp file of a declared output path."""
    name = rel.name
    if not name.startswith(".") or not name.endswith(".tmp"):
        return False
    for exp in expected:
        if exp.parent != rel.parent:
            continue
        if name == f".{exp.name}.tmp" or name.startswith(f".{exp.name}."):
            return True
    return False


def _remove_stale(gen: Path, outputs: dict[str, str]) -> None:
    expected = {PurePosixPath(rel) for rel in outputs}
    stale_dirs: list[Path] = []
    for f in _publisher_entries(gen):
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
        if _is_declared_output_temp(rel, expected):
            continue
        if rel.parts and rel.parts[0] == "reports" \
                and f.name.startswith(_KEEP_REPORT_PREFIX) \
                and f.name not in _OBSOLETE_REPORT_CACHES:
            continue
        if rel.parts and rel.parts[0] in _KEEP_TOP_DIRS:
            continue
        if rel not in expected:
            f.unlink()
    # Prune directories left empty by the deletions (deepest first);
    # rmdir refuses non-empty directories, so this is safe.
    for d in sorted(stale_dirs, reverse=True):
        if d.name == "reports":
            continue
        if d.relative_to(gen).parts[0] in _KEEP_TOP_DIRS:
            continue
        try:
            d.rmdir()
        except OSError:
            pass
