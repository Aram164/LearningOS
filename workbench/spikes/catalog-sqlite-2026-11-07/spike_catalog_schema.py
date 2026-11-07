"""Relational schema for the persistent derived catalog sidecar (Task C.2).

Compiles programs, modules, units, study maps, stages, sources, and concepts into
indexed relational tables. Enables instant zero-parse read queries for student
roadmaps, blocked study maps, and concept coverage.
"""

from __future__ import annotations

import sqlite3

CATALOG_SCHEMA_DDL = """
-- Programs
CREATE TABLE IF NOT EXISTS programs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT,
    status TEXT,
    raw_json TEXT NOT NULL
);

-- Modules
CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT,
    status TEXT,
    area_id TEXT,
    thematic_group_ids TEXT,
    unit_order TEXT,
    raw_json TEXT NOT NULL
);

-- Units
CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL REFERENCES modules(id),
    title TEXT NOT NULL,
    kind TEXT,
    status TEXT NOT NULL,
    order_num INTEGER,
    scope TEXT,
    raw_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_units_module_id ON units(module_id);
CREATE INDEX IF NOT EXISTS idx_units_status ON units(status);

-- Study Maps
CREATE TABLE IF NOT EXISTS study_maps (
    id TEXT PRIMARY KEY,
    unit_id TEXT REFERENCES units(id),
    status TEXT NOT NULL,
    current_stage TEXT,
    stage_count INTEGER NOT NULL DEFAULT 0,
    exam_critical_stages INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_study_maps_unit_id ON study_maps(unit_id);
CREATE INDEX IF NOT EXISTS idx_study_maps_status ON study_maps(status);

-- Study Map Stages
CREATE TABLE IF NOT EXISTS study_map_stages (
    id TEXT PRIMARY KEY,
    study_map_id TEXT NOT NULL REFERENCES study_maps(id),
    number INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    estimate_minutes INTEGER DEFAULT 0,
    exam_critical INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_stages_map_id ON study_map_stages(study_map_id);
CREATE INDEX IF NOT EXISTS idx_stages_status ON study_map_stages(status);

-- Sources
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT,
    status TEXT,
    thematic_group_ids TEXT,
    raw_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(type);

-- Concepts
CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT,
    raw_json TEXT NOT NULL
);

-- Stage to Concept References
CREATE TABLE IF NOT EXISTS stage_concepts (
    stage_id TEXT NOT NULL REFERENCES study_map_stages(id),
    concept_id TEXT NOT NULL REFERENCES concepts(id),
    PRIMARY KEY (stage_id, concept_id)
);
CREATE INDEX IF NOT EXISTS idx_stage_concepts_concept ON stage_concepts(concept_id);
"""


def init_catalog_db(db_path: str = ":memory:") -> sqlite3.Connection:
    """Initialize an SQLite connection with the catalog schema and optimal read pragmas."""
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.executescript(CATALOG_SCHEMA_DDL)
    return con
