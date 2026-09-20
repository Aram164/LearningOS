"""Incremental manifest graph over derived state (proof phase).

Every semantic stage of ``build_manifest()`` runs here as a derived node
with declared file inputs and dependency edges; ``build_manifest()``
itself stays production-authoritative. The shadow entry point evaluates
this graph and compares exact bytes against the legacy path.

Builder discipline: a builder closes over the loaded repo and calls the
exact legacy projector, so legacy and shadow can only differ when the
declared inputs fail to pin a read. Dependency outputs pin the raw reads
they cover (a projected record list pins the registry rows it projects
1:1); every other read is covered by a direct input digest. Over-
invalidation is acceptable; under-invalidation is a bug.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ..ai_actions.projection import project_ai_actions
from ..contracts.manifest_contract import declared_version, enforce, load_contract
from ..derived.engine import (
    BuildContext,
    Staging,
    commit_staging,
    evaluate,
    evaluate_many,
)
from ..derived.identity import (
    canonical_snapshot_digest,
    digest_bytes,
    digest_matching_files,
    validator_runtime_digest,
)
from ..derived.model import DERIVED_SUBSTRATE_FILES, DerivedError, NodeSpec
from ..derived.store import canonical_bytes, store_node
from ..errors import TransactionFailure
from ..garden import garden_id, project_garden_entries
from ..githistory import GitSnapshot, fresh_git_snapshot
from ..loader import Repo, load_repo
from ..materials_resolution import MATERIAL_SCHEME, MATERIAL_SUFFIX_TOKEN
from ..materials_resolution import leading_material_locator as _leading_locator
from ..materials_resolution import material_location as _material_location
from ..materials_resolution import material_uri_authority as _uri_authority
from ..materials_resolution import resolve_route_material_files as _resolve_route_files
from ..materials_resolution import safe_material_locator as _safe_locator
from ..materials_resolution import single_file_material as _single_file_material
from ..pathing import PathBoundaryError, read_text_inside, resolved_inside
from .common import _git_state, stable_generated_at
from .concepts import build_backlinks
from .coordination import adoption_counts
from .derived_generation import BACKLINKS_SEMANTIC_ID, generation_input_digests, generation_registry
from .derived_inputs import (
    enumerate_ai_action_files,
    enumerate_collection_files,
    enumerate_garden_files,
    enumerate_inbox_files,
    enumerate_inbox_top_names,
    enumerate_learning_path_files,
    enumerate_note_files,
    enumerate_program_files,
    enumerate_project_files,
    enumerate_single_file,
    enumerate_source_files,
    enumerate_source_map_only_files,
    enumerate_study_map_only_files,
    enumerate_synthesis_files,
)
from .manifest import (
    _projected_revision,
    assemble_manifest_semantic_payload,
    build_manifest,
    build_manifest_relations,
    build_manifest_semesters,
    build_manifest_stages,
    count_inbox_items,
    derive_manifest_collections,
    load_manifest_revisions,
    publish_manifest_metadata,
    require_publishable_manifest_repo,
    splice_manifest_records,
)
from .modules_view import _academic_deadlines
from .projection import (
    build_counts,
    build_indexes,
    build_module_concept_edges,
    build_progress,
    project_collections,
    project_concepts,
    project_coordination,
    project_learning_paths,
    project_module_source_maps,
    project_modules,
    project_notes,
    project_programs,
    project_project_aliases,
    project_project_relationships,
    project_projects,
    project_sources,
    project_study_maps,
    project_thematic_groups,
    project_topics,
    project_unit_material_syntheses,
    project_units,
    project_workspaces,
    unit_to_project_ids,
)
from .review import build_review_items

if TYPE_CHECKING:
    from ..derived.engine import Registry, TraceEvent

NOTES_ID = "manifest.notes"
CONCEPTS_ID = "manifest.concepts"
SOURCES_ID = "manifest.sources"
PROJECTS_ID = "manifest.projects"
PROJECT_RELATIONSHIPS_ID = "manifest.project-relationships"
PROJECT_ALIASES_ID = "manifest.project-aliases"
MODULES_ID = "manifest.modules"
COLLECTIONS_ID = "manifest.collections"
WORKSPACES_ID = "manifest.workspaces"
LEARNING_PATHS_ID = "manifest.learning-paths"
PROGRAMS_ID = "manifest.programs"
UNITS_ID = "manifest.units"
STUDY_MAPS_ID = "manifest.study-maps"
SOURCE_MAPS_ID = "manifest.source-maps"
SYNTHSES_ID = "manifest.unit-material-syntheses"
COORDINATION_ID = "manifest.coordination"
THEMATIC_GROUPS_ID = "manifest.thematic-groups"
TOPICS_ID = "manifest.topics"
UNIT_PROJECT_EDGES_ID = "manifest.unit-project-edges"
REVISIONS_ID = "manifest.revisions"
RELATIONS_ID = "manifest.relations"
RECORDS_ID = "manifest.records"
TYPED_COLLECTIONS_ID = "manifest.typed-collections"
STAGES_ID = "manifest.stages"
SEMESTERS_ID = "manifest.semesters"
EDGES_ID = "manifest.module-concept-edges"
INDEXES_ID = "manifest.indexes"
PROGRESS_ID = "manifest.progress"
COUNTS_ID = "manifest.counts"
REVIEW_ITEMS_ID = "manifest.review-items"
GARDEN_ID = "manifest.garden"
AI_ACTIONS_ID = "manifest.ai-actions"
DEADLINES_ID = "manifest.academic-deadlines"
SEMANTIC_PAYLOAD_ID = "manifest.semantic-payload"
VALIDATION_PROOF_ID = "manifest.validation-proof"

#: Bumped when a manifest node changes shape (inputs, dependencies, or
#: value structure) independently of its producer files.
MANIFEST_NODE_VERSION = 1

#: Validation semantics version: the proof node's spec version. Bump when
#: the meaning of "valid" changes independently of the contract bytes or
#: the validator code.
MANIFEST_VALIDATION_VERSION = 1

_SELF = ("tools/learning_os/genout/manifest_derived.py",)
_MANIFEST = ("tools/learning_os/genout/manifest.py",)
_LOADING_BASE = (
    "tools/learning_os/loading/model.py",
    "tools/learning_os/loading/yamlio.py",
)
_MATERIALS = (
    "tools/learning_os/genout/materials.py",
    "tools/learning_os/materials_resolution.py",
)
_ROUTES = (
    "tools/learning_os/routes.py",
    "tools/learning_os/route_identity.py",
)
_GIT_AND_PATHING = (
    "tools/learning_os/githistory.py",
    "tools/learning_os/pathing.py",
)


def _node(version_producers: tuple[str, ...]) -> tuple[str, ...]:
    """Producer list: this graph, the given files, the derived substrate."""
    return (*_SELF, *version_producers, *DERIVED_SUBSTRATE_FILES)


def _fresh_git_table(root: Path) -> dict[str, str]:
    """Whole-tree last-commit dates, read UNCACHED, or empty when unreadable.

    Every digest default reads fresh (G1a): sharing one cached walk across
    a transaction's observations would let a concurrent commit hide behind
    the first lookup. A broken history still falls back to empty — legacy
    raises in the builder either way, so the fallback can only accompany
    an identical legacy failure.
    """
    table = fresh_git_snapshot(root).table
    return dict(table) if table is not None else {}


def notes_git_digest(root: Path, git_table: dict[str, str] | None = None) -> str:
    """Per-note last-commit dates for the adoption drift check.

    Covers every note file, though only reviewed notes are read: a commit
    touching an unreviewed note costs one counts rebuild, never a wrong hit.
    ``None`` reads the table fresh; a transaction passes its attempt table.
    """
    table = git_table if git_table is not None else _fresh_git_table(root)
    digest = hashlib.sha256()
    for path in enumerate_note_files(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(table.get(rel, "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _working_note_line(
    root: Path, site: str, ref: Any, git_table: dict[str, str]
) -> str | None:
    """One digest line for a referenced working-note file.

    Mirrors the legacy read shape: resolve inside the root, read with
    replacement, look up the git date only for a successfully read file.
    An unreadable reference digests distinctly and carries no git date,
    exactly as the legacy fallback publishes ("", None).
    """
    if not ref:
        return None
    note_file = root / str(ref)
    try:
        resolved_inside(root, note_file)
        text = read_text_inside(root, note_file, errors="replace")
        rel = note_file.relative_to(root).as_posix()
    except (OSError, PathBoundaryError, ValueError):
        return f"{site}\0{ref}\0<unreadable>\0"
    content = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{site}\0{ref}\0{content}\0{git_table.get(rel, '')}"


def working_notes_digest(
    root: Path, repo: Repo, git_table: dict[str, str] | None = None
) -> str:
    """Content plus git dates for every working note units and stages inline.

    Sites are stable across evaluations; the unit/study-map/learning-path
    content digests pin the references themselves, so absent references
    contribute no line. ``None`` reads the table fresh; a transaction
    passes its attempt table.
    """
    table = git_table if git_table is not None else _fresh_git_table(root)
    lines: list[str] = []
    for unit in sorted(repo.units.values(), key=lambda item: item.id):
        line = _working_note_line(
            root, f"unit:{unit.id}", unit.data.get("working_note"), table
        )
        if line is not None:
            lines.append(line)
    for study_map in sorted(repo.study_maps.values(), key=lambda item: item.id):
        for index, stage in enumerate(study_map.data.get("stages", []) or []):
            if not isinstance(stage, dict):
                continue
            line = _working_note_line(
                root,
                f"study-map:{study_map.id}:{index}",
                stage.get("working_note"),
                table,
            )
            if line is not None:
                lines.append(line)
    for path in sorted(repo.learning_paths.values(), key=lambda item: item.id):
        for index, stage in enumerate(path.data.get("stages", []) or []):
            if not isinstance(stage, dict):
                continue
            line = _working_note_line(
                root,
                f"learning-path:{path.id}:{index}",
                stage.get("notes_path"),
                table,
            )
            if line is not None:
                lines.append(line)
    digest = hashlib.sha256()
    for line in sorted(lines):
        digest.update(line.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _stage_resources(data: dict) -> list[dict]:
    resources: list[dict] = []
    for stage in data.get("stages", []) or []:
        if not isinstance(stage, dict):
            continue
        rows = stage.get("resources")
        if isinstance(rows, list):
            resources.extend(row for row in rows if isinstance(row, dict))
    return resources


def _candidate_resource_uris(resource: dict, sources: dict) -> set[str]:
    """Every material:// URI project_material_resource could construct here.

    Mirrors the construction branches only — never the existence gating,
    which the digest pins separately. An extra candidate costs a rebuild
    when its file moves; a missing one would be under-invalidation.
    """
    if resource.get("material_path"):
        return set()
    vault_path = resource.get("vault_path")
    if isinstance(vault_path, str) and vault_path:
        if vault_path.startswith(MATERIAL_SCHEME) and _uri_authority(vault_path):
            return {vault_path}
        return set()
    locator = _safe_locator(resource.get("locator"))
    source = sources.get(resource.get("source_id"))
    source_material = source.get("material") if isinstance(source, dict) else None
    authority = _uri_authority(source_material)
    if locator is None:
        locator = _leading_locator(resource.get("locator"))
    if locator and authority:
        return {f"material://{authority}/{locator}"}
    if authority:
        single = _single_file_material(source_material)
        if single is not None:
            return {single}
    return set()


def _candidate_multi_uris(locator: Any, source_material: Any) -> set[str]:
    """Semicolon-bound multi-file candidates, mirroring the strict branch.

    When the guards fail the resolver returns [] regardless of files on
    disk, so no digest line is needed — the mirror returns empty too.
    """
    authority = _uri_authority(source_material)
    if not isinstance(locator, str) or ";" not in locator or not authority:
        return set()
    candidates: list[str] = []
    for part in locator.split(";"):
        matches = list(MATERIAL_SUFFIX_TOKEN.finditer(part))
        if len(matches) != 1:
            return set()
        candidate = _safe_locator(part[: matches[0].end()].strip())
        if candidate is None:
            return set()
        candidates.append(candidate)
    if len(candidates) < 2 or len(candidates) != len(set(candidates)):
        return set()
    return {f"material://{authority}/{item}" for item in candidates}


def materials_digest(root: Path, repo: Repo) -> str:
    """Resolution state for every referenced material file.

    Each line pins the constructed URI, its resolved path, its existence,
    and — for a plain file — its bytes. Unreferenced farm files are
    excluded on purpose: the 2GB materials tree is never walked. The
    .flat selection leads, since it flips the resolution root.
    """
    materials = repo.learningos_root / "materials"
    flat = materials / ".flat"
    selection = "flat" if not flat.is_symlink() and flat.is_dir() else "base"
    uris: set[str] = set()
    for sid in sorted(repo.sources):
        ref = repo.sources[sid].get("material")
        if _uri_authority(ref) is not None:
            uris.add(str(ref))
    for mid in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[mid]
        for entry in source_map.get("sources", []) or []:
            if not isinstance(entry, dict):
                continue
            entry_source_id = entry.get("source_id")
            entry_source = repo.sources.get(entry_source_id)
            entry_material = (
                entry_source.get("material")
                if isinstance(entry_source, dict)
                else None
            )
            for route in entry.get("unit_routes", []) or []:
                if not isinstance(route, dict):
                    continue
                for resolved in _resolve_route_files(repo, route):
                    uris.add(resolved.material_uri)
                uris |= _candidate_resource_uris(
                    {**route, "source_id": entry_source_id}, repo.sources
                )
                uris |= _candidate_multi_uris(route.get("locator"), entry_material)
    for study_map in sorted(repo.study_maps.values(), key=lambda item: item.id):
        for resource in _stage_resources(study_map.data):
            uris |= _candidate_resource_uris(resource, repo.sources)
    for path in sorted(repo.learning_paths.values(), key=lambda item: item.id):
        for resource in _stage_resources(path.data):
            uris |= _candidate_resource_uris(resource, repo.sources)
    lines = [f"resolution-root\0{selection}"]
    for uri in sorted(uris):
        location = _material_location(repo, uri)
        rel = location.get("material_path")
        exists = location.get("material_exists") is True
        token = "<absent>"
        if exists and isinstance(rel, str):
            target = repo.learningos_root / rel
            if target.is_file() and not target.is_symlink():
                try:
                    token = hashlib.sha256(target.read_bytes()).hexdigest()
                except OSError:
                    token = "<unreadable>"
            else:
                token = "<not-file>"
        lines.append(f"{uri}\0{rel if isinstance(rel, str) else '<none>'}\0{int(exists)}\0{token}")
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def study_map_presence_digest(root: Path) -> str:
    """Which units carry a study map — presence only, never content."""
    relatives = sorted(
        path.relative_to(root).as_posix()
        for path in enumerate_study_map_only_files(root)
    )
    digest = hashlib.sha256()
    for rel in relatives:
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def inbox_digest(root: Path) -> str:
    """Inbox file contents plus top-level entry names.

    Review rows read file bytes recursively; the inbox count also sees
    top-level directories, which a file walk alone would miss.
    """
    files = digest_matching_files(root, enumerate_inbox_files(root))
    names = "\0".join(enumerate_inbox_top_names(root))
    return digest_bytes(f"{files}\0{names}".encode())


def garden_digest(root: Path, repo: Repo) -> str:
    """Garden idea files plus each row's optional AI sidecar, if present."""
    garden_root = root / "knowledge" / "garden"
    sidecars = [
        root / "operations" / "ai-actions" / "garden-state"
        / f"{garden_id(garden_root, note.path)}.yaml"
        for note in repo.garden_notes
    ]
    return digest_matching_files(
        root, [*enumerate_garden_files(root), *sidecars]
    )


