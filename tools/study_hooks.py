#!/usr/bin/env python3
"""Claude Code hooks for the LearningOS study profile (Plan C, ADR-021).

A study profile is a ``LearningOS/.claude/settings.json`` that runs these hooks.
They make the reading memory something an agent cannot miss:

- ``session-start``: prints the entry point and this session's overdue and
  adoptable reading entries, and records the session start.
- ``pre-tool-use``: the fence. Bash runs only an allowlist (the two ``los``
  forms, ``seal_envelope.py``, ``cat`` of the record its ``--check-out`` just
  wrote, stdin-only ``head -n N`` and ``jq -c '.path'``). Every ``los`` call is
  rewritten to the absolute gateway form, ``material-span --extract`` becomes
  the study read, and ``--session`` is injected from this hook's own input; an
  agent-supplied session refuses. Read, Grep, Glob and the edit tools are kept
  out of the trees that hold raw page text or the private store; edits go to
  temporary scratch only. Anything else refuses with the supported command.
- ``stop``: at turn end asks the agent to settle open entries, at most twice,
  then marks the rest overdue and records the end.
- ``profile --out DIR``: writes a disposable ``DIR/.claude/settings.json`` that
  wires these hooks to this checkout. It never overwrites an existing file;
  installing a profile in the live LearningOS folder is a separate operation.

Hook input arrives as JSON on stdin; decisions leave as JSON on stdout. Any
failure inside ``pre-tool-use`` denies the call (fail closed).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import string
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
CORE = TOOLS.parent
LEARNINGOS = CORE.parent
CORE_PYTHON = CORE / ".venv" / "bin" / "python"
LOS_SCRIPT = CORE / "tools" / "los.py"
SEAL_SCRIPT = CORE / "tools" / "seal_envelope.py"

from learning_os.store.materials.reading_cards import (  # noqa: E402
    MAX_OPEN_ENTRIES,
    ReadingStore,
    ReadingStoreError,
    adopt_command,
    entry_view,
    settle_command,
    valid_session,
)

#: Commands that receive the hook's session (C7).
SESSION_COMMANDS = frozenset({
    "material-study-span", "material-card-settle", "material-search", "material-context",
})

#: los commands that stage raw page text where file tools could read it (decision P5).
STAGING_COMMANDS = frozenset({"ai-action-prepare", "ai-action-append-slices"})

#: los and seal_envelope options whose value is a file the call writes.
OUTPUT_DESTS = frozenset({"out", "report_out", "check_out"})

#: Request values that are never local paths, or that the gateway resolves itself.
UNSCANNED_DESTS = frozenset({
    "command", "func", "_operation", "_operation_kind", "_parser_factory",
    "query", "reason", "lock_timeout", "card", "text", "title", "label",
})

#: Tools that never touch files and may run as they are.
PASS_TOOLS = frozenset({
    "TodoWrite", "TaskCreate", "TaskUpdate", "TaskList", "TaskGet", "TaskOutput",
    "TaskStop", "AskUserQuestion", "ExitPlanMode", "EnterPlanMode", "ToolSearch",
    "BashOutput", "KillShell", "KillBash", "Agent", "Task", "WebFetch", "WebSearch",
    "Skill", "SlashCommand",
})

READ_TOOLS = {"Read": "file_path", "NotebookRead": "notebook_path"}
EDIT_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path"}
SEARCH_TOOLS = frozenset({"Grep", "Glob", "LS"})

SUPPORTED = (
    "the study profile runs only: los ARGS (or .venv/bin/python tools/los.py ARGS) "
    "from any directory; .venv/bin/python tools/seal_envelope.py ARGS; cat REC right "
    "after a seal_envelope --check-out REC in the same command; and stdin-only "
    "head -n N or jq -c '.path' after a pipe. One line, no redirections other than "
    "2>&1, no variables or substitutions; quote JSON in single quotes. Read materials "
    "through los material-search and los material-span --material PATH --pages "
    "\"pdf p. N\" --extract.")

_SAFE_UNQUOTED = frozenset(string.ascii_letters + string.digits + "_./:,@%+-=")
_JQ_PATH = re.compile(r"^\.(?:[A-Za-z_][A-Za-z0-9_]*(?:\[[0-9]+\])?)(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[[0-9]+\])?)*$|^\.$")
_SESSION_PREFIX = re.compile(r"^--s(?:e(?:s(?:s(?:i(?:o(?:n)?)?)?)?)?)?(?:=.*)?$")
_ROOT_PREFIX = re.compile(r"^--ro(?:o(?:t)?)?(?:=.*)?$")
_WALK_BUDGET = 20000


class Refused(Exception):
    """One tool call the fence refuses; the message goes back to the agent."""


# --------------------------------------------------------------------- places

def protected_reads(core: Path = CORE) -> list[Path]:
    """Trees holding raw page text or the private store (C2, decision P5)."""
    learningos = core.parent
    return [learningos / "materials", learningos / "reading-memory",
            core / "generated" / "text-cache", core / "generated" / "material-search",
            core / "operations" / "ai-actions"]


def scratch_roots() -> list[Path]:
    """Where edits and output files may go: temporary scratch only."""
    roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
    return sorted(roots)


def _real(path: Path) -> Path:
    return Path(os.path.realpath(path))


def _inside(path: Path, roots: list[Path]) -> bool:
    real = _real(path)
    for root in roots:
        base = _real(root)
        if real == base or base in real.parents:
            return True
    return False


def _resolve(value: str, cwd: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else cwd / path


def _looks_like_path(value: str) -> bool:
    return "/" in value or value.startswith((".", "~")) or value.endswith(
        (".pdf", ".md", ".txt", ".json", ".yaml", ".sqlite3", ".jsonl"))


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, (list, tuple)):
        return [text for item in value for text in _strings(item)]
    return []


def _refuse_protected(values: list[str], cwd: Path, core: Path, what: str) -> None:
    protected = protected_reads(core)
    for value in values:
        if _looks_like_path(value) and _inside(_resolve(value, cwd), protected):
            raise Refused(
                f"{what} names {value!r}, which lies in a tree the study profile keeps "
                "closed (raw page text or the private reading store). Read pages through "
                "los material-span --material PATH --pages \"pdf p. N\" --extract.")


def _scan_json_file(value: str, cwd: Path, core: Path, what: str) -> None:
    path = _resolve(value, cwd)
    if _inside(path, protected_reads(core)):
        raise Refused(f"{what} {value!r} lies in a closed tree")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refused(f"{what} {value!r} must be a readable JSON file: {exc}") from exc
    _refuse_protected(_strings(data), cwd, core, what)


def writable(path: Path, core: Path = CORE) -> bool:
    """Temporary scratch, never the profile's own LearningOS folder or Claude settings.

    The LearningOS folder holds the gateway's code, the profile, the raw text and
    the store, so it stays closed to direct writes even when it lies under a
    temporary directory itself (a disposable trial world).
    """
    return (_inside(path, scratch_roots())
            and not _inside(path, [core.parent, Path.home() / ".claude"]))


def _require_scratch(value: str, cwd: Path, what: str) -> None:
    path = _resolve(value, cwd)
    if not writable(path):
        raise Refused(
            f"{what} {value!r} must be a scratch path under "
            f"{', '.join(str(root) for root in scratch_roots())}, outside the LearningOS folder")


# ---------------------------------------------------------------------- shell

def lex(command: str) -> list[tuple[str, str]]:
    """Words and the allowed operators of one command line, quote-aware.

    Only single quotes (literal), double quotes without ``$``, backquote,
    backslash or ``!``, the operators ``|`` and ``&&``, the redirection
    ``2>&1``, and unquoted characters that no shell expands are admitted.
    """
    if any(mark in command for mark in ("\n", "\r", "\x00")):
        raise Refused("one command per line: newlines are refused")
    tokens: list[tuple[str, str]] = []
    word: str | None = None
    index, size = 0, len(command)

    def flush() -> None:
        nonlocal word
        if word is not None:
            tokens.append(("word", word))
            word = None

    while index < size:
        char = command[index]
        if char in " \t":
            flush()
            index += 1
        elif char == "'":
            end = command.find("'", index + 1)
            if end < 0:
                raise Refused("unbalanced single quote")
            word = (word or "") + command[index + 1:end]
            index = end + 1
        elif char == '"':
            end = index + 1
            while end < size and command[end] != '"':
                if command[end] in "$`\\!":
                    raise Refused("inside double quotes, $ ` \\ and ! are refused; "
                                  "use single quotes for literal text")
                end += 1
            if end >= size:
                raise Refused("unbalanced double quote")
            word = (word or "") + command[index + 1:end]
            index = end + 1
        elif char == "|":
            if command.startswith("||", index):
                raise Refused("|| is refused")
            flush()
            tokens.append(("op", "|"))
            index += 1
        elif char == "&":
            if not command.startswith("&&", index):
                raise Refused("& (background or redirection) is refused")
            flush()
            tokens.append(("op", "&&"))
            index += 2
        elif (char == "2" and word is None and command.startswith("2>&1", index)
              and (index + 4 == size or command[index + 4] in " \t|&")):
            tokens.append(("op", "2>&1"))
            index += 4
        elif char in _SAFE_UNQUOTED:
            if char == "=" and word is None:
                raise Refused("a word may not start with = (shell expansion)")
            word = (word or "") + char
            index += 1
        else:
            raise Refused(f"the character {char!r} is refused outside quotes")
    flush()
    return tokens


def split_command(tokens: list[tuple[str, str]]) -> list[list[tuple[list[str], bool]]]:
    """``&&``-separated pipelines of ``|``-separated (words, merges-stderr) commands."""
    pipelines: list[list[tuple[list[str], bool]]] = [[]]
    words: list[str] = []
    merged = False
    for kind, text in [*tokens, ("op", "end")]:
        if kind == "word":
            if merged:
                raise Refused("2>&1 may only end a command")
            words.append(text)
            continue
        if text == "2>&1":
            if not words or merged:
                raise Refused("2>&1 may only end a command")
            merged = True
            continue
        if not words:
            raise Refused("empty command around an operator")
        pipelines[-1].append((words, merged))
        words, merged = [], False
        if text == "&&":
            pipelines.append([])
    return pipelines


def _parse(parser: argparse.ArgumentParser, args: list[str], label: str) -> argparse.Namespace | None:
    """The namespace argparse itself would build, or a refusal naming its error."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            return parser.parse_args(args)
    except SystemExit as exc:
        if exc.code in (0, None):
            return None  # --help: harmless, nothing to rewrite
        message = err.getvalue().strip().splitlines()
        raise Refused(f"{label} would refuse these arguments: "
                      f"{message[-1] if message else 'usage error'}") from exc


