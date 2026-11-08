"""Material search index lifecycle, generation management, and query execution.

Stage 4 Production Integration:
- Disposable, immutable index generations under `generated/material-search/generations/<gen_id>/`
- Atomic generation publication via `generated/material-search/current.json`
- Readers pin a single immutable generation in read-only mode (`mode=ro`)
- Validated Stage-3c `Tiered_Stopwords` ranking over SQLite FTS5 (unicode61)
- Explicit route mapping and span references for downstream `material.span` retrieval
- Bounded input sanitization, bounded result payloads, and robust error classification
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
INDEX_TOKENIZER = "unicode61"
EXTRACTOR_NAME = "pdftotext+pypdf"
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50
MAX_QUERY_LENGTH = 500

# High-frequency grammatical function words (German & English)
# Kept identical to the validated Stage-3c benchmark
STOPWORDS = frozenset({
    # German stopwords
    "der", "die", "das", "ein", "eine", "einer", "einem", "einen", "eines",
    "und", "oder", "aber", "denn", "weil", "wenn", "als", "wie", "so",
    "in", "im", "an", "am", "auf", "aus", "bei", "beim", "mit", "nach",
    "von", "vom", "zu", "zum", "zur", "über", "unter", "vor", "zwischen",
    "durch", "für", "gegen", "ohne", "um", "ist", "sind", "war", "waren",
    "wird", "werden", "wurde", "wurden", "hat", "haben", "hatte", "hatten",
    "kann", "können", "konnte", "muss", "müssen", "musste", "soll", "sollte",
    "nicht", "kein", "keine", "keinem", "keinen", "keiner", "keines",
    "ich", "du", "er", "sie", "es", "wir", "ihr", "man", "sich", "was", "wer",
    "wo", "wann", "warum", "welche", "welcher", "welches", "welchem",
    "diese", "dieser", "dieses", "diesem", "diesen", "jenes", "jener",
    # English stopwords
    "the", "a", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from",
    "up", "down", "out", "on", "off", "over", "under", "again",
    "is", "are", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "can", "could", "shall", "should",
    "will", "would", "may", "might", "must", "not", "no", "nor", "too",
    "very", "just", "where", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "than", "that", "this", "these",
    "those", "what", "which", "who", "whom", "why"
})


def norm_token(text: str) -> str:
    """Normalize text using Unicode NFC, lowercased, and collapsed whitespace."""
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


def sanitize_fts5_term(term: str) -> str:
    """Escape special FTS5 characters to ensure term is safe inside double quotes."""
    return term.replace('"', '""').strip()


def build_tiered_queries(raw_query: str) -> list[tuple[str, str]]:
    """Build tiered query formulations: exact phrase -> AND -> OR.

    Reused verbatim from validated Stage 3c.
    """
    clean = re.sub(r"[^\w\s]", " ", raw_query).strip()
    words = [w for w in clean.split() if len(w) > 0]
    if not words:
        return []

    tiers: list[tuple[str, str]] = []

    # Tier 1: Exact Phrase (if multi-word)
    if len(words) > 1:
        escaped_phrase = sanitize_fts5_term(clean)
        tiers.append(("exact_phrase", f'"{escaped_phrase}"'))

    # Filter stopwords for conjunction and disjunction
    content_words = [w for w in words if norm_token(w) not in STOPWORDS]
    if not content_words:
        content_words = words

    # Tier 2: Content terms AND
    escaped_and_terms = [f'"{sanitize_fts5_term(w)}"' for w in content_words]
    tiers.append(("conjunction", " AND ".join(escaped_and_terms)))

    # Tier 3: Content terms OR (if more than 1 term)
    if len(content_words) > 1:
        tiers.append(("disjunction", " OR ".join(escaped_and_terms)))

    return tiers


@dataclass
class SearchHit:
    rank: int
    score: float
    source_sha256: str
    physical_page: int
    source_id: str
    title: str
    snippet: str
    is_mapped: bool
    route: dict[str, str] | None = None
    span_reference: dict[str, str] | None = None


@dataclass
class SearchResult:
    status: str  # "ok" or "unavailable"
    reason: str | None = None
    message: str | None = None
    generation_id: str | None = None
    query: str = ""
    total_hits: int = 0
    hits: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.status == "ok":
            data.pop("reason", None)
            data.pop("message", None)
        return data


class GenerationError(Exception):
    """Raised when an index generation cannot be read or validated."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


def get_search_base_dir(repo_root: Path) -> Path:
    return repo_root / "generated" / "material-search"


