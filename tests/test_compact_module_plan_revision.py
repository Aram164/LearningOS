"""Compact multi-unit edits still use the governed module import transaction."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml
from repo_builders import _audit, _compact_setup, run_los, write_yaml

from learning_os.warning_baseline import collect, write_baseline

ROOT = Path(__file__).resolve().parents[1]


def _two_units(root: Path) -> None:
    _compact_setup(root)
    base = root / "curriculum/modules/module-demo"
    module = yaml.safe_load((base / "module.yaml").read_text())
    module["unit_order"].append("unit-demo-l02")
    write_yaml(base / "module.yaml", module)
    first = base / "units/unit-demo-l01"
    second = base / "units/unit-demo-l02"
    original_study = yaml.safe_load((first / "study-map.yaml").read_text())
    original_study["plan_template_version"] = 1
    original_study["stages"][0].update(number=1, exam_critical=False, concepts=[])
    write_yaml(first / "study-map.yaml", original_study)
    unit = yaml.safe_load((first / "unit.yaml").read_text())
    unit.update(id="unit-demo-l02", title="Second lecture", order=2,
                current_study_map="study-map-demo-l02")
    write_yaml(second / "unit.yaml", unit)
    study = yaml.safe_load((first / "study-map.yaml").read_text())
    study.update(id="study-map-demo-l02", unit_id="unit-demo-l02",
                 current_stage="stage-demo-l02")
    study["stages"][0]["id"] = "stage-demo-l02"
    study["stages"][0]["working_note"] = (
        "curriculum/modules/module-demo/units/unit-demo-l02/"
        "stages/stage-demo-l02/notes.md")
    write_yaml(second / "study-map.yaml", study)
    note = root / study["stages"][0]["working_note"]
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text("", encoding="utf-8")
    source_path = base / "source-map.yaml"
    source_map = yaml.safe_load(source_path.read_text())
    route = copy.deepcopy(source_map["sources"][0]["unit_routes"][0])
    route.update(id="route-demo-book-l02", unit_id="unit-demo-l02")
    source_map["sources"][0]["unit_routes"].append(route)
    write_yaml(source_path, source_map)
    workspace = root / "work/active/workspace-demo/CONTEXT.md"
    workspace.write_text(workspace.read_text().replace(
        "- unit-demo-l01", "- unit-demo-l01\n- unit-demo-l02"), encoding="utf-8")
    _audit(root)
    write_baseline(root, collect(root)[0], "two-unit compact revision fixture")


def _revision(root: Path) -> dict:
    return {
        "module_id": "module-demo",
        "plan_contract": {
            "version": 2, "plan_template_version": 1,
            "coverage_audit": _audit(root), "intentional_reorders": [],
            "checks": {key: True for key in (
                "local_inventory_complete", "linked_inventory_complete",
                "materials_opened_and_content_checked",
                "current_and_prior_scope_reconciled",
                "duplicates_and_numbering_checked",
                "exclusions_and_unresolved_gaps_recorded")},
        },
        "unit_revisions": [
            {"unit_id": "unit-demo-l01",
             "route_changes": {"update": [{"route_id": "route-demo-book",
                                           "fields": {"angle": "First revised angle."}}]},
             "stage_patches": [{"stage_id": "stage-demo",
                                "fields": {"title": "First revised stage"}}]},
            {"unit_id": "unit-demo-l02",
             "route_changes": {"update": [{"route_id": "route-demo-book-l02",
                                           "fields": {"angle": "Second revised angle."}}]},
             "stage_patches": [{"stage_id": "stage-demo-l02",
                                "fields": {"title": "Second revised stage"}}]},
        ],
    }


def test_compact_batch_reviews_and_commits_both_units_atomically(mini_repo, tmp_path):
    _two_units(mini_repo)
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, _revision(mini_repo))
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert report["canonical_files_written"] == 0
    assert report["reviewed_file_sha256"] != report["assembled_package_sha256"]
    assert set(report["units"]) == {"unit-demo-l01", "unit-demo-l02"}
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert applied.returncode == 0, applied.stderr
    from learning_os.loader import load_repo
    repo = load_repo(mini_repo)
    routes = {route["id"]: route for source in repo.module_source_maps["module-demo"]["sources"]
              for route in source["unit_routes"]}
    assert routes["route-demo-book"]["angle"] == "First revised angle."
    assert routes["route-demo-book-l02"]["angle"] == "Second revised angle."
    assert repo.study_maps["study-map-demo-l01"].data["stages"][0]["title"] == "First revised stage"
    assert repo.study_maps["study-map-demo-l02"].data["stages"][0]["title"] == "Second revised stage"
    generated = subprocess.run([sys.executable, str(ROOT / "tools/generate.py"),
                                "--root", str(mini_repo)], text=True, capture_output=True)
    assert generated.returncode == 0, generated.stderr
    for uid in ("unit-demo-l01", "unit-demo-l02"):
        verified = subprocess.run(
            [sys.executable, str(ROOT / "tools/verify_plan_receipt.py"),
             "--root", str(mini_repo), "--unit", uid, "--report", str(review)],
            text=True, capture_output=True)
        assert verified.returncode == 0, verified.stderr


def test_compact_batch_refuses_bad_second_unit_without_partial_write(mini_repo, tmp_path):
    _two_units(mini_repo)
    draft_data = _revision(mini_repo)
    draft_data["unit_revisions"][1]["stage_patches"][0]["stage_id"] = "missing-stage"
    draft = tmp_path / "invalid.yaml"
    write_yaml(draft, draft_data)
    before = (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes()
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 2
    assert "missing or repeated stage" in checked.stderr
    assert (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes() == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_compact_batch_binds_the_exact_reviewed_file(mini_repo, tmp_path):
    _two_units(mini_repo)
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, _revision(mini_repo))
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    with draft.open("a", encoding="utf-8") as stream:
        stream.write("# changed after review\n")
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert refused.returncode == 2
    assert "reviewed bytes changed" in refused.stderr
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_compact_resource_patch_cannot_drop_independent_evidence(mini_repo, tmp_path):
    _two_units(mini_repo)
    path = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
    study = yaml.safe_load(path.read_text())
    study["stages"][0]["resources"][0]["independent_evidence"] = {
        "reviewed_by": "test", "note": "Preserve this assessment."}
    write_yaml(path, study)
    write_baseline(mini_repo, collect(mini_repo)[0], "evidence-preservation fixture")
    draft_data = _revision(mini_repo)
    draft_data["unit_revisions"][0]["stage_patches"][0]["fields"]["resources"] = []
    draft = tmp_path / "drop-evidence.yaml"
    write_yaml(draft, draft_data)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert refused.returncode == 1
    assert "loses independent evidence" in refused.stderr
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
