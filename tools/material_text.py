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

The default cache (``generated/text-cache/`` under this tool's own
repository root) is backed by per-digest derived nodes
(``cache.text:<sha256>``, SPEC §14, D-12): extraction persists the
node's texts, and a run serves the entry from cache only when the node
and the file views agree, so source, extractor, producer, runtime, and
page-count changes each invalidate. The files stay byte-identical
views of their node: page loss or corruption re-projects from the
node without re-running extraction. An explicit ``--cache-dir``
elsewhere keeps the legacy file-only behavior (§14 disposition: no
repo root is expressible for an arbitrary directory, so no derived
reads or writes happen there).
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

from learning_os.domain.failures import TransactionFailure  # noqa: E402
from learning_os.store.derived.engine import BuildContext, evaluate, evaluate_many  # noqa: E402
from learning_os.store.derived.model import (  # noqa: E402
    DERIVED_SUBSTRATE_FILES,
    DerivedError,
    NodeSpec,
)
from learning_os.store.derived.store import invalidate  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO / "generated" / "text-cache"
EXTRACTOR = "pdftotext+pypdf"

#: Per-digest derived nodes for the default cache (SPEC §14, D-12): one
#: node per cached digest, so one material's re-extraction never
#: invalidates another's texts.
TEXT_NODE_VERSION = 1
TEXT_PRODUCER_FILES = (
    "tools/material_text.py",
    *DERIVED_SUBSTRATE_FILES,
)

#: Direct-input kinds per node: the live source-bytes digest, the
#: effective extractor identity, and the live page count. Producer and
#: runtime identity ride in the key through the engine session.
TEXT_INPUT_KINDS = ("source", "extractor", "pages")


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


def _is_default_cache(cache: Path) -> bool:
    """Whether `cache` is the default text cache under this tool's repo.

    The default location is this module's own verified anchor
    (``REPO/generated/text-cache``, from this file's location), never
    inferred from arguments: any other `--cache-dir` keeps the legacy
    file-only behavior with no derived reads or writes.
    """
    try:
        return Path(cache).resolve() == CACHE_DIR.resolve()
    except OSError:
        return False


def _text_node_id(digest: str) -> str:
    """Logical derived node holding one digest's extracted texts."""
    return f"cache.text:{digest}"


def _text_input_id(kind: str, digest: str) -> str:
    """Direct-input id carrying one freshness fact for one digest."""
    return f"cache.text.{kind}:{digest}"


def _text_spec(digest: str) -> NodeSpec:
    """One digest's node: live source, extractor, and page count."""
    return NodeSpec(
        id=_text_node_id(digest),
        version=TEXT_NODE_VERSION,
        producer_files=TEXT_PRODUCER_FILES,
        direct_inputs=tuple(
            _text_input_id(kind, digest) for kind in TEXT_INPUT_KINDS),
    )


def _text_inputs(digest: str, pages: int) -> dict[str, str]:
    """Map the live freshness facts onto derived direct-input digests."""
    return {
        _text_input_id("source", digest): digest,
        _text_input_id("extractor", digest): EXTRACTOR,
        _text_input_id("pages", digest): str(pages),
    }


def _valid_text_value(value: object) -> bool:
    """Whether a derived hit has exactly the text shape we write."""
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("digest"), str):
        return False
    if not isinstance(value.get("material"), str):
        return False
    pages = value.get("pages")
    if not isinstance(pages, int):
        return False
    if not isinstance(value.get("extractor"), str):
        return False
    texts = value.get("texts")
    if not isinstance(texts, list) or len(texts) != pages:
        return False
    if not all(isinstance(text, str) for text in texts):
        return False
    hashes = value.get("pages_sha256")
    if not isinstance(hashes, list) or len(hashes) != pages:
        return False
    return all(isinstance(item, str) for item in hashes)


def _checked_text_value(node_id: str, value: object) -> dict | None:
    """A looked-up value, or None when wrongly shaped (then invalidated)."""
    if _valid_text_value(value):
        return value
    try:
        invalidate(REPO, node_id)
    except (OSError, TransactionFailure):
        pass
    return None


