"""Concept index, map, backlinks and the prerequisite dependency report."""

from __future__ import annotations

import re
from ..loader import Repo
from .common import _json_header, _letter_toc, _md_header, mermaid_node_ids
from .manifest import _source_fingerprint

def build_backlinks(repo: Repo, generated_at: str) -> dict:
    concept_to_notes: dict[str, list] = {}
    source_to_notes: dict[str, list] = {}
    note_incoming: dict[str, list] = {}
    workspace_to_notes: dict[str, list] = {}
    concept_relations: dict[str, dict] = {}
    module_to_workspaces: dict[str, list] = {}
    unit_to_workspaces: dict[str, list] = {}
    module_to_units: dict[str, list] = {}
    source_to_units: dict[str, list] = {}

    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        for cid in note.meta.get("concepts", []) or []:
            concept_to_notes.setdefault(cid, []).append(note.id)
        for sid in note.meta.get("sources", []) or []:
            source_to_notes.setdefault(sid, []).append(note.id)
        for wid in note.meta.get("contexts", []) or []:
            workspace_to_notes.setdefault(wid, []).append(note.id)
        for target in note.meta.get("supersedes", []) or []:
            note_incoming.setdefault(target, []).append(
                {"from": note.id, "kind": "superseded-by"})
        for m in re.finditer(r"note://(note-[a-z0-9-]+)", note.body):
            if m.group(1) != note.id:
                note_incoming.setdefault(m.group(1), []).append(
                    {"from": note.id, "kind": "mentions"})
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        for nid in ws.meta.get("notes", []) or []:
            lst = workspace_to_notes.setdefault(ws.id, [])
            if nid not in lst:
                lst.append(nid)
        explicit_modules = ws.meta.get("module_ids", []) or []
        for mid in explicit_modules:
            module_to_workspaces.setdefault(mid, []).append(ws.id)
        for uid in ws.meta.get("unit_ids", []) or []:
            unit_to_workspaces.setdefault(uid, []).append(ws.id)
        # Compatibility only for pre-v2 workspaces. V2 relationships are
        # declared in frontmatter and never inferred from names or prose.
        if not explicit_modules:
            for m in re.finditer(r"\bmodule-[a-z0-9]+(?:-[a-z0-9]+)*\b", ws.body):
                module_to_workspaces.setdefault(m.group(0), []).append(ws.id)
    for mid, module in repo.modules.items():
        module_to_units[mid] = list(module.get("unit_order", []) or [])
    for unit in repo.units.values():
        for scoped in unit.data.get("scope_sources", []) or []:
            sid = scoped.get("source_id") if isinstance(scoped, dict) else None
            if sid:
                source_to_units.setdefault(sid, []).append(unit.id)
        for selection in unit.data.get("source_selections", []) or []:
            sid = selection.get("source_id") if isinstance(selection, dict) else None
            if sid:
                source_to_units.setdefault(sid, []).append(unit.id)
    for study_map in repo.study_maps.values():
        for stage in study_map.data.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id") if isinstance(resource, dict) else None
                if sid:
                    source_to_units.setdefault(sid, []).append(study_map.unit_id)
    for rel in repo.relations:
        frm, to, rtype = rel.get("from"), rel.get("to"), rel.get("type")
        concept_relations.setdefault(frm, {"outgoing": [], "incoming": []})
        concept_relations.setdefault(to, {"outgoing": [], "incoming": []})
        concept_relations[frm]["outgoing"].append({"type": rtype, "to": to})
        concept_relations[to]["incoming"].append({"type": rtype, "from": frm})
    for d in concept_relations.values():
        d["outgoing"].sort(key=lambda e: (e["type"], e["to"]))
        d["incoming"].sort(key=lambda e: (e["type"], e["from"]))
    for m in (concept_to_notes, source_to_notes, workspace_to_notes,
              module_to_workspaces, unit_to_workspaces, module_to_units, source_to_units):
        for k in m:
            m[k] = sorted(set(m[k])) if all(isinstance(x, str) for x in m[k]) else m[k]
    generated_meta = _json_header(generated_at)
    generated_meta.update({
        "contract_version": 2,
        "snapshot_id": f"sha256:{_source_fingerprint(repo)}",
    })
    return {
        "_generated": generated_meta,
        "concept_to_notes": dict(sorted(concept_to_notes.items())),
        "source_to_notes": dict(sorted(source_to_notes.items())),
        "note_incoming": dict(sorted(note_incoming.items())),
        "workspace_to_notes": dict(sorted(workspace_to_notes.items())),
        "concept_relations": dict(sorted(concept_relations.items())),
        "module_to_workspaces": dict(sorted(module_to_workspaces.items())),
        "unit_to_workspaces": dict(sorted(unit_to_workspaces.items())),
        "module_to_units": dict(sorted(module_to_units.items())),
        "source_to_units": dict(sorted(source_to_units.items())),
    }


