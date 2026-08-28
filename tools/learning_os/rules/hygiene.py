"""Non-fatal hygiene for files inside the canonical repository."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from ..fingerprint import source_fingerprint
from ..githistory import last_commit_timestamp
from .common import STALE_LOCK_AGE_S


class ChecksHygiene:
    """Mixed into Validator; see rules/core.py."""
    # ------------------------------------------------------- hygiene (ADR-004)
    def check_hygiene(self):
        """Self-announcing mess detection. Warnings only — nags, never blocks."""
        self._hygiene_stale_locks()
        self._hygiene_stale_views()
        self._hygiene_unfiled()

    def _hygiene_stale_locks(self):
        # The repository's own .git plus the container repo above it (if any).
        candidates = [self.repo.root / ".git" / "index.lock"]
        container = self.repo.root.parent.parent
        if (container / ".git").is_dir():
            candidates.append(container / ".git" / "index.lock")
        now = time.time()
        for lock in candidates:
            try:
                if lock.is_file() and now - lock.stat().st_mtime > STALE_LOCK_AGE_S:
                    self.warn("HYGIENE-LOCK",
                              "stale git index.lock (crashed git process) — commits are "
                              f"silently blocked until it is removed: rm '{lock}'")
            except OSError:
                continue

    def _hygiene_stale_views(self):
        manifest = self.repo.root / "generated" / "manifest.json"
        if not manifest.is_file():
            # Synthetic/portable trees without Git history are valid before
            # their first projection. A real checkout should always publish.
            if not self._git(["log", "-1", "--format=%H"]).strip():
                return
            self.warn("HYGIENE-VIEWS",
                      "generated/ views absent — run `make views` (they are disposable, "
                      "but the human-fallback path depends on them)")
            return
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            projected = (data.get("_generated") or {}).get("source_fingerprint")
            current = source_fingerprint(self.repo)
        except (OSError, json.JSONDecodeError):
            projected, current = None, "unreadable"
        if projected != current:
            self.warn("HYGIENE-VIEWS",
                      "generated/manifest.json is not the current authored snapshot — "
                      "run `make views`",
                      "generated/manifest.json")

    def _hygiene_unfiled(self):
        root = self.repo.root

        def flag(p: Path, hint: str):
            self.warn("HYGIENE-UNFILED",
                      f"loose Markdown file — {hint} (drop-anything home: work/inbox/)",
                      self._rel(p))

        for p in root.glob("*.md"):
            if p.name not in {"README.md", "CLAUDE.md", "AGENTS.md"}:
                flag(p, "repository root is not a filing location")
        for p in (root / "knowledge").glob("*.md"):
            flag(p, "notes belong in knowledge/notes/<domain>/")
        for p in (root / "knowledge" / "notes").glob("*.md"):
            flag(p, "note is outside a domain bucket")
        for p in (root / "work").glob("*.md"):
            if p.name != "COORDINATION.md":
                flag(p, "work/ root holds only COORDINATION.md")
        for tree in ("records", "sources"):
            for p in (root / tree).rglob("*.md"):
                flag(p, f"{tree}/ holds registries (YAML), not Markdown")
        active = root / "work" / "active"
        if active.is_dir():
            for ws in active.iterdir():
                if ws.is_dir():
                    for p in ws.glob("*.md"):
                        if p.name != "CONTEXT.md":
                            flag(p, "file beside CONTEXT.md — belongs in scratch/, "
                                    "inputs/ or outputs/")

    # ------------------------------------------------------------------ git
    def _git(self, args: list[str]) -> str:
        try:
            out = subprocess.run(["git", *args], cwd=self.repo.root, capture_output=True,
                                 text=True, timeout=30)
            return out.stdout
        except Exception:  # noqa: BLE001
            return ""

    def _git_last_commit_ts(self, path: Path) -> float | None:
        """One batched history walk serves every path; see learning_os.githistory."""
        return last_commit_timestamp(
            self.repo.root, str(path.relative_to(self.repo.root)))
