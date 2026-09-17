"""Bounded readable slices of exact route material for AI-action bundles.

``unit.compare-materials`` must judge the material itself, not its metadata:
``contribution``, ``assumptions``, ``notation``, ``exercise_value``,
``best_for`` and ``limitations`` cannot be evidenced from a locator string.
This module resolves every deep-review route to its exact local files (one
shared rule, via ``materials_resolution``) and extracts a bounded,
citable text slice per file — at most ``MAX_SLICE_PAGES`` PDF pages or
``MAX_TEXT_SLICE_BYTES`` of plain text — so the whole bundle stays under
``MAX_SLICE_BYTES_TOTAL``.

Page numbers are PDF page numbers throughout (cover = 1), the convention
``tools/material_toc.py`` enforces; printed page numbers are never used.
Where the authored locator names explicit ranges (``pdf pp. 310-322``,
``slides 20-38``), those pages are preferred; otherwise the slice starts at
page 1. A slice that hits the cap says so in its header — the agent must
report the truncation in ``limitations``, never claim pages it did not see.

Deliberate non-goals: no relevance ranking, no embeddings, no OCR. A file
with no extractable text (image-only scans) or without a bounded text
reader is not silently skipped: for a mandatory route that is a
``SliceResolutionError`` naming the route, and ``prepare()`` must fail
closed instead of producing a seemingly complete dossier.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .materials_resolution import (
    ResolvedMaterialFile,
    resolve_route_material_files,
)

#: Scopes whose routes must carry a readable slice into the compare bundle.
#: Anything else stays metadata-only and may honestly be screened.
MANDATORY_SLICE_SCOPES = frozenset({"current", "prerequisite"})

#: Per-file page ceiling for PDF slices. No route-count ceiling exists: every
#: mandatory route appears in the dossier (the synthesis validator rejects
#: coverage gaps), so boundedness comes from pages and bytes, never from
#: dropping routes.
MAX_SLICE_PAGES = 12

#: Hard ceiling over all rendered slice documents in one bundle. When the
#: mandatory slices do not fit, preparation fails naming the route that
#: tipped the budget over — it never silently drops a route.
MAX_SLICE_BYTES_TOTAL = 1_000_000

#: Byte ceiling for plain-text slices (.md/.txt), which have no pages.
MAX_TEXT_SLICE_BYTES = 100_000

#: Suffixes with a trivial bounded text reader. PDFs go through pypdf;
#: anything else (slides decks, notebooks, videos) has no reader here.
READABLE_TEXT_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

SLICE_BUNDLE_PREFIX = "attachments/slices"


class SliceResolutionError(Exception):
    """One mandatory route's exact material cannot be read as a bounded slice."""

    def __init__(self, route_id: str, reason: str):
        self.route_id = route_id
        super().__init__(f"route {route_id} requires deep review but {reason}")


@dataclass(frozen=True)
class SlicePart:
    """The extracted text of one resolved file inside a route's slice."""

    material_uri: str
    kind: str  # "pdf" or "text"
    pages: tuple[int, ...] = ()
    page_total: int | None = None
    status: str = "complete"
    text: str = ""


@dataclass(frozen=True)
class MaterialSlice:
    """One route's bounded readable material plus the binding metadata."""

    route_id: str
    source_id: str
    locator: str
    material_checksum: str
    parts: tuple[SlicePart, ...] = ()
    slice_sha256: str = ""
    bundle_path: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_path", f"{SLICE_BUNDLE_PREFIX}/{self.route_id}.md")


_PRINTED_PAREN = re.compile(r"\([^()]*print[^()]*\)", re.IGNORECASE)
_PDF_RANGE = re.compile(r"(?:pdf\s+)?p{1,2}\.\s*(\d+)\s*[-\u2013]\s*(\d+)",
                        re.IGNORECASE)
_SLIDE_RANGE = re.compile(r"\bslides?\s+(\d+)\s*[-\u2013]\s*(\d+)", re.IGNORECASE)
_AND_PAGES = re.compile(r"\bpp?\.?\s*(\d+)\s+and\s+(\d+)\b", re.IGNORECASE)
_PDF_SINGLE = re.compile(r"(?:physical\s+)?pdf\s+p\.?\s*(\d+)\b", re.IGNORECASE)
_BARE_SINGLE = re.compile(r"(?<!printed )(?<!\w)p\.\s*(\d+)\b", re.IGNORECASE)


