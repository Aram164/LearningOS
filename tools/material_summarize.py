#!/usr/bin/env python3
"""Promote a reviewed chapter summary into the digest-keyed summary cache.

Summaries are judgments: the agent writes the draft, this tool only checks
structure. A draft is admitted when its digest exists in the page-text
cache, its material and page range match that digest's index, its length
is a genuine compression (at least 200 characters, at most 80% of the
source range), and no summary for that range exists yet. Admission writes
the draft after a fixed generated-file marker plus a provenance meta file
into ``generated/summaries/<sha256>/pages-<start>-<end>/``; anything else
refuses with a reason and writes nothing.

Usage:
    python tools/material_summarize.py --promote --draft DRAFT.md \\
        --digest SHA256 --material rel/path.pdf --pages 3-14 \\
        --model "muse-spark 2026-09"
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from material_text import cache_index  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TEXT_CACHE = REPO / "generated" / "text-cache"
SUMMARY_CACHE = REPO / "generated" / "summaries"

MIN_DRAFT_CHARS = 200
MAX_SOURCE_FRACTION = 0.8


def _refuse(reason: str) -> int:
    print(f"los: summary refused: {reason}", file=sys.stderr)
    return 2


def _parse_pages(raw: str) -> tuple[int, int] | None:
    try:
        first, _, last = raw.partition("-")
        start, end = int(first), int(last)
    except ValueError:
        return None
    if start < 1 or end < start:
        return None
    return start, end


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--promote", action="store_true", help="admit one draft summary")
    parser.add_argument("--draft", help="draft summary file (kept after a header line)")
    parser.add_argument("--digest", help="source material sha256 from the text cache")
    parser.add_argument("--material", help="manifest-relative material path")
    parser.add_argument("--pages", help="covered PDF page range, START-END")
    parser.add_argument("--model", help="authoring model name and version")
    parser.add_argument("--text-cache", default=str(TEXT_CACHE), help="page-text cache root")
    parser.add_argument("--cache-dir", default=str(SUMMARY_CACHE), help="summary cache root")
    args = parser.parse_args(argv)

    if not args.promote:
        parser.error("nothing to do; pass --promote")
    missing = [name for name in ("draft", "digest", "material", "pages", "model")
               if not getattr(args, name)]
    if missing:
        return _refuse(f"missing required input: {', '.join(missing)}")
    if "\n" in args.model or len(args.model) > 200:
        return _refuse("model must be one short line")
    try:
        bad_digest = len(args.digest) != 64 or int(args.digest, 16) < 0
    except (TypeError, ValueError):
        bad_digest = True
    if bad_digest:
        return _refuse("digest must be 64 hex characters")
    record = cache_index(Path(args.text_cache), args.digest)
    if record is None:
        return _refuse(f"digest {args.digest} has no valid text-cache index")
    if record.get("material") != args.material:
        return _refuse("material does not match the digest's cached index")
    span = _parse_pages(args.pages)
    if span is None:
        return _refuse("pages must read START-END with 1 <= START <= END")
    start, end = span
    try:
        total = int(record.get("pages", 0))
    except (TypeError, ValueError):
        return _refuse("cached index has no usable page count")
    if end > total:
        return _refuse("page range exceeds the cached page count")
    try:
        draft = Path(args.draft).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return _refuse(f"draft is missing or not UTF-8: {args.draft}")
    source_chars = 0
    for page in range(start, end + 1):
        try:
            source_chars += len((Path(args.text_cache) / args.digest
                                 / f"pp-{page:04d}.txt").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return _refuse(f"cached page text is incomplete near p{page}")
    if len(draft) < MIN_DRAFT_CHARS:
        return _refuse(f"draft below {MIN_DRAFT_CHARS} characters is not a summary")
    if source_chars and len(draft) > MAX_SOURCE_FRACTION * source_chars:
        return _refuse("draft exceeds 80% of its source range; compress, do not copy")
    target = Path(args.cache_dir) / args.digest / f"pages-{start}-{end}"
    if (target / "summary.md").exists():
        return _refuse("a summary for this range already exists; remove it deliberately first")
    target.mkdir(parents=True, exist_ok=True)
    (target / "summary.md").write_text(
        "<!-- GENERATED file - do not edit; promoted by "
        "tools/material_summarize.py --promote -->\n\n" + draft,
        encoding="utf-8")
    meta = {"_generated": {
                "warning": "GENERATED file - do not edit; rebuilt by "
                           "python tools/material_summarize.py --promote",
                "generator": "tools/material_summarize.py"},
            "material": args.material, "sha256": args.digest,
            "page_range": [start, end], "model": args.model,
            "built": _dt.date.today().isoformat(), "scope": "chapter"}
    (target / "meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": str(target / "summary.md"), "digest": args.digest,
                      "page_range": [start, end]},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
