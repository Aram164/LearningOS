#!/usr/bin/env python3
"""Fetch YouTube captions into the managed materials tree as addressable text.

WHY THIS EXISTS
---------------
Video was the one source class with no material layer. Every book resolves to
bytes on disk with a checksum in `records/materials-manifest.yaml`; every video
resolved to a name and sometimes a URL. Measured 2026-09-11: 63 video/course
sources, none with a `material:`, 43 plan rows pointing at them, *zero* with a
timestamp in the locator. So an agent asked to check a claim against a lecture
had nothing to read, and `source-changed-under-claim` could not fire for video
at all — there was no hash to change.

A transcript here is an ordinary managed material. Once it is one, everything
already built applies: `make inventory` checksums it, `material://` addresses
it, a plan locator can name an exact span the way a book locator names exact
pages, and a re-uploaded video invalidates the claims that cited it.

WHY NORMALISED MARKDOWN, NOT THE RAW VTT
----------------------------------------
Auto-captions arrive as rolling cues with per-word timing tags: the FFT probe
was 255 KB (~64k tokens) for 28 minutes, every line repeated two or three times
as the caption scrolled. Stripping the tags, dropping the rolling duplicates
and merging into fixed windows gives 10.4% of that — ~6.6k tokens — with one
timestamp per window. `.md` is already an accepted material suffix, so this
needs no contract change, and the result greps.

The window is the addressing unit. `[12:30]` is to a lecture what `PDF p. 46`
is to a book, and it is what lets a later reader open one span instead of an
hour.

NOT A CANONICAL WRITER
----------------------
This writes only under `LearningOS/materials/`, the external material tree, and
never repository state. It does not edit a source record, a study map or a
locator: pointing a plan row at a span is a governed `unit.map.import`, and
this tool deliberately stops one step short of it.

Usage:
    python3 tools/ingest_transcript.py --list
    python3 tools/ingest_transcript.py --source source-reducible-fft
    python3 tools/ingest_transcript.py --all [--limit N] [--window 30]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.loader import load_repo  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
MATERIALS = REPO.parent / "materials"

CUE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})\.\d{3}\s+-->")
TAG = re.compile(r"<[^>]+>")
URL = re.compile(r"https?://[^\s'\"\],)]+")
YOUTUBE = re.compile(r"(youtube\.com|youtu\.be)", re.IGNORECASE)

#: A channel URL names everything its author ever posted, which is not a
#: source's material — it is a subscription. Six of the registry's video
#: sources are recorded as channels (a statistics channel cited for two
#: explanations, say), so an unguarded `--all` would pull hundreds of unrelated
#: videos into the managed tree and checksum them. Fetching one needs an
#: explicit `--limit`, which makes the bound a decision rather than an
#: accident.
CHANNEL = re.compile(r"youtube\.com/(@|c/|user/|channel/)", re.IGNORECASE)
SKIP_LINE = ("WEBVTT", "Kind:", "Language:")

#: Where a source's folder belongs when it does not have one yet. ADR-007: the
#: tree is the subject taxonomy, and placement is presentation only — move an
#: entry and re-run `tools/build_materials_tree.py`, which stays the single
#: builder of `.flat/`.
PLACEMENT_HINT = {
    "fiset-graph-theory": "algorithms/structures",
    "kit-algorithmen2": "algorithms/structures",
    "reducible-fft": "algorithms/complexity",
    "3b1b-linear-algebra": "mathematics/linear-algebra",
    "3b1b-essence-of-calculus": "mathematics/analysis",
    "professor-leonard": "mathematics/analysis",
    "3b1b-bayes-theorem": "mathematics/probability-statistics",
    "brandon-foltz": "mathematics/probability-statistics",
    "jbstatistics": "mathematics/probability-statistics",
    "kurzes-tutorium-statistik": "mathematics/probability-statistics",
    "zedstatistics": "mathematics/probability-statistics",
    "statquest": "mathematics/probability-statistics",
    "3b1b-neural-networks": "machine-learning/classical",
    "cs229-2022-videos": "machine-learning/classical",
    "cs231n-2017-videos": "machine-learning/classical",
    "cs4780": "machine-learning/classical",
    "eecs498": "machine-learning/classical",
    "hinton-nnml": "machine-learning/classical",
    "karpathy-micrograd": "machine-learning/classical",
    "mit-6s191": "machine-learning/classical",
    "data-school-sklearn": "machine-learning/classical",
    "patrick-loeber-pytorch-cnn": "machine-learning/classical",
    "corey-schafer-oop": "software/python",
    "guo-cpython-internals": "software/python",
    "hettinger-class-toolkit": "software/python",
    "powell-python-expert": "software/python",
}


class IngestError(RuntimeError):
    """The fetch or the conversion cannot be completed as asked."""


# ---------------------------------------------------------------- discovery


def youtube_urls(source: dict) -> list[str]:
    """Every distinct YouTube URL anywhere in a source record, in order."""
    found = URL.findall(json.dumps(source, ensure_ascii=False))
    return [u for u in dict.fromkeys(x.rstrip(".,;") for x in found)
            if YOUTUBE.search(u)]


def video_sources(repo) -> dict[str, list[str]]:
    """Source id -> its YouTube URLs, for every source that names one."""
    out = {}
    for sid, source in sorted(repo.sources.items()):
        if not isinstance(source, dict):
            continue
        urls = youtube_urls(source)
        if urls:
            out[sid] = urls
    return out


def source_folder(slug: str) -> Path | None:
    """The source's existing materials folder, or None when it has none."""
    flat = MATERIALS / ".flat" / f"source-{slug}"
    if flat.is_symlink() or flat.is_dir():
        return flat.resolve()
    for candidate in (MATERIALS / f"source-{slug}", MATERIALS / slug):
        if candidate.is_dir() and not candidate.is_symlink():
            return candidate
    return None


