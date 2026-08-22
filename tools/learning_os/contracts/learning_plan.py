"""One authored-plan template shared by curriculum and Job boundaries."""

from __future__ import annotations

import re
from collections.abc import Mapping

PLAN_TEMPLATE_VERSION = 1
PLAN_PROFILES = frozenset({"curriculum", "job"})


class PlanTemplateError(ValueError):
    """An authoring path attempted to use a legacy or drifting plan shape."""


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _trimmed_list(value: object) -> object:
    if not isinstance(value, list):
        return value
    return [_trim(item) for item in value]


def _slug_id(value: object, prefix: str) -> str:
    raw = str(value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    slug = slug[:60].rstrip("-")
    return f"{prefix}-{slug}" if slug and not slug.startswith(f"{prefix}-") else slug


def normalise_resource(value: object) -> object:
    """Canonicalise the one resource vocabulary used by every plan profile."""
    if not isinstance(value, Mapping):
        return value
    result: dict = {}
    fields = (
        "kind", "label", "id", "source_id", "locator", "url", "vault_path",
        "scope_triage",
    )
    for field in fields:
        if field not in value:
            continue
        normalised = _trim(value[field])
        if normalised not in (None, ""):
            result[field] = normalised
    return result


def _normalise_job_context(value: object) -> object:
    if value is None:
        return {
            "mental_models": [],
            "read_only_anchor": "",
            "component": [],
            "verified_against": "",
        }
    if not isinstance(value, Mapping):
        return value
    raw_models = value.get("mental_models", [])
    models = (
        [
            {"label": _trim(raw.get("label")), "text": _trim(raw.get("text"))}
            if isinstance(raw, Mapping) else raw
            for raw in raw_models
        ]
        if isinstance(raw_models, list) else raw_models
    )
    return {
        "mental_models": models,
        "read_only_anchor": _trim(value.get("read_only_anchor", "")),
        "component": _trimmed_list(value.get("component", [])),
        "verified_against": _trim(value.get("verified_against", "")),
    }


def normalise_job_stage(value: object, plan_id: str, index: int) -> object:
    """Expand a Job stage draft into the canonical plan-template stage."""
    if not isinstance(value, Mapping):
        return value
    number = value.get("number", index)
    title = _trim(value.get("title", ""))
    stage_id = _trim(value.get("id", ""))
    if not stage_id and isinstance(title, str) and title:
        stage_id = _slug_id(f"{plan_id}-{number}-{title}", "stage")

    raw_resources = value.get("resources", [])
    resources = (
        [normalise_resource(resource) for resource in raw_resources]
        if isinstance(raw_resources, list) else raw_resources
    )
    resource_link = _trim(value.get("resource_link", ""))
    if isinstance(resource_link, str) and resource_link and resources == []:
        label = f"Learning material for {title or f'stage {number}'}"
        resources = [{
            "kind": "read",
            "label": label,
            **({"url": resource_link} if resource_link.startswith(("http://", "https://"))
               else {"vault_path": resource_link}),
            "scope_triage": "required-now",
        }]

    objective = _trim(value.get("objective", ""))
    if not objective and isinstance(title, str) and title:
        objective = f"Build working fluency in {title}."
    done_when = _trimmed_list(value.get("done_when", []))
    if done_when == [] and isinstance(title, str) and title:
        done_when = [f"Explain and apply {title} without notes."]

    result = {
        "id": stage_id,
        "number": number,
        "title": title,
        "status": _trim(value.get("status") or "pending"),
        "objective": objective,
        "done_when": done_when,
        "estimate_minutes": value.get("estimate_minutes", 90),
        "exam_critical": value.get("exam_critical") is True,
        "concepts": _trimmed_list(value.get("concepts", [])),
        "scope_triage": _trim(value.get("scope_triage") or "required-now"),
        "resources": resources,
        "attachments": value.get("attachments", []),
        "source_feedback": value.get("source_feedback", []),
        "job_context": _normalise_job_context(
            value.get("job_context", {
                "read_only_anchor": value.get("read_only_anchor", ""),
            })
        ),
    }
    if result["estimate_minutes"] is None:
        result.pop("estimate_minutes")
    return result


def current_template_problems(value: object, profile: str) -> list[str]:
    """Return drift errors every creation gateway must check before a write."""
    if profile not in PLAN_PROFILES:
        raise ValueError(f"unknown plan profile: {profile}")
    if not isinstance(value, Mapping):
        return ["plan must be a mapping"]
    problems: list[str] = []
    if value.get("plan_template_version") != PLAN_TEMPLATE_VERSION:
        problems.append(
            f"plan_template_version must be {PLAN_TEMPLATE_VERSION}; legacy plans are "
            "readable but cannot be used as creation templates"
        )
    stages = value.get("stages")
    if not isinstance(stages, list) or not stages:
        problems.append("stages must be a non-empty list")
        return problems
    numbers = [stage.get("number") if isinstance(stage, Mapping) else None for stage in stages]
    expected = list(range(1, len(stages) + 1))
    if numbers != expected:
        problems.append(
            f"stage numbers must be sequential in authored order: expected {expected}, got {numbers}"
        )
    return problems


def require_current_template(value: object, profile: str) -> None:
    problems = current_template_problems(value, profile)
    if problems:
        raise PlanTemplateError("; ".join(problems))


def build_plan_template(
    profile: str,
    *,
    title: str,
    unit_id: str | None = None,
    module_id: str | None = None,
) -> dict:
    """Build the official valid starting record for either plan boundary."""
    if profile not in PLAN_PROFILES:
        raise PlanTemplateError(f"unknown plan profile: {profile}")
    clean_title = str(title or "").strip()
    if not clean_title:
        raise PlanTemplateError("title must not be empty")
    stage_id = _slug_id(clean_title, "stage")
    if profile == "job":
        plan_id = _slug_id(clean_title, "job-plan")
        return {
            "type": "job-learning-plan",
            "schema_version": 2,
            "plan_template_version": PLAN_TEMPLATE_VERSION,
            "id": plan_id,
            "title": clean_title,
            "status": "ready",
            "horizon": "now",
            "cadence": "One stage per week",
            "outcome": f"Apply {clean_title} independently in a real task.",
            "stages": [normalise_job_stage({"title": clean_title}, plan_id, 1)],
        }

    if not unit_id or not module_id:
        raise PlanTemplateError("curriculum profile requires unit_id and module_id")
    unit_slug = str(unit_id).removeprefix("unit-")
    return {
        "id": f"study-map-{unit_slug}",
        "type": "study-map",
        "plan_template_version": PLAN_TEMPLATE_VERSION,
        "unit_id": unit_id,
        "status": "ready",
        "current_stage": stage_id,
        "source_plan": {"path": "replace-with-reviewed-plan.yaml", "provenance": "operator"},
        "detours": [],
        "stages": [{
            "id": stage_id,
            "number": 1,
            "title": clean_title,
            "status": "pending",
            "objective": f"Build working fluency in {clean_title}.",
            "done_when": [f"Explain and apply {clean_title} without notes."],
            "estimate_minutes": 90,
            "exam_critical": False,
            "concepts": [],
            "scope_triage": "required-now",
            "resources": [],
            "working_note": (
                f"curriculum/modules/{module_id}/units/{unit_id}/stages/"
                f"{stage_id}/notes.md"
            ),
            "attachments": [],
            "source_feedback": [],
        }],
        "shelving": {"state": "none"},
    }
