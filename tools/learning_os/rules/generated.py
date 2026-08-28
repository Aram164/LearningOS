"""Generated views and, when online, external URLs."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from .common import (
    CANONICAL_TREES,
    GENERATED_ALLOWED,
    GENERATED_REPORT_PREFIXES,
    MD_LINK_RE,
    _in_garden,
    _in_quarantine,
)


def _collect_http_urls(value, urls: set[str] | None = None) -> set[str]:
    """Collect every HTTP(S) value from a projected or canonical structure."""
    urls = urls if urls is not None else set()
    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            urls.add(value)
    elif isinstance(value, dict):
        for nested in value.values():
            _collect_http_urls(nested, urls)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _collect_http_urls(nested, urls)
    return urls


def _projected_http_urls(repo) -> set[str]:
    """Audit the same complete URL surface consumed by interfaces."""
    from ..genout import build_manifest
    from ..genout.common import stable_generated_at

    manifest = build_manifest(repo, stable_generated_at(repo.root))
    return _collect_http_urls(manifest)


def _loaded_http_urls(repo) -> set[str]:
    """Fallback URL inventory from the one loaded logical repository."""
    urls: set[str] = set()
    families = (
        repo.concepts,
        repo.sources,
        repo.collections,
        repo.modules,
        repo.module_source_maps,
        repo.thematic_groups,
        repo.topics,
        repo.projects,
        repo.programs,
        repo.units,
        repo.study_maps,
        repo.learning_paths,
        repo.notes,
        repo.workspaces,
    )
    for family in families:
        values = family.values() if isinstance(family, dict) else family
        for record in values:
            payload = getattr(record, "data", None)
            if payload is None:
                payload = getattr(record, "meta", record)
            _collect_http_urls(payload, urls)
    return urls


def _probe_external_url(url: str, timeout: int = 10,
                        opener=None) -> tuple[str | None, str]:
    """Return ``(finding, detail)`` with a browser-like GET fallback.

    HEAD-only audits create false alarms for sites such as notebooks and data
    portals.  A bounded range GET confirms those destinations without pulling
    their complete body.  Authentication and rate limiting are reported
    separately from genuine dead links.
    """
    opener = opener or urllib.request.urlopen
    last_status = None
    last_error = None
    for method in ("HEAD", "GET"):
        headers = {
            "User-Agent": "Mozilla/5.0 LearningOS link integrity check",
        }
        if method == "GET":
            headers["Range"] = "bytes=0-2047"
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with opener(request, timeout=timeout) as response:
                last_status = getattr(response, "status", 200)
                last_error = None
        except urllib.error.HTTPError as exc:
            last_status = exc.code
            last_error = None
        except Exception as exc:  # noqa: BLE001 - result is a warning, never a crash
            last_status = None
            last_error = exc.__class__.__name__
        if last_status is not None and 200 <= last_status < 400:
            return None, f"HTTP {last_status}"

    if last_status in {401, 403, 429}:
        return "access-controlled", f"HTTP {last_status}"
    if last_status in {404, 410}:
        return "dead-link", f"HTTP {last_status}"
    if last_status is not None:
        return "transient", f"HTTP {last_status}"
    return "transient", last_error or "unknown network failure"


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
                self.err("GEN-HEADER", "generated file lacks a generated-file warning header",
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
        urls = _loaded_http_urls(self.repo)
        try:
            urls.update(_projected_http_urls(self.repo))
        except Exception as exc:  # noqa: BLE001 - invalid data is reported elsewhere
            self.warn(
                "URL-AUDIT",
                "projected URL discovery unavailable; audited loaded canonical "
                f"records instead ({exc.__class__.__name__})",
            )
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
        with ThreadPoolExecutor(max_workers=min(8, len(urls) or 1)) as pool:
            findings = list(pool.map(_probe_external_url, sorted(urls)))
        for url, (finding, detail) in zip(sorted(urls), findings, strict=True):
            if finding == "access-controlled":
                self.warn("URL-ACCESS-CONTROLLED", f"{url} -> {detail}")
            elif finding == "dead-link":
                self.err("URL-DEAD", f"{url} -> {detail}")
            elif finding == "transient":
                self.warn("URL-TRANSIENT", f"{url} -> {detail}")
