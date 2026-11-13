#!/usr/bin/env python3
"""Optional UX hooks for the LearningOS study profile (Plan C/D, ADR-021).

Hard isolation (non-regex Seatbelt read/write denials, default-deny broker
allowlist, ``material-span --extract`` rewrite, authoritative ``--session``,
and host-side ``session_end`` on exit) lives in ``tools/study_launch.py`` and
``learning_os.adapters.study_broker``.  This script supplies optional lifecycle
UX nudges and a disposable ``--settings`` generator:

- ``session-start``: prints the study entry hint and this session's overdue and
  adoptable reading entries, and records the session start.
- ``stop``: at turn end reminds the agent up to twice (``STOP_ASKS = 2``) to
  settle open entries before marking the rest overdue.
- ``session-end``: records the session end when running unsandboxed outside
  ``tools/study_launch.py`` (inside a sandboxed launch, the host launcher owns
  ``session-end`` on exit).
- ``profile --out DIR``: writes a disposable ``DIR/.claude/settings.json``
  wiring those UX hooks without overwriting an existing file.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import cast

TOOLS = Path(__file__).resolve().parent
CORE = TOOLS.parent

from learning_os.adapters.study_broker import (  # noqa: E402
    GATE_SOCK_ENV,
    send_broker_request,
)
from learning_os.store.materials.reading_cards import (  # noqa: E402
    MAX_OPEN_ENTRIES,
    ReadingStore,
    ReadingStoreError,
    entry_view,
    join_adopt_commands,
    join_settle_commands,
    treatment_kinds_hint,
    valid_session,
)
from learning_os.store.study_fence import STUDY_FENCE_CORE_ENV  # noqa: E402


def _forward_broker_hook(
    gate_sock: str,
    *,
    event_name: str,
    stop_hook_active: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "tool": "study_hook",
        "event": event_name,
        "stop_hook_active": stop_hook_active,
    }
    return send_broker_request(gate_sock, payload)


def session_start(event: dict[str, object]) -> str:
    """The injected entry text: what to run first and what this session owes."""
    gate_sock = os.environ.get(GATE_SOCK_ENV)
    if gate_sock:
        try:
            response = _forward_broker_hook(gate_sock, event_name="session-start")
        except (OSError, ValueError, RuntimeError) as exc:
            return (
                "LearningOS study profile (reading memory, ADR-021).\n"
                f"- Study broker hook unavailable ({exc}); use .venv/bin/python tools/los.py bootstrap --brief."
            )
        stdout = response.get("stdout")
        if isinstance(stdout, str) and stdout.strip():
            return stdout.rstrip("\n")
        stderr = response.get("stderr")
        detail = stderr.strip() if isinstance(stderr, str) else "unknown error"
        return (
            "LearningOS study profile (reading memory, ADR-021).\n"
            f"- Study broker session-start error ({detail})."
        )

    session = event.get("session_id")
    sandboxed = bool(os.environ.get(STUDY_FENCE_CORE_ENV))
    lines = [
        "LearningOS study profile (reading memory, ADR-021 / ADR-022).",
    ]
    if not sandboxed:
        lines.append(
            "- Note: no study sandbox active (LOS_GATE_SOCK unset): file reads are unfenced "
            "and material-span --extract does not rewrite automatically."
        )
    lines.extend([
        "- Start with:\n"
        "  .venv/bin/python tools/los.py bootstrap --brief\n"
        "- Search first to check existing reading cards before opening PDFs:\n"
        "  .venv/bin/python tools/los.py material-search \"QUERY\"\n"
        "  .venv/bin/python tools/los.py material-context \"QUERY\"",
        "- Read narrow pages first (`span_reference` / targeted `pdf p. N`, avoiding wide "
        "bundles over unsectioned PDFs):\n"
        "  .venv/bin/python tools/los.py material-span --material PATH --pages \"pdf p. N\" --extract\n"
        "  .venv/bin/python tools/los.py material-span UNIT ROUTE --extract\n"
        "  Add --omit-covered-text when checking an already-covered span; dismiss isolated "
        "irrelevant pages with --dismiss irrelevant.",
        f"- Reading pages that no card covers opens a reading entry. Hold at most "
        f"{MAX_OPEN_ENTRIES} open entries, and settle each before your turn ends:\n"
        "  .venv/bin/python tools/los.py material-card-settle ENTRY --card '{...}'\n"
        "  .venv/bin/python tools/los.py material-card-settle ENTRY --dismiss irrelevant --reason '...'\n"
        f"  {treatment_kinds_hint()} Cards are private and unreviewed; "
        "reads show them beside the text unless --omit-covered-text is passed.",
        "- Write scratch / --check-out / --out files under $LOS_SCRATCH_DIR "
        "(seal_envelope.py --submit validates on the host; run validate.py with --no-report "
        "inside study mode and commit outside study mode).",
    ])
    if not valid_session(session):
        return "\n".join([*lines, "- No session id arrived: study reads will refuse."])
    store = ReadingStore(CORE)
    try:
        store.touch(session, start=True)
        from learning_os.store import observations

        now = observations.now()
        mine = store.entries(session=session)
        adoptable = store.adoptable(session, now)
    except ReadingStoreError as exc:
        return "\n".join(
            [*lines, f"- The reading store is unavailable ({exc}); study reads will refuse."]
        )
    overdue = [row for row in mine if row["state"] == "overdue"]
    if overdue:
        lines.append(
            f"- This session holds {len(overdue)} overdue entries; settle them before "
            "reading new pages: "
            + "; ".join(
                f"{row['entry']} ({entry_view(row)['pages']} of {row['material']})"
                for row in overdue
            )
        )
    else:
        lines.append("- This session holds no overdue entries.")
    if adoptable:
        count = sum(len(rows) for rows in adoptable.values())
        lines.append(
            f"- {count} entries of ended or idle sessions are adoptable; adopt and "
            "settle them before reading new pages:\n"
            + join_adopt_commands(adoptable)
        )
    else:
        lines.append("- No adoptable entries.")
    return "\n".join(lines)


def stop(event: dict[str, object]) -> dict[str, object] | None:
    """Turn end (C1.3): ask at most twice, then mark open entries overdue."""
    continuing = bool(event.get("stop_hook_active"))
    gate_sock = os.environ.get(GATE_SOCK_ENV)
    if gate_sock:
        try:
            response = _forward_broker_hook(
                gate_sock,
                event_name="stop",
                stop_hook_active=continuing,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"study profile: broker unavailable at turn end: {exc}", file=sys.stderr)
            return None
        stderr = response.get("stderr")
        if isinstance(stderr, str) and stderr:
            print(stderr, file=sys.stderr, end="")
        stdout = response.get("stdout")
        if not isinstance(stdout, str) or not stdout.strip():
            return None
        try:
            parsed = json.loads(stdout)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None

    session = event.get("session_id")
    if not valid_session(session):
        return None
    store = ReadingStore(CORE)
    try:
        if not store.exists():
            return None
        decision = store.stop(session, continuing=continuing)
    except ReadingStoreError as exc:
        print(f"study profile: the reading store is unavailable at turn end: {exc}", file=sys.stderr)
        return None
    if decision.block:
        listing = "; ".join(
            f"{row['entry']} ({entry_view(row)['pages']} of {row['material']})"
            for row in decision.entries
        )
        return {
            "decision": "block",
            "reason": (
                f"Settle your reading entries before ending the turn (ask {decision.asked} of 2): "
                f"{listing}. {treatment_kinds_hint()} Save a card or dismiss each entry by "
                "running one command at a time:\n"
                + join_settle_commands(
                    cast(str, row["entry"]) for row in decision.entries
                )
            ),
        }
    if decision.overdue:
        return {
            "systemMessage": "Reading entries left unsettled are now overdue: "
            + ", ".join(cast(str, row["entry"]) for row in decision.overdue)
        }
    return None


def session_end(event: dict[str, object]) -> str:
    """Session termination (C7): record the end when running outside study_launch."""
    if os.environ.get(GATE_SOCK_ENV):
        # Under study_launch.py the host launcher records session_end in finally:.
        return ""
    session = event.get("session_id")
    if not valid_session(session):
        return ""
    store = ReadingStore(CORE)
    try:
        if not store.exists():
            return ""
        store.session_end(session)
    except ReadingStoreError as exc:
        print(f"study profile: the reading store is unavailable at session end: {exc}",
              file=sys.stderr)
        return ""
    return (
        "Reading memory: session end recorded; this session's unsettled "
        "entries are adoptable."
    )


def profile_settings(core: Path = CORE) -> dict[str, object]:
    """Opt-in Claude Code UX hooks for one checkout (enforcement lives in study_launch.py)."""
    python = shlex.quote(str(core / ".venv" / "bin" / "python"))
    hooks = shlex.quote(str(core / "tools" / "study_hooks.py"))
    return {
        "hooks": {
            "SessionStart": [{
                "hooks": [{
                    "type": "command",
                    "command": f"{python} {hooks} session-start",
                    "timeout": 60,
                }],
            }],
            "Stop": [{
                "hooks": [{
                    "type": "command",
                    "command": f"{python} {hooks} stop",
                    "timeout": 60,
                }],
            }],
            "SubagentStop": [{
                "hooks": [{
                    "type": "command",
                    "command": f"{python} {hooks} stop",
                    "timeout": 60,
                }],
            }],
            "SessionEnd": [{
                "hooks": [{
                    "type": "command",
                    "command": f"{python} {hooks} session-end",
                    "timeout": 60,
                }],
            }],
        },
    }


def write_profile(out: Path) -> Path:
    """Write a disposable ``DIR/.claude/settings.json`` without overwriting an existing one."""
    target = out / ".claude" / "settings.json"
    if target.exists():
        raise FileExistsError(f"{target} exists; a profile is never overwritten here")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(profile_settings(), indent=2) + "\n", encoding="utf-8")
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for study UX hooks and profile generation."""
    parser = argparse.ArgumentParser(
        prog="study_hooks.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="event", required=True)
    sub.add_parser("session-start", help="SessionStart hook: hook JSON on stdin")
    sub.add_parser("stop", help="Stop hook: hook JSON on stdin")
    sub.add_parser("session-end", help="SessionEnd hook: hook JSON on stdin")
    profile = sub.add_parser("profile", help="write a disposable study profile into DIR/.claude")
    profile.add_argument(
        "--out",
        required=True,
        type=Path,
        help="the LearningOS-shaped folder that receives .claude/settings.json",
    )
    return parser


def _read_event() -> dict[str, object]:
    try:
        value = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def main(argv: list[str] | None = None) -> int:
    """Run one study UX hook event or generate an opt-in settings profile."""
    args = build_parser().parse_args(argv)
    if args.event == "profile":
        print(write_profile(args.out))
        return 0
    event = _read_event()
    if args.event == "session-start":
        print(session_start(event))
        return 0
    if args.event == "session-end":
        message = session_end(event)
        if message:
            print(message)
        return 0
    result = stop(event)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