def _interpreter(word: str, cwd: Path) -> bool:
    return os.path.normpath(_resolve(word, cwd)) == os.path.normpath(CORE_PYTHON)


def _script(word: str, cwd: Path, script: Path) -> bool:
    return _real(_resolve(word, cwd)) == _real(script)


def _subcommand_index(args: list[str]) -> int | None:
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--lock-timeout":
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return None


def _los(args: list[str], cwd: Path, session: str) -> tuple[list[str], bool]:
    """The rewritten los argv (absolute form) and whether it carries the session."""
    from learning_os.adapters.cli_parser import build_parser

    for token in args:
        if _SESSION_PREFIX.match(token):
            raise Refused("--session is supplied by the study profile's hook; an agent "
                          "never types it (use --adopt SESSION to take over an ended "
                          "session's entries)")
        if _ROOT_PREFIX.match(token):
            raise Refused("--root is refused: the study profile reads this LearningOS folder only")
    ns = _parse(build_parser(), args, "los")
    if ns is None:
        return [str(CORE_PYTHON), str(LOS_SCRIPT), *args], False
    command = ns.command
    if getattr(ns, "root", None) is not None:
        raise Refused("--root is refused: the study profile reads this LearningOS folder only")
    if command in STAGING_COMMANDS:
        raise Refused(f"los {command} stages raw page text outside the gateway and is "
                      "refused in the study profile")
    if getattr(ns, "session", None) is not None:
        raise Refused("--session is supplied by the study profile's hook; an agent never types it")
    values: list[str] = []
    for dest, value in vars(ns).items():
        if dest in UNSCANNED_DESTS or (dest == "material" and command.startswith("material-")):
            continue
        if dest in OUTPUT_DESTS and isinstance(value, str):
            _require_scratch(value, cwd, f"--{dest.replace('_', '-')}")
        if dest == "payload_file" and isinstance(value, str) and value != "-":
            _scan_json_file(value, cwd, CORE, "--payload-file")
        values.extend(_strings(value))
    _refuse_protected(values, cwd, CORE, f"los {command}")
    rewritten = list(args)
    position = _subcommand_index(rewritten)
    target = command
    if command == "material-span" and getattr(ns, "extract", False):
        assert position is not None
        rewritten[position] = target = "material-study-span"
    injected = target in SESSION_COMMANDS
    if injected:
        rewritten += ["--session", session]
    return [str(CORE_PYTHON), str(LOS_SCRIPT), *rewritten], injected


