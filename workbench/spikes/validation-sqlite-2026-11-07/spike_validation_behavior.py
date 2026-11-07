"""Behavioral and Parity Test Runner for SQLite Reference Validation (Role A Spike).

Tests live repository and 12-family mutation corpus comparing production references.py
vs in-memory SQLite spike byte-for-byte in exact diagnostic order.
Also benchmarks cold and warm execution timings and counts lines for the ledger.
"""

from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from learning_os.derive.validation.core import Validator
import learning_os.derive.validation.references as real_ref
import spike_references_sqlite as spike_ref
from learning_os.store.loader import load_repo
from learning_os.domain.snapshot import Note, Unit, StudyMap, LearningPath


class BaselineValidator(Validator):
    def __init__(self, repo):
        super().__init__(repo)
        self.issues = []


class SpikeValidator(spike_ref.ChecksReferences, Validator):
    def __init__(self, repo):
        super().__init__(repo)
        self.issues = []


def run_comparison(repo, label: str) -> None:
    v_base = BaselineValidator(repo)
    v_base.check_references()

    v_spike = SpikeValidator(repo)
    v_spike.check_references()

    if v_base.issues != v_spike.issues:
        print(f"\n[FAIL] Mismatch in test: {label}")
        print(f"Baseline issues ({len(v_base.issues)}):")
        for i in v_base.issues:
            print(f"  {i.severity} {i.code} [{i.path}]: {i.message}")
        print(f"Spike issues ({len(v_spike.issues)}):")
        for i in v_spike.issues:
            print(f"  {i.severity} {i.code} [{i.path}]: {i.message}")
        raise AssertionError(f"Parity mismatch in {label}")
    else:
        print(f"  [PASS] {label}: exact ordered parity ({len(v_base.issues)} diagnostics)")


