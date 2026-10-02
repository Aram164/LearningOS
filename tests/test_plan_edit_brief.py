"""Brief preparation form: what the next command needs, nothing else.

`plan-edit-context --brief` projects identities, guards, id inventories,
the audit's missing-evidence lists, reusable analysis references, required
follow-up inputs, applicable preflight checks, and explicit expandable
commands. Full route bodies, the study map, and analysis prose stay behind
the expand references — every listed expansion must run as printed.
"""

from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path

import yaml
from repo_builders import add_curriculum, run_los, write_yaml

ANALYSIS_BODY = """# Density intuition

The density chapter explains probability mass spreading over intervals.
A worked example integrates the uniform density step by step.
"""


def _plant_note(root: Path, note_id: str, body: str, binding: dict):
    meta = {"id": note_id, "type": "note", "role": "reference",
            "title": "Planted analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "unreviewed",
            "material_analysis": binding}
    path = root / "knowledge/notes/mathematics" / f"{note_id}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))


def _seed_material(root: Path, name: str, data: bytes) -> str:
    target = root.parent / "materials" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _seed_unit(root: Path):
    from learning_os.material_synthesis import current_unit_material_basis

    add_curriculum(root)
    digest = _seed_material(root, "source-demo-book/deck.pdf", b"%PDF brief\n")
    _plant_note(root, "note-brief-density", ANALYSIS_BODY, {
        "resolution": "resolved",
        "material": "source-demo-book/deck.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": digest,
        "live_source_digest": digest,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(ANALYSIS_BODY.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(ANALYSIS_BODY.encode("utf-8")),
    })
    map_path = root / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"] = [{
        "id": "route-demo-density", "unit_id": "unit-demo-l01",
        "title": "Density", "locator": "deck.pdf, pp. 1-3",
        "depth": "core", "scope": "current",
    }]
    write_yaml(map_path, source_map)
    unit_dir = root / "curriculum/modules/module-demo/units/unit-demo-l01"
    write_yaml(unit_dir / "material-synthesis.yaml", {
        "schema_version": 1, "id": "material-synthesis-demo-l01",
        "type": "unit-material-synthesis", "unit_id": "unit-demo-l01",
        "status": "approved",
        "basis": current_unit_material_basis(root, "unit-demo-l01"),
        "route_assessments": [{
            "route_id": "route-demo-density",
            "source_id": "source-demo-book",
            "locator": "deck.pdf, pp. 1-3",
            "review_status": "deep-reviewed",
            "concept_ids": ["concept-expected-value"],
            "contribution": "Derives density intuition from first principles.",
            "best_for": "A worked example of uniform density integration.",
        }],
    })


def _brief(root: Path, *args: str) -> dict:
    proc = run_los(root, "plan-edit-context", "unit-demo-l01", "--brief", *args)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


def test_brief_refuses_stale_snapshot_with_conflict_code(mini_repo):
    _seed_unit(mini_repo)
    snapshot = _brief(mini_repo)["snapshot_id"]
    note = next((mini_repo / "knowledge/notes/mathematics").glob("*.md"))
    note.write_text(note.read_text(encoding="utf-8") + "\nA changed explanation.\n",
                    encoding="utf-8")
    # plan-edit-context guards outside any _refusal try block: the stale
    # token still reaches exit 3 through the top-level handler.
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--brief",
                   "--expected-snapshot", snapshot)
    assert proc.returncode == 3, proc.stderr
    assert not proc.stdout


