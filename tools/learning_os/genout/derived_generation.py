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
from typing import Any

from ..derived.engine import (
    BuildContext,
    Registry,
    Staging,
    TraceEvent,
    commit_staging,
    evaluate_many,
)
from ..derived.identity import canonical_snapshot_digest, digest_matching_files
from ..derived.model import DERIVED_SUBSTRATE_FILES, NodeSpec
from ..errors import TransactionFailure
from ..loader import Repo, load_repo
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
from .derived_inputs import (
    enumerate_module_files as _module_files,
)
from .derived_inputs import (
    enumerate_note_files as _note_files,
)
from .derived_inputs import (
    enumerate_registry_files as _registry_files,
)
from .derived_inputs import (
    enumerate_study_map_files as _study_map_files,
)
from .derived_inputs import (
    enumerate_unit_files as _unit_files,
)
from .derived_inputs import (
    enumerate_workspace_files as _workspace_files,
)

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


def generation_input_digests(root: Path) -> dict[str, str]:
    """One content digest per generation input domain.

    Each digest covers exactly the canonical files its loader reads (see
    derived_inputs), never the whole-tree fingerprint and never
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


#: Snapshot-transaction attempts before a persistently moving tree
#: refuses instead of retrying (mirrors the manifest shadow's bound).
SNAPSHOT_ATTEMPTS = 3


def generate_shadow(
    repo: Repo,
    generated_at: str,
    *,
    trace: list[TraceEvent] | None = None,
) -> dict[str, str]:
    """Compute the shadow artifacts through the derived graph (no writes).

    Only semantic values come from cached nodes; publication stamping is
    always fresh, exactly as the legacy path does it.

    Snapshot-bound like the manifest shadow: the repo is loaded inside
    the transaction's own snapshot window and evaluation commits only
    when the inputs prove stable across it. (No parse-failure refusal
    here: the legacy backlinks/map/report builders do not refuse, so the
    shadow must match them exactly, malformed records and all.)
    """
    root = repo.root
    for _ in range(SNAPSHOT_ATTEMPTS):
        snapshot_before = canonical_snapshot_digest(root)
        fresh = load_repo(root)
        if canonical_snapshot_digest(root) != snapshot_before:
            continue  # the load raced a concurrent edit; reload
        staging = Staging()
        attempt_trace: list[TraceEvent] = []
        inputs_before = generation_input_digests(root)
        results = evaluate_many(
            root,
            [BACKLINKS_SEMANTIC_ID, CONCEPT_MAP_BODY_ID, DEPENDENCY_REPORT_BODY_ID],
            registry=generation_registry(fresh),
            inputs=inputs_before,
            staging=staging,
            trace=attempt_trace,
        )
        backlinks = publish_backlinks(
            fresh, results[BACKLINKS_SEMANTIC_ID].value, generated_at)
        artifacts = {
            "backlinks.json": _backlinks_artifact(backlinks),
            "concept-map.md": publish_concept_map(
                results[CONCEPT_MAP_BODY_ID].value, generated_at) + "\n",
            "dependency-report.md": publish_dependency_report(
                results[DEPENDENCY_REPORT_BODY_ID].value, generated_at) + "\n",
        }
        if generation_input_digests(root) != inputs_before:
            continue  # inputs moved during evaluation; the staging dies here
        if canonical_snapshot_digest(root) != snapshot_before:
            continue
        commit_staging(root, staging)
        if trace is not None:
            trace.extend(attempt_trace)
        return artifacts
    raise TransactionFailure(
        "cannot generate shadow artifacts: canonical inputs changed during "
        f"generation ({SNAPSHOT_ATTEMPTS} attempts)"
    )


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