def _evals_for_concept(repo: Repo, cid: str) -> list[tuple[str, dict, dict]]:
    """(source_id, source, evaluation) pairs whose evaluation targets cid."""
    out = []
    for sid in sorted(repo.sources):
        source = repo.sources[sid]
        for ev in source.get("evaluations", []) or []:
            if cid in (ev.get("concepts") or []):
                out.append((sid, source, ev))
    return out


def _eval_line(sid: str, source: dict, ev: dict) -> str:
    bits = []
    if ev.get("roles"):
        bits.append("roles: " + ", ".join(ev["roles"]))
    if ev.get("level"):
        bits.append(f"level: {ev['level']}")
    if ev.get("strengths"):
        bits.append(ev["strengths"][0])
    detail = " — ".join(bits)
    return f"**{source.get('title', sid)}** (`{sid}`)" + (f" — {detail}" if detail else "")


def build_concept_index(repo: Repo, backlinks: dict, generated_at: str) -> str:
    lines = _md_header("Concept index", generated_at)
    toc_entries = []
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        heading = label + (" *(deprecated)*" if c.get("deprecated") else "")
        toc_entries.append((label, heading))
    toc_entries.sort(key=lambda e: e[0].lower())
    lines.append("## Contents")
    lines.append("")
    lines.extend(_letter_toc(toc_entries))
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        dep = " *(deprecated)*" if c.get("deprecated") else ""
        lines.append(f"## {label}{dep}")
        lines.append("")
        lines.append(f"`{cid}`")
        if c.get("aliases"):
            lines.append("")
            lines.append("Aliases: " + " · ".join(sorted(c["aliases"])))
        if c.get("description"):
            lines.append("")
            lines.append(f"*{c['description']}*")
        if c.get("replaced_by"):
            lines.append("")
            lines.append(f"Replaced by: `{c['replaced_by']}`")
        note_ids = backlinks["concept_to_notes"].get(cid, [])
        if note_ids:
            lines.append("")
            lines.append("**Notes:**")
            lines.append("")
            for nid in note_ids:
                note = repo.notes.get(nid)
                role = note.meta.get("role", "synthesis") if note else "?"
                title = note.meta.get("title", nid) if note else nid
                lines.append(f"- `{nid}` — {title} *(role: {role})*")
        rels = backlinks["concept_relations"].get(cid)
        if rels and (rels["outgoing"] or rels["incoming"]):
            lines.append("")
            lines.append("**Related concepts:**")
            lines.append("")
            for e in rels["outgoing"]:
                lines.append(f"- {e['type']} → `{e['to']}`")
            for e in rels["incoming"]:
                lines.append(f"- ← {e['type']} from `{e['from']}`")
        evals = _evals_for_concept(repo, cid)
        if evals:
            lines.append("")
            lines.append("**Contextual sources:**")
            lines.append("")
            for sid, source, ev in evals:
                lines.append(f"- {_eval_line(sid, source, ev)}")
        lines.append("")
    return "\n".join(lines)


PREREQ_TYPES = ("requires", "builds-on")


