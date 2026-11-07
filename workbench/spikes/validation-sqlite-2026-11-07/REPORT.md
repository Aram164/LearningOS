# SPIKE REPORT — Reference-Validation Structural Families as SQL (Role A)

**Date:** 2026-11-07  
**Branch:** `research/relational-delegation-2026-11-06`  
**Location:** `workbench/spikes/validation-sqlite-2026-11-07/`  
**Status:** COMPLETE — Stopped for Review  

---

## 1. Executive Summary & Verdict

### Final Verdict: NO-GO for SQL Delegation of Reference Validation (Role A)

The experimental prototype of in-memory SQLite reference validation (Arm c / Task B.1) is fully built, 100% green, and verified to byte-exact, ordered diagnostic parity against both the live production repository and the comprehensive 12-category mutation corpus.

However, the empirical evidence overwhelmingly confirms the prediction of Deliverable 2 (§4–§5):
* **Bespoke Codebase Expansion:** **+1,003 LOC net (+149% increase)**, growing from 672 lines in production `references.py` to **1,675 lines** across the SQL spike modules.
* **Severe Performance Degradation:** **3.34× slowdown** in isolated validation micro-benchmarks (19.50 ms → 65.09 ms per run) and **4.42× slowdown** across the test suite (17.84s → 78.87s for 98 oracle tests).
* **Negative Architectural Score:** Relational engine capabilities (durability, WAL concurrency, indices, transaction isolation) are entirely wasted on ephemeral in-memory validation sessions, while imposing a third redundant layer of data modeling (JSON schema + Python dataclass + SQLite DDL + SQL queries).

Recommendation: **Do not adopt SQL delegation for reference validation.** Retain Python validation with table-driven or helper-unified refactoring (e.g. the proven route-guard unification from Slice 0).

---

## 2. Deliverables & Implementation Inventory

All code is strictly isolated in `workbench/spikes/validation-sqlite-2026-11-07/`. Production files under `tools/` remain pristine and untouched.

| File | Purpose | Lines (LOC) |
|---|---|---|
| `spike_validation_schema.py` | Schema DDL for entities, scoped entities, rich routes, reference edges, and violations. | 159 |
| `spike_validation_exporter.py` | Snapshot walker extracting targets, guards, and ordinals from `Repo` into SQLite. | 952 |
| `spike_validation_queries.py` | Parameterized SQL anti-joins, route guard checks, and diagnostic mapper with multi-key sort. | 411 |
| `spike_references_sqlite.py` | Drop-in `ChecksReferences` mixin replacement; enforces fail-closed refusal on `sqlite3.Error`. | 123 |
| `spike_validation_swap.py` | Pytest plugin for transparent in-process swap via `-p spike_validation_swap`. | 30 |
| `spike_validation_behavior.py` | Empirical parity harness covering live repo + 12 mutation families + benchmarks. | 395 |
| **TOTAL SPIKE ARTIFACTS** | | **2,070** |
| **Implementation Core (excl. tests/swap)** | | **1,675** |
| **Production `references.py` Baseline** | | **672** |
| **Net LOC Delta** | | **+1,003 LOC (+149%)** |

---

## 3. The Measured Six-Dimension Complexity Ledger

Measured against production `references.py` (`60da966` baseline):

| Dimension | (a) Production Baseline | (c) In-Memory SQLite Spike | Delta / Finding |
|---|---|---|---|
| **1. Bespoke Implementation** | **672 LOC** | **1,675 LOC** | **+1,003 LOC (+149%)**. Exporter loop, DDL declarations, and query mapping dwarf the code they replace. |
| **2. Duplicated Responsibility** | 12 sites; guard invariant ×4; stage membership ×2 | Same guard/stage unifications achieved, **BUT** record shapes are now declared a 3rd time (JSON Schema + Python Domain + SQLite DDL). | **Negative**. SQL adds schema redundancy without removing Python models. |
| **3. Change Propagation** | Touch 3–4 places to add a reference field | Touch **5 places**: JSON schema, domain model, DDL in `schema.py`, extraction in `exporter.py`, query mapping in `queries.py`. | **Negative**. Every domain field addition requires sync across Python and SQL. |
| **4. Failure Modes Owned** | Pure Python exceptions (type errors, key errors). | **New failure classes**: SQLite DDL syntax errors, type binding mismatches, connection exhaustion, engine refusal paths. | **Negative**. Requires fail-closed wrappers to ensure DB errors never convert to fake issues. |
| **5. Verification Burden** | 98 oracle scenario tests. | 98 oracle tests **+ 27 mutation & parity test cases** in `spike_validation_behavior.py`. | **Increased**. Ephemeral DB requires verifying collation, bag deduplication, and ordinal ordering. |
| **6. Operational Overhead** | **19.50 ms** / run | **65.09 ms** / run (**3.34× slower**) | **Negative**. 78.87s vs 17.84s test suite wall-clock overhead. In-memory DB creation dominates run. |

---

## 4. Parity & Mutation Verification Matrix

Full suite verification executed via:
```bash
# 1. Behavior and Mutation Parity Runner
PYTHONPATH="tools:workbench/spikes/validation-sqlite-2026-11-07" \
    .venv/bin/python workbench/spikes/validation-sqlite-2026-11-07/spike_validation_behavior.py

# 2. Pytest Oracle Suites with Swapped Module
PYTHONPATH="tools:workbench/spikes/validation-sqlite-2026-11-07" \
    .venv/bin/pytest -p spike_validation_swap \
    tests/test_manifest_routes.py tests/test_validation.py \
    tests/test_route_identity_migration.py tests/test_scenarios.py -q
```

### Mutation Corpus Results (27/27 PASSED, 100% Exact Diagnostic Parity)