def test_brief_carries_preparation_without_bodies(mini_repo):
    _seed_unit(mini_repo)
    payload = _brief(mini_repo)
    assert payload["contract"] == "plan-edit-context-brief"
    assert payload["unit_id"] == "unit-demo-l01"
    assert payload["module_id"] == "module-demo"
    for key in ("study_map", "routes", "source_selections"):
        assert key not in payload, key
    for key in ("artifact_revisions", "inventory", "unit_audit",
                "analysis_refs", "required_inputs", "preflight", "expand"):
        assert key in payload, key
    assert payload["inventory"]["route_ids"] == ["route-demo-density"]
    assert payload["inventory"]["stage_ids"] == ["stage-demo"]
    # Exact missing evidence: the route is current-scope but placed nowhere.
    assert payload["unit_audit"]["current_or_prerequisite_unplaced"] == [
        "route-demo-density"]
    refs = payload["analysis_refs"]["analysis_notes"]
    assert [ref["note_id"] for ref in refs] == ["note-brief-density"]
    assert refs[0]["freshness"] == "current"
    assert refs[0]["review"] == "unreviewed"
    assert payload["analysis_refs"]["approved_assessment_routes"] == [
        "route-demo-density"]
    assert payload["analysis_refs"]["stale_assessment_routes"] == []
    assert ANALYSIS_BODY.splitlines()[2] not in json.dumps(payload)
    assert sorted(payload["artifact_revisions"]) == [
        "module-demo", "study-map-demo-l01", "unit-demo-l01"]
    assert payload["required_inputs"]["route_patch"]["changes"]["fields"]
    assert {row["operation"] for row in payload["preflight"]} == {
        "route-patch", "unit-plan-revise", "unit-map-import",
        "module-plan-import", "verify"}


def test_brief_expand_commands_run_as_printed(mini_repo):
    _seed_unit(mini_repo)
    payload = _brief(mini_repo)
    expand = payload["expand"]
    commands = [expand["full"], expand["full_audit"],
                *expand["route_batches"], *expand["stages"].values()]
    snapshot = payload["snapshot_id"]
    assert expand["route_batches"] == [
        f"plan-edit-context unit-demo-l01 --route-ids route-demo-density "
        f"--expected-snapshot {snapshot}"]
    for command in commands:
        assert not command.startswith("los ")
        assert f"--expected-snapshot {snapshot}" in command
        proc = run_los(mini_repo, *shlex.split(command))
        assert proc.returncode == 0, f"{command}: {proc.stderr}"
    search = expand["analysis_search"].replace("QUERY", "density")
    assert not search.startswith("los ")
    proc = run_los(mini_repo, *shlex.split(search))
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["items"]
    hint = payload["analysis_refs"]["related_expand"]
    assert not hint.startswith("los ")
    proc = run_los(mini_repo, *shlex.split(hint))
    assert proc.returncode == 0, proc.stderr


def test_brief_splits_stale_assessment_routes(mini_repo):
    _seed_unit(mini_repo)
    assert _brief(mini_repo)["analysis_refs"]["approved_assessment_routes"] == [
        "route-demo-density"]
    map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["locator"] = "deck.pdf, pp. 4-6"
    write_yaml(map_path, source_map)
    refs = _brief(mini_repo)["analysis_refs"]
    assert refs["approved_assessment_routes"] == []
    assert refs["stale_assessment_routes"] == ["route-demo-density"]


def test_brief_lists_direct_refs_with_related_count_and_hint(mini_repo):
    _seed_unit(mini_repo)
    body = "Density from an unrouted file.\n"
    _plant_note(mini_repo, "note-brief-related", body, {
        "resolution": "resolved",
        "material": "source-demo-book/other.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": "ee" * 32,
        "live_source_digest": "ee" * 32,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(body.encode("utf-8")),
    })
    refs = _brief(mini_repo)["analysis_refs"]
    assert [ref["note_id"] for ref in refs["analysis_notes"]] == [
        "note-brief-density"]
    assert refs["analysis_notes"][0]["scope"] == "direct"
    assert refs["related_count"] == 1
    assert refs["related_expand"].startswith(
        "plan-edit-context unit-demo-l01 --brief --include-related "
        "--expected-snapshot sha256:")
    assert "related_notes" not in refs
    widened = _brief(mini_repo, "--include-related")["analysis_refs"]
    assert [ref["note_id"] for ref in widened["related_notes"]] == [
        "note-brief-related"]
    assert widened["related_notes"][0]["scope"] == "related"


