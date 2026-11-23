"""Deterministic JSON Canvas board templates (P2, IMPLEMENTATION-PLAN §P2).

Core publishes templates under ``generated/atlas/`` and the board catalog in
the manifest. Core never writes the editable ``boards/`` namespace; the UI
owns working copies there (P3).
"""

from __future__ import annotations

import hashlib
import json

from learning_os.derive.projection.canvas import CANVAS_EDGE_COLORS, _concept_depths
from learning_os.derive.projection.concepts import PREREQ_TYPES
from learning_os.domain.relations import enriched_relation, relation_evidence_state
from learning_os.domain.snapshot import Repo

CARD_W, CARD_H, STEP_X, STEP_Y = 320, 160, 520, 200

TEMPLATE_PREFIX = "generated/atlas/templates"
CARD_PREFIX = "generated/atlas/cards"


def _canvas_bytes(canvas: dict) -> bytes:
    return (json.dumps(canvas, separators=(",", ":"), sort_keys=True,
                       ensure_ascii=False) + "\n").encode("utf-8")


def _active_relations(repo: Repo) -> list[dict]:
    return [enriched_relation(r) for r in repo.relations
            if r.get("status", "active") == "active"]


def scopes_for(repo: Repo, module_to_concepts: dict, unit_to_concepts: dict) -> list[dict]:
    """The four board scopes, in catalog order (semester, module, lecture, exam)."""
    scopes: list[dict] = []
    for pid in sorted(repo.programs):
        program = repo.programs[pid]
        for semester in program.data.get("semesters") or []:
            sid = str(semester.get("id", ""))
            if sid:
                scopes.append({
                    "kind": "semester", "id": f"{pid}--{sid}",
                    "title": str(semester.get("title") or sid),
                    "parent_kind": None, "parent_id": None,
                    "concept_ids": sorted({
                        c for mid, cs in module_to_concepts.items()
                        for c in cs
                        if str(repo.modules.get(mid, {}).get("program_id", pid)) == pid
                    }),
                })
    for mid in sorted(set(repo.modules) | set(module_to_concepts)):
        module = repo.modules.get(mid, {})
        scopes.append({
            "kind": "module", "id": mid,
            "title": str(module.get("title") or mid),
            "parent_kind": "semester",
            "parent_id": _semester_scope_id(repo, module),
            "concept_ids": sorted(module_to_concepts.get(mid, [])),
        })
    for uid in sorted(set(repo.units) | set(unit_to_concepts)):
        unit = repo.units.get(uid)
        scopes.append({
            "kind": "lecture", "id": uid,
            "title": str(unit.data.get("title") or uid) if unit else uid,
            "parent_kind": "module",
            "parent_id": unit.module_id if unit else None,
            "concept_ids": sorted(unit_to_concepts.get(uid, [])),
        })
    for nid in sorted(repo.notes):
        note = repo.notes[nid]
        if note.meta.get("role") != "mock-exam":
            continue
        scopes.append({
            "kind": "exam", "id": nid,
            "title": str(note.meta.get("title") or nid),
            "parent_kind": "module", "parent_id": None,
            "concept_ids": sorted(note.meta.get("concepts") or []),
        })
    return scopes


def _semester_scope_id(repo: Repo, module: dict) -> str | None:
    pid = module.get("program_id")
    sid = module.get("semester_id")
    if pid and sid:
        return f"{pid}--{sid}"
    return None


def build_board_template(repo: Repo, scope: dict, child_scopes: list[dict]) -> dict:
    concepts = [c for c in scope["concept_ids"] if c in repo.concepts]
    relations = [r for r in _active_relations(repo)
                 if r["from"] in concepts and r["to"] in concepts]
    depths = _concept_depths(relations, set(concepts))
    by_layer: dict[int, list[str]] = {}
    for cid in concepts:
        by_layer.setdefault(depths.get(cid, 0), []).append(cid)

    nodes: list[dict] = []
    for layer in sorted(by_layer):
        for i, cid in enumerate(sorted(by_layer[layer])):
            rec = repo.concepts[cid]
            rel_summary = _relation_summary(cid, relations)
            state = _concept_evidence_state(repo, cid, relations)
            text = f"**{rec.get('label', cid)}**\n`{cid}`"
            if rec.get("description"):
                text += f"\n{rec['description']}"
            if rel_summary:
                text += "\n" + rel_summary
            text += f"\nEvidence: {state}"
            nodes.append({
                "id": f"los-concept-{cid}", "type": "text", "text": text,
                "x": layer * STEP_X, "y": i * STEP_Y,
                "width": CARD_W, "height": CARD_H,
            })
    for rel in relations:
        for ordinal, binding in enumerate(rel.get("evidence") or []):
            key = f"{rel['from']}--{rel['type']}--{rel['to']}"
            nodes.append({
                "id": f"los-evidence-{key}--{ordinal}", "type": "text",
                "text": (f"\"{binding['quote']}\"\n"
                         f"{binding['source_id']} · pdf p. {binding['page']}"),
                "x": (depths.get(rel["from"], 0) + 1) * STEP_X,
                "y": len(nodes) * 40 % (STEP_Y * 4),
                "width": CARD_W, "height": CARD_H,
            })
    for child in child_scopes:
        nodes.append({
            "id": f"los-scope-{child['kind']}--{child['id']}", "type": "file",
            "file": f"{TEMPLATE_PREFIX}/{child['kind']}/{child['id']}.canvas",
            "x": 0, "y": (len(nodes) + 1) * STEP_Y,
            "width": CARD_W, "height": CARD_H,
        })

    edges: list[dict] = []
    for rel in relations:
        strict = rel["type"] in PREREQ_TYPES
        edges.append({
            "id": f"los-rel-{rel['from']}--{rel['type']}--{rel['to']}",
            "fromNode": f"los-concept-{rel['to'] if strict else rel['from']}",
            "fromSide": "right" if strict else "left",
            "toNode": f"los-concept-{rel['from'] if strict else rel['to']}",
            "toSide": "left" if strict else "right",
            "label": (f"Strict · prerequisite for ({rel['type']})" if strict
                      else f"Semantic · {rel['type']}"),
            "color": CANVAS_EDGE_COLORS.get(rel["type"], "4"),
        })
    edges.sort(key=lambda e: e["id"])
    nodes.sort(key=lambda n: n["id"])
    return {"nodes": nodes, "edges": edges}


