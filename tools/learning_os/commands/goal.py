"""Aram's explicit goal decisions: the scan's dedup channel, finally fed.

Detectors emit every candidate forever unless told otherwise — ``known_ids``
existed on every detector and ``collect_observations`` never supplied it.
This ledger is the other end: one map of ``goal_id -> {state, decided_at,
note}`` under ``operations/``, written only by ``los goal <id>
--reject|--defer|--close`` and read back by the scan as ``known_ids``.
Rejected goals stay rejected; the queue stops re-emitting what Aram
already decided.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .support import TOOLS, WriteRefused, _atomic_text, _operator_lock, _root

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
    goal_id = (args.goal_id or "").strip()
    if not goal_id or any(char.isspace() for char in goal_id):
        print("los: goal id is one whitespace-free token", file=sys.stderr)
        return 2
    state = "rejected" if args.reject else "deferred" if args.defer else "closed"
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
        entry: dict = {"state": state, "decided_at": _dt.date.today().isoformat()}
        if args.note is not None:
            entry["note"] = args.note
        data["decisions"] = {**decisions, goal_id: entry}
        problems = _validate_ledger(data)
        if problems:
            print(f"los: {problems[0]}", file=sys.stderr)
            return 2
        try:
            _atomic_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        except WriteRefused as exc:
            print(f"los: {exc}", file=sys.stderr)
            return 2
    print(json.dumps({"ok": True, "goal_id": goal_id, "state": state}))
    return 0