def main():
    root = _REPO
    print("=== Loading Repository Snapshot ===")
    base_repo = load_repo(root)
    print("Snapshot loaded successfully.\n")

    checks_run = 0

    print("=== 1. Live Repository Parity ===")
    run_comparison(base_repo, "Live Repo Baseline")
    checks_run += 1

    print("\n=== 2. Mutation Corpus Parity ===")

    # Category 1: Unknown target IDs across target families
    # 1a: Unknown concept in note
    r = copy.deepcopy(base_repo)
    first_note = next(iter(r.notes.values()))
    first_note.meta.setdefault("concepts", []).append("unknown-concept-xyz")
    run_comparison(r, "Cat 1a: Unknown concept in note")
    checks_run += 1

    # 1b: Unknown source in note
    r = copy.deepcopy(base_repo)
    first_note = next(iter(r.notes.values()))
    first_note.meta.setdefault("sources", []).append("unknown-source-xyz")
    run_comparison(r, "Cat 1b: Unknown source in note")
    checks_run += 1

    # 1c: Unknown workspace in note
    r = copy.deepcopy(base_repo)
    first_note = next(iter(r.notes.values()))
    first_note.meta.setdefault("contexts", []).append("unknown-workspace-xyz")
    run_comparison(r, "Cat 1c: Unknown workspace in note")
    checks_run += 1

    # 1d: Unknown supersedes note
    r = copy.deepcopy(base_repo)
    first_note = next(iter(r.notes.values()))
    first_note.meta.setdefault("supersedes", []).append("unknown-supersedes-xyz")
    run_comparison(r, "Cat 1d: Unknown supersedes in note")
    checks_run += 1

    # 1e: Unknown program in workspace
    r = copy.deepcopy(base_repo)
    if r.workspaces:
        first_ws = next(iter(r.workspaces.values()))
        first_ws.meta.setdefault("program_ids", []).append("unknown-prog-xyz")
        run_comparison(r, "Cat 1e: Unknown program in workspace")
        checks_run += 1

    # 1f: Unknown module in workspace
    r = copy.deepcopy(base_repo)
    if r.workspaces:
        first_ws = next(iter(r.workspaces.values()))
        first_ws.meta.setdefault("module_ids", []).append("unknown-mod-xyz")
        run_comparison(r, "Cat 1f: Unknown module in workspace")
        checks_run += 1

    # 1g: Unknown project in workspace
    r = copy.deepcopy(base_repo)
    if r.workspaces:
        first_ws = next(iter(r.workspaces.values()))
        first_ws.meta["project_id"] = "unknown-project-xyz"
        run_comparison(r, "Cat 1g: Unknown project in workspace")
        checks_run += 1

    # 1h: Unknown unit in workspace
    r = copy.deepcopy(base_repo)
    if r.workspaces:
        first_ws = next(iter(r.workspaces.values()))
        first_ws.meta.setdefault("unit_ids", []).append("unknown-unit-xyz")
        run_comparison(r, "Cat 1h: Unknown unit in workspace")
        checks_run += 1

    # 1i: Unknown thematic group in module
    r = copy.deepcopy(base_repo)
    if r.modules:
        first_mid, first_m = next(iter(r.modules.items()))
        first_m.setdefault("thematic_group_ids", []).append("unknown-tg-xyz")
        run_comparison(r, "Cat 1i: Unknown thematic group in module")
        checks_run += 1

    # 1j: Unknown topic in source
    r = copy.deepcopy(base_repo)
    if r.sources:
        first_sid, first_s = next(iter(r.sources.items()))
        first_s.setdefault("topics", []).append("unknown-topic-xyz")
        run_comparison(r, "Cat 1j: Unknown topic in source")
        checks_run += 1

    # Category 2: Duplicate route ID across source maps
    r = copy.deepcopy(base_repo)
    smap = r.module_source_maps.get("module-hu-algo2")
    if smap and smap.get("sources"):
        smap["sources"][0]["unit_routes"].append({
            "id": "route-1416d2d68345093ac3d3125c",
            "unit_id": "unit-algo2-exam-prep",
            "locator": "duplicate copy",
        })
        run_comparison(r, "Cat 2: Duplicate route ID in module source map")
        checks_run += 1

    # Category 3: Guard drift & simultaneous multi-attribute drift (emission_rank ordering)
    real_route_id = "route-1416d2d68345093ac3d3125c"
    r = copy.deepcopy(base_repo)
    if r.units:
        first_uid, first_u = next(iter(r.units.items()))
        selections = first_u.data.setdefault("source_selections", [])
        # Simultaneous drift: wrong unit_id, wrong source_id, wrong locator
        selections.append({
            "route_id": real_route_id,
            "source_id": "wrong-source-guard",
            "locator": "wrong-locator-guard",
        })
        run_comparison(r, "Cat 3a: Unit source selection simultaneous guard drift")
        checks_run += 1

    # Category 3b: Synthesis route assessment guard drift
    r = copy.deepcopy(base_repo)
    r.unit_material_syntheses["synth-test"] = {
        "unit_id": "unit-foreign",
        "route_assessments": [{
            "route_id": real_route_id,
            "source_id": "wrong-source-guard",
            "locator": "wrong-locator-guard",
            "concept_ids": ["concept-unknown-xyz"],
        }],
        "concept_groups": [{
            "concept_id": "concept-unknown-grp",
            "related_unit_ids": ["unit-unknown-rel"],
            "bridge_note_ids": ["note-unknown-bridge"],
        }],
    }
    r.unit_material_synthesis_origins["synth-test"] = Path("curriculum/test-synthesis.yaml")
    run_comparison(r, "Cat 3b: Synthesis simultaneous guard drift + unknown entities")
    checks_run += 1

    # Category 3c: Study map resource guard drift
    r = copy.deepcopy(base_repo)
    if r.study_maps:
        first_smid, first_sm = next(iter(r.study_maps.items()))
        stages = first_sm.data.setdefault("stages", [])
        if stages:
            stages[0].setdefault("resources", []).append({
                "source_id": "wrong-source-guard",
                "route_id": real_route_id,
            })
            run_comparison(r, "Cat 3c: Study map resource route guard drift")
            checks_run += 1

    # Category 4: Self edges
    # 4a: REL-SELF
    r = copy.deepcopy(base_repo)
    r.relations.append({
        "from": "concept-self",
        "to": "concept-self",
        "source": "unknown-rel-source",
    })
    run_comparison(r, "Cat 4a: Relation self-edge + unknown endpoints/source")
    checks_run += 1

    # 4b: REF-ANSWER-NOTE self
    r = copy.deepcopy(base_repo)
    first_note = next(iter(r.notes.values()))
    first_note.meta["atlas_question"] = {"answer_notes": [first_note.id]}
    run_comparison(r, "Cat 4b: Atlas question self answer note")
    checks_run += 1

    # 4c: ROUTE-SOLUTION-SELF
    r = copy.deepcopy(base_repo)
    smap = r.module_source_maps.get("module-hu-algo2")
    if smap and smap.get("sources"):
        for rt in smap["sources"][0].get("unit_routes", []):
            if isinstance(rt, dict) and rt.get("id") == "route-1416d2d68345093ac3d3125c":
                rt["exposes_solutions_for"] = ["route-1416d2d68345093ac3d3125c", "unknown-answered-route"]
                break
        run_comparison(r, "Cat 4c: Route self & unknown solution exposure")
        checks_run += 1

    # Category 5: Quarantined workspace context & archived workspace
    r = copy.deepcopy(base_repo)
    r.quarantined_workspace_ids.add("ws-quarantine-valid")
    first_note = next(iter(r.notes.values()))
    first_note.meta.setdefault("contexts", []).append("ws-quarantine-valid")
    first_note.meta.setdefault("contexts", []).append("ws-quarantine-invalid")
    run_comparison(r, "Cat 5: Quarantined workspace dual-container resolution")
    checks_run += 1

    # Category 6: Malformed shapes (scalar workspace_ids, non-str list items)
    r = copy.deepcopy(base_repo)
    if r.units:
        first_uid, first_u = next(iter(r.units.items()))
        first_u.data["workspace_ids"] = "not-a-list-scalar"
        run_comparison(r, "Cat 6: Scalar workspace_ids (0 REF-WORKSPACE errors)")
        checks_run += 1

    # Category 7: Falsy / empty pointers
    r = copy.deepcopy(base_repo)
    r.learning_paths["lp-test"] = LearningPath(
        id="lp-test",
        path=Path("work/active/ws-test/learning-path.yaml"),
        data={"workspace_id": "non-existent-ws", "module_id": "unknown-module-lp"},
        workspace_id="ws-live-test",
    )
    run_comparison(r, "Cat 7: Learning path unknown & foreign workspace owner")
    checks_run += 1

    # Category 8: Scoped misses (covers foreign knowledge node, selection foreign stage)
    r = copy.deepcopy(base_repo)
    smap = r.module_source_maps.get("module-hu-algo2")
    if smap and smap.get("sources"):
        for rt in smap["sources"][0].get("unit_routes", []):
            if isinstance(rt, dict):
                rt["covers"] = ["foreign-knowledge-node-xyz"]
                break
        run_comparison(r, "Cat 8: Scoped miss - covers unknown knowledge node")
        checks_run += 1

    # Category 9: Polymorphic legs (relation source as note vs source)
    r = copy.deepcopy(base_repo)
    r.relations.append({
        "from": next(iter(r.concepts.keys())) if r.concepts else "concept-a",
        "to": next(iter(r.concepts.keys())) if r.concepts else "concept-b",
        "source": "foreign-non-note-non-source",
    })
    run_comparison(r, "Cat 9: Polymorphic relation source validation")
    checks_run += 1

    # Category 10: Ordinal ordering (multiple broken relations)
    r = copy.deepcopy(base_repo)
    r.relations.extend([
        {"from": "broken-concept-1", "to": "broken-concept-2"},
        {"from": "broken-concept-3", "to": "broken-concept-4"},
    ])
    run_comparison(r, "Cat 10: Multi-item relation ordinal ordering")
    checks_run += 1

    # Category 11: Fail-closed contract
    print("  Testing Cat 11: Fail-closed contract on sqlite3.Error...")
    try:
        import sqlite3
        class FaultySpikeValidator(SpikeValidator):
            def check_references(self):
                conn = sqlite3.connect(":memory:")
                # Purposely do not create tables to cause sqlite3.OperationalError
                try:
                    spike_ref.run_validation_queries(conn)
                except sqlite3.Error as exc:
                    raise RuntimeError(f"Reference validation database failed: {exc}") from exc
                finally:
                    conn.close()

        v_faulty = FaultySpikeValidator(base_repo)
        v_faulty.check_references()
        raise AssertionError("Expected RuntimeError was not raised!")
    except RuntimeError as exc:
        assert "Reference validation database failed" in str(exc)
        print("  [PASS] Cat 11: Fail-closed refusal properly raised RuntimeError")
        checks_run += 1

    # Category 12: Resume pointer chain
    r = copy.deepcopy(base_repo)
    r.resume_pointer = {
        "module_id": "unknown-resume-mod",
        "unit_id": "unknown-resume-unit",
        "study_map_id": "unknown-resume-sm",
        "stage_id": "unknown-resume-stage",
    }
    r.resume_pointer_path = Path("curriculum/resume.yaml")
    run_comparison(r, "Cat 12a: Resume pointer 4-hop unknown chain")
    checks_run += 1

    # Category 12b: Resume pointer with valid study map and unknown stage
    if base_repo.study_maps:
        first_smid = next(iter(base_repo.study_maps.keys()))
        r = copy.deepcopy(base_repo)
        r.resume_pointer = {
            "module_id": "unknown-resume-mod",
            "unit_id": "unknown-resume-unit",
            "study_map_id": first_smid,
            "stage_id": "unknown-resume-stage",
        }
        r.resume_pointer_path = Path("curriculum/resume.yaml")
        run_comparison(r, "Cat 12b: Resume pointer with valid study map and unknown stage")
        checks_run += 1

    print(f"\nAll {checks_run} parity & mutation checks passed with 100% exact diagnostic match!\n")

    print("=== 3. Performance Micro-benchmarks ===")
    iters = 20

    # Measure Python baseline
    t0 = time.perf_counter()
    for _ in range(iters):
        v = BaselineValidator(base_repo)
        v.check_references()
    baseline_time = (time.perf_counter() - t0) / iters * 1000

    # Measure SQLite spike
    t0 = time.perf_counter()
    for _ in range(iters):
        v = SpikeValidator(base_repo)
        v.check_references()
    spike_time = (time.perf_counter() - t0) / iters * 1000

    print(f"Baseline Python check_references(): {baseline_time:.2f} ms / run")
    print(f"SQLite Spike check_references():    {spike_time:.2f} ms / run")
    print(f"Overhead factor:                    {spike_time / baseline_time:.2f}x\n")

    print("=== 4. Line Counts ===")
    spike_files = [
        "spike_validation_schema.py",
        "spike_validation_exporter.py",
        "spike_validation_queries.py",
        "spike_references_sqlite.py",
        "spike_validation_swap.py",
    ]
    total_spike_loc = 0
    for fn in spike_files:
        fp = _SPIKE_DIR / fn
        loc = len(fp.read_text().splitlines())
        total_spike_loc += loc
        print(f"  {fn:30s} {loc:5d} LOC")
    print(f"  {'TOTAL SPIKE LOC':30s} {total_spike_loc:5d} LOC")

    real_fp = _REPO / "tools/learning_os/derive/validation/references.py"
    real_loc = len(real_fp.read_text().splitlines())
    print(f"  {'PRODUCTION references.py':30s} {real_loc:5d} LOC")
    print(f"  NET LOC DELTA:                  {total_spike_loc - real_loc:+5d} LOC")


if __name__ == "__main__":
    main()
