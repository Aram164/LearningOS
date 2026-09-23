#!/usr/bin/env python3
"""Reconcile the old learning-resource lists against the source registry.

A bounded, read-only audit tool for the two-pass source intake
(``work/active/workspace-library-reconciliation``). It answers "where did each
old item go?" occurrence by occurrence rather than trusting a registered-source
count, which OPERATOR rule 14 forbids as evidence of completeness.

It reads only the files named in ``inputs/declared-inputs.yaml`` -- no
recursive discovery -- and hashes every one of them. Each URL, local file name,
registered source ID, and locator-less resource entry in an origin file is an
*occurrence* with a stable ``key:line:kindN`` reference. The reviewed
``outputs/dispositions.yaml`` assigns every occurrence to a teaching object and
so to exactly one of seven dispositions. The normal ``check`` verifies the
frozen pre-intake review. ``check --applied`` verifies that reviewed targets,
links and provenance now exist while retaining the original input hashes;
``report --applied`` freezes that final proof separately. The tool never writes
canonical records; ``merge``, ``freeze`` and ``report`` write only inside the
workspace.

    python tools/library_reconciliation.py check   --workspace WS [--json]
    python tools/library_reconciliation.py check   --workspace WS --applied --report
    python tools/library_reconciliation.py report  --workspace WS
    python tools/library_reconciliation.py report  --workspace WS --applied
    python tools/library_reconciliation.py suggest --workspace WS --out F --worklist F
    python tools/library_reconciliation.py merge   --workspace WS FILE...
    python tools/library_reconciliation.py freeze  --workspace WS
    python tools/library_reconciliation.py extract --workspace WS [--key KEY] [--json]
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import yaml

TOOLS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_ROOT.parent

INPUTS_SCHEMA = "library-reconciliation-inputs/v1"
DISPOSITIONS_SCHEMA = "library-reconciliation-dispositions/v1"
DECLARED_INPUTS = "inputs/declared-inputs.yaml"
DISPOSITIONS_FILE = "outputs/dispositions.yaml"
REPORT_FILE = "outputs/reconciliation-report.md"
APPLIED_REPORT_FILE = "outputs/applied-check.json"

# The seven occurrence dispositions named by the plan, in report order.
DISPOSITIONS = (
    "existing-active-source",
    "existing-masters-candidate",
    "new-active-source",
    "new-masters-candidate",
    "alias-or-duplicate",
    "unresolved",
    "out-of-scope",
)
# An object's kind is a disposition; alias-or-duplicate is a role on an object.
OBJECT_KINDS = tuple(d for d in DISPOSITIONS if d != "alias-or-duplicate")
PSEUDO_KINDS = frozenset({"unresolved", "out-of-scope"})
ROLES = ("landing", "child", "companion", "alias", "duplicate", "mention", "local", "reference")
REDUNDANT_ROLES = frozenset({"alias", "duplicate"})
LINKED_ROLES = frozenset({"child", "companion"})
KIND_LETTER = {"url": "u", "path": "p", "source-ref": "s", "entry": "e"}
KIND_ORDER = {"url": 0, "path": 1, "source-ref": 2, "entry": 3}
DEFAULT_ROLE = {"url": "landing", "path": "local", "source-ref": "reference", "entry": "mention"}
ALLOWED_ROLES = {
    "url": frozenset({"landing", "child", "companion", "alias", "duplicate"}),
    "path": frozenset({"local", "alias", "duplicate"}),
    "source-ref": frozenset({"reference", "duplicate"}),
    "entry": frozenset({"mention", "duplicate"}),
}

SOURCE_ID = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$")
CANDIDATE_ID = re.compile(r"^candidate-source-[a-z0-9]+(?:-[a-z0-9]+)*$")
PSEUDO_ID = re.compile(r"^(?:out-of-scope|unresolved):[a-z0-9]+(?:-[a-z0-9]+)*$")
THEMATIC_GROUP_ID = re.compile(r"^thematic-group-[a-z0-9]+(?:-[a-z0-9]+)*$")
REF = re.compile(r"^(?P<key>[a-z0-9][a-z0-9-]*):(?P<line>[1-9][0-9]*):(?P<kind>[upse])(?P<n>[1-9][0-9]*)$")
LINE_REF = re.compile(r"^(?P<key>[a-z0-9][a-z0-9-]*):(?P<line>[1-9][0-9]*)$")
SOURCE_TYPES = frozenset({"book", "paper", "lecture", "course", "video", "website",
                          "documentation", "software", "conversation", "other"})

MD_LINK = re.compile(
    r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(\s*<?(https?://(?:[^()\s<>]|\([^()\s]*\))+)>?"
    r"(?:\s+\"[^\"]*\")?\s*\)")
AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
BARE_URL = re.compile(r"https?://[^\s<>\[\]()|`\"']+")
TICKED = re.compile(r"`([^`\n]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<body>\S.*)$")
TRAILING = ".,;:!?*_'\""
FILE_EXTENSIONS = (".pdf", ".ipynb", ".epub", ".djvu", ".zip", ".md", ".txt", ".csv", ".py",
                   ".pptx", ".ppt", ".key", ".tex", ".html", ".docx", ".xlsx", ".mp4", ".json")
PATH_ROOTS = frozenset({
    "Plans", "Masters-Planning", "materials", "LearningOS", "knowledge", "root", "legacy",
    "SaD", "Algo2", "Analysis", "AML", "AMLS", "Python", "Books", "Buecher", "Bücher",
    "learningcontent", "work", "curriculum", "sources", "records"})
STOPWORDS = frozenset("""
    a an and are as at be by das de der des die ein eine for from in is it its mit of on or
    the to und von with zu zum zur als auf aus bei fur im ist nach oder sich uber vom
    course kurs book buch lecture lectures notes paper papers video videos playlist free
