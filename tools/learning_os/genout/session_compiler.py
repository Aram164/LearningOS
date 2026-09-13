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
    activity_fingerprint,
    collect_requirements,
    read_observations,
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


def _known_exposures(repo: Repo, context: dict) -> set[str]:
    """Explicit exposure reports and recorded attempts; opening a file is not a report."""
    observations = read_observations(repo, collect_requirements(repo))
    superseded = {obs["supersedes"] for obs in observations if obs.get("supersedes")}
    exposed = set(context.get("exposed_resources", []))
    exposed.update(obs["activity"] for obs in observations
                   if obs["id"] not in superseded and obs["activity"].startswith("route-"))
    return exposed


#: Shortfalls that no further study, review or download can clear, because the
#: activity is spent for this target: it was attempted, or its answers were
#: read. Only registering a new activity restores an assessment route.
_EXHAUSTING_SHORTFALLS = frozenset({"already-familiar", "solutions-seen"})

#: What would clear each recoverable shortfall, in the learner's terms.
_SHORTFALL_REMEDIES = {
    "unreviewed": "review its suitability for this target",
    "requirement-drift": "review it against the current requirement",
    "activity-drift": "review it again against the current activity bytes",
    "conditions-unverified": "review whether it can test the missing conditions",
    "assets-missing": "obtain the missing asset it needs",
}


def _evidence_shortfall(repo: Repo, resource: dict, req: dict,
                        exposed: set[str]) -> tuple[str, str] | None:
    """Suitability of content is separate from qualification of an actual attempt.

    Returns ``(code, reason)``. The reason is what the learner reads; the code
    is what ``_evidence_gap`` needs in order to tell a blockage that is waiting
    for work from one that is waiting for material that does not exist.
    """
    rid = resource["route_id"]
    conditions = set(req.get("conditions", []))
    if rid in exposed and "unfamiliar-example" in conditions:
        return ("already-familiar",
                "a previous attempt or explicit exposure report makes this activity familiar")
    if any(rid in _exposes_solutions(repo, {"route_id": source}) for source in exposed):
        return ("solutions-seen",
                "the learner reported exposure to this activity's solutions in an earlier session")
    if _missing_assets(repo, resource):
        return ("assets-missing",
                "assigned activity is not runnable in full: " + "; ".join(_asset_notes(repo, [resource])))
    review = resource.get("independent_evidence")
    if not isinstance(review, dict):
        return ("unreviewed",
                "assessment suitability has not been reviewed; available for practice")
    if review.get("requirement_sha256") != requirement_fingerprint(req):
        return ("requirement-drift",
                "suitability review is not bound to the current requirement; review again")
    fingerprint = activity_fingerprint(repo, resource)
    if fingerprint is None or review.get("activity_sha256") != fingerprint:
        return ("activity-drift",
                "activity content or scope differs from its suitability review; review again")
    missing = sorted(conditions - set(review.get("verified_conditions", [])))
    if missing:
        return ("conditions-unverified",
                "review does not establish an activity suitable for: " + ", ".join(missing))
    return None


