"""Canonical file selection for derived-state input digests.

Every enumerator mirrors its loader's file selection exactly (glob shape,
missing-dir tolerance, exclusion rules), so an input digest moves if and
only if the loader could observe a different tree. Hashing lives in
``derived.identity``; this module only selects files.

Over-approximation is documented per enumerator where the loader's
selection depends on load outcomes (duplicate ids, failed modules) the
digest cannot see without loading: extra members cost rebuilds, never
stale values.
"""

from __future__ import annotations

from pathlib import Path


def enumerate_note_files(root: Path) -> list[Path]:
    """Mirror load_notes selection: every *.md under knowledge/notes."""
    notes_dir = root / "knowledge" / "notes"
    if not notes_dir.is_dir():
        return []
    return sorted(notes_dir.rglob("*.md"))


def enumerate_registry_files(root: Path, consolidated: str, partition: str) -> list[Path]:
    """Mirror _load_registry selection: consolidated file plus top-level *.yaml."""
    files: list[Path] = []
    single = root / consolidated
    if single.exists():
        files.append(single)
    part_dir = root / partition
    if part_dir.is_dir():
        files.extend(sorted(part_dir.glob("*.yaml")))
    return files


def enumerate_workspace_files(root: Path) -> list[Path]:
    """Mirror load_workspaces CONTEXT discovery.

    Learning-path files are excluded on purpose: they feed
    repo.learning_paths, never the workspace meta/body the shadowed
    builders read.
    """
    files: list[Path] = []
    active = root / "work" / "active"
    if active.is_dir():
        files.extend(sorted(active.glob("*/CONTEXT.md")))
    archived = root / "archive" / "workspaces"
    if archived.is_dir():
        files.extend(sorted(archived.rglob("CONTEXT.md")))
    return files


def enumerate_partitioned_module_files(root: Path) -> list[Path]:
    return sorted((root / "curriculum" / "modules").glob("*/module.yaml"))


def enumerate_module_files(root: Path) -> list[Path]:
    """Mirror load_modules: the always-loaded legacy snapshot plus every
    partitioned module file — exactly the files the loader opens."""
    files: list[Path] = []
    legacy = root / "records" / "modules.yaml"
    if legacy.exists():
        files.append(legacy)
    files.extend(enumerate_partitioned_module_files(root))
    return files


def enumerate_unit_files(root: Path) -> list[Path]:
    """Mirror _load_units: */unit.yaml exactly one level under each units/ dir.

    Over-approximates in one corner: units of modules that failed to load
    are hashed though the loader skips them (extra rebuild, never stale).
    """
    files: list[Path] = []
    for module_file in enumerate_partitioned_module_files(root):
        units_dir = module_file.parent / "units"
        if not units_dir.is_dir():
            continue
        files.extend(sorted(units_dir.glob("*/unit.yaml")))
    return files


def enumerate_study_map_files(root: Path) -> list[Path]:
    """Mirror study-map loading plus the expansion input.

    StudyMap.data is the EXPANDED map, so module source-map.yaml content
    flows into the stages backlinks reads: it is a study-map input.
    """
    files: list[Path] = []
    for unit_file in enumerate_unit_files(root):
        candidate = unit_file.parent / "study-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    for module_file in enumerate_partitioned_module_files(root):
        candidate = module_file.parent / "source-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    return files


def enumerate_study_map_only_files(root: Path) -> list[Path]:
    """Study-map.yaml beside each unit.yaml, without the expansion inputs.

    The manifest graph pins expansion inputs through its source-maps node
    instead, so this narrower set keeps that edge explicit.
    """
    files: list[Path] = []
    for unit_file in enumerate_unit_files(root):
        candidate = unit_file.parent / "study-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    return files


def enumerate_synthesis_files(root: Path) -> list[Path]:
    """Mirror _load_material_synthesis: material-synthesis.yaml per unit dir.

    Same load-outcome over-approximation as enumerate_unit_files.
    """
    files: list[Path] = []
    for unit_file in enumerate_unit_files(root):
        candidate = unit_file.parent / "material-synthesis.yaml"
        if candidate.is_file():
            files.append(candidate)
    return files


