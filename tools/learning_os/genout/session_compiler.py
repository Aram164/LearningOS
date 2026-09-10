"""Small, deterministic session proposals with explicit feasibility failures.

Fresh proposals select one intervention and one independent-evidence step from
the owning stage's eligible resources. Bounded repair covers two V0 cases and
nothing more: failed prerequisites prepend explicitly mapped repair steps
before the normal target pair, and an unsuitable selected resource is
structurally replaced by a same-intent alternative while unaffected steps are
preserved verbatim. Anything else is a feasibility failure, stated as a
blocker.
"""

from __future__ import annotations

import copy
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


def _check_context_numbers(context: dict) -> tuple[set, dict]:
    budget = context.get("available_minutes")
    if budget is not None and (isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget <= 0):
        raise RuntimeInputError("available_minutes must be a positive number")
    durations = context.get("resource_minutes", {})
    if any(not math.isfinite(value) for value in durations.values()):
        raise RuntimeInputError("resource duration estimates must be finite")
    return set(context.get("unavailable_resources", [])), durations


def _eligible_resources(repo: Repo, stage: dict, context: dict, unavailable: set, durations: dict, budget) -> tuple[list, list]:
    """Split stage resources into eligible and rejected with reasons."""
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
    return eligible, rejected


def _pools(eligible: list, status: str) -> tuple[list, list]:
    evidence = [r for r in eligible if r["affordance"] == "evidence"]
    intervention = [r for r in eligible if r["affordance"] == ("mixed" if status == "fragile" else "intervention")]
    if not intervention:
        intervention = [r for r in eligible if r["affordance"] == "mixed"]
    return intervention, evidence


def _step_for(resource: dict, status: str) -> dict:
    intent = "evidence" if resource["affordance"] == "evidence" else "intervention"
    role = "independent evidence" if intent == "evidence" else (
        "guided practice" if resource["affordance"] == "mixed" else "explanation")
    return {
        "resource_id": resource["route_id"], "role": role, "intent": intent,
        "reason": ("obtain the target evidence under the declared conditions without assistance"
                   if intent == "evidence" else f"address the current {status} evidence state"),
    }


def _fits(selected: list, budget, durations: dict) -> bool:
    if budget is None:
        return True
    return sum(durations[r["route_id"]] for r in selected) <= budget


def _assemble(root, req, interpretation, status, steps, rejected, blockers, eligible, context, budget, extra_assumptions=()) -> dict:
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
            *extra_assumptions,
        ],
        "replan_conditions": ["prerequisite-failure", "target-evidence-obtained-early", "selected-resource-unsuitable", "material-time-change", "target-changed"],
    }
    validate_contract(root, "session-plan.schema.json", session)
    return session


def compile_session(repo: Repo, req: dict, interpretation: dict, context: dict | None = None) -> dict:
    context = {} if context is None else context
    validate_contract(repo.root, "session-context.schema.json", context)
    _, _, stage = requirement_stage(repo, req)
    status = interpretation.get("status", "unseen")
    if status not in {"unseen", "uncertain", "fragile", "demonstrated"}:
        raise RuntimeInputError(f"unknown learner interpretation: {status}")
    budget = context.get("available_minutes")
    unavailable, durations = _check_context_numbers(context)
    eligible, rejected = _eligible_resources(repo, stage, context, unavailable, durations, budget)
    intervention, evidence = _pools(eligible, status)
    blockers = []
    selected: list[dict] = []
    failed = list(context.get("failed_prerequisites", []))
    repair_mode = status != "demonstrated" and bool(failed)
    if repair_mode:
        selected, blockers = _repair_with_prerequisites(
            repo, req, status, intervention, evidence, rejected, eligible, failed, budget, durations, context)
    elif status != "demonstrated":
        if not evidence:
            blockers.append("no accessible, in-scope independent evidence activity")
        if not blockers:
            # Consider alternatives when the preferred pair cannot fit. A
            # finite budget with missing durations never becomes unconstrained.
            candidates = [[a, b] for a in intervention for b in evidence]
            if not intervention:
                candidates = [[b] for b in evidence]
            for candidate in candidates:
                if _fits(candidate, budget, durations):
                    selected = candidate
                    break
            if not selected:
                blockers.append("no evidence-producing candidate fits the available time")
    if repair_mode and selected:
        steps = _repair_steps(selected, status)
        extra = ("bounded repair uses explicitly mapped repair resources; target evidence still required",)
    else:
        steps = [_step_for(resource, status) for resource in selected]
        extra = ()
    return _assemble(repo.root, req, interpretation, status, steps, rejected, blockers, eligible, context, budget,
                     extra_assumptions=extra)


