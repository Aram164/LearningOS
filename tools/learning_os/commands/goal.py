"""Aram's explicit goal decisions: the scan's dedup channel, finally fed.

Detectors emit every candidate forever unless told otherwise — ``known_ids``
existed on every detector and ``collect_observations`` never supplied it.
This ledger is the other end: one map of ``goal_id -> {state, decided_at,
note}`` under ``operations/``, written only by ``los goal <id>
--reject|--defer|--close`` and read back by the scan as ``known_ids``.
Rejected goals stay rejected; the queue stops re-emitting what Aram
already decided.

Only decidable ids are accepted: a goal in the current scan, or already in
the ledger. The decision joins the caller's session ledger under the same
identity the gateway and ``session-end`` resolve, so it is listed and
committed with the rest of the session's writes.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from learning_os.semantics.scan import intelligence_scan

from .suggest import not_found
from .support import (
    TOOLS,
    WriteRefused,
    _atomic_text,
    _current_session_id,
    _load_session_paths,
    _operator_lock,
    _record_touched,
    _root,
    _session_ledger,
)

LEDGER_RELATIVE = "operations/goal-ledger.yaml"


def _schema() -> dict:
    root = TOOLS.parent
    return json.loads((root / "system/schema/goal-ledger.schema.json").read_text(encoding="utf-8"))


def _validate_ledger(data: dict) -> list[str]:
    errors = sorted(
        Draft202012Validator(_schema(), format_checker=FormatChecker()).iter_errors(data),
        key=str,
    )
    return [f"goal ledger: {error.message}" for error in errors]


def cmd_goal(args) -> int:
    """Record one explicit goal decision. ``los goal <id> --reject|--defer|--close``."""
    root = _root(args)
    supplied = args.goal_id if isinstance(args.goal_id, list) else [args.goal_id]
    goal_ids = [item.strip() for item in supplied if isinstance(item, str)]
    if len(goal_ids) != len(supplied) or not goal_ids or len(set(goal_ids)) != len(goal_ids) \
            or any(not item or any(char.isspace() for char in item)
                   or any(char in item for char in "*?[]") for item in goal_ids):
        print("los: supply distinct exact goal ids, each one whitespace-free token; patterns are refused",
              file=sys.stderr)
        return 2
    state = "rejected" if args.reject else "deferred" if args.defer else "closed"
    revisit_on = getattr(args, "revisit_on", None)
    if revisit_on is not None:
        if state != "deferred":
            print("los: --revisit-on requires --defer", file=sys.stderr)
            return 2
        try:
            if not isinstance(revisit_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", revisit_on):
                raise ValueError("not YYYY-MM-DD")
            day = _dt.date.fromisoformat(revisit_on)
        except (TypeError, ValueError):
            print("los: --revisit-on needs an ISO date (YYYY-MM-DD)", file=sys.stderr)
            return 2
        if day <= _dt.date.today():
            print("los: --revisit-on must be a future date", file=sys.stderr)
            return 2
    with _operator_lock(root):
        path = root / LEDGER_RELATIVE
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raw = ""
        except OSError as exc:
            print(f"los: cannot read the goal ledger: {exc}", file=sys.stderr)
            return 2
        if not raw.strip():
            data: dict = {"schema_version": 1, "type": "goal-ledger", "decisions": {}}
        else:
            try:
                loaded = yaml.safe_load(raw)
            except yaml.YAMLError as exc:
                print(f"los: the goal ledger is malformed, refusing to clobber it: {exc}",
                      file=sys.stderr)
                return 2
            if not isinstance(loaded, dict):
                print("los: the goal ledger is malformed, refusing to clobber it",
                      file=sys.stderr)
                return 2
            data = loaded
        decisions = data.get("decisions")
        if not isinstance(decisions, dict):
            print("los: the goal ledger is malformed, refusing to clobber it",
                  file=sys.stderr)
            return 2
        # Only decidable ids: a goal in the current scan, or already in the
        # ledger (a goal that stopped being detected can still be closed or
        # re-decided). Unknown ids refuse before anything is written, so a
        # batch is all-or-nothing. A scan that cannot be read degrades to
        # ledger-only rather than inventing candidates.
        try:
            scan_ids = {goal.goal_id for goal in intelligence_scan(root)}
            scan_failed: Exception | None = None
        except Exception as exc:  # noqa: BLE001 - fail closed to ledger-only
            scan_ids = set()
            scan_failed = exc
        known = {key for key in decisions if isinstance(key, str)} | scan_ids
        unknown = [goal_id for goal_id in goal_ids if goal_id not in known]
        if unknown:
            if scan_failed is not None:
                print(f"los: the live scan is unavailable ({scan_failed}); "
                      f"deciding only ledger-known ids", file=sys.stderr)
            candidates = sorted(known)
            for goal_id in unknown:
                print(f"los: {not_found('goal', goal_id, candidates)}",
                      file=sys.stderr)
            return 2
        entry: dict = {"state": state, "decided_at": _dt.date.today().isoformat()}
        if revisit_on is not None:
            entry["revisit_on"] = revisit_on
        if args.note is not None:
            entry["note"] = args.note
        reviewed = {
            "ledger_bytes_sha256": "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "goal_ids": goal_ids,
            "decision": entry,
        }
        review_sha = "sha256:" + hashlib.sha256(json.dumps(
            reviewed, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        data["decisions"] = {**decisions, **{goal_id: dict(entry) for goal_id in goal_ids}}
        problems = _validate_ledger(data)
        if problems:
            print(f"los: {problems[0]}", file=sys.stderr)
            return 2
        if getattr(args, "check", False):
            print(json.dumps({"ok": True, "check": True, "reviewed_sha256": review_sha,
                              "goal_ids": goal_ids, "state": state,
                              "changes": [{"goal_id": goal_id, "before": decisions.get(goal_id),
                                           "after": entry} for goal_id in goal_ids]}))
            return 0
        expected = getattr(args, "reviewed_sha256", None)
        if (len(goal_ids) > 1 and expected is None) or (expected is not None and expected != review_sha):
            print("los: batch apply needs the exact --check reviewed-sha256; changed ledger or decisions require a fresh review",
                  file=sys.stderr)
            return 3
        # The decision joins the caller's session, so session-end lists and
        # commits the ledger with the rest of the session's writes. Identity
        # resolves exactly as the gateway and session-end do (explicit
        # --session-id, then the envelope, then LOS_SESSION_ID, then the
        # channel). Preflight the own ledger first: a corrupt ledger refuses
        # before the decision is written, never after.
        explicit_session = getattr(args, "session_id", None)
        own_session = _current_session_id(explicit=explicit_session)
        if _session_ledger(root, own_session).is_file():
            try:
                _load_session_paths(root, own_session)
            except WriteRefused as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
        try:
            _atomic_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        except WriteRefused as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
        try:
            _record_touched(root, [path], session_id=explicit_session)
        except WriteRefused as exc:
            # The decision above is durable; only the session claim failed
            # (a concurrent writer replaced our ledger mid-command). Exit 2
            # would falsely claim nothing was written.
            print(f"los: decision recorded but the session ledger could not be "
                  f"updated: {exc}", file=sys.stderr)
            return 1
    result = {"ok": True, "state": state}
    result["goal_id" if len(goal_ids) == 1 else "goal_ids"] = goal_ids[0] if len(goal_ids) == 1 else goal_ids
    if revisit_on is not None:
        result["revisit_on"] = revisit_on
    print(json.dumps(result))
    return 0