def _evidence_gap(shortfalls: list[tuple[str, str]]) -> tuple[str, tuple[str, ...]]:
    """Why no assessment activity remains — and whether working will change it.

    ``no accessible, in-scope independent evidence activity`` was true of a
    stage that declares none, of one whose only review needs re-running, and of
    one where every reviewed activity has already been attempted. The first two
    are work; the third is a dead end that no amount of studying clears, and
    saying them in the same sentence sends the learner looking for a task that
    is not there. This is F04's lesson — state plainly when no repair exists
    rather than proposing one more round — applied on the evidence side, where
    it was missing: the CLT stage ships exactly two activities able to satisfy
    its two-distinct-unfamiliar-tasks criterion, so one honest assessment
    consumes the entire pool.
    """
    if not shortfalls:
        return "no accessible, in-scope independent evidence activity", ()
    codes = {code for _, code in shortfalls}
    if codes <= _EXHAUSTING_SHORTFALLS:
        return (
            "every reviewed assessment activity for this target is spent: "
            "already attempted, or its solutions already seen",
            ("no unfamiliar activity remains for this target, so it cannot be "
             "assessed again from the material registered now. Register a new "
             "activity for this target; repeating an earlier one cannot "
             "establish it, and waiting will not make one appear.",),
        )
    remedies = sorted({_SHORTFALL_REMEDIES[code] for code in codes
                       if code in _SHORTFALL_REMEDIES})
    notes = ("no assessment activity is admissible yet; what would clear it: "
             + "; ".join(remedies) + ".",) if remedies else ()
    spent = sorted(rid for rid, code in shortfalls if code in _EXHAUSTING_SHORTFALLS)
    if spent:
        notes = (*notes, "spent for this target and not reusable: " + ", ".join(spent) + ".")
    return "no accessible, in-scope independent evidence activity", notes


def _exposes_solutions(repo: Repo, resource: dict) -> set[str]:
    """Route ids whose answers this material hands over.

    Read from the owning route in the module source map, not from the stage
    resource. "This file contains the worked solutions to that task" is a fact
    about the material, so it belongs with the material and holds in every
    stage that routes to it — a stage-local copy would be one more place for
    the guard to be absent exactly where it matters.
    """
    route_id = resource.get("route_id")
    if not route_id:
        return set()
    declared = _routes_by_id(repo).get(str(route_id), {}).get("exposes_solutions_for")
    if not isinstance(declared, list):
        return set()
    return {str(value) for value in declared if str(value).strip()}


def _routes_by_id(repo: Repo) -> dict[str, dict]:
    """Every rich route in the repository, by its stable identity."""
    from ..routes import iter_route_references

    cached = getattr(repo, "_session_routes_by_id", None)
    if cached is None:
        cached = {ref.route_id: ref.route for ref in iter_route_references(repo)}
        try:
            repo._session_routes_by_id = cached
        except AttributeError:  # a Repo that refuses attributes still works
            pass
    return cached


def _route_sources(repo: Repo) -> dict[str, str]:
    """The source each route belongs to, by route id."""
    from ..routes import iter_route_references

    cached = getattr(repo, "_session_route_sources", None)
    if cached is None:
        cached = {ref.route_id: ref.source_id for ref in iter_route_references(repo)}
        try:
            repo._session_route_sources = cached
        except AttributeError:  # a Repo that refuses attributes still works
            pass
    return cached


def _same_source_answer_notes(repo: Repo, evidence_ids: list[str]) -> tuple[str, ...]:
    """Say when the answers to an assessment sit inside the same material.

    Route separation is a property of the map, not of the object in the
    learner's hands. Both CLT transfer tasks live in the Arbeitsbuch at
    physical pages 132 and 158; their answers are in that same book at 155 and
    161. `exposes_solutions_for` keeps them apart as routes and `_reveals`
    keeps them out of one proposal, but turning twenty pages is not a route
    transition and `_known_exposures` reports exposure rather than inferring
    it — so nothing downstream can notice. What the proposal can honestly do
    is say the answers are within arm's reach, before the attempt rather than
    after it.
    """
    sources = _route_sources(repo)
    routes = _routes_by_id(repo)
    notes = []
    for rid in evidence_ids:
        for other_id, other in sorted(routes.items()):
            declared = other.get("exposes_solutions_for")
            if not isinstance(declared, list) or rid not in declared or other_id == rid:
                continue
            if sources.get(other_id) != sources.get(rid) or sources.get(rid) is None:
                continue
            notes.append(
                f"the answers to {rid} are in the same material as the task "
                f"({other_id}); opening them is not observable, so report the "
                f"exposure yourself if you read them before the attempt is done")
    return tuple(dict.fromkeys(notes))


