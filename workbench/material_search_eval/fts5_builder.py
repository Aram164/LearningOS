#!/usr/bin/env python3
"""FTS5 Index Builder for LearningOS Material Search Research Spike.

Builds isolated SQLite FTS5 index variants over generated/text-cache/:
1. unicode61: standard SQLite FTS5 with diacritic removal
2. prefix: unicode61 with pre-indexed prefixes (prefix='2 3 4')
3. trigram: 3-gram substring index for compound words and partial matching

All indices are disposable research artifacts stored in workbench/material_search_eval/indices/.
Zero modifications to Core, canonical data, or repo schemas.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.store.loading import load_repo
from learning_os.domain.material_refs import unit_routes
from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file

TEXT_CACHE_DIR = REPO_ROOT / "generated" / "text-cache"
INDICES_DIR = SCRIPT_DIR / "indices"


def load_metadata_mapping(repo) -> dict[str, dict[str, str]]:
    """Build sha256 -> {source_id, title} lookup from repo units and routes."""
    sha_map: dict[str, dict[str, str]] = {}
    for unit_id, unit in repo.units.items():
        sm = repo.module_source_maps.get(unit.module_id)
        if not sm:
            continue
        for r in unit_routes(sm, unit.module_id, unit.id):
            files = resolve_route_material_files(repo, r)
            for f in files:
                sha = sha256_file(Path(f.path)).removeprefix("sha256:")
                sid = r.get("source_id") or ""
                title = r.get("title") or (repo.sources.get(sid, {}).get("title") if sid else "") or ""
                if sha not in sha_map or not sha_map[sha].get("title"):
                    sha_map[sha] = {"source_id": sid, "title": title}
    return sha_map


def get_all_cached_pages() -> list[tuple[str, int, Path]]:
    """Collect all (sha256, page_no, path) tuples from text-cache."""
    pages = []
    if not TEXT_CACHE_DIR.exists():
        return pages
    for sha_dir in sorted(TEXT_CACHE_DIR.iterdir()):
        if not sha_dir.is_dir():
            continue
        sha = sha_dir.name
        for pfile in sorted(sha_dir.glob("pp-*.txt")):
            try:
                pno = int(pfile.stem.replace("pp-", ""))
                pages.append((sha, pno, pfile))
            except ValueError:
                continue
    return pages


def build_index(
    variant: str,
    pages: list[tuple[str, int, Path]],
    metadata_map: dict[str, dict[str, str]],
    dest_path: Path,
    batch_size: int = 5000
) -> dict[str, Any]:
    """Build a specific FTS5 database variant."""
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        dest_path.unlink()

    print(f"Building FTS5 index [{variant}] -> {dest_path.name}...")
    t0 = time.perf_counter()

    con = sqlite3.connect(dest_path)
    cur = con.cursor()

    # Fast insertion pragma settings for temporary index creation
    cur.execute("PRAGMA journal_mode = OFF;")
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA cache_size = -64000;")  # 64MB cache
    cur.execute("PRAGMA temp_store = MEMORY;")

    # Define schema based on variant
    if variant == "unicode61":
        schema_sql = """
        CREATE VIRTUAL TABLE material_fts USING fts5(
            source_sha256 UNINDEXED,
            page_no UNINDEXED,
            source_id UNINDEXED,
            title,
            body,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    elif variant == "prefix":
        schema_sql = """
        CREATE VIRTUAL TABLE material_fts USING fts5(
            source_sha256 UNINDEXED,
            page_no UNINDEXED,
            source_id UNINDEXED,
            title,
            body,
            tokenize='unicode61 remove_diacritics 2',
            prefix='2 3 4'
        );
        """
    elif variant == "trigram":
        schema_sql = """
        CREATE VIRTUAL TABLE material_fts USING fts5(
            source_sha256 UNINDEXED,
            page_no UNINDEXED,
            source_id UNINDEXED,
            title,
            body,
            tokenize='trigram'
        );
        """
    else:
        raise ValueError(f"Unknown variant: {variant}")

    cur.execute(schema_sql)

    # Insert rows in batches
    insert_sql = "INSERT INTO material_fts(source_sha256, page_no, source_id, title, body) VALUES (?, ?, ?, ?, ?);"
    batch = []
    total_inserted = 0

    for sha, pno, pfile in pages:
        try:
            body = pfile.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            body = ""
        meta = metadata_map.get(sha, {})
        source_id = meta.get("source_id", "")
        title = meta.get("title", "")
        batch.append((sha, pno, source_id, title, body))

        if len(batch) >= batch_size:
            cur.executemany(insert_sql, batch)
            total_inserted += len(batch)
            batch.clear()

    if batch:
        cur.executemany(insert_sql, batch)
        total_inserted += len(batch)
        batch.clear()

    con.commit()

    # Integrity check
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    con.close()

    elapsed = time.perf_counter() - t0
    file_size_bytes = dest_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    stats = {
        "variant": variant,
        "database_file": str(dest_path),
        "total_pages": total_inserted,
        "build_time_seconds": round(elapsed, 3),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "integrity_check": integrity
    }
    print(f"[{variant}] Completed in {elapsed:.2f}s | Size: {file_size_mb:.2f} MB | Pages: {total_inserted} | Integrity: {integrity}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Build SQLite FTS5 Material Search Indices")
    parser.add_argument(
        "--variant",
        choices=["unicode61", "prefix", "trigram", "all"],
        default="all",
        help="Tokenizer variant to build"
    )
    args = parser.parse_args()

    print("Loading LearningOS repository metadata...")
    repo = load_repo(REPO_ROOT)
    metadata_map = load_metadata_mapping(repo)
    print(f"Loaded metadata for {len(metadata_map)} mapped materials.")

    print(f"Scanning text-cache in {TEXT_CACHE_DIR}...")
    pages = get_all_cached_pages()
    print(f"Found {len(pages)} pages across {len(set(p[0] for p in pages))} unique SHAs.")

    variants_to_build = ["unicode61", "prefix", "trigram"] if args.variant == "all" else [args.variant]
    results = {}

    for var in variants_to_build:
        dest = INDICES_DIR / f"fts5_{var}.sqlite3"
        stats = build_index(var, pages, metadata_map, dest)
        results[var] = stats

    stats_file = INDICES_DIR / "build_stats.json"
    stats_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nAll requested indices built successfully. Stats written to {stats_file.name}")


if __name__ == "__main__":
    main()
