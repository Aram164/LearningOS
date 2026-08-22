"""One plan template owns every active creation boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from learning_os.contracts import (
    build_plan_template,
    current_template_problems,
    validate_contract,
)
from learning_os.contracts.capability_catalog import query_definitions
from learning_os.loader import load_repo

SHARED_PLAN_SCHEMA = "https://learningos.local/schema/learning-plan-v1"


def _plan_template(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_root / "tools" / "los.py"), "--root", str(repo_root),
         "plan-template", *args],
        capture_output=True, text=True, timeout=120,
    )


def test_plan_profiles_reference_the_same_stage_contract(repo_root):
    schemas = repo_root / "system" / "schema"
    study = json.loads((schemas / "study-map.schema.json").read_text(encoding="utf-8"))
    job = json.loads((schemas / "job-plan.schema.json").read_text(encoding="utf-8"))
    study_ref = study["allOf"][0]["then"]["properties"]["stages"]["items"]["$ref"]
    job_ref = job["properties"]["stages"]["items"]["$ref"]
    assert study_ref.startswith(f"{SHARED_PLAN_SCHEMA}#/")
    assert job_ref.startswith(f"{SHARED_PLAN_SCHEMA}#/")


def test_official_plan_templates_are_schema_valid(repo_root):
    curriculum = build_plan_template(
        "curriculum",
        title="Example lecture",
        module_id="module-example",
        unit_id="unit-example-l01",
    )
    job = build_plan_template("job", title="Example job track")
    validate_contract(repo_root, "study-map.schema.json", curriculum)
    validate_contract(repo_root, "job-plan.schema.json", job)
    for plan in (curriculum, job):
        assert plan["plan_template_version"] == 1
        assert [stage["number"] for stage in plan["stages"]] == [1]
        assert "estimate_minutes" not in plan["stages"][0]


def test_curriculum_import_refuses_the_unreplaced_source_plan_placeholder():
    plan = build_plan_template(
        "curriculum",
        title="Example lecture",
        module_id="module-example",
        unit_id="unit-example-l01",
    )
    assert current_template_problems(plan, "curriculum") == [
        "source_plan.path is still the template placeholder; name the reviewed plan"
    ]


def test_every_active_curriculum_plan_uses_current_template(repo_root):
    repo = load_repo(repo_root)
    assert repo.study_maps
    for study_map in repo.study_maps.values():
        assert study_map.data["plan_template_version"] == 1, study_map.path
        stages = study_map.data["stages"]
        assert [stage["number"] for stage in stages] == list(range(1, len(stages) + 1))


def test_module_import_template_carries_current_plan_contract(repo_root):
    template = yaml.safe_load(
        (repo_root / "system" / "templates" / "module-plan-import.template.yaml")
        .read_text(encoding="utf-8")
    )
    assert template["plan_contract"]["version"] == 2
    assert template["plan_contract"]["plan_template_version"] == 1
    study_map = template["units"][0]["study_map"]
    validate_contract(repo_root, "study-map.schema.json", study_map)
    assert "estimate_minutes" not in study_map["stages"][0]


# --------------------------------------------------------------- reachability
#
# A creation standard that only a terminal can reach is not enforced on the
# surface people actually author from. These four pin the route the interface
# uses, so the template cannot quietly become CLI-only again.


def test_the_plan_template_is_a_declared_query_with_a_producer_schema(repo_root: Path):
    definition = query_definitions(repo_root)["plan.template"]
    assert definition.result == "plan-template-v1"
    assert definition.schema == "system/schema/plan-template.schema.json"
    assert (repo_root / definition.schema).is_file()

    import los
    from learning_os.contracts.payloads import subparsers

    parser = subparsers(los.build_parser()).get("plan-template")
    assert parser is not None, "the declared query has no executable CLI route"
    assert parser.get_default("func").__name__ == f"cmd_{definition.handler}"


@pytest.mark.parametrize(
    ("profile", "extra", "record_type"),
    [
        ("job", (), "job-learning-plan"),
        (
            "curriculum",
            ("--unit-id", "unit-example-l01", "--module-id", "module-example"),
            "study-map",
        ),
    ],
)
def test_the_query_answers_the_shape_it_declares(repo_root, profile, extra, record_type):
    result = _plan_template(repo_root, profile, "--title", "Example plan", "--json", *extra)
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    validate_contract(repo_root, "plan-template.schema.json", response)
    assert response["contract"] == "plan-template-v1"
    assert response["profile"] == profile
    assert response["plan"]["type"] == record_type
    # The envelope must not be able to claim a template version the record
    # itself does not carry — that divergence is the whole failure mode.
    assert response["plan_template_version"] == response["plan"]["plan_template_version"] == 1
    validate_contract(repo_root, response["schema"], response["plan"])


def test_json_and_yaml_answer_the_same_record(repo_root: Path):
    text = _plan_template(repo_root, "job", "--title", "Example plan")
    envelope = _plan_template(repo_root, "job", "--title", "Example plan", "--json")
    assert text.returncode == envelope.returncode == 0
    assert yaml.safe_load(text.stdout) == json.loads(envelope.stdout)["plan"]


def test_a_refused_query_reports_its_reason_as_json(repo_root: Path):
    """The interface reads stdout as JSON; a bare stderr line is invisible there."""
    result = _plan_template(repo_root, "curriculum", "--title", "Example plan", "--json")
    assert result.returncode == 2
    body = json.loads(result.stdout)
    assert body["ok"] is False
    assert "unit_id" in body["error"]