""".split())
MOSES_HOST = "moseskonto.tu-berlin.de"
GENERIC_NAMES = frozenset({"readme.md", "index.md", "notes.md", "context.md", "readme.txt"})


class ReconciliationError(Exception):
    """A declaration or dispositions file cannot be used as written."""


# --------------------------------------------------------------------- inputs
@dataclass(frozen=True)
class Origin:
    key: str
    path: str
    kind: str
    scope: str
    entries: bool
    skip_table_headers: tuple[str, ...] = ()
    note: str = ""


@dataclass
class Declared:
    workspace: Path
    umbrella: Path
    origins: list[Origin]
    registry_dir: str
    registry_files: list[str]
    registry_consolidated: str | None
    collections_dir: str
    collection_files: list[str]
    masters_collections: list[str]
    masters_catalog: str | None
    materials_manifest: str
    materials_placement: str
    resolvers: dict[str, str]
    identical_copies: list[dict]
    not_declared: list[dict]
    baseline: str | None

    def path(self, relative: str) -> Path:
        return self.umbrella / relative

    def registry_paths(self) -> list[str]:
        paths = [f"{self.registry_dir}/{name}" for name in self.registry_files]
        if self.registry_consolidated:
            paths.insert(0, self.registry_consolidated)
        return paths

    def hashed_files(self) -> list[tuple[str, str]]:
        """Every declared file as (role, umbrella-relative path), in a stable order."""
        rows = [("origin", o.path) for o in self.origins]
        rows += [("registry", p) for p in self.registry_paths()]
        rows += [("collection", f"{self.collections_dir}/{n}") for n in self.collection_files]
        rows += [("masters-collection", p) for p in self.masters_collections]
        if self.masters_catalog:
            rows.append(("masters-catalog", self.masters_catalog))
        rows.append(("materials-manifest", self.materials_manifest))
        rows.append(("materials-placement", self.materials_placement))
        rows += [(f"resolver:{name}", p) for name, p in sorted(self.resolvers.items())]
        return rows


def _relative(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReconciliationError(f"{what}: expected a relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        raise ReconciliationError(f"{what}: {value!r} must be relative and must not climb")
    return str(pure)


def load_declared(workspace: Path, umbrella: Path) -> Declared:
    path = workspace / DECLARED_INPUTS
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReconciliationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != INPUTS_SCHEMA:
        raise ReconciliationError(f"{path}: schema must be {INPUTS_SCHEMA}")
    if doc.get("base") != "umbrella":
        raise ReconciliationError(f"{path}: base must be 'umbrella'")
    origins: list[Origin] = []
    seen: set[str] = set()
    for raw in doc.get("origins") or []:
        key = str(raw.get("key", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", key) or key in seen:
            raise ReconciliationError(f"origin key {key!r} is invalid or repeated")
        seen.add(key)
        kind = raw.get("kind")
        scope = raw.get("scope")
        if kind not in {"resource-list", "plan-input"} or scope not in {"active", "masters"}:
            raise ReconciliationError(f"origin {key}: kind/scope not recognised")
        origins.append(Origin(
            key=key, path=_relative(raw.get("path"), f"origin {key}"), kind=kind, scope=scope,
            entries=bool(raw.get("entries", False)),
            skip_table_headers=tuple(str(h) for h in raw.get("skip_table_headers") or ()),
            note=str(raw.get("note") or "")))
    if not origins:
        raise ReconciliationError(f"{path}: no origins declared")
    targets = doc.get("targets") or {}
    registry = targets.get("registry") or {}
    collections = targets.get("collections") or {}
    resolvers = {str(k): _relative(v, f"resolver {k}")
                 for k, v in (doc.get("resolvers") or {}).items()}
    baseline = doc.get("baseline")
    return Declared(
        workspace=workspace, umbrella=umbrella, origins=origins,
        registry_dir=_relative(registry.get("directory"), "registry directory"),
        registry_files=[str(n) for n in registry.get("files") or []],
        registry_consolidated=(_relative(registry["consolidated"], "consolidated registry")
                               if registry.get("consolidated") else None),
        collections_dir=_relative(collections.get("directory"), "collections directory"),
        collection_files=[str(n) for n in collections.get("files") or []],
        masters_collections=[_relative(p, "masters collection")
                             for p in targets.get("masters_collections") or []],
        masters_catalog=(_relative(targets["masters_catalog"], "masters catalog")
                         if targets.get("masters_catalog") else None),
        materials_manifest=_relative(targets.get("materials_manifest"), "materials manifest"),
        materials_placement=_relative(targets.get("materials_placement"), "materials placement"),
        resolvers=resolvers,
        identical_copies=list(doc.get("identical_copies") or []),
        not_declared=list(doc.get("not_declared") or []),
        baseline=_relative(baseline, "baseline") if baseline else None,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def live_hashes(declared: Declared) -> dict[str, str]:
    """sha256 per declared file; an optional file that does not exist is 'absent'."""
    hashes: dict[str, str] = {}
    for role, relative in declared.hashed_files():
        target = declared.path(relative)
        if target.is_file():
            hashes[relative] = sha256_file(target)
        elif role == "masters-catalog":
            hashes[relative] = "absent"
        else:
            raise ReconciliationError(f"declared {role} file is missing: {relative}")
    return hashes


def listing_problems(declared: Declared) -> list[str]:
    """A partition added or removed since the declaration is a finding, not a skip."""
    problems = []
    for directory, declared_names in ((declared.registry_dir, declared.registry_files),
                                      (declared.collections_dir, declared.collection_files)):
        on_disk = sorted(p.name for p in declared.path(directory).glob("*.yaml"))
        if sorted(declared_names) != on_disk:
            extra = sorted(set(on_disk) - set(declared_names))
            missing = sorted(set(declared_names) - set(on_disk))
            problems.append(f"{directory}: undeclared {extra}, missing {missing}")
    return problems


# ---------------------------------------------------------------- extraction
@dataclass(frozen=True)
class Occurrence:
    ref: str
    key: str
    line: int
    kind: str
    locator: str
    label: str
    text: str
    normalized: str = ""

    @property
    def order(self) -> tuple[int, int, int]:
        return (self.line, KIND_ORDER[self.kind], int(self.ref.rsplit(":", 1)[1][1:]))


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/")
    return host + path + (f"?{parts.query}" if parts.query else "")


def _clean(text: str) -> str:
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", text)
    return " ".join(text.split()).strip(" |-—·:")


def _short(text: str, limit: int = 120) -> str:
    text = _clean(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _cells(row: str) -> list[str]:
    body = row.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in body.split("|")]


def classify_ticked(token: str) -> str | None:
    value = token.strip()
    if not value or value.lower().startswith(("http://", "https://")):
        return None
    if SOURCE_ID.match(value):
        return "source-ref"
    if len(value) > 4 and value.lower().endswith(FILE_EXTENSIONS):
        return "path"
    if "/" in value and "=" not in value and not re.search(r"\s/|/\s", value):
        first = value.split("/", 1)[0]
        if value.endswith("/") or first in PATH_ROOTS or first.startswith("…"):
            return "path"
    return None


def _bare_label(line: str, start: int) -> str:
    before = _clean(line[:start])
    for separator in (" — ", " – ", " - ", ": ", " · ", "|", "(", "["):
        if separator in before:
            before = before.rsplit(separator, 1)[1]
    before = before.strip(" |-—·:(")
    if before:
        return _short(before, 100)
    bold = BOLD.search(line)
    return _short(bold.group(1), 100) if bold else ""


def extract_line(key: str, lineno: int, line: str) -> list[Occurrence]:
    """URL, path and source-ref occurrences of one line, in textual order per kind."""
    found: list[tuple[str, str, str, str]] = []  # (kind, locator, label, normalized)
    spans: list[tuple[int, int]] = []
    for match in MD_LINK.finditer(line):
        url = match.group(2)
        found.append(("url", url, _short(match.group(1), 100), normalize_url(url)))
        spans.append(match.span())
    for match in AUTOLINK.finditer(line):
        if any(a <= match.start() < b for a, b in spans):
            continue
        url = match.group(1)
        found.append(("url", url, _bare_label(line, match.start()), normalize_url(url)))
        spans.append(match.span())
    for match in BARE_URL.finditer(line):
        if any(a <= match.start() < b for a, b in spans):
            continue
        url = match.group(0).rstrip(TRAILING)
        found.append(("url", url, _bare_label(line, match.start()), normalize_url(url)))
    for match in TICKED.finditer(line):
        if any(a <= match.start() < b for a, b in spans):
            continue
        kind = classify_ticked(match.group(1))
        if kind:
            found.append((kind, match.group(1).strip(), "", ""))
    counters: Counter[str] = Counter()
    result = []
    stripped = line.strip()
    for kind, locator, label, normalized in found:
        counters[kind] += 1
        ref = f"{key}:{lineno}:{KIND_LETTER[kind]}{counters[kind]}"
        result.append(Occurrence(ref, key, lineno, kind, locator, label, stripped, normalized))
    return result


def extract_origin(origin: Origin, text: str) -> tuple[list[Occurrence], dict[str, int]]:
    """All occurrences of one origin file plus structural counts for the report."""
    lines = text.splitlines()
    skip = {h.casefold() for h in origin.skip_table_headers}
    occurrences: list[Occurrence] = []
    stats: Counter[str] = Counter()
    table_skip = False
    for index, line in enumerate(lines):
        lineno = index + 1
        stripped = line.strip()
        is_row = stripped.startswith("|")
        if not is_row:
            table_skip = False
        following = lines[index + 1].strip() if index + 1 < len(lines) else ""
        is_separator = is_row and bool(TABLE_SEPARATOR.match(stripped))
        is_header = is_row and not is_separator and bool(TABLE_SEPARATOR.match(following))
        if is_header:
            first = _clean(_cells(stripped)[0]) if _cells(stripped) else ""
            table_skip = first.casefold() in skip
        found = extract_line(origin.key, lineno, line)
        occurrences.extend(found)
        if not origin.entries or is_separator or is_header:
            continue
        item = LIST_ITEM.match(line)
        is_body_row = is_row and not table_skip
        if is_row and table_skip:
            stats["skipped_table_rows"] += 1
        if not (is_body_row or item):
            continue
        stats["resource_lines"] += 1
        if found:
            continue
        if is_body_row:
            label = _cells(stripped)[0] if _cells(stripped) else stripped
        else:
            bold = BOLD.search(item.group("body"))
            label = bold.group(1) if bold else item.group("body")
        occurrences.append(Occurrence(f"{origin.key}:{lineno}:e1", origin.key, lineno, "entry",
                                      _short(label), _short(label), stripped))
    stats["lines"] = len(lines)
    return occurrences, dict(stats)


def extract_all(declared: Declared) -> tuple[list[Occurrence], dict[str, dict[str, int]]]:
    occurrences: list[Occurrence] = []
    stats: dict[str, dict[str, int]] = {}
    for origin in declared.origins:
        path = declared.path(origin.path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ReconciliationError(f"cannot read origin {origin.key}: {exc}") from exc
        found, counts = extract_origin(origin, text)
        occurrences.extend(sorted(found, key=lambda o: o.order))
        stats[origin.key] = counts
    return occurrences, stats


# -------------------------------------------------------------------- targets
@dataclass
class Targets:
    sources: dict[str, dict]
    source_files: dict[str, str]
    url_index: dict[str, list[tuple[str, str]]]
    collections: dict[str, list[str]]
    candidates: dict[str, dict]
    manifest: dict[str, int]
    placement: list[tuple[str, str]]
    path_map: dict[str, str]
    material_moves: list[tuple[str, str]]
    inventory: dict[str, int]

    def stores(self, source_id: str, normalized: str) -> str | None:
        """Which field of the source already carries this exact normalized URL."""
        for sid, field_name in self.url_index.get(normalized, []):
            if sid == source_id:
                return field_name
        return None

    def slug_for_material(self, material_path: str) -> str | None:
        for prefix, slug in self.placement:
            if material_path.startswith(prefix):
                return slug
        return None


def _load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ReconciliationError(f"cannot read {path}: {exc}") from exc


def _placement(path: Path) -> dict[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        if any(isinstance(t, ast.Name) and t.id == "PLACEMENT" for t in targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items()}
    raise ReconciliationError(f"{path}: no PLACEMENT literal found")


def load_targets(declared: Declared) -> Targets:
    sources: dict[str, dict] = {}
    source_files: dict[str, str] = {}
    for relative in declared.registry_paths():
        doc = _load_yaml(declared.path(relative)) or {}
        for record in (doc.get("sources") if isinstance(doc, dict) else None) or []:
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                if record["id"] in sources:
                    raise ReconciliationError(f"source {record['id']} is registered twice")
                sources[record["id"]] = record
                source_files[record["id"]] = relative
    url_index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for sid, record in sources.items():
        if isinstance(record.get("url"), str):
            url_index[normalize_url(record["url"])].append((sid, "url"))
        for label, value in (record.get("identifiers") or {}).items():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                url_index[normalize_url(value)].append((sid, f"identifiers.{label}"))
    collections: dict[str, list[str]] = defaultdict(list)
    names = [f"{declared.collections_dir}/{n}" for n in declared.collection_files]
    for relative in names + declared.masters_collections:
        doc = _load_yaml(declared.path(relative)) or {}
        entries = []
        if isinstance(doc, dict):
            entries = list(doc.get("entries") or [])
            for group in doc.get("groups") or []:
                if isinstance(group, dict):
                    entries += list(group.get("entries") or [])
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("source"), str):
                collections[entry["source"]].append(PurePosixPath(relative).stem)
    candidates: dict[str, dict] = {}
    if declared.masters_catalog and declared.path(declared.masters_catalog).is_file():
        doc = _load_yaml(declared.path(declared.masters_catalog)) or {}
        for record in (doc.get("candidate_sources") if isinstance(doc, dict) else None) or []:
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                candidates[record["id"]] = record
    manifest_doc = _load_yaml(declared.path(declared.materials_manifest)) or {}
    manifest = {str(p): int((meta or {}).get("size", -1))
                for p, meta in ((manifest_doc.get("files") or {}).items()
                                if isinstance(manifest_doc, dict) else [])}
    placement = sorted(((f"{parent}/{slug}/", slug) for slug, parent in
                        _placement(declared.path(declared.materials_placement)).items()),
                       key=lambda row: -len(row[0]))
    path_map: dict[str, str] = {}
    moves: list[tuple[str, str]] = []
    if "path_map" in declared.resolvers:
        with declared.path(declared.resolvers["path_map"]).open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                path_map[row["old_path"]] = row["new_path"]
    if "material_moves" in declared.resolvers:
        with declared.path(declared.resolvers["material_moves"]).open(encoding="utf-8") as handle:
            moves = [(row["old_path"], row["new_path"]) for row in csv.DictReader(handle)]
        moves.sort(key=lambda row: -len(row[0]))
    inventory: dict[str, int] = {}
    if "inventory" in declared.resolvers:
        with declared.path(declared.resolvers["inventory"]).open(encoding="utf-8") as handle:
            doc = json.load(handle)
        for row in doc.get("files") or []:
            if isinstance(row, dict) and "path" in row:
                inventory[str(row["path"])] = int(row.get("size", -1))
    return Targets(sources, source_files, dict(url_index), dict(collections), candidates,
                   manifest, placement, path_map, moves, inventory)


# ---------------------------------------------------------------- dispositions
@dataclass
class Claim:
    ref: str
    role: str
    title: str = ""
    basis: str = ""
    note: str = ""


@dataclass
class DispositionObject:
    id: str
    kind: str
    title: str = ""
    type: str = ""
    shelf: str = ""
    reason: str = ""
    note: str = ""
    occurrences: list[Claim] = field(default_factory=list)
    extra_mentions: list[str] = field(default_factory=list)


@dataclass
class Dispositions:
    reviewed_input_hashes: dict[str, str]
    objects: list[DispositionObject]


def _parse_claim(raw: object, default_role: str | None) -> Claim:
    if isinstance(raw, str):
        return Claim(ref=raw, role=default_role or "")
    if not isinstance(raw, dict) or not isinstance(raw.get("ref"), str):
        raise ReconciliationError(f"occurrence claim must be a ref or a mapping: {raw!r}")
    return Claim(ref=raw["ref"], role=str(raw.get("role") or default_role or ""),
                 title=str(raw.get("title") or ""), basis=str(raw.get("basis") or ""),
                 note=str(raw.get("note") or ""))


def parse_dispositions(doc: object, where: str) -> Dispositions:
    if doc is None:
        return Dispositions({}, [])
    if not isinstance(doc, dict) or doc.get("schema") not in (None, DISPOSITIONS_SCHEMA):
        raise ReconciliationError(f"{where}: schema must be {DISPOSITIONS_SCHEMA}")
    objects = []
    for raw in doc.get("objects") or []:
        if not isinstance(raw, dict):
            raise ReconciliationError(f"{where}: object must be a mapping")
        objects.append(DispositionObject(
            id=str(raw.get("id") or ""), kind=str(raw.get("kind") or ""),
            title=str(raw.get("title") or ""), type=str(raw.get("type") or ""),
            shelf=str(raw.get("shelf") or ""), reason=str(raw.get("reason") or ""),
            note=str(raw.get("note") or ""),
            occurrences=[_parse_claim(c, None) for c in raw.get("occurrences") or []],
            extra_mentions=[str(m) for m in raw.get("extra_mentions") or []]))
    hashes = {str(k): str(v) for k, v in (doc.get("reviewed_input_hashes") or {}).items()}
    return Dispositions(hashes, objects)


def load_dispositions(path: Path) -> Dispositions:
    if not path.exists():
        return Dispositions({}, [])
    return parse_dispositions(_load_yaml(path), str(path))


def _flow(value: object) -> str:
    text = yaml.safe_dump(value, default_flow_style=True, sort_keys=False, allow_unicode=True,
                          width=1_000_000).rstrip("\n")
    return text[:-4].rstrip("\n") if text.endswith("\n...") else text


def render_dispositions(dispositions: Dispositions, order: dict[str, int]) -> str:
    """Deterministic YAML: objects by kind then id, claims in input order."""
    def claim_key(claim: Claim) -> tuple:
        match = REF.match(claim.ref)
        if not match:
            return (10**9, claim.ref)
        return (order.get(match["key"], 10**6), int(match["line"]),
                "upse".index(match["kind"]), int(match["n"]))

    lines = [
        "# Reviewed dispositions for the library reconciliation. Written by",
        "# tools/library_reconciliation.py merge/freeze; edit decisions, not layout.",
        f"schema: {DISPOSITIONS_SCHEMA}",
        "reviewed_input_hashes:" + ("" if dispositions.reviewed_input_hashes else " {}"),
    ]
    for relative, digest in dispositions.reviewed_input_hashes.items():
        lines.append(f"  {_flow(relative)}: {digest}")
    lines.append("objects:" + ("" if dispositions.objects else " []"))
    kind_rank = {kind: index for index, kind in enumerate(OBJECT_KINDS)}
    for obj in sorted(dispositions.objects, key=lambda o: (kind_rank.get(o.kind, 99), o.id)):
        lines.append(f"- id: {_flow(obj.id)}")
        lines.append(f"  kind: {obj.kind}")
        for name in ("title", "type", "shelf", "reason", "note"):
            value = getattr(obj, name)
            if value:
                lines.append(f"  {name}: {_flow(value)}")
        if obj.extra_mentions:
            lines.append(f"  extra_mentions: {_flow(sorted(set(obj.extra_mentions)))}")
        lines.append("  occurrences:" + ("" if obj.occurrences else " []"))
        for claim in sorted(obj.occurrences, key=claim_key):
            item: dict[str, str] = {"ref": claim.ref}
            if claim.role:
                item["role"] = claim.role
            for name in ("title", "basis", "note"):
                if getattr(claim, name):
                    item[name] = getattr(claim, name)
            lines.append(f"  - {_flow(item)}")
    return "\n".join(lines) + "\n"


def merge_dispositions(base: Dispositions, others: list[Dispositions]) -> Dispositions:
    """Later files win: a ref claimed in a later file leaves every object that file
    does not name for it, so a manual decision replaces a mechanical suggestion."""
    merged: dict[str, DispositionObject] = {o.id: o for o in base.objects}
    for other in others:
        owners: dict[str, set[str]] = defaultdict(set)
        for obj in other.objects:
            for claim in obj.occurrences:
                owners[claim.ref].add(obj.id)
        for current in merged.values():
            current.occurrences = [c for c in current.occurrences
                                   if c.ref not in owners or current.id in owners[c.ref]]
        for obj in other.objects:
            current = merged.get(obj.id)
            if current is None:
                merged[obj.id] = obj
                continue
            if obj.kind != current.kind:
                raise ReconciliationError(
                    f"object {obj.id}: kind {obj.kind} conflicts with {current.kind}")
            for name in ("title", "type", "shelf", "reason", "note"):
                if getattr(obj, name):
                    setattr(current, name, getattr(obj, name))
            by_ref = {c.ref: c for c in current.occurrences}
            for claim in obj.occurrences:
                by_ref[claim.ref] = claim
            current.occurrences = list(by_ref.values())
            current.extra_mentions = sorted(set(current.extra_mentions) | set(obj.extra_mentions))
    return Dispositions(dict(base.reviewed_input_hashes), list(merged.values()))


# --------------------------------------------------------------------- check
@dataclass
class Finding:
    code: str
    detail: str


@dataclass
class Result:
    occurrences: list[Occurrence]
    stats: dict[str, dict[str, int]]
    hashes: dict[str, str]
    disposition: dict[str, str]
    claims: dict[str, list[tuple[DispositionObject, Claim]]]
    findings: list[Finding]
    stale: list[str]

    @property
    def ok(self) -> bool:
        return not self.findings and not self.stale


def evaluate(declared: Declared, dispositions: Dispositions,
             targets: Targets | None = None, *, applied: bool = False) -> tuple[Result, Targets]:
    occurrences, stats = extract_all(declared)
    hashes = live_hashes(declared)
    targets = targets or load_targets(declared)
    by_ref = {o.ref: o for o in occurrences}
    lines_by_key: dict[str, int] = {}
    for origin in declared.origins:
        text = declared.path(origin.path).read_text(encoding="utf-8")
        lines_by_key[origin.key] = len(text.splitlines())
    findings: list[Finding] = [Finding("LISTING", p) for p in listing_problems(declared)]
    for copy in declared.identical_copies:
        same = next((o for o in declared.origins if o.key == copy.get("same_as")), None)
        copy_path = declared.path(_relative(copy.get("path"), "identical copy"))
        if same is None or not copy_path.is_file():
            findings.append(Finding("IDENTICAL-COPY", f"{copy.get('path')}: missing or unknown"))
        elif sha256_file(copy_path) != hashes[same.path]:
            findings.append(Finding("IDENTICAL-COPY",
                                    f"{copy.get('path')} no longer matches {same.key}"))
    claims: dict[str, list[tuple[DispositionObject, Claim]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for obj in dispositions.objects:
        if obj.id in seen_ids:
            findings.append(Finding("DUPLICATE-OBJECT", obj.id))
        seen_ids.add(obj.id)
        findings += _object_findings(obj, targets, applied=applied)
        for claim in obj.occurrences:
            occurrence = by_ref.get(claim.ref)
            if occurrence is None:
                findings.append(Finding("UNKNOWN-REF", f"{obj.id}: {claim.ref}"))
                continue
            role = claim.role or DEFAULT_ROLE[occurrence.kind]
            if role not in ROLES or role not in ALLOWED_ROLES[occurrence.kind]:
                findings.append(Finding("ROLE", f"{claim.ref}: role {role!r} "
                                                f"not allowed for a {occurrence.kind}"))
            if obj.kind in PSEUDO_KINDS and role in REDUNDANT_ROLES:
                findings.append(Finding("ROLE", f"{claim.ref}: {role} needs a real object"))
            claims[claim.ref].append((obj, replace(claim, role=role)))
        for mention in obj.extra_mentions:
            match = LINE_REF.match(mention)
            if not match or match["key"] not in lines_by_key \
                    or int(match["line"]) > lines_by_key[match["key"]]:
                findings.append(Finding("UNKNOWN-REF", f"{obj.id}: extra mention {mention}"))
    disposition: dict[str, str] = {}
    for occurrence in occurrences:
        entries = claims.get(occurrence.ref, [])
        if not entries:
            findings.append(Finding("UNDISPOSITIONED", f"{occurrence.ref} {occurrence.locator}"))
            continue
        kinds = {("alias-or-duplicate" if c.role in REDUNDANT_ROLES else o.kind)
                 for o, c in entries}
        if len(entries) > 1 and (len(kinds) > 1 or any(c.role != "mention" for _, c in entries)):
            owners = ", ".join(o.id for o, _ in entries)
            findings.append(Finding("CONFLICT", f"{occurrence.ref} claimed by {owners}"))
            continue
        disposition[occurrence.ref] = kinds.pop()
    reviewed = dispositions.reviewed_input_hashes
    mutable = ({*declared.registry_paths(), declared.masters_catalog}
               if applied else set())
    stale = sorted(p for p in hashes if p not in mutable and reviewed.get(p) != hashes[p])
    stale += sorted(p for p in reviewed if p not in hashes)
    if applied:
        findings += _applied_record_findings(declared, dispositions, targets, by_ref)
    return Result(occurrences, stats, hashes, disposition, dict(claims), findings, stale), targets


def _object_findings(obj: DispositionObject, targets: Targets, *, applied: bool = False) -> list[Finding]:
    findings = []
    if obj.kind not in OBJECT_KINDS:
        return [Finding("KIND", f"{obj.id}: unknown kind {obj.kind!r}")]
    if obj.kind == "existing-active-source" and obj.id not in targets.sources:
        findings.append(Finding("TARGET", f"{obj.id}: not in the source registry"))
    if obj.kind == "new-active-source":
        if not SOURCE_ID.match(obj.id):
            findings.append(Finding("TARGET", f"{obj.id}: not a source id"))
        elif applied and obj.id not in targets.sources:
            findings.append(Finding("TARGET", f"{obj.id}: registration missing"))
        elif not applied and obj.id in targets.sources:
            findings.append(Finding("TARGET", f"{obj.id}: already registered (existing)"))
        if not obj.title or obj.type not in SOURCE_TYPES:
            findings.append(Finding("TARGET", f"{obj.id}: new source needs title and type"))
    if obj.kind == "existing-masters-candidate" and obj.id not in targets.candidates:
        findings.append(Finding("TARGET", f"{obj.id}: not in the Master's catalogue"))
    if obj.kind == "new-masters-candidate":
        if not CANDIDATE_ID.match(obj.id):
            findings.append(Finding("TARGET", f"{obj.id}: not a candidate-source id"))
        elif applied and obj.id not in targets.candidates:
            findings.append(Finding("TARGET", f"{obj.id}: catalogue entry missing"))
        elif not applied and obj.id in targets.candidates:
            findings.append(Finding("TARGET", f"{obj.id}: already a candidate (existing)"))
        if not obj.title:
            findings.append(Finding("TARGET", f"{obj.id}: new candidate needs a title"))
    if obj.kind in PSEUDO_KINDS:
        if not PSEUDO_ID.match(obj.id) or not obj.id.startswith(obj.kind + ":"):
            findings.append(Finding("TARGET", f"{obj.id}: must be '{obj.kind}:<slug>'"))
        if not obj.reason:
            findings.append(Finding("TARGET", f"{obj.id}: needs a reason"))
    if obj.shelf and not THEMATIC_GROUP_ID.match(obj.shelf):
        findings.append(Finding("TARGET", f"{obj.id}: shelf {obj.shelf!r} is not a group id"))
    return findings


def _applied_record_findings(declared: Declared, dispositions: Dispositions,
                             targets: Targets, by_ref: dict[str, Occurrence]) -> list[Finding]:
    """Prove the frozen decisions reached their target records after intake."""
    findings: list[Finding] = []
    origins = {origin.key: origin.path for origin in declared.origins}
    for obj in dispositions.objects:
        if obj.kind in {"new-active-source", "existing-active-source"}:
            record = targets.sources.get(obj.id)
        elif obj.kind in {"new-masters-candidate", "existing-masters-candidate"}:
            record = targets.candidates.get(obj.id)
        else:
            continue
        if record is None:
            continue  # _object_findings reports the absent target.
        if obj.kind.startswith("new-"):
            if record.get("title") != obj.title or (obj.type and record.get("type") != obj.type):
                findings.append(Finding("APPLIED", f"{obj.id}: title/type differs from review"))
            refs = {f"{origins[by_ref[c.ref].key]}#L{by_ref[c.ref].line}"
                    for c in obj.occurrences if c.ref in by_ref}
            refs.update(f"{origins[x.split(':')[0]]}#L{x.split(':')[1]}"
                        for x in obj.extra_mentions if x.split(':')[0] in origins)
            if obj.kind == "new-active-source":
                discovery = record.get("discovery")
                if not isinstance(discovery, dict):
                    discovery = {}
                saved = {row.get("ref") for row in discovery.get("basis") or []
                         if isinstance(row, dict)}
            else:
                saved = set(record.get("provenance") or [])
            if not refs.issubset(saved):
                findings.append(Finding("APPLIED", f"{obj.id}: reviewed origin missing from provenance"))
        identifiers = record.get("identifiers") or {}
        if not isinstance(identifiers, dict):
            findings.append(Finding("APPLIED", f"{obj.id}: identifiers are not a mapping"))
            identifiers = {}
        saved_urls = {normalize_url(value) for value in
                      [record.get("url"), *identifiers.values()]
                      if isinstance(value, str) and value.startswith(("http://", "https://"))}
        for claim in obj.occurrences:
            occurrence = by_ref.get(claim.ref)
            if (occurrence and occurrence.kind == "url"
                    and (claim.role or DEFAULT_ROLE["url"]) not in REDUNDANT_ROLES
                    and occurrence.normalized not in saved_urls):
                findings.append(Finding("APPLIED", f"{obj.id}: {claim.ref} URL not stored"))
    return findings


# ------------------------------------------------------------------- suggest
def _tokens(text: str) -> set[str]:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return {t for t in re.split(r"[^a-z0-9]+", folded) if len(t) > 2 and t not in STOPWORDS}


def title_hints(label: str, targets: Targets, limit: int = 3) -> list[str]:
    wanted = _tokens(label)
    if len(wanted) < 2:
        return []
    scored = []
    for sid, record in targets.sources.items():
        have = _tokens(" ".join([str(record.get("title", ""))] +
                                [str(a) for a in record.get("authors") or []]))
        if not have:
            continue
        overlap = len(wanted & have) / min(len(wanted), len(have))
        if overlap >= 0.5 and len(wanted & have) >= 2:
            scored.append((overlap, sid))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [f"{sid} ({score:.2f})" for score, sid in scored[:limit]]


def _fold(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold().strip()


def resolve_path(occurrence: Occurrence, targets: Targets) -> tuple[str | None, str, str]:
    """(object id or None, basis, note) for one local path occurrence."""
    raw = occurrence.locator.strip().lstrip("…").lstrip("/")
    folder = raw.endswith("/")
    raw = raw.rstrip("/")
    name = raw.rsplit("/", 1)[-1]
    if raw in targets.path_map:
        return ("out-of-scope:internal-document", "path-map", targets.path_map[raw])
    if raw.lower().endswith(".md") and name.lower() not in GENERIC_NAMES:
        hits = [new for old, new in targets.path_map.items() if old.rsplit("/", 1)[-1] == name]
        if len(hits) == 1:
            return ("out-of-scope:internal-document", "path-map-basename", hits[0])
    for old, new in targets.material_moves:
        if raw == old or raw.startswith(old + "/"):
            match = re.search(r"materials/(source-[a-z0-9-]+)", new)
            if match and match.group(1) in targets.sources:
                return (match.group(1), "material-moves", new)
    candidates = set()
    if not folder:
        wanted = _fold(name)
        for material in targets.manifest:
            if _fold(material.rsplit("/", 1)[-1]) == wanted:
                slug = targets.slug_for_material(material)
                if slug:
                    candidates.add(f"source-{slug}")
    registered = {c for c in candidates if c in targets.sources}
    if len(registered) == 1:
        return (registered.pop(), "manifest-basename", "")
    if not candidates and not folder and raw in targets.inventory:
        size = targets.inventory[raw]
        suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        for material, material_size in targets.manifest.items():
            if material_size == size and material.lower().endswith(suffix):
                slug = targets.slug_for_material(material)
                if slug:
                    candidates.add(f"source-{slug}")
        registered = {c for c in candidates if c in targets.sources}
        if len(registered) == 1:
            return (registered.pop(), "inventory-size", "")
    note = ", ".join(sorted(candidates)) if candidates else ""
    return (None, "", note)


def suggest(result: Result, targets: Targets) -> tuple[Dispositions, list[tuple[Occurrence, str]]]:
    """Auto-dispositions for mechanical matches; everything else goes to the worklist."""
    objects: dict[str, DispositionObject] = {}
    worklist: list[tuple[Occurrence, str]] = []
    line_sources: dict[tuple[str, int], set[str]] = defaultdict(set)
    for occurrence in result.occurrences:
        if occurrence.kind == "url":
            for sid, _ in targets.url_index.get(occurrence.normalized, []):
                line_sources[(occurrence.key, occurrence.line)].add(sid)

    def put(object_id: str, kind: str, claim: Claim, reason: str = "") -> None:
        obj = objects.setdefault(object_id, DispositionObject(id=object_id, kind=kind,
                                                              reason=reason))
        obj.occurrences.append(claim)

    for occurrence in result.occurrences:
        if occurrence.ref in result.claims:
            continue
        hint = ""
        if occurrence.kind == "url":
            host = urlsplit(occurrence.locator).hostname or ""
            owners = sorted({sid for sid, _ in targets.url_index.get(occurrence.normalized, [])})
            if host.lower() == MOSES_HOST:
                put("out-of-scope:module-descriptor", "out-of-scope",
                    Claim(occurrence.ref, "", basis="moses-host"),
                    "TU Moses module description: candidate-module evidence, not a learning source")
                continue
            if len(owners) == 1:
                fields = {f for sid, f in targets.url_index[occurrence.normalized]
                          if sid == owners[0]}
                role = "landing" if "url" in fields else "companion"
                put(owners[0], "existing-active-source",
                    Claim(occurrence.ref, role, basis="exact-url" if role == "landing"
                          else "exact-identifier"))
                continue
            neighbours = sorted(line_sources.get((occurrence.key, occurrence.line), set()))
            hint = "; ".join(filter(None, [
                f"exact url owners {owners}" if owners else "",
                f"same line as {neighbours}" if neighbours else "",
                "title ~ " + ", ".join(title_hints(occurrence.label, targets))
                if title_hints(occurrence.label, targets) else ""]))
        elif occurrence.kind == "source-ref":
            if occurrence.locator in targets.sources:
                put(occurrence.locator, "existing-active-source",
                    Claim(occurrence.ref, "reference", basis="source-id"))
                continue
            hint = "not registered"
        elif occurrence.kind == "path":
            object_id, basis, note = resolve_path(occurrence, targets)
            if object_id and object_id.startswith("out-of-scope:"):
                put(object_id, "out-of-scope", Claim(occurrence.ref, "", basis=basis, note=note),
                    "Internal plan or note document (moved per migration/path-map.csv)")
                continue
            if object_id:
                put(object_id, "existing-active-source",
                    Claim(occurrence.ref, "local", basis=basis, note=note))
                continue
            hint = f"material candidates: {note}" if note else "no material match"
        else:
            hints = title_hints(occurrence.label, targets)
            hint = ("title ~ " + ", ".join(hints)) if hints else ""
        worklist.append((occurrence, hint))
    return Dispositions({}, list(objects.values())), worklist


def render_worklist(worklist: list[tuple[Occurrence, str]], declared: Declared) -> str:
    """Echoed lines keep their text but not their links: a relative Markdown link
    copied out of its folder would be a broken link in this file (LINK-BROKEN)."""
    paths = {o.key: o.path for o in declared.origins}
    lines = ["# Library reconciliation worklist (disposable; regenerate with `suggest`)", ""]
    current = None
    last_line = None
    for occurrence, hint in worklist:
        if occurrence.key != current:
            current = occurrence.key
            last_line = None
            lines += ["", f"## {current} — {paths[current]}", ""]
        if occurrence.line != last_line:
            last_line = occurrence.line
            lines.append(_inert(f"L{occurrence.line}: {_short(occurrence.text, 260)}"))
        lines.append(_inert(f"    {occurrence.ref} [{occurrence.kind}] {occurrence.locator}"
                            + (f"  «{occurrence.label}»" if occurrence.label
                               and occurrence.label != occurrence.locator else "")
                            + (f"  -> {hint}" if hint else "")))
    return "\n".join(lines) + "\n"


def _inert(text: str) -> str:
    return text.replace("](", "] (")


# -------------------------------------------------------------------- report
def _md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_report(declared: Declared, dispositions: Dispositions, result: Result,
                  targets: Targets) -> str:
    """Deterministic Markdown; `check --report` compares it byte for byte."""
    dispositions = _with_default_roles(dispositions, result)
    origin_by_key = {o.key: o for o in declared.origins}
    per_origin: dict[str, Counter[str]] = defaultdict(Counter)
    per_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for occurrence in result.occurrences:
        kind = result.disposition.get(occurrence.ref, "UNDISPOSITIONED")
        per_origin[occurrence.key][kind] += 1
        per_kind[occurrence.kind][kind] += 1
    total = Counter(result.disposition.values())
    named = [o for o in dispositions.objects if o.occurrences or o.extra_mentions]
    objects_by_kind = Counter(o.kind for o in named)
    mention_only = sum(1 for o in named if not o.occurrences)
    out = [
        "# Library reconciliation report",
        "",
        "> Generated by `tools/library_reconciliation.py report` from",
        f"> `{DECLARED_INPUTS}` and `{DISPOSITIONS_FILE}`. Do not edit by hand;",
        "> `check --report` fails when this file no longer matches its inputs.",
        "",
        "## Verdict",
        "",
        f"- Occurrences in declared origins: **{len(result.occurrences)}**",
        f"- With exactly one disposition: **{len(result.disposition)}**",
        f"- Findings (undispositioned, conflicts, invalid targets): **{len(result.findings)}**",
        "- Inputs changed since review (stale): "
        f"**{len(result.stale)}**{' — REVIEW IS STALE' if result.stale else ''}",
        "",
        "| Disposition | Occurrences | Distinct objects |",
        "|---|---:|---:|",
    ]
    for kind in DISPOSITIONS:
        distinct = objects_by_kind.get(kind, 0) if kind != "alias-or-duplicate" else "—"
        out.append(f"| {kind} | {total.get(kind, 0)} | {distinct} |")
    out += ["",
            "Distinct objects count every object the inputs name, including "
            f"{mention_only} named only",
            "by an extra mention: a name in a line whose link or entry belongs to another",
            "object. alias-or-duplicate occurrences point at objects counted in their own row."]
    out += ["", "## Baseline", ""]
    if declared.baseline and (declared.workspace / declared.baseline).is_file():
        out += [f"From `{declared.baseline}` (verbatim):", "", "```yaml",
                (declared.workspace / declared.baseline).read_text(encoding="utf-8").rstrip(),
                "```"]
    else:
        out.append("No baseline declared.")
    out += ["", "## Declared inputs and hashes", "",
            "Paths are relative to the LearningOS umbrella. `reviewed` is the hash the",
            "dispositions were checked against; a mismatch makes the review stale.", "",
            "| Role | Path | sha256 (live) | Reviewed |", "|---|---|---|---|"]
    for role, relative in declared.hashed_files():
        live = result.hashes.get(relative, "")
        reviewed = dispositions.reviewed_input_hashes.get(relative)
        state = "same" if reviewed == live else ("missing" if reviewed is None else "CHANGED")
        out.append(f"| {role} | `{relative}` | `{live}` | {state} |")
    out += ["", "Byte-identical copies (checked on every run, not enumerated twice):", ""]
    for copy in declared.identical_copies:
        out.append(f"- `{copy.get('path')}` = `{copy.get('same_as')}`")
    out += ["", "## Per origin", "",
            "| Key | Scope | Lines | Resource lines | Occurrences | "
            + " | ".join(DISPOSITIONS) + " |",
            "|---|---|---:|---:|---:|" + "---:|" * len(DISPOSITIONS)]
    for origin in declared.origins:
        counts = per_origin[origin.key]
        stats = result.stats.get(origin.key, {})
        out.append(f"| `{origin.key}` | {origin.scope} | {stats.get('lines', 0)} | "
                   f"{stats.get('resource_lines', 0) if origin.entries else 'n/a'} | "
                   f"{sum(counts.values())} | "
                   + " | ".join(str(counts.get(k, 0)) for k in DISPOSITIONS) + " |")
    out += ["", "| Occurrence kind | " + " | ".join(DISPOSITIONS) + " |",
            "|---|" + "---:|" * len(DISPOSITIONS)]
    for kind in KIND_ORDER:
        out.append(f"| {kind} | " + " | ".join(str(per_kind[kind].get(k, 0))
                                               for k in DISPOSITIONS) + " |")
    out += _findings_section(result)
    out += _existing_section(dispositions, result, targets)
    out += _new_section(dispositions, result, "new-active-source",
                        "New active sources (to register in step 8)")
    out += _new_section(dispositions, result, "new-masters-candidate",
                        "New Master's candidates (to add through the catalogue in step 6)")
    out += _children_section(dispositions, result)
    out += _flags_section(dispositions)
    out += _pseudo_section(dispositions, result, origin_by_key)
    out += _boundary_section(declared, targets)
    return "\n".join(out).rstrip() + "\n"


def _with_default_roles(dispositions: Dispositions, result: Result) -> Dispositions:
    """A copy with every omitted role spelled out; the input is never changed."""
    kinds = {o.ref: o.kind for o in result.occurrences}
    return Dispositions(dispositions.reviewed_input_hashes, [
        replace(obj, occurrences=[
            replace(c, role=c.role or DEFAULT_ROLE.get(kinds.get(c.ref, ""), ""))
            for c in obj.occurrences])
        for obj in dispositions.objects])


def _line_key(line_ref: str) -> tuple[str, int]:
    key, _, line = line_ref.partition(":")
    return (key, int(line) if line.isdigit() else 0)


def _occurrence_index(result: Result) -> dict[str, Occurrence]:
    return {o.ref: o for o in result.occurrences}


def _findings_section(result: Result) -> list[str]:
    out = ["", "## Findings", ""]
    if not result.findings and not result.stale:
        return out + ["None: every occurrence has exactly one disposition and the review is fresh."]
    for finding in result.findings:
        out.append(f"- `{finding.code}` {_md(finding.detail)}")
    for relative in result.stale:
        out.append(f"- `STALE` `{relative}` changed since the review")
    return out


def _existing_section(dispositions: Dispositions, result: Result, targets: Targets) -> list[str]:
    index = _occurrence_index(result)
    rows = []
    not_stored = []
    aliases = []
    for obj in sorted(dispositions.objects, key=lambda o: o.id):
        if obj.kind != "existing-active-source" or obj.id not in targets.sources:
            continue
        record = targets.sources[obj.id]
        urls = [c for c in obj.occurrences if c.ref in index and index[c.ref].kind == "url"]
        missing = [c for c in urls if c.role not in REDUNDANT_ROLES
                   and not targets.stores(obj.id, index[c.ref].normalized)]
        for claim in urls:
            if claim.role == "alias" and not targets.stores(obj.id, index[claim.ref].normalized):
                aliases.append(f"| `{obj.id}` | `{claim.ref}` | {index[claim.ref].locator} | "
                               f"{_md(claim.note)} |")
        rows.append(f"| `{obj.id}` | {_md(str(record.get('title', '')))} | "
                    f"`{targets.source_files.get(obj.id, '')}` | {len(obj.occurrences)} | "
                    f"{len(set(obj.extra_mentions))} | {len(missing)} |")
        for claim in missing:
            occurrence = index[claim.ref]
            not_stored.append(f"| `{obj.id}` | {claim.role} | `{claim.ref}` | "
                              f"{_md(claim.title or occurrence.label)} | {occurrence.locator} |")
    out = ["", f"## Existing active sources ({len(rows)})", "",
           f"{len(rows)} registered sources are named by the declared inputs, through claimed",
           "occurrences, extra mentions, or both. `Links not stored` counts URLs whose exact",
           "normalized form is in neither `url` nor `identifiers` of the record: the",
           "child-link gap step 3 addresses. An old exact-URL comparison that found no match",
           "is a lead only: these rows show where such links actually went.",
           "", "| Source | Title | Partition | Occurrences | Extra mentions | Links not stored |",
           "|---|---|---|---:|---:|---:|"]
    out += rows
    out += ["", f"### Links not yet stored on their record ({len(not_stored)})", "",
            "| Source | Role | Occurrence | Title | URL |", "|---|---|---|---|---|"]
    out += not_stored
    out += ["", f"### Alias URLs not stored on their record ({len(aliases)})", "",
            "Another address for the same object. Not counted as a missing link; whether",
            "an alias belongs in `identifiers` is a registry decision for step 8.", "",
            "| Source | Occurrence | URL | Note |", "|---|---|---|---|"]
    return out + aliases


def _new_section(dispositions: Dispositions, result: Result, kind: str, heading: str) -> list[str]:
    index = _occurrence_index(result)
    chosen = sorted((o for o in dispositions.objects if o.kind == kind), key=lambda o: o.id)
    out = ["", f"## {heading} ({len(chosen)})", "",
           "| Id | Title | Type | Shelf | Links | Origins |", "|---|---|---|---|---:|---|"]
    for obj in chosen:
        refs = sorted({c.ref.rsplit(":", 1)[0] for c in obj.occurrences}
                      | set(obj.extra_mentions), key=_line_key)
        urls = {index[c.ref].normalized for c in obj.occurrences
                if c.ref in index and index[c.ref].kind == "url"
                and c.role not in REDUNDANT_ROLES}
        out.append(f"| `{obj.id}` | {_md(obj.title)} | {obj.type or '—'} | "
                   f"{obj.shelf or '—'} | {len(urls)} | {', '.join(refs)} |")
    return out


def _children_section(dispositions: Dispositions, result: Result) -> list[str]:
    index = _occurrence_index(result)
    sizes = []
    for obj in dispositions.objects:
        children = {index[c.ref].normalized for c in obj.occurrences
                    if c.ref in index and c.role in LINKED_ROLES}
        if children:
            sizes.append((len(children), obj.id))
    sizes.sort(key=lambda row: (-row[0], row[1]))
    out = ["", "## Known child links per teaching object", "",
           "Distinct child and companion links named by the declared inputs, per object.",
           "Step 5 adds a bounded child-list read only if the largest list makes one",
           "source response excessive.", ""]
    if not sizes:
        return out + ["No object has child links."]
    out.append(f"Largest: **{sizes[0][0]}** links on `{sizes[0][1]}`. "
               f"Objects with children: {len(sizes)}.")
    out += ["", "| Object | Child links |", "|---|---:|"]
    out += [f"| `{object_id}` | {count} |" for count, object_id in sizes[:15]]
    return out


def _flags_section(dispositions: Dispositions) -> list[str]:
    """Every decision the reviewer marked with ⚠: unverified or needing a later call."""
    rows = []
    for obj in sorted(dispositions.objects, key=lambda o: o.id):
        if "⚠" in obj.note:
            rows.append(f"- `{obj.id}` — {_md(obj.note)}")
        for claim in obj.occurrences:
            if "⚠" in claim.note:
                rows.append(f"- `{claim.ref}` → `{obj.id}` — {_md(claim.note)}")
    out = ["", f"## Flags for review ({len(rows)})", "",
           "Decisions marked ⚠: unverified facts or a call deliberately left to a later step."]
    return out + ([""] + rows if rows else ["", "None."])


def _pseudo_section(dispositions: Dispositions, result: Result,
                    origin_by_key: dict[str, Origin]) -> list[str]:
    index = _occurrence_index(result)
    out = []
    for kind, heading in (("unresolved", "Unresolved"), ("out-of-scope", "Explicitly out of scope")):
        chosen = sorted((o for o in dispositions.objects if o.kind == kind), key=lambda o: o.id)
        count = sum(len(o.occurrences) for o in chosen)
        out += ["", f"## {heading} ({count} occurrences)", ""]
        for obj in chosen:
            out += [f"### `{obj.id}` ({len(obj.occurrences)})", "", _md(obj.reason), ""]
            if kind == "unresolved" or len(obj.occurrences) <= 40:
                for claim in obj.occurrences:
                    occurrence = index.get(claim.ref)
                    locator = occurrence.locator if occurrence else "?"
                    note = f" — {_md(claim.note)}" if claim.note else ""
                    out.append(f"- `{claim.ref}` {_md(locator)}{note}")
                for mention in sorted(set(obj.extra_mentions), key=_line_key):
                    out.append(f"- `{mention}` (extra mention: named beside another "
                               "object's link or entry)")
            else:
                keys = Counter(c.ref.split(":", 1)[0] for c in obj.occurrences)
                out.append("- by origin: " + ", ".join(f"`{k}` {n}" for k, n in sorted(keys.items())))
            out.append("")
    return out


def _boundary_section(declared: Declared, targets: Targets) -> list[str]:
    unsorted = sum(1 for p in targets.manifest if p.startswith("_unsorted/"))
    out = ["", "## Boundary: known material outside the declared inputs", "",
           "Named so that nothing is dropped silently. None of it is counted above.", ""]
    for item in declared.not_declared:
        out.append(f"- `{item.get('path')}` — {_md(str(item.get('reason', '')))}")
    out.append(f"- Materials manifest: {unsorted} files under `_unsorted/` "
               "are on disk without a registered source.")
    return out


def render_applied_report(declared: Declared, dispositions: Dispositions,
                          result: Result) -> str:
    """Frozen final proof with live hashes; the original review stays untouched."""
    summary = {
        "schema": "library-reconciliation-applied/v1",
        "occurrences": len(result.occurrences),
        "dispositioned": len(result.disposition),
        "new_active_sources": sum(o.kind == "new-active-source" for o in dispositions.objects),
        "new_masters_candidates": sum(o.kind == "new-masters-candidate" for o in dispositions.objects),
        "findings": [asdict(f) for f in result.findings],
        "stale_inputs": result.stale,
        "declared_inputs_sha256": sha256_file(declared.workspace / DECLARED_INPUTS),
        "dispositions_sha256": sha256_file(declared.workspace / DISPOSITIONS_FILE),
        "input_hashes": {path: result.hashes[path] for _, path in declared.hashed_files()},
    }
    return json.dumps(summary, indent=2, ensure_ascii=False) + "\n"


# ----------------------------------------------------------------------- CLI
def _workspace(args: argparse.Namespace) -> tuple[Declared, Path]:
    root = Path(args.root).resolve() if args.root else REPO_ROOT
    workspace = (root / args.workspace).resolve()
    if not workspace.is_dir() or root not in workspace.parents:
        raise ReconciliationError(f"workspace must be a directory inside {root}")
    return load_declared(workspace, root.parent), workspace


def _order(declared: Declared) -> dict[str, int]:
    return {origin.key: index for index, origin in enumerate(declared.origins)}


def command_check(args: argparse.Namespace) -> int:
    declared, workspace = _workspace(args)
    dispositions = load_dispositions(workspace / DISPOSITIONS_FILE)
    result, targets = evaluate(declared, dispositions, applied=args.applied)
    report_state = None
    if args.report:
        current = workspace / (APPLIED_REPORT_FILE if args.applied else REPORT_FILE)
        expected = (render_applied_report(declared, dispositions, result)
                    if args.applied else render_report(declared, dispositions, result, targets))
        report_state = "current" if current.is_file() and \
            current.read_text(encoding="utf-8") == expected else "outdated"
    summary = {
        "occurrences": len(result.occurrences),
        "dispositioned": len(result.disposition),
        "by_disposition": dict(Counter(result.disposition.values())),
        "findings": [asdict(f) for f in result.findings],
        "stale_inputs": result.stale,
        "report": report_state,
        "ok": result.ok and report_state in (None, "current"),
    }
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"library-reconciliation: {summary['dispositioned']}/{summary['occurrences']} "
              f"occurrences dispositioned; {len(result.findings)} finding(s); "
              f"{len(result.stale)} stale input(s)"
              + (f"; report {report_state}" if report_state else ""))
        for finding in result.findings[: args.limit]:
            print(f"  {finding.code}: {finding.detail}")
        if len(result.findings) > args.limit:
            print(f"  ... {len(result.findings) - args.limit} more (use --json)")
        for relative in result.stale:
            print(f"  STALE: {relative}")
    return 0 if summary["ok"] else 1


def command_report(args: argparse.Namespace) -> int:
    declared, workspace = _workspace(args)
    dispositions = load_dispositions(workspace / DISPOSITIONS_FILE)
    result, targets = evaluate(declared, dispositions, applied=args.applied)
    if args.applied and not result.ok:
        print("refusing applied report: applied check has findings or stale origins")
        return 1
    target = workspace / (APPLIED_REPORT_FILE if args.applied else REPORT_FILE)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_applied_report(declared, dispositions, result)
                      if args.applied else render_report(declared, dispositions, result, targets),
                      encoding="utf-8")
    print(f"wrote {target.relative_to(workspace)} "
          f"({len(result.disposition)}/{len(result.occurrences)} dispositioned, "
          f"{len(result.findings)} finding(s), {len(result.stale)} stale)")
    return 0


def command_suggest(args: argparse.Namespace) -> int:
    declared, workspace = _workspace(args)
    dispositions = load_dispositions(workspace / DISPOSITIONS_FILE)
    result, targets = evaluate(declared, dispositions)
    auto, worklist = suggest(result, targets)
    Path(args.out).write_text(render_dispositions(auto, _order(declared)), encoding="utf-8")
    Path(args.worklist).write_text(render_worklist(worklist, declared), encoding="utf-8")
    claimed = sum(len(o.occurrences) for o in auto.objects)
    print(f"suggested {claimed} mechanical disposition(s); {len(worklist)} left for review")
    return 0


def command_merge(args: argparse.Namespace) -> int:
    declared, workspace = _workspace(args)
    target = workspace / DISPOSITIONS_FILE
    base = load_dispositions(target)
    others = [parse_dispositions(_load_yaml(Path(p)), p) for p in args.files]
    merged = merge_dispositions(base, others)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_dispositions(merged, _order(declared)), encoding="utf-8")
    print(f"merged {len(args.files)} file(s) into {target.relative_to(workspace)}: "
          f"{len(merged.objects)} object(s)")
    return 0


def command_freeze(args: argparse.Namespace) -> int:
    declared, workspace = _workspace(args)
    target = workspace / DISPOSITIONS_FILE
    dispositions = load_dispositions(target)
    result, _ = evaluate(declared, dispositions)
    if result.findings:
        print(f"refusing to freeze: {len(result.findings)} finding(s) remain; run check")
        return 1
    dispositions.reviewed_input_hashes = dict(result.hashes)
    target.write_text(render_dispositions(dispositions, _order(declared)), encoding="utf-8")
    print(f"froze {len(result.hashes)} input hash(es) into {target.relative_to(workspace)}")
    return 0


def command_extract(args: argparse.Namespace) -> int:
    declared, _ = _workspace(args)
    occurrences, _ = extract_all(declared)
    chosen = [o for o in occurrences if not args.key or o.key == args.key]
    if args.json:
        print(json.dumps([asdict(o) for o in chosen], indent=1, ensure_ascii=False))
    else:
        for occurrence in chosen:
            print(f"{occurrence.ref}\t{occurrence.kind}\t{occurrence.locator}\t{occurrence.label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="repository root (default: this checkout)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("check", command_check), ("report", command_report),
                          ("suggest", command_suggest), ("merge", command_merge),
                          ("freeze", command_freeze), ("extract", command_extract)):
        command = sub.add_parser(name)
        command.add_argument("--workspace", required=True,
                             help="workspace directory relative to the repository root")
        command.set_defaults(handler=handler)
        if name == "check":
            command.add_argument("--json", action="store_true")
            command.add_argument("--report", action="store_true",
                                 help="also require the saved report to be current")
            command.add_argument("--limit", type=int, default=25)
        if name in {"check", "report"}:
            command.add_argument("--applied", action="store_true",
                                 help="verify the post-intake targets against frozen decisions")
        if name == "suggest":
            command.add_argument("--out", required=True)
            command.add_argument("--worklist", required=True)
        if name == "merge":
            command.add_argument("files", nargs="+")
        if name == "extract":
            command.add_argument("--key")
            command.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ReconciliationError as exc:
        print(f"library-reconciliation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
