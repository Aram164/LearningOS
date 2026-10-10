"""Learner-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from learning_os import observations
from learning_os.domain.failures import WriteRefused
from learning_os.learning_runtime import requirement_id_for
from learning_os.ops._legacy_plumbing import (
    _dump_study_map,
    _dump_yaml,
    _read_content_bound_file,
)
from learning_os.ops.context import OpContext
from learning_os.ops.handlers._shared import (
    require_path_or_error,
    require_stage,
    require_unit_map_or_error,
)
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions


def _dumps_stage(payload: dict) -> str:
    """The exact stage encoder: default separators, unescaped."""
    return json.dumps(payload, ensure_ascii=False)


def _on_commit_refused(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


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
    stages = data.get("stages", []) or []
    stage = require_stage(ctx, data, req["stage_id"])
    action = req["status"]
    if action in {"active", "revisit"}:
        for other in stages:
            if other.get("status") in {"active", "paused"}:
                other["status"] = "pending"
        stage["status"] = "active"
        stage.pop("completed", None)
        data["current_stage"] = stage["id"]
        data["status"] = "active"
        unit_data["status"] = "active"
    elif action == "paused":
        stage["status"] = "paused"
        data["current_stage"] = stage["id"]
        data["status"] = "paused"
        unit_data["status"] = "paused"
    elif action in {"complete", "skipped"}:
        if stage.get("status") != "active":
            raise WriteRefused(
                "complete/skip applies only to the active stage; activate it first",
                site=f"{ctx.operation}.not-active",
                gateway_message=("los: complete/skip applies only to the active "
                                 "stage; activate it first"),
                exit_code=2,
            )
        stage["status"] = action
        if action == "complete":
            stage["completed"] = observations.today().isoformat()
        following = next((row for row in stages[stages.index(stage) + 1:]
                          if row.get("status") == "pending"), None)
        if following:
            following["status"] = "active"
            data["current_stage"] = following["id"]
            data["status"] = "active"
            unit_data["status"] = "active"
        else:
            data["status"] = "ready-to-shelve"
            data.setdefault("shelving", {})["state"] = "draft"
            unit_data["status"] = "ready-to-shelve"
    else:
        # The gateway schema and payload_to_namespace refuse unknown
        # values first; this is the last backstop. An open `else` here
        # once recorded an unknown status as `skipped`.
        raise WriteRefused(
            f"unknown stage status: {action} "
            "(choose from active, paused, complete, skipped, revisit)",
            site=f"{ctx.operation}.unknown-status",
            gateway_message=(f"los: unknown stage status: {action} "
                             "(choose from active, paused, complete, skipped, "
                             "revisit)"),
            exit_code=2,
        )
    summary = req.get("progress_summary")
    upcoming = req.get("progress_next")
    if summary is not None or upcoming is not None:
        if summary is None or not summary.strip():
            raise WriteRefused(
                "--progress-next needs --progress-summary",
                site=f"{ctx.operation}.needs-summary",
                gateway_message="los: --progress-next needs --progress-summary",
                exit_code=2,
            )
        if upcoming is not None and not upcoming.strip():
            raise WriteRefused(
                "--progress-next must not be blank",
                site=f"{ctx.operation}.blank-next",
                gateway_message="los: --progress-next must not be blank",
                exit_code=2,
            )
        entry = {"updated": observations.today().isoformat(),
                 "summary": summary.strip()}
        if upcoming is not None:
            entry["next"] = upcoming.strip()
        stage["progress"] = entry
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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_stage,
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
            gateway_message="los: stage has no working_note",
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
            gateway_message="los: refusing to write an empty note — pass real text",
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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_stage,
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
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc
    ctx.require_snapshot(req.get("expected_snapshot"))
    _, _, study_map = require_unit_map_or_error(ctx, req["unit_id"])
    data = copy.deepcopy(study_map.data)
    stage = require_stage(ctx, data, req["stage_id"])
    note_path = root / stage["working_note"]
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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_stage,
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
            gateway_message=f"los: stage has no notes_path: {req['stage_id']}",
            exit_code=2,
        )
    text_value = req.get("text") if req.get("text") is not None else sys.stdin.read()
    if not text_value.strip():
        raise WriteRefused(
            "refusing to write an empty note — pass real text",
            site="path.note.write.empty-note",
            gateway_message="los: refusing to write an empty note — pass real text",
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
        on_commit_refused=_on_commit_refused,
        json_dumps=_dumps_stage,
    )