def _seal(args: list[str], cwd: Path) -> tuple[list[str], str | None]:
    """The absolute seal_envelope argv and its --check-out target, if any."""
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    import seal_envelope
    for token in args:
        if _ROOT_PREFIX.match(token):
            raise Refused("--root is refused: the study profile writes this LearningOS folder only")
    ns = _parse(seal_envelope.build_parser(), args, "seal_envelope.py")
    check_out = None
    if ns is not None:
        if getattr(ns, "root", None) is not None:
            raise Refused("--root is refused in the study profile")
        payload = getattr(ns, "payload", None)
        if isinstance(payload, str):
            if payload.startswith("@"):
                _scan_json_file(payload[1:], cwd, CORE, "--payload @PATH")
            else:
                try:
                    _refuse_protected(_strings(json.loads(payload)), cwd, CORE, "--payload")
                except ValueError:
                    pass  # seal_envelope refuses malformed JSON itself
        if isinstance(getattr(ns, "guards_from", None), str):
            _scan_json_file(ns.guards_from, cwd, CORE, "--guards-from")
        for dest in ("check_out", "out"):
            value = getattr(ns, dest, None)
            if isinstance(value, str):
                _require_scratch(value, cwd, f"--{dest.replace('_', '-')}")
        if isinstance(getattr(ns, "check_out", None), str):
            check_out = str(_real(_resolve(ns.check_out, cwd)))
        _refuse_protected([text for dest, value in vars(ns).items()
                           if dest not in ("payload",) for text in _strings(value)],
                          cwd, CORE, "seal_envelope.py")
    return [str(CORE_PYTHON), str(SEAL_SCRIPT), *args], check_out


