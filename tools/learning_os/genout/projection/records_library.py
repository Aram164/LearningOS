"""Record projection for sources/: the source registry and its collections."""

from __future__ import annotations

from typing import Callable

from ...loader import Repo
from ..atlas import ATLAS_COLLECTION_DOMAIN
from ..materials import _material_location
from .grouping import ordered_thematic_group_ids, source_thematic_groups

Revision = Callable[..., int]


def project_sources(repo: Repo, revision: Revision) -> list[dict]:
    thematic_groups = source_thematic_groups(repo)
    records = []
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        records.append({
            "id": sid, "type": "source", "title": s.get("title", ""),
            "revision": revision(sid, s),
            "path": str(repo.source_origins.get(sid, "").relative_to(repo.root))
            if repo.source_origins.get(sid) else "sources/sources.yaml",
            "source_type": s.get("type", ""),
            "thematic_group_ids": thematic_groups.get(sid, []),
            # ADR-009 topic facet. Projected even when empty, so an interface can
            # tell "no topics yet" from "this build predates topics" — on-use
            # population means most sources carry none for a long time, and that
            # sparsity is a fact to render, not a gap to hide.
            "topics": list(s.get("topics", []) or []),
            # interface fields: everything needed to SHOW and OPEN a source.
            # `material_path` is resolved HERE (material:// → the .flat farm is
            # a business rule, loader.materials_root) so no interface has to
            # reimplement URI resolution. It is relative to the LearningOS
            # root, i.e. the vault's parent.
            "url": s.get("url"),
            "material": s.get("material"),
            **_material_location(repo, s.get("material")),
            "authors": list(s.get("authors", []) or []),
            "organization": s.get("organization"),
            "year": s.get("year"),
            "identifiers": dict(s.get("identifiers", {}) or {}),
            "roles": sorted({str(r) for ev in (s.get("evaluations") or [])
                             for r in (ev.get("roles") or [])}),
            # `useful_sections` is where the reading plan actually lives ("read
            # ch. 3 for X") — projected with its concept links so an interface
            # can turn a source into a navigable table of contents.
            # Every field the evaluation schema allows is projected. It is a
            # closed schema (`additionalProperties: false`), so this list and
            # that one are the same list by construction — a projection that
            # emitted a subset silently held pedagogical judgment inside the
            # repository, and one that emitted an extra ("verdict", which the
            # schema has never allowed) shipped a field that could only ever
            # be null.
            "evaluations": [
                {"roles": list(ev.get("roles", []) or []),
                 "level": ev.get("level"),
                 "audience": list(ev.get("audience", []) or []),
                 "prerequisites": list(ev.get("prerequisites", []) or []),
                 "strengths": list(ev.get("strengths", []) or []),
                 "weaknesses": list(ev.get("weaknesses", []) or []),
                 "reviewed": ev.get("reviewed"),
                 "concepts": sorted(ev.get("concepts", []) or []),
                 "useful_sections": [
                     {"section": str(k), "note": str(v)}
                     for entry in (ev.get("useful_sections") or [])
                     if isinstance(entry, dict)
                     for k, v in entry.items()
                 ]}
                for ev in (s.get("evaluations") or []) if isinstance(ev, dict)
            ],
        })
    return records


def project_collections(repo: Repo, revision: Revision) -> list[dict]:
    records = []
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        entries = [e for e in doc.get("entries", []) or [] if isinstance(e, dict)]
        collection_kind = doc.get("collection_kind", "catalogue")
        records.append({
            "id": name,
            "type": "topic-pack" if collection_kind == "topic-pack" else "collection",
            "revision": revision(name, doc),
            "collection_kind": collection_kind,
            "title": doc.get("title", name),
            "path": f"sources/collections/{name}.yaml",
            "thematic_group_ids": ordered_thematic_group_ids(
                repo, doc.get("thematic_group_ids", []) or []),
            "purpose": " ".join(str(doc.get("purpose", "")).split()) or None,
            "sources": [str(e.get("source", "")) for e in entries],
            # A shelf is curation, not a bag of ids: its rationale, its domain and
            # each entry's group + role are what make it browsable. Projected here
            # so no interface re-parses the collection YAML (ADR-006).
            "summary": " ".join(str(doc.get("description", "")).split()),
            "domain": ATLAS_COLLECTION_DOMAIN.get(name, "cross-domain"),
            # File order is canonical for topic packs and catalogues alike.
            "entries": [{"source": str(e.get("source", "")),
                         "group": str(e.get("group", "")) or None,
                         "why": " ".join(str(e.get("why", "")).split()) or None}
                        for e in entries],
        })
    return records