1. **Category 1 (Unknown Target IDs across 11 families):**
   * 1a (Concept in note): `REF-CONCEPT` — PASS (exact match)
   * 1b (Source in note): `REF-SOURCE` — PASS (exact match)
   * 1c (Workspace in note): `REF-WORKSPACE` — PASS (exact match)
   * 1d (Supersedes note): `REF-SUPERSEDES` — PASS (exact match)
   * 1e (Program in workspace): `REF-PROGRAM` — PASS (exact match)
   * 1f (Module in workspace): `REF-MODULE` — PASS (exact match)
   * 1g (Project in workspace): `REF-PROJECT` — PASS (exact match)
   * 1h (Unit in workspace): `REF-UNIT` — PASS (exact match)
   * 1i (Thematic group in module): `REF-THEMATIC-GROUP` — PASS (exact match)
   * 1j (Topic in source): `REF-TOPIC` — PASS (exact match)
2. **Category 2 (Duplicate Route IDs):**
   * Duplicate authored route ID across source maps: `ROUTE-ID-DUPLICATE` — PASS (exact match, bag semantics preserved).
3. **Category 3 (Route Guard Drift & Simultaneous Drift):**
   * 3a (Unit source selection simultaneous unit + source + locator drift): Evaluated in exact order `(REF-SOURCE, SELECTION-ROUTE-OWNER, SELECTION-SOURCE-GUARD, SELECTION-LOCATOR-GUARD)` — PASS.
   * 3b (Synthesis simultaneous guard drift + unknown entities): Evaluated in exact order `(REF-UNIT, SYNTHESIS-ROUTE-OWNER, SYNTHESIS-SOURCE-GUARD, SYNTHESIS-LOCATOR-GUARD, REF-CONCEPT, REF-CONCEPT, REF-UNIT, REF-NOTE)` — PASS.
   * 3c (Study map resource route guard drift): `(RESOURCE-ROUTE-OWNER, RESOURCE-SOURCE-GUARD)` — PASS.
4. **Category 4 (Self Edges):**
   * 4a (Relation self-edge `REL-SELF` + endpoints + source): PASS.
   * 4b (Atlas question self-answer note `REF-ANSWER-NOTE`): PASS.
   * 4c (Route solution exposure `ROUTE-SOLUTION-SELF` and `ROUTE-SOLUTION-UNKNOWN`): PASS.
5. **Category 5 (Quarantined Workspaces & Dual-Container Resolution):**
   * Quarantined workspace accepted for note context; unlisted workspace rejected (`REF-WORKSPACE`): PASS.
6. **Category 6 (Malformed Shapes & Schema Discipline):**
   * Scalar `workspace_ids`: produces **0 `REF-WORKSPACE` diagnostics** (schema layer owns shape errors upstream): PASS.
7. **Category 7 (Falsy & Empty Pointers):**
   * Learning path foreign workspace: `REF-WORKSPACE` skips `PATH-OWNER` (matching Python `elif` short-circuit): PASS.
8. **Category 8 (Scoped Misses):**
   * Module source map `covers` referencing foreign knowledge node (`REF-KNOWLEDGE`): PASS.
9. **Category 9 (Polymorphic Legs):**
   * Relation source referencing non-note / non-source (`REL-SOURCE`): PASS.
10. **Category 10 (Multi-Item Ordinal Ordering):**
    * Multiple broken relation endpoints maintain exact input sequence: PASS.
11. **Category 11 (Fail-Closed Contract):**
    * Simulated `sqlite3.Error` causes immediate `RuntimeError` refusal; zero false diagnostics emitted: PASS.
12. **Category 12 (Resume Pointer Chain):**
    * 12a (4-hop unknown chain with missing study map): `REF-MODULE`, `REF-UNIT`, `REF-STUDY-MAP` (skips `REF-STAGE`): PASS.
    * 12b (Valid study map with unknown stage): `REF-STAGE`: PASS.

### Pytest Oracle Results
* **98 passed in 78.87s** across `test_manifest_routes.py`, `test_validation.py`, `test_route_identity_migration.py`, and `test_scenarios.py`.
* Zero regressions, zero assertions broken.

---

## 5. Architectural Findings on Role A Ephemeral SQL

1. **Why Role A SQL Loses to Python:**
   A relational database engine's advantages stem from **durability**, **concurrency control**, and **persistent index acceleration**. When SQLite is instantiated `:memory:` for a single read-only pass and discarded immediately after:
   * **Ingestion Penalty:** 100% of the repository's entities and edges must be serialized and inserted into SQLite tables via SQL string queries before any check can execute.
   * **No Reuse:** The database schema and indexes are discarded after each run, forcing cold initialization overhead on every invocation.
   * **Code Duplication:** Defining SQLite DDL tables creates a redundant third copy of schema definitions that already exist in `system/schema/*.json` and `tools/learning_os/domain/snapshot.py`.

2. **The Mandatory `emission_rank` Discovery:**
   Relational queries output sets; they have no natural concept of authored line-by-line `if / elif / else` sequence. To preserve byte-for-byte diagnostic order in simultaneous guard failures (e.g. when unit_id, source_id, and locator fail concurrently), every row required an explicit 4-key tuple:
   $$\text{ORDER BY } (\text{family\_ordinal}, \text{source\_ordinal}, \text{occurrence\_ordinal}, \text{emission\_rank})$$
   Encoding these ranks added ~60 lines of artificial ordering logic to the queries and exporter.

3. **Conclusion:**
   Task B.1 provides empirical confirmation that relational delegation is an anti-pattern for Ephemeral Validation (Role A). The technical decision is unambiguous: **NO-GO**.
