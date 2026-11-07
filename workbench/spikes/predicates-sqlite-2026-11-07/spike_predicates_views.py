"""SQL Views for relational semantic predicates (Task B.3).

Provides declarative, zero-procedural SQL views implementing the semantic
predicates over the catalog tables defined in `spike_predicates_schema.py`.
"""

from __future__ import annotations

import sqlite3
from typing import Final

DDL_VIEWS: Final[str] = """
-- 1. NeedsStudyMap (OPERATOR.md rule 6)
-- Derived obligation: unit owes a study map if its module is studied,
-- the unit is active/pending, and it has no study map yet.
CREATE VIEW IF NOT EXISTS v_needs_study_map AS
SELECT
    u.unit_id,
    u.module_id,
    u.status AS unit_status,
    m.status AS module_status,
    u.has_study_map,
    CASE
        WHEN u.has_study_map != 0 THEN 0
        WHEN m.status IS NULL OR m.status NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'studied_module_status') THEN 0
        WHEN u.status IS NOT NULL AND u.status IN (SELECT term FROM vocabulary_terms WHERE category = 'unit_status_without_obligation') THEN 0
        ELSE 1
    END AS needs_study_map
FROM units u
LEFT JOIN modules m ON u.module_id = m.module_id;


-- 2. NeedsScope (OPERATOR.md rule 6, module level)
-- Studied academic module with an owned record and zero units owes initial units.
CREATE VIEW IF NOT EXISTS v_needs_scope AS
SELECT
    m.module_id,
    m.kind AS module_kind,
    m.status AS module_status,
    m.is_owned,
    m.unit_count,
    CASE
        WHEN m.is_owned = 0 THEN 0
        WHEN m.kind IS NULL OR m.kind NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'academic_module_kind') THEN 0
        WHEN m.status IS NULL OR m.status NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'studied_module_status') THEN 0
        WHEN m.unit_count <= 0 THEN 1
        ELSE 0
    END AS needs_scope
FROM modules m;


-- 3. ClaimStale (operations/transactions/revisions.yaml)
-- A claim is stale if judged under a different contract version or any
-- read artifact's revision differs from the live revision or is absent.
CREATE VIEW IF NOT EXISTS v_claims_stale AS
SELECT
    c.claim_id,
    c.read_contract_version,
    c.statement_kind,
    CASE
        WHEN c.read_contract_version != (SELECT int_val FROM semantic_constants WHERE key = 'contract_version') THEN 1
        WHEN EXISTS (
            SELECT 1
            FROM claim_reads cr
            LEFT JOIN live_revisions lr ON cr.artifact = lr.artifact
            WHERE cr.claim_id = c.claim_id
              AND (lr.artifact IS NULL OR lr.revision != cr.revision)
        ) THEN 1
        ELSE 0
    END AS is_stale
FROM claims c;


-- 4. SourceComplete (OPERATOR.md rule 14)
-- Every source is selected/ref-only with working locator, or deferred with a non-blank reason.
CREATE VIEW IF NOT EXISTS v_sources_complete AS
SELECT
    s.source_id,
    s.selection_state,
    s.locator_ok,
    s.deferral_reason,
    CASE
        WHEN s.selection_state IN (SELECT term FROM vocabulary_terms WHERE category = 'selected_source_state')
            THEN CASE WHEN s.locator_ok != 0 THEN 1 ELSE 0 END
        WHEN s.selection_state = 'deferred'
            THEN CASE WHEN length(trim(COALESCE(s.deferral_reason, ''))) > 0 THEN 1 ELSE 0 END
        ELSE 0
    END AS is_complete
FROM sources s;


-- 5. AttemptConsistent (OPERATOR.md rule 5)
-- Every attempt must name a real sitting of its owning module.
CREATE VIEW IF NOT EXISTS v_module_attempts_consistent AS
SELECT
    a.module_id,
    a.termin,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM module_sittings s
            WHERE s.module_id = a.module_id
              AND s.termin = a.termin
        ) THEN 1
        ELSE 0
    END AS is_consistent
FROM module_attempts a;


-- 6. StudyMapGrounded (OPERATOR.md unit workflow)
-- A unit's study map is grounded if every planned resource appears in the complete menu.
CREATE VIEW IF NOT EXISTS v_study_map_grounded AS
SELECT
    u.unit_id,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM study_map_resources r
            LEFT JOIN study_map_menu m
              ON r.unit_id = m.unit_id
             AND r.source_id = m.source_id
             AND r.locator = m.locator
            WHERE r.unit_id = u.unit_id
              AND m.locator IS NULL
        ) THEN 0
        ELSE 1
    END AS is_grounded
FROM units u;


-- 7. RouteEvaluated (system/schema/module-source-map.schema.json)
CREATE VIEW IF NOT EXISTS v_routes_evaluated AS
SELECT
    r.route_id,
    r.unit_id,
    r.source_id,
    r.scope,
    CASE
        WHEN r.scope IN (SELECT term FROM vocabulary_terms WHERE category = 'route_scope')
         AND r.scope != 'unevaluated' THEN 1
        ELSE 0
    END AS is_evaluated
FROM routes r;
"""


def init_views(conn: sqlite3.Connection) -> None:
    """Create all relational semantic views."""
    conn.executescript(DDL_VIEWS)
