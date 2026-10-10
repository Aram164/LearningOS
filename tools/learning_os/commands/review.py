"""Review surfaces: shelving prepare/apply and the explicit session close."""

from __future__ import annotations

import copy
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path

from learning_os import observations
from learning_os.contracts.gateway import GATEWAY_CHANNELS
from learning_os.domain.failures import WriteRefused
from learning_os.ops._legacy_plumbing import (
    _current_session_id,
    _dump_study_map,
    _load_session_paths,
    _operator_lock,
    _publish,
    _row_proven_state,
    _row_recorded_at,
    _session_ledger,
    _session_path_state,
)

from .support import (
    CLIENT_ENV,
    SESSION_LEDGER_STALE_HOURS,
    _expected_ok,
    _expected_revisions_from_args,
    _load_other_session_ledgers,
    _root,
    _row_is_stale,
    _unit_map_or_error,
    _write_transaction,
)

TOOLS = Path(__file__).resolve().parent.parent.parent

def _approved_destination(root: Path, item: dict) -> Path | None:
    rel = str(item.get("destination", ""))
    target = (root / rel).resolve()
    allowed = (root / "knowledge" / "notes").resolve(), (root / "knowledge" / "garden").resolve()
    if not any(parent == target or parent in target.parents for parent in allowed):
        return None
    return target


def cmd_shelving_apply(args) -> int:
    if not args.approve:
        print("los: shelving apply requires --approve and explicit selected proposal IDs",
              file=sys.stderr)
        return 2
    root = _root(args)
    selected = set(args.selected)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        shelving = data.get("shelving") or {}
        items = [item for item in shelving.get("items", []) or []
                 if item.get("id") in selected]
        if not items or {item.get("id") for item in items} != selected:
            print("los: every selected ID must exist in the current proposal", file=sys.stderr)
            return 2
        writes: dict[Path, str] = {}
        for item in items:
            target = _approved_destination(root, item)
            if target is None or target.exists():
                print(f"los: unsafe or existing shelving destination: {item.get('destination')}",
                      file=sys.stderr)
                return 2
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                print(f"los: proposal item {item.get('id')} has no reviewable content", file=sys.stderr)
                return 2
            writes[target] = content.rstrip() + "\n"
        shelving["state"] = "applied"
        writes[study_map.path] = _dump_study_map(study_map, data)
        code, errors, confirmation = _write_transaction(
            root, writes, capability="review.apply",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id, *sorted(selected)],
        )
        if code:
            print("los: approved shelving changes failed validation and were rolled back",
                  file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "applied": sorted(selected),
                      **confirmation}, ensure_ascii=False))
    return 0


def _other_session_summary(rows: dict[str, dict]) -> dict:
    """One foreign session's rows for the `other_sessions` report.

    Fresh and stale rows are listed separately; the age is the oldest row's.
    Undated rows (the pre-session `legacy` file) count as stale — their age
    cannot be proven.
    """
    now = observations.now().astimezone(_dt.UTC)
    fresh = sorted(path for path, row in rows.items() if not _row_is_stale(row, now))
    stale = sorted(path for path, row in rows.items() if _row_is_stale(row, now))
    moments = [moment for row in rows.values()
               if (moment := _row_recorded_at(row)) is not None]
    oldest = min(moments) if moments else None
    return {
        "paths": fresh,
        "stale_paths": stale,
        "oldest_recorded_at": oldest.isoformat() if oldest else None,
        "age_hours": round((now - oldest).total_seconds() / 3600, 2)
        if oldest else None,
    }


