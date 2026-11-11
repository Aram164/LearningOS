"""Material search index lifecycle, freshness verification, and query execution.

Architecture (ADR-020):
- Single self-describing read-only SQLite FTS5 file per text-cache identity:
  `generated/material-search/index-<F[:16]>.sqlite3`
- Pure text index: `material_fts(body, sha256 UNINDEXED, page_no UNINDEXED)`
  with `unicode61 remove_diacritics 2` tokenization
- Per-call route bindings and live file freshness checks (stat first, hash on mismatch)
- Coverage and text-cache freshness disclosure on every response
- Bounded input validation, deferred snippet computation, and VM-step budget backstop
- Hits grouped by PDF outline section (digest-keyed outline cache under
  `generated/material-outlines/`, harvested by `tools/material_outline.py`), with
  an explicit unsectioned group per document; limit and offset count groups over
  one fixed candidate scan so paging is stable
- A query equal to a registered concept label or alias also searches that
  concept's other registered names, and says so in `expansion`
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.material_refs import unit_routes
from learning_os.domain.snapshot import Repo
from learning_os.domain.suggest import with_suggestions
from learning_os.domain.validation import OUTLINE_TOP_DIR, SEARCH_TOP_DIR
from learning_os.store.loading import load_repo
from learning_os.store.materials.resolution import (
    resolve_route_material_files,
    sha256_file,
)

__all__ = [
    "DEFAULT_SEARCH_LIMIT",
    "DEFAULT_VM_STEP_BUDGET",
    "DocRecord",
    "ExcludedRecord",
    "FileStatSnapshot",
    "GenerationError",
    "INDEX_TOKENIZER",
    "IndexReader",
    "MAX_BINDINGS_RETURNED",
    "MAX_QUERY_LENGTH",
    "MAX_QUERY_TERMS",
    "MAX_SEARCH_LIMIT",
    "MAX_SEARCH_OFFSET",
    "MaterialBinding",
    "OUTLINE_NORMALIZER",
    "OUTLINE_SCHEMA_VERSION",
    "OUTLINE_TOP_DIR",
    "OutlineRecord",
    "OutlineSection",
    "SCAN_PAGE_CAP",
    "SCHEMA_VERSION",
    "SEARCH_TOP_DIR",
    "STOPWORDS",
    "SearchHit",
    "SearchResult",
    "UNSECTIONED_REASONS",
    "build_tiered_queries",
    "check_index_integrity",
    "compute_text_cache_fingerprint",
    "derive_title_from_material",
    "execute_search",
    "expand_query_names",
    "get_outline_base_dir",
    "get_search_base_dir",
    "load_outline",
    "material_bindings",
    "material_bindings_with_paths",
    "norm_token",
    "normalize_outline",
    "normalize_query_terms",
    "open_index",
    "outline_payload",
    "parse_outline_payload",
    "resolve_file_sha256",
    "sanitize_fts5_term",
]

SCHEMA_VERSION = 1
INDEX_TOKENIZER = "unicode61 remove_diacritics 2"
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50
MAX_SEARCH_OFFSET = 200
MAX_QUERY_LENGTH = 500
MAX_QUERY_TERMS = 32
MAX_BINDINGS_RETURNED = 10
VM_STEP_CALLBACK_INTERVAL = 1000
DEFAULT_VM_STEP_BUDGET = 20_000_000

#: Candidate pages scanned per query, whatever the requested window. Groups are
#: built over this one fixed scan, so a section never moves between result
#: pages and `has_more` means the same thing at every offset.
SCAN_PAGE_CAP = 1000
#: Matched pages listed per group (best-ranked first, then sorted); the exact
#: count within the scan is `pages_total`.
MAX_GROUP_PAGES = 50
#: Widest `span_pages` range, equal to `material-span`'s 20-page cap
#: (`learning_os.store.materials.slices.MAX_SLICE_PAGES`, pinned by a test).
MAX_SPAN_PAGES = 20
#: At most this many names are searched for one query: the query itself plus
#: the other registered names of the concepts it names exactly.
MAX_EXPANSION_NAMES = 8

#: The outline-section cache contract shared with tools/material_outline.py.
OUTLINE_SCHEMA_VERSION = 1
OUTLINE_NORMALIZER = "material-outline-1"
OUTLINE_STATUSES = frozenset({"present", "absent", "unreadable", "unusable"})
MAX_OUTLINE_SECTIONS = 5000
MAX_SECTION_TITLE = 200
MAX_SECTION_PATH = 8
#: Why a page belongs to its document's explicit unsectioned group.
UNSECTIONED_REASONS = (
    "before-first-heading",  # the outline starts after this page
    "no-outline",            # the PDF has no usable bookmarks
    "not-harvested",         # no outline cache entry for this digest
    "cache-invalid",         # the cache entry failed validation
)
_OUTLINE_FILE_RE = re.compile(r"^([0-9a-f]{64})\.json$")

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_INDEX_FILE_RE = re.compile(r"^index-([0-9a-f]{16})\.sqlite3$")

REQUIRED_META_KEYS = frozenset(
    {
        "schema_version",
        "tokenizer",
        "fingerprint",
        "extractor",
        "built_at",
        "documents_indexed",
        "documents_total",
        "documents_without_text",
        "pages_indexed",
        "pages_without_text",
        "pages_total",
    }
)

# High-frequency grammatical function words (German & English)
# Kept identical to the validated Stage-3c benchmark (fts5_reranker.py:20)
STOPWORDS = frozenset(
    {
        "der",
        "die",
        "das",
        "des",
        "dem",
        "den",
        "ein",
        "eine",
        "einer",
        "eines",
        "einem",
        "einen",
        "in",
        "im",
        "von",
        "vom",
        "zu",
        "zum",
        "zur",
        "mit",
        "auf",
        "an",
        "am",
        "aus",
        "bei",
        "beim",
        "und",
        "oder",
        "aber",
        "nach",
        "über",
        "uber",
        "unter",
        "vor",
        "zwischen",
        "durch",
        "für",
        "fur",
        "ist",
        "sind",
        "wird",
        "werden",
        "wie",
        "wo",
        "wer",
        "was",
        "the",
        "a",
        "and",
        "or",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "were",
        "be",
        "been",
        "that",
        "this",
        "which",
    }
)


def norm_token(text: str) -> str:
    """Normalize text using Unicode NFC, casefold, and collapsed whitespace."""
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).casefold()


def sanitize_fts5_term(term: str) -> str:
    """Escape special FTS5 characters to ensure term is safe inside double quotes."""
    return term.replace('"', '""').strip()


def normalize_query_terms(raw_query: str) -> list[str]:
    """Apply Unicode NFC and casefold before stripping punctuation (D12)."""
    normalized = unicodedata.normalize("NFC", raw_query).casefold()
    clean = re.sub(r"[^\w\s]", " ", normalized).strip()
    return [w for w in clean.split() if len(w) > 0]


def _content_words(words: Sequence[str]) -> list[str]:
    """Stopword-filtered words, or all words when every one is a stopword."""
    content = [w for w in words if w not in STOPWORDS]
    return content if content else list(words)


def build_tiered_queries(
    raw_query: str, extra_names: Sequence[str] = ()
) -> list[tuple[str, str]]:
    """Build tiered query formulations: exact phrase -> AND -> OR.

    ``extra_names`` are further normalized names of the same concept
    (``expand_query_names``). They join the phrase and conjunction tiers as
    alternatives ranked together by BM25, so every registered name of a
    concept finds the same pages; the disjunction tier stays the query's own
    words. Without extra names the tiers are exactly the single-query ones.
    """
    words = normalize_query_terms(raw_query)
    if not words:
        return []

    names = [words]
    for extra in extra_names:
        extra_words = normalize_query_terms(extra)
        if extra_words and extra_words not in names:
            names.append(extra_words)
    tiers: list[tuple[str, str]] = []

    # Tier 1: Exact Phrase. A lone query phrases only when multi-word; with
    # extra names every name joins, a single word as a one-word phrase, so no
    # name outranks another by its word count.
    phrased = names if len(names) > 1 else [name for name in names if len(name) > 1]
    phrases = [f'"{sanitize_fts5_term(" ".join(name))}"' for name in phrased]
    if phrases:
        tiers.append(("exact_phrase", " OR ".join(phrases)))

    # Tier 2: Content terms AND (one conjunction per name, alternatives ORed)
    conjunctions = [
        " AND ".join(f'"{sanitize_fts5_term(w)}"' for w in _content_words(name))
        for name in names
    ]
    if len(conjunctions) == 1:
        tiers.append(("conjunction", conjunctions[0]))
    else:
        tiers.append(("conjunction", " OR ".join(f"({c})" for c in conjunctions)))

    # Tier 3: Content terms OR (if more than 1 term) — the query's own words
    content_words = _content_words(words)
    if len(content_words) > 1:
        escaped_or_terms = [f'"{sanitize_fts5_term(w)}"' for w in content_words]
        tiers.append(("disjunction", " OR ".join(escaped_or_terms)))

    return tiers


def expand_query_names(
    raw_query: str, concepts: Mapping[str, object] | None
) -> tuple[list[str], list[str]]:
    """The query plus every other registered name of the concepts it names.

    A concept is named when the normalized query equals its normalized label
    or one of its normalized aliases (``knowledge/concepts.yaml``). Partial
    matches never expand: a word that happens to be an alias inside a longer
    question is not a request for that concept. Returns ``(names, concept
    ids)``: the normalized query first, then the matched concepts' other names
    in registry order (concepts by id), at most ``MAX_EXPANSION_NAMES`` names.
    No match returns ``([query], [])``.
    """
    query = " ".join(normalize_query_terms(raw_query))
    names = [query] if query else []
    if not query or not concepts:
        return names, []
    matched: list[str] = []
    for concept_id in sorted(concepts):
        concept = concepts[concept_id]
        if not isinstance(concept, Mapping):
            continue
        raw_names: list[object] = [concept.get("label")]
        aliases = concept.get("aliases")
        if isinstance(aliases, list):
            raw_names.extend(aliases)
        normalized = [
            " ".join(normalize_query_terms(name))
            for name in raw_names
            if isinstance(name, str)
        ]
        normalized = [name for name in normalized if name]
        if query not in normalized:
            continue
        matched.append(concept_id)
        for name in normalized:
            if name not in names and len(name.split()) <= MAX_QUERY_TERMS:
                names.append(name)
    return names[:MAX_EXPANSION_NAMES], matched


def derive_title_from_material(material: str, sha256: str) -> str:
    """Derive a human-readable document title from a material relative path."""
    if material:
        return Path(material).stem.replace("-", " ").replace("_", " ").title()
    return sha256[:12]


@dataclass(frozen=True)
class OutlineSection:
    """One PDF outline heading and the physical pages it owns.

    Pages are PDF page numbers (the viewer's page box, cover = 1). A section
    owns its start page up to the page before the next heading starts; the
    last section ends at the document's last page.
    """

    title: str
    level: int
    path: tuple[str, ...]
    start_page: int
    end_page: int

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "level": self.level,
            "path": list(self.path),
            "start_page": self.start_page,
            "end_page": self.end_page,
        }


@dataclass(frozen=True)
class OutlineRecord:
    """One document's outline sections, or why a page has none."""

    status: str
    page_total: int = 0
    sections: tuple[OutlineSection, ...] = ()

    @cached_property
    def _starts(self) -> list[int]:
        return [row.start_page for row in self.sections]

    def locate(self, page: int) -> tuple[int | None, str | None]:
        """``(section index, None)``, or ``(None, unsectioned reason)``."""
        if self.status in ("not-harvested", "cache-invalid"):
            return None, self.status
        if not self.sections:
            return None, "no-outline"
        index = bisect_right(self._starts, page) - 1
        if index < 0:
            return None, "before-first-heading"
        if page > self.sections[index].end_page:
            # The index pages came from a different page count than the
            # outline: the cache entry does not describe these bytes.
            return None, "cache-invalid"
        return index, None


def _clean_heading(title: str) -> str:
    text = unicodedata.normalize("NFC", title)
    text = "".join(ch if ch.isprintable() else " " for ch in text)
    return " ".join(text.split())[:MAX_SECTION_TITLE]


def normalize_outline(
    rows: Sequence[tuple[int, str, int | None]], page_total: int
) -> tuple[str, list[OutlineSection]]:
    """Turn raw outline rows into page-owning sections (``status, sections``).

    ``rows`` are ``(level, title, page or None)`` in outline order, as
    ``tools/material_toc.outline_rows`` reads them. Rows without a page inside
    the document, or without a title, are dropped. Ancestor paths come from
    outline order; ownership comes from page order: when several headings start
    on one page, the last one in outline order owns it (the deepest heading of
    that page). Status is ``absent`` with no rows and ``unusable`` when no row
    survives; otherwise ``present``.
    """
    if not rows:
        return "absent", []
    stack: list[str] = []
    usable: list[tuple[int, int, str, int, tuple[str, ...]]] = []
    for order, (raw_level, raw_title, page) in enumerate(rows):
        level = max(0, int(raw_level))
        title = _clean_heading(str(raw_title))
        del stack[level:]
        path = tuple(stack[-MAX_SECTION_PATH:])
        stack.append(title)
        if not title or not isinstance(page, int) or isinstance(page, bool):
            continue
        if not 1 <= page <= page_total:
            continue
        usable.append((page, order, title, level, path))
    if not usable:
        return "unusable", []
    usable.sort(key=lambda row: (row[0], row[1]))
    owners = [row for i, row in enumerate(usable)
              if i + 1 == len(usable) or usable[i + 1][0] != row[0]]
    sections: list[OutlineSection] = []
    for i, (page, _order, title, level, path) in enumerate(owners[:MAX_OUTLINE_SECTIONS]):
        end = owners[i + 1][0] - 1 if i + 1 < len(owners) else page_total
        sections.append(OutlineSection(title, level, path, page, end))
    if len(owners) > MAX_OUTLINE_SECTIONS:
        last = sections[-1]
        sections[-1] = OutlineSection(last.title, last.level, last.path,
                                      last.start_page, page_total)
    return "present", sections


def outline_payload(
    sha256: str, material: str, page_total: int, status: str,
    sections: Sequence[OutlineSection], generator: str,
) -> dict[str, object]:
    """The one cache-file shape for ``generated/material-outlines/<sha256>.json``."""
    return {
        "_generated": {
            "generator": generator,
            "warning": f"GENERATED file - do not edit; rebuilt by python {generator} --refresh",
        },
        "schema_version": OUTLINE_SCHEMA_VERSION,
        "normalizer": OUTLINE_NORMALIZER,
        "sha256": sha256,
        "material": material,
        "page_total": page_total,
        "status": status,
        "sections": [section.to_dict() for section in sections],
    }


def _strict_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def parse_outline_payload(data: object, sha256: str) -> OutlineRecord | None:
    """A validated outline record, or None when the payload is not one.

    Fails closed on any deviation from ``outline_payload``: wrong digest,
    schema or normalizer, unknown status, sections out of order, overlapping,
    or outside the page count.
    """
    if not isinstance(data, dict):
        return None
    if _strict_int(data.get("schema_version")) != OUTLINE_SCHEMA_VERSION:
        return None
    if data.get("normalizer") != OUTLINE_NORMALIZER or data.get("sha256") != sha256:
        return None
    status = data.get("status")
    page_total = _strict_int(data.get("page_total"))
    raw_sections = data.get("sections")
    if (status not in OUTLINE_STATUSES or page_total is None or page_total < 0
            or not isinstance(raw_sections, list)
            or len(raw_sections) > MAX_OUTLINE_SECTIONS
            or (status == "present") != bool(raw_sections)):
        return None
    sections: list[OutlineSection] = []
    previous_end = 0
    for row in raw_sections:
        if not isinstance(row, dict):
            return None
        title = row.get("title")
        level = _strict_int(row.get("level"))
        start = _strict_int(row.get("start_page"))
        end = _strict_int(row.get("end_page"))
        path = row.get("path")
        if (not isinstance(title, str) or not title or len(title) > MAX_SECTION_TITLE
                or level is None or level < 0 or start is None or end is None
                or not isinstance(path, list) or len(path) > MAX_SECTION_PATH
                or not all(isinstance(part, str) for part in path)
                or start <= previous_end or end < start or end > page_total):
            return None
        sections.append(OutlineSection(title, level, tuple(path), start, end))
        previous_end = end
    return OutlineRecord(str(status), page_total, tuple(sections))


def get_outline_base_dir(repo_root: Path) -> Path:
    return repo_root / "generated" / OUTLINE_TOP_DIR


def load_outline(repo_root: Path, sha256: str) -> OutlineRecord:
    """The cached outline for one digest; never raises for a bad cache entry."""
    if _HEX64_RE.match(sha256) is None:
        return OutlineRecord("cache-invalid")
    path = get_outline_base_dir(repo_root) / f"{sha256}.json"
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return OutlineRecord("not-harvested")
    except OSError:
        return OutlineRecord("cache-invalid")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return OutlineRecord("cache-invalid")
    record = parse_outline_payload(data, sha256)
    return record if record is not None else OutlineRecord("cache-invalid")


def span_pages_for(best: int, pages: Sequence[int]) -> str:
    """The house-style page range around the best page, at most 20 pages.

    Grows from ``best`` through neighbouring matched pages at most two pages
    apart, so a section's adjacent hits read as one range and a distant hit
    in the same group does not widen it.
    """
    ordered = sorted(set(pages) | {best})
    i = ordered.index(best)
    lo = hi = i
    while (lo > 0 and ordered[lo] - ordered[lo - 1] <= 2
           and ordered[hi] - ordered[lo - 1] < MAX_SPAN_PAGES):
        lo -= 1
    while (hi + 1 < len(ordered) and ordered[hi + 1] - ordered[hi] <= 2
           and ordered[hi + 1] - ordered[lo] < MAX_SPAN_PAGES):
        hi += 1
    start, end = ordered[lo], ordered[hi]
    return f"pdf p. {start}" if start == end else f"pdf pp. {start}-{end}"


@dataclass(frozen=True)
class MaterialBinding:
    module: str
    unit: str
    route: str
    single_file: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "unit": self.unit,
            "route": self.route,
            "single_file": self.single_file,
        }


