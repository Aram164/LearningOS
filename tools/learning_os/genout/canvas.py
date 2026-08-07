"""Obsidian Canvas rendering for the concept graph."""

from __future__ import annotations

from ..loader import Repo
from .common import _json_header
from .concepts import PREREQ_TYPES

CANVAS_EDGE_COLORS = {
    "requires": "1", "builds-on": "2", "derives": "3", "generalizes": "4",
    "contrasts-with": "5", "equivalent-to": "6",
    "applies-in": "#8fa1b3", "motivates": "#d08770",
}


_CANVAS_NODE_W = 320


_CANVAS_NODE_H = 150


_CANVAS_GAP_X = 200


_CANVAS_GAP_Y = 40


def _concept_depths(relations: list[dict], involved: set[str]) -> dict[str, int]:
    """Longest-prerequisite-path depth over requires/builds-on edges (the same
    edge set as the Mermaid concept map). Cycles fall back to depth 0."""
    prereqs: dict[str, set[str]] = {c: set() for c in involved}
    for r in relations:
        if r.get("type") in PREREQ_TYPES:
            a, b = str(r.get("from")), str(r.get("to"))
            if a in involved and b in involved:
                prereqs[a].add(b)
    depths: dict[str, int] = {}

    def depth(c: str, seen: frozenset[str]) -> int:
        if c in depths:
            return depths[c]
        if c in seen:
            return 0  # cycle guard
        d = 0
        for p in sorted(prereqs.get(c, ())):
            d = max(d, 1 + depth(p, seen | {c}))
        depths[c] = d
        return d

    for c in sorted(involved):
        depth(c, frozenset())
    return depths


def build_concept_canvas(repo: Repo, generated_at: str) -> dict:
    """JSON Canvas (https://jsoncanvas.org) rendering of the relation registry
    (ADR-006): every concept appearing in >=1 relation becomes a card (label,
    aliases, links to up to three notes); every relation becomes a labelled,
    colored edge. Deterministic layered layout: x = prerequisite depth,
    y = alphabetical within the layer. Obsidian renders this natively; the
    file is disposable like every generated output."""
    involved = set()
    for r in repo.relations:
        involved.add(str(r.get("from")))
        involved.add(str(r.get("to")))
    involved &= set(repo.concepts)

    depths = _concept_depths(repo.relations, involved)
    by_layer: dict[int, list[str]] = {}
    for c in sorted(involved):
        by_layer.setdefault(depths[c], []).append(c)

    note_links: dict[str, list[str]] = {c: [] for c in involved}
    for nid in sorted(repo.notes):
        n = repo.notes[nid]
        rel = n.path.relative_to(repo.root).as_posix()
        for c in n.meta.get("concepts") or []:
            if c in note_links and len(note_links[c]) < 3:
                note_links[c].append(f"[{nid}](../{rel})")

    nodes = []
    for layer in sorted(by_layer):
        for i, cid in enumerate(by_layer[layer]):
            rec = repo.concepts[cid]
            label = rec.get("label", cid)
            aliases = ", ".join(rec.get("aliases") or [])
            text = f"**{label}**\n`{cid}`"
            if aliases:
                text += f"\n_{aliases}_"
            if note_links[cid]:
                text += "\n" + " · ".join(note_links[cid])
            nodes.append({
                "id": cid, "type": "text", "text": text,
                "x": layer * (_CANVAS_NODE_W + _CANVAS_GAP_X),
                "y": i * (_CANVAS_NODE_H + _CANVAS_GAP_Y),
                "width": _CANVAS_NODE_W, "height": _CANVAS_NODE_H,
            })

    edges = []
    for r in repo.relations:
        a, b, t = str(r.get("from")), str(r.get("to")), str(r.get("type"))
        if a not in involved or b not in involved:
            continue
        edges.append({
            "id": f"{a}--{t}--{b}",
            "fromNode": a, "fromSide": "left",
            "toNode": b, "toSide": "right",
            "label": t, "color": CANVAS_EDGE_COLORS.get(t, "4"),
        })
    edges.sort(key=lambda e: e["id"])

    return {"_generated": _json_header(generated_at), "nodes": nodes, "edges": edges}