def _repair_with_prerequisites(repo, req, status, intervention, evidence, rejected, eligible, failed, budget, durations, context):
    """Bounded prerequisite repair: explicitly mapped repair steps, then the target pair.

    The caller maps every failed prerequisite to an eligible intervention
    resource via ``prerequisite_repairs``. The compiler validates the mapping
    but never invents it: an unmapped, ineligible, or non-intervention repair
    resource is a feasibility failure, and a repair that leaves no target
    intervention is blocked rather than relabelled.
    """
    mapping = context.get("prerequisite_repairs", {}) or {}
    unmapped = [name for name in failed if name not in mapping]
    if unmapped:
        return [], [f"failed prerequisite(s) {', '.join(unmapped)} name no repair resource; "
                    "prerequisite repair needs an explicit prerequisite-to-resource mapping"]
    by_id = {resource["route_id"]: resource for resource in eligible}
    repairs: list[tuple[str, dict]] = []
    seen_routes: dict[str, list[str]] = {}
    for name in failed:
        rid = mapping[name]
        resource = by_id.get(rid)
        if resource is None:
            return [], [f"repair resource {rid} for failed prerequisite '{name}' is not eligible "
                        "(out of scope, inaccessible, or missing duration)"]
        if resource.get("affordance") not in {"intervention", "mixed"}:
            return [], [f"repair resource {rid} for failed prerequisite '{name}' is not an intervention resource"]
        seen_routes.setdefault(rid, []).append(name)
    for rid, names in seen_routes.items():
        repairs.append((", ".join(names), by_id[rid]))
    repair_ids = set(seen_routes)
    rest = [r for r in intervention if r["route_id"] not in repair_ids]
    if not evidence:
        return [], ["no accessible, in-scope independent evidence activity; prerequisite repair alone cannot produce target evidence"]
    if not rest:
        reserved = ", ".join(sorted(repair_ids))
        return [], [f"prerequisite repair reserves {reserved}; no target intervention remains"]
    target: list = []
    fixed = [resource for _, resource in repairs]
    for candidate in ([a, b] for a in rest for b in evidence):
        if _fits([*fixed, *candidate], budget, durations):
            target = candidate
            break
    if not target:
        return [], ["no evidence-producing candidate fits the available time after prerequisite repair"]
    return [{**resource, "_repair": names} for names, resource in repairs] + target, []


def _repair_steps(selected: list, status: str) -> list:
    steps = []
    for resource in selected:
        if resource.get("_repair"):
            steps.append({
                "resource_id": resource["route_id"], "role": "prerequisite repair",
                "intent": "intervention",
                "reason": f"repair failed prerequisite(s) ({resource['_repair']}) before target practice",
            })
        else:
            steps.append(_step_for(resource, status))
    return steps