def enumerate_source_map_only_files(root: Path) -> list[Path]:
    """Module source-map.yaml per module dir.

    Over-approximates like enumerate_unit_files: maps of modules that
    failed to load are hashed though the loader skips them.
    """
    files: list[Path] = []
    for module_file in enumerate_partitioned_module_files(root):
        candidate = module_file.parent / "source-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    return files


def enumerate_source_files(root: Path) -> list[Path]:
    """Mirror load_sources: sources.yaml or registry partitions."""
    return enumerate_registry_files(root, "sources/sources.yaml", "sources/registry")


def enumerate_collection_files(root: Path) -> list[Path]:
    """Mirror load_collections: one curated list per file."""
    collections_dir = root / "sources" / "collections"
    if not collections_dir.is_dir():
        return []
    return sorted(collections_dir.glob("*.yaml"))


def enumerate_project_files(root: Path) -> list[Path]:
    """Mirror load_projects: project-*.yaml under the project registry."""
    projects_dir = root / "projects" / "registry"
    if not projects_dir.is_dir():
        return []
    return sorted(projects_dir.glob("project-*.yaml"))


def enumerate_program_files(root: Path) -> list[Path]:
    """Mirror load_programs: top-level program records (never quarantine)."""
    programs_dir = root / "curriculum" / "programs"
    if not programs_dir.is_dir():
        return []
    return sorted(programs_dir.glob("*.yaml"))


def enumerate_learning_path_files(root: Path) -> list[Path]:
    """Mirror _load_learning_paths: path-*.yaml beside each CONTEXT.md.

    Over-approximates in one corner: paths of workspaces skipped as
    duplicate ids are hashed though the loader never loads them.
    """
    files: list[Path] = []
    for context in enumerate_workspace_files(root):
        paths_dir = context.parent / "paths"
        if not paths_dir.is_dir():
            continue
        files.extend(sorted(paths_dir.glob("path-*.yaml")))
    return files


def enumerate_garden_files(root: Path) -> list[Path]:
    """Mirror load_garden: idea notes only, with the loader's exclusions."""
    garden_dir = root / "knowledge" / "garden"
    if not garden_dir.is_dir():
        return []
    files: list[Path] = []
    for candidate in sorted(garden_dir.rglob("*.md")):
        rel_parts = candidate.relative_to(garden_dir).parts
        if (candidate.name.startswith((".", "_")) or candidate.stem.lower() == "readme"
                or any(part in {"transcriptions", "syntheses"}
                       or part.startswith((".", "_")) for part in rel_parts[:-1])):
            continue
        files.append(candidate)
    return files


def enumerate_inbox_files(root: Path) -> list[Path]:
    """Mirror build_review_items: every file under work/inbox without a dot part."""
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(
        candidate
        for candidate in inbox.rglob("*")
        if candidate.is_file()
        and not any(part.startswith(".") for part in candidate.relative_to(inbox).parts)
    )


def enumerate_inbox_top_names(root: Path) -> list[str]:
    """Mirror count_inbox_items: top-level inbox entry names, files and dirs alike."""
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(item.name for item in inbox.iterdir() if not item.name.startswith("."))


def enumerate_ai_action_files(root: Path) -> list[Path]:
    """Files the AI projection reads: action contracts, adapter contract,
    request bundles. Garden sidecars are enumerated separately per garden id."""
    files: list[Path] = []
    actions_dir = root / "system" / "contracts" / "ai-actions"
    if actions_dir.is_dir():
        files.extend(sorted(actions_dir.glob("*.yaml")))
    # Always listed: a missing adapters file falls back to defaults, and
    # that absence must digest distinctly from any present content.
    files.append(root / "system" / "contracts" / "ai-adapters.yaml")
    requests_dir = root / "operations" / "ai-actions" / "requests"
    if requests_dir.is_dir():
        files.extend(sorted(requests_dir.glob("*/request.yaml")))
    return files


def enumerate_single_file(root: Path, relative: str) -> list[Path]:
    """One canonical path that digests distinctly when absent.

    For single-file loader inputs (coordination, resume, revisions,
    aliases, relations, thematic groups, topics): the loader treats a
    missing file as empty state, and digest_matching_files gives absence
    its own digest — but only for members it is actually given.
    """
    return [root / relative]
