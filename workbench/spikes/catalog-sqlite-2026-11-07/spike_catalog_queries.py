"""Porcelain read queries evaluated across Python YAML walk vs SQLite Catalog (Task C.2).

Implements 5 high-frequency porcelain read operations under both models:
1. Student Roadmap Assembly: all units and study map progress for a target module.
2. Blocked Study Maps: study maps where unit is blocked or map is paused.
3. Exam-Critical Stages: all exam-critical stages across a module's units.
4. Concept Coverage: which modules, units, and stages teach a specific concept.
5. Sources by Thematic Group: sources filtered by thematic group membership.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from learning_os.domain.snapshot import Repo


# ---------------------------------------------------------------------------
# 1. Student Roadmap Assembly
# ---------------------------------------------------------------------------

def py_student_roadmap(repo: Repo, module_id: str) -> list[dict[str, Any]]:
    """Python YAML walk: assemble roadmap for a module."""
    # Find module
    mod = repo.modules.get(module_id)
    if not mod:
        return []
    units = [u for u in repo.units.values() if u.module_id == module_id]
    units.sort(key=lambda u: getattr(u, "data", u).get("order", 0))

    roadmap = []
    for u in units:
        data = getattr(u, "data", u)
        # Find study map for unit
        sm = next((s for s in repo.study_maps.values() if getattr(s, "data", s).get("unit_id") == u.id), None)
        sm_data = getattr(sm, "data", sm) if sm else {}
        roadmap.append({
            "unit_id": u.id,
            "title": data.get("title", u.id),
            "status": data.get("status", ""),
            "order": data.get("order", 0),
            "study_map_id": sm_data.get("id"),
            "study_map_status": sm_data.get("status"),
            "current_stage": sm_data.get("current_stage"),
        })
    return roadmap


def sql_student_roadmap(con: sqlite3.Connection, module_id: str) -> list[dict[str, Any]]:
    """SQLite single-query: assemble roadmap for a module."""
    cur = con.execute(
        """
        SELECT u.id, u.title, u.status, u.order_num, sm.id, sm.status, sm.current_stage
        FROM units u
        LEFT JOIN study_maps sm ON sm.unit_id = u.id
        WHERE u.module_id = ?
        ORDER BY u.order_num
        """,
        (module_id,),
    )
    return [
        {
            "unit_id": r[0],
            "title": r[1],
            "status": r[2],
            "order": r[3],
            "study_map_id": r[4],
            "study_map_status": r[5],
            "current_stage": r[6],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 2. Blocked Study Maps
# ---------------------------------------------------------------------------

def py_blocked_study_maps(repo: Repo) -> list[dict[str, Any]]:
    """Python YAML walk: find paused study maps or study maps with blocked units."""
    results = []
    for sm_id, sm in repo.study_maps.items():
        data = getattr(sm, "data", sm)
        unit = repo.units.get(data.get("unit_id", ""))
        u_data = getattr(unit, "data", unit) if unit else {}
        unit_status = u_data.get("status", "")
        sm_status = data.get("status", "")
        if sm_status == "paused" or unit_status == "blocked":
            results.append({
                "study_map_id": sm_id,
                "unit_id": data.get("unit_id"),
                "status": sm_status,
                "unit_title": u_data.get("title", ""),
                "unit_status": unit_status,
            })
    results.sort(key=lambda r: r["study_map_id"])
    return results


def sql_blocked_study_maps(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """SQLite single-query: find paused study maps or study maps with blocked units."""
    cur = con.execute(
        """
        SELECT sm.id, sm.unit_id, sm.status, u.title, u.status
        FROM study_maps sm
        JOIN units u ON u.id = sm.unit_id
        WHERE sm.status = 'paused' OR u.status = 'blocked'
        ORDER BY sm.id
        """
    )
    return [
        {
            "study_map_id": r[0],
            "unit_id": r[1],
            "status": r[2],
            "unit_title": r[3],
            "unit_status": r[4],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 3. Exam-Critical Stages for a Module
# ---------------------------------------------------------------------------

def py_exam_critical_stages(repo: Repo, module_id: str) -> list[dict[str, Any]]:
    """Python YAML walk: find all exam-critical stages across a module."""
    units = [u for u in repo.units.values() if u.module_id == module_id]
    units.sort(key=lambda u: getattr(u, "data", u).get("order", 0))

    results = []
    for u in units:
        sm = next((s for s in repo.study_maps.values() if getattr(s, "data", s).get("unit_id") == u.id), None)
        if not sm:
            continue
        sm_data = getattr(sm, "data", sm)
        for st in sm_data.get("stages", []):
            if st.get("exam_critical"):
                results.append({
                    "stage_id": st.get("id"),
                    "number": st.get("number"),
                    "title": st.get("title"),
                    "estimate_minutes": st.get("estimate_minutes", 0),
                    "unit_id": u.id,
                })
    return results


def sql_exam_critical_stages(con: sqlite3.Connection, module_id: str) -> list[dict[str, Any]]:
    """SQLite single-query: find all exam-critical stages across a module."""
    cur = con.execute(
        """
        SELECT st.id, st.number, st.title, st.estimate_minutes, u.id
        FROM study_map_stages st
        JOIN study_maps sm ON sm.id = st.study_map_id
        JOIN units u ON u.id = sm.unit_id
        WHERE u.module_id = ? AND st.exam_critical = 1
        ORDER BY u.order_num, st.number
        """,
        (module_id,),
    )
    return [
        {
            "stage_id": r[0],
            "number": r[1],
            "title": r[2],
            "estimate_minutes": r[3],
            "unit_id": r[4],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 4. Concept Coverage
# ---------------------------------------------------------------------------

def py_concept_coverage(repo: Repo, concept_id: str) -> list[dict[str, Any]]:
    """Python YAML walk: locate which units and stages teach a concept."""
    results = []
    for sm in repo.study_maps.values():
        data = getattr(sm, "data", sm)
        unit = repo.units.get(data.get("unit_id", ""))
        module_id = getattr(unit, "module_id", "") if unit else ""
        for st in data.get("stages", []):
            if concept_id in st.get("concepts", []):
                results.append({
                    "module_id": module_id,
                    "unit_id": data.get("unit_id"),
                    "stage_id": st.get("id"),
                    "stage_title": st.get("title"),
                })
    results.sort(key=lambda r: (r["module_id"], r["unit_id"], r["stage_id"]))
    return results


def sql_concept_coverage(con: sqlite3.Connection, concept_id: str) -> list[dict[str, Any]]:
    """SQLite single-query: locate which units and stages teach a concept."""
    cur = con.execute(
        """
        SELECT DISTINCT u.module_id, u.id, st.id, st.title
        FROM stage_concepts sc
        JOIN study_map_stages st ON st.id = sc.stage_id
        JOIN study_maps sm ON sm.id = st.study_map_id
        JOIN units u ON u.id = sm.unit_id
        WHERE sc.concept_id = ?
        ORDER BY u.module_id, u.id, st.id
        """,
        (concept_id,),
    )
    return [
        {
            "module_id": r[0],
            "unit_id": r[1],
            "stage_id": r[2],
            "stage_title": r[3],
        }
        for r in cur.fetchall()
    ]


# ---------------------------------------------------------------------------
# 5. Sources by Thematic Group
# ---------------------------------------------------------------------------

def py_sources_by_thematic_group(repo: Repo, group_id: str) -> list[dict[str, Any]]:
    """Python YAML walk: sources filtered by thematic group."""
    results = []
    for src_id, src in repo.sources.items():
        data = getattr(src, "data", src)
        groups = data.get("thematic_group_ids", [])
        if group_id in groups:
            results.append({
                "id": src_id,
                "title": data.get("title", src_id),
                "type": data.get("type", ""),
                "status": data.get("status", ""),
            })
    results.sort(key=lambda r: r["title"])
    return results


def sql_sources_by_thematic_group(con: sqlite3.Connection, group_id: str) -> list[dict[str, Any]]:
    """SQLite single-query: sources filtered by thematic group."""
    pattern = f'%"{group_id}"%'
    cur = con.execute(
        """
        SELECT id, title, type, status
        FROM sources
        WHERE thematic_group_ids LIKE ?
        ORDER BY title
        """,
        (pattern,),
    )
    return [
        {
            "id": r[0],
            "title": r[1],
            "type": r[2],
            "status": r[3],
        }
        for r in cur.fetchall()
    ]
