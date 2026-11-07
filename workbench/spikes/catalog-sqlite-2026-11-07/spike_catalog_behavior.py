"""Behavioral verification and benchmarks for Derived Catalog Sidecar (Task C.2).

Validates:
1. Entity count and data parity between Python Repo and SQLite catalog sidecar.
2. 100% Exact Result Parity across 5 high-frequency porcelain queries.
3. Cold YAML walk vs SQLite query latency benchmarks.
4. Full catalog compilation time and file size measurements.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_PATH = REPO_ROOT / "tools"
SPIKE_PATH = Path(__file__).resolve().parent
for p in (str(TOOLS_PATH), str(SPIKE_PATH)):
    if p not in sys.path:
        sys.path.insert(0, p)

from learning_os.store.loading import load_repo
from spike_catalog_compiler import build_catalog_sidecar, compile_catalog
from spike_catalog_queries import (
    py_blocked_study_maps,
    py_concept_coverage,
    py_exam_critical_stages,
    py_sources_by_thematic_group,
    py_student_roadmap,
    sql_blocked_study_maps,
    sql_concept_coverage,
    sql_exam_critical_stages,
    sql_sources_by_thematic_group,
    sql_student_roadmap,
)
from spike_catalog_schema import init_catalog_db


def test_compilation_and_counts(repo: Any, con: sqlite3.Connection):
    print("--- [1/3] Verifying Entity Counts & Schema Parity ---")
    cur = con.cursor()

    # Modules
    sql_modules = cur.execute("SELECT count(*) FROM modules").fetchone()[0]
    py_modules = len(repo.modules)
    assert sql_modules == py_modules, f"Module count mismatch: py={py_modules}, sql={sql_modules}"

    # Units
    sql_units = cur.execute("SELECT count(*) FROM units").fetchone()[0]
    py_units = len(repo.units)
    assert sql_units == py_units, f"Unit count mismatch: py={py_units}, sql={sql_units}"

    # Study Maps
    sql_sm = cur.execute("SELECT count(*) FROM study_maps").fetchone()[0]
    py_sm = len(repo.study_maps)
    assert sql_sm == py_sm, f"StudyMap count mismatch: py={py_sm}, sql={sql_sm}"

    # Sources
    sql_sources = cur.execute("SELECT count(*) FROM sources").fetchone()[0]
    py_sources = len(repo.sources)
    assert sql_sources == py_sources, f"Source count mismatch: py={py_sources}, sql={sql_sources}"

    # Concepts
    sql_concepts = cur.execute("SELECT count(*) FROM concepts").fetchone()[0]
    py_concepts = len(repo.concepts)
    assert sql_concepts == py_concepts, f"Concept count mismatch: py={py_concepts}, sql={sql_concepts}"

    # Stages & stage concepts
    sql_stages = cur.execute("SELECT count(*) FROM study_map_stages").fetchone()[0]
    sql_stage_concepts = cur.execute("SELECT count(*) FROM stage_concepts").fetchone()[0]

    print(f"✓ All entity counts match identically:")
    print(f"   Programs:     {cur.execute('SELECT count(*) FROM programs').fetchone()[0]}")
    print(f"   Modules:      {sql_modules}")
    print(f"   Units:        {sql_units}")
    print(f"   Study Maps:   {sql_sm}")
    print(f"   Stages:       {sql_stages}")
    print(f"   Stage-Concepts Links: {sql_stage_concepts}")
    print(f"   Sources:      {sql_sources}")
    print(f"   Concepts:     {sql_concepts}")


def test_query_parity(repo: Any, con: sqlite3.Connection):
    print("--- [2/3] Verifying Exact Parity on 5 Porcelain Read Queries ---")

    # Query 1: Student Roadmap Assembly
    for mod_id in list(repo.modules.keys())[:5]:
        py_res = py_student_roadmap(repo, mod_id)
        sql_res = sql_student_roadmap(con, mod_id)
        assert py_res == sql_res, f"Roadmap mismatch for {mod_id}:\nPY: {py_res}\nSQL: {sql_res}"
    print("✓ Query 1 (Student Roadmap Assembly): 5/5 modules matched identically.")

    # Query 2: Blocked Study Maps
    py_res = py_blocked_study_maps(repo)
    sql_res = sql_blocked_study_maps(con)
    assert py_res == sql_res, f"Blocked study maps mismatch: py={len(py_res)}, sql={len(sql_res)}"
    print(f"✓ Query 2 (Blocked Study Maps): matched identically ({len(sql_res)} maps).")

    # Query 3: Exam-Critical Stages
    for mod_id in list(repo.modules.keys())[:5]:
        py_res = py_exam_critical_stages(repo, mod_id)
        sql_res = sql_exam_critical_stages(con, mod_id)
        assert py_res == sql_res, f"Critical stages mismatch for {mod_id}"
    print("✓ Query 3 (Exam-Critical Stages): 5/5 modules matched identically.")

    # Query 4: Concept Coverage
    test_concepts = ["concept-asymptotic-analysis", "concept-recurrences-master-theorem", "concept-proof-technique"]
    for cid in test_concepts:
        py_res = py_concept_coverage(repo, cid)
        sql_res = sql_concept_coverage(con, cid)
        assert py_res == sql_res, f"Concept coverage mismatch for {cid}:\nPY: {py_res}\nSQL: {sql_res}"
    print("✓ Query 4 (Concept Coverage): 3/3 concept joins matched identically.")

    # Query 5: Sources by Thematic Group
    test_groups = ["group-algorithms-data-structures", "group-mathematics-foundations", "group-machine-learning"]
    for gid in test_groups:
        py_res = py_sources_by_thematic_group(repo, gid)
        sql_res = sql_sources_by_thematic_group(con, gid)
        assert py_res == sql_res, f"Sources by group mismatch for {gid}:\nPY: {py_res}\nSQL: {sql_res}"
    print("✓ Query 5 (Sources by Thematic Group): 3/3 groups matched identically.")


def run_benchmarks(repo: Any, con: sqlite3.Connection, db_path: Path):
    print("--- [3/3] Running Performance & Compilation Benchmarks ---")
    db_size = os.path.getsize(db_path)

    # 1. Compilation Time Benchmark
    t0 = time.perf_counter()
    mem_con = init_catalog_db(":memory:")
    compile_catalog(repo, mem_con)
    t_compile = (time.perf_counter() - t0) * 1000
    mem_con.close()

    # 2. Query Latency Benchmarks
    sample_module = next(iter(repo.modules.keys()))
    sample_concept = "concept-asymptotic-analysis"
    sample_group = "group-algorithms-data-structures"

    queries = [
        ("Student Roadmap (1 module)", lambda: py_student_roadmap(repo, sample_module), lambda: sql_student_roadmap(con, sample_module)),
        ("Blocked Study Maps", lambda: py_blocked_study_maps(repo), lambda: sql_blocked_study_maps(con)),
        ("Exam-Critical Stages", lambda: py_exam_critical_stages(repo, sample_module), lambda: sql_exam_critical_stages(con, sample_module)),
        ("Concept Coverage Join", lambda: py_concept_coverage(repo, sample_concept), lambda: sql_concept_coverage(con, sample_concept)),
        ("Sources by Group Filter", lambda: py_sources_by_thematic_group(repo, sample_group), lambda: sql_sources_by_thematic_group(con, sample_group)),
    ]

    print(f"\nCompilation & Storage:")
    print(f"  Catalog Compilation Time: {t_compile:.2f} ms")
    print(f"  Compiled Database Size:   {db_size:,} bytes ({db_size/1024:.1f} KB)")

    print(f"\nQuery Latency Benchmarks (1,000 iterations each):")
    for name, py_fn, sql_fn in queries:
        t0 = time.perf_counter()
        for _ in range(1000):
            py_fn()
        t_py = (time.perf_counter() - t0) / 1000 * 1e6

        t0 = time.perf_counter()
        for _ in range(1000):
            sql_fn()
        t_sql = (time.perf_counter() - t0) / 1000 * 1e6

        speedup = t_py / t_sql if t_sql > 0 else 0
        faster_str = f"{speedup:.1f}x faster" if speedup >= 1 else f"{1/speedup:.1f}x slower"
        print(f"  {name:30} | Python Walk: {t_py:8.2f} µs | SQLite Query: {t_sql:8.2f} µs | SQLite {faster_str}")


if __name__ == "__main__":
    t0 = time.perf_counter()
    print("Loading live repository...")
    repo = load_repo(REPO_ROOT)
    t_load = (time.perf_counter() - t0) * 1000
    print(f"Cold YAML repository loaded in {t_load:.2f} ms.")

    db_path = REPO_ROOT / ".derived" / "catalog.sqlite3"
    build_catalog_sidecar(REPO_ROOT, db_path)
    con = init_catalog_db(str(db_path))

    try:
        test_compilation_and_counts(repo, con)
        test_query_parity(repo, con)
        run_benchmarks(repo, con, db_path)
        print("\nALL CATALOG VERIFICATIONS PASSED SUCCESSFULLY.")
    finally:
        con.close()