@dataclass(frozen=True)
class FileStatSnapshot:
    path: str
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


@dataclass(frozen=True)
class DocRecord:
    sha256: str
    material: str
    pages_total: int
    pages_indexed: int
    pages_without_text: int


@dataclass(frozen=True)
class ExcludedRecord:
    sha256: str
    material: str
    reason: str


@dataclass(frozen=True)
class SearchHit:
    rank: int
    sha256: str
    page: int
    snippet: str
    score: float
    material: str
    title: str
    is_mapped: bool
    bindings: list[dict[str, object]]
    bindings_total: int
    span_reference: dict[str, object] | None = None
    section: dict[str, object] | None = None
    unsectioned: str | None = None
    pages: list[int] = field(default_factory=list)
    pages_total: int = 0
    span_pages: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "sha256": self.sha256,
            "page": self.page,
            "snippet": self.snippet,
            "score": self.score,
            "material": self.material,
            "title": self.title,
            "is_mapped": self.is_mapped,
            "bindings": self.bindings,
            "bindings_total": self.bindings_total,
            "span_reference": self.span_reference,
            "section": self.section,
            "unsectioned": self.unsectioned,
            "pages": self.pages,
            "pages_total": self.pages_total,
            "span_pages": self.span_pages,
        }


@dataclass
class SearchResult:
    status: str  # "ok" or "unavailable"
    query: str = ""
    has_more: bool = False
    hits: list[dict[str, object]] = field(default_factory=list)
    fingerprint: str | None = None
    freshness: dict[str, object] | None = None
    coverage: dict[str, object] | None = None
    reason: str | None = None
    message: str | None = None
    expansion: dict[str, object] | None = None
    scan_truncated: bool = False

    def to_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "contract": "material-search-v1",
            "status": self.status,
            "query": self.query,
            "has_more": self.has_more,
            "hits": self.hits,
        }
        if self.status == "ok":
            out["fingerprint"] = self.fingerprint or ""
            out["freshness"] = self.freshness or {
                "matches_text_cache": True,
                "changed_shas": [],
            }
            out["coverage"] = self.coverage or {}
            out["expansion"] = self.expansion
            out["scan_truncated"] = self.scan_truncated
        else:
            out["reason"] = self.reason
            out["message"] = self.message
        return out


