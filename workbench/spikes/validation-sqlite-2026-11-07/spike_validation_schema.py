"""Schema definition for the SQLite Reference-Validation Spike (Role A).

In-memory SQLite schema for validating reference integrity across curriculum,
knowledge, and workspace models. Declared per relational-delegation-pilot §4.

Rules:
- No FOREIGN KEY or UNIQUE constraints on target IDs (duplicates and broken
  references must survive as inspectable rows; checks report completely).
- BINARY collation for all TEXT columns (exact codepoint match, matching Python ==).
- Ordinal columns (family_ordinal, source_ordinal, occurrence_ordinal, emission_rank)
  preserve exact deterministic diagnostic emission order.
"""

from __future__ import annotations

import sqlite3

SCHEMA_DDL = """
-- Target entities for un-scoped reference resolution
CREATE TABLE entities (
    family TEXT NOT NULL COLLATE BINARY,
    id     TEXT NOT NULL COLLATE BINARY,
    PRIMARY KEY (family, id)
);

-- Scoped target entities (e.g. module components, unit knowledge nodes, study map stages)
CREATE TABLE scoped_entities (
    scope_kind    TEXT NOT NULL COLLATE BINARY,
    scope_id      TEXT NOT NULL COLLATE BINARY,
    target_family TEXT NOT NULL COLLATE BINARY,
    id            TEXT NOT NULL COLLATE BINARY,
    PRIMARY KEY (scope_kind, scope_id, target_family, id)
);

-- Rich routes extracted across module source maps
CREATE TABLE rich_routes (
    route_id       TEXT NOT NULL COLLATE BINARY,
    module_id      TEXT NOT NULL COLLATE BINARY,
    unit_id        TEXT NOT NULL COLLATE BINARY,
    source_id      TEXT NOT NULL COLLATE BINARY,
    locator        TEXT COLLATE BINARY,
    authored_id    INTEGER NOT NULL,
    source_ordinal INTEGER NOT NULL,
    origin_path    TEXT NOT NULL COLLATE BINARY
);
CREATE INDEX idx_rich_routes_id ON rich_routes (route_id);

-- Exposes solutions for declarations on rich routes
CREATE TABLE route_solution_exposures (
    route_id           TEXT NOT NULL COLLATE BINARY,
    answered_id        TEXT NOT NULL COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL
);

-- Synthesis assessment concept references (evaluated only when route resolves uniquely)
CREATE TABLE synthesis_assessment_concepts (
    synthesis_id       TEXT NOT NULL COLLATE BINARY,
    route_id           TEXT NOT NULL COLLATE BINARY,
    concept_id         TEXT NOT NULL COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL,
    emission_rank      INTEGER NOT NULL
);

-- Route references from syntheses, selections, and study map resources
CREATE TABLE route_references (
    ref_kind           TEXT NOT NULL COLLATE BINARY, -- 'synthesis', 'selection', 'resource'
    caller_id          TEXT NOT NULL COLLATE BINARY,
    route_id           TEXT NOT NULL COLLATE BINARY,
    guard_unit_id      TEXT NOT NULL COLLATE BINARY,
    guard_source_id    TEXT COLLATE BINARY,
    guard_locator      TEXT COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL
);
CREATE INDEX idx_route_refs_id ON route_references (route_id);

-- Legacy route selections without route_id
CREATE TABLE legacy_selections (
    unit_id            TEXT NOT NULL COLLATE BINARY,
    source_id          TEXT NOT NULL COLLATE BINARY,
    locator            TEXT COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL
);

-- General reference edges (membership checks)
CREATE TABLE reference_edges (
    edge_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL,
    emission_rank      INTEGER NOT NULL,
    source_family      TEXT NOT NULL COLLATE BINARY,
    source_id          TEXT NOT NULL COLLATE BINARY,
    target_family      TEXT NOT NULL COLLATE BINARY,
    target_id          TEXT NOT NULL COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    scope_kind         TEXT COLLATE BINARY,
    scope_id           TEXT COLLATE BINARY,
    alt_target_family  TEXT COLLATE BINARY,
    severity           TEXT NOT NULL COLLATE BINARY, -- 'E' or 'W'
    code               TEXT NOT NULL COLLATE BINARY,
    msg                TEXT NOT NULL COLLATE BINARY
);
CREATE INDEX idx_ref_edges_target ON reference_edges (target_family, target_id);
CREATE INDEX idx_ref_edges_order ON reference_edges (family_ordinal, source_ordinal, occurrence_ordinal, emission_rank);

-- Concept relations (from, to, source)
CREATE TABLE relations (
    ordinal     INTEGER NOT NULL,
    from_id     TEXT NOT NULL COLLATE BINARY,
    to_id       TEXT NOT NULL COLLATE BINARY,
    source_id   TEXT COLLATE BINARY,
    origin_path TEXT NOT NULL COLLATE BINARY
);

-- Source child title labels vs identifiers labels
CREATE TABLE child_titles (
    source_id          TEXT NOT NULL COLLATE BINARY,
    label              TEXT NOT NULL COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL
);

CREATE TABLE source_identifiers (
    source_id TEXT NOT NULL COLLATE BINARY,
    label     TEXT NOT NULL COLLATE BINARY,
    PRIMARY KEY (source_id, label)
);

-- Direct structural / ownership violations recorded during extraction
CREATE TABLE structural_violations (
    violation_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    family_ordinal     INTEGER NOT NULL,
    source_ordinal     INTEGER NOT NULL,
    occurrence_ordinal INTEGER NOT NULL,
    emission_rank      INTEGER NOT NULL,
    severity           TEXT NOT NULL COLLATE BINARY, -- 'E' or 'W'
    code               TEXT NOT NULL COLLATE BINARY,
    msg                TEXT NOT NULL COLLATE BINARY,
    origin_path        TEXT NOT NULL COLLATE BINARY
);
"""


def init_validation_db(conn: sqlite3.Connection) -> None:
    """Initialize schema on an ephemeral in-memory SQLite connection."""
    conn.executescript(SCHEMA_DDL)
