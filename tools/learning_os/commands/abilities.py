"""Snapshot-bound ability horizon and focused expansion."""

from __future__ import annotations

import json
import sys
from datetime import UTC

from jsonschema import Draft202012Validator, FormatChecker

from learning_os.ops._legacy_plumbing import (
    _operator_lock,
    _snapshot,
)

from .. import observations
from ..abilities import (
    ability_context,
    read_ability_candidates,
)
from ..contracts.gateway import current_gateway_request
from ..contracts.json_schema import validate_contract
from ..domain.failures import WriteRefused
from ..domain.suggest import suggest
from ..learning_runtime import runtime_path
from ..loader import load_repo
from .reads import _print_stable
from .support import (
    _expected_ok,
    _expected_revisions_from_args,
    _root,
    _write_transaction,
)


def cmd_ability_context(args) -> int:
    root = _root(args)
    try:
        if not 1 <= args.limit <= 50:
            raise WriteRefused("ability-context limit must be 1..50")
        brief = getattr(args, "brief", False)
        section = getattr(args, "section", None)
        if brief and not args.ability_id:
            raise WriteRefused("ability-context --brief needs a named ability")
        if section and not args.ability_id:
            raise WriteRefused("ability-context --section needs a named ability")
        if brief and section:
            raise WriteRefused("ability-context takes --brief or --section "
                               "evidence, not both")
        offset = getattr(args, "offset", 0) or 0
        if offset < 0:
            raise WriteRefused("ability-context offset must be nonnegative")
        if args.ability_id and offset and not section:
            raise WriteRefused("ability-context --offset pages the global "
                               "horizon or --section evidence, not a focused "
                               "ability")
        if brief and args.limit != 12:
            # 12 is the parser default: an explicit window on a single
            # summary is silently meaningless, so it refuses instead.
            raise WriteRefused("ability-context --brief is one summary; page "
                               "evidence with --section evidence")
        if offset and not args.expected_snapshot:
            raise WriteRefused("continuation requires --expected-snapshot from the "
                               "previous response")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            if repo.parse_failures:
                raise WriteRefused("ability-context refuses unreadable canonical records")
            payload = ability_context(repo, focus=args.ability_id, limit=args.limit,
                                      offset=offset, brief=brief, section=section,
                                      snapshot=snapshot)
            if (args.ability_id is not None
                    and args.ability_id not in repo.abilities
                    and payload.get("state") == "unmapped"):
                # An unknown identity, not a known-but-unmapped ability.
                # The unmapped shape stays what the UI reads (its decoder
                # tolerates extra keys); the flag and suggestions say this
                # is a mistyped id and where to look next.
                payload["known_identity"] = False
                payload["suggestions"] = suggest(args.ability_id, repo.abilities)
            result = {"schema_version": 1, "snapshot_id": snapshot,
                      "contract": "ability-context-v1", **payload}
            validate_contract(root, "ability-context.schema.json", result)
            rows = payload.get("abilities", [])
            if "ability" in payload:
                rows = [payload["ability"]]
            for row in rows:
                reasons, codes = row.get("reasons"), row.get("reason_codes")
                if not isinstance(reasons, list) or not isinstance(codes, list) \
                        or len(reasons) != len(codes):
                    raise WriteRefused("ability-context reason_codes must be parallel to reasons")
            return _print_stable(root, snapshot, result)
    except (WriteRefused, OSError, ValueError) as exc:
        from .reads import _refusal
        return _refusal(exc)


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
