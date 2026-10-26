"""Publication of the generated projection, and reads of a provably current manifest."""

from __future__ import annotations

import json
from pathlib import Path

from learning_os.app.lock import escalate_operator_lock as _escalate_operator_lock
from learning_os.app.lock import operator_lock as _operator_lock
from learning_os.derive.projection import (
    build_backlinks,
    build_manifest,
    generate_all,
    stable_generated_at,
    write_outputs,
)
from learning_os.derive.projection.common import git_state as _git_state
from learning_os.domain.snapshot import Repo
from learning_os.store.derived.model import DerivedError
from learning_os.store.fingerprint import (
    canonical_fingerprint,
    seed_source_fingerprint,
)
from learning_os.store.loader import load_repo
from learning_os.store.loading import load_workspaces
from learning_os.store.manifest_identity import (
    IDENTITY_FILENAME,
    bytes_sha256,
    check_identity,
    manifest_text,
)


def publish(root: Path) -> None:
    publish_repo(load_repo(root))


def publish_repo(repo) -> None:
    write_outputs(repo, generate_all(repo))


class _LazyRepo:
    """``load_repo`` deferred to first attribute access (reuse fast path).

    ``_fresh_manifest_and_repo`` serves the stored manifest without parsing
    canonical inputs; callers that only read the manifest never pay for the
    load (measured: load 0.24 s of a 2.0 s read). The first attribute access
    loads once; afterwards this answers exactly like the real repo. The
    workspace-owned learning_paths registry has its own partial load. Reads
    that need repo-only state (path-stage lookup, use evidence) trigger the
    load implicitly and stay correct.
    """

    def __init__(self, root: Path) -> None:
        self._lazy_root = root
        self._lazy_repo = None
        self._lazy_paths = None

    def _resolve(self):
        if self._lazy_repo is None:
            self._lazy_repo = load_repo(self._lazy_root)
        return self._lazy_repo

    @property
    def learning_paths(self):
        if self._lazy_repo is not None:
            return self._lazy_repo.learning_paths
        if self._lazy_paths is None:
            partial = Repo(root=self._lazy_root)
            load_workspaces(partial, self._lazy_root)
            self._lazy_paths = partial.learning_paths
        return self._lazy_paths

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


def _try_reuse_manifest(root: Path, live_snapshot: str, *, restamp: bool) -> dict | None:
    """The stored manifest when it provably describes current state, else None.

    Every mismatch, missing file, or parse error answers None so the caller
    rebuilds exactly as before; a partially matching or corrupt file is
    never served. Contract/git failures propagate: the fresh build raises
    them identically, so swallowing them here would serve reads the fresh
    path refuses.
    """
    try:
        raw = (root / "generated/manifest.json").read_bytes()
        identity = json.loads((root / "generated" / IDENTITY_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # The sidecar pins the exact manifest bytes it describes: a pair caught
    # mid-publication (or a hand-touched file) never passes as current.
    if not isinstance(identity, dict) or identity.get("manifest_sha256") != bytes_sha256(raw):
        return None
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(manifest, dict):
        return None
    try:
        current, _reason = check_identity(
            root, manifest, identity, live_snapshot=live_snapshot)
    except (OSError, ValueError, DerivedError):
        return None
    if not current:
        return None
    if restamp:
        # Runtime metadata is restamped so the served manifest equals a fresh
        # build byte for byte: git state can move (a docs-only commit) while
        # every pinned input still matches.
        manifest["_generated"]["generated_at"] = stable_generated_at(root)
        revision, dirty = _git_state(root)
        manifest["_generated"]["source_revision"] = revision
        manifest["_generated"]["source_dirty"] = dirty
    return manifest


def fresh_manifest_and_repo(
    root: Path, *, snapshot_id: str | None = None, restamp: bool = False,
) -> tuple[dict, object]:
    """A current manifest plus the repo it was built from.

    The manifest is served from the stored build when it is provably
    current, otherwise rebuilt exactly as before. ``restamp`` refreshes
    the served ``_generated`` runtime metadata (git state, timestamp) to
    what a fresh build would stamp; pass it only when the caller surfaces
    ``_generated`` (today: full bootstrap) — it costs several git queries
    and every other read answers from payload keys the check already
    verified.
    """
    # Every projection read takes the operator lock shared: concurrent
    # current-manifest reads proceed together, and acquisition still runs
    # crash recovery first (escalating when a journal awaits it), so
    # single-ID reads, batch reads, and bootstrap all observe
    # transaction-consistent post-recovery state instead of disagreeing
    # after a kill (JF-21). Re-entrant: callers already holding the lock
    # (batch inspect, bootstrap, gateway dispatch) pass straight through,
    # staying exclusive when they already are.
    with _operator_lock(root, shared=True):
        # Snapshot-bound callers already computed this under the same lock;
        # sharing it keeps a reuse read at two hashes and a rebuild read
        # at three (see test_bounded_read_hashes_thrice_with_seeded_manifest).
        live = snapshot_id if snapshot_id is not None else f"sha256:{canonical_fingerprint(root)}"
        reused = _try_reuse_manifest(root, live, restamp=restamp)
        if reused is not None:
            return reused, _LazyRepo(root)
        # Stale or missing: drop the shared lock, take the exclusive one,
        # re-check the identity (a writer may have published while the
        # shared lock was down), then build. Never upgrade in place. When
        # the caller already held the lock exclusive, nothing dropped and
        # the snapshot above is still the same instant — no re-hash.
        dropped = _escalate_operator_lock(root)
        if dropped:
            live = f"sha256:{canonical_fingerprint(root)}"
        reused = _try_reuse_manifest(root, live, restamp=restamp)
        if reused is not None:
            return reused, _LazyRepo(root)
        repo = load_repo(root)
        if snapshot_id is not None:
            seed_source_fingerprint(repo, live)
        generated_at = stable_generated_at(root)
        backlinks = build_backlinks(repo, generated_at)
        # Match the published manifest representation, including nested key order,
        # so the single CLI encoder produces identical bytes on cache hit and miss.
        manifest = build_manifest(repo, generated_at, backlinks)
        return json.loads(manifest_text(manifest)), repo


def fresh_manifest(root: Path, *, snapshot_id: str | None = None,
                    restamp: bool = False) -> dict:
    manifest, _ = fresh_manifest_and_repo(root, snapshot_id=snapshot_id, restamp=restamp)
    return manifest