def parse_locator_page_ranges(locator: str) -> list[tuple[int, int]]:
    """Explicit PDF page ranges named by an authored locator, in order.

    Only the house style counts: ``pdf pp. X-Y``, ``PDF p. X``,
    ``slides X-Y`` and ``pp. X and Y``. Parenthesised printed-page notes
    (``(printed p. 127)``) are stripped first — printed numbers disagree
    with PDF numbers by a per-book offset and must never become slice
    pages. Video timestamps (``03:25-04:55``) carry no keyword and never
    match. Returns ``[]`` when the locator names no pages.
    """
    if not isinstance(locator, str):
        return []
    text = _PRINTED_PAREN.sub("", locator)
    ranges: list[tuple[int, int]] = []
    for pattern in (_PDF_RANGE, _SLIDE_RANGE):
        for match in pattern.finditer(text):
            start, end = int(match.group(1)), int(match.group(2))
            if 1 <= start <= end:
                ranges.append((start, end))
    for match in _AND_PAGES.finditer(text):
        for group in (match.group(1), match.group(2)):
            page = int(group)
            if page >= 1:
                ranges.append((page, page))
    for pattern in (_PDF_SINGLE, _BARE_SINGLE):
        for match in pattern.finditer(text):
            page = int(match.group(1))
            if page >= 1:
                ranges.append((page, page))
    return list(dict.fromkeys(ranges))


def _select_pages(total: int, requested: list[tuple[int, int]]) -> tuple[tuple[int, ...], str]:
    """Clamp requested (or default) pages to ``MAX_SLICE_PAGES`` with a status."""
    if total < 1:
        return (), "complete"
    if not requested:
        selected = list(range(1, min(total, MAX_SLICE_PAGES) + 1))
        status = "complete" if total <= MAX_SLICE_PAGES else "truncated"
        return tuple(selected), status
    wanted: list[int] = []
    for start, end in requested:
        for page in range(start, min(end, total) + 1):
            if page not in wanted:
                wanted.append(page)
    if requested and not wanted:
        return (), "out-of-range"
    if len(wanted) > MAX_SLICE_PAGES:
        return tuple(wanted[:MAX_SLICE_PAGES]), "range-truncated"
    return tuple(wanted), "complete"


def _read_pdf_part(route_id: str, material_uri: str, path: Path, locator: str) -> SlicePart:
    try:
        import pypdf
    except ImportError as exc:
        raise SliceResolutionError(
            route_id, "pypdf is required for PDF slices: make setup") from exc
    try:
        reader = pypdf.PdfReader(str(path))
        total = len(reader.pages)
    except Exception as exc:
        raise SliceResolutionError(
            route_id, f"its file cannot be parsed as PDF: {exc}") from exc
    pages, status = _select_pages(total, parse_locator_page_ranges(locator))
    raw: list[tuple[int, str]] = []
    for page in pages:
        try:
            text = reader.pages[page - 1].extract_text() or ""
        except Exception:
            text = ""
        raw.append((page, text))
    if not any(text.strip() for _, text in raw):
        raise SliceResolutionError(route_id, "its file yields no extractable text")
    chunks = [f"--- PDF p.{page} ---\n{text.strip()}\n" for page, text in raw]
    return SlicePart(
        material_uri=material_uri,
        kind="pdf",
        pages=pages,
        page_total=total,
        status=status,
        text="".join(chunks),
    )


def _read_text_part(route_id: str, material_uri: str, path: Path) -> SlicePart:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SliceResolutionError(route_id, f"its file cannot be read: {exc}") from exc
    status = "complete"
    if len(text.encode("utf-8")) > MAX_TEXT_SLICE_BYTES:
        text = text.encode("utf-8")[:MAX_TEXT_SLICE_BYTES].decode("utf-8", errors="ignore")
        status = "truncated"
    return SlicePart(material_uri=material_uri, kind="text", status=status, text=text)


def _read_part(route_id: str, resolved: ResolvedMaterialFile, locator: str) -> SlicePart:
    suffix = resolved.path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf_part(route_id, resolved.material_uri, resolved.path, locator)
    if suffix in READABLE_TEXT_SUFFIXES:
        return _read_text_part(route_id, resolved.material_uri, resolved.path)
    raise SliceResolutionError(
        route_id, f"its format {suffix or '(none)'} has no bounded text reader"
    )


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def slice_content_digest(slice_: MaterialSlice) -> str:
    """Content hash of one slice: route, material checksum and part texts.

    This deliberately does NOT hash the rendered document (which contains
    the digest itself — a circular definition). It identifies the extracted
    content for transport integrity and, most importantly, is unmistakably
    not the material checksum the synthesis validator demands.
    """
    canonical = json.dumps({
        "route_id": slice_.route_id,
        "source_id": slice_.source_id,
        "locator": slice_.locator,
        "material_checksum": slice_.material_checksum,
        "parts": [
            {
                "material_uri": part.material_uri,
                "kind": part.kind,
                "pages": list(part.pages),
                "page_total": part.page_total,
                "status": part.status,
                "text": part.text,
            }
            for part in slice_.parts
        ],
    }, sort_keys=True, separators=(",", ":"))
    return _sha256_text(canonical)


