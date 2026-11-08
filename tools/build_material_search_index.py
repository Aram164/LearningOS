#!/usr/bin/env python3
"""Build and atomically publish disposable SQLite FTS5 material search index generations.

Usage:
    python tools/build_material_search_index.py [--force] [--check]

Architecture:
- Disposable, immutable generations under `generated/material-search/generations/<gen_id>/`
- Atomically published via `generated/material-search/current.json`
- Ingests text cache from `generated/text-cache/`
- Maps source SHAs to LearningOS canonical unit routes
- Preserves physical PDF page numbers and UTF-8 tokenization (unicode61)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.domain.material_refs import unit_routes  # noqa: E402
from learning_os.store.loading import load_repo  # noqa: E402
from learning_os.store.manifest_identity import (  # noqa: E402
    materials_digest as compute_live_materials_digest,
)
from learning_os.store.materials.resolution import (  # noqa: E402
    resolve_route_material_files,
    sha256_file,
)
from learning_os.store.materials.search_index import (  # noqa: E402
    EXTRACTOR_NAME,
    INDEX_TOKENIZER,
    SCHEMA_VERSION,
    GenerationError,
    compute_corpus_fingerprint,
    get_search_base_dir,
    open_pinned_generation,
)

BATCH_SIZE = 5000
MAX_GENERATIONS_KEPT = 3


def _generated_header(tool: str = "tools/build_material_search_index.py") -> dict:
    """The warning block every generated JSON file must carry (GEN-HEADER)."""
    return {
        "_generated": {
            "generator": tool,
            "warning": f"GENERATED file - do not edit; rebuilt by python {tool}",
        }
    }


def build_sha_route_map(repo) -> dict[str, tuple[str, str, str]]:
    """Map SHA-256 to (unit_id, route_id, module_id) for authoritative route resolution."""
    mapping = {}
    for _unit_id, unit in repo.units.items():
        sm = repo.module_source_maps.get(unit.module_id)
        if not sm:
            continue
        for r in unit_routes(sm, unit.module_id, unit.id):
            files = resolve_route_material_files(repo, r)
            for f in files:
                sha = sha256_file(Path(f.path)).removeprefix("sha256:")
                if sha not in mapping:
                    mapping[sha] = (unit.id, r.get("id"), unit.module_id)
    return mapping


def build_index_generation(repo_root: Path, force: bool = False) -> tuple[str, Path, dict]:
    """Build a complete, verified index generation and atomically publish it."""
    t0 = time.perf_counter()
    base_dir = get_search_base_dir(repo_root)
    generations_dir = base_dir / "generations"
    generations_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = repo_root / "generated" / "text-cache"
    if not cache_dir.exists():
        raise SystemExit(
            f"Text cache missing at {cache_dir}. Run `python tools/material_text.py --build` first."
        )

    manifest_file = repo_root / "generated" / "manifest.json"
    manifest_identity_file = repo_root / "generated" / "manifest.identity.json"
    materials_digest_val = ""
    manifest_sha256_val = ""
    if manifest_identity_file.exists():
        try:
            m_id = json.loads(manifest_identity_file.read_text(encoding="utf-8"))
            materials_digest_val = m_id.get("materials_digest", "")
            manifest_sha256_val = m_id.get("manifest_sha256", "")
        except Exception:
            pass
    if not materials_digest_val:
        try:
            materials_digest_val = compute_live_materials_digest(repo_root.resolve())
        except Exception:
            materials_digest_val = ""

    corpus_fingerprint = compute_corpus_fingerprint(repo_root, manifest_file)
    gen_id = f"gen_{corpus_fingerprint[:16]}"
    final_gen_dir = generations_dir / gen_id
    current_pointer = base_dir / "current.json"

    # Check if this exact generation is already built, published, and fresh
    if not force and final_gen_dir.exists() and current_pointer.exists():
        try:
            curr_data = json.loads(current_pointer.read_text(encoding="utf-8"))
            gen_meta_file = final_gen_dir / "generation.json"
            if curr_data.get("generation_id") == gen_id and gen_meta_file.exists():
                gen_meta = json.loads(gen_meta_file.read_text(encoding="utf-8"))
                mat_fresh = (not materials_digest_val) or (
                    gen_meta.get("materials_digest") == materials_digest_val
                )
                man_fresh = (not manifest_sha256_val) or (
                    gen_meta.get("manifest_sha256") == manifest_sha256_val
                )
                has_audit = (final_gen_dir / "blank_pages.json").exists()
                if mat_fresh and man_fresh and has_audit:
                    print(f"Index generation {gen_id} is already current, fresh, and published.")
                    return gen_id, final_gen_dir, curr_data
        except Exception:
            pass

    tmp_gen_dir = generations_dir / f"{gen_id}.tmp"
    if tmp_gen_dir.exists():
        shutil.rmtree(tmp_gen_dir)
    tmp_gen_dir.mkdir(parents=True, exist_ok=True)

    db_path = tmp_gen_dir / "search.sqlite3"
    print(f"Building index generation {gen_id}...")

    # Load repository context for route mappings
    print("Loading LearningOS repository routes...")
    repo = load_repo(repo_root)
    sha_to_route = build_sha_route_map(repo)
    print(f"Resolved {len(sha_to_route)} material SHAs to canonical unit routes.")

    # Create SQLite FTS5 table
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode = OFF;")
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute(f"""
    CREATE VIRTUAL TABLE material_fts USING fts5(
        source_sha256 UNINDEXED,
        page_no UNINDEXED,
        source_id UNINDEXED,
        body,
        tokenize = '{INDEX_TOKENIZER}'
    );
    """)

    insert_sql = """
    INSERT INTO material_fts (source_sha256, page_no, source_id, body)
    VALUES (?, ?, ?, ?);
    """

    total_pages_scanned = 0
    blank_pages_skipped = 0
    blank_pages_list: list[dict[str, Any]] = []
    total_docs = 0
    batch = []

    print("Ingesting page text cache...")
    for d in sorted(cache_dir.iterdir()):
        if not d.is_dir() or len(d.name) != 64:
            continue
        sha = d.name
        idx_file = d / "index.json"
        doc_title = sha[:12]
        doc_source_id = ""

        if idx_file.exists():
            try:
                meta = json.loads(idx_file.read_text(encoding="utf-8"))
                mat_path = meta.get("material", "")
                if mat_path:
                    doc_title = Path(mat_path).stem.replace("-", " ").replace("_", " ").title()
            except Exception:
                pass

        if sha in sha_to_route:
            uid, rid, mid = sha_to_route[sha]
            doc_source_id = f"{uid}:{rid}"

        total_docs += 1
        for p in sorted(d.glob("pp-*.txt")):
            total_pages_scanned += 1
            try:
                page_no = int(p.stem.split("-")[1])
                body_text = p.read_text(encoding="utf-8", errors="ignore")
                if not body_text.strip():
                    blank_pages_skipped += 1
                    blank_pages_list.append(
                        {
                            "source_sha256": sha,
                            "page_no": page_no,
                            "title": doc_title,
                            "reason": "empty_or_whitespace",
                        }
                    )
                    continue
                batch.append((sha, page_no, doc_source_id, body_text))
                if len(batch) >= BATCH_SIZE:
                    cur.executemany(insert_sql, batch)
                    con.commit()
                    batch.clear()
            except (ValueError, OSError):
                continue

    if batch:
        cur.executemany(insert_sql, batch)
        con.commit()
        batch.clear()

    indexed_pages = total_pages_scanned - blank_pages_skipped
    print(
        f"Optimizing FTS5 index across {indexed_pages:,} indexed pages "
        f"({blank_pages_skipped:,} blank pages skipped from {total_pages_scanned:,} scanned)..."
    )
    cur.execute("INSERT INTO material_fts(material_fts) VALUES('optimize');")
    con.commit()
    con.close()

    # Save machine-readable blank pages audit manifest
    blank_manifest = {
        **_generated_header(),
        "generation_id": gen_id,
        "total_pages_scanned": total_pages_scanned,
        "blank_pages_skipped": blank_pages_skipped,
        "indexed_pages": indexed_pages,
        "blank_pages": blank_pages_list,
    }
    (tmp_gen_dir / "blank_pages.json").write_text(
        json.dumps(blank_manifest, indent=2), encoding="utf-8"
    )

    # Generation metadata
    meta = {
        **_generated_header(),
        "generation_id": gen_id,
        "built_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "extractor": EXTRACTOR_NAME,
        "corpus_fingerprint": corpus_fingerprint,
        "materials_digest": materials_digest_val,
        "manifest_sha256": manifest_sha256_val,
        "total_documents": total_docs,
        "total_pages_scanned": total_pages_scanned,
        "blank_pages_skipped": blank_pages_skipped,
        "indexed_pages": indexed_pages,
        "total_pages": indexed_pages,
        "mapped_routes_count": len(sha_to_route),
        "tokenizer": INDEX_TOKENIZER,
        "db_size_bytes": db_path.stat().st_size,
    }
    (tmp_gen_dir / "generation.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Atomic rename of generation directory
    if final_gen_dir.exists():
        shutil.rmtree(final_gen_dir)
    tmp_gen_dir.rename(final_gen_dir)

    # Atomic update of current.json pointer
    pointer_tmp = base_dir / "current.json.tmp"
    pointer_data = {
        **_generated_header(),
        "generation_id": gen_id,
        "published_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "db_file": f"generations/{gen_id}/search.sqlite3",
    }
    pointer_tmp.write_text(json.dumps(pointer_data, indent=2), encoding="utf-8")
    pointer_tmp.replace(current_pointer)

    # Prune old generations
    existing_gens = sorted(generations_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_gen in existing_gens[MAX_GENERATIONS_KEPT:]:
        if old_gen.is_dir() and old_gen.name != gen_id:
            try:
                shutil.rmtree(old_gen)
            except OSError:
                pass

    elapsed = time.perf_counter() - t0
    print(
        f"Published generation {gen_id} in {elapsed:.1f}s ({meta['db_size_bytes'] / (1024 * 1024):.1f} MB, {indexed_pages:,} pages)."
    )
    return gen_id, final_gen_dir, meta


def main():
    parser = argparse.ArgumentParser(description="Build and publish material search index.")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if generation is current."
    )
    parser.add_argument(
        "--check", action="store_true", help="Verify current index availability without building."
    )
    args = parser.parse_args()

    if args.check:
        try:
            reader = open_pinned_generation(REPO_ROOT)
            print(
                f"Current generation: {reader.generation_id} (OK, {reader.db_path.stat().st_size / (1024 * 1024):.1f} MB)"
            )
            reader.close()
            sys.exit(0)
        except GenerationError as err:
            print(f"Index unavailable: {err.reason} - {err.message}", file=sys.stderr)
            sys.exit(1)

    build_index_generation(REPO_ROOT, force=args.force)


if __name__ == "__main__":
    main()
