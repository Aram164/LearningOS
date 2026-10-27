"""A bounded, input-pinned read lifetime; never a stamp-only truth cache."""
from __future__ import annotations

import contextvars
import hashlib
import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from learning_os.domain.snapshot import Repo
from learning_os.store import observations
from learning_os.store.contracts.manifest_contract import declared_schema_sha256
from learning_os.store.derived.identity import (
    digest_code_identity,
    digest_matching_files,
    digest_tree,
    runtime_digest,
)
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.manifest_identity import materials_digest, operations_digest
from learning_os.store.session.githistory import read_history

_CURRENT: contextvars.ContextVar[ReadSession | None] = contextvars.ContextVar("read_session", default=None)


def _dependency_state(root: Path) -> tuple[str, str]:
    """Observe authored and noncanonical dependencies, even if views did not move."""
    snapshot = "sha256:" + canonical_fingerprint(root)
    inputs = [str(root.resolve()), snapshot, digest_code_identity(root),
              runtime_digest(), declared_schema_sha256(root), materials_digest(root),
              operations_digest(root), observations.today().isoformat(),
              read_history(root, "-1", "--format=%H")]
    # Task descriptions can come from the executing authority when a data-only
    # fixture has no operator prose. Pin both actual readers' roots.
    authorities = {root.resolve(), Path(__file__).resolve().parents[3]}
    for authority in sorted(authorities):
        if authority != root.resolve():
            inputs.extend([digest_tree(authority, "system/schema"), digest_tree(authority, "system/contracts")])
        prose = sorted((authority / "system").rglob("*.md")) + [authority / "AGENTS.md", authority / "README.md"]
        inputs.append(digest_matching_files(authority, [p for p in prose if p.is_file()]))
    for name in ("generated/manifest.json", "generated/manifest.identity.json"):
        try:
            inputs.append(hashlib.sha256((root / name).read_bytes()).hexdigest())
        except OSError:
            inputs.append("missing:" + name)
    return hashlib.sha256(json.dumps(inputs).encode()).hexdigest(), snapshot


def dependency_pin(root: Path) -> str:
    return _dependency_state(root)[0]


def current_session(root: Path) -> ReadSession | None:
    session = _CURRENT.get()
    return session if session is not None and session.root == root.resolve() and not session.closed else None


class ReadSession:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.pin = self.snapshot = ""
        self._epoch_unchanged: bool | None = None
        self._memo: dict[tuple[str, ...], object] = {}
        self.loads = 0
        self.hits = 0
        self.closed = False
        self.active = False
        self.manifest: dict[str, object] | None = None
        self.model: object | None = None

    def valid(self) -> bool:
        if self.closed:
            return False
        if self.active:
            return True
        if not self.pin:
            self.pin, self.snapshot = _dependency_state(self.root)
            return True
        return dependency_pin(self.root) == self.pin

    def unchanged(self) -> bool:
        """Use the completed epoch's closing observation, or check a standalone memo."""
        if self.closed:
            return False
        if self._epoch_unchanged is not None:
            return self._epoch_unchanged
        return self.valid()

    def repository(self) -> Repo:
        if isinstance(self.model, Repo):
            return self.model
        resolve = getattr(self.model, "_resolve", None)
        previous_loads = self.loads
        if callable(resolve):
            repo: Repo = resolve()
        else:
            repo = load_repo(self.root)
        self.model = repo
        if self.loads == previous_loads:
            self.loads += 1
        return repo

    def get(self, key: tuple[str, ...]) -> object:
        if not self.valid():
            return None
        if key in self._memo:
            self.hits += 1
            return self._memo[key]
        return None

    def put(self, key: tuple[str, ...], value: object) -> None:
        if self.valid():
            self._memo[key] = value

    def invalidate(self) -> None:
        self._memo.clear()
        self.manifest = None
        self.model = None
        self.pin, self.snapshot = _dependency_state(self.root)
        self._epoch_unchanged = None

    @contextmanager
    def activate(self, prepare: Callable[[], tuple[dict[str, object], object]] | None = None,
                 *, timeout_s: float | None = None) -> Iterator[ReadSession]:
        """Hold the cooperating-writer boundary only while executing serial reads."""
        from learning_os.app.lock import operator_lock

        if self.closed or self.active:
            raise RuntimeError("read session is closed or already active")
        options = {} if timeout_s is None else {"timeout_s": timeout_s}
        with operator_lock(self.root, shared=True, **options):
            # Publication can escalate this lock before any memo is live.
            prepared = prepare() if prepare is not None else None
            self.invalidate()
            prepared_current = True
            if prepared is not None:
                self.manifest, self.model = prepared
                generated = self.manifest.get("_generated")
                if isinstance(generated, dict):
                    prepared_current = generated.get("snapshot_id") == self.snapshot
            self.active = True
            token = _CURRENT.set(self)
            try:
                yield self
            finally:
                try:
                    self._epoch_unchanged = dependency_pin(self.root) == self.pin and prepared_current
                finally:
                    self.active = False
                    _CURRENT.reset(token)

    def close(self) -> None:
        self.closed = True
        self._memo.clear()
        self.manifest = None
        self.model = None
