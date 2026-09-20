#!/usr/bin/env python3
"""Promote a reviewed chapter summary into the digest-keyed summary cache.

Summaries are judgments: the agent writes the draft, this tool only checks
structure. A draft is admitted when its digest exists in the page-text
cache, its material and page range match that digest's index, its length
is a genuine compression (at least 200 characters, at most 80% of a
non-empty source range), and no summary for that range exists yet.
An empty source range refuses: with nothing to compress against, the
fraction is unprovable. Admission writes
the draft after a fixed generated-file marker plus a provenance meta file
into ``generated/summaries/<sha256>/pages-<start>-<end>/``; anything else
refuses with a reason and writes nothing.

Usage:
    python tools/material_summarize.py --promote --draft DRAFT.md \\
        --digest SHA256 --material rel/path.pdf --pages 3-14 \\
        --model "muse-spark 2026-09"
    python tools/material_summarize.py --audit [--cache-dir DIR]
        [--materials-root DIR]
    python tools/material_summarize.py --read --material rel/path.pdf --pages 3-14
        [--digest EXPECTED_SHA256] [--materials-root DIR]

--read returns one source-bound chapter summary for triage, without reading
cached pages or generating new analysis. Exit 0 means a hit, 1 means missing
or stale, and 2 means refused. Legacy summaries remain readable with an
explicit unrecorded-integrity label; newly promoted summaries carry a body
checksum. Neither checksum nor source freshness certifies semantic quality.

--audit is read-only and deliberately narrow: a summary is stale if and
only if the live material bytes no longer hash to its recorded digest.
It is not a freshness check against revisions, routes, or prose.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from material_text import cache_index  # noqa: E402
from materials_manifest import materials_root, sha256  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TEXT_CACHE = REPO / "generated" / "text-cache"
SUMMARY_CACHE = REPO / "generated" / "summaries"

MIN_DRAFT_CHARS = 200
MAX_SOURCE_FRACTION = 0.8
MAX_SUMMARY_BYTES = 64_000
MAX_META_BYTES = 16_000


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


def _is_hex_digest(name: str) -> bool:
    return (isinstance(name, str) and len(name) == 64
            and all(char in "0123456789abcdefABCDEF" for char in name))


def _bounded_bytes(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"{path.name} exceeds the bounded read limit")
    return data


def _read_summary(cache_dir: Path, base: Path, material: str,
                  span: tuple[int, int], expected: str | None) -> int:
    """Read exactly one chapter, checking live source bytes before and after."""
    result = {"material": material, "page_range": list(span),
              "purpose": "chapter-triage", "primary_evidence_required": True}

    def emit(status: str, code: int, **fields) -> int:
        print(json.dumps({**result, "status": status, **fields},
                         ensure_ascii=False, separators=(",", ":")))
        return code

    try:
        relative = Path(material)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("material must be a relative path inside the materials root")
        live = (base / relative).resolve()
        live.relative_to(base.resolve())
        digest = sha256(live)

        def source_unchanged() -> bool:
            return (sha256(live) == digest
                    and (base / relative).resolve() == live)

        result["source_sha256"] = digest
        if expected is not None and expected.lower() != digest:
            return emit("stale", 1, expected_sha256=expected.lower(),
                        reason="source bytes changed; select the current chapter before reuse")
        target = cache_dir / digest / f"pages-{span[0]}-{span[1]}"
        target.resolve().relative_to(cache_dir.resolve())
        meta_path, body_path = target / "meta.json", target / "summary.md"
        # A partial or escaped entry is never reported as an ordinary miss.
        for path in (meta_path, body_path):
            path.resolve().relative_to(cache_dir.resolve())
        if not meta_path.exists() and not body_path.exists():
            if not source_unchanged():
                raise ValueError("source changed during lookup; retry")
            return emit("missing", 1, reason="no summary for the current source and exact page range")
        meta = json.loads(_bounded_bytes(meta_path, MAX_META_BYTES))
        if (not isinstance(meta, dict) or meta.get("sha256") != digest
                or meta.get("material") != material
                or meta.get("page_range") != list(span)
                or meta.get("scope") != "chapter"
                or not isinstance(meta.get("model"), str) or not meta["model"].strip()):
            raise ValueError("summary provenance does not match the requested source and range")
        body = _bounded_bytes(body_path, MAX_SUMMARY_BYTES)
        summary = body.decode("utf-8")
        if not summary.strip():
            raise ValueError("summary is empty")
        body_digest = hashlib.sha256(body).hexdigest()
        recorded = meta.get("summary_sha256")
        if recorded is not None and recorded != body_digest:
            raise ValueError("summary content checksum mismatch")
        if not source_unchanged():
            raise ValueError("source changed during lookup; retry")
        return emit("hit", 0, source_fresh=True,
                    integrity="verified" if recorded is not None else "legacy-unrecorded",
                    summary_sha256=body_digest, model=meta["model"],
                    built=meta.get("built"), summary=summary)
    except (OSError, ValueError, RuntimeError) as exc:
        return emit("refused", 2, reason=str(exc))


def _audit(cache_dir: Path, base: Path) -> int:
    """Report promoted summaries whose live bytes left their digest.

    Read-only. Prints one JSON object ``{checked, fresh, stale,
    unverifiable}`` and returns 1 only when at least one summary is
    stale. Missing or unreadable live files are unverifiable, never
    stale: staleness means digest mismatch, nothing else.
    """
    stale: list[dict] = []
    unverifiable: list[dict] = []
    fresh = 0
    try:
        digest_dirs = sorted(p for p in cache_dir.iterdir()
                             if p.is_dir() and _is_hex_digest(p.name))
    except OSError:
        digest_dirs = []
    for digest_dir in digest_dirs:
        try:
            ranges = sorted(p for p in digest_dir.iterdir()
                            if p.is_dir() and p.name.startswith("pages-"))
        except OSError:
            continue
        for ranged in ranges:
            where = {"digest": digest_dir.name, "range": ranged.name}
            try:
                meta = json.loads((ranged / "meta.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                unverifiable.append({**where, "reason": "unreadable meta.json"})
                continue
            if not isinstance(meta, dict) or meta.get("sha256") != digest_dir.name:
                unverifiable.append({**where, "reason": "meta digest mismatch"})
                continue
            material = meta.get("material")
            if not isinstance(material, str) or not material:
                unverifiable.append({**where, "reason": "meta has no material path"})
                continue
            try:
                live = (base / material).resolve()
                live.relative_to(base.resolve())
            except (OSError, ValueError):
                unverifiable.append({**where, "reason": "material path escapes root"})
                continue
            if not live.is_file():
                unverifiable.append({**where, "reason": "live material file missing"})
                continue
            try:
                current = sha256(live)
            except OSError:
                unverifiable.append({**where, "reason": "live material unreadable"})
                continue
            if current != digest_dir.name:
                stale.append({**where, "material": material})
            else:
                fresh += 1
    print(json.dumps({"checked": fresh + len(stale) + len(unverifiable),
                      "fresh": fresh, "stale": stale,
                      "unverifiable": unverifiable},
                     ensure_ascii=False, separators=(",", ":")))
    return 1 if stale else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--promote", action="store_true", help="admit one draft summary")
    parser.add_argument("--audit", action="store_true",
                        help="report summaries whose live bytes left their digest")
    parser.add_argument("--read", action="store_true",
                        help="read one current chapter summary with provenance as JSON")
    parser.add_argument("--materials-root", default=None, help="materials tree root")
    parser.add_argument("--draft", help="draft summary file (kept after a header line)")
    parser.add_argument("--digest", help="source material sha256 from the text cache")
    parser.add_argument("--material", help="manifest-relative material path")
    parser.add_argument("--pages", help="covered PDF page range, START-END")
    parser.add_argument("--model", help="authoring model name and version")
    parser.add_argument("--text-cache", default=str(TEXT_CACHE), help="page-text cache root")
    parser.add_argument("--cache-dir", default=str(SUMMARY_CACHE), help="summary cache root")
    args = parser.parse_args(argv)

    if sum((args.audit, args.promote, args.read)) != 1:
        parser.error("choose exactly one of --promote, --audit, or --read")
    if args.read:
        if not args.material or not args.pages or (span := _parse_pages(args.pages)) is None:
            parser.error("--read requires --material and --pages START-END")
        if args.digest is not None and not _is_hex_digest(args.digest):
            parser.error("--digest must be 64 hex characters")
        base = Path(args.materials_root) if args.materials_root else materials_root()
        return _read_summary(Path(args.cache_dir), base, args.material, span, args.digest)
    if args.audit:
        base = Path(args.materials_root) if args.materials_root else materials_root()
        return _audit(Path(args.cache_dir), base)
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
    if source_chars == 0:
        return _refuse("cached source range holds no text; compression is unprovable")
    if len(draft) > MAX_SOURCE_FRACTION * source_chars:
        return _refuse("draft exceeds 80% of its source range; compress, do not copy")
    target = Path(args.cache_dir) / args.digest / f"pages-{start}-{end}"
    if (target / "summary.md").exists():
        return _refuse("a summary for this range already exists; remove it deliberately first")
    target.mkdir(parents=True, exist_ok=True)
    summary = (
        "<!-- GENERATED file - do not edit; promoted by "
        "tools/material_summarize.py --promote -->\n\n" + draft).encode("utf-8")
    (target / "summary.md").write_bytes(summary)
    meta = {"_generated": {
                "warning": "GENERATED file - do not edit; rebuilt by "
                           "python tools/material_summarize.py --promote",
                "generator": "tools/material_summarize.py"},
            "material": args.material, "sha256": args.digest,
            "page_range": [start, end], "model": args.model,
            "summary_sha256": hashlib.sha256(summary).hexdigest(),
            "built": _dt.date.today().isoformat(), "scope": "chapter"}
    (target / "meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": str(target / "summary.md"), "digest": args.digest,
                      "page_range": [start, end]},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