def _missing_assets(repo: Repo, resource: dict) -> list[dict]:
    """Assets the activity needs that are not registered and resolvable here.

    ``_resource_available`` answers "can he open the worksheet". This answers
    "can he do what the worksheet asks", and the two were the same answer:
    Blatt 4 Aufgabe 3(b) needs `International_Education_Costs.csv` and an
    `aufgabe3.py` template from Moodle, neither of which exists in the
    registered materials, and the proposal reported the route ready with
    Aufgabe 3 included and part (b) not excluded (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F06). The source map had
    already recorded the absence in prose; nothing carried it to the runtime.
    """
    route_id = resource.get("route_id")
    if not route_id:
        return []
    declared = _routes_by_id(repo).get(str(route_id), {}).get("requires_assets")
    if not isinstance(declared, list):
        return []
    missing = []
    for asset in declared:
        if not isinstance(asset, dict) or not asset.get("name"):
            continue
        uri = asset.get("material_uri")
        if isinstance(uri, str) and uri:
            probe = {"vault_path": uri, "route_id": route_id}
            if project_material_resource(repo, probe).get("material_exists") is True:
                continue
        missing.append(asset)
    return missing


def _asset_notes(repo: Repo, selected: list) -> tuple[str, ...]:
    """One line per selected activity that cannot be done in full."""
    notes = []
    for resource in selected:
        missing = _missing_assets(repo, resource)
        if not missing:
            continue
        for asset in missing:
            part = asset.get("needed_for")
            where = asset.get("obtain_from")
            notes.append(
                f"{resource['route_id']} needs {asset['name']}"
                + (f" for {part}" if part else "")
                + ", which is not registered locally"
                + (f" — get the exact file from {where}" if where else "")
                + ". Use only parts that do not require the missing asset; do not substitute "
                  "another dataset or template and call it the supplied assignment."
            )
    return tuple(notes)


def _reveals(repo: Repo, step: dict, evidence: dict) -> bool:
    """Whether reading ``step`` hands over the answers to ``evidence``.

    A session that explains with the worked solutions and then asks for
    unaided transfer on the very task those solutions answer is not measuring
    transfer. This is not hypothetical: rejecting the CLT lecture as unhelpful
    replaced it with UE6 — the official Blatt 4 solutions — while Blatt 4
    itself stayed on as the independent-evidence step, solutions and
    assessment in the same proposal (audit F03).
    """
    return evidence.get("route_id") in _exposes_solutions(repo, step)


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
        elif rid in context.get("unsuitable_resources", []):
            reason = "learner reported this resource pedagogically unsuitable"
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


def _pools(repo: Repo, req: dict, context: dict, eligible: list, status: str,
           rejected: list | None = None,
           shortfalls: list[tuple[str, str]] | None = None) -> tuple[list, list]:
    # Mixed resources are genuinely dual-use: they compete as evidence
    # alongside pure evidence, and as intervention per status below.
    #
    # The preference flips with status and the fallback never does. Something
    # that broke down after working is usually better served by guided
    # practice than by another explanation of what he already understood once,
    # so `fragile` asks for `mixed` first — but "prefer" is not "only". Both
    # branches used to fall back to `mixed`, which for `fragile` meant falling
    # back to the pool that had just come up empty, excluding every pure
    # explanation in the stage. The learner whose understanding had just
    # collapsed was then handed one more assessment and nothing to repair it
    # with (audit `synthetic-learner-2026-09-12`, F04).
    evidence = []
    exposed = _known_exposures(repo, context)
    for resource in eligible:
        if resource["affordance"] not in {"evidence", "mixed"}:
            continue
        shortfall = _evidence_shortfall(repo, resource, req, exposed)
        if shortfall is None:
            evidence.append(resource)
            continue
        code, reason = shortfall
        if shortfalls is not None:
            shortfalls.append((resource["route_id"], code))
        if rejected is not None:
            rejected.append({"resource_id": resource["route_id"], "reason": reason})
    preferred, fallback = (("mixed", "intervention") if status == "fragile"
                           else ("intervention", "mixed"))
    intervention = [r for r in eligible if r["affordance"] == preferred]
    if not intervention:
        intervention = [r for r in eligible if r["affordance"] == fallback]
    return intervention, evidence


