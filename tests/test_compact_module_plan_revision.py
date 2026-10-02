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


def test_receipt_verification_without_a_synthesis_disposition(mini_repo, tmp_path):
    """A preflight records no synthesis disposition for a unit whose dossier path
    did not resolve before the import (a unit the import creates). Verification
    then takes its expectation from the receipt instead of rejecting the evidence
    (synthetic authoring campaign D6: `invalid-evidence` on a committed module
    import), and still fails closed on a dossier the request did not write."""
    from learning_os.material_synthesis import synthesis_destination

    _two_units(mini_repo)
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, _revision(mini_repo))
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert applied.returncode == 0, applied.stderr
    generated = subprocess.run([sys.executable, str(ROOT / "tools/generate.py"),
                                "--root", str(mini_repo)], text=True, capture_output=True)
    assert generated.returncode == 0, generated.stderr
    assert not synthesis_destination(mini_repo, "unit-demo-l02").exists()
    assert synthesis_destination(mini_repo, "unit-demo-l01").is_file()
    stripped = dict(report, synthesis={})
    review.write_text(json.dumps(stripped), encoding="utf-8")

    def verify(uid):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools/verify_plan_receipt.py"),
             "--root", str(mini_repo), "--unit", uid, "--report", str(review)],
            text=True, capture_output=True)

    no_dossier = verify("unit-demo-l02")
    assert no_dossier.returncode == 0, no_dossier.stdout + no_dossier.stderr
    assert no_dossier.stdout.splitlines()[0] == "state: committed-and-verified"
    unwritten = verify("unit-demo-l01")
    assert unwritten.returncode == 1, unwritten.stdout + unwritten.stderr
    assert unwritten.stdout.splitlines()[0] == "state: committed-but-verification-failed"
    assert "unexpected synthesis dossier" in unwritten.stderr


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


def test_unit_diff_covers_a_unit_without_a_study_map():
    """A unit with routes but no study map on either side still gets its diff:
    the review summary and the acknowledgment checks built on it (synthetic
    authoring campaign D13: the preflight showed `unit_id: ""` and 0 -> 0 routes
    for a unit the package added a route to)."""
    from learning_os.commands.module import _unit_semantic_diff

    kept = {"id": "route-x-kept", "unit_id": "unit-demo-x", "scope": "current",
            "covers": ["knowledge-x"], "locator": "Section 1"}
    added = {"id": "route-x-added", "unit_id": "unit-demo-x", "scope": "current",
             "covers": ["knowledge-x"], "locator": "Section 2"}
    live = {"sources": [{"source_id": "source-demo", "unit_routes": [kept]}]}
    staged = {"sources": [{"source_id": "source-demo", "unit_routes": [kept, added]}]}

    diff = _unit_semantic_diff(live, staged, None, None, "unit-demo-x")
    assert (diff["unit_id"], diff["routes_before"], diff["routes_after"]) == \
        ("unit-demo-x", 1, 2)
    assert diff["added"] == ["route-x-added"]

    removed = _unit_semantic_diff(staged, live, None, None, "unit-demo-x")
    assert removed["demoted_current_or_prerequisite"] == ["route-x-added"]


def _register_paper(root: Path) -> None:
    path = root / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text())
    data["sources"].append({
        "id": "source-demo-paper", "title": "Demo Paper", "type": "paper",
        "authors": ["P. Apier"],
        "evaluations": [{"concepts": ["concept-expected-value"],
                         "roles": ["first-learning"], "level": "introductory",
                         "strengths": ["a crisp derivation"]}],
    })
    write_yaml(path, data)


def _join_revision(root: Path) -> dict:
    revision = _revision(root)
    revision["source_joins"] = [{
        "source_id": "source-demo-paper", "role": "spine",
        "why": "The paper carries the lecture's core derivation.",
        "priority": 1,
    }]
    route = {
        "id": "route-demo-paper-l02", "unit_id": "unit-demo-l02",
        "title": "Route route-demo-paper-l02", "format": "paper",
        "angle": "A synthetic angle.",
        "angle_detail": "A synthetic angle in long form for this lecture.",
        "covers": ["knowledge-demo-expectation"],
        "depth": "derivation", "scope": "current",
        "locator": "paper-02.pdf, PDF pp. 2-5",
    }
    revision["unit_revisions"][1]["route_changes"]["add"] = [
        {"source_id": "source-demo-paper", "route": route}]
    revision["claim_evidence"] = [{
        "claim_id": "covers:route-demo-paper-l02",
        "evidence": [{"kind": "route-locator", "ref": "paper-02.pdf"}],
    }]
    return revision


