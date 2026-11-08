#!/usr/bin/env python3
"""Build and atomically publish the self-describing SQLite FTS5 material search index.

Usage:
    python tools/build_material_search_index.py [--force] [--check] [--root ROOT]

Architecture (ADR-020):
- Single self-describing file per text-cache identity:
  `generated/material-search/index-<F[:16]>.sqlite3`
- Pure text index (`material_fts(body, sha256 UNINDEXED, page_no UNINDEXED)`)
- Serialized by `fcntl.flock` on `generated/material-search/.build.lock` (exit 3 if busy)
- Validates every text-cache entry via `material_text.cache_index` and `_index_valid`
- Verifies SQLite and FTS5 integrity before atomic `os.replace` publication
"""

from __future__ import annotations

import argparse
import datetime as _dt
import errno
import fcntl
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from material_text import EXTRACTOR, _index_valid, cache_index  # noqa: E402
from materials_manifest import load_manifest  # noqa: E402

from learning_os.store.materials.resolution import sha256_file  # noqa: E402
from learning_os.store.materials.search_index import (  # noqa: E402
    INDEX_TOKENIZER,
    SCHEMA_VERSION,
    DocRecord,
    ExcludedRecord,
    FileStatSnapshot,
    GenerationError,
    check_index_integrity,
    compute_text_cache_fingerprint,
    get_search_base_dir,
    open_index,
)

BATCH_SIZE = 5000
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _read_raw_material_path(idx_file: Path) -> str:
    try:
        raw = json.loads(idx_file.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("material"), str):
            return str(raw["material"])
    except (OSError, ValueError):
        pass
    return ""


def _inventory_pdf_paths(repo_root: Path) -> list[tuple[str, Path]]:
    """Return sorted (rel_posix_path, abs_path) for every inventory PDF present on disk."""
    materials_dir = repo_root.parent / "materials"
    if not materials_dir.is_dir():
        return []

    manifest_file = repo_root / "records" / "materials-manifest.yaml"
    manifest_data = load_manifest(manifest_file) if manifest_file.is_file() else None
    result: list[tuple[str, Path]] = []

    if isinstance(manifest_data, dict) and isinstance(manifest_data.get("files"), dict):
        for rel_path in sorted(manifest_data["files"].keys()):
            rel_str = str(rel_path)
            if not rel_str.lower().endswith(".pdf"):
                continue
            abs_path = materials_dir / rel_str
            if abs_path.is_file() and not abs_path.is_symlink():
                result.append((rel_str, abs_path))
    else:
        for abs_path in sorted(materials_dir.rglob("*.pdf")):
            if abs_path.is_file() and not abs_path.is_symlink():
                rel_str = abs_path.relative_to(materials_dir).as_posix()
                result.append((rel_str, abs_path))

    return result


def _is_already_current(
    repo_root: Path,
    target_path: Path,
    fingerprint: str,
    cache_stats: dict[str, tuple[int, int]],
    pdf_paths: list[tuple[str, Path]],
) -> tuple[bool, dict[str, str]]:
    """Check whether target_path exists, is valid, and every recorded stat is unchanged."""
    if not target_path.is_file():
        return False, {}
    try:
        reader = open_index(repo_root, index_path=target_path)
    except GenerationError:
        return False, {}

    try:
        if reader.meta.get("fingerprint") != fingerprint:
            return False, {}
        if reader.cache_records != cache_stats:
            return False, {}
        if set(reader.files.keys()) != {rel for rel, _ in pdf_paths}:
            return False, {}
        for rel_str, abs_path in pdf_paths:
            snap = reader.files.get(rel_str)
            if snap is None:
                return False, {}
            try:
                st = abs_path.stat()
            except OSError:
                return False, {}
            if (
                st.st_size != snap.size
                or st.st_mtime_ns != snap.mtime_ns
                or st.st_ctime_ns != snap.ctime_ns
            ):
                return False, {}
        return True, dict(reader.meta)
    finally:
        reader.close()


