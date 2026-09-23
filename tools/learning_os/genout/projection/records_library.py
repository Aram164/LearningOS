"""Record projection for sources/: the source registry and its collections."""

from __future__ import annotations

from collections.abc import Callable

from ...loader import Repo
from ..atlas import ATLAS_COLLECTION_DOMAIN
from ..materials import _material_location
from .grouping import ordered_thematic_group_ids, source_thematic_groups

Revision = Callable[..., int]


def current_synthesis_freshness(repo: Repo, synthesis_id: str, dossier: dict) -> dict:
    """One memoized dossier-freshness verdict per build, shared by projectors.

    F13: the curriculum projector publishes every dossier's freshness and the
    library projector counts current dossiers per source; both must read the
    same verdict, or one build hashes every material file twice. Memoized on
    the repo like the session compiler's route map: the loader output is
    immutable within a build, and each repo object carries its own memo.
    """
    # Local import avoids a package-initialization cycle: the synthesis module
    # is a domain service and this is a projection of its output.
    from ...material_synthesis import material_synthesis_freshness

    memo = getattr(repo, "_projected_synthesis_freshness", None)
    if memo is None:
        memo = {}
        try:
            repo._projected_synthesis_freshness = memo
        except AttributeError:  # a Repo that refuses attributes still works
            pass
    shared = getattr(repo, "_projected_material_cache", None)
    if shared is None:
        shared = {}
        try:
            repo._projected_material_cache = shared
        except AttributeError:
            pass
    if synthesis_id not in memo:
        memo[synthesis_id] = material_synthesis_freshness(
            repo.root, str(dossier.get("unit_id", "")), dossier,
            repo=repo, cache=shared)
    return memo[synthesis_id]


def _approved_analysis_counts(repo: Repo) -> dict[str, int]:
    """Distinct current approved assessment routes per source (D13, R6).

    A route counts when an approved dossier assesses it while its dossier is
    current; stale dossiers are retained evidence, not examination. The route's
    own source id is authoritative, never the assessment row's copy of it.
    Memoized on the repo like the session compiler's route map: the loader
    output is immutable, and the projector may run twice in one build.
    """
    # Local import avoids a package-initialization cycle: route references are
    # a domain service, this is a projection of them.
    from ...routes import iter_route_references

    cached = getattr(repo, "_library_approved_analysis_counts", None)
    if cached is not None:
        return cached
    route_source = {ref.route_id: ref.source_id for ref in iter_route_references(repo)}
    per_source: dict[str, set[str]] = {}
    for synthesis_id in sorted(repo.unit_material_syntheses):
        dossier = repo.unit_material_syntheses[synthesis_id]
        if not isinstance(dossier, dict) or dossier.get("status") != "approved":
            continue
        fresh = current_synthesis_freshness(repo, synthesis_id, dossier)
        if fresh.get("status") != "current":
            continue
        for row in dossier.get("route_assessments") or []:
            if not isinstance(row, dict):
                continue
            route_id = row.get("route_id")
            source_id = route_source.get(route_id) if isinstance(route_id, str) else None
            if source_id:
                per_source.setdefault(source_id, set()).add(route_id)
    counts = {sid: len(routes) for sid, routes in per_source.items()}
    try:
        repo._library_approved_analysis_counts = counts
    except AttributeError:  # a Repo that refuses attributes still works
        pass
    return counts


def project_sources(repo: Repo, revision: Revision) -> list[dict]:
    thematic_groups = source_thematic_groups(repo)
    analyses = _approved_analysis_counts(repo)
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
            # Intake provenance is a bounded, factual navigation aid for an
            # agent's first read. Without it, `inspect source-id` knows only
            # that a source exists and has to reopen canonical registry YAML
            # to learn why it was shelved or what known child titles it holds.
            "discovery": s.get("discovery"),
            # Examination state, separate from the evaluations themselves: the
            # Library marks a metadata-only source "placed from metadata" while
            # this says none exists. Always published, so the interface can
            # tell "not examined" from "this build predates examination".
            "examination": {
                "evaluated": bool(s.get("evaluations")),
                "approved_analysis_count": analyses.get(sid, 0),
                "metadata_placed": bool(s.get("discovery")),
            },
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
