"""One snapshot-bound verdict for the migrated projection families.

The caller need not choose stamps, clear process caches, coordinate separate
proof runs, or infer whether their results describe the same repository.
This verifies four projections, not canonical validity or the entire system.
Published views are untouched; each inner build may update disposable state
only after its own snapshot admission.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..derived.identity import canonical_snapshot_digest
from ..errors import TransactionFailure
from ..githistory import fresh_git_snapshot, last_commit_dates, last_commit_timestamps
from ..loader import load_repo
from .common import _git_state
from .derived_generation import compare_shadow_generation
from .manifest_derived import SNAPSHOT_ATTEMPTS, compare_shadow_manifest, serialize_manifest


def verify_shadow_projections(root: Path) -> dict:
    """Compare all currently migrated projections within one stable window.

    A moving tree retries; a stable mismatch returns an explicit failure.
    The returned snapshot and input digest bind the verdict to this run,
    never authorize later writes, and never replace canonical validation.
    """
    for _ in range(SNAPSHOT_ATTEMPTS):
        git_before = fresh_git_snapshot(root)
        state_before = _git_state(root)
        if git_before.table is None or git_before.head != state_before[0]:
            continue
        before = canonical_snapshot_digest(root, git_before)
        # Reference builders use process-local Git maps. A second invocation
        # in the same interpreter must not inherit the first one's history.
        last_commit_dates.cache_clear()
        last_commit_timestamps.cache_clear()
        repo = load_repo(root)
        related_trace: list = []
        manifest_trace: list = []
        related = compare_shadow_generation(repo, trace=related_trace)
        manifest = compare_shadow_manifest(repo, trace=manifest_trace)
        git_after = fresh_git_snapshot(root)
        if (git_after.table is None or git_after.head != state_before[0]
                or _git_state(root) != state_before
                or canonical_snapshot_digest(root, git_after) != before):
            continue

        related_meta = json.loads(related.shadow["backlinks.json"])["_generated"]
        manifest_meta = manifest.shadow["_generated"]
        same_publication = all(
            related_meta[key] == manifest_meta[key]
            for key in ("snapshot_id", "generated_at")
        ) and manifest_meta["source_revision"] == state_before[0]
        shadow = {**related.shadow, "manifest.json": serialize_manifest(manifest.shadow)}
        legacy = {**related.legacy, "manifest.json": serialize_manifest(manifest.legacy)}
        artifacts = {
            name: {
                "equal": shadow[name] == legacy[name],
                "shadow_sha256": hashlib.sha256(shadow[name].encode("utf-8")).hexdigest(),
                "full_sha256": hashlib.sha256(legacy[name].encode("utf-8")).hexdigest(),
            }
            for name in sorted(shadow)
        }
        equivalent = same_publication and all(row["equal"] for row in artifacts.values())
        return {
            "status": "verified" if equivalent else "mismatch",
            "equivalent": equivalent,
            "snapshot_id": manifest_meta["snapshot_id"],
            "input_digest": f"sha256:{before}",
            "source_revision": state_before[0],
            "generated_at": manifest_meta["generated_at"],
            "same_publication": same_publication,
            "artifacts": artifacts,
            "nodes": {
                family: {
                    "reused": sum(event.status == "hit" for event in trace),
                    "rebuilt": sum(event.status == "rebuilt" for event in trace),
                }
                for family, trace in (("manifest", manifest_trace), ("related", related_trace))
            },
            "published": False,
        }
    raise TransactionFailure(
        "cannot verify projections: inputs changed or Git history was unreadable "
        f"({SNAPSHOT_ATTEMPTS} attempts)"
    )
