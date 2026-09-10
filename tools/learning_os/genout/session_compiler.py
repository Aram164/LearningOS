"""Small, deterministic session proposals with explicit feasibility failures."""

from __future__ import annotations

import copy
import json
import math

from ..contracts.json_schema import validate_contract
from ..learning_runtime import (
    RuntimeInputError,
    requirement_fingerprint,
    requirement_stage,
    runtime_path,
)
from ..loader import Repo
from ..materials_resolution import project_material_resource
from .learner_interpreter import _collect_and_interpret
from .learning_runtime import _collect_requirements


def _resource_available(repo: Repo, resource: dict) -> bool:
    projected = project_material_resource(repo, resource)
    if "material_exists" in projected:
        return projected["material_exists"] is True
    path = resource.get("vault_path")
    if path and not path.startswith("material://"):
        try:
            return runtime_path(repo.root, repo.root / path).is_file()
        except (RuntimeInputError, OSError):
            return False
    # A URL or prose locator alone is not evidence of accessibility.
    return False


def compile_session(repo: Repo, req: dict, interpretation: dict, context: dict | None = None) -> dict:
    context = {} if context is None else context
    validate_contract(repo.root, "session-context.schema.json", context)
    _, _, stage = requirement_stage(repo, req)
    status = interpretation.get("status", "unseen")
    if status not in {"unseen", "uncertain", "fragile", "demonstrated"}:
        raise RuntimeInputError(f"unknown learner interpretation: {status}")
    budget = context.get("available_minutes")
    if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget <= 0):
        raise RuntimeInputError("available_minutes must be a positive number")
    unavailable = set(context.get("unavailable_resources", []))
    durations = context.get("resource_minutes", {})
    if any(not math.isfinite(value) for value in durations.values()):
        raise RuntimeInputError("resource duration estimates must be finite")
    rejected = []
    eligible = []
    for resource in stage.get("resources", []):
        rid = resource.get("route_id")
        reason = None
        if not rid:
            reason = "resource has no stable route identity"
        elif resource.get("scope_triage") in {"reference-only", "deferred", "out-of-scope"}:
            reason = "resource is outside the current study scope"
        elif resource.get("affordance") not in {"intervention", "evidence", "mixed"}:
            reason = "no suitable intervention/evidence affordance is declared"
        elif rid in unavailable or not _resource_available(repo, resource):
            reason = "exact resource access is unavailable or unverified"
        elif budget is not None and (
                isinstance(durations.get(rid), bool)
                or not isinstance(durations.get(rid), (int, float))
                or durations[rid] <= 0):
            reason = "time budget is finite but this resource has no positive duration estimate"
        if reason:
            rejected.append({"resource_id": rid or "unidentified", "reason": reason})
        else:
            eligible.append(resource)
    # Preserve course priority before original authored order. No numeric
    # pedagogical score and no source coverage treated as recommendation.
    eligible.sort(key=lambda r: r.get("scope_triage") != "required-now")
    evidence = [r for r in eligible if r["affordance"] == "evidence"]
    intervention = [r for r in eligible if r["affordance"] == ("mixed" if status == "fragile" else "intervention")]
    if not intervention:
        intervention = [r for r in eligible if r["affordance"] == "mixed"]
    blockers = []
    selected = []
    if status != "demonstrated":
        if context.get("failed_prerequisites"):
            blockers.append("prerequisite failure requires a reviewed repair before target practice")
        if not evidence:
            blockers.append("no accessible, in-scope independent evidence activity")
        if not blockers:
            # Consider alternatives when the preferred pair cannot fit. A
            # finite budget with missing durations never becomes unconstrained.
            candidates = [[a, b] for a in intervention for b in evidence]
            if not intervention:
                candidates = [[b] for b in evidence]
            for candidate in candidates:
                if budget is None or sum(durations[r["route_id"]] for r in candidate) <= budget:
                    selected = candidate
                    break
            if not selected:
                blockers.append("no evidence-producing candidate fits the available time")
    steps = []
    for resource in selected:
        intent = "evidence" if resource["affordance"] == "evidence" else "intervention"
        role = "independent evidence" if intent == "evidence" else (
            "guided practice" if resource["affordance"] == "mixed" else "explanation")
        steps.append({
            "resource_id": resource["route_id"], "role": role, "intent": intent,
            "reason": ("obtain the target evidence under the declared conditions without assistance"
                       if intent == "evidence" else f"address the current {status} evidence state"),
        })
    selected_ids = {step["resource_id"] for step in steps}
    for resource in eligible:
        if resource["route_id"] not in selected_ids:
            reason = ("target evidence already demonstrated" if status == "demonstrated" else
                      "no feasible target plan" if blockers else
                      "same-role alternative; required-now priority, time feasibility, and authored order selected another route")
            rejected.append({"resource_id": resource["route_id"], "reason": reason})
    session = {
        "target_requirement_id": req["id"],
        "requirement_sha256": requirement_fingerprint(req),
        "source_stage": req["source_stage"],
        "current_status": status,
        "evidence_ids": interpretation.get("evidence_ids", []),
        "evidence_conditions": req.get("conditions", []),
        "evidence_spec": req["evidence_spec"],
        "plan_status": "satisfied" if status == "demonstrated" else "blocked" if blockers else "ready",
        "blockers": blockers,
        "steps": steps,
        "rejected_alternatives": rejected,
        "assumptions": [
            "authored affordances are candidate annotations; activity suitability still needs learner-facing review",
            "no prerequisite failure has been reported" if not context.get("failed_prerequisites") else "prerequisite assumption invalidated",
            "no time budget was supplied" if budget is None else f"available time: {budget} minutes; supplied resource duration estimates are assumed",
        ],
        "replan_conditions": ["prerequisite-failure", "target-evidence-obtained-early", "selected-resource-unsuitable", "material-time-change", "target-changed"],
    }
    validate_contract(repo.root, "session-plan.schema.json", session)
    return session


