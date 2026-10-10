"""Snapshot-bound ability horizon and focused expansion."""

from __future__ import annotations

import json
import sys
from datetime import UTC

from jsonschema import Draft202012Validator, FormatChecker

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
)

from .. import observations
from ..abilities import (
    read_ability_candidates,
)
from ..contracts.gateway import current_gateway_request
from ..domain.failures import WriteRefused
from ..learning_runtime import runtime_path
from ..loader import load_repo
from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _write_transaction,
)


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
                "id": "ability-candidate-" + observations.new_hex(),
                "from": args.from_ability, "to": args.to_ability,
                "kind": args.kind, "carries": args.carries,
                "changes": args.changes, "conditions": list(args.condition),
                "source_ref": args.source_ref,
                "created_at": observations.now().astimezone(UTC).isoformat(),
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
