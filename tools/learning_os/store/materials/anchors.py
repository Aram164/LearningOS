"""Exact-file quotation observations, scoped to one admission request."""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from urllib.parse import parse_qs, urlsplit

from learning_os.domain.snapshot import Repo
from learning_os.domain.verbatim import Quote, excerpt_digest, language, matches
from learning_os.store.materials.pdf_text import PDFTextError, pdf_page_text, pdf_reader
from learning_os.store.materials.resolution import (
    MATERIAL_SUFFIX_TOKEN,
    ResolvedMaterialFile,
    canonical_material_uri,
    material_location,
    material_uri_authority,
    materials_mount,
    resolve_route_material_files,
    single_file_material,
)
from learning_os.store.materials.slices import parse_locator_page_ranges

if TYPE_CHECKING:
    from pypdf import PdfReader

MaterialClass = Literal["local", "local-unresolved", "offline", "remote-unanchored"]
StatToken = tuple[int, int, int, int, int]
_TIMESTAMP = r"\d+:[0-5]\d(?::[0-5]\d)?"
_WINDOW_LINE = re.compile(rf"^\[({_TIMESTAMP})\]\s*(.*)$")
_LOCATOR_TIME = re.compile(rf"(?<![\w:])({_TIMESTAMP})(?![\w:])")


class AnchorError(ValueError):
    """The observation cannot prove the declared exact-file quotation."""


@dataclass(frozen=True)
class RouteMaterial:
    route_id: str
    source_id: str
    locator: str = ""
    vault_path: str = ""
    url: str = ""

    def row(self) -> dict[str, object]:
        return {"id": self.route_id, "source_id": self.source_id,
                "locator": self.locator, "vault_path": self.vault_path, "url": self.url}


@dataclass(frozen=True)
class MaterialSet:
    kind: MaterialClass
    files: tuple[ResolvedMaterialFile, ...] = ()


@dataclass(frozen=True)
class MaterialSnapshot:
    path: Path
    manifest_path: str
    content: bytes
    sha256: str
    stat_token: StatToken


@dataclass(frozen=True)
class AnchorProof:
    material_uri: str
    manifest_path: str
    material_sha256: str
    place: str
    quote_sha256: str = ""
    language: str = "und"

    @property
    def trail(self) -> str:
        if self.quote_sha256:
            suffix = f" lang={self.language}" if self.place.startswith("t") else ""
            return f"quote:{self.material_uri}#{self.place} {self.quote_sha256}{suffix}"
        return f"manifest:{self.manifest_path}#{self.place}"


@dataclass(frozen=True)
class Transcript:
    video_id: str
    grid: int
    duration: int
    windows: tuple[tuple[int, str], ...]


def seconds(value: str) -> int:
    if re.fullmatch(_TIMESTAMP, value) is None:
        raise AnchorError(f"invalid timestamp {value!r}")
    parts = [int(part) for part in value.split(":")]
    return sum(part * 60 ** index for index, part in enumerate(reversed(parts)))


def parse_transcript(content: bytes) -> Transcript:
    try:
        document = content.decode("utf-8")
    except UnicodeError as exc:
        raise AnchorError("transcript is not UTF-8") from exc
    grid_match = re.search(r"(?m)^- window:\s*(\d+)s\s*$", document)
    video_match = re.search(r"(?m)^- video_id:\s*`?([^`\s]+)`?\s*$", document)
    duration_match = re.search(rf"(?m)^- duration:\s*({_TIMESTAMP})\s*$", document)
    if grid_match is None or video_match is None or duration_match is None:
        raise AnchorError("transcript needs explicit window grid, video_id and duration headers")
    grid = int(grid_match[1])
    if grid <= 0:
        raise AnchorError("transcript window grid must be positive")
    duration = seconds(duration_match[1])
    windows: list[tuple[int, str]] = []
    for line in document.splitlines():
        match = _WINDOW_LINE.fullmatch(line)
        if match:
            start = seconds(match[1])
            if start % grid or start >= duration or (windows and start <= windows[-1][0]):
                raise AnchorError("transcript timestamps violate its ordered window grid")
            windows.append((start, match[2]))
    if not windows:
        raise AnchorError("transcript has no timestamped text")
    return Transcript(video_match[1], grid, duration, tuple(windows))


def _video_id(url: str) -> str | None:
    parsed = urlsplit(url)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/") or None
    if parsed.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        values = parse_qs(parsed.query).get("v")
        return values[0] if values else None
    return None


