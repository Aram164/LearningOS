"""Candidate B: run ``los-transcript`` fences as procedure transcripts.

Implements SPEC §7.2 (PLAN D11). A transcript is Markdown; every fenced
block with the language ``los-transcript`` is one block, every other fence
is prose. The first block of every transcript is ``$ los-fixture
rich_world``; the runner executes it as a built-in through the shared
:func:`scenario_harness.prepare_transcript_fixture`.

Line meanings are SPEC §7.2's table. Reading rules the table fixes only by
shape: a block is a sequence of ``$`` commands, each followed by the
expectation lines for that command (``>``, ``!``, ``= exit``); ``# bind``
and ``@`` lines execute where they stand; ``xfail`` is valid only as the
block's first line. Expected stdout/stderr lines must match the actual
lines exactly in count and order; ``{{*}}`` matches any run of characters
and ``{{re:…}}`` is an inline regex, both full-line. Blank lines are
skipped. Anything else fails the block.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent

sys.path.insert(0, str(TESTS_DIR))
try:
    from scenario_harness import prepare_transcript_fixture  # noqa: E402
finally:
    del sys.path[0]

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_STEP_RE = re.compile(r"\.([^.\[]+)|\[(\d+)\]")
_PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}")


class TranscriptFailure(AssertionError):
    """One transcript block failed; the message names file:line."""


@dataclass
class _Command:
    line_no: int
    argv_text: str
    want_stdout: list[tuple[int, str]] = field(default_factory=list)
    want_stderr: list[tuple[int, str]] = field(default_factory=list)
    want_exit: int = 0
    exit_line: int = 0
    run: _Run | None = None


@dataclass
class _Run:
    stdout: str
    stderr: str
    exit: int


class _Transcript:
    def __init__(self, path: Path, repo: Path):
        self.path = path
        self.repo = repo
        self.root: Path | None = None
        self.observations: Path | None = None
        self.bound: dict[str, str] = {}

    def fail(self, line_no: int, detail: str, expected: str = "",
             actual: str = "") -> TranscriptFailure:
        message = f"{self.path.name}:{line_no}: {detail}"
        if expected or actual:
            message += f"\n  expected: {expected}\n  actual:   {actual}"
        return TranscriptFailure(message)

    # -- blocks ------------------------------------------------------

    def _blocks(self) -> list[tuple[int, list[tuple[int, str]]]]:
        """(opener line, [(line no, text)]) for every los-transcript fence."""
        blocks = []
        current: list[tuple[int, str]] | None = None
        opener = 0
        for number, raw in enumerate(
                self.path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = raw.strip()
            if current is None:
                if stripped.startswith("```"):
                    info = stripped[3:].strip().split()
                    if info and info[0] == "los-transcript":
                        current = []
                        opener = number
            elif stripped.startswith("```"):
                blocks.append((opener, current))
                current = None
            else:
                current.append((number, raw))
        if current is not None:
            raise self.fail(opener, "unclosed los-transcript block")
        return blocks

    def run(self) -> None:
        blocks = self._blocks()
        for index, (opener, lines) in enumerate(blocks):
            self._run_block(index, opener, lines)

    def _run_block(self, index: int, opener: int,
                   lines: list[tuple[int, str]]) -> None:
        xfail_id: str | None = None
        first = True
        current: _Command | None = None
        failed: TranscriptFailure | None = None
        try:
            for number, raw in lines:
                stripped = raw.strip()
                if not stripped:
                    continue
                head = stripped.split(None, 1)
                if first and head[0] == "xfail":
                    if len(head) != 2:
                        raise self.fail(number, "xfail needs an M-id")
                    xfail_id = head[1]
                    first = False
                    continue
                first = False
                if stripped.startswith("$") and (
                        stripped == "$" or stripped[1] in " \t"):
                    if current is not None:
                        self._finalize(current)
                    text = stripped[1:].strip()
                    if not text:
                        raise self.fail(number, "empty command")
                    current = _Command(line_no=number, argv_text=text)
                    self._execute(index, current)
                elif stripped.startswith(">"):
                    if current is None:
                        raise self.fail(number, "expectation without a command")
                    current.want_stdout.append((number, _payload(stripped)))
                elif stripped.startswith("!"):
                    if current is None:
                        raise self.fail(number, "expectation without a command")
                    current.want_stderr.append((number, _payload(stripped)))
                elif stripped.startswith("="):
                    if current is None:
                        raise self.fail(number, "expectation without a command")
                    words = stripped[1:].split()
                    if len(words) != 2 or words[0] != "exit":
                        raise self.fail(number, f"bad exit line: {stripped!r}")
                    try:
                        current.want_exit = int(words[1])
                    except ValueError:
                        raise self.fail(
                            number,
                            f"bad exit line: {stripped!r}") from None
                    current.exit_line = number
                elif stripped.startswith("#"):
                    self._bind(current, number, stripped)
                elif stripped.startswith("@"):
                    self._assert_state(number, stripped)
                else:
                    raise self.fail(number, f"unknown line: {stripped!r}")
            if current is not None:
                self._finalize(current)
        except TranscriptFailure as exc:
            failed = exc
        if xfail_id is not None:
            if failed is None:
                raise self.fail(opener, f"unexpected pass (xfail {xfail_id})")
            return
        if failed is not None:
            raise failed

    # -- commands ----------------------------------------------------

    def _execute(self, index: int, command: _Command) -> None:
        words = command.argv_text.split(None, 1)
        if index == 0 and words[0] == "los-fixture":
            if len(words) != 2:
                raise self.fail(command.line_no,
                                "los-fixture needs one fixture name")
            container = Path(tempfile.mkdtemp(prefix="los-fx-"))
            try:
                built = prepare_transcript_fixture(
                    words[1], container, seed=self.path.name)
            except ValueError as exc:
                raise self.fail(command.line_no, str(exc)) from exc
            self.root = built["root"]
            self.observations = built["observations"]
            command.run = _Run(stdout="", stderr="", exit=0)
            return
        if self.root is None or self.observations is None:
            raise self.fail(command.line_no, "no fixture: the first block"
                            " must be `$ los-fixture rich_world`")
        prelude = (
            f'los() {{ {self.repo}/.venv/bin/python'
            f' {self.repo}/tools/los.py --root "$LOS_FX" "$@"; }}\n'
            f'los-seal() {{ {self.repo}/.venv/bin/python'
            f' {self.repo}/tools/seal_envelope.py --root "$LOS_FX" "$@"; }}\n')
        env = dict(os.environ, LOS_FX=str(self.root),
                   LOS_OBSERVATIONS=str(self.observations),
                   TZ="Europe/Berlin", **self.bound)
        proc = subprocess.run(["bash", "-c", prelude + command.argv_text],
                              capture_output=True, text=True, timeout=300,
                              env=env, cwd=self.root)
        command.run = _Run(stdout=proc.stdout, stderr=proc.stderr,
                           exit=proc.returncode)

    def _finalize(self, command: _Command) -> None:
        run = command.run
        assert run is not None
        if run.exit != command.want_exit:
            raise self.fail(command.exit_line or command.line_no,
                            f"exit {run.exit}, want {command.want_exit}",
                            f"exit {command.want_exit}", f"exit {run.exit}")
        self._match_lines(command.line_no, "stdout", run.stdout,
                          command.want_stdout)
        self._match_lines(command.line_no, "stderr", run.stderr,
                          command.want_stderr)

    def _match_lines(self, fallback: int, stream: str, actual_text: str,
                     want: list[tuple[int, str]]) -> None:
        actual = actual_text.split("\n")
        if actual and actual[-1] == "":
            actual.pop()
        for position, (number, pattern) in enumerate(want):
            if position >= len(actual):
                raise self.fail(number, f"{stream} line {position + 1}:"
                                " missing, want a line",
                                pattern, "<end of output>")
            try:
                regex = _translate(pattern)
            except ValueError as exc:
                raise self.fail(number, str(exc)) from exc
            if not re.fullmatch(regex, actual[position]):
                raise self.fail(number, f"{stream} line {position + 1} differs",
                                pattern, actual[position])
        if len(actual) > len(want):
            raise self.fail(fallback, f"{stream}: {len(actual) - len(want)}"
                            " surplus line(s)",
                            f"{len(want)} line(s)",
                            "\n".join(actual[len(want):])[:500])

    # -- directives --------------------------------------------------

    def _bind(self, current: _Command | None, number: int,
              stripped: str) -> None:
        words = stripped[1:].split(None, 3)
        if len(words) != 4 or words[0] != "bind" or words[2] != "=":
            raise self.fail(number, f"bad bind line: {stripped!r}")
        name, path = words[1], words[3]
        if not _NAME_RE.match(name):
            raise self.fail(number, f"bad variable name {name!r}")
        if current is None or current.run is None:
            raise self.fail(number, "bind without a command")
        try:
            document = json.loads(current.run.stdout)
        except json.JSONDecodeError as exc:
            raise self.fail(number, f"stdout is not JSON: {exc}") from exc
        ok, value, error = _resolve(document, path)
        if not ok:
            raise self.fail(number, error)
        self.bound[name] = (value if isinstance(value, str)
                            else json.dumps(value))

    def _assert_state(self, number: int, stripped: str) -> None:
        if self.root is None:
            raise self.fail(number, "no fixture yet")
        words = stripped[1:].split()
        if words[:3] == ["receipt", "last", "capability"]:
            if len(words) != 4:
                raise self.fail(number, f"bad receipt line: {stripped!r}")
            self._assert_receipt(number, words[3])
        elif words[:1] == ["file"] and len(words) >= 3:
            path = words[1]
            if words[2] == "sha256" and len(words) == 4:
                self._assert_file_sha(number, path, words[3])
            elif words[2] in ("exists", "absent") and len(words) == 3:
                self._assert_file_presence(number, path, words[2] == "exists")
            else:
                raise self.fail(number, f"bad file line: {stripped!r}")
        else:
            raise self.fail(number, f"bad @ line: {stripped!r}")

    def _assert_receipt(self, number: int, want: str) -> None:
        import yaml

        receipts = sorted(
            (self.root / "operations" / "transactions").glob(
                "transaction-*.yaml"),
            key=lambda path: path.stat().st_mtime)
        if not receipts:
            raise self.fail(number, "no transaction receipt", want, "none")
        actual = yaml.safe_load(receipts[-1].read_text(
            encoding="utf-8")).get("capability")
        if actual != want:
            raise self.fail(number, f"{receipts[-1].name} names {actual!r}",
                            want, repr(actual))

    def _assert_file_sha(self, number: int, path: str, want: str) -> None:
        import hashlib

        target = self.root / path
        try:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:
            raise self.fail(number, f"{path}: file is absent",
                            f"sha256 {want}", "absent") from None
        if actual.lower() != want.lower():
            raise self.fail(number, f"{path}: sha256 differs",
                            want, actual)

    def _assert_file_presence(self, number: int, path: str,
                              want_present: bool) -> None:
        target = self.root / path
        present = target.exists() if want_present else target.lexists()
        if want_present and not present:
            raise self.fail(number, f"{path}: want present, is absent",
                            "present", "absent")
        if not want_present and present:
            raise self.fail(number, f"{path}: want absent, is present",
                            "absent", "present")


def _payload(stripped: str) -> str:
    """An expectation's text: the marker plus one space removed."""
    rest = stripped[1:]
    return rest[1:] if rest.startswith(" ") else rest