def test_brief_include_related_is_refused_without_brief(mini_repo):
    _seed_unit(mini_repo)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--route-id", "route-demo-density", "--include-related")
    assert proc.returncode == 2
    assert "needs --brief" in proc.stderr


def test_brief_refuses_selectors_and_audit(mini_repo):
    _seed_unit(mini_repo)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--brief", "--route-id", "route-demo-density")
    assert proc.returncode == 2
    assert "expand one route" in proc.stderr
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--brief", "--audit")
    assert proc.returncode == 2
    assert "already carries the unit audit" in proc.stderr


def _second_unit(root: Path):
    module_dir = root / "curriculum/modules/module-demo"
    write_yaml(module_dir / "units/unit-demo-l02/unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2,
        "scope": "The second lecture as taught.", "status": "needs-map",
        "artifacts": {"ultimate_reference": "note-demo"},
        "workspace_ids": ["workspace-demo"],
    })
    map_path = module_dir / "source-map.yaml"
    source_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"].append({
        "id": "route-demo-l02", "unit_id": "unit-demo-l02",
        "title": "Variance", "locator": "deck.pdf, pp. 10-12",
        "depth": "core", "scope": "current",
    })
    write_yaml(map_path, source_map)
    module_path = module_dir / "module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)


def _run_expansion(root: Path, command: str):
    argv = shlex.split(command)
    assert not command.startswith("los ")
    return run_los(root, *argv)


def test_brief_reports_neighbor_count_with_runnable_expansion(mini_repo):
    _seed_unit(mini_repo)
    _second_unit(mini_repo)
    payload = _brief(mini_repo)
    audit = payload["unit_audit"]
    assert audit["adjacent_unit_source_reuse_count"] == 1
    assert "adjacent_unit_source_reuse" not in audit
    proc = _run_expansion(mini_repo, payload["expand"]["adjacent_unit_source_reuse"])
    assert proc.returncode == 0, proc.stderr
    widened = json.loads(proc.stdout)["unit_audit"]
    assert widened["adjacent_unit_source_reuse"] == {
        "unit-demo-l02": ["source-demo-book"]}
    assert widened["adjacent_unit_source_reuse_count"] == 1
    slim = {key: value for key, value in audit.items()
            if key != "adjacent_unit_source_reuse_count"}
    wide = {key: value for key, value in widened.items()
            if key not in ("adjacent_unit_source_reuse_count",
                           "adjacent_unit_source_reuse")}
    assert slim == wide


def test_brief_neighbor_expansion_matches_full_audit(mini_repo):
    _seed_unit(mini_repo)
    _second_unit(mini_repo)
    payload = _brief(mini_repo)
    proc = _run_expansion(mini_repo, payload["expand"]["adjacent_unit_source_reuse"])
    assert proc.returncode == 0, proc.stderr
    widened = json.loads(proc.stdout)
    audit_proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                         "--audit")
    assert audit_proc.returncode == 0, audit_proc.stderr
    audit = json.loads(audit_proc.stdout)
    assert audit["snapshot_id"] == widened["snapshot_id"] == payload["snapshot_id"]
    assert (widened["unit_audit"]["adjacent_unit_source_reuse"]
            == audit["unit_audit"]["adjacent_unit_source_reuse"])


def test_brief_without_neighbors_reports_zero_and_empty_map(mini_repo):
    _seed_unit(mini_repo)
    payload = _brief(mini_repo)
    assert payload["unit_audit"]["adjacent_unit_source_reuse_count"] == 0
    assert "adjacent_unit_source_reuse" not in payload["unit_audit"]
    proc = _run_expansion(mini_repo, payload["expand"]["adjacent_unit_source_reuse"])
    assert proc.returncode == 0, proc.stderr
    widened = json.loads(proc.stdout)["unit_audit"]
    assert widened["adjacent_unit_source_reuse"] == {}
    assert widened["adjacent_unit_source_reuse_count"] == 0