def _relation_summary(cid: str, relations: list[dict]) -> str:
    bits = []
    for rel in sorted(relations, key=lambda r: (r["from"], r["type"], r["to"])):
        if rel["from"] == cid:
            bits.append(f"{rel['type']} → {rel['to']}")
        if rel["to"] == cid:
            bits.append(f"← {rel['type']} from {rel['from']}")
    return " · ".join(bits)


def _concept_evidence_state(repo: Repo, cid: str, relations: list[dict]) -> str:
    states = [relation_evidence_state(repo, r) for r in relations
              if cid in (r["from"], r["to"])]
    for state in ("disputed", "stale", "missing", "verified"):
        if state in states:
            return state
    return "missing"


def build_concept_card(repo: Repo, cid: str, generated_at: str = "") -> str:
    from learning_os.derive.projection.common import md_header
    rec = repo.concepts[cid]
    lines = md_header(f"Concept card — {rec.get('label', cid)}", generated_at)
    lines += [f"`{cid}`", ""]
    if rec.get("description"):
        lines += [rec["description"], ""]
    relations = [r for r in _active_relations(repo) if cid in (r["from"], r["to"])]
    summary = _relation_summary(cid, relations)
    if summary:
        lines += [summary, ""]
    note_ids = sorted(n.id for n in repo.notes.values()
                      if cid in (n.meta.get("concepts") or []))
    if note_ids:
        lines += ["Notes: " + ", ".join(note_ids), ""]
    lines += [f"Evidence: {_concept_evidence_state(repo, cid, relations)}",
              "Verified practice: 0", ""]
    return "\n".join(lines)


def build_atlas_boards(repo: Repo, indexes: dict, generated_at: str = "") -> tuple[list[dict], dict[str, str]]:
    """(catalog, {generated-relative path: text}) for templates and cards."""
    module_to_concepts = indexes.get("module_to_concepts", {})
    unit_to_concepts = indexes.get("unit_to_concepts", {})
    scopes = scopes_for(repo, module_to_concepts, unit_to_concepts)
    by_parent: dict[tuple, list[dict]] = {}
    for scope in scopes:
        if scope["parent_kind"]:
            by_parent.setdefault((scope["parent_kind"], scope["parent_id"]), []).append(scope)

    catalog: list[dict] = []
    files: dict[str, str] = {}
    for scope in scopes:
        children = by_parent.get((scope["kind"], scope["id"]), [])
        template = build_board_template(repo, scope, children)
        path = f"{TEMPLATE_PREFIX}/{scope['kind']}/{scope['id']}.canvas"
        files[path] = _canvas_bytes(template).decode("utf-8")
        concept_ids = [c for c in scope["concept_ids"] if c in repo.concepts]
        relation_count = sum(
            1 for r in _active_relations(repo)
            if r["from"] in concept_ids and r["to"] in concept_ids)
        catalog.append({
            "kind": scope["kind"], "id": scope["id"], "title": scope["title"],
            "parent_kind": scope["parent_kind"], "parent_id": scope["parent_id"],
            "template_path": path,
            "working_path": f"boards/atlas/{scope['kind']}/{scope['id']}.canvas",
            "sha256": hashlib.sha256(files[path].encode("utf-8")).hexdigest(),
            "concept_count": len(concept_ids),
            "relation_count": relation_count,
        })
    for cid in sorted(repo.concepts):
        files[f"{CARD_PREFIX}/{cid}.md"] = build_concept_card(repo, cid, generated_at)
    catalog.sort(key=lambda e: (e["kind"], e["id"]))
    return catalog, files