def _step_for(resource: dict, status: str, *, as_evidence: bool = False) -> dict:
    intent = "evidence" if (resource["affordance"] == "evidence" or as_evidence) else "intervention"
    if intent == "evidence":
        role = "independent evidence"
        reason = ("reviewed prompt suitable for the target; record whether this actual attempt "
                  "was unfamiliar, uncued and unassisted — the content review does not establish those facts")
        # Who judged this prompt suitable, and when, is the thing the whole
        # gate rests on. The fingerprints below it prove the review still
        # describes these bytes; they cannot prove the judgment was right, and
        # nothing re-opens it while the bytes hold still. Name it, so a review
        # nobody would stand behind is visible at the moment it is relied on.
        review = resource.get("independent_evidence")
        if isinstance(review, dict) and review.get("reviewed_by"):
            when = review.get("reviewed_on")
            reason += (f". Admitted on a content review by {review['reviewed_by']}"
                       + (f" of {when}" if when else "")
                       + ", bound to these exact bytes and not re-examined while they hold")
    else:
        role = "guided practice" if resource["affordance"] == "mixed" else "explanation"
        reason = f"address the current {status} evidence state"
    return {
        "resource_id": resource["route_id"], "role": role, "intent": intent,
        "reason": reason,
    }


def _target_steps(candidate: list, status: str) -> list:
    """Build evidence/intent steps: the last pick always comes from the evidence pool."""
    if len(candidate) == 2:
        first, last = candidate
        return [_step_for(first, status),
                _step_for(last, status, as_evidence=last["affordance"] == "mixed")]
    (only,) = candidate
    return [_step_for(only, status, as_evidence=only["affordance"] == "mixed")]


def _fits(selected: list, budget, durations: dict) -> bool:
    if budget is None:
        return True
    return sum(durations[r["route_id"]] for r in selected) <= budget


def _assemble(repo, req, interpretation, status, steps, rejected, blockers, eligible, context, budget, extra_assumptions=()) -> dict:
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
            "only a current content review can establish assessment suitability; actual attempt conditions remain learner-reported",
            "no prerequisite failure has been reported" if not context.get("failed_prerequisites") else "prerequisite assumption invalidated",
            "no time budget was supplied" if budget is None else f"available time: {budget} minutes; supplied resource duration estimates are assumed",
            # A difficulty nobody can interpret yet is the most important thing
            # on this screen, and it has to arrive with the remedy attached.
            # Reporting it and leaving him to guess which flags were missing is
            # how the report got filed unqualified in the first place.
            #
            # Shown whenever one exists, not only when it displaced a
            # `demonstrated` verdict. An unresolved report against an
            # `uncertain` target changes no conclusion — `uncertain` was
            # already honest — but it is still a thing he said that the system
            # could not read, and silence about it is the defect either way.
            *_unresolved_note(interpretation),
            *extra_assumptions,
        ],
        "resource_reviews": [{"resource_id": resource["route_id"],
                              "activity_sha256": activity_fingerprint(repo, resource),
                              "requirement_sha256": requirement_fingerprint(req)}
                             for resource in eligible if resource.get("affordance") in {"evidence", "mixed"}],
        "replan_conditions": ["prerequisite-failure", "target-evidence-obtained-early", "selected-resource-unsuitable", "material-time-change", "target-changed"],
    }
    validate_contract(repo.root, "session-plan.schema.json", session)
    return session


