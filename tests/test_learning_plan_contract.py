"""One plan template owns every active creation boundary."""

from __future__ import annotations

import json

import yaml

from learning_os.contracts import build_plan_template, validate_contract
from learning_os.loader import load_repo


SHARED_PLAN_SCHEMA = "https://learningos.local/schema/learning-plan-v1"


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