class GenerationError(Exception):
    """Raised when an index file cannot be opened or validated."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


def get_search_base_dir(repo_root: Path) -> Path:
    return repo_root / "generated" / SEARCH_TOP_DIR


def compute_text_cache_fingerprint(
    valid_records: Sequence[tuple[str, int, str, Sequence[str]]],
    excluded_records: Sequence[tuple[str, str]] = (),
) -> str:
    """Compute deterministic fingerprint F of the text cache (D3).

    F = sha256(schema_version, tokenizer, sorted (sha256, pages, extractor, pages_sha256)
    of every valid cache index.json, plus sorted excluded entries).
    """
    hasher = hashlib.sha256()
    hasher.update(f"schema_v{SCHEMA_VERSION}\0{INDEX_TOKENIZER}\n".encode())
    for sha, pages, extractor, pages_sha256 in sorted(valid_records, key=lambda r: r[0]):
        joined_hashes = ",".join(pages_sha256)
        hasher.update(f"V:{sha}:{pages}:{extractor}:{joined_hashes}\n".encode())
    for sha, reason in sorted(excluded_records, key=lambda r: r[0]):
        hasher.update(f"E:{sha}:{reason}\n".encode())
    return hasher.hexdigest()


def resolve_file_sha256(
    file_path: Path,
    materials_root: Path,
    files: Mapping[str, FileStatSnapshot] | None,
    memo: dict[Path, str],
) -> str:
    """Resolve a material file's SHA-256: stat first against the index table, hash on mismatch (D7)."""
    resolved = file_path.resolve()
    cached = memo.get(resolved)
    if cached is not None:
        return cached.removeprefix("sha256:")

    if files:
        rel_key: str | None = None
        try:
            rel_key = file_path.relative_to(materials_root).as_posix()
        except ValueError:
            try:
                rel_key = resolved.relative_to(materials_root.resolve()).as_posix()
            except ValueError:
                rel_key = None
        if rel_key is not None:
            snap = files.get(rel_key)
            if snap is not None:
                try:
                    st = file_path.stat()
                    if (
                        st.st_size == snap.size
                        and st.st_mtime_ns == snap.mtime_ns
                        and st.st_ctime_ns == snap.ctime_ns
                    ):
                        memo[resolved] = f"sha256:{snap.sha256}"
                        return snap.sha256
                except OSError:
                    pass

    digest = sha256_file(file_path, memo).removeprefix("sha256:")
    return digest