def _refuses_join(mini_repo: Path, tmp_path: Path, revision: dict, fragment: str):
    draft = tmp_path / "join.yaml"
    write_yaml(draft, revision)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert refused.returncode == 2, refused.stdout
    assert fragment in refused.stderr, refused.stderr
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_source_join_adds_routes_and_patches_atomically(mini_repo, tmp_path):
    _two_units(mini_repo)
    _register_paper(mini_repo)
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, _join_revision(mini_repo))
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert report["canonical_files_written"] == 0
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert applied.returncode == 0, applied.stderr
    from learning_os.loader import load_repo
    repo = load_repo(mini_repo)
    entries = {entry["source_id"]: entry
               for entry in repo.module_source_maps["module-demo"]["sources"]}
    assert set(entries) == {"source-demo-book", "source-demo-paper"}
    joined = entries["source-demo-paper"]
    assert (joined["role"], joined["priority"]) == ("spine", 1)
    routes = {route["id"]: route for route in joined["unit_routes"]}
    assert routes["route-demo-paper-l02"]["unit_id"] == "unit-demo-l02"
    assert repo.study_maps["study-map-demo-l01"].data["stages"][0]["title"] == \
        "First revised stage"


def test_source_join_refuses_unknown_and_repeated_sources(mini_repo, tmp_path):
    _two_units(mini_repo)
    _register_paper(mini_repo)
    ghost = _join_revision(mini_repo)
    ghost["source_joins"][0]["source_id"] = "source-ghost"
    ghost["unit_revisions"][1]["route_changes"]["add"][0]["source_id"] = "source-ghost"
    _refuses_join(mini_repo, tmp_path, ghost, "not registered")
    joined = _join_revision(mini_repo)
    joined["source_joins"][0]["source_id"] = "source-demo-book"
    _refuses_join(mini_repo, tmp_path, joined, "already joined")
    twice = _join_revision(mini_repo)
    twice["source_joins"].append(dict(twice["source_joins"][0]))
    _refuses_join(mini_repo, tmp_path, twice, "same source twice")


def test_source_join_refuses_an_empty_source_id_as_missing(mini_repo, tmp_path):
    """An empty join source_id is a missing id, not an unregistered source:
    'not registered: ' names nothing to look up."""
    _two_units(mini_repo)
    _register_paper(mini_repo)
    revision = _join_revision(mini_repo)
    revision["source_joins"][0]["source_id"] = ""
    _refuses_join(mini_repo, tmp_path, revision, "needs a source_id")


def test_source_join_refuses_falsy_non_list_joins(mini_repo, tmp_path):
    """A mistyped `source_joins: {}` must fail loudly, not join nothing
    while the revision succeeds."""
    _two_units(mini_repo)
    _register_paper(mini_repo)
    for bad in ({}, "", 0, False):
        revision = _join_revision(mini_repo)
        revision["source_joins"] = bad
        _refuses_join(mini_repo, tmp_path, revision,
                      "source_joins must be a list")


def test_source_join_validates_the_join_record(mini_repo, tmp_path):
    _two_units(mini_repo)
    _register_paper(mini_repo)
    bad_role = _join_revision(mini_repo)
    bad_role["source_joins"][0]["role"] = "required-reading"
    _refuses_join(mini_repo, tmp_path, bad_role, "not a source-map role")
    empty_why = _join_revision(mini_repo)
    empty_why["source_joins"][0]["why"] = "  "
    _refuses_join(mini_repo, tmp_path, empty_why, "non-empty 'why'")
    bad_priority = _join_revision(mini_repo)
    bad_priority["source_joins"][0]["priority"] = -1
    _refuses_join(mini_repo, tmp_path, bad_priority, "'priority' must be")
    unknown_field = _join_revision(mini_repo)
    unknown_field["source_joins"][0]["mood"] = "hopeful"
    _refuses_join(mini_repo, tmp_path, unknown_field, "unknown fields")


