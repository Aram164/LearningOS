"""Deterministic JSON Canvas board templates (P2, IMPLEMENTATION-PLAN §P2).

Core publishes templates under ``generated/atlas/`` and the board catalog in
the manifest. Core never writes the editable ``boards/`` namespace; the UI
owns working copies there (P3).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from typing import TypedDict, cast
from urllib.parse import urlencode

from learning_os.derive.projection.canvas import CANVAS_EDGE_COLORS, concept_depths
from learning_os.derive.projection.concepts import PREREQ_TYPES
from learning_os.domain.relations import RelationRow, enriched_relation
from learning_os.domain.snapshot import Repo
from learning_os.store.practice import (
    checked_practice_by_note,
    relation_evidence_state,
)

CARD_W, CARD_H, STEP_X, STEP_Y = 320, 160, 520, 200

TEMPLATE_PREFIX = "generated/atlas/templates"
CARD_PREFIX = "generated/atlas/cards"


class BoardScope(TypedDict):
    kind: str
    id: str
    title: str
    parent_kind: str | None
    parent_id: str | None
    concept_ids: list[str]


class BoardCatalogEntry(TypedDict):
    kind: str
    id: str
    title: str
    parent_kind: str | None
    parent_id: str | None
    template_path: str
    working_path: str
    sha256: str
    concept_count: int
    relation_count: int


def _canvas_bytes(canvas: Mapping[str, object]) -> bytes:
    return (json.dumps(canvas, separators=(",", ":"), sort_keys=True,
                       ensure_ascii=False) + "\n").encode("utf-8")


def _active_relations(repo: Repo) -> list[RelationRow]:
    return [enriched_relation(cast(RelationRow, r)) for r in repo.relations
            if r.get("status", "active") == "active"]


def scopes_for(repo: Repo, module_to_concepts: dict[str, list[str]], unit_to_concepts: dict[str, list[str]],
               exam_concepts: dict[str, set[str]]) -> list[BoardScope]:
    """The four board scopes, in catalog order (semester, module, lecture, exam)."""
    scopes: list[BoardScope] = []
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
                        if _semester_scope_id(repo.modules.get(mid, {})) == f"{pid}--{sid}"
                    }),
                })
    semester_ids = {s["id"] for s in scopes}
    for mid in sorted(set(repo.modules) | set(module_to_concepts)):
        module = repo.modules.get(mid, {})
        parent = _semester_scope_id(module)
        if parent not in semester_ids:
            parent = None
        scopes.append({
            "kind": "module", "id": mid,
            "title": str(module.get("title") or mid),
            "parent_kind": "semester" if parent is not None else None,
            "parent_id": parent,
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
    exam_modules: dict[str, set[str]] = {}
    for unit in repo.units.values():
        exam_id = (unit.data.get("artifacts") or {}).get("mock_exam")
        if exam_id and unit.module_id in repo.modules:
            exam_modules.setdefault(exam_id, set()).add(unit.module_id)
    for nid in sorted(repo.notes):
        note = repo.notes[nid]
        if note.meta.get("role") != "mock-exam":
            continue
        parents = exam_modules.get(nid, set())
        parent = next(iter(parents)) if len(parents) == 1 else None
        scopes.append({
            "kind": "exam", "id": nid,
            "title": str(note.meta.get("title") or nid),
            "parent_kind": "module" if parent is not None else None, "parent_id": parent,
            "concept_ids": sorted(set(note.meta.get("concepts") or []) | exam_concepts.get(nid, set())),
        })
    return scopes


def _semester_scope_id(module: Mapping[str, object]) -> str | None:
    area = module.get("area_id")
    semester = module.get("semester")
    if area and semester:
        return f"{area}--semester-{semester}"
    return None


def build_board_template(repo: Repo, scope: BoardScope, child_scopes: list[BoardScope],
                         practice_counts: Counter[str]) -> dict[str, object]:
    concepts = [c for c in scope["concept_ids"] if c in repo.concepts]
    relations = [r for r in _active_relations(repo)
                 if r["from"] in concepts and r["to"] in concepts]
    depths = concept_depths(relations, set(concepts))
    by_layer: dict[int, list[str]] = {}
    for cid in concepts:
        by_layer.setdefault(depths.get(cid, 0), []).append(cid)

    nodes: list[dict[str, object]] = []
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
            text += f"\nEvidence: {state} · Verified practice: {practice_counts[cid]}"
            text += f"\n[[{CARD_PREFIX}/{cid}|Concept details]]"
            nodes.append({
                "id": f"los-concept-{cid}", "type": "text", "text": text,
                "x": layer * STEP_X, "y": i * STEP_Y,
                "width": CARD_W, "height": CARD_H,
            })
    if not concepts:
        nodes.append({
            "id": "los-group-empty", "type": "text", "text": "No scoped concepts are recorded.",
            "x": 0, "y": 0, "width": CARD_W, "height": CARD_H,
        })
    evidence_x = (max(depths.values(), default=0) + 1) * STEP_X
    evidence_index = 0
    for rel in relations:
        for ordinal, binding in enumerate(rel.get("evidence") or []):
            key = f"{rel['from']}--{rel['type']}--{rel['to']}"
            citation = f"{binding['source_id']} · pdf p. {binding['page']}"
            url = "obsidian://learningos-atlas-evidence?" + urlencode({"relation": key, "ordinal": ordinal})
            nodes.append({
                "id": f"los-evidence-{key}--{ordinal}", "type": "text",
                "text": f"\"{binding['quote']}\"\n{citation}\n[Open evidence]({url})",
                "x": evidence_x, "y": evidence_index * STEP_Y,
                "width": CARD_W, "height": CARD_H,
            })
            evidence_index += 1
    for child in child_scopes:
        nodes.append({
            "id": f"los-scope-{child['kind']}--{child['id']}", "type": "file",
            "file": f"{TEMPLATE_PREFIX}/{child['kind']}/{child['id']}.canvas",
            "x": 0, "y": (len(nodes) + 1) * STEP_Y,
            "width": CARD_W, "height": CARD_H,
        })

    edges: list[dict[str, object]] = []
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
    edges.sort(key=lambda e: str(e["id"]))
    nodes.sort(key=lambda n: str(n["id"]))
    return {"nodes": nodes, "edges": edges}


def _relation_summary(cid: str, relations: list[RelationRow]) -> str:
    bits = []
    for rel in sorted(relations, key=lambda r: (r["from"], r["type"], r["to"])):
        if rel["from"] == cid:
            bits.append(f"{rel['type']} → {rel['to']}")
        if rel["to"] == cid:
            bits.append(f"← {rel['type']} from {rel['from']}")
    return " · ".join(bits)


def _concept_evidence_state(repo: Repo, cid: str, relations: list[RelationRow]) -> str:
    states = [relation_evidence_state(repo, r) for r in relations
              if cid in (r["from"], r["to"])]
    for state in ("disputed", "stale", "missing", "verified"):
        if state in states:
            return state
    return "missing"


def build_concept_card(repo: Repo, cid: str, practice_count: int = 0) -> str:
    from learning_os.derive.projection.common import md_header
    rec = repo.concepts[cid]
    lines = [line for line in md_header(f"Concept card — {rec.get('label', cid)}", "")
             if not line.startswith("> Generated:")]
    lines += [f"`{cid}`", ""]
    if rec.get("description"):
        lines += [rec["description"], ""]
    relations = [r for r in _active_relations(repo) if cid in (r["from"], r["to"])]
    summary = _relation_summary(cid, relations)
    if summary:
        lines += [summary, ""]
    notes = sorted((note for note in repo.notes.values()
                    if cid in (note.meta.get("concepts") or [])), key=lambda note: note.id)
    if notes:
        lines += ["Notes: " + ", ".join(note.id for note in notes), ""]
    sources = {sid for note in notes for sid in note.meta.get("sources") or []}
    sources.update(binding["source_id"] for binding in rec.get("description_evidence") or [])
    if sources:
        lines += ["Sources: " + ", ".join(sorted(sources)), ""]
    lines += [f"Evidence: {_concept_evidence_state(repo, cid, relations)}",
              f"Verified practice: {practice_count}", ""]
    return "\n".join(lines)


def build_atlas_boards(
    repo: Repo, indexes: Mapping[str, object],
) -> tuple[list[BoardCatalogEntry], dict[str, str]]:
    """(catalog, {generated-relative path: text}) for templates and cards."""
    module_to_concepts = cast(dict[str, list[str]], indexes.get("module_to_concepts", {}))
    unit_to_concepts = cast(dict[str, list[str]], indexes.get("unit_to_concepts", {}))
    practice_counts: Counter[str] = Counter()
    note_concepts: dict[str, set[str]] = {}
    by_note = checked_practice_by_note(repo)
    for note_id, items in by_note.items():
        for item in items:
            concepts = set(item.row["concept_ids"] if item.row is not None else [])
            practice_counts.update(concepts)
            note_concepts.setdefault(note_id, set()).update(concepts)
    scopes = scopes_for(repo, module_to_concepts, unit_to_concepts, note_concepts)
    by_parent: dict[tuple[str | None, str | None], list[BoardScope]] = {}
    for scope in scopes:
        if scope["parent_kind"]:
            by_parent.setdefault((scope["parent_kind"], scope["parent_id"]), []).append(scope)

    catalog: list[BoardCatalogEntry] = []
    files: dict[str, str] = {}
    for scope in scopes:
        children = by_parent.get((scope["kind"], scope["id"]), [])
        template = build_board_template(repo, scope, children, practice_counts)
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
        files[f"{CARD_PREFIX}/{cid}.md"] = build_concept_card(repo, cid, practice_counts[cid])
    catalog.sort(key=lambda e: (e["kind"], e["id"]))
    return catalog, files
