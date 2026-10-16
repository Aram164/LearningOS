"""The Module × Concept projection: which modules touch a concept, and how we know.

The domain atlas answers "what is in this domain". It cannot answer the
question a learner carrying four modules at once actually has — *this concept
appears in three of them; are they the same thing?* — because nothing publishes
the crossing.

This module publishes it, as edges rather than as a rendered table, so an
interface can pivot it either way and a reader can always ask why a cell is
filled.

EVIDENCE, AND WHY IT IS THE WHOLE POINT
---------------------------------------
An edge exists only where something explicit says so. Two sources, both
authored, both reviewable:

  ``stage-concept``   a stage's ``concepts`` tag. Carries unit, study-map and
                      stage identity, so the cell drills into the exact stage.
  ``knowledge-node``  a knowledge-map node's ``concept_ids``, which the unit
                      schema defines as *reviewed* links to canonical concepts.
                      Carries unit and node identity.

Nothing else. A concept is never inferred from a title, a note body, a source
evaluation, a shared word, or a similarity score. A wrong edge here is worse
than a missing one: it would tell a learner two modules share ground they do
not, and the cost lands as wasted study time rather than as a failing test.
``absence means not mapped, never that no relationship exists`` — the unit
schema's phrasing for ``concept_ids`` — governs this projection too.

A NOTE ON THE STATE THIS FOUND
-------------------------------
Measured 2026-08-28 while building this: 376 of 416 stages carry concept tags,
covering 124 distinct concepts, while **zero** knowledge-map nodes carry
``concept_ids``. The pre-existing ``unit_to_concepts`` and ``concept_to_units``
indexes read only the node source, so both had been publishing ``{}`` since
they shipped. ``indexes.py`` now reads the same explicit union as this module,
which is what makes those two keys non-empty for the first time.
"""

from __future__ import annotations

from typing import Any

#: Evidence kinds, in the order they sort. Extending this list is a manifest
#: contract change, never an implementation detail.
STAGE_CONCEPT = "stage-concept"
KNOWLEDGE_NODE = "knowledge-node"


def _stage_evidence(stages: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """(module_id, concept_id) -> stage evidence rows, from explicit tags only."""
    found: dict[tuple[str, str], list[dict]] = {}
    for stage in stages:
        module_id = stage.get("module_id")
        unit_id = stage.get("unit_id")
        study_map_id = stage.get("study_map_id")
        stage_id = stage.get("id")
        if not (module_id and unit_id and study_map_id and stage_id):
            continue
        for concept_id in stage.get("concepts") or ():
            if not isinstance(concept_id, str) or not concept_id:
                continue
            found.setdefault((module_id, concept_id), []).append({
                "kind": STAGE_CONCEPT,
                "unit_id": unit_id,
                "study_map_id": study_map_id,
                "stage_id": stage_id,
            })
    return found


def _node_evidence(units: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """(module_id, concept_id) -> knowledge-node evidence rows."""
    found: dict[tuple[str, str], list[dict]] = {}
    for unit in units:
        module_id = unit.get("module_id")
        unit_id = unit.get("id")
        if not (module_id and unit_id):
            continue
        for node in (unit.get("knowledge_map") or {}).get("nodes") or ():
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            if not node_id:
                continue
            for concept_id in node.get("concept_ids") or ():
                if not isinstance(concept_id, str) or not concept_id:
                    continue
                found.setdefault((module_id, concept_id), []).append({
                    "kind": KNOWLEDGE_NODE,
                    "unit_id": unit_id,
                    "node_id": node_id,
                })
    return found


def _sort_key(evidence: dict) -> tuple:
    return (
        evidence["kind"],
        evidence.get("unit_id", ""),
        evidence.get("study_map_id", ""),
        evidence.get("stage_id", "") or evidence.get("node_id", ""),
    )


def build_module_concept_edges(
    *,
    modules: list[dict],
    units: list[dict],
    stages: list[dict],
    concepts: dict[str, Any],
) -> list[dict]:
    """Deterministic ``{module_id, concept_id, evidence}`` rows.

    ``concepts`` is the canonical registry. An edge naming a concept that is not
    in it is dropped rather than published: the projection must not invent a
    concept identity, and a dangling reference is already an error the validator
    reports against the authored record. The same holds for a module id that no
    projected module carries.

    Ordering is total and derived only from ids, so two builds of the same
    repository produce byte-identical output.
    """
    known_modules = {module["id"] for module in modules if module.get("id")}
    known_concepts = set(concepts or ())

    merged: dict[tuple[str, str], list[dict]] = {}
    for source in (_stage_evidence(stages), _node_evidence(units)):
        for key, rows in source.items():
            merged.setdefault(key, []).extend(rows)

    edges: list[dict] = []
    for (module_id, concept_id), rows in merged.items():
        if module_id not in known_modules or concept_id not in known_concepts:
            continue
        deduped = {tuple(sorted(row.items())): row for row in rows}
        edges.append({
            "module_id": module_id,
            "concept_id": concept_id,
            "evidence": sorted(deduped.values(), key=_sort_key),
        })
    edges.sort(key=lambda edge: (edge["module_id"], edge["concept_id"]))
    return edges


def cross_module_concepts(edges: list[dict]) -> list[str]:
    """Concepts carried by more than one module — the Atlas's default view."""
    by_concept: dict[str, set[str]] = {}
    for edge in edges:
        by_concept.setdefault(edge["concept_id"], set()).add(edge["module_id"])
    return sorted(cid for cid, mids in by_concept.items() if len(mids) > 1)
