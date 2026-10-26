"""Learner-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import yaml

from learning_os.app.context import OpContext
from learning_os.app.gateway import read_content_bound_file as _read_content_bound_file
from learning_os.app.handlers._shared import (
    require_path_or_error,
    require_stage,
    require_unit_map_or_error,
)
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import register
from learning_os.derive.learning_runtime import requirement_id_for
from learning_os.derive.routes import route_with_identity
from learning_os.domain.curriculum.stages import (
    PATH_ACTIONS,
    STAGE_ACTIONS,
    apply_path_action,
    apply_stage_action,
    progress_entry,
)
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import not_found, with_suggestions
from learning_os.domain.unit_notes import unit_note_marker
from learning_os.store import observations
from learning_os.store.codec import dump_study_map as _dump_study_map
from learning_os.store.codec import dump_yaml as _dump_yaml
from learning_os.store.transactions import parse_expected_revisions

#: The one return-to-work record. `los resume` and the app's Home both start
#: here, so they cannot disagree about where the learner left off.
#: Moved verbatim from commands.support with its only writer (SPEC 12).
RESUME_POINTER_PATH = "curriculum/resume.yaml"


def _resume_pointer_write(root: Path, *, module_id: str, unit_id: str,
                          study_map_id: str, stage_id: str) -> dict[Path, str]:
    """The resume-pointer file for one explicit study action.

    Returned as a ``{path: text}`` fragment to merge into the *same*
    ``_write_transaction`` as the records that moved. That is the whole point:
    the pointer is written under the operator lock the caller already holds,
    inside the capability's declared write scope, covered by the same receipt,
    the same post-action scope check, the same validation and the same
    republished projection. A separate write after the transaction would be an
    untracked side effect that could survive a rolled-back change, or be lost
    while the change committed — and the destination would then be lying about
    where the work actually is.

    Until 2026-09-13 nothing wrote this file at all. `curriculum/resume.yaml`
    did not exist; `los resume` silently recovered through "last recorded
    result", and the app's Home, which reads only this pointer, said "Nothing
    to resume yet". Activating a stage in another subject therefore left both
    interfaces pointing at the old one (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F05).
    """
    pointer = {
        "type": "resume-pointer",
        "module_id": str(module_id),
        "unit_id": str(unit_id),
        "study_map_id": str(study_map_id),
        "stage_id": str(stage_id),
        "updated": observations.today().isoformat(),
    }
    return {root / RESUME_POINTER_PATH: _dump_yaml(pointer)}


def _observe_offer(unit_id: str, stage: dict) -> dict:
    """The observation verb for one stage's requirement, or nothing.

    Pure and read-only: when the stage authors a runtime requirement, name
    the exact ``los observe`` invocation that would record evidence against
    it. Otherwise return no keys. Suggesting never writes — the ledger
    still moves only through ``los observe``.
    """
    target = stage.get("runtime_target")
    if not isinstance(target, dict):
        return {}
    requirement_id = requirement_id_for(unit_id, str(stage.get("id", "")))
    # Name the conditions this target actually declares. The offer used to
    # stop at activity and result, so the command it taught could not produce
    # evidence the interpreter would credit, and a difficulty reported through
    # it could not be read as a failure of this target at all (audit
    # `synthetic-learner-2026-09-12`, F02). The flags are prompts to state what
    # happened, never defaults to accept — an unmet condition is dropped, not
    # asserted.
    conditions = [str(name) for name in (target.get("conditions") or [])
                  if str(name).strip()]
    flags = "".join(f" --condition {name}" for name in conditions)
    offer = {
        "observe_requirement": requirement_id,
        "observe_next": f"los observe {requirement_id} --activity <what-you-did> "
                        f"--result <correct|incorrect|partial|abandoned>{flags}",
    }
    if conditions:
        offer["observe_conditions"] = conditions
        offer["observe_note"] = (
            "keep only the conditions that actually held; an omitted one is "
            "read as unknown, never as met"
        )
    return offer


@register("stage.progress.update", kind="command")
def stage_progress(ctx: OpContext, req: dict) -> Result:
    """Move one stage's status and record progress against it."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    unit_data = copy.deepcopy(unit.data)
    stage = require_stage(ctx, data, req["stage_id"])
    action = req["status"]
    if action in {"complete", "skipped"} and stage.get("status") != "active":
        raise WriteRefused(
            "complete/skip applies only to the active stage; activate it first",
            site=f"{ctx.operation}.not-active",
            prefixed=True,
            exit_code=2,
        )
    if action not in STAGE_ACTIONS:
        # The gateway schema and payload_to_namespace refuse unknown
        # values first; this is the last backstop. An open `else` here
        # once recorded an unknown status as `skipped`.
        raise WriteRefused(
            f"unknown stage status: {action} "
            "(choose from active, paused, complete, skipped, revisit)",
            site=f"{ctx.operation}.unknown-status",
            prefixed=True,
            exit_code=2,
        )
    apply_stage_action(data, unit_data, stage, action, observations.today)
    summary = req.get("progress_summary")
    upcoming = req.get("progress_next")
    if summary is not None or upcoming is not None:
        if summary is None or not summary.strip():
            raise WriteRefused(
                "--progress-next needs --progress-summary",
                site=f"{ctx.operation}.needs-summary",
                prefixed=True,
                exit_code=2,
            )
        if upcoming is not None and not upcoming.strip():
            raise WriteRefused(
                "--progress-next must not be blank",
                site=f"{ctx.operation}.blank-next",
                prefixed=True,
                exit_code=2,
            )
        stage["progress"] = progress_entry(summary, upcoming, observations.today)
    # One rule for every branch: the destination is the stage this action
    # just made current. Activate or revisit and you return to it; pause it
    # and you return to the thing you paused, which is what pausing means;
    # complete or skip and you return to the stage that became current
    # after it, or — when the map has run out of stages — to the finished
    # one, where `resume` can honestly say it is ready to shelve. Other
    # units keep their own active maps; this names where *he* is, not what
    # is open.
    resume_stage = str(data.get("current_stage") or stage["id"])
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site=f"{ctx.operation}.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"], "stage_id": req["stage_id"],
         "status": action, "map_status": data["status"],
         "current_stage": data["current_stage"],
         **({"progress": stage["progress"]} if "progress" in stage else {}),
         **_observe_offer(req["unit_id"], stage)},
        proposal=TransactionProposal(
            capability="stage.progress.update",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data),
                    **_resume_pointer_write(
                        ctx.root, module_id=unit.module_id, unit_id=req["unit_id"],
                        study_map_id=study_map.id, stage_id=resume_stage)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )


