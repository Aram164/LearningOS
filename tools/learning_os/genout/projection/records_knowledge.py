"""Record projection for knowledge/: notes and concepts."""

from __future__ import annotations

from ...loader import Repo
from ..common import _first_para, _strip_headings


def project_notes(repo: Repo) -> list[dict]:
    records = []
    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        rel = note.path.relative_to(repo.root)
        records.append({
            "id": note.id, "type": "note",
            "title": note.meta.get("title", ""),
            "path": str(rel),
            "domain": rel.parent.name if rel.parent.name != "notes" else "",
            "summary": _first_para(_strip_headings(note.body))[:400],
            "role": note.meta.get("role", "synthesis"),
            "state": note.meta.get("state"),
            "authorship": note.meta.get("authorship"),
            "concepts": sorted(note.meta.get("concepts", []) or []),
            "sources": sorted(note.meta.get("sources", []) or []),
            "contexts": sorted(note.meta.get("contexts", []) or []),
            "attachments": list(note.meta.get("attachments", []) or []),
            "evidence": list(note.meta.get("evidence", []) or []),
            "supersedes": sorted(note.meta.get("supersedes", []) or []),
            "reviewed": note.meta.get("reviewed"),
            # The note-life axis: how the text got here and whether its meaning
            # has been checked. Both are schema fields (v3) and both are
            # authored today; omitting them meant the provenance of a
            # transcribed note stopped at the repository boundary.
            "transcription": note.meta.get("transcription"),
            "semantic_review": note.meta.get("semantic_review"),
        })
    return records


def project_concepts(repo: Repo) -> list[dict]:
    records = []
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        records.append({
            "id": cid, "type": "concept", "title": c.get("label", ""),
            "path": str(repo.concept_origins.get(cid, "").relative_to(repo.root))
            if repo.concept_origins.get(cid) else "knowledge/concepts.yaml",
            "aliases": sorted(c.get("aliases", []) or []),
            "deprecated": bool(c.get("deprecated", False)),
        })
    return records
