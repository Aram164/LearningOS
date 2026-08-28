"""knowledge/ — the concept graph, the shelved notes, and the Garden.

Concepts and notes are canonical; the Garden deliberately is not. Keeping all
three here makes that boundary visible in one file instead of implied by
position in a long function.
"""

from __future__ import annotations

from pathlib import Path

from .model import GardenNote, Note, Repo, _register
from .vocabulary import GARDEN_TAG_RE, _strip_code
from .yamlio import LoaderError, _load_registry, _read_text, _record_id, parse_frontmatter


def load_concepts(repo: Repo, root: Path) -> None:
    """Concepts (consolidated or partitioned)."""
    records, origins, failures = _load_registry(
        root / "knowledge" / "concepts.yaml", root / "knowledge" / "concepts", "concepts",
        root=root,
    )
    repo.parse_failures.extend(failures)
    for rec, origin in zip(records, origins, strict=True):
        cid = _record_id(rec)
        if cid is None:
            repo.parse_failures.append(
                (origin, f"{origin}: concept record with missing or empty id — skipped"))
            continue
        _register(repo, repo.concepts, cid, rec, origin, "concept")
        repo.concept_origins.setdefault(cid, origin)


def load_relations(repo: Repo, root: Path) -> None:
    """Concept relations (consolidated or partitioned)."""
    records, _, failures = _load_registry(
        root / "knowledge" / "concept-relations.yaml",
        root / "knowledge" / "concept-relations",
        "relations",
        root=root,
    )
    repo.parse_failures.extend(failures)
    repo.relations = records


def load_notes(repo: Repo, root: Path) -> None:
    notes_dir = root / "knowledge" / "notes"
    if not notes_dir.is_dir():
        return
    for f in sorted(notes_dir.rglob("*.md")):
        try:
            meta, body = parse_frontmatter(_read_text(f, root), f)
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        if "id" in meta and _record_id(meta) is None:
            repo.parse_failures.append(
                (f, f"{f}: note frontmatter id is empty or not a string — skipped"))
            continue
        nid = str(meta.get("id", f.stem))
        note = Note(id=nid, path=f, meta=meta, body=body)
        _register(repo, repo.notes, nid, note, f, "note")


def load_garden(repo: Repo, root: Path) -> None:
    """Garden (exploratory layer — CLAUDE.md §14).

    Free-form Markdown in knowledge/garden/: NO frontmatter schema, NOT
    registered as notes, and skipped by the validator (see rules.py
    _in_garden). We only read the body and pull inline #tags so the Nebula view
    can group them. README, dot- and underscore-files are treated as meta and
    excluded from the idea list.
    """
    garden_dir = root / "knowledge" / "garden"
    if not garden_dir.is_dir():
        return
    for f in sorted(garden_dir.rglob("*.md")):
        rel_parts = f.relative_to(garden_dir).parts
        if (f.name.startswith((".", "_")) or f.stem.lower() == "readme"
                or any(part in {"transcriptions", "syntheses"}
                       or part.startswith((".", "_")) for part in rel_parts[:-1])):
            continue
        try:
            text = _read_text(f, root, errors="replace")
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        tags = sorted(set(GARDEN_TAG_RE.findall(_strip_code(text))))
        repo.garden_notes.append(GardenNote(path=f, body=text, tags=tags))
