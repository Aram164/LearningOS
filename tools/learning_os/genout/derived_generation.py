"""Shadow incremental generation over the derived-state graph (proof phase).

Selected artifacts are computed through derived nodes and compared
against the legacy builders byte-for-byte. ``generate_all()`` stays
authoritative: this module never writes generated/ — the disposable
derived-state cache is its only side effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..derived.engine import BuildContext, Registry, TraceEvent, evaluate_many
from ..derived.identity import digest_matching_files
from ..derived.model import DERIVED_SUBSTRATE_FILES, NodeSpec
from .concepts import (
    build_backlinks,
    build_backlinks_semantic,
    build_concept_map,
    build_concept_map_body,
    build_dependency_report,
    build_dependency_report_body,
    publish_backlinks,
    publish_concept_map,
    publish_dependency_report,
)

if TYPE_CHECKING:
    from ..loader import Repo

BACKLINKS_SEMANTIC_ID = "gen.backlinks.semantic"
CONCEPT_MAP_BODY_ID = "gen.concept-map.body"
DEPENDENCY_REPORT_BODY_ID = "gen.dependency-report.body"

#: Bumped when a shadow node changes shape (inputs, dependencies, or value
#: structure) independently of its producer files.
GENERATION_NODE_VERSION = 1

BACKLINKS_PRODUCERS = (
    "tools/learning_os/genout/concepts.py",
    *DERIVED_SUBSTRATE_FILES,
)
# concepts.py holds the bodies; common.py holds the header/mermaid helpers.
# The dependency body uses no common.py helper today — its inclusion is the
# conservative choice (an extra producer only costs a rebuild).
CONCEPT_MAP_PRODUCERS = (
    "tools/learning_os/genout/concepts.py",
    "tools/learning_os/genout/common.py",
    *DERIVED_SUBSTRATE_FILES,
)
DEPENDENCY_REPORT_PRODUCERS = CONCEPT_MAP_PRODUCERS

SHADOW_ARTIFACTS = ("backlinks.json", "concept-map.md", "dependency-report.md")


def _note_files(root: Path) -> list[Path]:
    """Mirror load_notes selection: every *.md under knowledge/notes."""
    notes_dir = root / "knowledge" / "notes"
    if not notes_dir.is_dir():
        return []
    return sorted(notes_dir.rglob("*.md"))


def _registry_files(root: Path, consolidated: str, partition: str) -> list[Path]:
    """Mirror _load_registry selection: consolidated file plus top-level *.yaml."""
    files: list[Path] = []
    single = root / consolidated
    if single.exists():
        files.append(single)
    part_dir = root / partition
    if part_dir.is_dir():
        files.extend(sorted(part_dir.glob("*.yaml")))
    return files


def _workspace_files(root: Path) -> list[Path]:
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


def _partitioned_module_files(root: Path) -> list[Path]:
    return sorted((root / "curriculum" / "modules").glob("*/module.yaml"))


def _module_files(root: Path) -> list[Path]:
    """Mirror load_modules: the always-loaded legacy snapshot plus every
    partitioned module file — exactly the files the loader opens."""
    files: list[Path] = []
    legacy = root / "records" / "modules.yaml"
    if legacy.exists():
        files.append(legacy)
    files.extend(_partitioned_module_files(root))
    return files


def _unit_files(root: Path) -> list[Path]:
    """Mirror _load_units: */unit.yaml exactly one level under each units/ dir.

    Over-approximates in one corner: units of modules that failed to load
    are hashed though the loader skips them (extra rebuild, never stale).
    """
    files: list[Path] = []
    for module_file in _partitioned_module_files(root):
        units_dir = module_file.parent / "units"
        if not units_dir.is_dir():
            continue
        files.extend(sorted(units_dir.glob("*/unit.yaml")))
    return files


def _study_map_files(root: Path) -> list[Path]:
    """Mirror study-map loading plus the expansion input.

    StudyMap.data is the EXPANDED map, so module source-map.yaml content
    flows into the stages backlinks reads: it is a study-map input.
    """
    files: list[Path] = []
    for unit_file in _unit_files(root):
        candidate = unit_file.parent / "study-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    for module_file in _partitioned_module_files(root):
        candidate = module_file.parent / "source-map.yaml"
        if candidate.is_file():
            files.append(candidate)
    return files


def generation_input_digests(root: Path) -> dict[str, str]:
    """One content digest per generation input domain.

    Each digest covers exactly the canonical files its loader reads (see
    the enumerators above), never the whole-tree fingerprint and never
    Repo object identity.
    """
    return {
        "gen.notes": digest_matching_files(root, _note_files(root)),
        "gen.concepts": digest_matching_files(
            root, _registry_files(root, "knowledge/concepts.yaml", "knowledge/concepts")),
        "gen.relations": digest_matching_files(
            root,
            _registry_files(
                root, "knowledge/concept-relations.yaml", "knowledge/concept-relations")),
        "gen.workspaces": digest_matching_files(root, _workspace_files(root)),
        "gen.modules": digest_matching_files(root, _module_files(root)),
        "gen.units": digest_matching_files(root, _unit_files(root)),
        "gen.study_maps": digest_matching_files(root, _study_map_files(root)),
    }


def generation_registry(repo: Repo) -> Registry:
    """Node specs (static) with builders closed over the loaded repo.

    The repo is execution data; reuse is proven by the declared input
    digests, never by object identity.
    """

    def build_backlinks_node(_ctx: BuildContext) -> dict[str, Any]:
        return build_backlinks_semantic(repo)

    def build_concept_map_node(_ctx: BuildContext) -> str:
        return build_concept_map_body(repo)

    def build_dependency_report_node(ctx: BuildContext) -> str:
        return build_dependency_report_body(
            repo, ctx.dependencies[BACKLINKS_SEMANTIC_ID].value)

    return {
        BACKLINKS_SEMANTIC_ID: (
            NodeSpec(
                id=BACKLINKS_SEMANTIC_ID,
                version=GENERATION_NODE_VERSION,
                producer_files=BACKLINKS_PRODUCERS,
                direct_inputs=(
                    "gen.notes",
                    "gen.workspaces",
                    "gen.modules",
                    "gen.units",
                    "gen.study_maps",
                    "gen.relations",
                ),
            ),
            build_backlinks_node,
        ),
        CONCEPT_MAP_BODY_ID: (
            NodeSpec(
                id=CONCEPT_MAP_BODY_ID,
                version=GENERATION_NODE_VERSION,
                producer_files=CONCEPT_MAP_PRODUCERS,
                direct_inputs=("gen.concepts", "gen.relations"),
            ),
            build_concept_map_node,
        ),
        DEPENDENCY_REPORT_BODY_ID: (
            NodeSpec(
                id=DEPENDENCY_REPORT_BODY_ID,
                version=GENERATION_NODE_VERSION,
                producer_files=DEPENDENCY_REPORT_PRODUCERS,
                direct_inputs=("gen.concepts", "gen.relations", "gen.modules", "gen.workspaces"),
                dependencies=(BACKLINKS_SEMANTIC_ID,),
            ),
            build_dependency_report_node,
        ),
    }


def _backlinks_artifact(payload: dict) -> str:
    """Serialize backlinks exactly as outputs.py does for backlinks.json."""
    return (
        json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n"
    )


def generate_shadow(
    repo: Repo,
    generated_at: str,
    *,
    trace: list[TraceEvent] | None = None,
) -> dict[str, str]:
    """Compute the shadow artifacts through the derived graph (no writes).

    Only semantic values come from cached nodes; publication stamping is
    always fresh, exactly as the legacy path does it.
    """
    results = evaluate_many(
        repo.root,
        [BACKLINKS_SEMANTIC_ID, CONCEPT_MAP_BODY_ID, DEPENDENCY_REPORT_BODY_ID],
        registry=generation_registry(repo),
        inputs=generation_input_digests(repo.root),
        trace=trace,
    )
    backlinks = publish_backlinks(repo, results[BACKLINKS_SEMANTIC_ID].value, generated_at)
    return {
        "backlinks.json": _backlinks_artifact(backlinks),
        "concept-map.md": publish_concept_map(
            results[CONCEPT_MAP_BODY_ID].value, generated_at) + "\n",
        "dependency-report.md": publish_dependency_report(
            results[DEPENDENCY_REPORT_BODY_ID].value, generated_at) + "\n",
    }


def legacy_shadow_artifacts(repo: Repo, generated_at: str) -> dict[str, str]:
    """The same three artifacts through the legacy builders (reference)."""
    backlinks = build_backlinks(repo, generated_at)
    return {
        "backlinks.json": _backlinks_artifact(backlinks),
        "concept-map.md": build_concept_map(repo, generated_at) + "\n",
        "dependency-report.md": build_dependency_report(repo, backlinks, generated_at) + "\n",
    }


@dataclass(frozen=True)
class ShadowComparison:
    """Byte-exact shadow-vs-legacy verdict with both sides attached."""

    equivalent: bool
    artifacts: dict[str, bool]
    shadow: dict[str, str]
    legacy: dict[str, str]


def compare_shadow_generation(
    repo: Repo,
    generated_at: str,
    *,
    trace: list[TraceEvent] | None = None,
) -> ShadowComparison:
    """Run both implementations and compare artifact bytes exactly."""
    legacy = legacy_shadow_artifacts(repo, generated_at)
    shadow = generate_shadow(repo, generated_at, trace=trace)
    artifacts = {name: shadow[name] == legacy[name] for name in SHADOW_ARTIFACTS}
    return ShadowComparison(
        equivalent=all(artifacts.values()),
        artifacts=artifacts,
        shadow=shadow,
        legacy=legacy,
    )
