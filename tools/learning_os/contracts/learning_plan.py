"""The single authored study-map template used by every learning module."""

from __future__ import annotations

import re
from collections.abc import Mapping

PLAN_TEMPLATE_VERSION = 1
PLAN_PROFILES = frozenset({"curriculum"})


class PlanTemplateError(ValueError):
    """An authoring path attempted to use a legacy or drifting plan shape."""


def _slug_id(value: object, prefix: str) -> str:
    raw = str(value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    slug = slug[:60].rstrip("-")
    return f"{prefix}-{slug}" if slug and not slug.startswith(f"{prefix}-") else slug


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
    source_plan = value.get("source_plan")
    source_path = source_plan.get("path") if isinstance(source_plan, Mapping) else None
    if source_path == "replace-with-reviewed-plan.yaml":
        problems.append(
            "source_plan.path is still the template placeholder; name the reviewed plan"
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
    """Build the official schema-valid starting record for a learning module.

    Curriculum keeps an explicit source-plan placeholder so the missing review
    evidence is visible while authoring. The import gate refuses that sentinel;
    a starting template is not evidence that its placeholders were completed.
    """
    if profile not in PLAN_PROFILES:
        raise PlanTemplateError(f"unknown plan profile: {profile}")
    clean_title = str(title or "").strip()
    if not clean_title:
        raise PlanTemplateError("title must not be empty")
    stage_id = _slug_id(clean_title, "stage")
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