def _default_text_lookup(digest: str, pages: int) -> dict | None:
    """The derived value for one digest, or None on any miss.

    Lookup-only: a miss never builds (the caller extracts, exactly as
    the uncached path does). A hash-verified but wrongly shaped value
    invalidates and misses, like the dossier and receipt lookups.
    """
    node_id = _text_node_id(digest)
    inputs = _text_inputs(digest, pages)

    def _no_rebuild(_ctx: BuildContext) -> dict:
        raise DerivedError("text-cache lookup miss (no rebuild)")

    try:
        evaluation = evaluate(
            REPO, node_id,
            registry={node_id: (_text_spec(digest), _no_rebuild)},
            inputs=inputs)
    except (OSError, DerivedError, TransactionFailure, ValueError):
        return None
    return _checked_text_value(node_id, evaluation.value)


def _default_text_lookups(pairs: list[tuple[str, int]]) -> dict[tuple[str, int], dict | None]:
    """Lookup-only values for many digests sharing one session.

    One `evaluate_many` serves every warm hit with one session's
    identity costs; a miss aborts the batch (lookup builds never
    rebuild), and then each pair resolves singly, exactly as
    `_default_text_lookup` does. Read-only either way: hits never
    write, and a wrongly shaped value invalidates and misses.
    """
    unique = list(dict.fromkeys(pairs))
    if not unique:
        return {}

    def _no_rebuild(_ctx: BuildContext) -> dict:
        raise DerivedError("text-cache lookup miss (no rebuild)")

    registry = {
        _text_node_id(digest): (_text_spec(digest), _no_rebuild)
        for digest, _pages in unique
    }
    inputs: dict[str, str] = {}
    for digest, pages in unique:
        inputs.update(_text_inputs(digest, pages))
    try:
        evaluations = evaluate_many(
            REPO, [_text_node_id(digest) for digest, _pages in unique],
            registry=registry, inputs=inputs)
    except (OSError, DerivedError, TransactionFailure, ValueError):
        return {pair: _default_text_lookup(*pair) for pair in unique}
    return {
        (digest, pages): _checked_text_value(
            _text_node_id(digest), evaluations[_text_node_id(digest)].value)
        for digest, pages in unique
    }


def _value_matches_inputs(value: dict, digest: str, pages: int) -> bool:
    """Whether the stored proof agrees with the live freshness facts.

    The key already required them; the value must agree too, or a
    value persisted under different facts would be served.
    """
    return (
        value.get("digest") == digest
        and value.get("pages") == pages
        and value.get("extractor") == EXTRACTOR
        and len(value.get("texts", [])) == pages
    )


def _texts_match_index(value: dict, cache: Path, digest: str) -> bool:
    """Whether the node's texts are exactly the verified file bytes."""
    record = cache_index(cache, digest)
    if record is None:
        return False
    hashed = [hashlib.sha256(text.encode("utf-8")).hexdigest()
              for text in value["texts"]]
    return hashed == record.get("pages_sha256")


def _persist_text_node(digest: str, rel: str, cache: Path, pages: int) -> None:
    """Persist one digest's texts as its derived value (best-effort).

    Reads the just-published views back (the bytes `_extract`
    admitted); any failure simply misses next run and re-extracts —
    the cache stays auxiliary and never fails the build.
    """
    try:
        texts = [(cache / digest / f"pp-{page:04d}.txt").read_text(encoding="utf-8")
                 for page in range(1, pages + 1)]
    except (OSError, ValueError):
        return
    value = {
        "digest": digest,
        "material": rel,
        "pages": pages,
        "extractor": EXTRACTOR,
        "texts": texts,
        "pages_sha256": [hashlib.sha256(text.encode("utf-8")).hexdigest()
                         for text in texts],
    }
    node_id = _text_node_id(digest)

    def _fixed(_ctx: BuildContext) -> dict:
        return value

    try:
        evaluate(
            REPO, node_id,
            registry={node_id: (_text_spec(digest), _fixed)},
            inputs=_text_inputs(digest, pages))
    except (OSError, DerivedError, TransactionFailure, ValueError):
        return


