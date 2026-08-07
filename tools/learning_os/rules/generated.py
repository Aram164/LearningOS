"""Generated views and, when online, external URLs."""

from __future__ import annotations

import json
from .common import (
    CANONICAL_TREES, GENERATED_ALLOWED, GENERATED_REPORT_PREFIXES, MD_LINK_RE, _in_garden,
    _in_quarantine
)


class ChecksGenerated:
    """Mixed into Validator; see rules/core.py."""
    def check_generated(self):
        gen = self.repo.root / "generated"
        if not gen.is_dir():
            return
        for f in sorted(gen.iterdir()):
            if f.name == "reports":
                continue
            if f.is_file() and f.name not in GENERATED_ALLOWED:
                self.err("GEN-UNKNOWN",
                         f"unexpected file in generated/: {f.name} (agent-computed artifacts "
                         "live in workspaces, never in generated/)")
        reports = gen / "reports"
        if reports.is_dir():
            for f in sorted(reports.iterdir()):
                if f.is_file() and not f.name.startswith(GENERATED_REPORT_PREFIXES):
                    self.err("GEN-UNKNOWN", f"unexpected file in generated/reports/: {f.name}")
        # Generated warning headers
        for f in sorted(gen.rglob("*.md")):
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            if "GENERATED" not in head:
                self.err("GEN-HEADER", f"generated file lacks a generated-file warning header",
                         self._rel(f))
        for f in sorted(gen.rglob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.err("GEN-JSON", "generated JSON does not parse", self._rel(f))
                continue
            if isinstance(data, dict) and "_generated" not in data:
                self.err("GEN-HEADER", "generated JSON lacks the '_generated' warning key",
                         self._rel(f))
        # Archived workspaces excluded from generated indexes
        archived_ids = [w.id for w in self.repo.archived_workspaces()]
        for name in ("concept-index.md", "source-index.md"):
            f = gen / name
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="replace")
                for wid in archived_ids:
                    if wid in text:
                        self.err("GEN-ARCHIVED",
                                 f"archived workspace '{wid}' appears in generated/{name}")

    def check_external_urls(self):
        import urllib.request
        urls = set()
        for source in self.repo.sources.values():
            if source.get("url"):
                urls.add(source["url"])
        for tree in CANONICAL_TREES:
            base = self.repo.root / tree
            if not base.is_dir():
                continue
            for f in base.rglob("*.md"):
                if _in_garden(self.repo.root, f) or _in_quarantine(self.repo.root, f):
                    continue
                for target in MD_LINK_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
                    if target.startswith(("http://", "https://")):
                        urls.add(target)
        for url in sorted(urls):
            try:
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "learning-os-validate/0.1"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        self.warn("URL-UNREACHABLE", f"{url} -> HTTP {resp.status}")
            except Exception as exc:  # noqa: BLE001 - report, never block
                self.warn("URL-UNREACHABLE", f"{url} -> {exc.__class__.__name__}")