def compile_session(repo: Repo, req: dict, interpretation: dict, context: dict | None = None) -> dict:
    context = {} if context is None else context
    validate_contract(repo.root, "session-context.schema.json", context)
    _, _, stage = requirement_stage(repo, req)
    status = interpretation.get("status", "unseen")
    if status not in {"unseen", "uncertain", "fragile", "unresolved", "demonstrated"}:
        raise RuntimeInputError(f"unknown learner interpretation: {status}")
    budget = context.get("available_minutes")
    unavailable, durations = _check_context_numbers(context)
    eligible, rejected = _eligible_resources(repo, stage, context, unavailable, durations, budget)
    shortfalls: list[tuple[str, str]] = []
    intervention, evidence = _pools(repo, req, context, eligible, status, rejected, shortfalls)
    blockers = []
    evidence_notes: tuple[str, ...] = ()
    selected: list[dict] = []
    failed = list(context.get("failed_prerequisites", []))
    repair_mode = status != "demonstrated" and bool(failed)
    if repair_mode:
        selected, blockers = _repair_with_prerequisites(
            repo, req, status, intervention, evidence, rejected, eligible, failed, budget, durations,
            context, shortfalls)
    elif status != "demonstrated":
        if not evidence:
            blocker, evidence_notes = _evidence_gap(shortfalls)
            blockers.append(blocker)
        if not blockers:
            # Consider alternatives when the preferred pair cannot fit. A
            # finite budget with missing durations never becomes unconstrained.
            # Pools overlap on mixed resources, so a pair never uses one twice.
            distinct = [[a, b] for a in intervention for b in evidence
                        if a["route_id"] != b["route_id"]]
            candidates = [pair for pair in distinct if not _reveals(repo, *pair)]
            if not intervention:
                candidates = [[b] for b in evidence]
            for candidate in candidates:
                if _fits(candidate, budget, durations):
                    selected = candidate
                    break
            if not selected:
                # Say which constraint emptied the list. "No candidate fits the
                # available time" would be a plain untruth when the pairs were
                # ruled out for handing over the assessment's answers, and the
                # learner would go looking for time he does not need.
                blockers.append(
                    "every explanation available here exposes the solutions to "
                    "the independent-evidence activity; no unaided pairing "
                    "remains" if distinct and not candidates else
                    "no evidence-producing candidate fits the available time")
    if repair_mode and selected:
        steps = _repair_steps(selected, status)
        extra = ("bounded repair uses explicitly mapped repair resources; target evidence still required",)
    else:
        steps = _target_steps(selected, status) if selected else []
        # A proposal that assesses without explaining has to say so. Handing a
        # learner whose understanding just broke down one more assessment and
        # calling it a session is defensible only if he can see that no repair
        # was available and decide for himself (audit F04).
        extra = _no_repair_note(status, selected, intervention, eligible) if selected else ()
    if blockers and not steps:
        # Assessment can be blocked while useful reading/practice remains reachable.
        #
        # Fully runnable resources come first, but a partially runnable one is
        # offered rather than dropped. This branch used to skip anything with a
        # missing asset outright, while the ordinary path selected the same
        # resource and merely annotated it — one resource, two policies, and
        # the stricter of them applied exactly where the learner had least
        # left. Decision 5 of the repair is that practice survives a blocked
        # assessment; `_asset_notes` below still says which parts cannot be
        # attempted, which is what F06 actually asked for.
        pool = [*intervention, *eligible]
        runnable = [r for r in pool if not _missing_assets(repo, r)]
        partial = [r for r in pool if _missing_assets(repo, r)]
        selected = []
        for resource in [*runnable, *partial]:
            if resource in selected or not _fits([*selected, resource], budget, durations):
                continue
            selected.append(resource)
            if len(selected) == 2:
                break
        steps = [{"resource_id": resource["route_id"], "role": "practice", "intent": "intervention",
                  "reason": "available practice; does not count as independent assessment"}
                 for resource in selected]
        extra = (*extra, *evidence_notes,
                 "assessment is blocked; the listed practice remains available")
    # Reachable is not the same as doable, and the proposal says which parts of
    # a selected activity cannot be attempted here (F06).
    extra = (*extra, *_asset_notes(repo, selected))
    extra = (*extra, *_same_source_answer_notes(
        repo, [step["resource_id"] for step in steps if step["intent"] == "evidence"]))
    return _assemble(repo, req, interpretation, status, steps, rejected, blockers, eligible, context, budget,
                     extra_assumptions=extra)