@register("stage.note.write", kind="command")
def stage_note(ctx: OpContext, req: dict) -> Result:
    """Append to (or replace) a stage's working note."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    stage = require_stage(ctx, study_map.data, req["stage_id"])
    target = root / str(stage.get("working_note", ""))
    if not stage.get("working_note"):
        raise WriteRefused(
            "stage has no working_note",
            site="stage.note.write.no-working-note",
            prefixed=True,
            exit_code=2,
        )
    value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not value.strip():
        # `--replace --text ""` used to truncate an existing note to zero
        # bytes and report success. Emptying a note is a deliberate edit,
        # not something a save button should ever do.
        raise WriteRefused(
            "refusing to write an empty note — pass real text",
            site="stage.note.write.empty-note",
            prefixed=True,
            exit_code=2,
        )
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    if req.get("replace"):
        updated = value.rstrip() + ("\n" if value.strip() else "")
    else:
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + value.rstrip() + "\n"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="stage.note.write.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "working_note": stage["working_note"]},
        proposal=TransactionProposal(
            capability="stage.note.write",
            writes={target: updated},
            artifact_ids=[req["unit_id"]],
            expected_revisions=expected_revisions,
        ),


    )


def _allocate_attachment_path(attachment_dir: Path, source_name: str) -> Path:
    """A destination no existing attachment occupies.

    Attachment bytes are approved canonical content, so the previous holder of a
    name must never be overwritten. A timestamp was not a uniqueness argument:
    it is precise to one second and the name it produced was never itself
    checked, so two uploads of `handwriting.png` within the same second silently
    replaced the first one's bytes.

    Every candidate is checked now, and the counter guarantees the search ends
    on a free name. Checking existence is sufficient here — and only here —
    because every caller allocates while holding the operator lock, so no other
    process can take the name between this check and the transaction that writes
    it.
    """
    target = attachment_dir / source_name
    if not target.exists():
        return target

    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    target = attachment_dir / f"{stamp}-{source_name}"
    if not target.exists():
        return target

    counter = 1
    while True:
        target = attachment_dir / f"{stamp}-{counter}-{source_name}"
        if not target.exists():
            return target
        counter += 1


@register("stage.attachment.add", kind="command")
def stage_attach(ctx: OpContext, req: dict) -> Result:
    """Attach a content-bound file beside a stage's working note."""
    root = ctx.root
    try:
        source, source_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="stage attachment",
        )
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="stage.attachment.add.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    note_ref = stage.get("working_note")
    if not isinstance(note_ref, str) or not note_ref:
        raise WriteRefused("stage has no working_note",
                           site="stage.attachment.add.no-working-note", prefixed=True, exit_code=2)
    note_path = root / note_ref
    attachment_dir = note_path.parent / "attachments"
    target = _allocate_attachment_path(attachment_dir, source.name)
    rel = target.relative_to(root).as_posix()
    stage.setdefault("attachments", []).append(
        {"path": rel, "label": req.get("label") or source.stem})
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="stage.attachment.add.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "attachment": rel},
        proposal=TransactionProposal(
            capability="stage.attachment.add",
            writes={study_map.path: _dump_study_map(study_map, data),
                    target: source_bytes},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )


@register("path.note.write", kind="command")
def path_note(ctx: OpContext, req: dict) -> Result:
    """Append to (or replace) a learning-path stage note."""
    root = ctx.root
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    stage = require_stage(ctx, learning_path.data, req["stage_id"])
    note_ref = stage.get("notes_path")
    if not note_ref:
        raise WriteRefused(
            f"stage has no notes_path: {req['stage_id']}",
            site="path.note.write.no-notes-path",
            prefixed=True,
            exit_code=2,
        )
    text_value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not text_value.strip():
        raise WriteRefused(
            "refusing to write an empty note — pass real text",
            site="path.note.write.empty-note",
            prefixed=True,
            exit_code=2,
        )
    target = root / str(note_ref)
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    if req.get("replace"):
        updated = text_value.rstrip() + ("\n" if text_value.strip() else "")
    else:
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + text_value.rstrip() + "\n"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.note.write.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "notes_path": note_ref},
        proposal=TransactionProposal(
            capability="path.note.write",
            writes={target: updated},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),


    )




@register("path.progress.update", kind="command")
def path_progress(ctx: OpContext, req: dict) -> Result:
    """Move one learning-path stage's status."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    data = learning_path.data
    stage = require_stage(ctx, data, req["stage_id"])
    if req["status"] in {"complete", "skipped"} and stage.get("status") != "active":
        raise WriteRefused(
            "only the active stage can be completed or skipped; activate it first",
            site="path.progress.update.not-active",
            prefixed=True,
            exit_code=2,
        )
    if req["status"] not in PATH_ACTIONS:
        raise WriteRefused(
            f"unknown path status: {req['status']} "
            "(choose from active, complete, skipped)",
            site="path.progress.update.unknown-status",
            prefixed=True,
            exit_code=2,
        )
    apply_path_action(data, stage, req["status"], observations.today)
    data["updated"] = observations.today().isoformat()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.progress.update.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "status": req["status"],
         "path_status": data["status"],
         "current_stage": data["current_stage"]},
        proposal=TransactionProposal(
            capability="path.progress.update",
            writes={learning_path.path: rendered},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),


    )




@register("path.attachment.add", kind="command")
def path_attach(ctx: OpContext, req: dict) -> Result:
    """Attach a content-bound file to a learning-path stage."""
    root = ctx.root
    try:
        source, source_bytes = _read_content_bound_file(
            req["file"],
            req.get("file_sha256"),
            label="path attachment",
        )
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="path.attachment.add.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, learning_path = require_path_or_error(ctx, req["path_id"])
    data = learning_path.data
    stage = require_stage(ctx, data, req["stage_id"])
    workspace = learning_path.path.parent.parent
    attachment_dir = workspace / "scratch" / "paths" / learning_path.id \
        / "attachments" / stage["id"]
    target = _allocate_attachment_path(attachment_dir, source.name)
    rel = target.relative_to(root).as_posix()
    stage.setdefault("attachments", []).append({
        "path": rel, "label": req.get("label") or source.stem})
    data["updated"] = observations.today().isoformat()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="path.attachment.add.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "path_id": req["path_id"],
         "stage_id": req["stage_id"], "attachment": rel},
        proposal=TransactionProposal(
            capability="path.attachment.add",
            writes={learning_path.path: rendered, target: source_bytes},
            artifact_ids=[req["path_id"]],
            expected_revisions=expected_revisions,
        ),


    )


@register("detour.create", kind="command")
def detour_create(ctx: OpContext, req: dict) -> Result:
    """Open a scoped detour off one stage."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    base = re.sub(r"[^a-z0-9]+", "-", req["title"].lower()).strip("-") or "gap"
    did = f"detour-{base}"
    existing = {row.get("id") for row in data.get("detours", []) or []}
    if did in existing:
        suffix = 2
        while f"{did}-{suffix}" in existing:
            suffix += 1
        did = f"{did}-{suffix}"
    detour = {"id": did, "title": req["title"], "spawned_by_stage": req["stage_id"],
              "classification": req["classification"], "status": "open",
              "return_to_stage": req["stage_id"]}
    data.setdefault("detours", []).append(detour)
    stage["detour_id"] = did
    if req["classification"] == "required-now":
        stage["status"] = "paused"
        data["status"] = "paused"
        unit_data = copy.deepcopy(unit.data)
        unit_data["status"] = "paused"
    elif req["classification"] in {"helpful-now", "deferred", "reference-only"}:
        unit_data = unit.data
    else:
        raise WriteRefused(
            f"unknown detour classification: {req['classification']} "
            "(choose from required-now, helpful-now, deferred, "
            "reference-only)",
            site="detour.create.unknown-classification",
            prefixed=True,
            exit_code=2,
        )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="detour.create.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "detour": detour},
        proposal=TransactionProposal(
            capability="detour.create",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )


def _stage(data: dict, stage_id: str):
    return next((row for row in data.get("stages", []) or []
                 if isinstance(row, dict) and row.get("id") == stage_id), None)


@register("detour.resolve", kind="command")
def detour_resolve(ctx: OpContext, req: dict) -> Result:
    """Resolve a detour and reactivate its return stage."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    detour = next((row for row in data.get("detours", []) or []
                   if row.get("id") == req["detour_id"]), None)
    if detour is None:
        known = [row.get("id") for row in data.get("detours", []) or []
                 if isinstance(row, dict) and row.get("id")]
        message = not_found("detour", req["detour_id"], known)
        raise NotFound(
            "detour", req["detour_id"], known,
            site="detour.resolve.unknown-detour",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    detour["status"] = "resolved"
    if req.get("resolution"):
        detour["resolution"] = req["resolution"]
    target_stage = require_stage(ctx, data, detour["return_to_stage"])
    for other in data.get("stages", []) or []:
        if other.get("status") in {"active", "paused"}:
            other["status"] = "pending"
    target_stage["status"] = "active"
    target_stage.pop("completed", None)
    data["current_stage"] = target_stage["id"]
    data["status"] = "active"
    unit_data = copy.deepcopy(unit.data)
    unit_data["status"] = "active"
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="detour.resolve.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "detour_id": req["detour_id"],
         "return_to_stage": target_stage["id"]},
        proposal=TransactionProposal(
            capability="detour.resolve",
            writes={study_map.path: _dump_study_map(study_map, data),
                    unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )


@register("source.feedback.record", kind="command")
def source_feedback(ctx: OpContext, req: dict) -> Result:
    """Record source feedback against an exact unit/stage/source."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    if req["source_id"] not in repo.sources:
        message = not_found("source", req["source_id"], repo.sources)
        raise NotFound(
            "source", req["source_id"], repo.sources,
            site="source.feedback.record.unknown-source",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    entry = {"source_id": req["source_id"], "feedback": req["feedback"],
             "recorded": observations.today().isoformat()}
    resource_id = req.get("resource_id")
    if resource_id:
        # Resolve against THIS stage before writing. The validator rejects a
        # dangling resource_id, but failing here gives the caller the actual
        # id list instead of a post-hoc validation error, and keeps the
        # transaction from being attempted at all.
        resources = {str(r.get("id")): r for r in (stage.get("resources") or [])
                     if isinstance(r, dict) and r.get("id")}
        target = resources.get(resource_id)
        if target is None:
            known = (", ".join(sorted(resources))
                     or "(this stage has no identified resources)")
            refusal = with_suggestions(
                f"resource not found on stage {req['stage_id']}: {resource_id}",
                resource_id, resources)
            raise NotFound(
                "resource", resource_id, resources,
                message=f"{refusal}\n     known: {known}",
                site="source.feedback.record.unknown-resource",
                gateway_message=f"los: {refusal}\n     known: {known}",
                exit_code=2,
            )
        declared = target.get("source_id")
        if declared and declared != req["source_id"]:
            raise WriteRefused(
                f"resource {resource_id} belongs to {declared}, "
                f"not {req['source_id']}",
                site="source.feedback.record.wrong-source",
                prefixed=True,
                exit_code=2,
            )
        entry["resource_id"] = resource_id
    if req.get("note"):
        entry["note"] = req["note"]
    stage.setdefault("source_feedback", []).append(entry)
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="source.feedback.record.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "stage_id": req["stage_id"], "feedback": entry},
        proposal=TransactionProposal(
            capability="source.feedback.record",
            writes={study_map.path: _dump_study_map(study_map, data)},
            artifact_ids=[req["unit_id"], study_map.id],
            expected_revisions=expected_revisions,
        ),


    )