def test_route_add_to_an_unjoined_source_is_still_refused(mini_repo, tmp_path):
    _two_units(mini_repo)
    _register_paper(mini_repo)
    revision = _join_revision(mini_repo)
    del revision["source_joins"]
    _refuses_join(mini_repo, tmp_path, revision, "unknown source")


def test_join_with_a_bad_second_unit_writes_nothing(mini_repo, tmp_path):
    _two_units(mini_repo)
    _register_paper(mini_repo)
    revision = _join_revision(mini_repo)
    revision["unit_revisions"][1]["stage_patches"][0]["stage_id"] = "missing-stage"
    before = (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes()
    _refuses_join(mini_repo, tmp_path, revision, "missing or repeated stage")
    assert (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes() == before


def test_route_change_refusal_names_the_expected_keys(mini_repo, tmp_path):
    """An add entry with a wrong key is refused naming both the unknown and the
    expected keys, so the entry shape is recoverable from the refusal alone
    (synthetic authoring campaign D10)."""
    _two_units(mini_repo)
    revision = _revision(mini_repo)
    revision["unit_revisions"][0]["route_changes"]["add"] = [
        {"source": "source-demo-book", "route": {"id": "route-demo-extra"}}]
    draft = tmp_path / "compact.yaml"
    write_yaml(draft, revision)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert refused.returncode != 0
    assert "route_changes.add has unknown fields ['source']" in refused.stderr
    assert "expected ['route', 'source_id']" in refused.stderr


def _append_fixture(root: Path) -> list[dict]:
    """A 23-row stage with unique ids and evidence on the first row."""
    _two_units(root)
    path = root / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study = yaml.safe_load(path.read_text(encoding="utf-8"))
    template = copy.deepcopy(study["stages"][0]["resources"][0])
    rows = []
    for number in range(23):
        row = copy.deepcopy(template)
        row["id"] = f"resource-demo-existing-{number:02d}"
        rows.append(row)
    rows[0]["independent_evidence"] = {
        "reviewed_by": "test", "reviewed_on": "2026-10-01",
        "verified_conditions": [], "note": "Preserve this assessment."}
    study["stages"][0]["resources"] = rows
    write_yaml(path, study)
    write_baseline(root, collect(root)[0], "resources-append fixture")
    return rows


def _appended_row(root_id="resource-demo-added", **overrides):
    row = {"id": root_id, "kind": "read", "scope_triage": "helpful-now",
           "material_ref": {"route_id": "route-demo-book",
                            "inherit": ["label", "source_id", "locator",
                                        "angle", "angle_detail"]}}
    row.update(overrides)
    return row


def _append_draft(root: Path, patches: list, *, unit_id="unit-demo-l01") -> dict:
    revision = _revision(root)
    revision["unit_revisions"] = [{"unit_id": unit_id, "stage_patches": patches}]
    return revision


def test_resources_append_adds_one_row_without_copying_old_ones(mini_repo, tmp_path):
    """One new placement in, 23 old rows carried forward, counts in review."""
    old_rows = _append_fixture(mini_repo)
    draft_data = _append_draft(mini_repo, [{"stage_id": "stage-demo",
                                           "resources_append": [_appended_row()]}])
    draft = tmp_path / "append.yaml"
    write_yaml(draft, draft_data)
    assert draft.stat().st_size < 1024
    assert "resource-demo-existing" not in draft.read_text(encoding="utf-8")
    before_l02 = (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02"
                  / "study-map.yaml").read_bytes()
    before_map = (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes()
    before_resume = (mini_repo / "curriculum/resume.yaml").read_bytes()
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert report["canonical_files_written"] == 0
    assert report["semantic_ack_required"] == []
    diff = report["units"]["unit-demo-l01"]
    assert (diff["placements_before"], diff["placements_after"]) == (23, 24)
    assert (diff["routes_before"], diff["routes_after"]) == (1, 1)
    assert diff["added"] == diff["updated"] == diff["removed"] == []
    assert diff["learner_state_changes"] == {}
    assert "stage-demo" in diff["learner_state_preserved"]
    synthesis = report["synthesis"]["unit-demo-l01"]
    assert synthesis["before"]["fresh"] is True
    assert synthesis["after"] == {"replaced": False, "fresh": True, "detail": None}
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert applied.returncode == 0, applied.stderr
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["capability"] == "module.plan.import"
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 1
    live = yaml.safe_load((mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01"
                           / "study-map.yaml").read_text(encoding="utf-8"))
    live_rows = live["stages"][0]["resources"]
    assert live_rows[:23] == old_rows
    assert live_rows[23]["id"] == "resource-demo-added"
    assert live_rows[23]["material_ref"]["route_id"] == "route-demo-book"
    assert (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02"
            / "study-map.yaml").read_bytes() == before_l02
    assert (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes() == before_map
    assert (mini_repo / "curriculum/resume.yaml").read_bytes() == before_resume
    from learning_os.loader import load_repo
    effective = load_repo(mini_repo).study_maps["study-map-demo-l01"].data
    added = effective["stages"][0]["resources"][23]
    assert added["label"] == "Route route-demo-book"
    assert added["source_id"] == "source-demo-book"
    generated = subprocess.run([sys.executable, str(ROOT / "tools/generate.py"),
                                "--root", str(mini_repo)], text=True, capture_output=True)
    assert generated.returncode == 0, generated.stderr


def test_resources_append_to_empty_stage_and_ordered_batch(mini_repo, tmp_path):
    """Appending to an empty stage keeps explicit submission order."""
    _two_units(mini_repo)
    path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
    study = yaml.safe_load(path.read_text(encoding="utf-8"))
    study["stages"][0]["resources"] = []
    write_yaml(path, study)
    write_baseline(mini_repo, collect(mini_repo)[0], "empty-stage append fixture")
    rows = [_appended_row(f"resource-demo-added-{suffix}")
            for suffix in ("a", "b", "c")]
    draft_data = _append_draft(mini_repo, [{"stage_id": "stage-demo",
                                           "resources_append": rows}])
    draft = tmp_path / "append-batch.yaml"
    write_yaml(draft, draft_data)
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    diff = report["units"]["unit-demo-l01"]
    assert (diff["placements_before"], diff["placements_after"]) == (0, 3)
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert applied.returncode == 0, applied.stderr
    live = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert [row["id"] for row in live["stages"][0]["resources"]] == [
        "resource-demo-added-a", "resource-demo-added-b", "resource-demo-added-c"]


def _append_refusal_cases():
    row = _appended_row()
    return [
        ("bare-stage", [{"stage_id": "stage-demo"}], 2,
         "changes nothing; give fields and/or resources_append"),
        ("empty-append", [{"stage_id": "stage-demo", "resources_append": []}], 2,
         "must be a non-empty list of resource objects"),
        ("dict-append", [{"stage_id": "stage-demo", "resources_append": {}}], 2,
         "must be a non-empty list of resource objects"),
        ("scalar-row", [{"stage_id": "stage-demo", "resources_append": ["x"]}], 2,
         "must be a non-empty list of resource objects"),
        ("unknown-field", [{"stage_id": "stage-demo", "fields": {"title": "t"},
                            "bogus": 1}], 2,
         "needs stage_id plus fields and/or resources_append"),
        ("scalar-patch", ["stage-demo"], 2,
         "needs stage_id plus fields and/or resources_append"),
        ("replacement-plus-append",
         [{"stage_id": "stage-demo", "fields": {"resources": []},
           "resources_append": [row]}], 2,
         "cannot combine resources_append with fields.resources"),
        ("missing-stage", [{"stage_id": "stage-missing",
                            "resources_append": [row]}], 2,
         "missing or repeated stage"),
        ("repeated-stage", [{"stage_id": "stage-demo", "resources_append": [row]},
                            {"stage_id": "stage-demo",
                             "resources_append": [_appended_row("resource-demo-second")]}],
         2, "missing or repeated stage"),
        ("missing-id", [{"stage_id": "stage-demo",
                        "resources_append": [{k: v for k, v in row.items()
                                             if k != "id"}]}], 2,
         "needs a fresh resource id on every row"),
        ("batch-duplicate",
         [{"stage_id": "stage-demo",
           "resources_append": [row, _appended_row("resource-demo-added")]}], 2,
         "repeats a resource id"),
        ("colliding-id",
         [{"stage_id": "stage-demo",
           "resources_append": [_appended_row("resource-demo-existing-00")]}], 2,
         "reuses an existing resource id"),
        ("empty-fields-with-append",
         [{"stage_id": "stage-demo", "fields": {},
           "resources_append": [row]}], 2,
         "fields must be non-empty"),
        ("bad-kind",
         [{"stage_id": "stage-demo",
           "resources_append": [_appended_row(kind="bogus")]}], 1,
         "'bogus' is not one of"),
        ("missing-route",
         [{"stage_id": "stage-demo",
           "resources_append": [_appended_row(material_ref={
               "route_id": "route-missing", "inherit": ["label"]})]}], 1,
         "material_ref route-missing is missing or ambiguous"),
        ("conflicting-override",
         [{"stage_id": "stage-demo",
           "resources_append": [_appended_row(label="X", material_ref={
               "route_id": "route-demo-book", "inherit": ["label"]})]}], 1,
         "cannot also override inherited label"),
    ]


def test_resources_append_refusals(mini_repo, tmp_path):
    """Every malformed append fails closed without partial writes."""
    old = _append_fixture(mini_repo)
    assert old[0]["id"] == "resource-demo-existing-00"
    before = (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes()
    for name, patches, code, fragment in _append_refusal_cases():
        draft = tmp_path / f"{name}.yaml"
        write_yaml(draft, _append_draft(mini_repo, patches))
        refused = run_los(mini_repo, "module-plan-import", "module-demo",
                          "--file", str(draft), "--check")
        assert refused.returncode == code, (name, refused.stdout, refused.stderr)
        assert fragment in refused.stderr, (name, refused.stderr)
    cross = tmp_path / "cross-unit.yaml"
    write_yaml(cross, _append_draft(mini_repo, [{"stage_id": "stage-demo-l02",
                                                "resources_append": [_appended_row()]}]))
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(cross), "--check")
    assert refused.returncode == 2, refused.stderr
    assert "missing or repeated stage" in refused.stderr
    cross_route = tmp_path / "cross-route.yaml"
    write_yaml(cross_route, _append_draft(mini_repo, [{"stage_id": "stage-demo",
        "resources_append": [_appended_row(material_ref={
            "route_id": "route-demo-book-l02", "inherit": ["label"]})]}]))
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(cross_route), "--check")
    assert refused.returncode == 1, refused.stderr
    assert "missing or ambiguous in unit-demo-l01" in refused.stderr
    assert (mini_repo / "curriculum/modules/module-demo/source-map.yaml").read_bytes() == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_resources_append_apply_refuses_edited_and_stale_state(mini_repo, tmp_path):
    """Edited drafts and moved snapshots cannot ride a saved append review."""
    from learning_os.fingerprint import canonical_fingerprint

    _append_fixture(mini_repo)
    draft_data = _append_draft(mini_repo, [{"stage_id": "stage-demo",
                                           "resources_append": [_appended_row()]}])
    draft = tmp_path / "append.yaml"
    write_yaml(draft, draft_data)
    checked = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    review = tmp_path / "review.json"
    review.write_text(checked.stdout, encoding="utf-8")
    edited = tmp_path / "edited.yaml"
    edited.write_text(draft.read_text(encoding="utf-8") + "# changed after review\n",
                      encoding="utf-8")
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(edited), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert refused.returncode == 2
    assert "reviewed bytes changed" in refused.stderr
    (mini_repo / "work/inbox/intervening.md").write_text("New learner input.\n",
                                                        encoding="utf-8")
    before = canonical_fingerprint(mini_repo)
    refused = run_los(mini_repo, "module-plan-import", "module-demo",
                      "--file", str(draft), "--review-report", str(review),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"])
    assert refused.returncode != 0
    assert "STALE_SNAPSHOT" in refused.stdout
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