def today_digest() -> str:
    """Today's date: academic availability is actionable state, not history."""
    return datetime.date.today().isoformat()


def contract_closure_digest(root: Path) -> str:
    """Every file enforce() can read: the contract, its schema, the registry.

    Mirrors the validator's selection exactly: ``manifest-contract.yaml``
    always; the schema at the contract's declared schema_path when that
    path resolves inside the root (mirroring _schema_path's guards — an
    unresolvable declaration fails validation regardless of schema
    bytes); every top-level ``*.schema.json`` under system/schema,
    which schema_registry loads unconditionally.
    """
    contract_file = root / "system" / "contracts" / "manifest-contract.yaml"
    files = [contract_file]
    try:
        doc = yaml.safe_load(contract_file.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        doc = {}
    relative = doc.get("schema_path") if isinstance(doc, dict) else None
    if isinstance(relative, str) and relative:
        candidate = Path(relative)
        if not candidate.is_absolute() and ".." not in candidate.parts:
            files.append(root / relative)
    schema_dir = root / "system" / "schema"
    if schema_dir.is_dir():
        files.extend(sorted(schema_dir.glob("*.schema.json")))
    return digest_matching_files(root, files)


def manifest_input_digests(
    root: Path, repo: Repo, git_table: dict[str, str] | None = None
) -> dict[str, str]:
    """One content digest per manifest input domain.

    Complements ``generation_input_digests`` (the gen.* groups are reused
    as-is); evaluation merges both maps. The git table is read once here
    and shared by the notes and working-note digests — a transaction
    passes its attempt table, ``None`` reads fresh.
    """
    table = git_table if git_table is not None else _fresh_git_table(root)
    return {
        "manifest.sources": digest_matching_files(root, enumerate_source_files(root)),
        "manifest.collections": digest_matching_files(
            root, enumerate_collection_files(root)
        ),
        "manifest.projects": digest_matching_files(root, enumerate_project_files(root)),
        "manifest.project_relations": digest_matching_files(
            root, enumerate_single_file(root, "projects/relations/project-relations.yaml")
        ),
        "manifest.project_aliases": digest_matching_files(
            root, enumerate_single_file(root, "projects/aliases.yaml")
        ),
        "manifest.programs": digest_matching_files(root, enumerate_program_files(root)),
        "manifest.thematic": digest_matching_files(
            root, enumerate_single_file(root, "curriculum/thematic-groups.yaml")
        ),
        "manifest.topics": digest_matching_files(
            root, enumerate_single_file(root, "sources/topics.yaml")
        ),
        "manifest.learning_paths": digest_matching_files(
            root, enumerate_learning_path_files(root)
        ),
        "manifest.coordination": digest_matching_files(
            root, enumerate_single_file(root, "work/COORDINATION.md")
        ),
        "manifest.revisions": digest_matching_files(
            root, enumerate_single_file(root, "operations/transactions/revisions.yaml")
        ),
        "manifest.resume": digest_matching_files(
            root, enumerate_single_file(root, "curriculum/resume.yaml")
        ),
        "manifest.syntheses": digest_matching_files(
            root, enumerate_synthesis_files(root)
        ),
        "manifest.study_map_files": digest_matching_files(
            root, enumerate_study_map_only_files(root)
        ),
        "manifest.study_map_presence": study_map_presence_digest(root),
        "manifest.source_map_files": digest_matching_files(
            root, enumerate_source_map_only_files(root)
        ),
        "manifest.inbox": inbox_digest(root),
        "manifest.garden": garden_digest(root, repo),
        "manifest.ai_files": digest_matching_files(
            root, enumerate_ai_action_files(root)
        ),
        "manifest.working_notes": working_notes_digest(root, repo, table),
        "manifest.notes_git": notes_git_digest(root, table),
        "manifest.materials": materials_digest(root, repo),
        "manifest.today": today_digest(),
        # The contract closure is an input even though no semantic node
        # names it: the snapshot transaction compares the whole map
        # before and after evaluation, which proves the validator's
        # reads stayed stable across enforce() (F2). The proof node
        # takes the same pre-evaluation value as its direct input.
        "manifest.contract_closure": contract_closure_digest(root),
    }


def _proj(*names: str) -> tuple[str, ...]:
    return tuple(f"tools/learning_os/genout/projection/{name}.py" for name in names)


def _load(*names: str) -> tuple[str, ...]:
    return tuple(f"tools/learning_os/loading/{name}.py" for name in names)


_COMMON = ("tools/learning_os/genout/common.py",)
_REVISIONS = ("tools/learning_os/revisions.py",)

#: Record-group name (RECORD_SPLICE_ORDER) -> node producing it.
_RECORD_GROUP_NODES = {
    "notes": NOTES_ID,
    "concepts": CONCEPTS_ID,
    "sources": SOURCES_ID,
    "projects": PROJECTS_ID,
    "project_relationships": PROJECT_RELATIONSHIPS_ID,
    "project_aliases": PROJECT_ALIASES_ID,
    "modules": MODULES_ID,
    "collections": COLLECTIONS_ID,
    "workspaces": WORKSPACES_ID,
    "learning_paths": LEARNING_PATHS_ID,
    "programs": PROGRAMS_ID,
    "units": UNITS_ID,
    "study_maps": STUDY_MAPS_ID,
    "source_maps": SOURCE_MAPS_ID,
    "unit_material_syntheses": SYNTHSES_ID,
    "coordination": COORDINATION_ID,
}


def manifest_registry(repo: Repo, git: GitSnapshot | None = None) -> Registry:
    """Node specs (static) with builders closed over the loaded repo.

    The repo is execution data; reuse is proven by the declared input
    digests and dependency outputs, never by object identity. Builders
    call the exact legacy projectors — see the module docstring for the
    pinning discipline. A snapshot transaction passes its attempt snapshot
    so git-reading builders observe the table the input digests pinned
    (G1a); ``None`` keeps the legacy live read. A ``None`` table inside a
    passed snapshot (unreadable history) likewise falls back to the live
    read, reproducing the legacy failure rather than inventing values.
    """
    git_table = git.table if git is not None else None

    def _revision(ctx: BuildContext) -> Callable[[str, dict | None], int]:
        return partial(_projected_revision, ctx.dependencies[REVISIONS_ID].value)

    def build_notes(_ctx: BuildContext) -> list[dict]:
        return project_notes(repo)

    def build_concepts(_ctx: BuildContext) -> list[dict]:
        return project_concepts(repo)

    def build_sources(ctx: BuildContext) -> list[dict]:
        return project_sources(repo, _revision(ctx))

    def build_projects(ctx: BuildContext) -> list[dict]:
        return project_projects(repo, _revision(ctx))

    def build_project_relationships(_ctx: BuildContext) -> list[dict]:
        return project_project_relationships(repo)

    def build_project_aliases(_ctx: BuildContext) -> list[dict]:
        return project_project_aliases(repo)

    def build_modules(ctx: BuildContext) -> list[dict]:
        return project_modules(repo, _revision(ctx))

    def build_collections(ctx: BuildContext) -> list[dict]:
        return project_collections(repo, _revision(ctx))

    def build_workspaces(ctx: BuildContext) -> list[dict]:
        return project_workspaces(repo, _revision(ctx))

    def build_learning_paths(ctx: BuildContext) -> list[dict]:
        return project_learning_paths(repo, _revision(ctx), git_table)

    def build_programs(ctx: BuildContext) -> list[dict]:
        return project_programs(repo, _revision(ctx))

    def build_units(ctx: BuildContext) -> list[dict]:
        return project_units(
            repo, _revision(ctx), ctx.dependencies[UNIT_PROJECT_EDGES_ID].value,
            git_table,
        )

    def build_study_maps(ctx: BuildContext) -> list[dict]:
        return project_study_maps(
            repo, _revision(ctx), ctx.dependencies[SOURCE_MAPS_ID].value,
            git_table,
        )

    def build_source_maps(ctx: BuildContext) -> list[dict]:
        return project_module_source_maps(repo, _revision(ctx))

    def build_syntheses(_ctx: BuildContext) -> list[dict]:
        return project_unit_material_syntheses(repo)

    def build_coordination(_ctx: BuildContext) -> list[dict]:
        return project_coordination(repo)

    def build_thematic_groups(_ctx: BuildContext) -> list[dict]:
        return project_thematic_groups(repo)

    def build_topics(_ctx: BuildContext) -> list[dict]:
        return project_topics(repo)

    def build_unit_project_edges(_ctx: BuildContext) -> dict[str, list[str]]:
        return unit_to_project_ids(repo)

    def build_revisions(_ctx: BuildContext) -> dict[str, int]:
        return load_manifest_revisions(repo.root)

    def build_relations(_ctx: BuildContext) -> list[dict]:
        return build_manifest_relations(repo)

    def build_records(ctx: BuildContext) -> list[dict]:
        return splice_manifest_records({
            name: ctx.dependencies[node].value
            for name, node in _RECORD_GROUP_NODES.items()
        })

    def build_typed_collections(ctx: BuildContext) -> dict[str, list]:
        return derive_manifest_collections(ctx.dependencies[RECORDS_ID].value)

    def build_stages(ctx: BuildContext) -> list[dict]:
        return build_manifest_stages(
            ctx.dependencies[TYPED_COLLECTIONS_ID].value["study_maps"]
        )

    def build_semesters(ctx: BuildContext) -> list[dict]:
        return build_manifest_semesters(
            ctx.dependencies[TYPED_COLLECTIONS_ID].value["programs"]
        )

    def build_edges(ctx: BuildContext) -> list[dict]:
        collections = ctx.dependencies[TYPED_COLLECTIONS_ID].value
        return build_module_concept_edges(
            modules=collections["modules"],
            units=collections["units"],
            stages=ctx.dependencies[STAGES_ID].value,
            concepts=repo.concepts,
        )

    def build_indexes_node(ctx: BuildContext) -> dict:
        collections = ctx.dependencies[TYPED_COLLECTIONS_ID].value
        return build_indexes(
            repo,
            ctx.dependencies[RECORDS_ID].value,
            modules_v2=collections["modules"],
            units_v2=collections["units"],
            study_maps_v2=collections["study_maps"],
            source_maps_v2=collections["module_source_maps"],
            projects_v2=collections["projects"],
            project_relationships_v2=collections["project_relationships"],
            unit_material_syntheses_v2=ctx.dependencies[SYNTHSES_ID].value,
            module_concept_edges=ctx.dependencies[EDGES_ID].value,
        )

    def build_progress_node(ctx: BuildContext) -> dict:
        collections = ctx.dependencies[TYPED_COLLECTIONS_ID].value
        return build_progress(
            collections["modules"], collections["units"], collections["study_maps"]
        )

    def build_counts_node(ctx: BuildContext) -> dict:
        collections = ctx.dependencies[TYPED_COLLECTIONS_ID].value
        return build_counts(
            repo,
            thematic_groups=ctx.dependencies[THEMATIC_GROUPS_ID].value,
            topics_v2=ctx.dependencies[TOPICS_ID].value,
            topic_packs_v2=collections["topic_packs"],
            projects_v2=collections["projects"],
            programs_v2=collections["programs"],
            modules_v2=collections["modules"],
            units_v2=collections["units"],
            stages_v2=ctx.dependencies[STAGES_ID].value,
            inbox_items=count_inbox_items(repo.root),
            garden_entries=ctx.dependencies[GARDEN_ID].value,
            ai_requests=ctx.dependencies[AI_ACTIONS_ID].value["ai_actions"]["requests"],
            adoption=adoption_counts(repo, git_table),
        )

    def build_review_items_node(ctx: BuildContext) -> list[dict]:
        collections = ctx.dependencies[TYPED_COLLECTIONS_ID].value
        return build_review_items(
            repo, collections["units"], collections["study_maps"]
        )

    def build_garden(_ctx: BuildContext) -> list[dict]:
        return project_garden_entries(repo)

    def build_ai_actions(_ctx: BuildContext) -> dict:
        return project_ai_actions(repo)

    def build_deadlines(_ctx: BuildContext) -> list[dict]:
        return _academic_deadlines(repo)

    def build_semantic_payload(ctx: BuildContext) -> dict:
        deps = ctx.dependencies
        return assemble_manifest_semantic_payload(
            repo,
            deps[BACKLINKS_SEMANTIC_ID].value,
            records=deps[RECORDS_ID].value,
            relations=deps[RELATIONS_ID].value,
            thematic_groups=deps[THEMATIC_GROUPS_ID].value,
            topics_v2=deps[TOPICS_ID].value,
            artifact_revisions=deps[REVISIONS_ID].value,
            collections=deps[TYPED_COLLECTIONS_ID].value,
            stages_v2=deps[STAGES_ID].value,
            module_concept_edges=deps[EDGES_ID].value,
            semesters_v2=deps[SEMESTERS_ID].value,
            unit_material_syntheses_v2=deps[SYNTHSES_ID].value,
            garden_entries=deps[GARDEN_ID].value,
            review_items=deps[REVIEW_ITEMS_ID].value,
            ai_projection=deps[AI_ACTIONS_ID].value,
            indexes=deps[INDEXES_ID].value,
            progress=deps[PROGRESS_ID].value,
            counts=deps[COUNTS_ID].value,
            project_aliases=dict(sorted(repo.project_aliases.items())),
            resume_pointer=dict(repo.resume_pointer or {}),
            academic_deadlines=deps[DEADLINES_ID].value,
        )

    version = MANIFEST_NODE_VERSION
    return {
        NOTES_ID: (
            NodeSpec(
                id=NOTES_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_knowledge"), *_COMMON,
                     *_load("knowledge"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.notes",),
            ),
            build_notes,
        ),
        CONCEPTS_ID: (
            NodeSpec(
                id=CONCEPTS_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_knowledge"),
                     *_load("knowledge"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.concepts",),
            ),
            build_concepts,
        ),
        SOURCES_ID: (
            NodeSpec(
                id=SOURCES_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_library", "grouping"), *_MATERIALS,
                     *_load("library", "curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.sources", "manifest.materials"),
                dependencies=(REVISIONS_ID, THEMATIC_GROUPS_ID),
            ),
            build_sources,
        ),
        PROJECTS_ID: (
            NodeSpec(
                id=PROJECTS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_projects"),
                     *_load("projects"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.projects",),
                dependencies=(REVISIONS_ID, PROJECT_RELATIONSHIPS_ID),
            ),
            build_projects,
        ),
        PROJECT_RELATIONSHIPS_ID: (
            NodeSpec(
                id=PROJECT_RELATIONSHIPS_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_projects"),
                     *_load("projects"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.project_relations",),
            ),
            build_project_relationships,
        ),
        PROJECT_ALIASES_ID: (
            NodeSpec(
                id=PROJECT_ALIASES_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_projects"),
                     *_load("projects"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.project_aliases",),
            ),
            build_project_aliases,
        ),
        MODULES_ID: (
            NodeSpec(
                id=MODULES_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_curriculum", "grouping", "lifecycle"),
                     *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.modules",),
                dependencies=(REVISIONS_ID, THEMATIC_GROUPS_ID, UNITS_ID),
            ),
            build_modules,
        ),
        COLLECTIONS_ID: (
            NodeSpec(
                id=COLLECTIONS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_library", "grouping", "atlas"),
                     *_load("library", "curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.collections",),
                dependencies=(REVISIONS_ID, THEMATIC_GROUPS_ID),
            ),
            build_collections,
        ),
        WORKSPACES_ID: (
            NodeSpec(
                id=WORKSPACES_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_work"), *_COMMON,
                     *_load("work"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.workspaces",),
                dependencies=(REVISIONS_ID,),
            ),
            build_workspaces,
        ),
        LEARNING_PATHS_ID: (
            NodeSpec(
                id=LEARNING_PATHS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_work", "stages"), *_MATERIALS,
                     *_load("work"), *_LOADING_BASE, *_GIT_AND_PATHING)
                ),
                direct_inputs=(
                    "manifest.learning_paths",
                    "manifest.working_notes",
                    "manifest.materials",
                ),
                dependencies=(REVISIONS_ID, SOURCES_ID),
            ),
            build_learning_paths,
        ),
        PROGRAMS_ID: (
            NodeSpec(
                id=PROGRAMS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_curriculum"),
                     *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.programs",),
                dependencies=(REVISIONS_ID,),
            ),
            build_programs,
        ),
        UNITS_ID: (
            NodeSpec(
                id=UNITS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_curriculum"), *_ROUTES,
                     "tools/learning_os/unit_notes.py",
                     "tools/learning_os/semantics/predicates.py",
                     *_COMMON, *_load("curriculum"), *_LOADING_BASE,
                     *_GIT_AND_PATHING)
                ),
                direct_inputs=(
                    "gen.units",
                    "gen.modules",
                    "manifest.study_map_presence",
                    "manifest.working_notes",
                ),
                dependencies=(REVISIONS_ID, UNIT_PROJECT_EDGES_ID, SOURCE_MAPS_ID),
            ),
            build_units,
        ),
        STUDY_MAPS_ID: (
            NodeSpec(
                id=STUDY_MAPS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_curriculum", "stages"), *_ROUTES,
                     "tools/learning_os/material_refs.py", *_MATERIALS,
                     *_load("curriculum"), *_LOADING_BASE, *_GIT_AND_PATHING)
                ),
                direct_inputs=(
                    "manifest.study_map_files",
                    "manifest.working_notes",
                    "manifest.materials",
                ),
                dependencies=(REVISIONS_ID, SOURCE_MAPS_ID, SOURCES_ID),
            ),
            build_study_maps,
        ),
        SOURCE_MAPS_ID: (
            NodeSpec(
                id=SOURCE_MAPS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("records_curriculum"), *_ROUTES, *_MATERIALS,
                     *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.source_map_files", "manifest.materials"),
                dependencies=(REVISIONS_ID, SOURCES_ID),
            ),
            build_source_maps,
        ),
        SYNTHSES_ID: (
            NodeSpec(
                id=SYNTHSES_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_curriculum"),
                     "tools/learning_os/material_synthesis.py",
                     "tools/learning_os/materials_resolution.py",
                     *_ROUTES, *_REVISIONS,
                     *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=(
                    "manifest.syntheses",
                    "gen.units",
                    "manifest.revisions",
                    "manifest.materials",
                ),
                dependencies=(SOURCE_MAPS_ID,),
            ),
            build_syntheses,
        ),
        COORDINATION_ID: (
            NodeSpec(
                id=COORDINATION_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_work"), *_load("work"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.coordination",),
            ),
            build_coordination,
        ),
        THEMATIC_GROUPS_ID: (
            NodeSpec(
                id=THEMATIC_GROUPS_ID,
                version=version,
                producer_files=_node(
                    (*_proj("grouping"), *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.thematic",),
            ),
            build_thematic_groups,
        ),
        TOPICS_ID: (
            NodeSpec(
                id=TOPICS_ID,
                version=version,
                producer_files=_node(
                    (*_proj("grouping"), *_load("library"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.topics",),
            ),
            build_topics,
        ),
        UNIT_PROJECT_EDGES_ID: (
            NodeSpec(
                id=UNIT_PROJECT_EDGES_ID,
                version=version,
                producer_files=_node(
                    (*_proj("records_projects"),
                     *_load("projects"), *_LOADING_BASE)
                ),
                dependencies=(PROJECTS_ID,),
            ),
            build_unit_project_edges,
        ),
        REVISIONS_ID: (
            NodeSpec(
                id=REVISIONS_ID,
                version=version,
                producer_files=_node((*_MANIFEST, *_REVISIONS)),
                direct_inputs=("manifest.revisions",),
            ),
            build_revisions,
        ),
        RELATIONS_ID: (
            NodeSpec(
                id=RELATIONS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_load("knowledge"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.relations",),
            ),
            build_relations,
        ),
        RECORDS_ID: (
            NodeSpec(
                id=RECORDS_ID,
                version=version,
                producer_files=_node(_MANIFEST),
                dependencies=tuple(_RECORD_GROUP_NODES.values()),
            ),
            build_records,
        ),
        TYPED_COLLECTIONS_ID: (
            NodeSpec(
                id=TYPED_COLLECTIONS_ID,
                version=version,
                producer_files=_node(_MANIFEST),
                dependencies=(RECORDS_ID,),
            ),
            build_typed_collections,
        ),
        STAGES_ID: (
            NodeSpec(
                id=STAGES_ID,
                version=version,
                producer_files=_node(_MANIFEST),
                dependencies=(TYPED_COLLECTIONS_ID,),
            ),
            build_stages,
        ),
        SEMESTERS_ID: (
            NodeSpec(
                id=SEMESTERS_ID,
                version=version,
                producer_files=_node(_MANIFEST),
                dependencies=(TYPED_COLLECTIONS_ID,),
            ),
            build_semesters,
        ),
        EDGES_ID: (
            NodeSpec(
                id=EDGES_ID,
                version=version,
                producer_files=_node(_proj("atlas")),
                dependencies=(TYPED_COLLECTIONS_ID, STAGES_ID, CONCEPTS_ID),
            ),
            build_edges,
        ),
        INDEXES_ID: (
            NodeSpec(
                id=INDEXES_ID,
                version=version,
                producer_files=_node(_proj("indexes")),
                dependencies=(
                    RECORDS_ID,
                    TYPED_COLLECTIONS_ID,
                    SYNTHSES_ID,
                    EDGES_ID,
                    PROJECT_ALIASES_ID,
                ),
            ),
            build_indexes_node,
        ),
        PROGRESS_ID: (
            NodeSpec(
                id=PROGRESS_ID,
                version=version,
                producer_files=_node(_proj("tallies")),
                dependencies=(TYPED_COLLECTIONS_ID,),
            ),
            build_progress_node,
        ),
        COUNTS_ID: (
            NodeSpec(
                id=COUNTS_ID,
                version=version,
                producer_files=_node(
                    (*_MANIFEST, *_proj("tallies"),
                     "tools/learning_os/genout/coordination.py",
                     *_COMMON, "tools/learning_os/githistory.py",
                     *_load("knowledge", "library", "work", "curriculum"),
                     *_LOADING_BASE)
                ),
                direct_inputs=(
                    "gen.notes",
                    "gen.concepts",
                    "manifest.sources",
                    "manifest.collections",
                    "gen.workspaces",
                    "manifest.learning_paths",
                    "gen.units",
                    "manifest.study_map_presence",
                    "gen.relations",
                    "manifest.notes_git",
                    "manifest.inbox",
                ),
                dependencies=(
                    TYPED_COLLECTIONS_ID,
                    STAGES_ID,
                    THEMATIC_GROUPS_ID,
                    TOPICS_ID,
                    GARDEN_ID,
                    AI_ACTIONS_ID,
                ),
            ),
            build_counts_node,
        ),
        REVIEW_ITEMS_ID: (
            NodeSpec(
                id=REVIEW_ITEMS_ID,
                version=version,
                producer_files=_node(("tools/learning_os/genout/review.py",)),
                direct_inputs=("manifest.inbox",),
                dependencies=(TYPED_COLLECTIONS_ID,),
            ),
            build_review_items_node,
        ),
        GARDEN_ID: (
            NodeSpec(
                id=GARDEN_ID,
                version=version,
                producer_files=_node(
                    ("tools/learning_os/garden.py",
                     *_load("knowledge"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.garden",),
            ),
            build_garden,
        ),
        AI_ACTIONS_ID: (
            NodeSpec(
                id=AI_ACTIONS_ID,
                version=version,
                producer_files=_node(
                    ("tools/learning_os/ai_actions/projection.py",
                     "tools/learning_os/ai_actions/registry.py",
                     "tools/learning_os/ai_actions/storage.py",
                     "tools/learning_os/ai_actions/support.py",
                     "tools/learning_os/ai_actions/errors.py",
                     "tools/learning_os/garden.py",
                     *_load("knowledge"), *_LOADING_BASE)
                ),
                direct_inputs=("manifest.ai_files",),
                dependencies=(GARDEN_ID,),
            ),
            build_ai_actions,
        ),
        DEADLINES_ID: (
            NodeSpec(
                id=DEADLINES_ID,
                version=version,
                producer_files=_node(
                    ("tools/learning_os/genout/modules_view.py",
                     *_load("curriculum"), *_LOADING_BASE)
                ),
                direct_inputs=("gen.modules", "manifest.today"),
            ),
            build_deadlines,
        ),
        SEMANTIC_PAYLOAD_ID: (
            NodeSpec(
                id=SEMANTIC_PAYLOAD_ID,
                version=version,
                producer_files=_node(_MANIFEST),
                direct_inputs=("manifest.project_aliases", "manifest.resume"),
                dependencies=(
                    RECORDS_ID,
                    RELATIONS_ID,
                    THEMATIC_GROUPS_ID,
                    TOPICS_ID,
                    TYPED_COLLECTIONS_ID,
                    STAGES_ID,
                    SEMESTERS_ID,
                    EDGES_ID,
                    SYNTHSES_ID,
                    GARDEN_ID,
                    REVIEW_ITEMS_ID,
                    AI_ACTIONS_ID,
                    INDEXES_ID,
                    PROGRESS_ID,
                    COUNTS_ID,
                    REVISIONS_ID,
                    DEADLINES_ID,
                    BACKLINKS_SEMANTIC_ID,
                ),
            ),
            build_semantic_payload,
        ),
    }


def manifest_shadow_registry(repo: Repo, git: GitSnapshot | None = None) -> Registry:
    """The manifest graph plus the shared backlinks semantic node."""
    return {**generation_registry(repo), **manifest_registry(repo, git)}


def manifest_shadow_inputs(
    root: Path, repo: Repo, git: GitSnapshot | None = None
) -> dict[str, str]:
    """Merged gen.* and manifest.* input digests for one evaluation.

    A snapshot transaction passes its attempt snapshot so the git-backed
    digests pin the same table the builders observe; ``None`` reads fresh.
    """
    table = git.table if git is not None else None
    return {
        **generation_input_digests(root),
        **manifest_input_digests(root, repo, table),
    }


def serialize_manifest(payload: dict) -> str:
    """manifest.json bytes exactly as outputs.py writes them."""
    return (
        json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        + "\n"
    )


def validation_proof_producers() -> tuple[str, ...]:
    """Producer files for the validation-proof node (staging helper)."""
    return _node((
        "tools/learning_os/contracts/manifest_contract.py",
        "tools/learning_os/contracts/json_schema.py",
    ))


def _proof_matches(proof: Any, root: Path, full_digest: str, closure: str) -> bool:
    """Whether a cached proof actually certifies this payload (F5).

    The engine guarantees the bytes are intact; this guarantees they
    are the RIGHT bytes — a valid proof for this manifest under this
    contract. Anything else is rejected even on a key hit.
    """
    return (
        isinstance(proof, dict)
        and proof.get("valid") is True
        and proof.get("contract_version") == declared_version(root)
        and proof.get("manifest_sha256") == full_digest
        and proof.get("contract_closure_sha256") == closure
    )


def _enforce_with_proof(
    root: Path,
    payload: dict,
    *,
    closure: str,
    staging: Staging | None = None,
    trace: list[TraceEvent] | None = None,
) -> dict:
    """Enforce the contract, reusing a previous proof when identity matches.

    The proof key covers the complete manifest bytes, the contract
    closure, the validator implementation, the core code digest, the
    runtime identity, the validator's format-provider closure (G3), and
    the validation semantics version — the rule is "same bytes, same
    contract, same validator, same code, same runtime, same providers,
    same semantics, or enforce() runs again". A failed validation raises
    out of the builder, which the engine never caches, so failures are
    always re-examined.

    The proof evaluates in its own phase because its key needs the live
    publication metadata, which is stamped fresh and never cached. Its
    event appends to the same trace as the semantic graph.

    The closure arrives precomputed from the snapshot transaction's
    input map: enforce()'s reads happened after that observation and
    the transaction re-verifies it afterwards, so the proof cannot be
    keyed on contract bytes enforce() never saw.
    """
    full_digest = digest_bytes(canonical_bytes(payload))

    def build_proof(ctx: BuildContext) -> dict:
        enforce(payload, ctx.root)
        return {
            "valid": True,
            "contract_version": int(load_contract(ctx.root)["contract_version"]),
            "manifest_sha256": full_digest,
            "contract_closure_sha256": closure,
        }

    spec = NodeSpec(
        id=VALIDATION_PROOF_ID,
        version=MANIFEST_VALIDATION_VERSION,
        producer_files=validation_proof_producers(),
        direct_inputs=(
            "manifest.full_bytes",
            "manifest.contract_closure",
            "manifest.validator_runtime",
        ),
    )
    registry = {VALIDATION_PROOF_ID: (spec, build_proof)}
    inputs = {
        "manifest.full_bytes": full_digest,
        "manifest.contract_closure": closure,
        "manifest.validator_runtime": validator_runtime_digest(),
    }
    evaluation = evaluate(
        root, VALIDATION_PROOF_ID, registry=registry, inputs=inputs,
        staging=staging, trace=trace,
    )
    if evaluation.status == "hit" and not _proof_matches(
        evaluation.value, root, full_digest, closure
    ):
        # Internally consistent but wrong cache state (a valid blob for
        # another payload, a bug-written proof) must not skip enforce():
        # rebuild once through the validator. The replacement stages in
        # memory and persists only if the surrounding transaction commits
        # — a discarded attempt mutates nothing persistent. A second
        # mismatch is not instability but corruption the rebuild cannot
        # heal, so it fails closed instead of looping. (The trace keeps
        # the single hit event: the engine owns event construction, and
        # this path is reachable only through out-of-band state surgery.)
        rebuilt = build_proof(BuildContext(
            root=root, spec=spec, inputs=inputs, dependencies={}))
        if not _proof_matches(rebuilt, root, full_digest, closure):
            raise DerivedError(
                "validation proof failed verification after rebuild")
        if staging is not None:
            staging.pending[VALIDATION_PROOF_ID] = (
                evaluation.node_key, rebuilt)
        else:
            store_node(
                root, VALIDATION_PROOF_ID,
                node_key=evaluation.node_key, value=rebuilt)
        return rebuilt
    return evaluation.value


#: Snapshot-transaction attempts before a persistently moving tree
#: refuses instead of retrying. One attempt covers the overwhelmingly
#: common stable tree; the retries absorb a concurrent edit landing
#: mid-run.
SNAPSHOT_ATTEMPTS = 3


def build_manifest_shadow(
    repo: Repo,
    generated_at: str,
    *,
    trace: list[TraceEvent] | None = None,
    enforce_contract: bool = True,
    reuse_validation: bool = True,
) -> dict:
    """Compute the manifest through the derived graph (no writes).

    Only the semantic payload comes from cached nodes; publication
    metadata is stamped fresh and the contract is enforced exactly as
    the legacy path does (through the validation-proof node when
    reuse is enabled). ``build_manifest()`` stays authoritative.

    Snapshot-bound (F2): the shadow loads the repo inside its own
    snapshot window — snapshot, load, snapshot, verify — so the passed
    repo's contents are never trusted, only its root. Evaluation runs
    into staged (uncommitted) cache state; the inputs and the snapshot
    are re-verified afterwards and the staging commits only when all
    three observations agree. A concurrent edit therefore retries the
    run instead of memoizing torn bytes under a fresh digest. Trace
    events from discarded attempts are dropped; the trace holds the
    committed attempt only.

    Every git observation is snapshot-bound too (G1): the attempt captures
    one fresh history snapshot up front, evaluates builders and input
    digests against its table, and requires a fresh re-observation to
    agree — HEAD and table — before committing. Publication revision and
    dirtiness are bound the same way. ``generated_at`` stays a
    caller-asserted stamp: the future ``build_manifest_incremental`` MUST
    resolve it inside its own transaction instead of accepting it.
    """
    root = repo.root
    for _ in range(SNAPSHOT_ATTEMPTS):
        git_before = fresh_git_snapshot(root)
        state_before = _git_state(root)
        snapshot_before = canonical_snapshot_digest(root, git_before)
        fresh = load_repo(root)
        git_mid = fresh_git_snapshot(root)
        if (
            git_mid.head != git_before.head
            or canonical_snapshot_digest(root, git_mid) != snapshot_before
        ):
            continue  # the load raced a concurrent edit; reload
        require_publishable_manifest_repo(fresh)
        staging = Staging()
        attempt_trace: list[TraceEvent] = []
        inputs_before = manifest_shadow_inputs(root, fresh, git_before)
        results = evaluate_many(
            root,
            [SEMANTIC_PAYLOAD_ID],
            registry=manifest_shadow_registry(fresh, git_before),
            inputs=inputs_before,
            staging=staging,
            trace=attempt_trace,
        )
        payload = {
            "_generated": publish_manifest_metadata(
                fresh, generated_at, git_state=state_before),
            **results[SEMANTIC_PAYLOAD_ID].value,
        }
        if enforce_contract:
            if reuse_validation:
                _enforce_with_proof(
                    root,
                    payload,
                    closure=inputs_before["manifest.contract_closure"],
                    staging=staging,
                    trace=attempt_trace,
                )
            else:
                enforce(payload, root)
        git_after = fresh_git_snapshot(root)
        if git_after.head != git_before.head:
            continue  # history moved during evaluation; the staging dies here
        if manifest_shadow_inputs(root, fresh, git_after) != inputs_before:
            continue  # inputs moved during evaluation; the staging dies here
        if canonical_snapshot_digest(root, git_after) != snapshot_before:
            continue
        if _git_state(root) != state_before:
            continue  # publication state moved; the staging dies here
        commit_staging(root, staging)
        if trace is not None:
            trace.extend(attempt_trace)
        return payload
    raise TransactionFailure(
        "cannot publish the manifest: canonical inputs changed during "
        f"generation ({SNAPSHOT_ATTEMPTS} attempts)"
    )


@dataclass(frozen=True)
class ShadowManifestComparison:
    """Byte-exact shadow-vs-legacy verdict with both sides attached."""

    equivalent: bool
    shadow_sha256: str
    legacy_sha256: str
    shadow: dict
    legacy: dict


def compare_shadow_manifest(
    repo: Repo,
    generated_at: str | None = None,
    *,
    trace: list[TraceEvent] | None = None,
) -> ShadowManifestComparison:
    """Run both implementations and compare manifest bytes exactly.

    ``None`` resolves the stamp fresh INSIDE, once, shared by both sides
    (G1b): computing it outside admits stamp(H0)+revision(H1) tears. An
    explicit stamp is used as-is (tests). A commit landing during the
    legacy build surfaces as an honest mismatch, never a silent tear.
    """
    stamp = generated_at if generated_at is not None else stable_generated_at(repo.root)
    legacy = build_manifest(repo, stamp, build_backlinks(repo, stamp))
    shadow = build_manifest_shadow(repo, stamp, trace=trace)
    legacy_blob = serialize_manifest(legacy).encode("utf-8")
    shadow_blob = serialize_manifest(shadow).encode("utf-8")
    return ShadowManifestComparison(
        equivalent=shadow_blob == legacy_blob,
        shadow_sha256=hashlib.sha256(shadow_blob).hexdigest(),
        legacy_sha256=hashlib.sha256(legacy_blob).hexdigest(),
        shadow=shadow,
        legacy=legacy,
    )

