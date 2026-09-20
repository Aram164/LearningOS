#!/usr/bin/env python3
"""Digest-keyed page-text cache for local materials.

Extracting the same deck twice is rework, not learning. This tool keeps one
UTF-8 page-text file per PDF page under ``generated/text-cache/<sha256>/``
plus an ``index.json`` per digest (material, digest, pages, extractor,
per-page content hashes, built-at). Keys are the live file bytes, so changed
bytes always miss and
identical bytes always hit. The cache is a disposable generated view:
rebuildable, gitignored, never referenced by canonical files. Agents read
cached pages instead of re-running extraction.

Usage:
    python tools/material_text.py --build     # cache every PDF in the manifest
    python tools/material_text.py --refresh   # cache missing digests, prune orphans
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from materials_manifest import (  # noqa: E402
    MANIFEST,
    load_manifest,
    materials_root,
    sha256,
)

REPO = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO / "generated" / "text-cache"
EXTRACTOR = "pdftotext+pypdf"


def _generated_header(tool: str) -> dict:
    """The warning block every generated JSON file must carry (GEN-HEADER)."""
    return {"warning": f"GENERATED file - do not edit; rebuilt by python {tool}",
            "generator": tool}


def _page_count(path: Path) -> int:
    try:
        import pypdf
    except ImportError as exc:  # pragma: no cover - declared dependency
        raise SystemExit("pypdf is required: make setup") from exc
    return len(pypdf.PdfReader(str(path)).pages)


def _page_text(path: Path, page: int) -> str | None:
    proc = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(path), "-"],
        capture_output=True, text=True, errors="replace",
    )
    return proc.stdout if proc.returncode == 0 else None


def _index_path(cache: Path, digest: str) -> Path:
    return cache / digest / "index.json"


def cache_index(cache_dir: Path, digest: str) -> dict | None:
    """Read a digest's cache index; None when absent, corrupt, or mismatched.

    The one reader for this format — the summary promoter uses it rather
    than re-parsing, so the two cannot drift apart.
    """
    try:
        record = json.loads(_index_path(Path(cache_dir), digest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or record.get("sha256") != digest:
        return None
    return record


def _page_path(cache: Path, digest: str, page: int) -> Path:
    return cache / digest / f"pp-{page:04d}.txt"


def _page_hashes(cache: Path, digest: str, pages: int) -> list[str] | None:
    """sha256 per page file, in order; None when any page is unreadable."""
    hashes = []
    for page in range(1, pages + 1):
        try:
            data = _page_path(cache, digest, page).read_bytes()
        except OSError:
            return None
        hashes.append(hashlib.sha256(data).hexdigest())
    return hashes


def _index_valid(cache: Path, digest: str, pages: int) -> bool:
    """A cache entry is valid only when extractor, page count, page files,
    and per-page content hashes all agree with the index record."""
    record = cache_index(cache, digest)
    if record is None or record.get("pages") != pages:
        return False
    if record.get("extractor") != EXTRACTOR:
        return False
    return record.get("pages_sha256") == _page_hashes(cache, digest, pages)


def _extract(path: Path, digest: str, rel: str, cache: Path, pages: int) -> dict:
    texts: list[str] = []
    for page in range(1, pages + 1):
        text = _page_text(path, page)
        if text is None:
            return {"material": rel, "reason": "extract-failed"}
        texts.append(text)
    if sha256(path) != digest:
        return {"material": rel, "reason": "source-changed"}
    staging = cache / f".{digest}.staging"
    if staging.is_symlink() or staging.is_file():
        staging.unlink()
    elif staging.is_dir():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    hashes = []
    try:
        for page, text in enumerate(texts, start=1):
            data = text.encode("utf-8")
            (staging / f"pp-{page:04d}.txt").write_bytes(data)
            hashes.append(hashlib.sha256(data).hexdigest())
        index = {
            "_generated": _generated_header("tools/material_text.py"),
            "material": rel,
            "sha256": digest,
            "pages": pages,
            "extractor": EXTRACTOR,
            "pages_sha256": hashes,
            "built": _dt.date.today().isoformat(),
        }
        (staging / "index.json").write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        # Admit only text extracted from the bytes the digest names: a source
        # that changed during extraction publishes nothing under this digest.
        if sha256(path) != digest:
            return {"material": rel, "reason": "source-changed"}
        target = cache / digest
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        staging.rename(target)
    finally:
        if staging.is_symlink() or staging.is_file():
            staging.unlink()
        elif staging.is_dir():
            shutil.rmtree(staging, ignore_errors=True)
    return {"material": rel, "pages": pages}


def _heal_index(cache: Path, digest: str, pages: int) -> bool:
    """Fill a legacy index's missing header, extractor, and page hashes.

    Page text is untouched: healing rewrites one small JSON file, never
    re-extracts. Returns True only when it wrote something. A present but
    disagreeing extractor or hash list is corruption, not legacy, and is
    left for _index_valid to refuse so the entry re-extracts.
    """
    path = _index_path(cache, digest)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(record, dict) or record.get("pages") != pages:
        return False
    if record.get("sha256") != digest:
        return False
    if "extractor" in record and record["extractor"] != EXTRACTOR:
        return False
    if "pages_sha256" in record:
        complete = record.get("extractor") == EXTRACTOR and "_generated" in record
        if complete:
            return False
    hashes = _page_hashes(cache, digest, pages)
    if hashes is None:
        return False
    record.setdefault("_generated", _generated_header("tools/material_text.py"))
    record.setdefault("extractor", EXTRACTOR)
    record.setdefault("pages_sha256", hashes)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return True


def _prune(cache: Path, live: set[str]) -> int:
    pruned = 0
    if not cache.is_dir():
        return pruned
    for child in sorted(cache.iterdir()):
        name = child.name
        if not child.is_dir() or len(name) != 64:
            continue
        try:
            int(name, 16)
        except ValueError:
            continue
        if name not in live:
            shutil.rmtree(child)
            pruned += 1
    return pruned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", action="store_true", help="cache every PDF in the manifest")
    parser.add_argument("--refresh", action="store_true",
                        help="cache missing digests and prune orphans (default)")
    parser.add_argument("--manifest", default=str(MANIFEST), help="materials manifest path")
    parser.add_argument("--materials-root", default=None, help="materials tree root")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR), help="cache root")
    args = parser.parse_args(argv)

    if shutil.which("pdftotext") is None:
        print("los: pdftotext is required for page-text extraction", file=sys.stderr)
        return 2
    manifest = load_manifest(Path(args.manifest))
    if not manifest:
        print(f"los: no materials manifest at {args.manifest}; run make inventory",
              file=sys.stderr)
        return 2
    base = Path(args.materials_root) if args.materials_root else materials_root()
    cache = Path(args.cache_dir)
    cache.mkdir(parents=True, exist_ok=True)

    recorded = (manifest.get("files") or {})
    cached = extracted = healed = 0
    skipped: list[dict] = []
    stale: list[str] = []
    live: set[str] = set()
    for rel in sorted(recorded):
        path = base / rel
        try:
            inside = path.resolve().is_relative_to(base.resolve())
        except OSError:
            inside = False
        if not inside:
            skipped.append({"material": rel, "reason": "boundary"})
            continue
        if path.is_symlink() or not path.is_file():
            skipped.append({"material": rel, "reason": "missing"})
            continue
        if path.suffix.casefold() != ".pdf":
            skipped.append({"material": rel, "reason": "not-pdf"})
            continue
        digest = sha256(path)
        live.add(digest)
        if digest != (recorded[rel] or {}).get("sha256"):
            stale.append(rel)
        try:
            pages = _page_count(path)
        except Exception:
            skipped.append({"material": rel, "reason": "unreadable-pdf"})
            continue
        if _heal_index(cache, digest, pages):
            healed += 1
            continue
        if _index_valid(cache, digest, pages):
            cached += 1
            continue
        outcome = _extract(path, digest, rel, cache, pages)
        if "pages" in outcome:
            extracted += 1
        else:
            skipped.append(outcome)
    pruned = _prune(cache, live) if (args.refresh or not args.build) else 0
    print(json.dumps({"cached": cached, "extracted": extracted,
                      "healed": healed, "skipped": skipped, "stale": sorted(stale),
                      "pruned": pruned, "cache": str(cache)},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