def compute_corpus_fingerprint(repo_root: Path, manifest_path: Path | None = None) -> str:
    """Compute deterministic hash of the material corpus and text cache."""
    cache_dir = repo_root / "generated" / "text-cache"
    hasher = hashlib.sha256()
    hasher.update(f"schema_v{SCHEMA_VERSION}_{INDEX_TOKENIZER}".encode())

    if manifest_path and manifest_path.exists():
        try:
            m_bytes = manifest_path.read_bytes()
            hasher.update(m_bytes)
        except OSError:
            pass

    if cache_dir.exists():
        # Hash sorted directory entries and their index.json files
        for entry in sorted(cache_dir.iterdir()):
            if entry.is_dir() and len(entry.name) == 64:
                idx_file = entry / "index.json"
                if idx_file.exists():
                    try:
                        hasher.update(idx_file.read_bytes())
                    except OSError:
                        pass
    return hasher.hexdigest()


class IndexGenerationReader:
    """Pins a single immutable index generation for the duration of a search operation."""

    def __init__(self, generation_id: str, db_path: Path, metadata: dict[str, Any]):
        self.generation_id = generation_id
        self.db_path = db_path
        self.metadata = metadata
        self._con: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._con is not None:
            return self._con
        if not self.db_path.exists():
            raise GenerationError("index_corrupt", f"Database file missing: {self.db_path}")

        # Strictly read-only connection URI
        uri = f"file:{self.db_path.resolve()}?mode=ro"
        try:
            con = sqlite3.connect(uri, uri=True, timeout=5.0)
            cur = con.cursor()
            cur.execute("SELECT 1 FROM material_fts LIMIT 0;")
            self._con = con
            return con
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
            raise GenerationError(
                "index_corrupt", f"Cannot open index in read-only mode: {exc}"
            ) from exc

    def close(self):
        if self._con:
            try:
                self._con.close()
            except Exception:
                pass
            self._con = None

    def __enter__(self) -> IndexGenerationReader:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def verify_generation_freshness(repo_root: Path, meta: dict[str, Any]) -> None:
    """Ensure generation matches declared schema, extractor, and live material corpus."""
    gen_schema = meta.get("schema_version")
    if gen_schema is not None and gen_schema != SCHEMA_VERSION:
        raise GenerationError(
            "index_stale",
            f"Search index schema version mismatch: expected {SCHEMA_VERSION}, got {gen_schema}. "
            "Rebuild with `python tools/build_material_search_index.py`.",
        )

    gen_extractor = meta.get("extractor")
    if gen_extractor is not None and gen_extractor != EXTRACTOR_NAME:
        raise GenerationError(
            "index_stale",
            f"Search index extractor mismatch: expected {EXTRACTOR_NAME}, got {gen_extractor}. "
            "Rebuild with `python tools/build_material_search_index.py`.",
        )

    identity_path = repo_root / "generated" / "manifest.identity.json"
    if identity_path.exists():
        try:
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            curr_mat_digest = identity.get("materials_digest")
            curr_man_sha = identity.get("manifest_sha256")
            gen_mat_digest = meta.get("materials_digest")
            gen_man_sha = meta.get("manifest_sha256")

            if gen_mat_digest and curr_mat_digest and gen_mat_digest != curr_mat_digest:
                raise GenerationError(
                    "index_stale",
                    f"Search index is stale: materials corpus changed (index: {gen_mat_digest[:12]}, live: {curr_mat_digest[:12]}). "
                    "Rebuild with `python tools/build_material_search_index.py` or pass --allow-stale.",
                )
            if gen_man_sha and curr_man_sha and gen_man_sha != curr_man_sha:
                raise GenerationError(
                    "index_stale",
                    f"Search index is stale: manifest changed (index: {gen_man_sha[:12]}, live: {curr_man_sha[:12]}). "
                    "Rebuild with `python tools/build_material_search_index.py` or pass --allow-stale.",
                )
        except GenerationError:
            raise
        except Exception:
            pass


