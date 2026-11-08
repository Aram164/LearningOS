"""FTS5 Reranker and Query-Parsing Module for LearningOS Material Search.

Provides:
1. Query-Parsing Strategies:
   - raw: phrase OR conjunct OR disjunct
   - tiered_stopword: exact phrase -> AND content words -> OR content words
2. Candidate Diversification:
   - unlimited (standard)
   - max_per_sha(k) (at most k pages per document SHA)
3. Content Filtering:
   - is_index_page(body): detects back-of-the-book index / bibliography pages
"""

from __future__ import annotations

import re
from typing import Any

# Standard German and English stopwords (function words only, preserving domain terms)
STOPWORDS = {
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
    "an",
    "and",
    "or",
    "in",
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
    "was",
    "were",
    "be",
    "been",
    "that",
    "this",
    "which",
}


def sanitize_tokens(text: str) -> list[str]:
    """Extract alphanumeric words while preserving formulas and accented characters."""
    clean = re.sub(r"[^\w\s]", " ", text).strip()
    return [w for w in clean.split() if len(w) > 0]


def is_index_or_toc_page(body: str) -> bool:
    """Heuristic to detect index/bibliography/TOC pages with high symbol/page-number density."""
    if not body:
        return False
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if not lines:
        return False

    first_few = " ".join(lines[:5]).lower()
    if any(
        h in first_few
        for h in [
            "sachregister",
            "stichwortverzeichnis",
            "symbolverzeichnis",
            "inhaltsverzeichnis",
            "author index",
            "subject index",
        ]
    ):
        return True

    # Check dot leader density (e.g. 'Chapter 1 . . . . . 12') or comma-number density
    dot_leaders = sum(1 for l in lines if ". . ." in l or "..." in l)
    if dot_leaders > 4:
        return True

    # Index page indicator: very high density of numbers following commas
    comma_numbers = len(re.findall(r",\s*\d{1,4}", body))
    if comma_numbers > 8:
        return True

    return False


def build_tiered_queries(raw_query: str) -> list[tuple[str, str]]:
    """Generate tiered query expressions: (tier_name, fts_query_string)."""
    words = sanitize_tokens(raw_query)
    clean_phrase = " ".join(words)
    content_words = [w for w in words if w.lower() not in STOPWORDS]
    if not content_words:
        content_words = words

    tiers = []
    # Tier 1: Exact Phrase
    if len(words) > 1 and clean_phrase:
        tiers.append(("exact_phrase", f'"{clean_phrase}"'))

    # Tier 2: Conjunction of content words (AND)
    if len(content_words) > 1:
        and_expr = " AND ".join(f'"{w}"' for w in content_words)
        tiers.append(("conjunction", and_expr))
    elif len(content_words) == 1:
        tiers.append(("single_word", f'"{content_words[0]}"'))

    # Tier 3: Disjunction of content words (OR)
    if len(content_words) > 1:
        or_expr = " OR ".join(f'"{w}"' for w in content_words)
        tiers.append(("disjunction", or_expr))

    return tiers


def apply_diversification_and_reranking(
    raw_candidates: list[dict[str, Any]],
    max_per_sha: int = 2,
    penalize_index_pages: bool = True,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Rerank candidates with document diversification and index-page demotion."""
    # Annotate index pages
    processed = []
    for cand in raw_candidates:
        c = dict(cand)
        is_idx = is_index_or_toc_page(c.get("body", ""))
        c["is_index_page"] = is_idx
        score = c.get("score", 0.0)
        if penalize_index_pages and is_idx:
            # Demote index pages by adding a positive penalty (in FTS5 BM25, more negative = better)
            score = score * 0.5  # shrinks negative magnitude
        c["adjusted_score"] = score
        processed.append(c)

    # Sort by adjusted score ascending (lower/more negative is better rank)
    processed.sort(key=lambda x: x["adjusted_score"])

    # Apply diversification (max per SHA)
    diversified = []
    sha_counts: dict[str, int] = {}

    for cand in processed:
        sha = cand.get("source_sha256")
        count = sha_counts.get(sha, 0)
        if max_per_sha is None or count < max_per_sha:
            diversified.append(cand)
            sha_counts[sha] = count + 1
        if len(diversified) >= limit:
            break

    return diversified
