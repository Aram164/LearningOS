"""Learner observations, stage results and ability observations."""

from __future__ import annotations

import json
from datetime import UTC

from jsonschema import Draft202012Validator, FormatChecker

from learning_os.app.admission import gesture_allowed
from learning_os.app.context import OpContext
from learning_os.app.handlers._shared import _on_commit_refused
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    gateway_request_context,
    intent_sha256,
    verified_gateway_snapshot,
)
from learning_os.derive.abilities import ability_fingerprint, read_ability_observations
from learning_os.derive.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    read_stage_results,
    requirement_fingerprint,
    runtime_path,
    validate_runtime_record,
)
from learning_os.domain.failures import Unconfirmed, WriteRefused
from learning_os.domain.suggest import with_suggestions
from learning_os.store import observations
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import parse_expected_revisions

STAGE_RESULT_CAPABILITY = "learner.stage-result.append"


@register("learner.stage-result.append", kind="command", json_formats=("ascii",))
def stage_result(ctx: OpContext, req: dict) -> Result:
    """Append an untargeted learner result against a unit/stage."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "stage results require GatewayEnvelopeV2; direct CLI application is disabled",
            site="learner.stage-result.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "stage results require a registered active workspace",
            site="learner.stage-result.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    try:
        unit = repo.units.get(req["unit"])
        if unit is None:
            raise RuntimeInputError(f"unknown unit: {req['unit']}")
        study_map = repo.study_maps.get((unit.data or {}).get("current_study_map"))
        if study_map is None or study_map.unit_id != unit.id \
                or study_map.module_id != unit.module_id:
            raise RuntimeInputError(f"unit {unit.id} has no current study map")
        stage = next((item for item in study_map.data.get("stages", [])
                      if isinstance(item, dict) and item.get("id") == req["stage"]), None)
        if stage is None:
            raise RuntimeInputError(
                f"unknown stage {req['stage']} in unit {unit.id}")
        if (unit.module_id not in workspace.meta.get("module_ids", [])
                and unit.id not in workspace.meta.get("unit_ids", [])):
            raise RuntimeInputError("stage is outside the workspace's declared module/unit scope")
        historical = read_stage_results(repo)
        ledger = runtime_path(root, workspace.path.parent / "stage-results.jsonl")
        row = {
            "id": "stage-result-" + observations.new_hex(),
            "unit": unit.id,
            "stage": stage["id"],
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
        }
        if req.get("assistance") is not None:
            row["assistance"] = req["assistance"]
        if req.get("note") is not None:
            row["note"] = req["note"]
        if req.get("supersedes"):
            prior = next((item for item in historical if item["id"] == req["supersedes"]), None)
            if (prior is None or prior["unit"] != unit.id
                    or prior["stage"] != stage["id"]
                    or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                    or any(item.get("supersedes") == prior["id"] for item in historical)):
                raise RuntimeInputError("correction must supersede one uncorrected stage result of this unit/stage in this ledger")
            row["supersedes"] = req["supersedes"]
        validate_runtime_record(repo, "learner-stage-result", row)
        try:
            old = ledger.read_text(encoding="utf-8")
        except FileNotFoundError:
            old = ""
        separator = "\n" if old and not old.endswith("\n") else ""
        new = old + separator + json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "stage_result_id": row["id"],
             "workspace_id": workspace.id, "unit": unit.id,
             "stage": stage["id"], "credit": "none"},
            proposal=TransactionProposal(
                capability=STAGE_RESULT_CAPABILITY,
                writes={ledger: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_format="ascii",
        )
    except (RuntimeInputError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.stage-result.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc


OBSERVE_CAPABILITY = "learner.observation.append"


def _stage_index(repo):
    """Every study-map stage: ``stage_id -> (unit_id, has_target)``.

    Only the current map of each unit is indexed: a stage id that exists
    solely on a superseded map is not observable, and naming it as a
    stage would point at work that no longer resolves.
    """
    index = {}
    for unit in repo.units.values():
        study_map = repo.study_maps.get((unit.data or {}).get("current_study_map"))
        if study_map is None or study_map.unit_id != unit.id:
            continue
        for stage in study_map.data.get("stages", []):
            if isinstance(stage, dict) and isinstance(stage.get("id"), str):
                index.setdefault(stage["id"], (
                    unit.id, isinstance(stage.get("runtime_target"), dict)))
    return index


def _unknown_requirement_message(repo, requirements, value):
    """Refuse an unresolvable id with the way forward named.

    A stage id whose stage carries no ``runtime_target`` is the ordinary
    untargeted case — most stages have no target — so it names the stage,
    the untargeted ``stage-result`` path, and the target-authoring
    ``unit-plan-revise`` path instead of crying unknown. A stage id that
    already has a target names the requirement id to observe. Anything
    else is a mistyped id, with suggestions over requirements and stages.
    """
    stages = _stage_index(repo)
    if value in stages:
        unit_id, has_target = stages[value]
        if has_target:
            requirement_id = next(
                (req["id"] for req in requirements
                 if req.get("source_stage", {}).get("stage_id") == value
                 and req.get("source_stage", {}).get("unit_id") == unit_id),
                None,
            )
            observed = f" {requirement_id}" if requirement_id else ""
            return (f"stage {value} (unit {unit_id}) already has a requirement "
                    f"target; observe the requirement id{observed} instead of "
                    f"the stage id")
        return (f"stage {value} (unit {unit_id}) has no requirement target; "
                f"record the result without credit via `stage-result "
                f"--workspace WORKSPACE --unit {unit_id} --stage {value} "
                f"--activity ACTIVITY --result RESULT`, or author a target "
                f"with `unit-plan-revise {unit_id} --file REVISION.yaml "
                f"--check` adding a runtime_target stage patch (WORKFLOWS §8)")
    return with_suggestions(f"unknown requirement: {value}", value,
                            [*(req["id"] for req in requirements), *stages])


def _condition_notice(requirement: dict, obs: dict) -> dict:
    """Say what this record does and does not establish, while he can still fix it.

    The write succeeded either way — the ledger is his, and refusing a report
    of difficulty because it lacked flags would be worse than accepting it.
    But a report that cannot be read as a failure of the current target needs
    to say so at the moment it is filed. It used to persist silently and leave
    the requirement reading `demonstrated`, `satisfied`, no next steps: the
    successful save was the only feedback, and it concealed that the report
    had no effect (audit `synthetic-learner-2026-09-12`, F02).
    """
    if obs["result"] not in {"incorrect", "partial"}:
        return {}
    declared = set(requirement.get("conditions", []))
    refuted = sorted(declared & set(obs.get("conditions_not_met", [])))
    if refuted:
        return {"refuted_conditions": refuted,
                "interpretation_notice": (
                    f"recorded as a different situation ({', '.join(refuted)} "
                    f"did not hold), so it is not read as a failure of this "
                    f"target and resets nothing")}
    missing = sorted(declared - set(obs.get("conditions", [])))
    if not missing:
        return {"interpretation_notice":
                "recorded under every condition this target declares; it is "
                "read as a failure of this target"}
    flags = " ".join(f"--condition {name}" for name in missing)
    not_met = " ".join(f"--condition-not-met {name}" for name in missing)
    return {
        "unstated_conditions": missing,
        "interpretation_notice": (
            f"this result does not say whether the target's conditions held "
            f"({', '.join(missing)}), so it is held as unresolved: it is not "
            f"read as a failure of this target, and the successes recorded "
            f"before it stop counting toward a current conclusion until this "
            f"is settled. Settle it by superseding this record — "
            f"los observe {requirement['id']} --activity {obs['activity']} "
            f"--result {obs['result']} --supersedes {obs['id']} — adding "
            f"{flags} for the conditions that held, or {not_met} for the ones "
            f"that did not. Two distinct qualified activities recorded after "
            f"this also establish a new basis, without claiming the missing "
            f"facts were ever known."
        ),
    }


@register("learner.observation.append", kind="command", json_formats=("ascii",))
def observation_append(ctx: OpContext, req: dict) -> Result:
    """Append one immutable learner observation against a requirement."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "observations require GatewayEnvelopeV2; direct CLI application is disabled",
            site="learner.observation.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "observations require a registered active workspace",
            site="learner.observation.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    try:
        requirements = collect_requirements(repo)
        requirement = next((row for row in requirements
                            if row["id"] == req["requirement"]), None)
        if requirement is None:
            raise RuntimeInputError(
                _unknown_requirement_message(repo, requirements, req["requirement"]))
        source = requirement["source_stage"]
        if (source["module_id"] not in workspace.meta.get("module_ids", [])
                and source["unit_id"] not in workspace.meta.get("unit_ids", [])):
            raise RuntimeInputError("requirement is outside the workspace's declared module/unit scope")
        historical = read_observations(repo, requirements)
        ledger = runtime_path(root, workspace.path.parent / "observations.jsonl")
        obs = {
            "id": "observation-" + observations.new_hex(),
            "requirement": req["requirement"],
            "requirement_sha256": requirement_fingerprint(requirement),
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
            "evidence_tags": [tag.strip() for tag in (req.get("tags") or "").split(",") if tag.strip()],
        }
        refuted = list(req.get("condition_not_met") or [])
        if refuted:
            both = sorted(set(obs["conditions"]) & set(refuted))
            if both:
                raise RuntimeInputError(
                    "a condition cannot be recorded as both met and not met: "
                    + ", ".join(both))
            obs["conditions_not_met"] = refuted
        if req.get("assistance") is not None:
            obs["assistance"] = req.get("assistance")
        if req.get("context") is not None:
            obs["context"] = req.get("context")
        if req.get("supersedes"):
            prior = next((item for item in historical if item["id"] == req["supersedes"]), None)
            if (prior is None or prior["requirement"] != req["requirement"]
                    or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                    or any(item.get("supersedes") == prior["id"] for item in historical)):
                raise RuntimeInputError("correction must supersede one uncorrected observation of this requirement in this ledger")
            obs["supersedes"] = req["supersedes"]
        validate_runtime_record(repo, "learner-observation", obs)
        try:
            old = ledger.read_text(encoding="utf-8")
        except FileNotFoundError:
            old = ""
        separator = "\n" if old and not old.endswith("\n") else ""
        new = old + separator + json.dumps(obs, sort_keys=True, ensure_ascii=False) + "\n"
        return Result(
            {"ok": True, "observation_id": obs["id"],
             "workspace_id": workspace.id,
             **_condition_notice(requirement, obs)},
            proposal=TransactionProposal(
                capability=OBSERVE_CAPABILITY,
                writes={ledger: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_format="ascii",
        )
    except (RuntimeInputError, OSError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.observation.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc


def _resolve_observe_workspace(repo, requirement, explicit_id):
    """Return ``(workspace, refusal)`` for the direct path.

    An explicit id behaves exactly like ``observation-append``. An omitted
    id resolves the single active workspace covering the requirement's
    module or unit scope; zero or several candidates refuse rather than
    guess, because the ledger line cannot move workspaces afterwards.
    """
    source = requirement["source_stage"]

    def covers(workspace) -> bool:
        return (source["module_id"] in workspace.meta.get("module_ids", [])
                or source["unit_id"] in workspace.meta.get("unit_ids", []))

    if explicit_id is not None:
        workspace = repo.workspaces.get(explicit_id)
        if workspace is None or workspace.archived or workspace.status != "active":
            return None, "observations require a registered active workspace"
        if not covers(workspace):
            return None, "requirement is outside the workspace's declared module/unit scope"
        return workspace, ""
    candidates = sorted(
        workspace.id for workspace in repo.workspaces.values()
        if not workspace.archived and workspace.status == "active" and covers(workspace)
    )
    if not candidates:
        return None, (f"no active workspace covers requirement {requirement['id']}; "
                      "pass --workspace to choose one")
    if len(candidates) > 1:
        return None, (f"requirement {requirement['id']} is covered by "
                      f"{len(candidates)} workspaces ({', '.join(candidates)}); "
                      "pass --workspace to choose one")
    return repo.workspaces[candidates[0]], ""


@register("cli.observe", kind="command", json_formats=("ascii",))
def cli_observe(ctx: OpContext, req: dict) -> Result:
    """Record Aram's own evidence directly; the terminal session is the approval."""
    root = ctx.root
    if not gesture_allowed(OBSERVE_CAPABILITY):
        raise WriteRefused(
            "the direct observation path is not admitted",
            site="cli.observe.not-admitted",
            prefixed=True,
            exit_code=2,
        )
    snapshot = ctx.snapshot_id()
    repo = ctx.repo()
    try:
        requirements = collect_requirements(repo)
    except RuntimeInputError as exc:
        raise WriteRefused(
            str(exc),
            site="cli.observe.invalid-target",
            prefixed=True,
            exit_code=2,
        ) from exc
    requirement = next((row for row in requirements
                        if row["id"] == req["requirement"]), None)
    if requirement is None:
        message = _unknown_requirement_message(
            repo, requirements, req["requirement"])
        raise WriteRefused(
            message,
            site="cli.observe.unknown-requirement",
            prefixed=True,
            exit_code=2,
        )
    workspace, refusal = _resolve_observe_workspace(
        repo, requirement, req.get("workspace"))
    if workspace is None:
        raise WriteRefused(
            refusal,
            site="cli.observe.unresolved-workspace",
            prefixed=True,
            exit_code=2,
        )
    payload: dict = {
        "workspace": workspace.id,
        "requirement": requirement["id"],
        "activity": req["activity"],
        "result": req["result"],
    }
    if req.get("assistance") is not None:
        payload["assistance"] = req["assistance"]
    if req.get("tags") is not None:
        payload["tags"] = req["tags"]
    if req.get("note") is not None:
        payload["context"] = req["note"]
    if req.get("condition"):
        payload["condition"] = list(req["condition"])
    if req.get("condition_not_met"):
        payload["condition_not_met"] = list(req["condition_not_met"])
    if req.get("supersedes"):
        payload["supersedes"] = req["supersedes"]
    expected_revisions = {workspace.id: artifact_revision(root, workspace.id)}
    subject = intent_sha256({
        "schema_version": 2,
        "capability": OBSERVE_CAPABILITY,
        "channel": "operator",
        "expected_snapshot": snapshot,
        "expected_revisions": expected_revisions,
        "payload": payload,
    })
    key = observations.new_hex()
    context = GatewayRequestContext(
        request_id=f"observe-{key}",
        idempotency_key=f"observe-{key}",
        capability=OBSERVE_CAPABILITY,
        channel="operator",
        intent_sha256=subject,
        approval_kind="direct-user-gesture",
        approval_subject_sha256=subject,
        expected_snapshot=snapshot,
    )
    core_req = {
        "workspace": workspace.id,
        "requirement": requirement["id"],
        "activity": req["activity"],
        "result": req["result"],
        "expected_snapshot": snapshot,
        "expected_revision": [
            f"{workspace.id}={expected_revisions[workspace.id]}"],
        "assistance": req.get("assistance"),
        "tags": req.get("tags"),
        "context": req.get("note"),
        "condition": req.get("condition"),
        "condition_not_met": req.get("condition_not_met"),
        "supersedes": req.get("supersedes"),
    }
    with gateway_request_context(context), verified_gateway_snapshot(
            root, snapshot):
        core = observation_append(ctx, core_req)
    return Result(
        core.payload,
        proposal=core.proposal,
        on_commit_refused=_on_commit_refused,
        json_format="ascii",
        gesture=context,
    )


def _valid_work_ref(value: str) -> bool:
    if not value.startswith(("conversation://", "note://", "project://", "curriculum/")):
        return False
    if any(character.isspace() for character in value):
        return False
    if value.startswith("curriculum/"):
        path = value.split("#", 1)[0]
        parts = path.split("/")
        return "\\" not in path and len(parts) > 1 and all(
            part not in ("", ".", "..") for part in parts)
    return True


@register("learner.ability-observation.append", kind="command", json_formats=("ascii",))
def ability_observation_append(ctx: OpContext, req: dict) -> Result:
    """Record an exact learner-confirmed claim; the V2 approval binds payload."""
    root = ctx.root
    request = current_gateway_request()
    if request is None:
        raise WriteRefused(
            "ability observations require GatewayEnvelopeV2",
            site="learner.ability-observation.append.direct-cli",
            prefixed=True,
            exit_code=2,
        )
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    workspace = repo.workspaces.get(req["workspace"])
    if workspace is None or workspace.archived or workspace.status != "active":
        raise WriteRefused(
            "a registered active workspace must own this work",
            site="learner.ability-observation.append.bad-workspace",
            prefixed=True,
            exit_code=2,
        )
    ability = repo.abilities.get(req["ability"])
    if (ability is None or ability.get("review", {}).get("state") != "reviewed"
            or ability.get("lifecycle") == "retired"):
        raise WriteRefused(
            "evidence requires an active reviewed ability identity",
            site="learner.ability-observation.append.unknown-ability",
            prefixed=True,
            exit_code=2,
        )
    if not _valid_work_ref(req["work_ref"]):
        raise WriteRefused(
            "work-ref must safely point to conversation, note, project, or curriculum work",
            site="learner.ability-observation.append.bad-work-ref",
            prefixed=True,
            exit_code=2,
        )
    if not req["confirmation_ref"].startswith(("conversation://", "note://")):
        raise Unconfirmed(
            "confirmation-ref must point to Aram's confirmation",
            site="learner.ability-observation.append.bad-confirmation-ref",
            prefixed=True,
            exit_code=2,
        )
    if (request.channel == "ui" and req["confirmation_ref"] !=
            f"conversation://learningos-app/{request.idempotency_key}"):
        raise Unconfirmed(
            "app confirmation-ref must name this exact request",
            site="learner.ability-observation.append.bad-app-confirmation",
            prefixed=True,
            exit_code=2,
        )
    try:
        history = read_ability_observations(repo)
        path = runtime_path(root, workspace.path.parent / "ability-observations.jsonl")
        if req.get("supersedes"):
            prior = next((row for row in history if row["id"] == req["supersedes"]), None)
            if (prior is None or prior["ability_id"] != req["ability"]
                    or prior["origin"]["path"] != path.relative_to(root).as_posix()
                    or any(row.get("supersedes") == prior["id"] for row in history)):
                raise WriteRefused("correction must supersede one uncorrected observation in this ledger")
        row = {
            "id": "ability-observation-" + observations.new_hex(),
            "ability_id": req["ability"],
            "ability_sha256": ability_fingerprint(ability),
            "claim": req["claim"],
            "work_ref": req["work_ref"],
            "confirmation_ref": req["confirmation_ref"],
            "activity": req["activity"],
            "result": req["result"],
            "timestamp": observations.now().astimezone(UTC).isoformat(),
            "conditions": list(req.get("condition") or []),
            "evidence_tags": list(req.get("evidence_tag") or []),
            "assistance": req["assistance"],
            "confirmed_by": "learner",
        }
        if req.get("condition_not_met"):
            row["conditions_not_met"] = list(req.get("condition_not_met"))
        if req.get("supersedes"):
            row["supersedes"] = req["supersedes"]
        if set(row["conditions"]) & set(row.get("conditions_not_met", [])):
            raise WriteRefused("condition cannot be both met and not met")
        schema = json.loads((root / "system/schema/ability-observation.schema.json").read_text())
        errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(row), key=str)
        if errors:
            raise WriteRefused(f"ability observation: {errors[0].message}")
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        new = old + ("\n" if old and not old.endswith("\n") else "")
        new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "observation_id": row["id"]},
            proposal=TransactionProposal(
                capability="learner.ability-observation.append",
                writes={path: new},
                artifact_ids=[workspace.id],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_format="ascii",
        )
    except (WriteRefused, OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            site="learner.ability-observation.append.invalid-input",
            prefixed=True,
            exit_code=2,
        ) from exc
