"""Bounded read epoch (D04/D05): share verified pins, never truth.

A ReadSession memoizes raw outcomes of explicitly eligible reads only while
its dependency pin (manifest + identity bytes) is unchanged. Any write,
pin change, or close() ends the epoch; callers then take the fresh path.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def dependency_pin(root: Path) -> str:
    h = hashlib.sha256()
    for name in ("generated/manifest.json", "generated/manifest.identity.json"):
        try:
            h.update((root / name).read_bytes())
        except OSError:
            h.update(b"<missing>")
    return "sha256:" + h.hexdigest()


class ReadSession:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.pin = dependency_pin(self.root)
        self._memo: dict[tuple[str, ...], object] = {}
        self.loads = 0
        self.hits = 0
        self.closed = False

    def valid(self) -> bool:
        return not self.closed and dependency_pin(self.root) == self.pin

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
        self.pin = dependency_pin(self.root)

    def close(self) -> None:
        self.closed = True
        self._memo.clear()