def _structural_replacement(repo, previous: dict, req: dict, interpretation: dict,
                            context: dict, flagged: dict[str, str]) -> dict:
    """Replace flagged steps with same-intent alternatives; preserve the rest verbatim."""
    _, _, stage = requirement_stage(repo, req)
    status = interpretation.get("status", "unseen")
    budget = context.get("available_minutes")
    unavailable, durations = _check_context_numbers(context)
    eligible, rejected = _eligible_resources(repo, stage, context, unavailable, durations, budget)
    intervention, evidence = _pools(eligible, status)
    used = {s["resource_id"] for s in previous["steps"]} - set(flagged)
    repaired = []
    for step in previous["steps"]:
        if step["resource_id"] not in flagged:
            repaired.append(copy.deepcopy(step))
            continue
        pool = evidence if step["intent"] == "evidence" else intervention
        swap = next((r for r in pool if r["route_id"] not in used and r["route_id"] not in flagged), None)
        if swap is None:
            blockers = [f"no same-intent alternative for unsuitable step {step['resource_id']} ({flagged[step['resource_id']]})"]
            return _assemble(repo.root, req, interpretation, status, [], rejected, blockers, eligible, context, budget,
                             extra_assumptions=("no executable plan: structural repair failed, "
                                                "so the previous proposal is withdrawn rather than partially preserved",))
        used.add(swap["route_id"])
        new_step = _step_for(swap, status)
        new_step["reason"] = (f"structural replacement for {step['resource_id']}: {flagged[step['resource_id']]}")
        repaired.append(new_step)
    if budget is not None:
        try:
            total = sum(durations[s["resource_id"]] for s in repaired)
        except KeyError:
            return _assemble(repo.root, req, interpretation, status, [], rejected,
                             ["no evidence-producing candidate fits the available time after structural repair"],
                             eligible, context, budget)
        if total > budget:
            return _assemble(repo.root, req, interpretation, status, [], rejected,
                             ["no evidence-producing candidate fits the available time after structural repair"],
                             eligible, context, budget)
    return _assemble(repo.root, req, interpretation, status, repaired, rejected, [], eligible, context, budget,
                     extra_assumptions=("structural repair: unaffected steps preserved verbatim",))


def replan_session(repo: Repo, previous_packet: dict, req: dict, interpretation: dict,
                   context: dict, event: str, current_snapshot: str) -> dict:
    """Repair one proposal only after an explicit material execution event.

    The previous proposal travels as the full runtime-session-v1 packet it
    was issued in, never as a bare session: the replan is bound to the
    packet's originating snapshot and refused when the tree has moved on.
    """
    validate_contract(repo.root, "runtime-session.schema.json", previous_packet)
    try:
        previous = previous_packet["session"]
    except (TypeError, KeyError, AttributeError) as exc:
        raise RuntimeInputError("previous proposal must be a runtime-session-v1 packet") from exc
    if previous_packet.get("snapshot_id") != current_snapshot:
        raise RuntimeInputError(f"previous proposal is bound to snapshot {previous_packet.get('snapshot_id')}; "
                                "snapshot changed, propose a fresh session")
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
        if event != "target-changed" and previous["requirement_sha256"] != requirement_fingerprint(req):
            raise RuntimeInputError("requirement definition changed; previous proposal is bound to its definition snapshot")
        if event == "target-evidence-obtained-early" and interpretation.get("status") != "demonstrated":
            raise RuntimeInputError("early completion requires demonstrated target evidence")
        if event == "prerequisite-failure" and not context.get("failed_prerequisites"):
            raise RuntimeInputError("prerequisite failure must identify the invalidated prerequisite")
        if event == "selected-resource-unsuitable":
            step_ids = {s["resource_id"] for s in previous["steps"]}
            pedagogical = set(context.get("unsuitable_resources", [])) & step_ids
            access = set(context.get("unavailable_resources", [])) & step_ids
            if not pedagogical and not access:
                raise RuntimeInputError("resource failure must identify a selected resource via unsuitable_resources or unavailable_resources")
            flagged = {rid: "pedagogically unsuitable for this learner" for rid in pedagogical}
            for rid in access - set(flagged):
                flagged[rid] = "exact resource access failed"
            result = _structural_replacement(repo, previous, req, interpretation, context, flagged)
            result["replan"] = {"action": "local", "reason": event}
            validate_contract(repo.root, "session-plan.schema.json", result)
            return result
        if event == "material-time-change" and "available_minutes" not in context:
            raise RuntimeInputError("time change must supply the new available_minutes")
        result = compile_session(repo, req, interpretation, context)
        action = "session" if event == "target-changed" else "local"
    result["replan"] = {"action": action, "reason": event}
    validate_contract(repo.root, "session-plan.schema.json", result)
    return result
