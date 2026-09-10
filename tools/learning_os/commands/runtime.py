"""Snapshot-bound, read-only session proposal and bounded repair entry point."""

from __future__ import annotations

import json
import sys

from learning_os.contracts.json_schema import ContractValidationError, validate_contract
from learning_os.fingerprint import canonical_fingerprint
from learning_os.genout.learner_interpreter import _collect_and_interpret
from learning_os.genout.session_compiler import compile_session, replan_session
from learning_os.learning_runtime import RuntimeInputError, collect_requirements
from learning_os.loader import load_repo

from .support import _operator_lock, _root


def cmd_runtime_session(args) -> int:
    root = _root(args)
    try:
        with _operator_lock(root):
            before = f"sha256:{canonical_fingerprint(root)}"
            if args.expected_snapshot is not None and args.expected_snapshot != before:
                print("los: snapshot changed; reload before proposing a session", file=sys.stderr)
                return 3
            context = json.loads(args.context_json)
            repo = load_repo(root)
            requirement = next((r for r in collect_requirements(repo) if r["id"] == args.requirement), None)
            if requirement is None:
                raise RuntimeInputError(f"unknown requirement: {args.requirement}")
            interpretation = _collect_and_interpret(repo)[requirement["id"]]
            if bool(args.previous_json) != bool(args.event):
                raise RuntimeInputError("bounded repair requires both --previous-json and --event")
            if args.previous_json:
                previous_packet = json.loads(args.previous_json)
                validate_contract(root, "runtime-session.schema.json", previous_packet)
                if previous_packet.get("snapshot_id") != before:
                    print("los: previous proposal belongs to a different snapshot; propose a fresh session", file=sys.stderr)
                    return 3
                session = replan_session(repo, previous_packet, requirement,
                                         interpretation, context, args.event, before)
            else:
                session = compile_session(repo, requirement, interpretation, context)
            result = {"contract": "runtime-session-v1", "schema_version": 1,
                      "snapshot_id": before, "session": session}
            validate_contract(root, "runtime-session.schema.json", result)
            if before != f"sha256:{canonical_fingerprint(root)}":
                print("los: snapshot changed during runtime read; retry", file=sys.stderr)
                return 3
            print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0
    except (RuntimeInputError, ContractValidationError, json.JSONDecodeError, OSError) as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
