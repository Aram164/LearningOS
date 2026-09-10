"""Append learner evidence through the existing snapshot/revision transaction."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

from learning_os.contracts.gateway import current_gateway_request
from learning_os.learning_runtime import (
    RuntimeInputError,
    collect_requirements,
    read_observations,
    requirement_fingerprint,
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


def cmd_observation_append(args) -> int:
    root = _root(args)
    if current_gateway_request() is None:
        print("los: observations require GatewayEnvelopeV2; direct CLI application is disabled", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        workspace = repo.workspaces.get(args.workspace)
        if workspace is None or workspace.archived or workspace.status != "active":
            print("los: observations require a registered active workspace", file=sys.stderr)
            return 2
        try:
            requirements = collect_requirements(repo)
            requirement = next((req for req in requirements if req["id"] == args.requirement), None)
            if requirement is None:
                raise RuntimeInputError(f"unknown requirement: {args.requirement}")
            source = requirement["source_stage"]
            if (source["module_id"] not in workspace.meta.get("module_ids", [])
                    and source["unit_id"] not in workspace.meta.get("unit_ids", [])):
                raise RuntimeInputError("requirement is outside the workspace's declared module/unit scope")
            historical = read_observations(repo, requirements)
            ledger = runtime_path(root, workspace.path.parent / "observations.jsonl")
            obs = {
                "id": "observation-" + uuid4().hex,
                "requirement": args.requirement,
                "requirement_sha256": requirement_fingerprint(requirement),
                "activity": args.activity,
                "result": args.result,
                "timestamp": datetime.now(UTC).isoformat(),
                "conditions": args.condition or [],
                "evidence_tags": [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()],
            }
            if args.assistance is not None:
                obs["assistance"] = args.assistance
            if args.context is not None:
                obs["context"] = args.context
            if args.supersedes:
                prior = next((item for item in historical if item["id"] == args.supersedes), None)
                if (prior is None or prior["requirement"] != args.requirement
                        or prior["origin"]["path"] != ledger.relative_to(root).as_posix()
                        or any(item.get("supersedes") == prior["id"] for item in historical)):
                    raise RuntimeInputError("correction must supersede one uncorrected observation of this requirement in this ledger")
                obs["supersedes"] = args.supersedes
            validate_runtime_record(repo, "learner-observation", obs)
            try:
                old = ledger.read_text(encoding="utf-8")
            except FileNotFoundError:
                old = ""
            separator = "\n" if old and not old.endswith("\n") else ""
            new = old + separator + json.dumps(obs, sort_keys=True, ensure_ascii=False) + "\n"
            code, errors, confirmation = _write_transaction(
                root, {ledger: new}, capability="learner.observation.append",
                expected_revisions=_expected_revisions_from_args(args), artifact_ids=[workspace.id],
            )
            if code:
                for error in errors[:12]:
                    print(error, file=sys.stderr)
                return code
        except (RuntimeInputError, OSError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
    print(json.dumps({"ok": True, "observation_id": obs["id"], "workspace_id": workspace.id, **confirmation}))
    return 0
