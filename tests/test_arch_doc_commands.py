"""A8 doc commands: executable argv, declared references and explicit argv macros.

SPEC §7.4 / PLAN D11/A8. The S32 technical clarification is recorded in the
completion control/A8-INDEPENDENT-DESIGN.md: references are never reported as
runnable examples. Every match is classified and logged. Parser errors never
change the classification. Shell examples always parse their full argv.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import importlib
import io
import json
import os
import re
import shlex
from collections import Counter
from pathlib import Path

import yaml

from learning_os.store.contracts import normative_corpus as corpus

ROOT = Path(__file__).resolve().parents[1]
RATCHETS_PATH = ROOT / "tests" / "architecture" / "ratchets.yaml"
CHECK_ID = "A8-doc-commands"
FIX = "Update the transcript, or fix the doc command (PLAN D11)."
MENTION_RE = re.compile(r"(?<![A-Za-z0-9_.])(?:tools/(?P<tool>[a-z_]+)\.py|(?P<los>los)(?=\s|$))")
ALL_CAPS_RE = re.compile(r"[A-Z0-9_]*[A-Z][A-Z0-9_]*\Z")
SHELL_VAR_RE = re.compile(r"\$(?:[A-Z][A-Z0-9_]*|\{[A-Z][A-Z0-9_]*\})\Z")
ANGLE_RE = re.compile(r"<([^<>]+)>")
ANNOTATION_RE = re.compile(r"^\s*<!-- los:(reference|macro) (\{.*\}) -->\s*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
SHELL_KINDS = {"", "sh", "bash", "shell", "console"}

def _binding_docs() -> list[str]:
    """Corpus paths with ``authority: binding``, sorted (SPEC §7.4)."""
    loaded = corpus.load(ROOT)
    return sorted(doc.path for doc in loaded.documents
                  if doc.authority == "binding")


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



def _sub_parser(parser, argv):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction) and argv:
            return action.choices.get(argv[0])
    return None


def _actions(parser, argv):
    sub = _sub_parser(parser, argv)
    return [*parser._actions, *(sub._actions if sub else [])]


def _dummy(action):
    choices = getattr(action, "choices", None)
    if choices:
        return str(next(iter(choices)))
    converter = getattr(action, "type", None)
    samples = ["X", "1", "1.5", "sha256:" + "0" * 64, "{}", "[]"]
    if converter is None:
        return "X"
    for sample in samples:
        try:
            converter(sample)
        except (ValueError, TypeError, argparse.ArgumentTypeError):
            continue
        return sample
    raise ValueError(f"cannot produce placeholder for {action.dest}")


def _placeholder(token, action):
    if token.startswith("sha256:") and ALL_CAPS_RE.fullmatch(token[7:]):
        return "sha256:" + "0" * 64
    if ALL_CAPS_RE.fullmatch(token):
        return _dummy(action)
    # A whole-token shell expansion ("$COLLECTION_SHA" in an executable
    # transcript) is a value only the run knows, exactly like an ALL_CAPS
    # placeholder: the flag and its position are still checked, only the
    # value is filled. A token that merely contains an expansion is not.
    if SHELL_VAR_RE.fullmatch(token):
        return _dummy(action)
    match = ANGLE_RE.fullmatch(token)
    if match:
        label = match.group(1)
        if label == "expansion":
            raise ValueError("<expansion> requires an explicit argv-macro declaration")
        if "|" in label:
            values = label.split("|")
            choices = getattr(action, "choices", None)
            if not choices or any(value not in choices for value in values):
                raise ValueError("placeholder alternatives disagree with parser choices")
            return values[0]
        return _dummy(action)
    if "<" in token or ">" in token:
        replaced = ANGLE_RE.sub(lambda match: _dummy(action), token)
        if "<" in replaced or ">" in replaced:
            raise ValueError("malformed placeholder")
        return replaced
    return token


def _normalize(parser, argv):
    actions = _actions(parser, argv)
    options = {opt: action for action in actions for opt in action.option_strings}
    positional = [action for action in actions if not action.option_strings
                  and not isinstance(action, argparse._SubParsersAction)]
    sub = _sub_parser(parser, argv)
    filled = []
    index = 0
    position = 0
    while index < len(argv):
        token = argv[index]
        if index == 0 and sub is not None:
            filled.append(token)
            index += 1
            continue
        key, equals, value = token.partition("=")
        action = options.get(key)
        if action is not None:
            filled.append(key + "=" + _placeholder(value, action) if equals else token)
            index += 1
            if equals or action.nargs == 0:
                continue
            count = action.nargs if isinstance(action.nargs, int) else 1
            if action.nargs in ("*", "+"):
                count = 0
                while index + count < len(argv) and not argv[index + count].startswith("--"):
                    count += 1
            for _ in range(count):
                if index >= len(argv) or argv[index].startswith("--"):
                    break  # argparse diagnoses missing option values.
                filled.append(_placeholder(argv[index], action))
                index += 1
            continue
        action = positional[min(position, len(positional) - 1)] if positional else None
        filled.append(_placeholder(token, action))
        position += 1
        index += 1
    return filled


def _parse(parser, argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            parser.parse_args(argv)
        except (ValueError, TypeError, argparse.ArgumentTypeError) as exc:
            return str(exc)
        except SystemExit as exc:
            if exc.code != 0:
                return buffer.getvalue().strip().splitlines()[-1] or f"exit {exc.code}"
    return None


def _reference_completion(parser, argv, kind):
    if kind not in {"command", "option"}:
        raise ValueError("reference kind must be command or option")
    sub = _sub_parser(parser, argv)
    if any(isinstance(a, argparse._SubParsersAction) for a in parser._actions) and sub is None:
        raise ValueError("unknown command in reference")
    actions = _actions(parser, argv)
    options = {opt: action for action in actions for opt in action.option_strings}
    used = set()
    completed = [argv[0]] if sub else []
    index = 1 if sub else 0
    while index < len(argv):
        token = argv[index]
        key, equals, value = token.partition("=")
        action = options.get(key)
        if action is None:
            raise ValueError(f"reference contains unknown option or positional operand: {token}")
        if action.dest == "help":
            raise ValueError("--help is not reference completion")
        used.add(id(action))
        completed.append(token)
        index += 1
        if equals or action.nargs == 0:
            continue
        count = action.nargs if isinstance(action.nargs, int) else 1
        for _ in range(count):
            if index < len(argv) and not argv[index].startswith("--"):
                completed.append(argv[index])
                index += 1
            elif kind == "option":
                completed.append(_dummy(action))
            else:
                raise ValueError(f"missing supplied option value: {key}")
    for action in actions:
        if isinstance(action, argparse._SubParsersAction) or action.dest == "help":
            continue
        if id(action) in used:
            continue
        if action.required and action.option_strings:
            completed.append(action.option_strings[0])
            if action.nargs != 0:
                completed.extend([_dummy(action)] * (action.nargs if isinstance(action.nargs, int) else 1))
            used.add(id(action))
        elif action.required and not action.option_strings:
            completed.extend([_dummy(action)] * (action.nargs if isinstance(action.nargs, int) else 1))
    for selected in [parser, sub]:
        if selected is None:
            continue
        for group in selected._mutually_exclusive_groups:
            if group.required and not any(id(a) in used for a in group._group_actions):
                action = group._group_actions[0]
                completed.append(action.option_strings[0])
                if action.nargs != 0:
                    completed.append(_dummy(action))
                used.add(id(action))
    return completed


def _check_candidate(parser, argv):
    try:
        return _parse(parser, _normalize(parser, argv))
    except ValueError as exc:
        return str(exc)


def _substitution_end(text, start):
    quote = None
    depth = 1
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if char in "'\"":
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif text.startswith("$(", index) and quote != "'":
            index = _substitution_end(text, index + 2) + 1
            continue
        elif quote is None:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return index
        index += 1
    raise ValueError("unclosed shell substitution")


def _shell_parts(text):
    """Yield (offset, argv source); recurse real substitutions, preserve data."""
    quote = None
    index = start = 0
    masked = list(text)
    nested = []
    while index < len(text):
        char = text[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if char in "'\"":
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif text.startswith("$(", index) and quote != "'":
            end = _substitution_end(text, index + 2)
            nested.append((index + 2, text[index + 2:end]))
            masked[index:end + 1] = "X" + " " * (end - index)
            index = end + 1
            continue
        elif quote is None and char == "`":
            raise ValueError("unsupported backtick shell execution")
        elif quote is None and char == "<":
            match = ANGLE_RE.match(text, index)
            if match:
                index = match.end()
                continue
        index += 1
    if quote is not None:
        raise ValueError("not shell-tokenizable")
    for offset, inner in nested:
        for inner_offset, part in _shell_parts(inner):
            yield offset + inner_offset, part
    skeleton = "".join(masked)
    quote = None
    index = start = 0
    while index < len(skeleton):
        char = skeleton[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if char in "'\"":
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif quote is None:
            if char == "<":
                match = ANGLE_RE.match(skeleton, index)
                if match:
                    index = match.end()
                    continue
            if skeleton.startswith(" → ", index):
                yield start, skeleton[start:index]
                return
            if char in "|&;<>\n":
                yield start, skeleton[start:index]
                # A redirect target is data; the next command follows a separator.
                op = char
                while index < len(skeleton) and skeleton[index] in "|&;<>\n":
                    index += 1
                if op in "<>":
                    match = re.match(r"\s*(?:'[^']*'|\"[^\"]*\"|[^\s;&|]+)", skeleton[index:])
                    if match:
                        index += match.end()
                start = index
                continue
        index += 1
    yield start, skeleton[start:]


def _without_assignments(tokens):
    index = 0
    while index < len(tokens) and re.match(r"[A-Za-z_][A-Za-z0-9_]*=", tokens[index]):
        index += 1
    return tokens[index:]


def _target(tokens):
    tokens = _without_assignments(tokens)
    index = 0
    if index < len(tokens) and tokens[index] in {"env", "command"}:
        index += 1
        while index < len(tokens) and re.match(r"[A-Za-z_][A-Za-z0-9_]*=", tokens[index]):
            index += 1
    if index >= len(tokens):
        return None
    if re.search(r"(?:^|/)python(?:3(?:\.\d+)?)?$", tokens[index]):
        index += 1
    if index >= len(tokens):
        return None
    executable = tokens[index]
    if executable in {"los", ".venv/bin/los"}:
        return "los", "los", tokens[index + 1:]
    match = re.fullmatch(r"(?:\./)?tools/([a-z_]+)\.py", executable)
    if match:
        return "tool", match.group(1), tokens[index + 1:]
    return None


def _mentions(text, first, category):
    return [dict(line=first + text[:m.start()].count("\n"), offset=m.start(),
                 kind="tool" if m.group("tool") else "los", name=m.group("tool") or "los",
                 text=m.group(0), category=category, original_argv=None,
                 synthesized_argv=None, reason=None) for m in MENTION_RE.finditer(text)]


def _shell_rows(text, first):
    rows = _mentions(text, first, "shell-data")
    if not rows:
        return rows
    by_offset = {row["offset"]: row for row in rows}
    try:
        parts = list(_shell_parts(text))
        for offset, source in parts:
            tokens = shlex.split(source, comments=True)
            target = _target(tokens)
            if target is None:
                head = _without_assignments(tokens)
                if head and (head[0].startswith("(") or head[0] in {"{", "if", "then", "do", "while", "for", "case", "!", "sudo", "time", "nohup", "eval", "exec", "env", "command"}) and MENTION_RE.search(source):
                    raise ValueError("unsupported target-bearing shell construct")
                # Static shell scripts are executable arguments, unlike Python -c data.
                if len(head) >= 3 and head[0] in {"sh", "bash"} and head[1] == "-c":
                    nested = _shell_rows(head[2], first + text[:offset].count("\n"))
                    rows.extend(row for row in nested
                                if row["category"] in {"invocation", "extraction-error"})
                continue
            kind, name, argv = target
            match = next((m for m in MENTION_RE.finditer(source)
                          if (m.group("tool") or "los") == name), None)
            absolute = offset + (match.start() if match else len(source) - len(source.lstrip()))
            row = by_offset.get(absolute)
            if row is None:
                row = dict(line=first + text[:absolute].count("\n"), offset=absolute)
                rows.append(row)
            raw_source = text[offset:offset + len(source)]
            raw_target = _target(shlex.split(raw_source, comments=True))
            original_argv = raw_target[2] if raw_target else argv
            row.update(kind=kind, name=name, text=raw_source.strip(), category="invocation",
                       original_argv=original_argv, parser_argv=argv,
                       synthesized_argv=None, reason=None)
    except ValueError as exc:
        rows.append(dict(line=first, offset=0, kind="extraction", name="shell", text=text,
                         category="extraction-error", original_argv=None,
                         synthesized_argv=None, reason=str(exc)))
    return rows


def _spans(text):
    """Yield (offset, inline content), including multiline backtick spans."""
    pattern = re.compile(r"(`+)(.*?)\1", re.DOTALL)
    for match in pattern.finditer(text):
        yield match.start(), match.group(2)


def _execution_context(paragraph, offset):
    prefix = paragraph[:offset].rstrip()
    return bool(re.search(r"\b(?:(?:run|execute|invoke|submit|use)(?:\s+(?:it|one|as|this|the|following|shell|example|command))*|(?:for\s+)?example)\s*[:—-]?\s*$", prefix, re.I))


def _inline_variants(text):
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if char in "'\"":
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif quote is None:
            match = re.match(r"--[a-z-]+(?:\|--[a-z-]+)+", text[index:])
            if match:
                return [text[:index] + choice + text[index + match.end():]
                        for choice in match.group(0).split("|")]
        index += 1
    return [text]


def _prose_rows(text, first, declarations):
    spans = list(_spans(text))
    rows = []
    assigned = {}
    for category, declaration in declarations:
        allowed = {"kind", "text"} if category == "reference" else {"text", "transcript"}
        if category == "reference" and declaration.get("kind") == "option" and "target" in declaration:
            allowed.add("target")
        if set(declaration) != allowed:
            rows.append(dict(line=first, category="annotation-error", reason="invalid declaration fields"))
            continue
        matches = [(offset, span) for offset, span in spans if span == declaration["text"]]
        if len(matches) != 1 or matches[0][0] in assigned:
            rows.append(dict(line=first, category="annotation-error", reason="declaration must bind exactly one new inline span"))
            continue
        assigned[matches[0][0]] = (category, declaration)
    for offset, span in spans:
        line = first + text[:offset].count("\n")
        declared = assigned.get(offset)
        if declared:
            category, declaration = declared
            try:
                target_text = declaration.get("target", "")
                if target_text:
                    target_tokens = shlex.split(target_text)
                    context_target = _target(target_tokens)
                    if context_target is None or (context_target[0] == "los" and len(context_target[2]) != 1) or (context_target[0] == "tool" and context_target[2]):
                        raise ValueError("option reference target must be an entrypoint/subcommand")
                target = _target(shlex.split((target_text + " " + span).strip()))
            except ValueError:
                target = None
            if target is None:
                rows.append(dict(line=line, category="annotation-error", reason="declared span has no command target"))
                continue
            kind, name, argv = target
            rows.append(dict(line=line, offset=offset, text=span, kind=kind, name=name,
                             category=category, declaration=declaration, source_argv=shlex.split(span), original_argv=argv,
                             synthesized_argv=None, reason="execution prose cannot declare a reference"
                             if category == "reference" and _execution_context(text, offset) else None))
        else:
            try:
                tokens = shlex.split(span)
            except ValueError:
                tokens = []
            target = _target(tokens)
            if target and not target[2] and len(tokens) == 1 and not _execution_context(text, offset):
                rows.append(dict(line=line, offset=offset, text=span, kind="tool", name=target[1],
                                 category="file-reference", original_argv=[], synthesized_argv=None, reason=None))
            else:
                for variant in _inline_variants(span.replace("\n", " ")):
                    variant_rows = _shell_rows(variant, line)
                    for row in variant_rows:
                        row["source_text"] = span
                    rows.extend(variant_rows)
    return rows


def _document_rows(text):
    lines = text.splitlines()
    rows = []
    paragraph = []
    paragraph_first = 1
    declarations = []
    fence = None
    fence_kind = ""
    pending = []
    pending_first = 0

    def prose_flush():
        nonlocal paragraph, declarations
        if paragraph:
            rows.extend(_prose_rows("\n".join(paragraph), paragraph_first, declarations))
            paragraph, declarations = [], []

    for number, line in enumerate(lines, 1):
        marker = FENCE_RE.match(line)
        if marker:
            if fence is None:
                prose_flush()
                if declarations:
                    rows.append(dict(line=number, category="annotation-error", reason="reference cannot target a fence"))
                    declarations = []
                fence, fence_kind = marker.group(1), marker.group(2).strip().split(" ", 1)[0]
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                if pending:
                    rows.extend(_shell_rows(" ".join(pending), pending_first))
                    pending = []
                fence = None
            continue
        if fence is not None:
            if fence_kind == "scrut":
                if pending:
                    pending.append(line)
                elif line.startswith("$ "):
                    pending, pending_first = [line[2:]], number
                else:
                    rows.extend(_mentions(line, number, "scrut-output"))
                    continue
            elif fence_kind in SHELL_KINDS:
                if not pending:
                    pending_first = number
                pending.append(line)
            else:
                rows.extend(_mentions(line, number, "fenced-data"))
                continue
            if line.rstrip().endswith("\\"):
                pending[-1] = pending[-1].rstrip()[:-1]
            else:
                rows.extend(_shell_rows(" ".join(pending), pending_first))
                pending = []
            continue
        annotation = ANNOTATION_RE.match(line)
        if annotation:
            prose_flush()
            try:
                declaration = json.loads(annotation.group(2))
                if not isinstance(declaration, dict):
                    raise ValueError("declaration is not an object")
                declarations.append((annotation.group(1), declaration))
            except ValueError as exc:
                rows.append(dict(line=number, category="annotation-error", reason=str(exc)))
        elif re.search(r"<!-- los:(?:reference|macro)\b", line):
            prose_flush()
            rows.append(dict(line=number, category="annotation-error", reason="malformed A8 annotation"))
        elif not line.strip():
            prose_flush()
        else:
            if not paragraph:
                paragraph_first = number
            paragraph.append(line)
    prose_flush()
    if declarations:
        rows.append(dict(line=len(lines), category="annotation-error", reason="unbound declaration"))
    if fence is not None:
        rows.append(dict(line=len(lines), category="extraction-error", reason="unclosed fence"))
    return rows


def _evaluate(rows, tools):
    for row in rows:
        if row.get("reason") or row["category"] in {"scrut-output", "fenced-data", "shell-data"}:
            continue
        name = row.get("name")
        parser = tools.get(name)
        if parser is None:
            row["reason"] = f"unknown tool/command target {name}"
            continue
        category = row["category"]
        argv = row.get("parser_argv", row.get("original_argv", []))
        try:
            if category == "file-reference":
                if row["kind"] == "tool" and not (ROOT / "tools" / f"{name}.py").is_file():
                    raise ValueError(f"unknown file reference tools/{name}.py")
                continue
            if category == "macro":
                declaration = row["declaration"]
                transcript = ROOT / declaration["transcript"]
                if argv != ["<expansion>"] or name != "los":
                    raise ValueError("argv macro must contain only the <expansion> slot")
                if (transcript.resolve().parent != (ROOT / "system/procedures").resolve()
                        or transcript.suffix != ".md" or not transcript.is_file()):
                    raise ValueError("argv macro requires an existing procedure transcript")
                body = transcript.read_text(encoding="utf-8")
                if "--expected-snapshot" not in body or not re.search(r"^\$ .*los ", body, re.M):
                    raise ValueError("argv macro transcript must show a concrete guarded expansion")
                continue
            if category == "reference" and row["declaration"]["kind"] == "entrypoint":
                if argv:
                    raise ValueError("entrypoint reference cannot contain argv")
                row["synthesized_argv"] = []
                continue
            filled = _normalize(parser, argv)
            if category == "reference":
                filled = _reference_completion(parser, filled, row["declaration"]["kind"])
            row["synthesized_argv"] = filled
            row["reason"] = _parse(parser, filled)
        except (ValueError, TypeError) as exc:
            row["reason"] = str(exc)
    return rows


def _scan(products, inventory_path=None):
    _, tools = products
    failures = Counter()
    reasons = {}
    inventory = []
    for doc in _binding_docs():
        rows = _evaluate(_document_rows((ROOT / doc).read_text(encoding="utf-8")), tools)
        for row in rows:
            row["doc"] = doc
            inventory.append(row)
            if row.get("reason"):
                signature = f"{doc}::{row['line']}"
                failures[signature] += 1
                reasons.setdefault(signature, row["reason"])
    if inventory_path is not None:
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(json.dumps({"categories": dict(Counter(row["category"] for row in inventory)),
                                              "matches": inventory}, indent=2) + "\n", encoding="utf-8")
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


def test_doc_commands_parse(tmp_path):
    _, tools = _parsers()
    current, reasons = _scan((tools["los"], tools), inventory_path=Path(os.environ.get("LOS_A8_INVENTORY", str(tmp_path / "A8-candidates.json"))))
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