def target_folder(slug: str) -> tuple[Path, bool]:
    """(folder, is_new). A source with no folder is placed by the hint map."""
    existing = source_folder(slug)
    if existing is not None:
        return existing, False
    parent = PLACEMENT_HINT.get(slug)
    if parent is None:
        raise IngestError(
            f"{slug} has no materials folder and no placement hint — add it to "
            "PLACEMENT_HINT here and to PLACEMENT in build_materials_tree.py")
    hinted = MATERIALS / parent / slug
    # Already placed by an earlier run, just not yet linked into `.flat/`
    # (that is `build_materials_tree.py`'s job, and it may not have run since).
    # Reporting it as new a second time would ask for a PLACEMENT entry that
    # is already there.
    return hinted, not hinted.is_dir()


# ---------------------------------------------------------------- conversion


def normalise_vtt(text: str, *, window: int = 30) -> list[tuple[int, str]]:
    """Rolling, word-tagged cues -> one deduplicated line per time window.

    Auto-captions repeat each phrase as the caption scrolls and tag every word
    with its own timestamp. Both are noise for a reader. What survives is the
    spoken text, bucketed so a locator can name `[12:30]` and mean it.
    """
    cues: list[tuple[int, str]] = []
    at: int | None = None
    for line in text.splitlines():
        match = CUE.match(line)
        if match:
            hours, minutes, seconds = (int(p) for p in match.groups())
            at = hours * 3600 + minutes * 60 + seconds
            continue
        if not line.strip() or line.startswith(SKIP_LINE):
            continue
        clean = TAG.sub("", line).strip()
        if clean and at is not None:
            cues.append((at, clean))

    kept: list[tuple[int, str]] = []
    for at, line in cues:
        if kept and (kept[-1][1] == line or kept[-1][1].endswith(line)):
            continue
        kept.append((at, line))

    merged: list[tuple[int, str]] = []
    bucket: int | None = None
    words: list[str] = []
    for at, line in kept:
        start = (at // window) * window
        if bucket is None:
            bucket = start
        if start != bucket:
            merged.append((bucket, " ".join(words)))
            bucket, words = start, []
        words.extend(line.split())
    if words and bucket is not None:
        merged.append((bucket, " ".join(words)))
    return merged


def stamp(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def render(meta: dict, segments: list[tuple[int, str]], *, source_id: str,
           window: int) -> str:
    """One transcript file: a header that says what it is, then the spans."""
    head = [
        f"# {meta.get('title', meta['id'])}",
        "",
        "> Machine transcript of a third-party video, fetched for study use.",
        "> Not authored knowledge and not a note: this is source material — the",
        "> video's own words, addressable by timestamp. Auto-captions contain",
        "> recognition errors, so quote from it only after checking the moment",
        "> it names.",
        "",
        f"- source: `{source_id}`",
        f"- video: {meta.get('webpage_url', '')}",
        f"- video_id: `{meta['id']}`",
        f"- duration: {stamp(int(meta.get('duration') or 0))}",
        f"- captions: {meta.get('_caption_kind', 'auto')}",
        f"- window: {window}s",
        f"- fetched: {datetime.now(UTC).date().isoformat()}",
        "",
        "---",
        "",
    ]
    body = [f"[{stamp(at)}] {text}" for at, text in segments]
    return "\n".join(head + body) + "\n"


# ---------------------------------------------------------------- fetching


def ytdlp() -> str:
    for candidate in (REPO / ".venv/bin/yt-dlp", Path("yt-dlp")):
        found = shutil.which(str(candidate))
        if found:
            return found
    raise IngestError(
        "yt-dlp is not available — install it into the project venv with "
        "`.venv/bin/python -m pip install yt-dlp`")


def listed_ids(url: str, *, limit: int | None) -> list[str]:
    """The video ids behind a URL, in order, without fetching any captions.

    `--flat-playlist` costs one request for a whole playlist, which is what
    makes the skip cheap: the ids are known before anything is downloaded, so
    a video already on disk never becomes a request at all. A single-video URL
    prints its own id, so both shapes take the same path.
    """
    argv = [ytdlp(), "--flat-playlist", "--print", "%(id)s",
            "--ignore-errors", "--no-warnings"]
    if limit:
        argv += ["--playlist-items", f"1-{limit * 4}"]
    argv.append(url)
    done = subprocess.run(argv, check=False, capture_output=True, text=True)
    return [line.strip() for line in done.stdout.splitlines() if line.strip()]


def fetch(video_ids: list[str], into: Path) -> list[tuple[dict, Path]]:
    """Download captions for exactly these videos. Returns (meta, vtt) pairs."""
    if not video_ids:
        return []
    argv = [
        ytdlp(), "--skip-download", "--write-auto-subs", "--write-subs",
        "--sub-langs", "en.*,de.*", "--sub-format", "vtt",
        "--write-info-json", "--ignore-errors", "--no-warnings",
        "--sleep-requests", "1",
        "-o", str(into / "%(id)s"),
    ]
    argv += [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
    subprocess.run(argv, check=False, capture_output=True, text=True)

    pairs = []
    for info in sorted(into.glob("*.info.json")):
        meta = json.loads(info.read_text(encoding="utf-8"))
        vid = meta.get("id")
        if not vid:
            continue
        tracks = [t for t in sorted(into.glob(f"{vid}.*.vtt"))
                  if ".en-orig." not in t.name] or sorted(into.glob(f"{vid}.*.vtt"))
        if not tracks:
            continue
        meta["_caption_kind"] = "manual" if meta.get("subtitles") else "auto"
        pairs.append((meta, tracks[0]))
    return pairs


def ingest(source_id: str, urls: list[str], *, window: int,
           limit: int | None, dry_run: bool) -> tuple[int, int, Path | None]:
    """Fetch what is missing for one source. Returns (written, skipped, new folder).

    Existing transcripts are never re-fetched: the ids are listed first and
    filtered against what is already on disk, so widening `--limit` later costs
    only the new videos. `--limit` therefore bounds *new* work rather than
    re-counting from the top of the playlist every run.
    """
    slug = source_id.removeprefix("source-")
    folder, is_new = target_folder(slug)
    out_dir = folder / "transcript"
    have = {path.stem for path in out_dir.glob("*.md")} if out_dir.is_dir() else set()
    written = skipped = 0

    for url in urls:
        if CHANNEL.search(url) and not limit:
            print(f"    skipped channel {url} — pass --limit to bound it",
                  file=sys.stderr)
            continue
        ids = listed_ids(url, limit=limit)
        fresh = [vid for vid in ids if vid not in have]
        skipped += len(ids) - len(fresh)
        if limit:
            fresh = fresh[:limit]
        if not fresh:
            continue
        with tempfile.TemporaryDirectory(prefix="los-transcript-") as tmp:
            staging = Path(tmp)
            for meta, vtt in fetch(fresh, staging):
                segments = normalise_vtt(
                    vtt.read_text(encoding="utf-8", errors="replace"),
                    window=window)
                if not segments:
                    continue
                text = render(meta, segments, source_id=source_id, window=window)
                written += 1
                have.add(meta["id"])
                if dry_run:
                    continue
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"{meta['id']}.md").write_text(text, encoding="utf-8")
    return written, skipped, (folder if is_new and written and not dry_run else None)


# ---------------------------------------------------------------- entry point


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true",
                       help="show every source with a YouTube URL and its target folder")
    group.add_argument("--source", help="ingest one source id")
    group.add_argument("--all", action="store_true", help="ingest every such source")
    parser.add_argument("--window", type=int, default=30,
                        help="seconds per addressable span (default 30)")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap NEW videos fetched per URL (already-held ones "
                             "are skipped before they count)")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch and convert, write nothing")
    args = parser.parse_args()

    if args.window < 5:
        print("ingest-transcript: --window below 5s makes spans unusable", file=sys.stderr)
        return 2

    repo = load_repo(REPO)
    catalogue = video_sources(repo)

    if args.list:
        print(f"{len(catalogue)} source(s) naming a YouTube URL\n")
        for sid, urls in catalogue.items():
            slug = sid.removeprefix("source-")
            try:
                folder, is_new = target_folder(slug)
                root = MATERIALS.resolve()
                where = folder.relative_to(root) if folder.is_relative_to(root) else folder
                mark = "new" if is_new else "   "
            except IngestError:
                where, mark = "(no placement)", "!!!"
            print(f"  {mark} {sid:36} -> {where}")
            for url in urls:
                print(f"        {url}")
        return 0

    targets = {args.source: catalogue.get(args.source, [])} if args.source else catalogue
    if args.source and not targets[args.source]:
        print(f"ingest-transcript: {args.source} names no YouTube URL", file=sys.stderr)
        return 2

    new_folders, total = [], 0
    for sid, urls in targets.items():
        print(f"  {sid} ...", flush=True)
        try:
            count, skipped, created = ingest(sid, urls, window=args.window,
                                             limit=args.limit, dry_run=args.dry_run)
        except IngestError as exc:
            print(f"    refused: {exc}", file=sys.stderr)
            continue
        total += count
        if created:
            new_folders.append(sid.removeprefix("source-"))
        note = f", {skipped} already held" if skipped else ""
        print(f"    {count} transcript(s){note}", flush=True)

    print(f"\n{total} transcript(s) {'converted' if args.dry_run else 'written'}")
    if new_folders:
        print("\nNew source folders were created. Add these to PLACEMENT in "
              "tools/build_materials_tree.py, then run it so `.flat/` links them:")
        for slug in sorted(new_folders):
            print(f'    "{slug}": "{PLACEMENT_HINT[slug]}",')
    if total and not args.dry_run:
        print("\nThen: make inventory   (checksums the new material)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
