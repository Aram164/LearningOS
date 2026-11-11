#!/usr/bin/env python3
"""Harvest PDF outline sections into the digest-keyed outline cache.

``material.search`` groups its hits by the outline section that owns each
page. This tool writes what it reads: one file per PDF digest,
``generated/material-outlines/<sha256>.json``, holding the document's
bookmarks normalized into page-owning sections (``search_index.
normalize_outline``). The cache is disposable and rebuildable; deleting it
only turns every group back into an explicit ``not-harvested`` unsectioned
group.

    python tools/material_outline.py --check     # report the cache, write nothing
    python tools/material_outline.py --refresh   # harvest missing or invalid entries

The digests come from the page-text cache's index records, so exactly the
indexed PDFs are covered. An entry is a pure function of the PDF bytes and the
normalizer version, so a valid entry is never rebuilt. A new entry hashes the
live file and parses the outline of exactly those bytes; a file whose bytes no
longer match its digest is skipped, never cached under the wrong digest.
``--refresh`` also removes entries whose digest left the page-text cache. The
page-text producer (``tools/material_text.py``) is read, never changed.

Page numbers are PDF page numbers (the viewer's page box, cover = 1), as in
``tools/material_toc.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path, PurePosixPath

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from material_toc import outline_rows  # noqa: E402

from learning_os.store.materials.pdf_text import PDFTextError, pdf_reader  # noqa: E402
from learning_os.store.materials.search_index import (  # noqa: E402
    OUTLINE_TOP_DIR,
    OutlineRecord,
    normalize_outline,
    outline_payload,
    parse_outline_payload,
)

REPO = Path(__file__).resolve().parents[1]
GENERATOR = "tools/material_outline.py"
#: Outline nesting read in full; deeper bookmarks are vanishingly rare.
OUTLINE_DEPTH = 32
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ENTRY = re.compile(r"^([0-9a-f]{64})\.json$")


def _text_cache_documents(text_cache: Path) -> dict[str, tuple[str, int]]:
    """digest -> (materials-relative path, cached page count) of every record."""
    documents: dict[str, tuple[str, int]] = {}
    if not text_cache.is_dir():
        return documents
    for entry in sorted(text_cache.iterdir()):
        if not entry.is_dir() or _HEX64.match(entry.name) is None:
            continue
        try:
            record = json.loads((entry / "index.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        material = record.get("material") if isinstance(record, dict) else None
        pages = record.get("pages") if isinstance(record, dict) else None
        if (record.get("sha256") == entry.name and isinstance(material, str) and material
                and isinstance(pages, int) and not isinstance(pages, bool)):
            documents[entry.name] = (material, pages)
    return documents


def _material_file(materials_root: Path, material: str) -> Path | None:
    """The regular, non-symlinked file a relative material path names, else None."""
    rel = PurePosixPath(material)
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        return None
    root = materials_root.resolve()
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None
    return cursor if cursor.is_file() else None


def _harvest(path: Path, sha256: str, material: str) -> tuple[str, dict[str, object] | None]:
    """(outcome, payload); payload is None when the bytes are not the digest's."""
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != sha256:
        return "skipped-changed-file", None
    try:
        reader = pdf_reader(content)
        page_total = len(reader.pages)
    except PDFTextError:
        return "unreadable", outline_payload(sha256, material, 0, "unreadable", [], GENERATOR)
    try:
        rows = outline_rows(reader, OUTLINE_DEPTH)
    except Exception:  # pypdf raises many shapes for broken outline trees
        return "unreadable", outline_payload(
            sha256, material, page_total, "unreadable", [], GENERATOR)
    status, sections = normalize_outline(rows, page_total)
    return status, outline_payload(sha256, material, page_total, status, sections, GENERATOR)


def _write_atomic(target: Path, payload: dict[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def run(*, text_cache: Path, outline_dir: Path, materials_root: Path,
        refresh: bool) -> dict:
    documents = _text_cache_documents(text_cache)
    counts: dict[str, int] = {}
    pages_total = pages_sectioned = 0

    def bump(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    if refresh:
        outline_dir.mkdir(parents=True, exist_ok=True)
    for sha256, (material, _cached_pages) in sorted(documents.items()):
        record = _load_from(outline_dir, sha256)
        if record.status not in ("not-harvested", "cache-invalid"):
            bump(f"cached-{record.status}")
        elif not refresh:
            bump(record.status)
            continue
        else:
            path = _material_file(materials_root, material)
            if path is None:
                bump("skipped-missing-file")
                continue
            outcome, payload = _harvest(path, sha256, material)
            if payload is None:
                bump(outcome)
                continue
            _write_atomic(outline_dir / f"{sha256}.json", payload)
            bump(f"written-{outcome}")
            record = _load_from(outline_dir, sha256)
        if record.sections:
            pages_total += record.page_total
            pages_sectioned += record.page_total - record.sections[0].start_page + 1
    pruned = 0
    if refresh and outline_dir.is_dir():
        for entry in sorted(outline_dir.iterdir()):
            match = _ENTRY.match(entry.name)
            if match and match.group(1) not in documents and entry.is_file():
                entry.unlink()
                pruned += 1
    return {
        "documents": len(documents),
        "outcomes": dict(sorted(counts.items())),
        "pages_in_outlined_documents": pages_total,
        "pages_owned_by_a_section": pages_sectioned,
        "pruned": pruned,
        "refresh": refresh,
    }


def _load_from(outline_dir: Path, sha256: str) -> OutlineRecord:
    """``search_index.load_outline`` for an explicit cache directory."""
    path = outline_dir / f"{sha256}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return OutlineRecord("not-harvested")
    except (OSError, ValueError):
        return OutlineRecord("cache-invalid")
    record = parse_outline_payload(data, sha256)
    return record if record is not None else OutlineRecord("cache-invalid")


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="report the outline cache against the page-text cache; write nothing")
    mode.add_argument("--refresh", action="store_true",
                      help="harvest missing or invalid entries and prune orphaned ones")
    parser.add_argument("--repo", default=str(REPO), help="Core repository root")
    parser.add_argument("--text-cache", default=None,
                        help="page-text cache (default: REPO/generated/text-cache)")
    parser.add_argument("--outline-dir", default=None,
                        help=f"outline cache (default: REPO/generated/{OUTLINE_TOP_DIR})")
    parser.add_argument("--materials-root", default=None,
                        help="physical materials tree (default: REPO/../materials)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # pypdf logs every malformed cross-reference it repairs; the summary is
    # the report, so keep only its errors.
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    repo = Path(args.repo).resolve()
    summary = run(
        text_cache=Path(args.text_cache) if args.text_cache else repo / "generated" / "text-cache",
        outline_dir=(Path(args.outline_dir) if args.outline_dir
                     else repo / "generated" / OUTLINE_TOP_DIR),
        materials_root=(Path(args.materials_root) if args.materials_root
                        else repo.parent / "materials"),
        refresh=args.refresh,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.check:
        outcomes = summary["outcomes"]
        pending = sum(count for name, count in outcomes.items()
                      if not name.startswith("cached-"))
        return 0 if pending == 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