def _resolve(document: object, path: str) -> tuple[bool, object, str]:
    """Resolve a ``$.a.b[0]`` style path; (ok, value, error)."""
    text = path[1:] if path.startswith("$") else path
    if text == "":
        return True, document, ""
    node = document
    pos = 0
    while pos < len(text):
        match = _STEP_RE.match(text, pos)
        if match is None:
            return False, None, f"bad JSONPATH {path!r}"
        key, index = match.groups()
        if key is not None:
            if not isinstance(node, dict) or key not in node:
                return False, None, f"{path!r}: no key {key!r}"
            node = node[key]
        else:
            if not isinstance(node, list) or int(index) >= len(node):
                return False, None, f"{path!r}: no index [{index}]"
            node = node[int(index)]
        pos = match.end()
    return True, node, ""


def _translate(pattern: str) -> str:
    """An expectation line to a regex source; ``{{*}}``/``{{re:…}}``."""
    pieces = []
    pos = 0
    for match in _PLACEHOLDER_RE.finditer(pattern):
        pieces.append(re.escape(pattern[pos:match.start()]))
        body = match.group(1)
        if body == "*":
            pieces.append(".*")
        elif body.startswith("re:"):
            pieces.append(f"(?:{body[3:]})")
        else:
            raise ValueError(f"bad pattern {match.group(0)!r}")
        pos = match.end()
    pieces.append(re.escape(pattern[pos:]))
    return "".join(pieces)


def run_transcript(path: str | Path, *, repo: str | Path | None = None) -> None:
    """Run one transcript; raise :class:`TranscriptFailure` on mismatch."""
    resolved = Path(path)
    _Transcript(resolved,
                REPO_ROOT if repo is None else Path(repo)).run()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: procedures_runner.py TRANSCRIPT...", file=sys.stderr)
        return 2
    failures = 0
    for name in argv[1:]:
        try:
            run_transcript(name)
        except TranscriptFailure as exc:
            print(f"{exc}", file=sys.stderr)
            print(f"{name}: FAIL")
            failures += 1
        else:
            print(f"{name}: ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