def rewrite_bash(command: str, cwd: Path, session: str) -> tuple[str, bool]:
    """The command to run instead, and whether it calls the gateway."""
    pipelines = split_command(lex(command))
    rendered: list[str] = []
    gateway = False
    checked_out: set[str] = set()
    for pipeline in pipelines:
        parts: list[str] = []
        for position, (words, merged) in enumerate(pipeline):
            head = words[0]
            if position == 0:
                if head == "los":
                    argv, _ = _los(words[1:], cwd, session)
                    gateway = True
                elif len(words) > 1 and _interpreter(head, cwd) and _script(words[1], cwd, LOS_SCRIPT):
                    argv, _ = _los(words[2:], cwd, session)
                    gateway = True
                elif len(words) > 1 and _interpreter(head, cwd) and _script(words[1], cwd, SEAL_SCRIPT):
                    argv, target = _seal(words[2:], cwd)
                    if target is not None:
                        checked_out.add(target)
                    gateway = True
                elif head == "cat" and len(words) == 2:
                    target = str(_real(_resolve(words[1], cwd)))
                    if target not in checked_out:
                        raise Refused("cat runs only on the record a seal_envelope --check-out "
                                      "wrote earlier in the same command (--check-out REC && cat REC)")
                    argv = ["/bin/cat", target]
                else:
                    raise Refused(f"{head!r} is not part of the study profile; {SUPPORTED}")
            elif head == "head" and len(words) == 3 and words[1] == "-n" and words[2].isdigit():
                argv = ["/usr/bin/head", "-n", words[2]]
            elif head == "jq" and len(words) == 3 and words[1] == "-c" and _JQ_PATH.match(words[2]):
                found = shutil.which("jq")
                if found is None:
                    raise Refused("jq is not installed here; use head -n N instead")
                argv = [found, "-c", words[2]]
            else:
                raise Refused(f"after a pipe only stdin-only head -n N or jq -c '.path' run; {SUPPORTED}")
            parts.append(shlex.join(argv) + (" 2>&1" if merged else ""))
        rendered.append(" | ".join(parts))
    return " && ".join(rendered), gateway


# ---------------------------------------------------------------- file tools