def _unit_note_target(root: Path, unit) -> tuple[Path, str]:
    declared = str(unit.data.get("working_note") or "").strip()
    target = root / declared if declared else unit.path.parent / "notes.md"
    try:
        rel = target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise WriteRefused("unit working note must stay inside the repository") from exc
    return target, rel


@register("unit.note.append", kind="command")
def unit_note(ctx: OpContext, req: dict) -> Result:
    """Append one session-level section to the unit working note."""
    root = ctx.root
    value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not value.strip():
        raise WriteRefused(
            "refusing to write an empty unit note — pass real text",
            site="unit.note.append.empty-note",
            prefixed=True,
            exit_code=2,
        )
    raw_sources = list(req.get("attachment") or [])
    source_hashes = list(req.get("attachment_sha256") or [])
    if source_hashes and len(source_hashes) != len(raw_sources):
        raise WriteRefused(
            "--attachment-sha256 must be repeated once per --attachment",
            site="unit.note.append.attachment-sha-count",
            prefixed=True,
            exit_code=2,
        )
    try:
        sources = [
            _read_content_bound_file(
                raw,
                source_hashes[index] if index < len(source_hashes) else None,
                label=f"unit-note attachment[{index}]",
            )
            for index, raw in enumerate(raw_sources)
        ]
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="unit.note.append.bad-file",
            prefixed=True,
            exit_code=2,
        ) from exc

    ctx.require_snapshot(req.get("expected_snapshot"))
    _, unit, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    stage_ids = list(dict.fromkeys(req.get("stage_id") or []))
    allowed = {row.get("id") for row in study_map.data.get("stages", []) or []}
    unknown = [stage_id for stage_id in stage_ids if stage_id not in allowed]
    if unknown:
        raise NotFound(
            "stage", unknown[0], allowed,
            message=f"stage does not belong to unit '{req['unit_id']}': {unknown[0]}",
            site="unit.note.append.unknown-stage",
            gateway_message=(f"los: stage does not belong to unit "
                             f"'{req['unit_id']}': {unknown[0]}"),
            exit_code=2,
        )

    unit_data = copy.deepcopy(unit.data)
    try:
        target, rel = _unit_note_target(root, unit)
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc),
            site="unit.note.append.note-outside-repo",
            prefixed=True,
            exit_code=2,
        ) from exc
    old = target.read_text(encoding="utf-8") if target.is_file() else ""
    recorded_at = observations.now().replace(microsecond=0).isoformat()
    title = " ".join((req.get("title") or "Learning session note").split()) \
        or "Learning session note"

    attachments: list[dict] = []
    attachment_writes: dict[Path, bytes] = {}
    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    attachment_dir = unit.path.parent / "attachments" / f"unit-note-{stamp}"
    try:
        for source, source_bytes in sources:
            target_file = attachment_dir / source.name
            suffix = 2
            while target_file.exists() or target_file in attachment_writes:
                target_file = attachment_dir / f"{suffix}-{source.name}"
                suffix += 1
            attachment_writes[target_file] = source_bytes
            attachments.append({
                "path": target_file.relative_to(root).as_posix(),
                "label": source.stem,
            })

        metadata = {
            "recorded_at": recorded_at,
            "title": title,
            "stage_ids": stage_ids,
            "attachments": attachments,
        }
        lines = [unit_note_marker(metadata), f"## {title}", "", value.rstrip()]
        if attachments:
            lines.extend(["", "### Attachments", ""] + [
                f"- [{item['label']}]({Path(item['path']).relative_to(unit.path.parent.relative_to(root)).as_posix()})"
                for item in attachments
            ])
        section = "\n".join(lines).rstrip() + "\n"
        divider = "\n" if old and not old.endswith("\n\n") else ""
        updated = old + divider + section
        if not unit_data.get("working_note"):
            unit_data["working_note"] = rel
        writes: dict[Path, str | bytes] = {
            target: updated,
            unit.path: _dump_yaml(unit_data),
            **attachment_writes,
        }
        try:
            expected_revisions = parse_expected_revisions(req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        return Result(
            {"ok": True, "unit_id": req["unit_id"], "working_note": rel,
             "recorded_at": recorded_at, "stage_ids": stage_ids,
             "attachments": attachments},
            proposal=TransactionProposal(
                capability="unit.note.append",
                writes=writes,
                artifact_ids=[req["unit_id"]],
                expected_revisions=expected_revisions,
            ),


        )
    except (OSError, WriteRefused) as exc:
        raise WriteRefused(
            f"cannot write unit note: {exc}",
            site="unit.note.append.write-failed",
            prefixed=True,
            exit_code=2,
        ) from exc


def _selection_used_by_current_map(repo, unit, route: dict, source_id: str,
                                   locator: str) -> bool:
    """Derive usage from the current map before editing a material choice.

    A stable route ID is authoritative when the resource has one. Older
    resources identify a choice by its exact source and locator; a shared
    source alone never means that this particular route is used.
    """
    study_map = repo.study_maps.get(unit.data.get("current_study_map"))
    if study_map is None:
        return False
    # Compact references retain identity even with a stage-specific locator;
    # expansion drops material_ref, so inspect the authored reference for this
    # mutation precondition, falling back for programmatically built maps.
    map_data = study_map.authored_data if study_map.authored_data is not None else study_map.data
    for stage in map_data.get("stages", []) or []:
        for resource in stage.get("resources", []) or []:
            material_ref = resource.get("material_ref")
            route_id = resource.get("route_id") or (
                material_ref.get("route_id") if isinstance(material_ref, dict) else None)
            if route_id:
                if route_id == route["id"]:
                    return True
            elif (resource.get("source_id"), resource.get("locator")) == (
                    source_id, locator):
                return True
    return False


@register("unit.source-selection.set", kind="command")
def unit_source_selection(ctx: OpContext, req: dict) -> Result:
    """Persist one learner choice without changing the complete material menu."""
    ctx.require_snapshot(req.get("expected_snapshot"))
    repo = ctx.repo()
    unit = repo.units.get(req["unit_id"])
    if unit is None:
        message = not_found("unit", req["unit_id"], repo.units)
        raise NotFound(
            "unit", req["unit_id"], repo.units,
            site="unit.source-selection.set.unknown-unit",
            gateway_message=f"los: {message}",
            exit_code=2,
        )
    if req["source_id"] not in repo.sources:
        message = not_found("source", req["source_id"], repo.sources)
        raise NotFound(
            "source", req["source_id"], repo.sources,
            site="unit.source-selection.set.unknown-source",
            gateway_message=f"los: {message}",
            exit_code=2,
        )

    source_map = repo.module_source_maps.get(unit.module_id, {})
    matching_route = None
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict) or source.get("source_id") != req["source_id"]:
            continue
        for route in source.get("unit_routes", []) or []:
            if (
                isinstance(route, dict)
                and route.get("unit_id") == req["unit_id"]
                and route.get("locator") == req["locator"]
            ):
                matching_route = route_with_identity(
                    unit.module_id, req["source_id"], route
                )
                break
        if matching_route is not None:
            break
    if matching_route is None:
        raise WriteRefused(
            "selection must match one rich material route on this unit "
            f"({req['source_id']} · {req['locator']})",
            site="unit.source-selection.set.no-matching-route",
            prefixed=True,
            exit_code=2,
        )

    unit_data = copy.deepcopy(unit.data)
    selections = list(unit_data.get("source_selections", []) or [])
    index = next((
        i for i, row in enumerate(selections)
        if isinstance(row, dict)
        and row.get("source_id") == req["source_id"]
        and row.get("locator") == req["locator"]
    ), None)

    if req["action"] == "select":
        purpose = str(req.get("purpose") or matching_route.get("angle") or "Chosen learning material").strip()
        if not purpose:
            raise WriteRefused(
                "a selected material needs a purpose",
                site="unit.source-selection.set.missing-purpose",
                prefixed=True,
                exit_code=2,
            )
        replacement = {
            "route_id": matching_route["id"],
            "source_id": req["source_id"],
            "locator": req["locator"],
            "purpose": purpose,
        }
        if index is None:
            selections.append(replacement)
        else:
            if selections[index].get("stage_ids"):
                replacement["stage_ids"] = list(selections[index]["stage_ids"])
            selections[index] = replacement
        selected = True
    elif req["action"] == "remove":
        if index is not None and _selection_used_by_current_map(
                repo, unit, matching_route, req["source_id"], req["locator"]):
            raise WriteRefused(
                "this choice is used by the current study path; remove it "
                "from those stages before removing the choice",
                site="unit.source-selection.set.used-by-map",
                prefixed=True,
                exit_code=2,
            )
        if index is not None:
            selections.pop(index)
        selected = False
    else:
        raise WriteRefused(
            f"unknown source-selection action: {req['action']} "
            "(choose from select, remove)",
            site="unit.source-selection.set.unknown-action",
            prefixed=True,
            exit_code=2,
        )

    unit_data["source_selections"] = selections
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="unit.source-selection.set.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "unit_id": req["unit_id"],
         "source_id": req["source_id"], "locator": req["locator"],
         "selected": selected},
        proposal=TransactionProposal(
            capability="unit.source-selection.set",
            writes={unit.path: _dump_yaml(unit_data)},
            artifact_ids=[req["unit_id"]],
            expected_revisions=expected_revisions,
        ),


    )