def test_brief_neighbor_growth_stays_in_the_count(mini_repo):
    _seed_unit(mini_repo)
    solo_proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                        "--brief")
    assert solo_proc.returncode == 0, solo_proc.stderr
    solo = json.loads(solo_proc.stdout)
    _second_unit(mini_repo)
    duo_proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                       "--brief")
    assert duo_proc.returncode == 0, duo_proc.stderr
    duo = json.loads(duo_proc.stdout)
    assert duo["unit_audit"]["adjacent_unit_source_reuse_count"] == 1
    assert "adjacent_unit_source_reuse" not in duo["unit_audit"]
    solo_audit = dict(solo["unit_audit"])
    duo_audit = dict(duo["unit_audit"])
    assert duo_audit.pop("adjacent_unit_source_reuse_count") == 1
    assert solo_audit.pop("adjacent_unit_source_reuse_count") == 0
    assert duo_audit == solo_audit
    # Expansions pin their own snapshot, which the second unit moves;
    # compare shapes with the token normalized away.
    solo_expand = json.loads(json.dumps(solo["expand"]).replace(
        solo["snapshot_id"], "SNAPSHOT"))
    duo_expand = json.loads(json.dumps(duo["expand"]).replace(
        duo["snapshot_id"], "SNAPSHOT"))
    solo_expand.pop("adjacent_unit_source_reuse")
    duo_expand.pop("adjacent_unit_source_reuse")
    assert duo_expand == solo_expand
    solo_refs = json.loads(json.dumps(solo["analysis_refs"]).replace(
        solo["snapshot_id"], "SNAPSHOT"))
    duo_refs = json.loads(json.dumps(duo["analysis_refs"]).replace(
        duo["snapshot_id"], "SNAPSHOT"))
    assert duo_refs == solo_refs
    for key in ("contract", "unit_id", "module_id", "artifact_revisions",
                "inventory", "required_inputs", "preflight"):
        assert duo[key] == solo[key], key
    assert len(duo_proc.stdout) - len(solo_proc.stdout) < 200


def test_brief_neighbors_combine_with_related(mini_repo):
    _seed_unit(mini_repo)
    _second_unit(mini_repo)
    body = "Density from an unrouted file.\n"
    _plant_note(mini_repo, "note-brief-related", body, {
        "resolution": "resolved",
        "material": "source-demo-book/other.pdf",
        "source_id": "source-demo-book",
        "recorded_source_digest": "ee" * 32,
        "live_source_digest": "ee" * 32,
        "inspected_range": {"start": 1, "end": 3},
        "frozen_input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "frozen_input_bytes": len(body.encode("utf-8")),
    })
    refs = _brief(mini_repo)["analysis_refs"]
    assert refs["related_count"] == 1
    widened = _brief(mini_repo, "--include-related", "--include-neighbors")
    assert [ref["note_id"] for ref in widened["analysis_refs"]["related_notes"]] == [
        "note-brief-related"]
    assert widened["unit_audit"]["adjacent_unit_source_reuse"] == {
        "unit-demo-l02": ["source-demo-book"]}


def test_brief_include_neighbors_is_refused_without_brief(mini_repo):
    _seed_unit(mini_repo)
    cases = (("--route-id", "route-demo-density"),
             ("--stage-id", "stage-demo"),
             ("--audit",),
             ())
    for extra in cases:
        proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                       *extra, "--include-neighbors")
        assert proc.returncode == 2, extra
        assert "needs --brief" in proc.stderr, extra
        assert not proc.stdout, extra


def test_brief_neighbor_expansion_refuses_a_stale_snapshot(mini_repo):
    _seed_unit(mini_repo)
    _second_unit(mini_repo)
    payload = _brief(mini_repo)
    command = payload["expand"]["adjacent_unit_source_reuse"]
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.write_text(note.read_text(encoding="utf-8")
                    + "\nA changed explanation.\n", encoding="utf-8")
    proc = _run_expansion(mini_repo, command)
    # A genuine optimistic-concurrency conflict: exit 3, like every other
    # stale-snapshot read (the top-level handler maps StaleSnapshot).
    assert proc.returncode == 3, proc.stderr
    assert "snapshot changed" in proc.stderr
    assert not proc.stdout