def material_bindings_with_paths(
    repo: Repo,
    files: Mapping[str, FileStatSnapshot] | None = None,
    memo: dict[Path, str] | None = None,
) -> tuple[dict[str, list[MaterialBinding]], dict[str, str]]:
    """Map each material SHA-256 to all of its (module, unit, route, single_file) bindings
    and its relative path under materials/ (D7, D8, Step 5.1).
    """
    hash_memo: dict[Path, str] = memo if memo is not None else {}
    materials_root = repo.learningos_root / "materials"
    bindings_by_sha: dict[str, list[MaterialBinding]] = {}
    seen_per_sha: dict[str, set[MaterialBinding]] = {}
    sha_to_rel_path: dict[str, str] = {}

    for _unit_id, unit in sorted(repo.units.items()):
        sm = repo.module_source_maps.get(unit.module_id)
        if not isinstance(sm, dict):
            continue
        for route in unit_routes(sm, unit.module_id, unit.id):
            if not isinstance(route, dict):
                continue
            route_id = str(route.get("id") or "")
            if not route_id:
                continue
            resolved_files = resolve_route_material_files(repo, route)
            if not resolved_files:
                continue
            single_file = len(resolved_files) == 1
            for rf in resolved_files:
                fpath = Path(rf.path)
                try:
                    sha = resolve_file_sha256(fpath, materials_root, files, hash_memo)
                except OSError:
                    continue
                if sha not in sha_to_rel_path:
                    try:
                        sha_to_rel_path[sha] = fpath.relative_to(materials_root).as_posix()
                    except ValueError:
                        sha_to_rel_path[sha] = fpath.name
                binding = MaterialBinding(
                    module=unit.module_id,
                    unit=unit.id,
                    route=route_id,
                    single_file=single_file,
                )
                seen = seen_per_sha.setdefault(sha, set())
                if binding not in seen:
                    seen.add(binding)
                    bindings_by_sha.setdefault(sha, []).append(binding)

    return bindings_by_sha, sha_to_rel_path


def material_bindings(
    repo: Repo,
    files: Mapping[str, FileStatSnapshot] | None = None,
    memo: dict[Path, str] | None = None,
) -> dict[str, list[MaterialBinding]]:
    """Map each material SHA-256 to all of its (module, unit, route, single_file) bindings (Step 5.1)."""
    bindings_by_sha, _paths = material_bindings_with_paths(repo, files=files, memo=memo)
    return bindings_by_sha