def cmd_session_end(args) -> int:
    root = _root(args)
    if getattr(args, "close", False) and args.commit_message:
        print("los: --close and --commit-message are mutually exclusive: "
              "closing discards the ownership window instead of committing it",
              file=sys.stderr)
        return 2
    channel = getattr(args, "channel", None)
    if channel is not None and channel not in GATEWAY_CHANNELS:
        print(f"los: unknown session channel {channel!r} "
              f"(one of: {', '.join(sorted(GATEWAY_CHANNELS))})", file=sys.stderr)
        return 2
    own_session = _current_session_id(channel=channel,
                                      explicit=getattr(args, "session_id", None))
    ledger = _session_ledger(root, own_session)
    try:
        recorded = _load_session_paths(root, own_session)
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    others = _load_other_session_ledgers(root, own_session)
    include_stale = bool(getattr(args, "include_stale", False))
    fresh = sorted(
        path for path, row in recorded.items()
        if Path(path).suffix.lower() != ".canvas" and not _row_is_stale(row)
    )
    stale_paths = sorted(
        path for path, row in recorded.items()
        if Path(path).suffix.lower() != ".canvas" and _row_is_stale(row)
    )
    # Only this session's own rows are ever claimed; foreign rows are
    # reported under `other_sessions` and never staged, and stale own rows
    # need the explicit opt-in.
    touched = sorted(fresh + stale_paths) if include_stale else fresh
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != _row_proven_state(recorded[path])
    ]
    # `validate.py` resolves its repository from its own location unless told
    # otherwise, so a bare `cwd=root` would validate the repository the tools
    # live in — not the one this session touched. Pass the root explicitly.
    # --compact: a failed close prints its errors and the summary line, not
    # every baselined warning; the full list is in the validation report.
    validation = subprocess.run(
        [sys.executable, str(TOOLS / "validate.py"), "--compact", "--root", str(root)],
        cwd=root, capture_output=True, text=True)
    if validation.returncode != 0:
        print(validation.stdout, end="")
        print(validation.stderr, end="", file=sys.stderr)
        return validation.returncode or 1
    # Errors gate; warnings are advisory and reported. Gating on zero warnings
    # made session-end impossible in a repository carrying the by-design
    # "material may be offline" set. External link rot is gated only by the
    # explicit online validator and never runs during session-end.
    validation_line = next((line for line in validation.stdout.splitlines()
                            if "warning(s)" in line), "").strip()
    with _operator_lock(root):
        _publish(root)
    all_changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        cwd=root, capture_output=True, text=True, timeout=30,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.splitlines()
    owned = [line for line in all_changed if line[3:] in touched]
    unrelated = [line for line in all_changed if line[3:] not in touched]
    payload = {"ok": True, "touched": touched, "owned_changes": owned,
               "unrelated_changes": unrelated, "committed": False, "pushed": False,
               "validation": validation_line,
               "ownership_conflicts": ownership_conflicts,
               "session_id": own_session,
               # The calling client when it marks itself (`obsidian-ui/<build>`
               # on every UI-spawned child); None for terminal agents, which
               # stay valid unmarked. Informational: never a refusal input.
               "client": os.environ.get(CLIENT_ENV),
               "stale_paths": stale_paths,
               "stale_hours": SESSION_LEDGER_STALE_HOURS,
               "other_sessions": {
                   identity: _other_session_summary(rows)
                   for identity, rows in sorted(others.items())
               }}
    if not args.commit_message:
        # A review never closes: it validates, publishes, and lists owned
        # and unrelated changes while the ledger survives, so the documented
        # review-then-commit sequence can stage exactly the reviewed list.
        # Only the explicit --close ends this session's ownership window,
        # deleting just its own ledger; foreign ledgers are left untouched
        # either way, so closing here never wipes another session's (or the
        # UI's) unclaimed rows. Running a review twice shows the same list.
        if getattr(args, "close", False):
            ledger.unlink(missing_ok=True)
            payload["session_closed"] = True
        else:
            payload["session_closed"] = False
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not touched:
        print("los: no files were touched through this learning session", file=sys.stderr)
        return 2
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != _row_proven_state(recorded[path])
    ]
    payload["ownership_conflicts"] = ownership_conflicts
    if ownership_conflicts:
        print(
            "los: refusing to stage files changed after their recorded LearningOS "
            "transaction: " + ", ".join(ownership_conflicts),
            file=sys.stderr,
        )
        return 2
    subprocess.run(["git", "add", "--", *touched], cwd=root, check=True, timeout=30)
    commit = subprocess.run(["git", "commit", "-m", args.commit_message], cwd=root,
                            capture_output=True, text=True, timeout=180)
    if commit.returncode != 0:
        print(commit.stdout, end="")
        print(commit.stderr, end="", file=sys.stderr)
        return commit.returncode
    payload["committed"] = True
    if args.push:
        pushed = subprocess.run(["git", "push"], cwd=root, capture_output=True,
                                text=True, timeout=180)
        if pushed.returncode != 0:
            print(pushed.stdout, end="")
            print(pushed.stderr, end="", file=sys.stderr)
            return pushed.returncode
        payload["pushed"] = True
    ledger.unlink(missing_ok=True)
    payload["session_closed"] = True
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0
