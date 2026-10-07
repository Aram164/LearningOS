"""A8 doc command lint (SPEC §7.4, PLAN D11/A8).

Every ``los …`` mention in a binding doc parses with the CLI parser, and
every ``tools/X.py …`` mention parses with that tool's ``build_parser()``.
Mentions live inside backticks (inline spans, which may wrap across lines)
or inside fenced blocks (whose backslash continuations join). ALL-CAPS
tokens are placeholders and are replaced by a dummy value of the type the
parser declares for that option before parsing. Failures are counted under
``A8-doc-commands`` with signature ``doc::line``.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import importlib
import io
import re
import shlex
from collections import Counter
from pathlib import Path

import yaml

from learning_os.contracts import normative_corpus as corpus

ROOT = Path(__file__).resolve().parents[1]
RATCHETS_PATH = ROOT / "tests" / "architecture" / "ratchets.yaml"

CHECK_ID = "A8-doc-commands"
FIX = "Update the transcript, or fix the doc command (PLAN D11)."

LOS_RE = re.compile(r"(?<![A-Za-z0-9_])los ([a-z-]+)")
TOOL_RE = re.compile(r"(?<![A-Za-z0-9_.])tools/([a-z_]+)\.py")
ALL_CAPS_RE = re.compile(r"[A-Z0-9_]*[A-Z][A-Z0-9_]*\Z")

#: Shell structure ends the argv: the cut runs before tokenizing, outside
#: quotes and outside `<…>` placeholders (which may hold `|` or `>`).
_CUT_CHARS = frozenset("|&;<>")
_FENCE_RE = re.compile(r"^(```|~~~)")


def _binding_docs() -> list[str]:
    """Corpus paths with ``authority: binding``, sorted (SPEC §7.4)."""
    loaded = corpus.load(ROOT)
    return sorted(doc.path for doc in loaded.documents
                  if doc.authority == "binding")


def _logical_lines(lines: list[str]) -> list[tuple[int, str, bool]]:
    """Join fence continuations; (first lineno, text, in_fence).

    Fence boundary lines are markup, not content, and are skipped. A fence
    line ending in a backslash joins with the next line, shell-style.
    """
    out: list[tuple[int, str, bool]] = []
    in_fence = False
    pending: list[str] | None = None
    pending_first = 0
    for number, line in enumerate(lines, 1):
        if _FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((number, line, False))
            continue
        if pending is None:
            pending, pending_first = [line], number
        else:
            pending.append(line)
        if line.rstrip("\n").rstrip().endswith("\\"):
            pending[-1] = pending[-1].rstrip("\n")
            pending[-1] = pending[-1][:pending[-1].rfind("\\")]
        else:
            out.append((pending_first, "\n".join(pending), True))
            pending = None
    if pending is not None:
        out.append((pending_first, "\n".join(pending), True))
    return out


def _prose_spans(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Backtick spans across prose lines; multi-line spans join with newline.

    Splits on backtick runs: a run opens a span, and the next run of the
    same length closes it. Returns (opening lineno, span text).
    """
    spans: list[tuple[int, str]] = []
    open_len = 0
    open_line = 0
    current: list[str] = []

    def flush(complete: bool) -> None:
        nonlocal open_len, open_line, current
        if open_len and complete:
            spans.append((open_line, "\n".join(current)))
        open_len, open_line, current = 0, 0, []

    for number, line in lines:
        parts = re.split(r"(`+)", line)
        if open_len:
            current.append("")
        for index, part in enumerate(parts):
            if index % 2 == 0:
                if open_len:
                    current[-1] += part
                continue
            if open_len:
                if len(part) == open_len:
                    closed = "\n".join(current)
                    spans.append((open_line, closed))
                    open_len, open_line, current = 0, 0, []
                else:
                    current[-1] += part
            else:
                open_len, open_line, current = len(part), number, [""]
        if open_len:
            pass  # the span wraps; the newline joins at close
    flush(False)
    return spans


def _cut_shell(text: str) -> str:
    """Cut the command text where shell structure begins.

    Outside quotes and ``<…>`` placeholders, the first ``| & ; < >``
    character ends the argv (pipes, redirects, ``&&``). A backslash escapes
    the next character.
    """
    single = double = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "'" and not double:
            single = not single
        elif char == '"' and not single:
            double = not double
        elif not single and not double:
            if char == "<" and index + 1 < len(text) and text[index + 1] not in " \t\n\"'":
                end = index + 1
                while end < len(text) and text[end] not in " \t\n>":
                    end += 1
                index = end + 1 if end < len(text) and text[end] == ">" else end
                continue
            if char in _CUT_CHARS:
                return text[:index]
        index += 1
    return text


