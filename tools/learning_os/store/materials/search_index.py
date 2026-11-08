"""Material search index lifecycle, freshness verification, and query execution.

Architecture (ADR-020):
- Single self-describing read-only SQLite FTS5 file per text-cache identity:
  `generated/material-search/index-<F[:16]>.sqlite3`
- Pure text index: `material_fts(body, sha256 UNINDEXED, page_no UNINDEXED)`
  with `unicode61 remove_diacritics 2` tokenization
- Per-call route bindings and live file freshness checks (stat first, hash on mismatch)
- Coverage and text-cache freshness disclosure on every response
- Bounded input validation, deferred snippet computation, and VM-step budget backstop
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.material_refs import unit_routes
from learning_os.domain.snapshot import Repo
from learning_os.domain.suggest import with_suggestions
from learning_os.domain.validation import SEARCH_TOP_DIR
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
    "SCHEMA_VERSION",
    "SEARCH_TOP_DIR",
    "STOPWORDS",
    "SearchHit",
    "SearchResult",
    "build_tiered_queries",
    "check_index_integrity",
    "compute_text_cache_fingerprint",
    "derive_title_from_material",
    "execute_search",
    "get_search_base_dir",
    "material_bindings",
    "material_bindings_with_paths",
    "norm_token",
    "normalize_query_terms",
    "open_index",
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

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_INDEX_FILE_RE = re.compile(r"^index-([0-9a-f]{16})\.sqlite3$")

REQUIRED_META_KEYS = frozenset({
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
})

# High-frequency grammatical function words (German & English)
# Kept identical to the validated Stage-3c benchmark (fts5_reranker.py:20)
STOPWORDS = frozenset({
    "der", "die", "das", "des", "dem", "den", "ein", "eine", "einer", "eines", "einem", "einen",
    "in", "im", "von", "vom", "zu", "zum", "zur", "mit", "auf", "an", "am", "aus", "bei", "beim",
    "und", "oder", "aber", "nach", "über", "uber", "unter", "vor", "zwischen", "durch", "für", "fur",
    "ist", "sind", "wird", "werden", "wie", "wo", "wer", "was",
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "is", "are", "was", "were", "be", "been", "that", "this", "which",
})


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


def build_tiered_queries(raw_query: str) -> list[tuple[str, str]]:
    """Build tiered query formulations: exact phrase -> AND -> OR."""
    words = normalize_query_terms(raw_query)
    if not words:
        return []

    clean = " ".join(words)
    tiers: list[tuple[str, str]] = []

    # Tier 1: Exact Phrase (if multi-word)
    if len(words) > 1:
        escaped_phrase = sanitize_fts5_term(clean)
        tiers.append(("exact_phrase", f'"{escaped_phrase}"'))

    # Filter stopwords for conjunction and disjunction
    content_words = [w for w in words if w not in STOPWORDS]
    if not content_words:
        content_words = words

    # Tier 2: Content terms AND
    escaped_and_terms = [f'"{sanitize_fts5_term(w)}"' for w in content_words]
    tiers.append(("conjunction", " AND ".join(escaped_and_terms)))

    # Tier 3: Content terms OR (if more than 1 term)
    if len(content_words) > 1:
        tiers.append(("disjunction", " OR ".join(escaped_and_terms)))

    return tiers


def derive_title_from_material(material: str, sha256: str) -> str:
    """Derive a human-readable document title from a material relative path."""
    if material:
        return Path(material).stem.replace("-", " ").replace("_", " ").title()
    return sha256[:12]


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
                    raise GenerationError("index_corrupt", "Index meta table contains non-text values.")
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
        con_fts.execute("INSERT INTO material_fts(material_fts, rank) VALUES('integrity-check', 1);")
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
            docs_without_text.append({
                "sha256": doc.sha256,
                "material": doc.material,
                "pages_total": doc.pages_total,
                "pages_without_text": doc.pages_without_text,
            })

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
            reason = "cache-entry-invalid"
        elif doc_rec is None:
            reason = "not-in-text-cache"
        elif doc_rec.pages_indexed == 0:
            reason = "no-text"

        if reason is not None:
            unindexed_route_shas.add(sha)
            b_list = bindings_by_sha[sha]
            unindexed_route_materials.append({
                "sha256": sha,
                "material": mat_path,
                "reason": reason,
                "bindings": [b.to_dict() for b in b_list[:MAX_BINDINGS_RETURNED]],
                "bindings_total": len(b_list),
            })

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

    loaded_repo = repo
    if loaded_repo is None and (repo_root / "curriculum").is_dir():
        try:
            loaded_repo = load_repo(repo_root)
        except Exception:
            loaded_repo = None

    if loaded_repo is not None:
        if unit_id is not None and unit_id not in loaded_repo.units:
            complaint = with_suggestions(
                f"unknown unit: {unit_id!r}", unit_id, loaded_repo.units
            )
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
            for rel_path, snap in reader.files.items():
                pdf_path = materials_root / rel_path
                if pdf_path.is_file() and not pdf_path.is_symlink():
                    try:
                        sha = resolve_file_sha256(pdf_path, materials_root, reader.files, memo)
                        live_shas.add(sha)
                    except OSError:
                        continue
            dead_shas = set(reader.docs.keys()) - live_shas

        allowed_shas: set[str] | None = None
        if unit_id is not None or module_id is not None:
            allowed_shas = set()
            for sha, b_list in bindings_by_sha.items():
                if sha in dead_shas:
                    continue
                if any(
                    (unit_id is None or b.unit == unit_id)
                    and (module_id is None or b.module == module_id)
                    for b in b_list
                ):
                    allowed_shas.add(sha)

        freshness = _compute_text_cache_freshness(repo_root, reader.cache_records)
        coverage = _build_coverage_block(
            reader=reader,
            bindings_by_sha=bindings_by_sha,
            route_sha_to_path=route_sha_to_path,
            dead_shas=dead_shas,
            unit_id=unit_id,
            module_id=module_id,
        )

        if allowed_shas is not None and len(allowed_shas) == 0:
            return SearchResult(
                status="ok",
                query=clean_query,
                has_more=False,
                hits=[],
                fingerprint=reader.meta["fingerprint"],
                freshness=freshness,
                coverage=coverage,
            )

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

        tiers = build_tiered_queries(clean_query)
        fetch_cap = offset + limit + 1
        raw_candidates: list[tuple[int, str, int, float, str]] = []
        seen_keys: set[tuple[str, int]] = set()

        where_parts = ["material_fts MATCH ?"]
        filter_params: list[str] = []
        if allowed_shas is not None:
            sorted_allowed = sorted(allowed_shas)
            placeholders = ", ".join("?" for _ in sorted_allowed)
            where_parts.append(f"sha256 IN ({placeholders})")
            filter_params.extend(sorted_allowed)
        if dead_shas:
            sorted_dead = sorted(dead_shas)
            placeholders = ", ".join("?" for _ in sorted_dead)
            where_parts.append(f"sha256 NOT IN ({placeholders})")
            filter_params.extend(sorted_dead)

        where_clause = " AND ".join(where_parts)
        rank_sql = (
            f"SELECT rowid, sha256, page_no, bm25(material_fts) AS score "
            f"FROM material_fts WHERE {where_clause} "
            f"ORDER BY rank, sha256, page_no LIMIT ?;"
        )

        try:
            for _tier_name, fts_expr in tiers:
                if len(raw_candidates) >= fetch_cap:
                    break
                cur.execute(rank_sql, (fts_expr, *filter_params, fetch_cap))
                for row in cur.fetchall():
                    rowid = int(row[0])
                    sha = str(row[1])
                    page_no = int(row[2])
                    score = float(row[3])
                    key = (sha, page_no)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        raw_candidates.append((rowid, sha, page_no, score, fts_expr))
                        if len(raw_candidates) >= fetch_cap:
                            break

            has_more = len(raw_candidates) > (offset + limit)
            paged_candidates = raw_candidates[offset : offset + limit]

            snippet_sql = (
                "SELECT snippet(material_fts, 0, '[', ']', ' … ', 20) "
                "FROM material_fts WHERE material_fts MATCH ? AND rowid = ?;"
            )

            hits: list[dict[str, object]] = []
            for rank_idx, (rowid, sha, page_no, score, fts_expr) in enumerate(
                paged_candidates, start=offset + 1
            ):
                cur.execute(snippet_sql, (fts_expr, rowid))
                snip_row = cur.fetchone()
                snippet_text = str(snip_row[0]) if snip_row and snip_row[0] is not None else ""

                doc_rec = reader.docs.get(sha)
                material_rel = (
                    doc_rec.material
                    if doc_rec is not None and doc_rec.material
                    else route_sha_to_path.get(sha, "")
                )
                title = derive_title_from_material(material_rel, sha)

                sha_bindings = bindings_by_sha.get(sha, [])
                is_mapped = len(sha_bindings) > 0
                span_ref = _select_span_reference(
                    sha=sha,
                    page=page_no,
                    bindings=sha_bindings,
                    unit_id=unit_id,
                    module_id=module_id,
                )

                hit = SearchHit(
                    rank=rank_idx,
                    sha256=sha,
                    page=page_no,
                    snippet=snippet_text,
                    score=round(score, 4),
                    material=material_rel,
                    title=title,
                    is_mapped=is_mapped,
                    bindings=[b.to_dict() for b in sha_bindings[:MAX_BINDINGS_RETURNED]],
                    bindings_total=len(sha_bindings),
                    span_reference=span_ref,
                )
                hits.append(hit.to_dict())

        except sqlite3.DatabaseError as exc:
            if budget_exceeded:
                raise WriteRefused(
                    "material.search query exceeded the VM-step budget; narrow the query terms",
                    site="material.search.query-too-expensive",
                    prefixed=True,
                    exit_code=2,
                ) from exc
            return SearchResult(
                status="unavailable",
                reason="index_corrupt",
                message=f"Database error during search query: {exc}",
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
        )
    finally:
        reader.close()