def _fsync_file(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def build_index_generation(
    repo_root: Path, force: bool = False
) -> tuple[str, Path, dict[str, object]]:
    """Build a complete, verified self-describing index file and atomically publish it."""
    t0 = time.perf_counter()
    repo_root = repo_root.resolve()
    cache_dir = repo_root / "generated" / "text-cache"
    if not cache_dir.is_dir():
        raise SystemExit(
            f"Text cache missing at {cache_dir}. Run `python tools/material_text.py --refresh` first."
        )

    base_dir = get_search_base_dir(repo_root)
    base_dir.mkdir(parents=True, exist_ok=True)
    lock_path = base_dir / ".build.lock"

    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                print(
                    f"Another material search index build is already holding {lock_path}.",
                    file=sys.stderr,
                )
                raise SystemExit(3) from exc
            raise

        # Step 4.4 (2): Remove stale .build-* files now that we hold the lock
        for stale_tmp in base_dir.glob(".build-*"):
            try:
                if stale_tmp.is_dir():
                    shutil.rmtree(stale_tmp)
                else:
                    stale_tmp.unlink(missing_ok=True)
            except OSError:
                pass

        # Step 4.3: Validate each 64-hex cache entry and collect pages
        cache_stats: dict[str, tuple[int, int]] = {}
        valid_fp_inputs: list[tuple[str, int, str, list[str]]] = []
        excluded_records: list[ExcludedRecord] = []
        valid_entries: list[tuple[str, str, int]] = []

        for entry in sorted(cache_dir.iterdir()):
            if not entry.is_dir() or _HEX64_RE.match(entry.name) is None:
                continue
            sha = entry.name
            idx_file = entry / "index.json"
            try:
                st = idx_file.stat()
                cache_stats[sha] = (st.st_size, st.st_mtime_ns)
            except OSError:
                cache_stats[sha] = (-1, -1)

            record = cache_index(cache_dir, sha)
            if record is None:
                excluded_records.append(
                    ExcludedRecord(
                        sha256=sha,
                        material=_read_raw_material_path(idx_file),
                        reason="cache-entry-invalid",
                    )
                )
                continue

            material_rel = str(record.get("material") or "")
            rec_extractor = str(record.get("extractor") or "")
            if rec_extractor != EXTRACTOR:
                excluded_records.append(
                    ExcludedRecord(
                        sha256=sha,
                        material=material_rel,
                        reason="extractor-mismatch",
                    )
                )
                continue

            pages_val = record.get("pages")
            pages_sha_val = record.get("pages_sha256")
            if (
                not isinstance(pages_val, int)
                or isinstance(pages_val, bool)
                or pages_val < 0
                or not isinstance(pages_sha_val, list)
                or not all(isinstance(x, str) for x in pages_sha_val)
            ):
                excluded_records.append(
                    ExcludedRecord(
                        sha256=sha,
                        material=material_rel,
                        reason="cache-entry-invalid",
                    )
                )
                continue

            if not _index_valid(cache_dir, sha, pages_val):
                excluded_records.append(
                    ExcludedRecord(
                        sha256=sha,
                        material=material_rel,
                        reason="cache-entry-invalid",
                    )
                )
                continue

            valid_fp_inputs.append(
                (sha, pages_val, rec_extractor, [str(x) for x in pages_sha_val])
            )
            valid_entries.append((sha, material_rel, pages_val))

        # Verify strict UTF-8 decoding and read page texts per valid entry
        doc_records: list[DocRecord] = []
        fts_rows: list[tuple[str, str, int]] = []
        still_valid_fp: list[tuple[str, int, str, list[str]]] = []
        fp_by_sha = {item[0]: item for item in valid_fp_inputs}

        total_pages_indexed = 0
        total_pages_without_text = 0
        documents_indexed = 0
        documents_without_text = 0

        for sha, material_rel, pages_total in valid_entries:
            entry_dir = cache_dir / sha
            entry_rows: list[tuple[str, str, int]] = []
            doc_indexed = 0
            doc_without_text = 0
            decode_failed = False

            for page_no in range(1, pages_total + 1):
                page_file = entry_dir / f"pp-{page_no:04d}.txt"
                try:
                    body_text = page_file.read_text(encoding="utf-8", errors="strict")
                except (OSError, UnicodeDecodeError):
                    decode_failed = True
                    break
                if body_text.strip():
                    entry_rows.append((body_text, sha, page_no))
                    doc_indexed += 1
                else:
                    doc_without_text += 1

            if decode_failed:
                excluded_records.append(
                    ExcludedRecord(
                        sha256=sha,
                        material=material_rel,
                        reason="cache-entry-invalid",
                    )
                )
                continue

            still_valid_fp.append(fp_by_sha[sha])
            fts_rows.extend(entry_rows)
            total_pages_indexed += doc_indexed
            total_pages_without_text += doc_without_text
            if doc_indexed > 0:
                documents_indexed += 1
            else:
                documents_without_text += 1

            doc_records.append(
                DocRecord(
                    sha256=sha,
                    material=material_rel,
                    pages_total=pages_total,
                    pages_indexed=doc_indexed,
                    pages_without_text=doc_without_text,
                )
            )

        excluded_records.sort(key=lambda r: r.sha256)
        fingerprint = compute_text_cache_fingerprint(
            still_valid_fp,
            [(ex.sha256, ex.reason) for ex in excluded_records],
        )
        f16 = fingerprint[:16]
        target_path = base_dir / f"index-{f16}.sqlite3"
        pdf_paths = _inventory_pdf_paths(repo_root)

        if not force:
            is_curr, existing_meta = _is_already_current(
                repo_root=repo_root,
                target_path=target_path,
                fingerprint=fingerprint,
                cache_stats=cache_stats,
                pdf_paths=pdf_paths,
            )
            if is_curr:
                print(f"Index {target_path.name} is already current and valid.")
                return f16, target_path, dict(existing_meta)

        # Build file stat snapshot table for inventory PDFs on disk (D7, Step 4.3)
        memo: dict[Path, str] = {}
        file_snapshots: list[FileStatSnapshot] = []
        for rel_str, abs_path in pdf_paths:
            try:
                st = abs_path.stat()
                sha = sha256_file(abs_path, memo).removeprefix("sha256:")
                file_snapshots.append(
                    FileStatSnapshot(
                        path=rel_str,
                        size=st.st_size,
                        mtime_ns=st.st_mtime_ns,
                        ctime_ns=st.st_ctime_ns,
                        sha256=sha,
                    )
                )
            except OSError:
                continue

        tmp_path = base_dir / f".build-{os.getpid()}.sqlite3"
        if tmp_path.exists():
            tmp_path.unlink()

        con: sqlite3.Connection | None = None
        try:
            con = sqlite3.connect(str(tmp_path))
            cur = con.cursor()
            cur.execute("PRAGMA journal_mode = OFF;")
            cur.execute("PRAGMA synchronous = OFF;")

            cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
            cur.execute(
                """
                CREATE TABLE docs (
                    sha256 TEXT PRIMARY KEY,
                    material TEXT NOT NULL,
                    pages_total INTEGER NOT NULL,
                    pages_indexed INTEGER NOT NULL,
                    pages_without_text INTEGER NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE files (
                    path TEXT PRIMARY KEY,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    ctime_ns INTEGER NOT NULL,
                    sha256 TEXT NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE cache_records (
                    sha256 TEXT PRIMARY KEY,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE excluded (
                    sha256 TEXT PRIMARY KEY,
                    material TEXT NOT NULL,
                    reason TEXT NOT NULL
                );
                """
            )
            cur.execute(
                f"""
                CREATE VIRTUAL TABLE material_fts USING fts5(
                    body,
                    sha256 UNINDEXED,
                    page_no UNINDEXED,
                    tokenize = '{INDEX_TOKENIZER}'
                );
                """
            )

            cur.executemany(
                "INSERT INTO docs (sha256, material, pages_total, pages_indexed, pages_without_text) VALUES (?, ?, ?, ?, ?);",
                [
                    (
                        d.sha256,
                        d.material,
                        d.pages_total,
                        d.pages_indexed,
                        d.pages_without_text,
                    )
                    for d in doc_records
                ],
            )
            cur.executemany(
                "INSERT INTO files (path, size, mtime_ns, ctime_ns, sha256) VALUES (?, ?, ?, ?, ?);",
                [(f.path, f.size, f.mtime_ns, f.ctime_ns, f.sha256) for f in file_snapshots],
            )
            cur.executemany(
                "INSERT INTO cache_records (sha256, size, mtime_ns) VALUES (?, ?, ?);",
                [(sha, sz, mt) for sha, (sz, mt) in sorted(cache_stats.items())],
            )
            cur.executemany(
                "INSERT INTO excluded (sha256, material, reason) VALUES (?, ?, ?);",
                [(ex.sha256, ex.material, ex.reason) for ex in excluded_records],
            )

            insert_fts_sql = "INSERT INTO material_fts (body, sha256, page_no) VALUES (?, ?, ?);"
            for i in range(0, len(fts_rows), BATCH_SIZE):
                cur.executemany(insert_fts_sql, fts_rows[i : i + BATCH_SIZE])
                con.commit()

            # Step 4.4 (4): Run optimize
            cur.execute("INSERT INTO material_fts(material_fts) VALUES('optimize');")
            con.commit()

            # Step 4.4 (5): Require integrity_check == ok, FTS5 integrity-check, and exact row count
            integrity_rows = cur.execute("PRAGMA integrity_check;").fetchall()
            if integrity_rows != [("ok",)]:
                raise GenerationError(
                    "index_corrupt", f"Built index failed PRAGMA integrity_check: {integrity_rows}"
                )

            cur.execute("INSERT INTO material_fts(material_fts, rank) VALUES('integrity-check', 1);")
            count_row = cur.execute("SELECT count(*) FROM material_fts;").fetchone()
            actual_rows = int(count_row[0]) if count_row else -1
            if actual_rows != total_pages_indexed:
                raise GenerationError(
                    "index_corrupt",
                    f"Built FTS row count {actual_rows} != sum of text pages {total_pages_indexed}",
                )

            # Step 4.4 (6): Write meta, then close
            built_at = _dt.datetime.now(_dt.UTC).isoformat()
            total_pages_all = total_pages_indexed + total_pages_without_text
            meta_dict: dict[str, str] = {
                "schema_version": str(SCHEMA_VERSION),
                "tokenizer": INDEX_TOKENIZER,
                "fingerprint": fingerprint,
                "extractor": EXTRACTOR,
                "built_at": built_at,
                "documents_indexed": str(documents_indexed),
                "documents_total": str(len(doc_records)),
                "documents_without_text": str(documents_without_text),
                "pages_indexed": str(total_pages_indexed),
                "pages_without_text": str(total_pages_without_text),
                "pages_total": str(total_pages_all),
            }
            cur.executemany(
                "INSERT INTO meta (key, value) VALUES (?, ?);",
                sorted(meta_dict.items()),
            )
            con.commit()
            con.close()
            con = None

            # Step 4.4 (7): fsync the file, os.replace to index-<F16>.sqlite3, then fsync directory
            _fsync_file(tmp_path)
            os.replace(tmp_path, target_path)
            _fsync_dir(base_dir)

            # Step 4.4 (8): Prune older files (and any pre-redesign sidecars)
            for existing in base_dir.iterdir():
                if existing.name == ".build.lock":
                    continue
                if existing.resolve() == target_path.resolve():
                    continue
                try:
                    if existing.is_dir():
                        shutil.rmtree(existing)
                    else:
                        existing.unlink(missing_ok=True)
                except OSError:
                    pass

            elapsed = time.perf_counter() - t0
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(
                f"Published {target_path.name} in {elapsed:.1f}s "
                f"({size_mb:.1f} MB, {total_pages_indexed:,} indexed pages, "
                f"{total_pages_without_text:,} pages without text, "
                f"{len(excluded_records)} excluded cache entries)."
            )
            return f16, target_path, dict(meta_dict)

        except BaseException:
            if con is not None:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(lock_fd)


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(
        description="Build and atomically publish the SQLite FTS5 material search index."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="force rebuild even if the current index matches the text cache and file stats",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run full SQLite and FTS5 integrity checks on the active index without building",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (default: parent of tools/)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.root).resolve()

    if args.check:
        try:
            fp, db_path, meta = check_index_integrity(repo_root)
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(
                f"Index OK: {db_path.name} (fingerprint={fp[:16]}, "
                f"{int(meta['pages_indexed']):,} pages, {size_mb:.1f} MB)"
            )
            return 0
        except GenerationError as err:
            print(f"Index unavailable: {err.reason} - {err.message}", file=sys.stderr)
            return 1

    try:
        build_index_generation(repo_root, force=args.force)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
