"""Schema definitions for relational semantic predicates (Task B.3).

Defines SQLite tables for:
1. Catalog entities (modules, units, sources, routes, study maps, sittings, attempts)
2. Derived claims and revision lineage (claims, claim_reads, live_revisions)
3. Governance & vocabulary lookup tables (fact_owners, vocabulary_terms)
"""

from __future__ import annotations

import sqlite3
from typing import Final

DDL_CATALOG: Final[str] = """
-- Core curriculum entities
CREATE TABLE IF NOT EXISTS modules (
    module_id TEXT PRIMARY KEY,
    kind TEXT,
    status TEXT,
    is_owned INTEGER NOT NULL DEFAULT 0,
    owner_path TEXT,
    unit_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS units (
    unit_id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    status TEXT,
    has_study_map INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
);

CREATE TABLE IF NOT EXISTS module_sittings (
    module_id TEXT NOT NULL,
    termin INTEGER NOT NULL,
    PRIMARY KEY (module_id, termin),
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
);

CREATE TABLE IF NOT EXISTS module_attempts (
    module_id TEXT NOT NULL,
    termin INTEGER NOT NULL,
    PRIMARY KEY (module_id, termin),
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
);

-- Learning sources and routes
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    selection_state TEXT,
    locator_ok INTEGER NOT NULL DEFAULT 0,
    deferral_reason TEXT
);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    locator TEXT NOT NULL,
    scope TEXT,
    FOREIGN KEY (unit_id) REFERENCES units(unit_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

-- Study map grounding (menu vs planned resources)
CREATE TABLE IF NOT EXISTS study_map_menu (
    unit_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    locator TEXT NOT NULL,
    PRIMARY KEY (unit_id, source_id, locator),
    FOREIGN KEY (unit_id) REFERENCES units(unit_id)
);

CREATE TABLE IF NOT EXISTS study_map_resources (
    unit_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    locator TEXT NOT NULL,
    PRIMARY KEY (unit_id, source_id, locator),
    FOREIGN KEY (unit_id) REFERENCES units(unit_id)
);

-- Claims, reads and live revisions
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    read_contract_version INTEGER NOT NULL,
    statement_kind TEXT
);

CREATE TABLE IF NOT EXISTS claim_reads (
    claim_id TEXT NOT NULL,
    artifact TEXT NOT NULL,
    revision INTEGER NOT NULL,
    PRIMARY KEY (claim_id, artifact),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);

CREATE TABLE IF NOT EXISTS live_revisions (
    artifact TEXT PRIMARY KEY,
    revision INTEGER NOT NULL
);

-- Fact ownership mappings (OPERATOR.md boundaries 4-5)
CREATE TABLE IF NOT EXISTS fact_owners (
    fact_kind TEXT PRIMARY KEY,
    template TEXT NOT NULL,
    req_module INTEGER NOT NULL DEFAULT 0,
    req_unit INTEGER NOT NULL DEFAULT 0,
    req_workspace INTEGER NOT NULL DEFAULT 0,
    req_note INTEGER NOT NULL DEFAULT 0,
    req_program INTEGER NOT NULL DEFAULT 0,
    req_source INTEGER NOT NULL DEFAULT 0
);

-- Closed vocabulary lookup tables
CREATE TABLE IF NOT EXISTS vocabulary_terms (
    category TEXT NOT NULL,
    term TEXT NOT NULL,
    PRIMARY KEY (category, term)
);

-- Static configuration
CREATE TABLE IF NOT EXISTS semantic_constants (
    key TEXT PRIMARY KEY,
    int_val INTEGER,
    str_val TEXT
);
"""

# Initial seed data for fact_owners and vocabularies
FACT_OWNER_ROWS = (
    ("exam_date", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("exam_sitting", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("exam_attempt", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("registration_window", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("module_status", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("module_role", "curriculum/modules/{module_id}/module.yaml", 1, 0, 0, 0, 0, 0),
    ("workspace_status", "work/active/{workspace_id}/CONTEXT.md", 0, 0, 1, 0, 0, 0),
    ("coordination_decision", "work/COORDINATION.md", 0, 0, 0, 0, 0, 0),
    ("priority", "work/COORDINATION.md", 0, 0, 0, 0, 0, 0),
    ("deferral", "work/COORDINATION.md", 0, 0, 0, 0, 0, 0),
    ("study_map_order", "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml", 1, 1, 0, 0, 0, 0),
    ("stage_status", "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml", 1, 1, 0, 0, 0, 0),
    ("stage_source_feedback", "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml", 1, 1, 0, 0, 0, 0),
    ("source_selection", "curriculum/modules/{module_id}/units/{unit_id}/unit.yaml", 1, 1, 0, 0, 0, 0),
    ("concept_definition", "knowledge/notes/{note_id}.md", 0, 0, 0, 1, 0, 0),
    ("note_body", "knowledge/notes/{note_id}.md", 0, 0, 0, 1, 0, 0),
    ("concept_relation", "knowledge/concept-relations.yaml", 0, 0, 0, 0, 0, 0),
    ("source_record", "sources/registry/ ({source_id})", 0, 0, 0, 0, 0, 1),
    ("material_identity", "sources/registry/ ({source_id})", 0, 0, 0, 0, 0, 1),
    ("program_status", "curriculum/programs/{program_id}.yaml", 0, 0, 0, 0, 1, 0),
    ("transaction_receipt", "operations/transactions/", 0, 0, 0, 0, 0, 0),
)

VOCABULARY_SEEDS = {
    "studied_module_status": ("active", "enrolled"),
    "unit_status_without_obligation": ("complete", "archived", "paused", "ready-to-shelve"),
    "academic_module_kind": ("academic",),
    "route_scope": ("current", "prerequisite", "complementary", "optional", "prior-year", "out-of-scope", "unevaluated"),
    "evidence_type": ("derivation", "explanation", "implementation", "exercise", "exam", "external"),
    "mastery_declaring_kind": ("mastered", "mastery", "complete", "task-complete", "exam-passed"),
    "non_mastery_kind": ("open", "resolved", "evidence", "progress", "question"),
    "review_required_change": ("semantic-rewrite", "identity-change", "deletion", "inferred-relation", "pedagogical-judgment"),
    "review_free_change": ("typo", "formatting", "evidence-append", "measurement", "link-fix"),
    "canonical_write_channel": ("module.plan.import", "unit.map.import", "route.patch", "migration"),
    "workspace_coordination_kind": ("program_ids", "module_ids", "unit_ids"),
    "workspace_ownership_kind": ("unit_order", "module_status", "study_map", "note_body", "source_evaluation"),
    "selected_source_state": ("selected", "reference-only"),
    "judgment_only": ("authorization", "scope-choice", "conflict-resolution", "pedagogical-stance", "mastery-assessment"),
}


def init_schema(conn: sqlite3.Connection) -> None:
    """Apply DDL and populate static seed tables."""
    conn.executescript(DDL_CATALOG)
    with conn:
        conn.executemany(
            """INSERT OR REPLACE INTO fact_owners
               (fact_kind, template, req_module, req_unit, req_workspace, req_note, req_program, req_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            FACT_OWNER_ROWS,
        )
        vocab_rows = [
            (category, term)
            for category, terms in VOCABULARY_SEEDS.items()
            for term in terms
        ]
        conn.executemany(
            "INSERT OR REPLACE INTO vocabulary_terms (category, term) VALUES (?, ?)",
            vocab_rows,
        )
        conn.execute(
            "INSERT OR REPLACE INTO semantic_constants (key, int_val) VALUES ('contract_version', 3)"
        )
