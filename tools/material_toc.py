#!/usr/bin/env python3
"""Read a local material's own table of contents, and check a locator against it.

A locator is only worth writing if it can be checked. `"Chapter 9"` of a
700-page book cannot: nothing in the repository knows where Chapter 9 starts,
so nothing can tell a correct locator from a stale one after a re-download or
an edition change. This tool closes that gap from the material side.

Two modes:

    --toc      print the material's own outline (PDF bookmarks) or, when a PDF
               carries none, scan the opening pages for a printed contents
               list. Use it while authoring a locator.
    --verify   given a page and a heading, confirm the page actually contains
               it. Use it when a locator is questioned or a file was replaced.

**Page numbers are PDF page numbers throughout** — the number the reader types
into a viewer's page box, counting the cover as 1. Printed page numbers are not
used anywhere in this repository: they disagree with the viewer by a per-book
offset, which is exactly the ambiguity an exact locator exists to remove.
`system/PLAN-CREATION-SOP.md` states the convention; this tool is what makes it
checkable.

Usage:
    python tools/material_toc.py --toc  material://source-x/book.pdf [--depth 2]
    python tools/material_toc.py --toc  ../materials/path/to/book.pdf
    python tools/material_toc.py --verify ../materials/path/book.pdf --page 382 \
        --expect "Parameterschätzung"
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from learning_os.materials_resolution import (  # noqa: E402
    PathBoundaryError,
    material_uri_authority,
    resolve_material_target,
)

REPO = Path(__file__).resolve().parents[1]
MATERIALS = REPO.parent / "materials"


def _resolution_roots() -> tuple[Path, Path]:
    """Where a ``material://`` payload starts, and the boundary it may not leave.

    ``materials/.flat/`` holds one ``source-<id>`` alias per registered source
    and is the id-based resolution root when it exists; the physical topic tree
    is the fallback. This mirrors ``Repo.materials_root`` exactly — the point of
    this tool is to answer the same question the manifest answers.
    """
    flat = MATERIALS / ".flat"
    root = flat if not flat.is_symlink() and flat.is_dir() else MATERIALS
    return root, MATERIALS


def resolve(ref: str) -> Path:
    """`material://<source-id>/<rest>` or an ordinary path.

    The complete relative path decides which file this is. An earlier version
    scanned the whole tree and matched the final filename, so a request for
    ``source-x/b/chapter.pdf`` could be answered with ``source-x/a/chapter.pdf``
    — and this tool exists to *establish* locator evidence, so that answer
    looked like a successful verification. Ambiguity and absence now fail
    closed.
    """
    if not ref.startswith("material://"):
        path = Path(ref)
        return path if path.is_absolute() else (Path.cwd() / path).resolve()

    if material_uri_authority(ref) is None:
        raise SystemExit(f"unsafe or malformed material URI: {ref}")

    root, boundary = _resolution_roots()
    payload = ref[len("material://"):]
    authority, _, rest = payload.partition("/")
    # A source folder may be spelled with or without its `source-` prefix.
    # Both spellings are tried, but two existing candidates are an ambiguity
    # the caller must resolve — never a silent pick.
    spellings = [authority]
    alternative = (authority.removeprefix("source-") if authority.startswith("source-")
                   else f"source-{authority}")
    if alternative != authority:
        spellings.append(alternative)

    found: list[Path] = []
    failures: list[str] = []
    for spelling in spellings:
        candidate = f"material://{spelling}/{rest}" if rest else f"material://{spelling}"
        try:
            found.append(resolve_material_target(
                candidate, resolution_root=root, boundary_root=boundary))
        except (PathBoundaryError, FileNotFoundError, OSError) as exc:
            failures.append(str(exc))
    unique = sorted({path.resolve() for path in found})
    if len(unique) > 1:
        listed = ", ".join(str(path) for path in unique)
        raise SystemExit(f"ambiguous material reference {ref}: {listed}")
    if not unique:
        raise SystemExit(
            f"no material at the exact path named by {ref} under {root}"
            + (f" ({failures[0]})" if failures else "")
        )
    return unique[0]


def outline_toc(path: Path, depth: int) -> list[tuple[int, str, int | None]]:
    try:
        import pypdf
    except ImportError as exc:  # pragma: no cover - declared in pyproject
        raise SystemExit("pypdf is required: make setup") from exc
    reader = pypdf.PdfReader(str(path))
    rows: list[tuple[int, str, int | None]] = []

    def walk(items, level: int = 0) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
                continue
            if level > depth:
                continue
            try:
                page = reader.get_destination_page_number(item) + 1
            except Exception:
                page = None
            title = re.sub(r"\s+", " ", str(item.title)).strip()
            rows.append((level, title, page))

    walk(reader.outline)
    return rows


def page_text(path: Path, page: int) -> str:
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(path), "-"],
        capture_output=True, text=True,
    )
    return out.stdout


def printed_toc(path: Path, scan_pages: int) -> list[str]:
    """A PDF with no bookmarks still prints its contents; scan for it.

    Deliberately dumb: it returns the numbered lines it finds and says which
    PDF page they were printed on. Those numbers are the book's *printed*
    pages, so they still have to be resolved with --verify before they may be
    written into a locator.
    """
    rows: list[str] = []
    for page in range(1, scan_pages + 1):
        text = page_text(path, page)
        for line in text.splitlines():
            if re.match(r"^\s*\d+(\.\d+)*\.?\s+[A-ZÀ-Ü]", line):
                rows.append(f"[pdf p{page}] {line.strip()}")
    return rows


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("material", help="material:// reference or a path")
    parser.add_argument("--toc", action="store_true", help="print the table of contents")
    parser.add_argument("--depth", type=int, default=1,
                        help="outline nesting depth to print (default 1)")
    parser.add_argument("--scan", type=int, default=14,
                        help="pages to scan for a printed contents list (default 14)")
    parser.add_argument("--verify", action="store_true",
                        help="check that --page contains --expect")
    parser.add_argument("--page", type=int, help="PDF page number to check")
    parser.add_argument("--expect", help="heading text the page must contain")
    args = parser.parse_args(argv)

    path = resolve(args.material)
    if not path.exists():
        raise SystemExit(f"missing: {path}")

    if args.verify:
        if not args.page or not args.expect:
            raise SystemExit("--verify needs --page and --expect")
        found = normalise(args.expect) in normalise(page_text(path, args.page))
        print(f"{'OK  ' if found else 'MISS'} p{args.page} {args.expect!r} in {path.name}")
        return 0 if found else 1

    rows = outline_toc(path, args.depth)
    if rows:
        print(f"# {path.name} — PDF outline (PDF page numbers)")
        for level, title, page in rows:
            print("  " * level + f"{title}  [p{page if page else '?'}]")
        return 0

    print(f"# {path.name} — no PDF outline; printed contents scan "
          f"(numbers below are PRINTED pages, resolve with --verify)")
    for row in printed_toc(path, args.scan):
        print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