def render_slice_markdown(slice_: MaterialSlice) -> bytes:
    """Render one slice document to its bundle bytes."""
    lines = [
        f"# Material slice — {slice_.route_id}",
        "",
        f"- source_id: {slice_.source_id}",
        f"- locator: {slice_.locator}",
        "- material_checksum: " + slice_.material_checksum,
        "  (canonical basis; use this as evidence[].checksum)",
        "- slice_sha256: " + (slice_.slice_sha256 or "(pending)"),
        "  (content hash over route, material checksum and extracted texts;",
        "  never use as evidence checksum)",
    ]
    for part in slice_.parts:
        if part.kind == "pdf":
            shown = f"PDF pp. {part.pages[0]}-{part.pages[-1]}" if part.pages else "no pages"
            lines.append(
                f"- part: {part.material_uri}, {shown} of {part.page_total}, "
                f"status {part.status}, {len(part.text)} chars"
            )
        else:
            lines.append(
                f"- part: {part.material_uri}, plain text, "
                f"status {part.status}, {len(part.text)} chars"
            )
    lines += [
        "- extraction: pypdf extract_text for PDFs; formulas, tables and layout "
        "may be degraded — cite page numbers, note gaps, do not invent symbols",
        "",
        "---",
    ]
    for part in slice_.parts:
        lines += ["", f"## {part.material_uri}", "", part.text.rstrip(), ""]
    lines.append("---")
    return ("\n".join(lines) + "\n").encode("utf-8")


def slice_index_entry(slice_: MaterialSlice) -> dict[str, Any]:
    """Machine-readable slice record for ``attachments/slices/index.json``."""
    return {
        "route_id": slice_.route_id,
        "source_id": slice_.source_id,
        "locator": slice_.locator,
        "material_checksum": slice_.material_checksum,
        "slice_sha256": slice_.slice_sha256,
        "bundle_path": slice_.bundle_path,
        "parts": [
            {
                "material_uri": part.material_uri,
                "kind": part.kind,
                "pages": list(part.pages),
                "page_total": part.page_total,
                "status": part.status,
                "chars": len(part.text),
            }
            for part in slice_.parts
        ],
    }


def build_unit_slices(
    repo: Any,
    routes: list[dict[str, Any]],
    *,
    basis: dict[str, Any],
) -> list[tuple[MaterialSlice, bytes]]:
    """Bounded slices for every mandatory-scope route, or raise naming the route.

    ``basis`` is the unit's current material basis (as computed for the
    request): each slice binds the same ``material_checksums[route_id]`` the
    synthesis validator later demands in ``evidence[].checksum``. Routes
    outside ``MANDATORY_SLICE_SCOPES`` are skipped — they stay metadata-only
    and may honestly be screened. The total rendered budget is enforced
    incrementally: the route that tips it over is named, nothing is dropped.
    """
    checksums = basis.get("material_checksums") or {}
    slices: list[tuple[MaterialSlice, bytes]] = []
    spent = 0
    for route in routes:
        if route.get("scope") not in MANDATORY_SLICE_SCOPES:
            continue
        route_id = str(route.get("id"))
        checksum = checksums.get(route_id)
        if not isinstance(checksum, str):
            raise SliceResolutionError(route_id, "it has no material checksum in the current basis")
        try:
            files = resolve_route_material_files(repo, route)
        except Exception as exc:
            raise SliceResolutionError(
                route_id, f"its material cannot be resolved: {exc}") from exc
        if not files:
            raise SliceResolutionError(
                route_id,
                f"its exact material cannot be resolved from locator {route.get('locator')!r}",
            )
        parts = tuple(
            _read_part(route_id, resolved, str(route.get("locator"))) for resolved in files
        )
        if not any(part.text.strip() for part in parts):
            raise SliceResolutionError(route_id, "its file yields no extractable text")
        pending = MaterialSlice(
            route_id=route_id,
            source_id=str(route.get("source_id")),
            locator=str(route.get("locator")),
            material_checksum=checksum,
            parts=parts,
        )
        digest = slice_content_digest(pending)
        body = render_slice_markdown(replace(pending, slice_sha256=digest))
        spent += len(body)
        if spent > MAX_SLICE_BYTES_TOTAL:
            raise SliceResolutionError(
                route_id,
                f"its slice tips the bundle over the {MAX_SLICE_BYTES_TOTAL}-byte ceiling",
            )
        slices.append((replace(pending, slice_sha256=digest), body))
    return slices