def _parsers() -> tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]]:
    """The CLI parser plus every tool's parser, imported once."""
    import los

    cli = los.build_parser()
    tools: dict[str, argparse.ArgumentParser] = {"los": cli}
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.stem in tools:
            continue
        module = importlib.import_module(path.stem)
        tools[path.stem] = module.build_parser()
    return cli, tools


def _sub_parser(parser: argparse.ArgumentParser, argv: list[str],
                ) -> argparse.ArgumentParser | None:
    """The selected subparser, if argv names a known subcommand."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for token in argv:
                if token in action.choices:
                    return action.choices[token]
    return None


def _option_types(*parsers: argparse.ArgumentParser | None,
                  ) -> dict[str, argparse.Action]:
    """Option string to action over the given parsers (later wins)."""
    options: dict[str, argparse.Action] = {}
    for parser in parsers:
        if parser is None:
            continue
        for action in parser._actions:
            for option in getattr(action, "option_strings", ()):
                options[option] = action
    return options


def _dummy(action: argparse.Action | None) -> str:
    """A dummy value of the type the option declares (SPEC §7.4)."""
    if action is not None:
        choices = getattr(action, "choices", None)
        if choices:
            return str(list(choices)[0])
        if getattr(action, "type", None) is int:
            return "1"
        if getattr(action, "type", None) is float:
            return "1.5"
    return "X"


def _check_candidate(parser: argparse.ArgumentParser, argv: list[str]) -> str | None:
    """Parse argv; None when it parses, else the failure reason."""
    sub = _sub_parser(parser, argv)
    options = _option_types(parser, sub)
    filled = [token if not ALL_CAPS_RE.fullmatch(token)
              else _dummy(options.get(argv[index - 1]) if index else None)
              for index, token in enumerate(argv)]
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            parser.parse_args(filled)
        except SystemExit as exc:
            if exc.code == 0:
                return None
            return f"exit {exc.code}"
    return None


def _candidates(doc: str) -> list[tuple[int, str, str, str]]:
    """Every doc-command candidate: (line, kind, name, text from the match)."""
    lines = (ROOT / doc).read_text(encoding="utf-8").splitlines()
    logical = _logical_lines(lines)
    code = [(first, text) for first, text, in_fence in logical if in_fence]
    prose = [(first, text) for first, text, in_fence in logical if not in_fence]
    code.extend(_prose_spans(prose))
    found: list[tuple[int, str, str, str]] = []
    for first, span in code:
        for match in LOS_RE.finditer(span):
            found.append((first, "los", match.group(1), span[match.start():]))
        for match in TOOL_RE.finditer(span):
            found.append((first, "tool", match.group(1), span[match.start():]))
    return found


def _scan(products: tuple[argparse.ArgumentParser, dict[str, argparse.ArgumentParser]],
          ) -> tuple[Counter, dict[str, str]]:
    """Parse every candidate; (failures per doc::line, first reason seen)."""
    _, tools = products
    failures: Counter = Counter()
    reasons: dict[str, str] = {}
    for doc in _binding_docs():
        for lineno, kind, name, text in _candidates(doc):
            signature = f"{doc}::{lineno}"
            if kind == "tool" and name not in tools:
                failures[signature] += 1
                reasons.setdefault(signature, f"unknown tool tools/{name}.py")
                continue
            parser = tools["los"] if kind == "los" else tools[name]
            try:
                tokens = shlex.split(_cut_shell(text))
            except ValueError:
                failures[signature] += 1
                reasons.setdefault(signature, "not shell-tokenizable")
                continue
            if kind == "los" and (not tokens or tokens[0] != "los"):
                failures[signature] += 1
                reasons.setdefault(signature, "not a los invocation")
                continue
            if kind == "tool" and (not tokens
                                   or tokens[0] != f"tools/{name}.py"):
                failures[signature] += 1
                reasons.setdefault(signature, f"not a tools/{name}.py invocation")
                continue
            reason = _check_candidate(parser, tokens[1:])
            if reason is not None:
                failures[signature] += 1
                reasons.setdefault(signature, reason)
    return failures, reasons


def test_every_tool_exposes_build_parser():
    """Each tools/*.py CLI parser is reachable as build_parser() (S09 Task 2.2)."""
    missing = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        builds = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "ArgumentParser"
            for node in ast.walk(tree))
        defines = any(
            isinstance(node, ast.FunctionDef) and node.name == "build_parser"
            for node in tree.body)
        if builds and not defines:
            missing.append(f"A8 {path.relative_to(ROOT)}: parser built inline — "
                           f"expose build_parser() — {FIX}")
    assert not missing, "\n".join(missing)


def test_doc_commands_parse():
    _, tools = _parsers()
    current, reasons = _scan((tools["los"], tools))
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            failures.append(
                f"A8 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} ({reasons[signature]}) — "
                f"{signature.replace('::', ':')} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A8 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)