def replan_session(repo: Repo, previous: dict, req: dict, interpretation: dict,
                   context: dict, event: str) -> dict:
    """Repair one proposal only after an explicit material execution event."""
    validate_contract(repo.root, "session-plan.schema.json", previous)
    validate_contract(repo.root, "session-context.schema.json", context)
    if req["id"] == previous["target_requirement_id"] and req["source_stage"] != previous["source_stage"]:
        raise RuntimeInputError("previous proposal belongs to a different stage")
    if event not in {"minor-mistake", "hesitation", "hint-request", *previous["replan_conditions"]}:
        raise RuntimeInputError(f"unknown replan event: {event}")
    if req["id"] != previous["target_requirement_id"] and event != "target-changed":
        raise RuntimeInputError("a different requirement requires an explicit target-changed event")
    if event in {"minor-mistake", "hesitation", "hint-request"}:
        if previous["requirement_sha256"] != requirement_fingerprint(req):
            raise RuntimeInputError("requirement definition changed; an explicit material replan is required")
        _, _, stage = requirement_stage(repo, req)
        resources = {resource.get("route_id"): resource for resource in stage.get("resources", [])}
        for step in previous["steps"]:
            resource = resources.get(step["resource_id"])
            if (resource is None or resource.get("scope_triage") in {"reference-only", "deferred", "out-of-scope"}
                    or not _resource_available(repo, resource)
                    or (step["intent"] == "evidence" and resource.get("affordance") != "evidence")
                    or (step["intent"] == "intervention" and resource.get("affordance") not in {"intervention", "mixed"})):
                raise RuntimeInputError("previous steps are no longer eligible; an explicit material replan is required")
        current_status = interpretation.get("status", "unseen")
        if previous["plan_status"] == "satisfied" and current_status != "demonstrated":
            raise RuntimeInputError("current evidence does not support the previous completion claim")
        if previous["plan_status"] == "ready" and not any(step["intent"] == "evidence" for step in previous["steps"]):
            raise RuntimeInputError("previous ready proposal has no independent evidence step")
        result = copy.deepcopy(previous)
        result["current_status"] = current_status
        result["evidence_ids"] = interpretation.get("evidence_ids", [])
        action = "none"
    else:
        if event == "target-evidence-obtained-early" and interpretation.get("status") != "demonstrated":
            raise RuntimeInputError("early completion requires demonstrated target evidence")
        if event == "prerequisite-failure" and not context.get("failed_prerequisites"):
            raise RuntimeInputError("prerequisite failure must identify the invalidated prerequisite")
        if event == "selected-resource-unsuitable" and not (
                set(context.get("unavailable_resources", [])) & {s["resource_id"] for s in previous["steps"]}):
            raise RuntimeInputError("resource failure must identify a selected resource")
        if event == "material-time-change" and "available_minutes" not in context:
            raise RuntimeInputError("time change must supply the new available_minutes")
        result = compile_session(repo, req, interpretation, context)
        action = "session" if event == "target-changed" else "local"
    result["replan"] = {"action": action, "reason": event}
    validate_contract(repo.root, "session-plan.schema.json", result)
    return result


def _compile_sessions(repo: Repo) -> list[dict]:
    requirements = _collect_requirements(repo)
    interpretations = _collect_and_interpret(repo)
    return [compile_session(repo, req, interpretations.get(req["id"], {})) for req in requirements]


def build_compiled_sessions_json(repo: Repo, generated_at: str) -> str:
    output = {
        "_generated": {"generated_at": generated_at, "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py"},
        "sessions": _compile_sessions(repo),
    }
    validate_contract(repo.root, "compiled-sessions.schema.json", output)
    return json.dumps(output, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def build_compiled_sessions_md(repo: Repo) -> str:
    lines = ["# Session proposals", "", "> GENERATED — rebuild from authored inputs; do not edit.", ""]
    for session in _compile_sessions(repo):
        lines += [f"## {session['target_requirement_id']}",
                  f"Evidence: {session['current_status']}. Proposal: {session['plan_status']}."]
        if session["plan_status"] == "blocked":
            lines += [f"- Blocked: {reason}" for reason in session["blockers"]]
        elif session["plan_status"] == "satisfied":
            lines.append("The recorded evidence meets this target's conditions; no further steps proposed.")
        lines += [f"- {s['resource_id']} — {s['role']}: {s['reason']}" for s in session["steps"]]
        lines += ["", "Required evidence: " + ", ".join(session["evidence_spec"]),
                  "Conditions: " + ", ".join(session["evidence_conditions"]),
                  "Evidence IDs: " + (", ".join(session["evidence_ids"]) or "none"), "", "### Not selected"]
        lines += [f"- {r['resource_id']}: {r['reason']}" for r in session["rejected_alternatives"]]
        lines += ["", "### Assumptions", *[f"- {a}" for a in session["assumptions"]],
                  "", "Replan on: " + ", ".join(session["replan_conditions"]), ""]
    if len(lines) == 4:
        lines.append("No runtime requirements are configured.")
    return "\n".join(lines) + "\n"
