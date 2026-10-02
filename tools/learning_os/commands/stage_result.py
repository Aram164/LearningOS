"""Append untargeted learner results against a unit/stage.

``stage-result`` is the intake for stages that carry no requirement target
yet (WORKFLOWS §8): activity, result, assistance, optional conditions and a
note, in the same append-only workspace-ledger style as observations —
``stage-results.jsonl`` beside the workspace's ``CONTEXT.md``, with the
same tested ``--supersedes`` correction path. It has no credit, mastery or
requirement semantics: the evidence interpreters read the observation
ledgers only, so these rows stay context even after a target is authored,
and are never retro-credited.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

from learning_os.contracts.gateway import current_gateway_request
from learning_os.learning_runtime import (
    RuntimeInputError,
    read_stage_results,
    runtime_path,
    validate_runtime_record,
)
from learning_os.loader import load_repo

from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
)

STAGE_RESULT_CAPABILITY = "learner.stage-result.append"


def cmd_stage_result(args) -> int:
    root = _root(args)
    if current_gateway_request() is None:
        print("los: stage results require GatewayEnvelopeV2; direct CLI application is disabled",
              file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        workspace = repo.workspaces.get(args.workspace)
        if workspace is None or workspace.archived or workspace.status != "active":
            print("los: stage results require a registered active workspace", file=sys.stderr)
            return 2
        try:
            unit = repo.units.get(args.unit)
            if unit is None:
                raise RuntimeInputError(f"unknown unit: {args.unit}")
            study_map = repo.study_maps.get((unit.data or {}).get("current_study_map"))
            if study_map is None or study_map.unit_id != unit.id \
                    or study_map.module_id != unit.module_id:
                raise RuntimeInputError(f"unit {unit.id} has no current study map")
            stage = next((item for item in study_map.data.get("stages", [])
                          if isinstance(item, dict) and item.get("id") == args.stage), None)
            if stage is None:
                raise RuntimeInputError(
                    f"unknown stage {args.stage} in unit {unit.id}")
            if (unit.module_id not in workspace.meta.get("module_ids", [])
                    and unit.id not in workspace.meta.get("unit_ids", [])):
                raise RuntimeInputError("stage is outside the workspace's declared module/unit scope")
            historical = read_stage_results(repo)
            ledger = runtime_path(root, workspace.path.parent / "stage-results.jsonl")
            row = {
                "id": "stage-result-" + uuid4().hex,
                "unit": unit.id,
                "stage": stage["id"],
                "activity": args.activity,
                "result": args.result,
                "timestamp": datetime.now(UTC).isoformat(),
                "conditions": list(args.condition or []),
            }
            if args.assistance is not None:
                row["assistance"] = args.assistance
            if args.note is not None:
                row["note"] = args.note
            if args.supersedes:
                prior = next((item for item in historical if item["id"] == args.supersedes), None)
                if (prior is None or prior["unit"] != unit.id
                        or prior["stage"] != stage["id"]
                        or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                        or any(item.get("supersedes") == prior["id"] for item in historical)):
                    raise RuntimeInputError("correction must supersede one uncorrected stage result of this unit/stage in this ledger")
                row["supersedes"] = args.supersedes
            validate_runtime_record(repo, "learner-stage-result", row)
            try:
                old = ledger.read_text(encoding="utf-8")
            except FileNotFoundError:
                old = ""
            separator = "\n" if old and not old.endswith("\n") else ""
            new = old + separator + json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
            code, errors, confirmation = _write_transaction(
                root, {ledger: new}, capability=STAGE_RESULT_CAPABILITY,
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=[workspace.id],
            )
            if code:
                for error in errors[:12]:
                    print(error, file=sys.stderr)
                return code
        except (RuntimeInputError, OSError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
    result = {"ok": True, "stage_result_id": row["id"],
              "workspace_id": workspace.id, "unit": unit.id,
              "stage": stage["id"], "credit": "none",
              **confirmation}
    print(json.dumps(result))
    return 0