def _subtree_reaches(root: Path, protected: list[Path]) -> bool:
    """Whether a search below ``root`` could reach a closed tree (link, ancestor, size)."""
    real = _real(root)
    if any(real == _real(tree) or _real(tree).is_relative_to(real) for tree in protected):
        return True
    seen = 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in [*dirs, *files]:
            seen += 1
            if seen > _WALK_BUDGET:
                return True
            path = Path(parent) / name
            if path.is_symlink() and _inside(path, protected):
                return True
    return False


def check_file_tool(tool: str, tool_input: dict, cwd: Path) -> None:
    protected = protected_reads(CORE)
    if tool in READ_TOOLS:
        target = tool_input.get(READ_TOOLS[tool])
        if not isinstance(target, str) or _inside(_resolve(target, cwd), protected):
            raise Refused(
                f"{tool} of {target!r} is refused: that tree holds raw page text or the "
                "private reading store. Read pages through los material-span --material "
                "PATH --pages \"pdf p. N\" --extract.")
        return
    if tool in EDIT_TOOLS:
        target = tool_input.get(EDIT_TOOLS[tool])
        if (not isinstance(target, str) or _inside(_resolve(target, cwd), protected)
                or not writable(_resolve(target, cwd))):
            raise Refused(
                f"{tool} of {target!r} is refused: the study profile edits only temporary "
                f"scratch ({', '.join(str(root) for root in scratch_roots())}); learner "
                "records change through los and seal_envelope.py")
        return
    if tool in SEARCH_TOOLS:
        pattern = tool_input.get("pattern") if tool == "Glob" else None
        if isinstance(pattern, str) and (pattern.startswith("/") or ".." in Path(pattern).parts):
            raise Refused("Glob patterns may not be absolute or climb with ..; pass path instead")
        base = tool_input.get("path") or str(cwd)
        if not isinstance(base, str) or _inside(_resolve(base, cwd), protected) or \
                _subtree_reaches(_resolve(base, cwd), protected):
            raise Refused(
                f"{tool} below {base!r} could reach raw page text or the private reading "
                "store; search a narrower folder, and find material pages with "
                "los material-search \"QUERY\"")
        return
    raise Refused(f"the tool {tool!r} is not part of the study profile")


# --------------------------------------------------------------------- events

def _decision(decision: str, reason: str, updated: dict | None = None) -> dict:
    output: dict[str, Any] = {"hookEventName": "PreToolUse", "permissionDecision": decision,
                              "permissionDecisionReason": reason}
    if updated is not None:
        output["updatedInput"] = updated
    return {"hookSpecificOutput": output}


def pre_tool_use(event: dict) -> dict:
    """The fence for one tool call (step 4); refusals carry the supported form."""
    session = event.get("session_id")
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    cwd = Path(event.get("cwd") or os.getcwd())
    try:
        if not valid_session(session):
            raise Refused("the study profile needs Claude Code's session id in the hook input")
        if tool == "Bash":
            command = tool_input.get("command")
            if not isinstance(command, str) or not command.strip():
                raise Refused("empty command")
            rewritten, gateway = rewrite_bash(command, cwd, session)
            if gateway:
                with contextlib.suppress(ReadingStoreError):
                    ReadingStore(CORE).touch(session)
            return _decision("allow", "study profile: gateway form",
                             dict(tool_input, command=rewritten))
        if isinstance(tool, str) and tool.startswith("mcp__"):
            raise Refused(f"MCP tool {tool} is not part of the study profile")
        if tool in PASS_TOOLS:
            return _decision("allow", "study profile: tool without file access")
        if isinstance(tool, str):
            check_file_tool(tool, tool_input, cwd)
            return _decision("allow", "study profile: path outside the closed trees")
        raise Refused("no tool name in the hook input")
    except Refused as exc:
        return _decision("deny", str(exc))
    except Exception as exc:  # fail closed: a broken fence refuses
        return _decision("deny", f"the study profile's hook failed, so the call is refused: "
                                 f"{type(exc).__name__}: {exc}")