class AnchorReader:
    """One immutable byte snapshot and one PDF reader per unique physical file.

    The instance belongs to a single check or apply; nothing survives the
    request. Apply constructs a new reader and observes materials again.
    """

    def __init__(self, repo: Repo, manifest: Mapping[str, object], *,
                 previous_repo: Repo | None = None) -> None:
        self.repo = repo
        self.previous_repo = previous_repo or repo
        self.manifest = manifest
        self._snapshots: dict[Path, MaterialSnapshot] = {}
        self._aliases: dict[Path, Path] = {}
        self._pdfs: dict[Path, PdfReader] = {}
        self._pages: dict[tuple[Path, int], str] = {}

    def _source_material(self, route: RouteMaterial, *, previous: bool = False) -> str:
        repo = self.previous_repo if previous else self.repo
        source: object = repo.sources.get(route.source_id)
        value: object = source.get("material") if isinstance(source, dict) else None
        return value if isinstance(value, str) else ""

    def _explicit_file(self, route: RouteMaterial, *, previous: bool = False) -> bool:
        return bool(route.vault_path.startswith("material://") or MATERIAL_SUFFIX_TOKEN.search(
            route.locator) or single_file_material(self._source_material(route, previous=previous)))

    def materials(self, route: RouteMaterial, previous: RouteMaterial | None = None) -> MaterialSet:
        known_local = self._explicit_file(route) or bool(material_uri_authority(
            self._source_material(route)))
        if previous is not None:
            known_local |= self._explicit_file(previous, previous=True) or bool(material_uri_authority(
                self._source_material(previous, previous=True)))
        tree, _ = materials_mount(self.repo)
        if tree is None:
            return MaterialSet("offline" if known_local else "remote-unanchored")
        files = tuple(resolve_route_material_files(self.repo, route.row()))
        if files:
            return MaterialSet("local", files)
        return MaterialSet("local-unresolved" if known_local else "remote-unanchored")

    def snapshot(self, file: ResolvedMaterialFile) -> MaterialSnapshot:
        tree, why = materials_mount(self.repo)
        if tree is None:
            raise AnchorError(why)
        try:
            path = file.path.resolve(strict=True)
            relative = path.relative_to(tree.resolve()).as_posix()
            self._aliases[file.path] = path
            prior = self._snapshots.get(path)
            if prior is not None:
                self.assert_unchanged()
                return prior
            with path.open("rb") as handle:
                before = _stat_token(os.fstat(handle.fileno()))
                content = handle.read()
                after = _stat_token(os.fstat(handle.fileno()))
            if before != after:
                raise AnchorError("material changed while its byte snapshot was being read")
        except (OSError, ValueError, RuntimeError) as exc:
            raise AnchorError(f"material cannot be read safely: {file.material_uri}") from exc
        digest = hashlib.sha256(content).hexdigest()
        entry = self.manifest.get(relative)
        declared: object = entry.get("sha256") if isinstance(entry, dict) else None
        if not isinstance(declared, str) or declared.removeprefix("sha256:") != digest:
            raise AnchorError(f"material digest differs from the registered manifest: {relative}")
        observed = MaterialSnapshot(path, relative, content, digest, after)
        self._snapshots[path] = observed
        self.assert_unchanged()
        return observed

    def assert_unchanged(self) -> None:
        try:
            for alias, physical in self._aliases.items():
                if alias.resolve(strict=True) != physical:
                    raise AnchorError("material binding changed during admission")
            for snapshot in self._snapshots.values():
                if _stat_token(snapshot.path.stat()) != snapshot.stat_token:
                    raise AnchorError("material changed during admission; observe it again")
        except (OSError, RuntimeError) as exc:
            raise AnchorError("material became unavailable during admission") from exc

    def _quote_file(self, route: RouteMaterial, quote: Quote,
                    previous: RouteMaterial | None) -> ResolvedMaterialFile:
        if canonical_material_uri(quote.ref) != quote.ref:
            raise AnchorError("quote ref must use one canonical material URI")
        material = self.materials(route, previous)
        if material.kind == "offline":
            raise AnchorError("local material is offline; existence-only evidence cannot admit it")
        if material.files:
            found = next((file for file in material.files if file.material_uri == quote.ref), None)
            if found is None:
                raise AnchorError("quote names the wrong file for this route")
            return found
        if (self._explicit_file(route)
                or (material.kind == "local-unresolved" and not material_uri_authority(self._source_material(route)))
                or (previous is not None and self._explicit_file(previous, previous=True))):
            raise AnchorError("known local material is unresolved; removing or confusing its binding cannot downgrade it")
        # A URL-only route may explicitly bind a transcript under its declared
        # authority. This is not a basename search or an inferred transcript.
        authority = material_uri_authority(self._source_material(route))
        if authority is None or material_uri_authority(quote.ref) != authority:
            raise AnchorError("quote is outside the route source's declared material authority")
        location = material_location(self.repo, quote.ref)
        relative = location.get("material_path")
        if not isinstance(relative, str) or location.get("material_exists") is not True:
            raise AnchorError("quoted material cannot be resolved")
        if _video_id(route.url) is None:
            raise AnchorError("unbound transcript requires an exact supported video URL")
        return ResolvedMaterialFile(quote.ref, self.repo.learningos_root / relative)

    def _page(self, snapshot: MaterialSnapshot, page: int) -> str:
        key = snapshot.path, page
        if key not in self._pages:
            try:
                reader = self._pdfs.get(snapshot.path)
                if reader is None:
                    reader = pdf_reader(snapshot.content)
                    self._pdfs[snapshot.path] = reader
                self._pages[key] = pdf_page_text(reader, page)
            except PDFTextError as exc:
                raise AnchorError(str(exc)) from exc
        return self._pages[key]

    def _pdf_text(self, route: RouteMaterial, file: ResolvedMaterialFile,
                  snapshot: MaterialSnapshot, page: int, page_end: int | None) -> str:
        locator = route.locator
        if ";" in locator:
            name = file.material_uri.rsplit("/", 1)[-1]
            parts = [part for part in locator.split(";") if name in part]
            if len(parts) != 1:
                raise AnchorError("multi-file locator does not identify the quoted file's page span")
            locator = parts[0]
        ranges = parse_locator_page_ranges(locator)
        pages = (page,) if page_end is None else (page, page_end)
        if ranges and (min(pages) < min(start for start, _ in ranges)
                       or max(pages) > max(end for _, end in ranges)):
            raise AnchorError("quote page is outside this file's locator span")
        return "\n".join(self._page(snapshot, number) for number in pages)

    def verify_quote(self, route: RouteMaterial, quote: Quote,
                     previous: RouteMaterial | None = None) -> AnchorProof:
        file = self._quote_file(route, quote, previous)
        snapshot = self.snapshot(file)
        if snapshot.path.suffix.casefold() == ".pdf":
            if quote.page is None:
                raise AnchorError("PDF quotation requires an explicit page")
            observed = self._pdf_text(route, file, snapshot, quote.page, quote.page_end)
            place = f"p{quote.page}" + (f"-{quote.page_end}" if quote.page_end else "")
        elif snapshot.path.suffix.casefold() in {".md", ".txt"}:
            if quote.window is None or quote.window.count("-") != 1:
                raise AnchorError("transcript quotation requires an explicit timestamp window")
            transcript = parse_transcript(snapshot.content)
            if route.url and transcript.video_id != _video_id(route.url):
                raise AnchorError("transcript video_id differs from the route URL")
            start, end = (seconds(part) for part in quote.window.split("-"))
            if (not 0 <= start < end <= transcript.duration or end - start > 300
                    or start % transcript.grid or (end % transcript.grid and end != transcript.duration)):
                raise AnchorError("quote window must lie on the transcript grid, within its duration, and span at most 5:00")
            times = [seconds(match[1]) for match in _LOCATOR_TIME.finditer(route.locator)]
            if times and (end <= max(0, min(times) - 300) or start >= max(times) + 300):
                raise AnchorError("quote window does not overlap the locator's timestamp neighborhood")
            observed = "\n".join(text for time, text in transcript.windows if start <= time < end)
            place = "t" + quote.window
        else:
            raise AnchorError("material format has no quotation reader; use explicit manifest evidence with a note")
        if not observed.strip():
            raise AnchorError("cited place has no text layer; use manifest evidence with this explicit place and a note")
        if not matches(quote.text, observed):
            raise AnchorError(f"quote not found at the cited place (excerpt language={language(quote.text)}, material language={language(observed)})")
        self.assert_unchanged()
        return AnchorProof(file.material_uri, snapshot.manifest_path, snapshot.sha256,
                           place, excerpt_digest(quote.text), language(observed))

    def verify_unreadable(self, route: RouteMaterial, ref: str, note: str,
                          page: int | None = None, previous: RouteMaterial | None = None) -> AnchorProof:
        if not note.strip():
            raise AnchorError("manifest fallback needs an explicit verification note")
        material = self.materials(route, previous)
        if material.kind != "local":
            raise AnchorError("manifest fallback requires fully resolved local material")
        for file in material.files:
            snapshot = self.snapshot(file)
            if snapshot.manifest_path != ref:
                continue
            suffix = snapshot.path.suffix.casefold()
            if suffix == ".pdf":
                if type(page) is not int or page < 1:
                    raise AnchorError("unreadable PDF fallback requires an explicit page")
                if self._pdf_text(route, file, snapshot, page, None).strip():
                    raise AnchorError("cited PDF page is readable and requires a quotation")
                place = f"p{page}"
            elif suffix in {".md", ".txt"}:
                raise AnchorError("readable text material requires a quotation")
            else:
                place = "unsupported-format"
            self.assert_unchanged()
            return AnchorProof(file.material_uri, ref, snapshot.sha256, place)
        raise AnchorError("manifest fallback names the wrong file for this route")


def _stat_token(value: os.stat_result) -> StatToken:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
