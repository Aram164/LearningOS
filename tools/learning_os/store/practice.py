"""The practice verification sidecar and its effective status (P6 step 34).

`knowledge/practice-index.yaml` is the only place verification lives; the
canonical note remains the only source of prompt and solution text, and no
solution text is ever copied into the sidecar. A stored status is a claim:
the effective status is recomputed from the current item bytes, the pinned
source files and the recorded proofs, and any gap makes the item ineligible
regardless of what the row says.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TypedDict, cast

import yaml

from learning_os.domain.failures import PracticeSidecarUnreadable
from learning_os.domain.practice import (
    PracticeItem,
    content_sha256,
    extract_items,
)
from learning_os.domain.relations import (
    EvidenceBinding,
    RelationRow,
    evidence_state,
    normalize_quote,
)
from learning_os.domain.snapshot import Note, Repo
from learning_os.store.contracts.json_schema import load_standalone_validator
from learning_os.store.layout import PathBoundaryError, resolve_symlinks_inside
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.materials.resolution import parse_material_uri

SIDECAR_REL = "knowledge/practice-index.yaml"
ARTIFACT_ID = "registry-practice-index"
CHECKED_STATUSES = ("cross-checked", "source-matched", "confirmed")
METHOD_FOR_STATUS = {
    "source-matched": "official-source",
    "cross-checked": "independent-solve",
    "confirmed": "explicit-review",
}


class PracticeProof(TypedDict):
    method: str
    verified_at: str
    artifact_sha256: str
    reviewer_id: str
    source_binding: EvidenceBinding | None
    comparison_sha256: str | None


class PracticeRow(TypedDict):
    item_id: str
    concept_ids: list[str]
    kind: str
    status: str
    content_sha256: str
    source_bindings: list[EvidenceBinding]
    verifications: list[PracticeProof]


class PracticeIndex(TypedDict):
    items: list[PracticeRow]


#: SHA-256 of material files, keyed by (path, device, inode, size, mtime_ns).
#: One publish asks for the same cited PDF once per board, concept card and
#: manifest row that shows it; without this every ask re-read and re-hashed
#: the whole file. Any change to the file changes its stat key, so a stale
#: digest is never served; entries for replaced files are simply unused.
_DIGESTS: dict[tuple[str, int, int, int, int], str] = {}


def material_file(repo: Repo, rel: object) -> Path | None:
    """The regular file ``rel`` names under the materials resolution root.

    Core's materials rule (``resolve_symlinks_inside``): the ``.flat`` id
    aliases are symlinks into the topic tree, so links are followed, but every
    hop must stay inside ``materials/``. Requiring the resolved path to stay
    under ``.flat`` itself refused every real material, because every
    ``.flat/<source>`` entry is such a link.
    """
    rel = str(rel or "")
    if not rel or PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts:
        return None
    try:
        resolved = resolve_symlinks_inside(
            repo.learningos_root / "materials", repo.materials_root / rel, strict=False)
    except (PathBoundaryError, OSError):
        return None
    return resolved if resolved.is_file() else None


def file_sha256(path: Path) -> str:
    """The file's SHA-256, read once per unchanged file."""
    stat = path.stat()
    key = (str(path), stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    digest = _DIGESTS.get(key)
    if digest is None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        _DIGESTS[key] = digest
    return digest


def binding_file_state(repo: Repo, binding: Mapping[str, object]) -> str:
    """``ok`` when the pinned file exists under materials with its digest."""
    candidate = material_file(repo, binding.get("material_relpath"))
    if candidate is None:
        return "stale"
    try:
        digest = file_sha256(candidate)
    except OSError:
        return "stale"
    return "ok" if digest == binding.get("file_sha256") else "stale"


def relation_evidence_state(repo: Repo, row: RelationRow) -> str:
    """A relation's derived evidence state (disputed > stale > missing > verified)."""
    evidence = row.get("evidence") or []
    if not evidence:
        return "disputed" if row.get("evidence_disputed") else "missing"
    return evidence_state(row, [binding_file_state(repo, binding) for binding in evidence])


_MATERIAL_FILE_SUFFIXES = frozenset({
    ".pdf", ".md", ".markdown", ".txt", ".html", ".ipynb", ".csv", ".json",
})


def _safe_schema_reason(err: object) -> tuple[str, str]:
    """Field path and value-free reason; never echoes excerpts or instance bytes."""
    path = getattr(err, "absolute_path", ()) or ()
    field = ".".join(str(part) for part in path) or "<root>"
    validator = str(getattr(err, "validator", ""))
    limit = getattr(err, "validator_value", None)
    if validator == "maxLength":
        return field, f"exceeds maximum length ({limit})"
    if validator == "minLength":
        return field, f"shorter than minimum length ({limit})"
    if validator == "maxItems":
        return field, f"exceeds maximum item count ({limit})"
    if validator == "minItems":
        return field, f"fewer than minimum item count ({limit})"
    if validator in ("minimum", "exclusiveMinimum"):
        return field, f"below minimum ({limit})"
    if validator in ("maximum", "exclusiveMaximum"):
        return field, f"above maximum ({limit})"
    if validator == "type":
        return field, f"expected type {limit}"
    if validator == "required":
        instance = getattr(err, "instance", None)
        if isinstance(limit, list) and isinstance(instance, dict):
            missing = [str(key) for key in limit if key not in instance]
            if missing:
                return field, f"missing required property {missing[0]!r}"
        return field, "missing required property"
    if validator == "additionalProperties":
        return field, "contains an unexpected property"
    if validator == "pattern":
        return field, "does not match the required pattern"
    if validator == "format":
        return field, f"invalid format ({limit})"
    if validator == "enum":
        return field, "not one of the allowed values"
    return field, f"failed schema constraint ({validator})"


def sidecar_path(root: Path) -> Path:
    return root / SIDECAR_REL


def load_sidecar(root: Path) -> PracticeIndex:
    path = sidecar_path(root)
    if path.is_symlink():
        raise PracticeSidecarUnreadable(f"practice-index cannot be a symlink: {path}")
    if not path.exists():
        return {"items": []}
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PracticeSidecarUnreadable(
            f"practice-index unreadable ({path}): invalid UTF-8 at byte {exc.start}"
        ) from exc
    except OSError as exc:
        detail = exc.strerror or type(exc).__name__
        raise PracticeSidecarUnreadable(f"practice-index unreadable ({path}): {detail}") from exc
    try:
        data = yaml.load(raw, Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        loc = f"line {mark.line + 1}, column {mark.column + 1}" if mark is not None else "parse error"
        raise PracticeSidecarUnreadable(
            f"practice-index unreadable ({path}): invalid YAML ({loc})"
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise PracticeSidecarUnreadable("practice-index invalid at <root>: must be a mapping with an items list")
    validator = load_standalone_validator(
        root / "system/schema/practice-index.schema.json", format_checker=True)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda err: (tuple(str(part) for part in err.absolute_path), str(err.validator)),
    )
    if errors:
        field, reason = _safe_schema_reason(errors[0])
        raise PracticeSidecarUnreadable(f"practice-index invalid at {field}: {reason}")
    return cast(PracticeIndex, data)


def dump_sidecar(data: PracticeIndex) -> str:
    rows = sorted(data["items"], key=lambda row: row["item_id"].encode("utf-8"))
    return yaml.safe_dump({"items": rows}, sort_keys=False, allow_unicode=True)


def row_for(data: PracticeIndex, item_id: str) -> PracticeRow | None:
    for row in data["items"]:
        if row["item_id"] == item_id:
            return row
    return None


@dataclass
class EffectiveItem:
    item: PracticeItem
    row: PracticeRow | None
    status: str
    reasons: list[str] = field(default_factory=list)

    @property
    def checked(self) -> bool:
        """Eligible as a verified item (export applies its own extra gates)."""
        return self.status in CHECKED_STATUSES and not self.reasons


def _proof_ok(repo: Repo, row: PracticeRow) -> str | None:
    """Why the row's proofs do not support its status, or None.

    Re-checked on every read, not only when recorded: a stored source binding
    must still verify in full (registered source, current digest, page and
    the excerpt verbatim on that page), so a hand-edited sidecar cannot keep
    an item eligible.
    """
    status = row["status"]
    if status in ("unverified", "disputed"):
        return None
    method = METHOD_FOR_STATUS.get(status)
    proofs = [p for p in row.get("verifications") or [] if p.get("method") == method]
    if not proofs:
        return "missing proof"
    proof = proofs[-1]
    if proof.get("artifact_sha256") != row["content_sha256"]:
        return "proof was recorded for different item content"
    if status == "source-matched":
        binding = proof.get("source_binding")
        if not binding:
            return "source-matched proof has no source binding"
        if not str(binding.get("quote") or "").strip():
            return "source-matched proof has no excerpt of the official answer"
        problem = verified_binding(repo, binding)
        if problem:
            return f"source-matched proof no longer verifies: {problem}"
    if status == "cross-checked":
        # No stored independent comparison exists to check a digest against.
        return "cross-checked has no stored independent comparison"
    return None


def _effective_item(repo: Repo, data: PracticeIndex, item: PracticeItem) -> EffectiveItem:
    row = row_for(data, item.item_id)
    if row is None:
        return EffectiveItem(item=item, row=None, status="unverified")
    reasons: list[str] = []
    current = content_sha256(item.item_id, item.prompt, item.solution)
    if row["content_sha256"] != current:
        reasons.append("content changed since verification")
    for binding in row.get("source_bindings") or []:
        problem = verified_binding(repo, binding)
        if problem:
            reasons.append(f"source binding no longer verifies: {problem}")
            break
    proof_problem = _proof_ok(repo, row)
    if proof_problem:
        reasons.append(proof_problem)
    status = row["status"]
    if reasons and status in CHECKED_STATUSES:
        status = "unverified"
    return EffectiveItem(item=item, row=row, status=status, reasons=reasons)


def note_items(repo: Repo, note: Note) -> tuple[list[EffectiveItem], list[str]]:
    """(effective items, diagnostic reasons) for one canonical note."""
    extraction = extract_items(note.id, note.meta.get("role"), note.body)
    diagnostics = [f"{d.label or note.id}: {d.reason}" for d in extraction.diagnostics]
    data = load_sidecar(repo.root)
    return [_effective_item(repo, data, item) for item in extraction.items], diagnostics


def checked_practice_by_note(repo: Repo) -> dict[str, list[EffectiveItem]]:
    """Current checked items for notes named by the verification sidecar.

    Gated per item: an item with its own problem is never extracted, and a
    note-level problem extracts nothing, so a diagnostic about one item never
    hides its checked siblings.
    """
    data = load_sidecar(repo.root)
    note_ids = {row["item_id"].partition("#")[0] for row in data["items"]}
    checked: dict[str, list[EffectiveItem]] = {}
    for note_id in sorted(note_ids):
        note = repo.notes.get(note_id)
        if note is None:
            continue
        extraction = extract_items(note.id, note.meta.get("role"), note.body)
        items = [_effective_item(repo, data, item) for item in extraction.items]
        checked[note_id] = [item for item in items if item.checked]
    return checked


def current_material_digest(repo: Repo, relative: object) -> str | None:
    """SHA-256 of the material file a binding names, or None if unusable."""
    path = material_file(repo, relative)
    if path is None:
        return None
    try:
        return file_sha256(path)
    except OSError:
        return None


#: Page counts and page text of pinned PDFs, keyed by path and the digest the
#: caller has just confirmed is current. Read-back verification asks for the
#: same page on every projection; extracting it once per file version keeps
#: that cheap, and a changed file has a different digest.
_PDF_PAGE_COUNTS: dict[tuple[str, str], int] = {}
_PDF_PAGE_TEXT: dict[tuple[str, str, int], str] = {}


def _pinned_page(path: Path, digest: str, page: int, *, with_text: bool) -> tuple[int, str]:
    """(page count, text of ``page`` or "") for a PDF whose digest is current."""
    key = (str(path), digest)
    count = _PDF_PAGE_COUNTS.get(key)
    text = _PDF_PAGE_TEXT.get((*key, page)) if with_text else ""
    if count is None or text is None:
        from learning_os.store.materials.pdf_text import pdf_page_text, pdf_reader

        reader = pdf_reader(path.read_bytes())
        count = len(reader.pages)
        _PDF_PAGE_COUNTS[key] = count
        if with_text and 1 <= page <= count:
            text = pdf_page_text(reader, page)
            _PDF_PAGE_TEXT[(*key, page)] = text
    return count, text or ""


def _registered_is_file(repo: Repo, registered_path: str) -> bool:
    """Whether a registered material path denotes a single file rather than a directory."""
    if not registered_path or registered_path.endswith("/"):
        return False
    try:
        resolved = resolve_symlinks_inside(
            repo.learningos_root / "materials",
            repo.materials_root / registered_path,
            strict=False,
        )
    except (PathBoundaryError, OSError):
        resolved = None
    if resolved is not None:
        if resolved.is_dir():
            return False
        if resolved.is_file():
            return True
    return PurePosixPath(registered_path).suffix.lower() in _MATERIAL_FILE_SUFFIXES


def verified_binding(repo: Repo, binding: Mapping[str, object]) -> str | None:
    """Why a proposed source binding cannot be admitted, or None.

    Known source, current pinned digest, physical page bounds, and — when a
    quote is carried — the quote verbatim on that page (open item 2, via the
    existing span machinery: `pdf_page_text` over the pinned bytes).
    """
    source_id = binding.get("source_id")
    if not isinstance(source_id, str) or source_id not in repo.sources:
        return "binding names an unknown source"
    relative = binding.get("material_relpath")
    if not isinstance(relative, str) or PurePosixPath(relative).suffix.lower() != ".pdf":
        return "binding must name a material PDF"
    registered = parse_material_uri(repo.sources[source_id].get("material"))
    if registered is not None and _registered_is_file(repo, registered.path):
        if relative != registered.path:
            return "binding PDF does not match the registered source file"
    elif not relative.startswith((registered.path if registered else source_id).rstrip("/") + "/"):
        return "binding PDF is outside the registered source"
    if binding_file_state(repo, binding) != "ok":
        return "binding file is missing or its digest changed"
    page = binding.get("page")
    quote = binding.get("quote", "")
    if type(page) is not int or page < 1 or not isinstance(quote, str):
        return "binding needs a physical PDF page and a text excerpt"
    path = material_file(repo, relative)
    if path is None:
        return "binding file is missing or its digest changed"
    try:
        page_count, page_text = _pinned_page(
            path, str(binding.get("file_sha256")), page, with_text=bool(quote))
    except Exception as exc:  # extraction failure refuses, never passes
        return f"binding page could not be read: {exc}"
    if page > page_count:
        return "binding page is outside the pinned file"
    if quote and (not normalize_quote(quote) or normalize_quote(quote) not in normalize_quote(page_text)):
        return "quote does not appear verbatim on the pinned page"
    return None