def build_dependency_report(repo: Repo, backlinks: dict, generated_at: str) -> str:
    """Concept/module dependency view (ADR-001): direct + transitive
    prerequisites per concept, a layered study order over the prerequisite
    subgraph, and the module -> workspace -> concept graph."""
    prereqs: dict[str, set] = {}
    for rel in repo.relations:
        if rel.get("type") in PREREQ_TYPES:
            prereqs.setdefault(str(rel["from"]), set()).add(str(rel["to"]))

    def closure(cid: str) -> list[str]:
        seen, stack = set(), sorted(prereqs.get(cid, ()))
        while stack:
            c = stack.pop()
            if c in seen or c == cid:
                continue
            seen.add(c)
            stack.extend(sorted(prereqs.get(c, ())))
        return sorted(seen)

    lines = _md_header("Dependency report", generated_at)
    lines.append("*Prerequisite semantics = `requires` + `builds-on` edges from "
                 "the relation registry. `motivates`/`applies-in`/`contrasts-with` "
                 "edges are context, not prerequisites, and are excluded.*")
    lines.append("")

    lines.append("## Prerequisites per concept (direct → transitive)")
    lines.append("")
    for cid in sorted(repo.concepts):
        direct = sorted(prereqs.get(cid, ()))
        if not direct:
            continue
        label = repo.concepts[cid].get("label", cid)
        lines.append(f"- **{label}** (`{cid}`)")
        lines.append(f"  - direct: " + ", ".join(f"`{c}`" for c in direct))
        trans = [c for c in closure(cid) if c not in direct]
        if trans:
            lines.append(f"  - transitive: " + ", ".join(f"`{c}`" for c in trans))
    lines.append("")

    # Layered study order (Kahn levels over the prerequisite subgraph)
    lines.append("## Layered study order")
    lines.append("")
    lines.append("Concepts in the same layer are independent; every concept's "
                 "prerequisites live in earlier layers. Concepts with no "
                 "prerequisite edges in the registry are omitted unless someone "
                 "depends on them.")
    lines.append("")
    involved = set(prereqs)
    for deps in prereqs.values():
        involved |= deps
    remaining = dict((c, set(d for d in prereqs.get(c, ()) if d in involved))
                     for c in involved)
    layer_no = 0
    while remaining:
        ready = sorted(c for c, deps in remaining.items() if not deps)
        if not ready:  # cycle guard — report and stop
            lines.append(f"- ⚠️ cycle detected among: "
                         + ", ".join(f"`{c}`" for c in sorted(remaining)))
            break
        layer_no += 1
        labels = [f"`{c}`" for c in ready]
        lines.append(f"- **Layer {layer_no}:** " + " · ".join(labels))
        for c in ready:
            remaining.pop(c)
        for deps in remaining.values():
            deps.difference_update(ready)
    lines.append("")

    lines.append("## Modules → workspaces → concepts")
    lines.append("")
    m2w = backlinks.get("module_to_workspaces", {})
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        lines.append(f"- **{module.get('title', mid)}** (`{mid}`)")
        wids = m2w.get(mid, [])
        if not wids:
            lines.append("  - (no workspace references it)")
            continue
        for wid in wids:
            ws = repo.workspaces.get(wid)
            if ws is None:
                continue
            cids = sorted(ws.meta.get("concepts", []) or [])
            tail = (": " + ", ".join(f"`{c}`" for c in cids)) if cids else ""
            state = "archived" if ws.archived else ws.status
            lines.append(f"  - `{wid}` ({state}){tail}")
    lines.append("")
    return "\n".join(lines)


def build_concept_map(repo: Repo, generated_at: str) -> str:
    """Mermaid rendering of the prerequisite graph (requires + builds-on).

    Human-facing counterpart of the dependency report: GitHub and VS Code
    render the diagram natively. Context edges (motivates/applies-in/
    contrasts-with) are excluded, same as the dependency report.
    """
    lines = _md_header("Concept map (prerequisite graph)", generated_at)
    lines.append("*Arrows point from prerequisite to dependent — follow the "
                 "arrows to get a study order. Solid = `requires`, "
                 "dotted = `builds-on`. Textual version: "
                 "`dependency-report.md`.*")
    lines.append("")

    edges = sorted(
        (str(r["to"]), str(r["from"]), str(r["type"]))
        for r in repo.relations if r.get("type") in PREREQ_TYPES)
    if not edges:
        lines.append("(no prerequisite edges in the relation registry)")
        lines.append("")
        return "\n".join(lines)

    involved = sorted({c for e in edges for c in e[:2]})
    nodes = mermaid_node_ids(involved)
    lines.append("```mermaid")
    lines.append("graph LR")
    for cid in involved:
        label = str(repo.concepts.get(cid, {}).get("label", cid)).replace('"', "'")
        lines.append(f'    {nodes[cid]}["{label}"]')
    for pre, dep, rtype in edges:
        arrow = "-->" if rtype == "requires" else "-.->"
        lines.append(f"    {nodes[pre]} {arrow} {nodes[dep]}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)