def open_pinned_generation(repo_root: Path, allow_stale: bool = False) -> IndexGenerationReader:
    """Read current pointer and return a pinned read-only reader for the active generation."""
    base_dir = get_search_base_dir(repo_root)
    current_pointer = base_dir / "current.json"

    if not current_pointer.exists():
        raise GenerationError(
            "index_missing",
            "Search index has not been built. Run `python tools/build_material_search_index.py`.",
        )

    try:
        pointer_data = json.loads(current_pointer.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GenerationError("index_corrupt", f"Corrupt current.json pointer: {exc}") from exc

    gen_id = pointer_data.get("generation_id")
    if not gen_id:
        raise GenerationError("index_corrupt", "current.json missing generation_id.")

    gen_dir = base_dir / "generations" / gen_id
    db_path = gen_dir / "search.sqlite3"
    meta_path = gen_dir / "generation.json"

    if not gen_dir.exists() or not db_path.exists():
        raise GenerationError(
            "index_missing", f"Pinned generation directory or database missing: {gen_dir}"
        )

    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if not allow_stale:
        verify_generation_freshness(repo_root, meta)

    reader = IndexGenerationReader(generation_id=gen_id, db_path=db_path, metadata=meta)
    reader.connect()
    return reader


def execute_search(
    repo_root: Path,
    query: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
    offset: int = 0,
    unit_id: str | None = None,
    module_id: str | None = None,
    sha_to_route: dict[str, tuple[str, str, str]] | None = None,
    allow_stale: bool = False,
) -> SearchResult:
    """Execute a search query over the pinned index generation."""
    clean_query = query.strip()
    if not clean_query:
        return SearchResult(status="ok", query=clean_query, total_hits=0, hits=[])

    if len(clean_query) > MAX_QUERY_LENGTH:
        clean_query = clean_query[:MAX_QUERY_LENGTH]

    limit = max(1, min(limit, MAX_SEARCH_LIMIT))
    offset = max(0, offset)

    try:
        reader = open_pinned_generation(repo_root, allow_stale=allow_stale)
    except GenerationError as err:
        return SearchResult(
            status="unavailable", reason=err.reason, message=err.message, query=clean_query
        )

    try:
        con = reader.connect()
        cur = con.cursor()

        tiers = build_tiered_queries(clean_query)
        raw_candidates = []
        seen_keys = set()

        for _tier_name, fts_expr in tiers:
            if len(raw_candidates) >= (offset + limit * 3):
                break
            sql = """
            SELECT source_sha256, page_no, source_id, title,
                   bm25(material_fts) AS score,
                   snippet(material_fts, 4, '[', ']', ' … ', 20) AS excerpt
            FROM material_fts
            WHERE material_fts MATCH ?
            ORDER BY rank
            LIMIT ?;
            """
            try:
                cur.execute(sql, (fts_expr, offset + limit * 3))
                for r in cur.fetchall():
                    key = (r[0], int(r[1]))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        raw_candidates.append(
                            {
                                "source_sha256": r[0],
                                "physical_page": int(r[1]),
                                "source_id": r[2],
                                "title": r[3],
                                "score": float(r[4]),
                                "snippet": r[5],
                            }
                        )
            except sqlite3.OperationalError:
                # FTS5 syntax or query structure error, continue to next tier
                continue

        # Optional filtering by unit / module if sha_to_route is provided
        filtered_candidates = []
        for cand in raw_candidates:
            sha = cand["source_sha256"]
            mapping = sha_to_route.get(sha) if sha_to_route else None
            cand_uid = mapping[0] if mapping else None
            cand_mid = mapping[2] if mapping else None

            if unit_id and cand_uid != unit_id:
                continue
            if module_id and cand_mid != module_id:
                continue
            filtered_candidates.append((cand, mapping))

        paged_candidates = filtered_candidates[offset : offset + limit]

        hits: list[dict[str, Any]] = []
        for rank_idx, (cand, mapping) in enumerate(paged_candidates, start=offset + 1):
            sha = cand["source_sha256"]
            page = cand["physical_page"]
            is_mapped = mapping is not None

            route_info = None
            span_ref = None
            if is_mapped and mapping:
                uid, rid, mid = mapping
                route_info = {"unit_id": uid, "route_id": rid, "module_id": mid}
                span_ref = {"unit_id": uid, "route_id": rid, "pages": f"pdf p. {page}"}

            hit = SearchHit(
                rank=rank_idx,
                score=round(cand["score"], 4),
                source_sha256=sha,
                physical_page=page,
                source_id=cand["source_id"] or "",
                title=cand["title"] or "",
                snippet=cand["snippet"] or "",
                is_mapped=is_mapped,
                route=route_info,
                span_reference=span_ref,
            )
            hits.append(asdict(hit))

        return SearchResult(
            status="ok",
            generation_id=reader.generation_id,
            query=clean_query,
            total_hits=len(filtered_candidates),
            hits=hits,
        )

    finally:
        reader.close()
