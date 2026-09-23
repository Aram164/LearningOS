"""Snapshot-bound ability horizon and focused expansion."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

from ..abilities import (
    ability_context,
    ability_fingerprint,
    read_ability_candidates,
    read_ability_observations,
)
from ..contracts.gateway import current_gateway_request
from ..learning_runtime import runtime_path
from ..loader import load_repo
from .reads import _print_stable, _snapshot
from .support import (
    WriteRefused,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _root,
    _write_transaction,
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


def cmd_ability_context(args) -> int:
    root = _root(args)
    try:
        if not 1 <= args.limit <= 50:
            raise WriteRefused("ability-context limit must be 1..50")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            if repo.parse_failures:
                raise WriteRefused("ability-context refuses unreadable canonical records")
            payload = ability_context(repo, focus=args.ability_id, limit=args.limit)
            return _print_stable(root, snapshot, {"contract": "ability-context-v1", **payload})
    except (WriteRefused, OSError, ValueError) as exc:
        from .reads import _refusal
        return _refusal(exc)


def cmd_ability_observation_append(args) -> int:
    """Record an exact learner-confirmed claim; the V2 approval binds payload."""
    root = _root(args)
    request = current_gateway_request()
    if request is None:
        print("los: ability observations require GatewayEnvelopeV2", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        workspace = repo.workspaces.get(args.workspace)
        if workspace is None or workspace.archived or workspace.status != "active":
            print("los: a registered active workspace must own this work", file=sys.stderr)
            return 2


        ability = repo.abilities.get(args.ability)
        if (ability is None or ability.get("review", {}).get("state") != "reviewed"
                or ability.get("lifecycle") == "retired"):
            print("los: evidence requires an active reviewed ability identity", file=sys.stderr)
            return 2
        if not _valid_work_ref(args.work_ref):
            print("los: work-ref must safely point to conversation, note, project, or curriculum work", file=sys.stderr)
            return 2
        if not args.confirmation_ref.startswith(("conversation://", "note://")):
            print("los: confirmation-ref must point to Aram's confirmation", file=sys.stderr)
            return 2
        if (request.channel == "ui" and args.confirmation_ref !=
                f"conversation://learningos-app/{request.idempotency_key}"):
            print("los: app confirmation-ref must name this exact request", file=sys.stderr)
            return 2
        try:
            history = read_ability_observations(repo)
            path = runtime_path(root, workspace.path.parent / "ability-observations.jsonl")
            if args.supersedes:
                prior = next((row for row in history if row["id"] == args.supersedes), None)
                if (prior is None or prior["ability_id"] != args.ability
                        or prior["origin"]["path"] != path.relative_to(root).as_posix()
                        or any(row.get("supersedes") == prior["id"] for row in history)):
                    raise WriteRefused("correction must supersede one uncorrected observation in this ledger")
            row = {
                "id": "ability-observation-" + uuid4().hex,
                "ability_id": args.ability,
                "ability_sha256": ability_fingerprint(ability),
                "claim": args.claim,
                "work_ref": args.work_ref,
                "confirmation_ref": args.confirmation_ref,
                "activity": args.activity,
                "result": args.result,
                "timestamp": datetime.now(UTC).isoformat(),
                "conditions": list(args.condition),
                "evidence_tags": list(args.evidence_tag),
                "assistance": args.assistance,
                "confirmed_by": "learner",
            }
            if args.condition_not_met:
                row["conditions_not_met"] = list(args.condition_not_met)
            if args.supersedes:
                row["supersedes"] = args.supersedes
            if set(row["conditions"]) & set(row.get("conditions_not_met", [])):
                raise WriteRefused("condition cannot be both met and not met")
            schema = json.loads((root / "system/schema/ability-observation.schema.json").read_text())
            errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(row), key=str)
            if errors:
                raise WriteRefused(f"ability observation: {errors[0].message}")
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            new = old + ("\n" if old and not old.endswith("\n") else "")
            new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
            code, errors, confirmation = _write_transaction(
                root, {path: new}, capability="learner.ability-observation.append",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=[workspace.id],
            )
            if code:
                for error in errors[:12]:
                    print(error, file=sys.stderr)
                return code
            print(json.dumps({"ok": True, "observation_id": row["id"], **confirmation}))
            return 0
        except (WriteRefused, OSError, ValueError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2


def cmd_ability_candidate_append(args) -> int:
    """Capture a tentative cross-ability connection; it never grants credit."""
    root = _root(args)
    if current_gateway_request() is None:
        print("los: ability candidates require GatewayEnvelopeV2", file=sys.stderr)
        return 2
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        repo = load_repo(root)
        if (args.from_ability not in repo.abilities or args.to_ability not in repo.abilities
                or args.from_ability == args.to_ability
                or repo.abilities[args.from_ability].get("lifecycle") == "retired"
                or repo.abilities[args.to_ability].get("lifecycle") == "retired"):
            print("los: candidate endpoints must be two active abilities", file=sys.stderr)
            return 2
        if not args.source_ref.startswith(("conversation://", "note://", "project://")):
            print("los: candidate source-ref must identify the discovery", file=sys.stderr)
            return 2
        try:
            read_ability_candidates(repo)
            path = runtime_path(root, root / "knowledge/ability-candidates.jsonl")
            row = {
                "id": "ability-candidate-" + uuid4().hex,
                "from": args.from_ability, "to": args.to_ability,
                "kind": args.kind, "carries": args.carries,
                "changes": args.changes, "conditions": list(args.condition),
                "source_ref": args.source_ref,
                "created_at": datetime.now(UTC).isoformat(),
                "state": "candidate",
            }
            schema = json.loads((root / "system/schema/ability-candidate.schema.json").read_text())
            errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(row), key=str)
            if errors:
                raise WriteRefused(f"ability candidate: {errors[0].message}")
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            new = old + ("\n" if old and not old.endswith("\n") else "")
            new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
            code, errors, confirmation = _write_transaction(
                root, {path: new}, capability="ability.candidate.append",
                expected_revisions=_expected_revisions_from_args(args),
                artifact_ids=["ability-candidates"],
            )
            if code:
                for error in errors[:12]:
                    print(error, file=sys.stderr)
                return code
            print(json.dumps({"ok": True, "candidate_id": row["id"], **confirmation}))
            return 0
        except (WriteRefused, OSError, ValueError) as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