def session_start(event: dict) -> str:
    """The injected entry text: what to run first and what this session owes."""
    session = event.get("session_id")
    lines = [
        "LearningOS study profile (reading memory, ADR-021).",
        "- Start with: los bootstrap --brief. Find pages: los material-search \"QUERY\". "
        "Read pages: los material-span --material PATH --pages \"pdf p. N\" --extract "
        "(or los material-span UNIT ROUTE --extract).",
        f"- Reading pages that no card covers opens a reading entry. Hold at most "
        f"{MAX_OPEN_ENTRIES} open entries, and settle each before your turn ends: "
        "los material-card-settle ENTRY --card '{...}' or --dismiss irrelevant --reason '...'. "
        "Cards are private and unreviewed; reads show them beside the text.",
        f"- {SUPPORTED}",
    ]
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
        return "\n".join([*lines, f"- The reading store is unavailable ({exc}); study reads will refuse."])
    overdue = [row for row in mine if row["state"] == "overdue"]
    if overdue:
        lines.append(f"- This session holds {len(overdue)} overdue entries; settle them before "
                     "reading new pages: " + "; ".join(
                         f"{row['entry']} ({entry_view(row)['pages']} of {row['material']})"
                         for row in overdue))
    else:
        lines.append("- This session holds no overdue entries.")
    if adoptable:
        count = sum(len(rows) for rows in adoptable.values())
        lines.append(f"- {count} entries of ended or idle sessions are adoptable; adopt and "
                     "settle them before reading new pages: " + "; ".join(
                         adopt_command(name) for name in adoptable))
    else:
        lines.append("- No adoptable entries.")
    return "\n".join(lines)


def stop(event: dict) -> dict | None:
    """Turn end (C1.3): ask at most twice, then mark open entries overdue."""
    session = event.get("session_id")
    if not valid_session(session):
        return None
    store = ReadingStore(CORE)
    try:
        if not store.exists():
            return None
        decision = store.stop(session, continuing=bool(event.get("stop_hook_active")))
    except ReadingStoreError as exc:
        print(f"study profile: the reading store is unavailable at turn end: {exc}", file=sys.stderr)
        return None
    if decision.block:
        listing = "; ".join(f"{row['entry']} ({entry_view(row)['pages']} of {row['material']})"
                            for row in decision.entries)
        return {"decision": "block", "reason": (
            f"Settle your reading entries before ending the turn (ask {decision.asked} of 2): "
            f"{listing}. For each, save a card or dismiss it: "
            + "  ||  ".join(settle_command(row["entry"]) for row in decision.entries))}
    if decision.overdue:
        return {"systemMessage": "Reading entries left unsettled are now overdue: "
                + ", ".join(row["entry"] for row in decision.overdue)}
    return None


# -------------------------------------------------------------------- profile

def profile_settings(core: Path = CORE) -> dict:
    """The study profile's settings for one checkout: hooks plus deny rules."""
    python = shlex.quote(str(core / ".venv" / "bin" / "python"))
    hooks = shlex.quote(str(core / "tools" / "study_hooks.py"))
    deny = []
    for tree in protected_reads(core):
        rule = "/" + str(_real(tree)) + "/**"
        deny += [f"Read({rule})", f"Edit({rule})", f"Write({rule})"]
    return {
        "hooks": {
            "SessionStart": [{"hooks": [{"type": "command",
                                         "command": f"{python} {hooks} session-start",
                                         "timeout": 60}]}],
            "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command",
                                                       "command": f"{python} {hooks} pre-tool-use",
                                                       "timeout": 60}]}],
            "Stop": [{"hooks": [{"type": "command", "command": f"{python} {hooks} stop",
                                 "timeout": 60}]}],
        },
        "permissions": {"deny": deny},
    }


def write_profile(out: Path) -> Path:
    target = out / ".claude" / "settings.json"
    if target.exists():
        raise FileExistsError(f"{target} exists; a profile is never overwritten here")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(profile_settings(), indent=2) + "\n", encoding="utf-8")
    return target


# ------------------------------------------------------------------------ cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="study_hooks.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="event", required=True)
    sub.add_parser("session-start", help="SessionStart hook: hook JSON on stdin")
    sub.add_parser("pre-tool-use", help="PreToolUse hook: hook JSON on stdin")
    sub.add_parser("stop", help="Stop hook: hook JSON on stdin")
    profile = sub.add_parser("profile", help="write a disposable study profile into DIR/.claude")
    profile.add_argument("--out", required=True, type=Path,
                         help="the LearningOS-shaped folder that receives .claude/settings.json")
    return parser


def _read_event() -> dict:
    try:
        value = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.event == "profile":
        print(write_profile(args.out))
        return 0
    event = _read_event()
    if args.event == "pre-tool-use":
        print(json.dumps(pre_tool_use(event)))
        return 0
    if args.event == "session-start":
        print(session_start(event))
        return 0
    result = stop(event)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