class IndexReader:
    """Pins a single immutable self-describing index file in read-only mode (D4, D6, D14)."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._con: sqlite3.Connection | None = None
        self.meta: dict[str, str] = {}
        self.docs: dict[str, DocRecord] = {}
        self.files: dict[str, FileStatSnapshot] = {}
        self.cache_records: dict[str, tuple[int, int]] = {}
        self.excluded: list[ExcludedRecord] = []

    def connect(self) -> sqlite3.Connection:
        if self._con is not None:
            return self._con
        if not self.db_path.is_file():
            raise GenerationError("index_missing", f"Database file missing: {self.db_path}")

        uri = f"file:{self.db_path.resolve()}?mode=ro"
        con: sqlite3.Connection | None = None
        try:
            con = sqlite3.connect(uri, uri=True, timeout=5.0)
            cur = con.cursor()
            cur.execute("SELECT key, value FROM meta;")
            meta_rows = cur.fetchall()
            meta: dict[str, str] = {}
            for k, v in meta_rows:
                if not isinstance(k, str) or not isinstance(v, str):
                    raise GenerationError(
                        "index_corrupt", "Index meta table contains non-text values."
                    )
                meta[k] = v

            if not REQUIRED_META_KEYS.issubset(meta.keys()):
                missing = sorted(REQUIRED_META_KEYS - meta.keys())
                raise GenerationError(
                    "index_corrupt",
                    f"Index metadata table is missing required keys: {', '.join(missing)}",
                )

            try:
                schema_ver = int(meta["schema_version"])
                for int_key in (
                    "documents_indexed",
                    "documents_total",
                    "documents_without_text",
                    "pages_indexed",
                    "pages_without_text",
                    "pages_total",
                ):
                    int(meta[int_key])
            except ValueError as exc:
                raise GenerationError(
                    "index_corrupt", "Index metadata contains invalid numeric values."
                ) from exc

            if schema_ver != SCHEMA_VERSION:
                raise GenerationError(
                    "index_incompatible",
                    f"Search index schema version mismatch: expected {SCHEMA_VERSION}, got {schema_ver}. "
                    "Rebuild with `python tools/build_material_search_index.py`.",
                )

            if meta["tokenizer"] != INDEX_TOKENIZER:
                raise GenerationError(
                    "index_incompatible",
                    f"Search index tokenizer mismatch: expected {INDEX_TOKENIZER!r}, got {meta['tokenizer']!r}. "
                    "Rebuild with `python tools/build_material_search_index.py`.",
                )

            docs: dict[str, DocRecord] = {}
            cur.execute(
                "SELECT sha256, material, pages_total, pages_indexed, pages_without_text FROM docs;"
            )
            for row in cur.fetchall():
                sha = str(row[0])
                docs[sha] = DocRecord(
                    sha256=sha,
                    material=str(row[1]),
                    pages_total=int(row[2]),
                    pages_indexed=int(row[3]),
                    pages_without_text=int(row[4]),
                )

            files: dict[str, FileStatSnapshot] = {}
            cur.execute("SELECT path, size, mtime_ns, ctime_ns, sha256 FROM files;")
            for row in cur.fetchall():
                rel_p = str(row[0])
                files[rel_p] = FileStatSnapshot(
                    path=rel_p,
                    size=int(row[1]),
                    mtime_ns=int(row[2]),
                    ctime_ns=int(row[3]),
                    sha256=str(row[4]),
                )

            cache_records: dict[str, tuple[int, int]] = {}
            cur.execute("SELECT sha256, size, mtime_ns FROM cache_records;")
            for row in cur.fetchall():
                cache_records[str(row[0])] = (int(row[1]), int(row[2]))

            excluded: list[ExcludedRecord] = []
            cur.execute("SELECT sha256, material, reason FROM excluded ORDER BY sha256;")
            for row in cur.fetchall():
                excluded.append(
                    ExcludedRecord(
                        sha256=str(row[0]),
                        material=str(row[1]),
                        reason=str(row[2]),
                    )
                )

            cur.execute("SELECT 1 FROM material_fts LIMIT 0;")

            self.meta = meta
            self.docs = docs
            self.files = files
            self.cache_records = cache_records
            self.excluded = excluded
            self._con = con
            return con
        except GenerationError:
            if con is not None:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
            raise
        except (sqlite3.DatabaseError, ValueError, TypeError) as exc:
            if con is not None:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
            raise GenerationError(
                "index_corrupt", f"Cannot open or validate search index: {exc}"
            ) from exc

    def close(self) -> None:
        if self._con is not None:
            try:
                self._con.close()
            except sqlite3.Error:
                pass
            self._con = None

    def __enter__(self) -> IndexReader:
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()


def _find_newest_index_file(base_dir: Path) -> Path | None:
    if not base_dir.is_dir():
        return None
    candidates: list[tuple[int, str, Path]] = []
    for entry in base_dir.iterdir():
        if not entry.is_file() or not _INDEX_FILE_RE.match(entry.name):
            continue
        try:
            st = entry.stat()
            candidates.append((st.st_mtime_ns, entry.name, entry))
        except OSError:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def open_index(repo_root: Path, index_path: Path | None = None) -> IndexReader:
    """Open the newest published self-describing index file in read-only mode (Step 4.5)."""
    target = index_path
    if target is None:
        base_dir = get_search_base_dir(repo_root)
        target = _find_newest_index_file(base_dir)
        if target is None:
            raise GenerationError(
                "index_missing",
                "Search index has not been built. Run `python tools/build_material_search_index.py`.",
            )
    elif not target.is_file():
        raise GenerationError(
            "index_missing",
            f"Search index file does not exist: {target}",
        )

    reader = IndexReader(target)
    reader.connect()
    return reader


def check_index_integrity(
    repo_root: Path, index_path: Path | None = None
) -> tuple[str, Path, dict[str, str]]:
    """Run full SQLite and FTS5 integrity checks on the active index (D14, --check)."""
    reader = open_index(repo_root, index_path=index_path)
    db_path = reader.db_path
    meta = dict(reader.meta)
    try:
        con = reader.connect()
        cur = con.cursor()
        rows = cur.execute("PRAGMA integrity_check;").fetchall()
        if rows != [("ok",)]:
            raise GenerationError("index_corrupt", f"PRAGMA integrity_check failed: {rows}")
        row_count_row = cur.execute("SELECT count(*) FROM material_fts;").fetchone()
        row_count = int(row_count_row[0]) if row_count_row else -1
        expected_pages = int(meta["pages_indexed"])
        if row_count != expected_pages:
            raise GenerationError(
                "index_corrupt",
                f"FTS row count {row_count} does not match recorded pages_indexed {expected_pages}.",
            )
    except sqlite3.DatabaseError as exc:
        raise GenerationError("index_corrupt", f"Integrity check failed: {exc}") from exc
    finally:
        reader.close()

    # Run FTS5's internal virtual-table integrity-check command
    con_fts: sqlite3.Connection | None = None
    try:
        con_fts = sqlite3.connect(str(db_path), timeout=5.0)
        con_fts.execute(
            "INSERT INTO material_fts(material_fts, rank) VALUES('integrity-check', 1);"
        )
    except sqlite3.DatabaseError as exc:
        raise GenerationError("index_corrupt", f"FTS5 integrity-check failed: {exc}") from exc
    finally:
        if con_fts is not None:
            try:
                con_fts.close()
            except sqlite3.Error:
                pass

    return meta["fingerprint"], db_path, meta


def _compute_text_cache_freshness(
    repo_root: Path, recorded_cache: Mapping[str, tuple[int, int]]
) -> dict[str, object]:
    """Compare recorded cache index.json stats with current text-cache directory (D6, D7, Step 4.5)."""
    cache_dir = repo_root / "generated" / "text-cache"
    live_stats: dict[str, tuple[int, int]] = {}
    if cache_dir.is_dir():
        try:
            for entry in sorted(cache_dir.iterdir()):
                if entry.is_dir() and _HEX64_RE.match(entry.name) is not None:
                    idx_file = entry / "index.json"
                    try:
                        st = idx_file.stat()
                        live_stats[entry.name] = (st.st_size, st.st_mtime_ns)
                    except OSError:
                        live_stats[entry.name] = (-1, -1)
        except OSError:
            pass

    all_shas = sorted(set(recorded_cache.keys()) | set(live_stats.keys()))
    changed_shas: list[str] = []
    for sha in all_shas:
        rec = recorded_cache.get(sha)
        live = live_stats.get(sha)
        if rec is None or live is None or rec != live:
            changed_shas.append(sha)

    return {
        "matches_text_cache": len(changed_shas) == 0,
        "changed_shas": changed_shas,
    }


def _build_coverage_block(
    reader: IndexReader,
    bindings_by_sha: Mapping[str, Sequence[MaterialBinding]],
    route_sha_to_path: Mapping[str, str],
    dead_shas: set[str],
    unit_id: str | None,
    module_id: str | None,
) -> dict[str, object]:
    """Build the response coverage block (D9, Step 5.4)."""
    docs_without_text: list[dict[str, object]] = []
    for sha in sorted(reader.docs.keys()):
        doc = reader.docs[sha]
        if doc.pages_indexed == 0:
            docs_without_text.append(
                {
                    "sha256": doc.sha256,
                    "material": doc.material,
                    "pages_total": doc.pages_total,
                    "pages_without_text": doc.pages_without_text,
                }
            )

    excluded_entries: list[dict[str, object]] = [
        {
            "sha256": ex.sha256,
            "material": ex.material,
            "reason": ex.reason,
        }
        for ex in reader.excluded
    ]
    excluded_by_sha = {ex.sha256: ex for ex in reader.excluded}

    unindexed_route_materials: list[dict[str, object]] = []
    unindexed_route_shas: set[str] = set()

    for sha in sorted(bindings_by_sha.keys()):
        mat_path = route_sha_to_path.get(sha, "")
        # Non-PDF materials are out of scope for PDF text-cache indexing (§8 Q2)
        if mat_path and not mat_path.lower().endswith(".pdf"):
            continue
        doc_rec = reader.docs.get(sha)
        reason: str | None = None
        if sha in excluded_by_sha:
            ex_reason = excluded_by_sha[sha].reason
            reason = (
                "legacy — run --refresh"
                if ex_reason == "legacy — run --refresh"
                else "cache-entry-invalid"
            )
        elif doc_rec is None:
            reason = "not-in-text-cache"
        elif doc_rec.pages_indexed == 0:
            reason = "no-text"

        if reason is not None:
            unindexed_route_shas.add(sha)
            b_list = bindings_by_sha[sha]
            unindexed_route_materials.append(
                {
                    "sha256": sha,
                    "material": mat_path,
                    "reason": reason,
                    "bindings": [b.to_dict() for b in b_list[:MAX_BINDINGS_RETURNED]],
                    "bindings_total": len(b_list),
                }
            )

    if unit_id is not None or module_id is not None:
        scope_complete = True
        for sha, b_list in bindings_by_sha.items():
            mat_path = route_sha_to_path.get(sha, "")
            if mat_path and not mat_path.lower().endswith(".pdf"):
                continue
            in_scope = any(
                (unit_id is None or b.unit == unit_id)
                and (module_id is None or b.module == module_id)
                for b in b_list
            )
            if in_scope and (sha in unindexed_route_shas or sha in dead_shas):
                scope_complete = False
                break
    else:
        scope_complete = len(unindexed_route_materials) == 0

    return {
        "documents_indexed": int(reader.meta["documents_indexed"]),
        "documents_total": int(reader.meta["documents_total"]),
        "pages_indexed": int(reader.meta["pages_indexed"]),
        "pages_without_text": int(reader.meta["pages_without_text"]),
        "pages_total": int(reader.meta["pages_total"]),
        "documents_without_text": docs_without_text,
        "excluded_cache_entries": excluded_entries,
        "unindexed_route_materials": unindexed_route_materials,
        "scope_complete": scope_complete,
    }


def _select_span_reference(
    sha: str,
    page: int,
    bindings: Sequence[MaterialBinding],
    unit_id: str | None,
    module_id: str | None,
) -> dict[str, object] | None:
    """Build span_reference from a single-file binding (D17, L5)."""
    single_bindings = [b for b in bindings if b.single_file]
    if not single_bindings:
        return None

    chosen = single_bindings[0]
    if unit_id is not None or module_id is not None:
        for b in single_bindings:
            if (unit_id is None or b.unit == unit_id) and (
                module_id is None or b.module == module_id
            ):
                chosen = b
                break

    return {
        "unit": chosen.unit,
        "route": chosen.route,
        "pages": f"pdf p. {page}",
        "extract": True,
        "file_sha256": f"sha256:{sha}",
    }


def _validate_search_request(query: str, limit: int, offset: int) -> str:
    """Validate bounded search arguments and return the stripped query string."""
    if not isinstance(query, str) or not query.strip():
        raise WriteRefused(
            "material.search requires a nonempty query",
            site="material.search.empty-query",
            prefixed=True,
            exit_code=2,
        )
    if len(query) > MAX_QUERY_LENGTH:
        raise WriteRefused(
            f"query length {len(query)} exceeds maximum of {MAX_QUERY_LENGTH} characters",
            site="material.search.query-too-long",
            prefixed=True,
            exit_code=2,
        )
    if (
        not isinstance(offset, int)
        or isinstance(offset, bool)
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or offset < 0
        or offset > MAX_SEARCH_OFFSET
        or not (1 <= limit <= MAX_SEARCH_LIMIT)
    ):
        raise WriteRefused(
            f"offset must be between 0 and {MAX_SEARCH_OFFSET} and limit between 1 and {MAX_SEARCH_LIMIT}",
            site="material.search.offset-too-large",
            prefixed=True,
            exit_code=2,
        )

    clean_query = query.strip()
    terms = normalize_query_terms(clean_query)
    if not terms:
        raise WriteRefused(
            "material.search query contains no searchable terms after normalization",
            site="material.search.no-terms",
            prefixed=True,
            exit_code=2,
        )
    if len(terms) > MAX_QUERY_TERMS:
        raise WriteRefused(
            f"material.search query has {len(terms)} terms after normalization (maximum is {MAX_QUERY_TERMS})",
            site="material.search.too-many-terms",
            prefixed=True,
            exit_code=2,
        )
    return clean_query


def _load_and_validate_repo(
    repo_root: Path, repo: Repo | None, unit_id: str | None, module_id: str | None
) -> Repo | None:
    """Load the Repo if needed and refuse unknown unit_id / module_id filters."""
    loaded_repo = repo
    if loaded_repo is None and (repo_root / "curriculum").is_dir():
        try:
            loaded_repo = load_repo(repo_root)
        except Exception:
            loaded_repo = None

    if loaded_repo is not None:
        if unit_id is not None and unit_id not in loaded_repo.units:
            complaint = with_suggestions(f"unknown unit: {unit_id!r}", unit_id, loaded_repo.units)
            raise NotFound(
                "unit",
                unit_id,
                loaded_repo.units,
                message=complaint,
                site="material.search.unknown-unit",
                gateway_message=f"los: {complaint}",
                exit_code=2,
            )
        if module_id is not None and module_id not in loaded_repo.modules:
            complaint = with_suggestions(
                f"unknown module: {module_id!r}", module_id, loaded_repo.modules
            )
            raise NotFound(
                "module",
                module_id,
                loaded_repo.modules,
                message=complaint,
                site="material.search.unknown-module",
                gateway_message=f"los: {complaint}",
                exit_code=2,
            )
    return loaded_repo


def _resolve_live_bindings_and_scope(
    repo_root: Path,
    loaded_repo: Repo | None,
    reader: IndexReader,
    unit_id: str | None,
    module_id: str | None,
) -> tuple[
    dict[str, list[MaterialBinding]],
    dict[str, str],
    set[str],
    set[str] | None,
]:
    """Compute live route bindings, dead SHAs, and optional scope filter SHAs."""
    memo: dict[Path, str] = {}
    bindings_by_sha: dict[str, list[MaterialBinding]] = {}
    route_sha_to_path: dict[str, str] = {}
    if loaded_repo is not None:
        bindings_by_sha, route_sha_to_path = material_bindings_with_paths(
            loaded_repo, files=reader.files, memo=memo
        )

    materials_root = repo_root.parent / "materials"
    dead_shas: set[str] = set()
    if materials_root.is_dir() and (reader.files or bindings_by_sha):
        live_shas: set[str] = set(bindings_by_sha.keys())
        for rel_path in reader.files:
            pdf_path = materials_root / rel_path
            if pdf_path.is_file() and not pdf_path.is_symlink():
                try:
                    live_shas.add(resolve_file_sha256(pdf_path, materials_root, reader.files, memo))
                except OSError:
                    continue
        dead_shas = set(reader.docs.keys()) - live_shas

    allowed_shas: set[str] | None = None
    if unit_id is not None or module_id is not None:
        allowed_shas = {
            sha
            for sha, b_list in bindings_by_sha.items()
            if sha not in dead_shas
            and any(
                (unit_id is None or b.unit == unit_id)
                and (module_id is None or b.module == module_id)
                for b in b_list
            )
        }
    return bindings_by_sha, route_sha_to_path, dead_shas, allowed_shas


def _query_fts_hits(
    reader: IndexReader,
    repo_root: Path,
    clean_query: str,
    extra_names: Sequence[str],
    limit: int,
    offset: int,
    unit_id: str | None,
    module_id: str | None,
    bindings_by_sha: Mapping[str, Sequence[MaterialBinding]],
    route_sha_to_path: Mapping[str, str],
    dead_shas: set[str],
    allowed_shas: set[str] | None,
    vm_step_budget: int,
) -> tuple[bool, bool, list[dict[str, object]]]:
    """Run tiered FTS5 queries, group pages by outline section, page over groups.

    One scan of at most ``SCAN_PAGE_CAP`` candidate pages, whatever the
    window, so groups and their order are identical at every offset. A group
    is one document's section (or its explicit unsectioned group); it ranks at
    its best page, and the window is ``groups[offset : offset + limit]``.
    Returns ``(has_more, scan_truncated, hits)``.
    """
    con = reader.connect()
    steps_taken = 0
    budget_exceeded = False
    step_interval = min(VM_STEP_CALLBACK_INTERVAL, max(1, vm_step_budget))

    def _progress_handler() -> int:
        nonlocal steps_taken, budget_exceeded
        steps_taken += step_interval
        if steps_taken > vm_step_budget:
            budget_exceeded = True
            return 1
        return 0

    con.set_progress_handler(_progress_handler, step_interval)
    cur = con.cursor()

    where_parts = ["material_fts MATCH ?"]
    filter_params: list[str] = []
    if allowed_shas is not None:
        sorted_allowed = sorted(allowed_shas)
        where_parts.append(f"sha256 IN ({', '.join('?' for _ in sorted_allowed)})")
        filter_params.extend(sorted_allowed)
    if dead_shas:
        sorted_dead = sorted(dead_shas)
        where_parts.append(f"sha256 NOT IN ({', '.join('?' for _ in sorted_dead)})")
        filter_params.extend(sorted_dead)

    rank_sql = (
        f"SELECT rowid, sha256, page_no, bm25(material_fts) AS score "
        f"FROM material_fts WHERE {' AND '.join(where_parts)} "
        f"ORDER BY rank, sha256, page_no LIMIT ?;"
    )
    snippet_sql = (
        "SELECT snippet(material_fts, 0, '[', ']', ' … ', 20) "
        "FROM material_fts WHERE material_fts MATCH ? AND rowid = ?;"
    )

    raw_candidates: list[tuple[int, str, int, float, str]] = []
    seen_keys: set[tuple[str, int]] = set()

    try:
        for _tier_name, fts_expr in build_tiered_queries(clean_query, extra_names):
            if len(raw_candidates) > SCAN_PAGE_CAP:
                break
            cur.execute(rank_sql, (fts_expr, *filter_params, SCAN_PAGE_CAP + 1))
            for row in cur.fetchall():
                rowid, sha, page_no, score = int(row[0]), str(row[1]), int(row[2]), float(row[3])
                key = (sha, page_no)
                if key not in seen_keys:
                    seen_keys.add(key)
                    raw_candidates.append((rowid, sha, page_no, score, fts_expr))
                    if len(raw_candidates) > SCAN_PAGE_CAP:
                        break
        scan_truncated = len(raw_candidates) > SCAN_PAGE_CAP
        candidates = raw_candidates[:SCAN_PAGE_CAP]

        outlines: dict[str, OutlineRecord] = {}
        groups: dict[tuple[str, int], list[tuple[int, str, int, float, str]]] = {}
        located: dict[tuple[str, int], tuple[int | None, str | None]] = {}
        for candidate in candidates:
            sha, page_no = candidate[1], candidate[2]
            outline = outlines.get(sha)
            if outline is None:
                outline = load_outline(repo_root, sha)
                outlines[sha] = outline
            index, reason = outline.locate(page_no)
            group_key = (sha, -1 if index is None else index)
            if group_key not in groups:
                groups[group_key] = []
                located[group_key] = (index, reason)
            groups[group_key].append(candidate)

        ordered_keys = list(groups)
        has_more = len(ordered_keys) > (offset + limit)
        hits: list[dict[str, object]] = []
        for rank_idx, group_key in enumerate(
            ordered_keys[offset : offset + limit], start=offset + 1
        ):
            members = groups[group_key]
            rowid, sha, page_no, score, fts_expr = members[0]
            cur.execute(snippet_sql, (fts_expr, rowid))
            snip_row = cur.fetchone()
            snippet_text = str(snip_row[0]) if snip_row and snip_row[0] is not None else ""
            doc_rec = reader.docs.get(sha)
            material_rel = (
                doc_rec.material
                if doc_rec is not None and doc_rec.material
                else route_sha_to_path.get(sha, "")
            )
            sha_bindings = bindings_by_sha.get(sha, [])
            index, reason = located[group_key]
            listed = sorted(member[2] for member in members[:MAX_GROUP_PAGES])
            hit = SearchHit(
                rank=rank_idx,
                sha256=sha,
                page=page_no,
                snippet=snippet_text,
                score=round(score, 4),
                material=material_rel,
                title=derive_title_from_material(material_rel, sha),
                is_mapped=len(sha_bindings) > 0,
                bindings=[b.to_dict() for b in sha_bindings[:MAX_BINDINGS_RETURNED]],
                bindings_total=len(sha_bindings),
                span_reference=_select_span_reference(
                    sha=sha,
                    page=page_no,
                    bindings=sha_bindings,
                    unit_id=unit_id,
                    module_id=module_id,
                ),
                section=(
                    outlines[sha].sections[index].to_dict() if index is not None else None
                ),
                unsectioned=reason,
                pages=listed,
                pages_total=len(members),
                span_pages=span_pages_for(page_no, listed),
            )
            hits.append(hit.to_dict())
        return has_more, scan_truncated, hits
    except sqlite3.DatabaseError as exc:
        if budget_exceeded:
            raise WriteRefused(
                "material.search query exceeded the VM-step budget; narrow the query terms",
                site="material.search.query-too-expensive",
                prefixed=True,
                exit_code=2,
            ) from exc
        raise GenerationError(
            "index_corrupt", f"Database error during search query: {exc}"
        ) from exc


def execute_search(
    repo_root: Path,
    query: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
    offset: int = 0,
    unit_id: str | None = None,
    module_id: str | None = None,
    repo: Repo | None = None,
    index_path: Path | None = None,
    vm_step_budget: int = DEFAULT_VM_STEP_BUDGET,
) -> SearchResult:
    """Execute a bounded search query over the self-describing FTS5 index."""
    clean_query = _validate_search_request(query, limit, offset)
    loaded_repo = _load_and_validate_repo(repo_root, repo, unit_id, module_id)
    names, expanded_concepts = expand_query_names(
        clean_query, loaded_repo.concepts if loaded_repo is not None else None
    )
    expansion: dict[str, object] | None = (
        {"concepts": expanded_concepts, "names": names} if expanded_concepts else None
    )

    try:
        reader = open_index(repo_root, index_path=index_path)
    except GenerationError as err:
        return SearchResult(
            status="unavailable",
            reason=err.reason,
            message=err.message,
            query=clean_query,
        )

    try:
        bindings_by_sha, route_sha_to_path, dead_shas, allowed_shas = (
            _resolve_live_bindings_and_scope(repo_root, loaded_repo, reader, unit_id, module_id)
        )
        freshness = _compute_text_cache_freshness(repo_root, reader.cache_records)
        coverage = _build_coverage_block(
            reader=reader,
            bindings_by_sha=bindings_by_sha,
            route_sha_to_path=route_sha_to_path,
            dead_shas=dead_shas,
            unit_id=unit_id,
            module_id=module_id,
        )

        if allowed_shas is not None and not allowed_shas:
            return SearchResult(
                status="ok",
                query=clean_query,
                has_more=False,
                hits=[],
                fingerprint=reader.meta["fingerprint"],
                freshness=freshness,
                coverage=coverage,
                expansion=expansion,
            )

        try:
            has_more, scan_truncated, hits = _query_fts_hits(
                reader=reader,
                repo_root=repo_root,
                clean_query=clean_query,
                extra_names=names[1:],
                limit=limit,
                offset=offset,
                unit_id=unit_id,
                module_id=module_id,
                bindings_by_sha=bindings_by_sha,
                route_sha_to_path=route_sha_to_path,
                dead_shas=dead_shas,
                allowed_shas=allowed_shas,
                vm_step_budget=vm_step_budget,
            )
        except GenerationError as err:
            return SearchResult(
                status="unavailable",
                reason=err.reason,
                message=err.message,
                query=clean_query,
            )

        return SearchResult(
            status="ok",
            query=clean_query,
            has_more=has_more,
            hits=hits,
            fingerprint=reader.meta["fingerprint"],
            freshness=freshness,
            coverage=coverage,
            expansion=expansion,
            scan_truncated=scan_truncated,
        )
    finally:
        reader.close()