def _unresolved_note(interpretation: dict) -> tuple[str, ...]:
    """The interpreter's own sentence about a difficulty it could not read."""
    reason = interpretation.get("unresolved_reason")
    return (reason,) if isinstance(reason, str) and reason else ()


def _no_repair_note(status: str, selected: list, intervention: list,
                    eligible: list) -> tuple[str, ...]:
    """Explain an evidence-only proposal, in the terms that produced it."""
    if status == "demonstrated" or any(
            step["affordance"] in {"intervention", "mixed"} for step in selected):
        return ()
    repairs = [r for r in eligible if r["affordance"] in {"intervention", "mixed"}]
    if not repairs:
        return ("this stage has no accessible explanation or guided-practice "
                "resource, so the session can only assess; it offers no repair",)
    if not intervention:
        return ("every explanation and guided-practice resource in this stage "
                "was ruled out as inaccessible, out of scope, or unaffordable "
                "in the available time; see rejected_alternatives",)
    return ("no explanation or guided-practice resource fits alongside the "
            "evidence activity in the available time, so the session assesses "
            "without repairing",)


def _repair_with_prerequisites(repo, req, status, intervention, evidence, rejected, eligible, failed, budget, durations, context, shortfalls=None):
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
    evidence_rest = [r for r in evidence if r["route_id"] not in repair_ids]
    if not evidence:
        blocker, _ = _evidence_gap(shortfalls or [])
        return [], [f"{blocker}; prerequisite repair alone cannot produce target evidence"]
    if not evidence_rest:
        reserved = ", ".join(sorted(repair_ids))
        return [], [f"prerequisite repair reserves {reserved}; no target evidence remains"]
    if not rest:
        reserved = ", ".join(sorted(repair_ids))
        return [], [f"prerequisite repair reserves {reserved}; no target intervention remains"]
    target: list = []
    fixed = [resource for _, resource in repairs]
    for candidate in ([a, b] for a in rest for b in evidence_rest if a["route_id"] != b["route_id"]):
        # The repair steps are read before the evidence step, so they are as
        # capable of handing over its answers as the intervention is.
        if any(_reveals(repo, step, candidate[-1]) for step in [*fixed, candidate[0]]):
            continue
        if _fits([*fixed, *candidate], budget, durations):
            target = candidate
            break
    if not target:
        return [], ["no evidence-producing candidate fits the available time after prerequisite repair "
                    "without exposing its solutions"]
    marked = [{**resource, "_repair": names} for names, resource in repairs]
    marked += [{**resource, "_as_evidence": resource["affordance"] == "mixed"} if i == len(target) - 1 else resource
               for i, resource in enumerate(target)]
    return marked, []


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
            steps.append(_step_for(resource, status, as_evidence=bool(resource.get("_as_evidence"))))
    return steps


