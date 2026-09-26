"""Regression tests for the unit-revision friction (Steps 1-3).

Each test pins a failure observed during the L04 revision: schema/generator
divergence, preflight/live perimeter disagreement, and the route/synthesis
ordering trap. Later steps build the compact revise path on top of these.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from repo_builders import (
    _audit,
    _compact_revision,
    _compact_setup,
    _plan_contract,
    _sliced_route,
    _sliced_unit,
    _valid_dossier,
)

from learning_os.contracts import perimeter as pm

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "system" / "schema" / "capabilities"
ENVELOPE_OWNED = {"approve", "apply_reviewed_sha256", "review_report",
                  "expected_snapshot", "expected_revision", "expected_revisions"}


def test_generated_schemas_never_expose_envelope_owned_fields():
    schemas = sorted(SCHEMA_DIR.glob("*.schema.json"))
    assert schemas, "no generated capability schemas found"
    leaked = []
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        props = set(schema.get("properties", {}))
        required = set(schema.get("required", []))
        hit = (props | required) & ENVELOPE_OWNED
        if hit:
            leaked.append(f"{path.name}: {sorted(hit)}")
    assert not leaked, "envelope-owned fields leaked into payload schemas:\n" + "\n".join(leaked)
    # `check` is a per-command dry-run mode the gateway honors — it must stay
    # a payload field where the CLI defines it, or gateway dry runs silently
    # become live writes.
    for name in ("module.plan.import", "unit.plan.revise"):
        schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert "check" in schema.get("properties", {}), name


def test_unit_revision_schema_requires_inline_reviewed_content():
    from jsonschema import Draft202012Validator

    schema = json.loads((SCHEMA_DIR / "unit.plan.revise.schema.json").read_text())
    validator = Draft202012Validator(schema)
    inline = {"unit_id": "unit-test", "record": {}}
    assert not list(validator.iter_errors(inline))
    file_input = {"unit_id": "unit-test", "file": "revision.yaml",
                  "file_sha256": "sha256:" + "0" * 64}
    assert list(validator.iter_errors(file_input))
    assert list(validator.iter_errors({**file_input, "record": {}}))


def test_gateway_refuses_smuggled_approval(mini_repo: Path):
    """A hand-built V2 payload containing `approve` must be refused."""
    from learning_os.commands.capability import _dispatch
    from learning_os.contracts.capability_catalog import command_definitions

    definitions = command_definitions(mini_repo)
    definition = definitions["capture.create"]

    def parser_factory():
        import los
        return los.build_parser()

    envelope = {
        "schema_version": 2,
        "request_id": "request-smuggled-approve",
        "idempotency_key": "smuggled-approve-001",
        "capability": "capture.create",
        "channel": "codex",
        "expected_snapshot": "sha256:" + "0" * 64,
        "expected_revisions": {},
        "approval": {"kind": "operator-approval",
                     "subject_sha256": "sha256:" + "0" * 64},
    }
    with pytest.raises(Exception, match="(?i)approv"):
        _dispatch(mini_repo, definition, envelope,
                  {"text": "x", "approve": True},
                  parser_factory=parser_factory)


def test_preflight_sees_the_same_perimeter_as_live(mini_repo: Path):
    """An undeclared wrapper sibling must fail `--check`, not just live apply."""
    from learning_os.commands.module import _module_plan_validation_errors

    wrapper = mini_repo.parent
    for anchor in ("obsidian-ui", "workbench", "archive"):
        (wrapper / anchor).mkdir(parents=True, exist_ok=True)
    (mini_repo / "system" / "contracts").mkdir(parents=True, exist_ok=True)
    (mini_repo / pm.PERIMETER_RELATIVE).write_text(
        yaml.safe_dump({
            "perimeter_version": 1,
            "roots": {"wrapper": ".", "umbrella": "LearningOS"},
            "applies_when_present": ["LearningOS/obsidian-ui",
                                     "LearningOS/workbench",
                                     "LearningOS/archive"],
            "material_suffixes": [".pdf"],
            "ephemera": [".DS_Store"],
            "entries": [
                {"path": "LearningOS", "kind": "directory", "owner": "learningos"},
                {"path": "LearningOS/repository", "kind": "nested_repo",
                 "owner": "learningos"},
                {"path": "LearningOS/obsidian-ui", "kind": "nested_repo",
                 "owner": "learningos"},
                {"path": "LearningOS/workbench", "kind": "directory",
                 "owner": "workbench"},
                {"path": "LearningOS/archive", "kind": "directory",
                 "owner": "archive"},
            ],
            "pending_disposition": [],
        }, sort_keys=False),
        encoding="utf-8",
    )
    (wrapper / "Claude outputs").mkdir(parents=True, exist_ok=True)
    ((wrapper / "Claude outputs") / "stray.md").write_text("x\n", encoding="utf-8")

    assert any(i.code == "UNDECLARED" for i in pm.check(mini_repo))
    failures = _module_plan_validation_errors(mini_repo, {})
    assert any("PERIMETER-UNDECLARED" in line for line in failures), failures


def test_route_change_with_stale_dossier_fails_closed(mini_repo: Path):
    """Adding a route without a replacement dossier must keep failing."""
    from learning_os.material_synthesis import (
        MaterialSynthesisError,
        validate_unit_material_synthesis,
    )

    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    good = _valid_dossier(mini_repo, "route-demo-book", "lecture-01.pdf")
    assert validate_unit_material_synthesis(mini_repo, "unit-demo-l01", good)

    stale = dict(good)
    stale["route_assessments"] = [{**good["route_assessments"][0],
                                   "route_id": "route-that-does-not-exist"}]
    with pytest.raises(MaterialSynthesisError, match="coverage mismatch"):
        validate_unit_material_synthesis(mini_repo, "unit-demo-l01", stale)

    from repo_builders import run_los

    from learning_os.material_synthesis import synthesis_destination
    synthesis_destination(mini_repo, "unit-demo-l01").write_text(
        yaml.safe_dump(stale, sort_keys=False), encoding="utf-8")
    context = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--brief")
    assert context.returncode == 0, context.stderr
    synthesis = json.loads(context.stdout)["unit_audit"]["synthesis"]
    assert synthesis["present"] is True
    assert synthesis["fresh"] is False
    assert synthesis["replacement_required_if_evidential_routes_change"] is True


def _changed_scope_map(mini_repo: Path) -> dict:
    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    source_map = yaml.safe_load(source_map_path.read_text(encoding="utf-8"))
    source_map["sources"][0]["unit_routes"][0]["scope"] = "complementary"
    return source_map


def test_route_change_without_replacement_demands_a_dossier(mini_repo, tmp_path):
    """An evidential route edit with an old dossier fails with one diagnostic."""

    from repo_builders import run_los, write_yaml

    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    good = _valid_dossier(mini_repo, "route-demo-book", "lecture-01.pdf")
    from learning_os.material_synthesis import synthesis_destination
    synthesis_destination(mini_repo, "unit-demo-l01").write_text(
        yaml.safe_dump(good, sort_keys=False), encoding="utf-8")

    audit_rel = _audit(mini_repo)
    from learning_os.warning_baseline import collect, write_baseline
    write_baseline(mini_repo, collect(mini_repo)[0], "unit revision fixture")
    unit_data = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml")
        .read_text(encoding="utf-8"))
    package = tmp_path / "scope-change.yaml"
    write_yaml(package, {
        "module_id": "module-demo",
        "plan_contract": _plan_contract(audit_rel),
        "module_patch": {},
        "source_map": _changed_scope_map(mini_repo),
        "units": [{"unit": unit_data, "study_map": None}],
    })
    proc = run_los(mini_repo, "module-plan-import", "module-demo",
                   "--file", str(package), "--check")
    assert proc.returncode == 1, proc.stderr
    assert "no replacement dossier was supplied" in proc.stderr


def test_route_change_with_replacement_applies_atomically(mini_repo, tmp_path):
    """New map, unchanged placements and replacement dossier validate together."""
    import copy
    import json

    from repo_builders import run_los, write_yaml

    from learning_os.material_synthesis import (
        current_unit_material_basis,
        synthesis_destination,
    )

    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    good = _valid_dossier(mini_repo, "route-demo-book", "lecture-01.pdf")
    destination = synthesis_destination(mini_repo, "unit-demo-l01")
    destination.write_text(yaml.safe_dump(good, sort_keys=False), encoding="utf-8")
    audit_rel = _audit(mini_repo)
    from learning_os.warning_baseline import collect, write_baseline
    write_baseline(mini_repo, collect(mini_repo)[0], "unit revision fixture")

    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    original = source_map_path.read_text(encoding="utf-8")
    try:
        source_map_path.write_text(
            yaml.safe_dump(_changed_scope_map(mini_repo), sort_keys=False),
            encoding="utf-8")
        changed_basis = current_unit_material_basis(mini_repo, "unit-demo-l01")
    finally:
        source_map_path.write_text(original, encoding="utf-8")
    replacement = copy.deepcopy(good)
    replacement["basis"] = {**changed_basis, "ai_provenance": good["basis"]["ai_provenance"]}

    unit_data = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml")
        .read_text(encoding="utf-8"))
    package = tmp_path / "scope-change.yaml"
    body = {
        "module_id": "module-demo",
        "plan_contract": _plan_contract(audit_rel),
        "module_patch": {},
        "source_map": _changed_scope_map(mini_repo),
        "units": [{"unit": unit_data, "study_map": None}],
        "material_syntheses": [{"unit_id": "unit-demo-l01", "dossier": replacement}],
    }
    write_yaml(package, body)
    missing_ack = run_los(mini_repo, "module-plan-import", "module-demo",
                          "--file", str(package), "--check")
    assert missing_ack.returncode == 1, missing_ack.stderr
    assert "semantic review required (demotion route-demo-book)" in missing_ack.stderr

    body["acknowledgments"] = [{
        "kind": "demotion",
        "target": "route-demo-book",
        "reason": "Superseded by the new derivation; tutorial keeps the drill.",
    }]
    write_yaml(package, body)
    proc = run_los(mini_repo, "module-plan-import", "module-demo",
                   "--file", str(package), "--check")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["canonical_files_written"] == 0
    assert report["routes_updated"] == ["route-demo-book"]
    assert report["synthesis"]["unit-demo-l01"]["after"]["fresh"] is True
    assert report["expected_snapshot"].startswith("sha256:")
    assert report["semantic_ack_required"] == []


def test_compact_revision_checks_one_lecture(mini_repo, tmp_path):
    """One context-sized patch, one preflight, no full-map copy in the input."""
    import json

    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    context = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--brief")
    assert context.returncode == 0, context.stderr
    synthesis = json.loads(context.stdout)["unit_audit"]["synthesis"]
    assert synthesis["present"] is True
    assert synthesis["fresh"] is True
    assert synthesis["replacement_required_if_evidential_routes_change"] is True
    revision_file = tmp_path / "l04-revision.yaml"
    write_yaml(revision_file, _compact_revision(
        mini_repo,
        route_changes={"update": [{
            "route_id": "route-demo-book",
            "fields": {"angle": "A sharper lecture-specific angle.",
                       "angle_detail": "A sharper long form for this lecture."}}]},
    ))
    assert revision_file.stat().st_size < 2048
    assert "unit_routes" not in revision_file.read_text(encoding="utf-8")
    proc = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                   "--file", str(revision_file), "--check")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["canonical_files_written"] == 0
    assert report["routes_updated"] == ["route-demo-book"]
    assert report["synthesis"]["unit-demo-l01"]["after"]["fresh"] is True
    assert report["expected_revisions"] == {"module-demo": 0}


def test_missing_dossier_does_not_require_replacement_for_route_addition(
    mini_repo, tmp_path,
):
    """The briefing and real revision preflight agree on an absent dossier."""
    from repo_builders import run_los, write_yaml

    _sliced_unit(mini_repo, [_sliced_route("route-demo-book", "lecture-01.pdf")])
    from learning_os.warning_baseline import collect, write_baseline
    write_baseline(mini_repo, collect(mini_repo)[0], "unit revision fixture")
    context = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--brief")
    assert context.returncode == 0, context.stderr
    synthesis = json.loads(context.stdout)["unit_audit"]["synthesis"]
    assert synthesis["present"] is False
    assert synthesis["fresh"] is False
    assert synthesis["replacement_required_if_evidential_routes_change"] is False
    assert "no existing dossier" in synthesis["replacement_reason"]

    route = _sliced_route("route-demo-new", "lecture-01.pdf, PDF p. 1",
                          scope="complementary")
    revision = _compact_revision(mini_repo, route_changes={"add": [
        {"source_id": "source-demo-book", "route": route},
    ]}, claim_evidence=[{
        "claim_id": "covers:route-demo-new",
        "evidence": [{"kind": "route-locator", "ref": "lecture-01.pdf"}],
    }])
    path = tmp_path / "add-without-dossier.yaml"
    write_yaml(path, revision)
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(path), "--check")
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["routes_added"] == ["route-demo-new"]


def test_compact_revision_route_ops_fail_closed(mini_repo, tmp_path):
    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    cases = [
        {"update": [{"route_id": "route-missing",
                     "fields": {"angle": "x"}}]},
        {"update": [{"route_id": "route-demo-book",
                     "fields": {"unit_id": "unit-demo-l02"}}]},
        {"remove": [{"route_id": "route-demo-book"}]},
        {"add": [{"source_id": "source-demo-book",
                  "route": {"id": "route-demo-book", "unit_id": "unit-demo-l01",
                            "title": "Dup", "format": "book", "angle": "a",
                            "covers": [], "depth": "orientation",
                            "scope": "optional", "locator": "p. 1"}}]},
    ]
    for changes in cases:
        revision_file = tmp_path / "bad-revision.yaml"
        write_yaml(revision_file, _compact_revision(mini_repo, route_changes=changes))
        proc = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                       "--file", str(revision_file), "--check")
        assert proc.returncode == 2, (changes, proc.stderr)


def test_compact_revision_applies_through_the_gateway(mini_repo, tmp_path):
    """One governed application, one receipt, synthesis stays current."""
    import json

    from gateway_helpers import approved_v2_cli

    _compact_setup(mini_repo)
    revision = _compact_revision(
        mini_repo,
        route_changes={"update": [{
            "route_id": "route-demo-book",
            "fields": {"angle": "A sharper lecture-specific angle."}}]},
    )
    proc = approved_v2_cli(
        mini_repo, "unit-plan-revise", "unit-demo-l01",
        "--record", json.dumps(revision),
        artifact_ids=["module-demo"],
        idempotency_key="unit-revise-angle-001",
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    # An angle-only edit touches the module source map, so the module owns
    # the revision; the unit artifact is untouched — no false churn.
    assert response["result"]["artifact_revisions"]["module-demo"] == 1
    assert "unit-demo-l01" not in response["result"]["artifact_revisions"]
    from learning_os.loader import load_repo
    live_map = load_repo(mini_repo).module_source_maps["module-demo"]
    row = next(r for s in live_map["sources"] for r in s["unit_routes"]
               if r.get("id") == "route-demo-book")
    assert row["angle"] == "A sharper lecture-specific angle."


def test_reviewed_apply_needs_no_hand_built_envelope(mini_repo, tmp_path):
    """--check, review the SHA, apply it: one receipt, operator approval."""
    import json

    from gateway_helpers import file_sha256
    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    revision_file = tmp_path / "l04-revision.yaml"
    write_yaml(revision_file, _compact_revision(
        mini_repo,
        route_changes={"update": [{
            "route_id": "route-demo-book",
            "fields": {"angle": "A sharper lecture-specific angle."}}]},
    ))
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    sha = report["reviewed_file_sha256"]
    assert sha == file_sha256(revision_file)
    assert report["assembled_package_sha256"] != sha
    report_file = tmp_path / "review.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", sha,
                      "--review-report", str(report_file))
    assert applied.returncode == 0, applied.stderr
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    assert response["capability"] == "unit.plan.revise"
    receipt = yaml.safe_load(
        (mini_repo / response["receipt_path"]).read_text(encoding="utf-8"))
    assert receipt["capability"] == "unit.plan.revise"
    assert receipt["request"]["approval"]["kind"] == "operator-approval"
    assert receipt["request"]["intent_sha256"].startswith("sha256:")
    grants = [g["capability"] for g in receipt["authority"]["grants"]]
    assert grants == ["unit.plan.revise"]
    assert response["snapshot_after"] == receipt["snapshot_after"]
    from learning_os.loader import load_repo
    live_map = load_repo(mini_repo).module_source_maps["module-demo"]
    row = next(r for s in live_map["sources"] for r in s["unit_routes"]
               if r.get("id") == "route-demo-book")
    assert row["angle"] == "A sharper lecture-specific angle."


def test_verify_plan_receipt_checks_projection(mini_repo, tmp_path):
    """Receipt, checksums, counts, synthesis and artifact scope agree."""
    import json
    import subprocess
    import sys

    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    revision = _compact_revision(
        mini_repo,
        route_changes={"update": [{
            "route_id": "route-demo-book",
            "fields": {"angle": "A sharper lecture-specific angle."}}]},
    )
    revision_file = tmp_path / "l04-revision.yaml"
    write_yaml(revision_file, revision)
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file), "--check")
    assert checked.returncode == 0, checked.stderr
    report_file = tmp_path / "check-report.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    proc = run_los(
        mini_repo, "unit-plan-revise", "unit-demo-l01",
        "--file", str(revision_file), "--review-report", str(report_file),
        "--apply-reviewed-sha256", json.loads(checked.stdout)["reviewed_file_sha256"],
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    generated = subprocess.run(
        [sys.executable,
         str(Path(__file__).resolve().parents[1] / "tools" / "generate.py"),
         "--root", str(mini_repo)],
        text=True, capture_output=True,
    )
    assert generated.returncode == 0, generated.stderr
    script = Path(__file__).resolve().parents[1] / "tools" / "verify_plan_receipt.py"
    verify = subprocess.run(
        [sys.executable, str(script), "--root", str(mini_repo),
         "--receipt", response["receipt_path"], "--unit", "unit-demo-l01",
         "--report", str(report_file), "--expect-artifacts", "module-demo"],
        text=True, capture_output=True,
    )
    assert verify.returncode == 0, verify.stderr


def _live_study_map() -> dict:
    def resource(rid, triage):
        return {"kind": "read", "label": f"Resource {rid}",
                "source_id": "source-demo-book", "locator": "lecture-01.pdf",
                "route_id": rid, "scope_triage": triage}

    def stage(sid, number, title, resources):
        return {"id": sid, "number": number, "title": title, "status": "pending",
                "objective": f"Objective for {title}.",
                "done_when": [f"Done when {title} is understood."],
                "exam_critical": False, "concepts": [],
                "scope_triage": "required-now", "resources": resources,
                "working_note": "curriculum/modules/module-demo/units/unit-demo-l01"
                                f"/stages/{sid}/notes.md",
                "attachments": [], "source_feedback": []}

    return {"id": "study-map-demo-l01", "type": "study-map",
            "plan_template_version": 1, "unit_id": "unit-demo-l01",
            "status": "ready", "current_stage": "stage-demo-intro",
            "source_plan": {"path": "work/active/workspace-demo/CONTEXT.md",
                            "provenance": "operator"},
            "detours": [], "shelving": {"state": "none"},
            "stages": [
                stage("stage-demo-intro", 1, "Intro",
                      [resource("route-demo-book", "required-now"),
                       resource("route-demo-old", "required-now")]),
                stage("stage-demo-drill", 2, "Drill",
                      [resource("route-demo-sup", "helpful-now")]),
            ]}


def _acceptance_setup(mini_repo: Path):
    from repo_builders import write_yaml

    _sliced_unit(mini_repo, [
        _sliced_route("route-demo-book", "lecture-01.pdf"),
        _sliced_route("route-demo-old", "lecture-01.pdf"),
        _sliced_route("route-demo-sup", "lecture-01.pdf", scope="complementary"),
    ])
    unit_path = mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml"
    unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
    unit["current_study_map"] = "study-map-demo-l01"
    write_yaml(unit_path, unit)
    live_map_doc = _live_study_map()
    write_yaml(mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
               live_map_doc)
    for _stage in live_map_doc["stages"]:
        note = mini_repo / _stage["working_note"]
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("", encoding="utf-8")
    resume_path = mini_repo / "curriculum/resume.yaml"
    resume = yaml.safe_load(resume_path.read_text(encoding="utf-8"))
    resume["stage_id"] = "stage-demo-intro"
    write_yaml(resume_path, resume)
    good = _valid_dossier(mini_repo, "route-demo-book", "lecture-01.pdf")
    from learning_os.material_synthesis import (
        current_unit_material_basis,
        synthesis_destination,
    )
    basis = current_unit_material_basis(mini_repo, "unit-demo-l01")
    assessments = []
    for rid, status in (("route-demo-book", "deep-reviewed"),
                        ("route-demo-old", "deep-reviewed"),
                        ("route-demo-sup", "screened")):
        row = dict(good["route_assessments"][0])
        if status == "screened":
            row = {k: row[k] for k in ("route_id", "source_id", "locator",
                                       "review_status", "concept_ids")}
            row["reason"] = "Complementary background; screened, not deeply reviewed."
        row.update(route_id=rid, review_status=status,
                   evidence=[{"locator": "lecture-01.pdf p.1",
                              "checksum": basis["material_checksums"][rid]}])
        assessments.append(row)
    good["basis"] = {**basis, "ai_provenance": good["basis"]["ai_provenance"]}
    good["route_assessments"] = assessments
    synthesis_destination(mini_repo, "unit-demo-l01").write_text(
        yaml.safe_dump(good, sort_keys=False), encoding="utf-8")
    _audit(mini_repo)
    from learning_os.warning_baseline import collect, write_baseline
    write_baseline(mini_repo, collect(mini_repo)[0], "acceptance fixture")
    return good


def test_acceptance_one_lecture_revision_end_to_end(mini_repo, tmp_path):
    """The L04 shape: add one, remove one, re-angle, re-triage, one receipt."""
    import copy
    import json

    from repo_builders import run_los, write_yaml

    from learning_os.material_synthesis import current_unit_material_basis

    _acceptance_setup(mini_repo)
    new_route = _sliced_route("route-demo-new", "lecture-01.pdf")
    revision = _compact_revision(
        mini_repo,
        route_changes={
            "add": [{"source_id": "source-demo-book", "route": new_route}],
            "update": [{"route_id": "route-demo-book",
                        "fields": {"angle": "A sharper lecture-specific angle."}}],
            "remove": [{"route_id": "route-demo-old",
                        "reason": "Superseded by route-demo-new."}],
        },
        acknowledgments=[{
            "kind": "demotion", "target": "route-demo-old",
            "reason": "Superseded by route-demo-new; coverage retained.",
        }],
        claim_evidence=[
            {"claim_id": "covers:route-demo-old",
             "evidence": [{"kind": "route-locator", "ref": "lecture-01.pdf"}]},
            {"claim_id": "covers:route-demo-new",
             "evidence": [{"kind": "route-locator", "ref": "lecture-01.pdf"}]},
        ],
    )
    final_map = _live_study_map()
    intro = next(s for s in final_map["stages"] if s["id"] == "stage-demo-intro")
    intro["resources"] = [r for r in intro["resources"]
                          if r["route_id"] != "route-demo-old"]
    intro["resources"].append({"kind": "read", "label": "Resource route-demo-new",
                               "source_id": "source-demo-book",
                               "locator": "lecture-01.pdf",
                               "route_id": "route-demo-new",
                               "scope_triage": "required-now"})
    revision["study_map"] = final_map

    source_map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    original = source_map_path.read_text(encoding="utf-8")
    try:
        staged = yaml.safe_load(original)
        staged["sources"][0]["unit_routes"] = [
            r for r in staged["sources"][0]["unit_routes"]
            if r.get("id") != "route-demo-old"]
        staged["sources"][0]["unit_routes"].append(
            {k: v for k, v in new_route.items()})
        staged["sources"][0]["unit_routes"][0]["angle"] = \
            "A sharper lecture-specific angle."
        source_map_path.write_text(yaml.safe_dump(staged, sort_keys=False),
                                   encoding="utf-8")
        changed_basis = current_unit_material_basis(mini_repo, "unit-demo-l01")
    finally:
        source_map_path.write_text(original, encoding="utf-8")
    old_dossier = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/material-synthesis.yaml")
        .read_text(encoding="utf-8"))
    replacement = copy.deepcopy(old_dossier)
    replacement["basis"] = {**changed_basis,
                            "ai_provenance": old_dossier["basis"]["ai_provenance"]}
    kept = [a for a in old_dossier["route_assessments"]
            if a["route_id"] != "route-demo-old"]
    new_assessment = copy.deepcopy(kept[0])
    new_assessment.update(
        route_id="route-demo-new", review_status="deep-reviewed",
        evidence=[{"locator": "lecture-01.pdf p.1",
                   "checksum": changed_basis["material_checksums"]["route-demo-new"]}])
    replacement["route_assessments"] = kept + [new_assessment]
    revision["material_synthesis"] = replacement

    revision_file = tmp_path / "l04-revision.yaml"
    write_yaml(revision_file, revision)
    assert revision_file.stat().st_size < 12288
    before = {p.name for p in (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")}
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert sorted(report["routes_added"]) == ["route-demo-new"]
    assert sorted(report["routes_removed"]) == ["route-demo-old"]
    assert report["routes_updated"] == ["route-demo-book"]
    unit_diff = report["units"]["unit-demo-l01"]
    assert unit_diff["triage_after"] == {"required-now": 2, "helpful-now": 1}
    assert unit_diff["learner_state_changes"] == {}
    assert unit_diff["learner_state_preserved"]["stage-demo-intro"] == [
        "status", "working_note", "attachments", "source_feedback", "runtime_review", "completed"]
    assert report["synthesis"]["unit-demo-l01"]["after"]["fresh"] is True
    assert report["semantic_ack_required"] == []

    from gateway_helpers import file_sha256
    report_file = tmp_path / "acceptance-review.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", file_sha256(revision_file),
                      "--review-report", str(report_file))
    assert applied.returncode == 0, applied.stderr
    response = json.loads(applied.stdout)
    assert response["ok"] is True
    after = {p.name for p in (mini_repo / "operations" / "transactions").glob("transaction-*.yaml")}
    assert len(after - before) == 1
    from learning_os.loader import load_repo
    live_map = load_repo(mini_repo).module_source_maps["module-demo"]
    live_ids = sorted(r.get("id") for s in live_map["sources"]
                      for r in s["unit_routes"])
    assert live_ids == ["route-demo-book", "route-demo-new", "route-demo-sup"]


def test_plan_edit_context_audit_reports_shape(mini_repo):
    """The deterministic audit names counts, triage gaps and freshness."""
    import json

    from repo_builders import run_los

    _compact_setup(mini_repo)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01", "--audit")
    assert proc.returncode == 0, proc.stderr
    audit = json.loads(proc.stdout)["unit_audit"]
    assert audit["routes"] == 1
    assert audit["routes_by_scope"] == {"current": 1}
    assert audit["synthesis"]["fresh"] is True
    assert audit["synthesis"]["deep_reviewed"] == 1
    assert audit["unplaced_routes"] == ["route-demo-book"]
    assert audit["current_or_prerequisite_unplaced"] == ["route-demo-book"]
    assert audit["exact_routes_with_unresolved_siblings"] == []


def test_reviewed_apply_refuses_changed_bytes(mini_repo, tmp_path):
    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    revision_file = tmp_path / "l04-revision.yaml"
    write_yaml(revision_file, _compact_revision(mini_repo))
    from gateway_helpers import file_sha256
    sha = file_sha256(revision_file)
    revision_file.write_text(
        revision_file.read_text(encoding="utf-8") + "\n# edited after review\n",
        encoding="utf-8",
    )
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01",
                      "--file", str(revision_file),
                      "--apply-reviewed-sha256", sha)
    assert applied.returncode == 2
    assert "changed since --check" in applied.stderr


def _reviewed_fixture(mini_repo, tmp_path, *, structural=False):
    from repo_builders import run_los, write_yaml

    _compact_setup(mini_repo)
    revision = _compact_revision(mini_repo, route_changes={"update": [{
        "route_id": "route-demo-book", "fields": {"angle": "Reviewed precise explanation."}}]})
    command, target = "unit-plan-revise", "unit-demo-l01"
    if structural:
        import copy

        from learning_os.loader import load_repo

        repo = load_repo(mini_repo)
        source_map = copy.deepcopy(repo.module_source_maps["module-demo"])
        source_map["sources"][0]["unit_routes"][0]["angle"] = "Reviewed precise explanation."
        revision = {"module_id": "module-demo", "plan_contract": _plan_contract(_audit(mini_repo)),
                    "source_map": source_map, "units": [{"unit": repo.units[target].data}]}
        command, target = "module-plan-import", "module-demo"
    revision_file = tmp_path / "revision.yaml"
    write_yaml(revision_file, revision)
    checked = run_los(mini_repo, command, target, "--file", str(revision_file), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    report_file = tmp_path / "review.json"
    report_file.write_text(checked.stdout, encoding="utf-8")
    apply_args = (command, target, "--file", str(revision_file),
                  "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                  "--review-report", str(report_file))
    return report, report_file, revision_file, apply_args


@pytest.mark.parametrize("structural", [False, True])
def test_reviewed_request_retries_exactly_once(mini_repo, tmp_path, structural):
    from repo_builders import run_los

    report, _, _, args = _reviewed_fixture(mini_repo, tmp_path, structural=structural)
    first = run_los(mini_repo, *args)
    assert first.returncode == 0, first.stdout + first.stderr
    second = run_los(mini_repo, *args)
    assert second.returncode == 0, second.stdout + second.stderr
    one, two = json.loads(first.stdout), json.loads(second.stdout)
    assert two["replayed"] is True
    assert two["transaction_id"] == one["transaction_id"]
    assert one["request_id"] == report["gateway_envelope"]["request_id"]
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 1


@pytest.mark.parametrize("structural", [False, True])
def test_reviewed_request_refuses_intervening_changes(mini_repo, tmp_path, structural):
    from repo_builders import run_los

    from learning_os.fingerprint import canonical_fingerprint

    _, _, _, args = _reviewed_fixture(mini_repo, tmp_path, structural=structural)
    (mini_repo / "work/inbox/intervening.md").write_text("New learner input.\n", encoding="utf-8")
    before = canonical_fingerprint(mini_repo)
    refused = run_los(mini_repo, *args)
    assert refused.returncode != 0
    assert "STALE_SNAPSHOT" in refused.stdout
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))


def test_reviewed_apply_uses_only_the_verified_read(mini_repo, tmp_path, monkeypatch):
    import los
    from learning_os.commands import module

    _, _, revision_file, args = _reviewed_fixture(mini_repo, tmp_path)
    original = module._read_content_bound_file
    calls = []

    def swapped(path, *a, **kw):
        result = original(path, *a, **kw)
        if Path(path) == revision_file:
            calls.append(path)
            revision_file.write_text("unit_id: not-the-reviewed-unit\n", encoding="utf-8")
        return result

    monkeypatch.setattr(module, "_read_content_bound_file", swapped)
    namespace = los.build_parser().parse_args(["--root", str(mini_repo), *args])
    assert namespace.func(namespace) == 0
    assert len(calls) == 1
    from learning_os.loader import load_repo
    route = load_repo(mini_repo).module_source_maps["module-demo"]["sources"][0]["unit_routes"][0]
    assert route["angle"] == "Reviewed precise explanation."


def test_removed_stage_is_refused_even_with_acknowledgment(mini_repo, tmp_path):
    from repo_builders import run_los, write_yaml

    _acceptance_setup(mini_repo)
    final_map = _live_study_map()
    final_map["stages"].pop()
    revision = _compact_revision(mini_repo, study_map=final_map, acknowledgments=[{
        "kind": "learner-state", "target": "unit-demo-l01", "reason": "Attempt to delete stage."}])
    path = tmp_path / "drop.yaml"
    write_yaml(path, revision)
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01", "--file", str(path), "--check")
    assert checked.returncode != 0
    assert "learner-state preservation" in checked.stderr
    assert "stage-demo-drill removed" in checked.stderr


@pytest.mark.parametrize("change", ["remove", "replace", "duplicate", "move"])
def test_resource_evidence_preservation_is_per_stage_and_occurrence(change):
    import copy

    from learning_os.commands.module import _unit_semantic_diff

    before = _live_study_map()
    resource = before["stages"][0]["resources"][0]
    resource["independent_evidence"] = {"reviewed_by": "operator"}
    if change == "duplicate":
        before["stages"][0]["resources"].append(copy.deepcopy(resource))
    after = copy.deepcopy(before)
    if change == "replace":
        after["stages"][0]["resources"][0]["independent_evidence"] = {}
    else:
        removed = after["stages"][0]["resources"].pop(0)
        if change == "move":
            after["stages"][1]["resources"].append(removed)
    diff = _unit_semantic_diff({}, {}, before, after)
    assert diff["destructive_learner_changes"]
    assert diff["resource_learner_changes"]


@pytest.mark.parametrize("change", ["new", "depth", "triage", "duplicate-placement", "unchanged"])
def test_advanced_promotion_uses_staged_routes_and_every_placement(change):
    import copy

    from learning_os.commands.module import _unit_semantic_diff

    route = _sliced_route("route-demo-book", "lecture-01.pdf")
    route["depth"] = "advanced-reference"
    after_map = {"sources": [{"source_id": "source-demo-book", "unit_routes": [route]}]}
    before_map = copy.deepcopy(after_map)
    after = _live_study_map()
    before = copy.deepcopy(after)
    if change == "new":
        before_map["sources"][0]["unit_routes"] = []
        before["stages"][0]["resources"] = []
    elif change == "depth":
        before_map["sources"][0]["unit_routes"][0]["depth"] = "course-aligned"
    elif change in {"triage", "duplicate-placement"}:
        before["stages"][0]["resources"][0]["scope_triage"] = "reference-only"
    if change == "duplicate-placement":
        extra = copy.deepcopy(after["stages"][0]["resources"][0])
        extra["scope_triage"] = "reference-only"
        after["stages"][1]["resources"].append(extra)
    diff = _unit_semantic_diff(before_map, after_map, before, after)
    assert diff["promoted_advanced_reference"] == ([] if change == "unchanged" else ["route-demo-book"])


@pytest.mark.parametrize("damage", ["missing-manifest", "wrong-unit", "wrong-request", "wrong-hash", "wrong-artifacts", "unsafe-path", "malformed-report", "missing-hash"])
def test_receipt_verifier_fails_closed(mini_repo, tmp_path, damage):
    import subprocess
    import sys

    from repo_builders import run_los

    report, report_file, _, args = _reviewed_fixture(mini_repo, tmp_path)
    applied = run_los(mini_repo, *args)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    response = json.loads(applied.stdout)
    unit = "unit-demo-l01"
    if damage == "missing-manifest":
        (mini_repo / "generated/manifest.json").unlink()
    elif damage == "wrong-unit":
        unit = "unit-demo-l02"
    elif damage == "wrong-request":
        report["gateway_envelope"]["request_id"] = "request-another"
    elif damage == "wrong-hash":
        key = next(iter(report["expected_write_sha256"]))
        report["expected_write_sha256"][key] = "0" * 64
    elif damage == "wrong-artifacts":
        report["commit_artifact_ids"].append("unit-unrelated")
    elif damage == "malformed-report":
        report["gateway_envelope"]["schema_version"] = "invalid"
    elif damage == "missing-hash":
        report["expected_write_sha256"] = {}
    elif damage == "unsafe-path":
        path = mini_repo / response["receipt_path"]
        receipt = yaml.safe_load(path.read_text())
        receipt["writes"][0]["path"] = "../outside.yaml"
        path.write_text(yaml.safe_dump(receipt), encoding="utf-8")
    report_file.write_text(json.dumps(report), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(REPO_ROOT / "tools/verify_plan_receipt.py"),
                           "--root", str(mini_repo), "--receipt", response["receipt_path"],
                           "--unit", unit, "--report", str(report_file)], capture_output=True, text=True)
    assert proc.returncode != 0, proc.stdout
    assert "Traceback" not in proc.stderr


def test_make_entrypoints_parse(repo_root):
    import subprocess

    # "setup" carries shell conditionals (stale-venv recovery, JF-01):
    # a quoting slip breaks every fresh clone, so it parses here.
    for target in ("help", "plan-check", "system-check", "setup", "setup-lean",
                   "check-python"):
        result = subprocess.run(["make", "-n", target], cwd=repo_root, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_setup_lean_overrides_no_pip_environment_option(repo_root):
    import re
    import subprocess

    # make exports a command-line override into every recipe's environment,
    # and pip reads PIP_<OPTION> variables as option defaults. The first
    # setup-lean passed PIP_EDITABLE=., so `pip install --upgrade pip` and
    # pip's own build-dependency install also installed `-e .`, and every
    # fresh clone failed. `make -n` parses fine either way, hence this check.
    result = subprocess.run(["make", "-n", "setup-lean"], cwd=repo_root,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not re.search(r"\bPIP_[A-Z_]+=", result.stdout), result.stdout


def test_check_python_refuses_an_unusable_interpreter(repo_root):
    import subprocess

    # F-s13-verify-01: a bogus PYTHON must fail in the viability gate,
    # before `setup` may touch the existing .venv. The gate itself never
    # writes, so this runs against the repo under test with no fixture.
    result = subprocess.run(["make", "check-python", "PYTHON=python9.9-nonexistent"],
                            cwd=repo_root, capture_output=True, text=True)
    assert result.returncode != 0
    assert "refusing to touch" in result.stdout + result.stderr


def test_check_python_accepts_the_running_interpreter(repo_root):
    import subprocess
    import sys

    result = subprocess.run(["make", "check-python", f"PYTHON={sys.executable}"],
                            cwd=repo_root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout


def test_reviewed_apply_rolls_back_all_writes_on_publish_failure(mini_repo, tmp_path, monkeypatch):
    import los
    from learning_os.commands import support
    from learning_os.fingerprint import canonical_fingerprint

    _, _, _, args = _reviewed_fixture(mini_repo, tmp_path)
    before = canonical_fingerprint(mini_repo)
    publish = support._publish_repo
    calls = []

    def fail_once(repo):
        calls.append(repo)
        if len(calls) == 1:
            raise OSError("injected projection failure")
        return publish(repo)

    monkeypatch.setattr(support, "_publish_repo", fail_once)
    namespace = los.build_parser().parse_args(["--root", str(mini_repo), *args])
    assert namespace.func(namespace) != 0
    assert canonical_fingerprint(mini_repo) == before
    assert not list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))
    # Retrying the same reviewed request after a proven rollback is safe.
    assert namespace.func(namespace) == 0
    assert len(list((mini_repo / "operations/transactions").glob("transaction-*.yaml"))) == 1


def test_route_only_coverage_revision_stamps_actual_artifact_owners(mini_repo, tmp_path):
    import copy

    from repo_builders import run_los, write_yaml

    from learning_os.commands.module import _staged_shadow
    from learning_os.material_synthesis import current_unit_material_basis
    from learning_os.revisions import load_revisions
    from learning_os.semantics.lineage import load_ledger

    good = _compact_setup(mini_repo)
    map_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    staged = yaml.safe_load(map_path.read_text())
    covers = ["knowledge-demo-expectation", "knowledge-demo-outcomes"]
    staged["sources"][0]["unit_routes"][0]["covers"] = covers
    with _staged_shadow(mini_repo, {map_path: yaml.safe_dump(staged, sort_keys=False)}) as shadow:
        basis = current_unit_material_basis(shadow, "unit-demo-l01")
    dossier = copy.deepcopy(good)
    dossier["basis"] = {**basis, "ai_provenance": good["basis"]["ai_provenance"]}
    revision = _compact_revision(mini_repo,
        route_changes={"update": [{"route_id": "route-demo-book", "fields": {"covers": covers}}]},
        material_synthesis=dossier,
        claim_evidence=[{"claim_id": "covers:route-demo-book",
                         "evidence": [{"kind": "route-locator", "ref": "lecture-01.pdf"}]}])
    file = tmp_path / "coverage.yaml"
    write_yaml(file, revision)
    checked = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01", "--file", str(file), "--check")
    assert checked.returncode == 0, checked.stderr
    report = json.loads(checked.stdout)
    assert "unit-demo-l01" not in report["expected_revisions"]
    saved = tmp_path / "coverage-report.json"
    saved.write_text(checked.stdout, encoding="utf-8")
    applied = run_los(mini_repo, "unit-plan-revise", "unit-demo-l01", "--file", str(file),
                      "--apply-reviewed-sha256", report["reviewed_file_sha256"],
                      "--review-report", str(saved))
    assert applied.returncode == 0, applied.stdout + applied.stderr
    claim = load_ledger(mini_repo)["covers:route-demo-book"]
    revisions = load_revisions(mini_repo)
    reads = dict(claim.derived_from.revisions)
    assert reads["unit-demo-l01"] == revisions.get("unit-demo-l01", 0) == 0
    assert reads["module-demo"] == revisions["module-demo"] == 1
