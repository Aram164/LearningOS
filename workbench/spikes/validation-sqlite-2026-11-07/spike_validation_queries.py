"""Query engine and diagnostic mapper for SQLite Reference-Validation Spike (Role A).

Executes parameterized anti-joins, route guard checks, and relation integrity
queries over the ephemeral in-memory database, mapping rows to Issue diagnostics.

All outputs strictly sorted by:
  (family_ordinal, source_ordinal, occurrence_ordinal, emission_rank)
to ensure byte-for-byte exact diagnostic parity against production Python.
"""

from __future__ import annotations

import sqlite3
from typing import NamedTuple

from learning_os.domain.validation import Issue


class DiagnosticRow(NamedTuple):
    family_ordinal: int
    source_ordinal: int
    occurrence_ordinal: int
    emission_rank: int
    severity: str
    code: str
    msg: str
    origin_path: str


def run_validation_queries(conn: sqlite3.Connection) -> list[Issue]:
    """Execute validation queries against conn and return strictly ordered Issues."""
    cur = conn.cursor()
    collected: list[DiagnosticRow] = []

    # 1. Route missing ID warnings (Family 1)
    cur.execute(
        """SELECT origin_path, source_id, unit_id, route_id, source_ordinal
           FROM rich_routes
           WHERE authored_id = 0
           ORDER BY source_ordinal"""
    )
    for origin_path, source_id, unit_id, route_id, s_ord in cur.fetchall():
        collected.append(DiagnosticRow(
            1, s_ord, 0, 0,
            "W", "ROUTE-ID-MISSING",
            f"source '{source_id}' route to '{unit_id}' has no persisted route id; v13 projects '{route_id}' until migration",
            origin_path,
        ))

    # 2. Duplicate Route IDs (Family 1)
    cur.execute(
        """SELECT route_id,
                  (
                      SELECT GROUP_CONCAT(module_id || '/' || unit_id || '/' || source_id, ', ')
                      FROM (
                          SELECT module_id, unit_id, source_id
                          FROM rich_routes r2
                          WHERE r2.route_id = r1.route_id
                          ORDER BY module_id, unit_id, source_id
                      )
                  ) AS owners
           FROM rich_routes r1
           GROUP BY route_id
           HAVING COUNT(*) >= 2
           ORDER BY route_id"""
    )
    for s_ord, (route_id, owners) in enumerate(cur.fetchall()):
        collected.append(DiagnosticRow(
            1, 1000 + s_ord, 0, 0,
            "E", "ROUTE-ID-DUPLICATE",
            f"route id '{route_id}' is owned by more than one rich route: {owners}",
            "curriculum/modules",
        ))

    # 3. Route Solution Exposures (Family 1)
    # Self-exposure
    cur.execute(
        """SELECT route_id, origin_path, source_ordinal, occurrence_ordinal
           FROM route_solution_exposures
           WHERE route_id = answered_id
           ORDER BY source_ordinal, occurrence_ordinal"""
    )
    for route_id, origin_path, s_ord, o_ord in cur.fetchall():
        collected.append(DiagnosticRow(
            1, 2000 + s_ord, o_ord, 1,
            "E", "ROUTE-SOLUTION-SELF",
            f"route '{route_id}' declares that it exposes its own solutions",
            origin_path,
        ))

    # Unknown answered route
    cur.execute(
        """SELECT s.route_id, s.answered_id, s.origin_path, s.source_ordinal, s.occurrence_ordinal
           FROM route_solution_exposures s
           LEFT JOIN (SELECT DISTINCT route_id FROM rich_routes) r ON s.answered_id = r.route_id
           WHERE r.route_id IS NULL
           ORDER BY s.source_ordinal, s.occurrence_ordinal"""
    )
    for route_id, answered_id, origin_path, s_ord, o_ord in cur.fetchall():
        collected.append(DiagnosticRow(
            1, 2000 + s_ord, o_ord, 2,
            "E", "ROUTE-SOLUTION-UNKNOWN",
            f"route '{route_id}' declares solutions for unknown route '{answered_id}'",
            origin_path,
        ))

    # 4. Route References & Guard Checks (Families 2, 6, 8)
    cur.execute(
        """SELECT
               rref.ref_kind,
               rref.caller_id,
               rref.route_id,
               rref.guard_unit_id,
               rref.guard_source_id,
               rref.guard_locator,
               rref.origin_path,
               rref.family_ordinal,
               rref.source_ordinal,
               rref.occurrence_ordinal,
               COALESCE(rc.match_count, 0) AS match_count,
               rr.unit_id AS actual_unit_id,
               rr.source_id AS actual_source_id,
               rr.locator AS actual_locator
           FROM route_references rref
           LEFT JOIN (
               SELECT route_id, COUNT(*) AS match_count
               FROM rich_routes
               GROUP BY route_id
           ) rc ON rref.route_id = rc.route_id
           LEFT JOIN rich_routes rr ON rref.route_id = rr.route_id
           ORDER BY rref.family_ordinal, rref.source_ordinal, rref.occurrence_ordinal"""
    )
    for (
        ref_kind, caller_id, route_id, guard_unit_id, guard_source_id,
        guard_locator, origin_path, fam_ord, s_ord, o_ord,
        match_count, actual_unit_id, actual_source_id, actual_locator
    ) in cur.fetchall():
        if ref_kind == "synthesis":
            if match_count != 1:
                collected.append(DiagnosticRow(
                    fam_ord, s_ord, o_ord, 0,
                    "E", "REF-ROUTE",
                    f"material synthesis '{caller_id}' route '{route_id}' resolves {match_count} rich routes",
                    origin_path,
                ))
            else:
                if actual_unit_id != guard_unit_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 1,
                        "E", "SYNTHESIS-ROUTE-OWNER",
                        f"material synthesis '{caller_id}' uses route '{route_id}' owned by '{actual_unit_id}'",
                        origin_path,
                    ))
                if guard_source_id is not None and actual_source_id != guard_source_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 2,
                        "E", "SYNTHESIS-SOURCE-GUARD",
                        f"material synthesis route '{route_id}' source guard does not match the current route",
                        origin_path,
                    ))
                if guard_locator is not None and actual_locator != guard_locator:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 3,
                        "E", "SYNTHESIS-LOCATOR-GUARD",
                        f"material synthesis route '{route_id}' locator guard does not match the current route",
                        origin_path,
                    ))
        elif ref_kind == "selection":
            # For selection: REF-SOURCE is rank 0. Route checks start at rank 1.
            if match_count == 0:
                collected.append(DiagnosticRow(
                    fam_ord, s_ord, o_ord, 1,
                    "E", "REF-ROUTE",
                    f"unit '{caller_id}' selects unknown route '{route_id}'",
                    origin_path,
                ))
            elif match_count == 1:
                if actual_unit_id != guard_unit_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 2,
                        "E", "SELECTION-ROUTE-OWNER",
                        f"unit '{caller_id}' selects route '{route_id}' owned by '{actual_unit_id}'",
                        origin_path,
                    ))
                if guard_source_id is not None and actual_source_id != guard_source_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 3,
                        "E", "SELECTION-SOURCE-GUARD",
                        f"selection route '{route_id}' belongs to source '{actual_source_id}', not '{guard_source_id}'",
                        origin_path,
                    ))
                if guard_locator is not None and actual_locator != guard_locator:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 4,
                        "E", "SELECTION-LOCATOR-GUARD",
                        f"selection route '{route_id}' locator no longer matches its stored guard",
                        origin_path,
                    ))
        elif ref_kind == "resource":
            # For study map resource: REF-SOURCE is rank 0. Route checks start at rank 1.
            if match_count == 0:
                collected.append(DiagnosticRow(
                    fam_ord, s_ord, o_ord, 1,
                    "E", "REF-ROUTE",
                    f"study map '{caller_id}' references unknown route '{route_id}'",
                    origin_path,
                ))
            elif match_count == 1:
                if actual_unit_id != guard_unit_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 2,
                        "E", "RESOURCE-ROUTE-OWNER",
                        f"study map '{caller_id}' resource route '{route_id}' belongs to '{actual_unit_id}'",
                        origin_path,
                    ))
                if guard_source_id and guard_source_id != actual_source_id:
                    collected.append(DiagnosticRow(
                        fam_ord, s_ord, o_ord, 3,
                        "E", "RESOURCE-SOURCE-GUARD",
                        f"study map '{caller_id}' resource route '{route_id}' belongs to source '{actual_source_id}', not '{guard_source_id}'",
                        origin_path,
                    ))

    # 4b. Synthesis Assessment Concepts (only evaluated when route resolves uniquely)
    cur.execute(
        """SELECT c.family_ordinal, c.source_ordinal, c.occurrence_ordinal, c.emission_rank,
                  c.concept_id, c.synthesis_id, c.origin_path
           FROM synthesis_assessment_concepts c
           JOIN (
               SELECT route_id, COUNT(*) AS match_count
               FROM rich_routes
               GROUP BY route_id
               HAVING match_count = 1
           ) rc ON c.route_id = rc.route_id
           LEFT JOIN entities e ON e.family = 'concept' AND e.id = c.concept_id
           WHERE e.id IS NULL"""
    )
    for fam_ord, s_ord, o_ord, rank, cid, synth_id, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, rank,
            "E", "REF-CONCEPT",
            f"material synthesis '{synth_id}' references unknown concept '{cid}'",
            origin_path,
        ))

    # 5. Legacy Selection resolution (Family 6)
    cur.execute(
        """SELECT ls.unit_id, ls.origin_path, ls.family_ordinal, ls.source_ordinal, ls.occurrence_ordinal,
                  COUNT(rr.route_id) AS match_count,
                  MIN(rr.route_id) AS matched_route_id
           FROM legacy_selections ls
           JOIN rich_routes rr
             ON rr.unit_id = ls.unit_id
            AND rr.source_id = ls.source_id
            AND (ls.locator IS NULL OR rr.locator = ls.locator)
           GROUP BY ls.unit_id, ls.source_id, ls.origin_path, ls.family_ordinal, ls.source_ordinal, ls.occurrence_ordinal
           HAVING match_count = 1"""
    )
    for uid, origin_path, fam_ord, s_ord, o_ord, match_count, matched_route_id in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, 5,
            "W", "SELECTION-ROUTE-ID-MISSING",
            f"unit '{uid}' has a readable pre-v13 source selection without route_id; exact route '{matched_route_id}' is available",
            origin_path,
        ))

    # 6. Direct Reference Edges (Unscoped anti-join)
    cur.execute(
        """SELECT e.severity, e.code, e.msg, e.origin_path,
                  e.family_ordinal, e.source_ordinal, e.occurrence_ordinal, e.emission_rank
           FROM reference_edges e
           LEFT JOIN entities t ON e.target_family = t.family AND e.target_id = t.id
           WHERE e.scope_kind IS NULL
             AND e.alt_target_family IS NULL
             AND t.id IS NULL"""
    )
    for sev, code, msg, origin_path, fam_ord, s_ord, o_ord, rank in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, rank, sev, code, msg, origin_path,
        ))

    # 7. Scoped Reference Edges
    cur.execute(
        """SELECT e.severity, e.code, e.msg, e.origin_path,
                  e.family_ordinal, e.source_ordinal, e.occurrence_ordinal, e.emission_rank
           FROM reference_edges e
           LEFT JOIN scoped_entities s
             ON e.scope_kind = s.scope_kind
            AND e.scope_id = s.scope_id
            AND e.target_family = s.target_family
            AND e.target_id = s.id
           WHERE e.scope_kind IS NOT NULL
             AND s.id IS NULL"""
    )
    for sev, code, msg, origin_path, fam_ord, s_ord, o_ord, rank in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, rank, sev, code, msg, origin_path,
        ))

    # 8. Dual Container / Alt-Target Reference Edges
    cur.execute(
        """SELECT e.severity, e.code, e.msg, e.origin_path,
                  e.family_ordinal, e.source_ordinal, e.occurrence_ordinal, e.emission_rank
           FROM reference_edges e
           LEFT JOIN entities t1 ON e.target_family = t1.family AND e.target_id = t1.id
           LEFT JOIN entities t2 ON e.alt_target_family = t2.family AND e.target_id = t2.id
           WHERE e.alt_target_family IS NOT NULL
             AND t1.id IS NULL
             AND t2.id IS NULL"""
    )
    for sev, code, msg, origin_path, fam_ord, s_ord, o_ord, rank in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, rank, sev, code, msg, origin_path,
        ))

    # 9. Source Child Titles (Family 12)
    cur.execute(
        """SELECT ct.origin_path, ct.source_id, ct.label,
                  ct.family_ordinal, ct.source_ordinal, ct.occurrence_ordinal
           FROM child_titles ct
           LEFT JOIN source_identifiers si
             ON ct.source_id = si.source_id AND ct.label = si.label
           WHERE si.label IS NULL"""
    )
    for origin_path, source_id, label, fam_ord, s_ord, o_ord in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, 0,
            "E", "REF-CHILD-TITLE",
            f"source '{source_id}' discovery.child_titles key '{label}' has no matching identifiers label",
            origin_path,
        ))

    # 10. Relations (Family 14)
    # 10a. 'from' endpoint
    cur.execute(
        """SELECT r.ordinal, r.from_id, r.origin_path
           FROM relations r
           LEFT JOIN entities e ON e.family = 'concept' AND e.id = r.from_id
           WHERE e.id IS NULL"""
    )
    for ord_val, from_id, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            14, ord_val, 0, 1,
            "E", "REL-ENDPOINT",
            f"relation[{ord_val}] 'from' does not resolve: '{from_id}'",
            origin_path,
        ))

    # 10b. 'to' endpoint
    cur.execute(
        """SELECT r.ordinal, r.to_id, r.origin_path
           FROM relations r
           LEFT JOIN entities e ON e.family = 'concept' AND e.id = r.to_id
           WHERE e.id IS NULL"""
    )
    for ord_val, to_id, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            14, ord_val, 0, 2,
            "E", "REL-ENDPOINT",
            f"relation[{ord_val}] 'to' does not resolve: '{to_id}'",
            origin_path,
        ))

    # 10c. Self endpoint
    cur.execute(
        """SELECT r.ordinal, r.from_id, r.origin_path
           FROM relations r
           WHERE r.from_id != '' AND r.from_id = r.to_id"""
    )
    for ord_val, from_id, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            14, ord_val, 0, 3,
            "E", "REL-SELF",
            f"relation[{ord_val}] endpoints are not distinct ('{from_id}')",
            origin_path,
        ))

    # 10d. Source reference
    cur.execute(
        """SELECT r.ordinal, r.source_id, r.origin_path
           FROM relations r
           LEFT JOIN entities en ON en.family = 'note' AND en.id = r.source_id
           LEFT JOIN entities es ON es.family = 'source' AND es.id = r.source_id
           WHERE r.source_id IS NOT NULL AND en.id IS NULL AND es.id IS NULL"""
    )
    for ord_val, source_id, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            14, ord_val, 0, 4,
            "E", "REL-SOURCE",
            f"relation[{ord_val}] cites unknown note/source '{source_id}'",
            origin_path,
        ))

    # 11. Structural Violations (ownership, working notes, etc.)
    cur.execute(
        """SELECT family_ordinal, source_ordinal, occurrence_ordinal, emission_rank,
                  severity, code, msg, origin_path
           FROM structural_violations"""
    )
    for fam_ord, s_ord, o_ord, rank, sev, code, msg, origin_path in cur.fetchall():
        collected.append(DiagnosticRow(
            fam_ord, s_ord, o_ord, rank, sev, code, msg, origin_path,
        ))

    # Strict multi-key deterministic sort
    collected.sort(key=lambda r: (r.family_ordinal, r.source_ordinal, r.occurrence_ordinal, r.emission_rank))

    return [
        Issue(row.severity, row.code, row.msg, row.origin_path)
        for row in collected
    ]