def _structural_replacement(repo, previous: dict, req: dict, interpretation: dict,
                            context: dict, flagged: dict[str, str]) -> dict:
    """Replace flagged steps with same-intent alternatives; preserve the rest verbatim."""
    _, _, stage = requirement_stage(repo, req)
    status = interpretation.get("status", "unseen")
    budget = context.get("available_minutes")
    unavailable, durations = _check_context_numbers(context)
    eligible, rejected = _eligible_resources(repo, stage, context, unavailable, durations, budget)
    intervention, evidence = _pools(repo, req, context, eligible, status, rejected)
    used = {s["resource_id"] for s in previous["steps"]} - set(flagged)
    # The steps this repair preserves verbatim are the constraint a replacement
    # has to respect. Preserving the assessment and swapping the explanation
    # for its answer key is a "structural" replacement that destroys exactly
    # what the preserved step was for (audit F03).
    by_id = {r["route_id"]: r for r in eligible}
    kept_evidence = [by_id[s["resource_id"]] for s in previous["steps"]
                     if s["intent"] == "evidence" and s["resource_id"] not in flagged
                     and s["resource_id"] in by_id]
    valid_evidence = {r["route_id"] for r in evidence}
    if any(s["resource_id"] not in by_id or
           (s["intent"] == "evidence" and s["resource_id"] not in valid_evidence)
           for s in previous["steps"] if s["resource_id"] not in flagged):
        return compile_session(repo, req, interpretation, {**context,
            "unavailable_resources": sorted(unavailable | set(flagged))})
    kept_interventions = [by_id[s["resource_id"]] for s in previous["steps"]
                          if s["intent"] == "intervention" and s["resource_id"] not in flagged]
    repaired = []
    for step in previous["steps"]:
        if step["resource_id"] not in flagged:
            repaired.append(copy.deepcopy(step))
            continue
        pool = evidence if step["intent"] == "evidence" else intervention
        swap = next((r for r in pool
                     if r["route_id"] not in used and r["route_id"] not in flagged
                     and not any(_reveals(repo, r, kept) for kept in kept_evidence)
                     and not (step["intent"] == "evidence" and
                              any(_reveals(repo, kept, r) for kept in kept_interventions))),
                    None)
        if swap is None:
            blockers = [f"no same-intent alternative for unsuitable step {step['resource_id']} ({flagged[step['resource_id']]})"]
            if any(_reveals(repo, candidate, kept)
                   for candidate in pool for kept in kept_evidence):
                blockers = [f"no same-intent alternative for unsuitable step "
                            f"{step['resource_id']} ({flagged[step['resource_id']]}) "
                            "that does not expose the preserved assessment's solutions"]
            return _assemble(repo, req, interpretation, status, [], rejected, blockers, eligible, context, budget,
                             extra_assumptions=("no executable assessment: structural repair failed, "
                                                "so the previous proposal is withdrawn rather than partially preserved",))
        used.add(swap["route_id"])
        (kept_evidence if step["intent"] == "evidence" else kept_interventions).append(swap)
        new_step = _step_for(swap, status,
                             as_evidence=step["intent"] == "evidence" and swap["affordance"] == "mixed")
        new_step["reason"] = (f"structural replacement for {step['resource_id']}: {flagged[step['resource_id']]}")
        repaired.append(new_step)
    if budget is not None:
        try:
            total = sum(durations[s["resource_id"]] for s in repaired)
        except KeyError:
            return _assemble(repo, req, interpretation, status, [], rejected,
                             ["no evidence-producing candidate fits the available time after structural repair"],
                             eligible, context, budget)
        if total > budget:
            return _assemble(repo, req, interpretation, status, [], rejected,
                             ["no evidence-producing candidate fits the available time after structural repair"],
                             eligible, context, budget)
    return _assemble(repo, req, interpretation, status, repaired, rejected, [], eligible, context, budget,
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
        exposed = _known_exposures(repo, context)
        for step in previous["steps"]:
            resource = resources.get(step["resource_id"])
            if (resource is None or resource.get("scope_triage") in {"reference-only", "deferred", "out-of-scope"}
                    or not _resource_available(repo, resource)
                    or (step["intent"] == "evidence" and resource.get("affordance") not in {"evidence", "mixed"})
                    or (step["intent"] == "intervention" and resource.get("affordance") not in {"intervention", "mixed"})):
                raise RuntimeInputError("previous steps are no longer eligible; an explicit material replan is required")
            if step["intent"] == "evidence" and _evidence_shortfall(repo, resource, req, exposed):
                raise RuntimeInputError("assessment suitability or exposure changed; propose a fresh session")
        evidence_steps = [resources[s["resource_id"]] for s in previous["steps"] if s["intent"] == "evidence"]
        if any(_reveals(repo, resources[s["resource_id"]], evidence)
               for s in previous["steps"] if s["intent"] == "intervention" for evidence in evidence_steps):
            raise RuntimeInputError("previous explanation exposes assessment solutions; propose a fresh session")
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