def _project_views(path: Path, digest: str, rel: str, cache: Path,
                   pages: int, texts: list[str]) -> bool:
    """Rewrite one digest's file views from its node texts.

    Byte-identical publication to `_extract` (same staging name, same
    page and index bytes): the node value is the authority, the files
    its views. Admits only text for the bytes the digest names — a
    source that changed since the lookup publishes nothing — and any
    write failure publishes nothing either, so the caller extracts
    instead. Returns True only when the views were published.
    """
    if len(texts) != pages or sha256(path) != digest:
        return False
    staging = cache / f".{digest}.staging"
    try:
        if staging.is_symlink() or staging.is_file():
            staging.unlink()
        elif staging.is_dir():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        hashes = []
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
        # Admit only text for the bytes the digest names: a source that
        # changed during projection publishes nothing under this digest.
        if sha256(path) != digest:
            return False
        target = cache / digest
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        staging.rename(target)
    except OSError:
        return False
    finally:
        if staging.is_symlink() or staging.is_file():
            try:
                staging.unlink()
            except OSError:
                pass
        elif staging.is_dir():
            shutil.rmtree(staging, ignore_errors=True)
    return True


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


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", action="store_true", help="cache every PDF in the manifest")
    parser.add_argument("--refresh", action="store_true",
                        help="cache missing digests and prune orphans (default)")
    parser.add_argument("--manifest", default=str(MANIFEST), help="materials manifest path")
    parser.add_argument("--materials-root", default=None, help="materials tree root")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR), help="cache root")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
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
    default_cache = _is_default_cache(cache)

    recorded = (manifest.get("files") or {})
    cached = extracted = healed = 0
    skipped: list[dict] = []
    stale: list[str] = []
    live: set[str] = set()
    pending: list[tuple[str, Path, str, int, bool]] = []
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
        if default_cache:
            # File facts now; the node's lookup joins one shared
            # session below, so a run pays one session's identity
            # costs however many materials it holds.
            pending.append((rel, path, digest, pages,
                            _index_valid(cache, digest, pages)))
            continue
        if _index_valid(cache, digest, pages):
            cached += 1
            continue
        outcome = _extract(path, digest, rel, cache, pages)
        if "pages" in outcome:
            extracted += 1
        else:
            skipped.append(outcome)
    if pending:
        values = _default_text_lookups(
            [(digest, pages) for _, _, digest, pages, _ in pending])
        for rel, path, digest, pages, files_ok in pending:
            value = values[(digest, pages)]
            if value is None:
                # A batch miss resolves singly now, picking up any node
                # or view this run published for a shared digest — the
                # same interleaving as one lookup per material.
                value = _default_text_lookup(digest, pages)
                files_ok = _index_valid(cache, digest, pages)
            if (value is not None and files_ok
                    and _texts_match_index(value, cache, digest)):
                cached += 1
                continue
            if (value is not None and not files_ok
                    and _value_matches_inputs(value, digest, pages)
                    and _project_views(
                        path, digest, rel, cache, pages, value["texts"])):
                cached += 1
                continue
            outcome = _extract(path, digest, rel, cache, pages)
            if "pages" in outcome:
                _persist_text_node(digest, rel, cache, pages)
                extracted += 1
            else:
                skipped.append(outcome)
        # Phase-1 refusals precede phase-3 outcomes above; restore the
        # manifest order a single pass produces.
        order = {rel: index for index, rel in enumerate(sorted(recorded))}
        skipped.sort(key=lambda entry: order[entry["material"]])
    pruned = _prune(cache, live) if (args.refresh or not args.build) else 0
    print(json.dumps({"cached": cached, "extracted": extracted,
                      "healed": healed, "skipped": skipped, "stale": sorted(stale),
                      "pruned": pruned, "cache": str(cache)},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
