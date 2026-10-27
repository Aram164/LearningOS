"""Loader and checks for ``system/contracts/task-scope.yaml``.

The normative corpus classifies documents and their optional applicability.
This contract supplies the task-shaped view. Each task names the
entry read that starts it, the executable procedure that carries it, and the
binding documents that scope it. Nothing here is inferred: the loader checks
that every scoped document is a binding corpus document, that every named
procedure exists with the anchor it claims, and that every verb in an entry
read is a real command. Explicit corpus applicability must agree in both
directions with these task scopes.
"""

from __future__ import annotations

import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from learning_os.store.contracts import normative_corpus

CONTRACT_RELATIVE = "system/contracts/task-scope.yaml"
REQUESTS_RELATIVE = "system/schema/requests"
PROCEDURES_RELATIVE = "system/procedures"
OPERATOR_RELATIVE = "system/OPERATOR.md"
ENTRY_HEADING = "## Start here"


class TaskScopeError(Exception):
    pass


@dataclass(frozen=True)
class ProcedureLink:
    label: str
    target: str
    path: str
    anchor: str


@dataclass(frozen=True)
class TaskScope:
    id: str
    task: str
    entry_read: str
    entry_verb: str | None
    procedures: tuple[ProcedureLink, ...]
    procedure_text: str | None
    scope: tuple[str, ...]


def _slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def _heading_slugs(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {
        _slug(heading)
        for heading in re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    }


def scoped_paths(scope: tuple[str, ...]) -> set[str]:
    """The documents a scope names, whole or by one of their sections."""
    return {entry.partition("#")[0] for entry in scope}


#: What ``capabilities TASK --json`` inlines (agent-cost plan D7). Every early
#: read stays in an agent's context and is paid again on every later turn, so
#: the task read carries the sections it binds instead of naming whole
#: documents. Bounded (~3k tokens in all) so the entry read stays small.
READ_SECTION_LIMIT = 6_000
READ_TOTAL_LIMIT = 12_000


def _section(path: Path, anchor: str) -> tuple[str, str, int] | None:
    """The level-2 heading, full text and first line of one ``path#anchor`` section."""
    text = path.read_text(encoding="utf-8")
    line = 1
    for part in re.split(r"(?m)^(?=## )", text):
        if part.startswith("## "):
            heading = part.splitlines()[0][3:].strip()
            if _slug(heading) == anchor:
                return heading, part.rstrip() + "\n", line
        line += part.count("\n")
    return None


def task_reading(root: Path, procedures: tuple[str, ...],
                 scope: tuple[str, ...]) -> list[dict[str, object]]:
    """The text a task binds: its procedure sections, then its scoped ones.

    Whole-document scope entries are not inlined. The operator contract is
    read at entry, and any other whole document is expanded only when the
    task crosses into it. A section cut at the bound says how much was left
    out and the exact lines that hold the rest (``rest_lines``, first and
    last, 1-based), so the next read is one ranged read, not a search.
    """
    rows: list[dict[str, object]] = []
    used = 0
    refs = [*procedures, *(entry for entry in scope if "#" in entry)]
    for ref in dict.fromkeys(refs):
        relative, _, anchor = ref.partition("#")
        if not (root / relative).is_file():
            continue
        found = _section(root / relative, anchor)
        if found is None:
            continue
        heading, text, first_line = found
        budget = max(0, min(READ_SECTION_LIMIT, READ_TOTAL_LIMIT - used))
        shown = text if len(text) <= budget else text[:budget].rsplit("\n", 1)[0] + "\n"
        if len(shown) > budget:
            shown = ""
        row: dict[str, object] = {"ref": ref, "text": shown}
        if len(shown) < len(text):
            start = first_line + shown.count("\n")
            end = first_line + text.count("\n") - 1
            row["omitted_chars"] = len(text) - len(shown)
            row["rest"] = f"{relative} lines {start}-{end}, section '## {heading}'"
            row["rest_lines"] = [start, end]
        rows.append(row)
        used += len(shown)
    return rows


def _parser_verbs(root: Path) -> set[str]:
    requests = root / REQUESTS_RELATIVE
    if not requests.is_dir():
        raise TaskScopeError(f"request-schema directory is missing: {REQUESTS_RELATIVE}")
    verbs = set()
    for path in sorted(requests.glob("*.schema.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise TaskScopeError(f"cannot read request schema {path.name}: {exc}") from exc
        binding = data.get("x-los-cli-command")
        if isinstance(binding, dict) and isinstance(binding.get("name"), str):
            verbs.add(binding["name"])
    if not verbs:
        raise TaskScopeError("no CLI verb is declared by the request schemas")
    return verbs


def entry_read_verbs(entry_read: str) -> list[str]:
    """The verbs an entry read names, in the order it names them.

    Commands are written in backticks in the operator contract, so the
    backticked spans are the commands and the prose between them is not.
    """
    spans = re.findall(r"`([^`]+)`", entry_read)
    if spans:
        candidates = [span.split()[0] for span in spans if span.split()]
    else:
        candidates = [
            segment.strip().split()[0]
            for segment in entry_read.split(",")
            if segment.strip()
        ]
    verbs = []
    for candidate in candidates:
        if candidate in {"none", "no"}:
            continue
        if not re.fullmatch(r"[a-z][a-z0-9-]*", candidate):
            continue
        verbs.append(candidate)
    return verbs


def entry_read_expansions(entry_read: str) -> list[str]:
    """The names an entry read expands with ``capabilities NAME``.

    ``capabilities capture.create --json`` starts its task at
    ``capture.create``, not at the discovery verb, so the task is linked to
    that name and ``capabilities capture.create --json`` returns the task's
    reading (#22). Placeholders (``NAME``, ``TASK``) are not names.
    """
    names = []
    for span in re.findall(r"`([^`]+)`", entry_read):
        words = span.split()
        if len(words) >= 2 and words[0] == "capabilities" \
                and re.fullmatch(r"[a-z][a-z0-9._-]*", words[1]):
            names.append(words[1])
    return names


def load_task_scope(root: Path) -> dict[str, TaskScope]:
    path = root / CONTRACT_RELATIVE
    if not path.is_file():
        raise TaskScopeError(f"task scope contract not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise TaskScopeError(f"invalid task scope contract: {exc}") from exc
    if not isinstance(data, dict) or data.get("contract") != "learningos-task-scope":
        raise TaskScopeError(
            "task scope contract must declare contract learningos-task-scope")
    if data.get("schema_version") != 1:
        raise TaskScopeError("task scope contract must declare schema_version 1")
    rows = data.get("tasks")
    if not isinstance(rows, list) or not rows:
        raise TaskScopeError("task scope contract must declare a non-empty tasks list")

    try:
        corpus = normative_corpus.load(root)
    except (normative_corpus.NormativeCorpusError, OSError, UnicodeError) as exc:
        raise TaskScopeError(
            f"the normative corpus cannot be read, so no task scope can be "
            f"resolved: {exc}") from exc
    binding = {
        document.path
        for document in corpus.documents
        if document.authority == "binding" and document.status == "current"
    }
    by_path = corpus.by_path()

    def operator_document(identifier: str, relative: str) -> None:
        document = by_path.get(relative)
        if relative not in binding or document is None:
            raise TaskScopeError(
                f"task scope {identifier} names {relative!r}, which is not "
                "a current binding document")
        if document.audience not in {"operator", "both"}:
            raise TaskScopeError(
                f"task scope {identifier} names {relative!r} with audience "
                f"{document.audience!r}; operator tasks require operator or both")
    verbs = _parser_verbs(root)
    procedures_root = root / PROCEDURES_RELATIVE
    # A synthetic repository carries the contracts without the prose spine.
    # The transcripts cannot be checked where they are not; the corpus
    # validator reports absent prose on its own.
    transcripts_present = procedures_root.is_dir()

    declared: dict[str, TaskScope] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise TaskScopeError("invalid task scope declaration")
        identifier = row.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9-]+", identifier):
            raise TaskScopeError(f"task scope id {identifier!r} is not a slug")
        if identifier in declared:
            raise TaskScopeError(f"duplicate task scope id {identifier!r}")
        task = row.get("task")
        entry_read = row.get("entry_read")
        if not isinstance(task, str) or not task.strip():
            raise TaskScopeError(f"task scope {identifier} has no task label")
        if not isinstance(entry_read, str) or not entry_read.strip():
            raise TaskScopeError(f"task scope {identifier} has no entry read")
        for verb in entry_read_verbs(entry_read):
            if verb not in verbs:
                raise TaskScopeError(
                    f"task scope {identifier} names {verb!r}, which is not a "
                    f"CLI command")
        if "entry_verb" not in row:
            raise TaskScopeError(f"task scope {identifier} must declare entry_verb (null for a boundary)")
        entry_verb = row["entry_verb"]
        if entry_verb is not None and (not isinstance(entry_verb, str) or entry_verb not in verbs):
            raise TaskScopeError(f"task scope {identifier} entry_verb must name a CLI command")
        if entry_read_verbs(entry_read) and entry_verb is None:
            raise TaskScopeError(f"task scope {identifier} executable entry needs entry_verb")
        procedures = []
        for link in row.get("procedures") or []:
            if not isinstance(link, dict):
                raise TaskScopeError(f"task scope {identifier} has an invalid procedure")
            label = link.get("label")
            target = link.get("target")
            if not isinstance(label, str) or not label.strip():
                raise TaskScopeError(f"task scope {identifier} has an unlabelled procedure")
            if not isinstance(target, str) or "#" not in target:
                raise TaskScopeError(
                    f"task scope {identifier} procedure {label!r} needs a "
                    f"path#anchor target")
            relative, _, anchor = target.partition("#")
            operator_document(identifier, relative)
            target_path = (root / relative).resolve()
            if transcripts_present:
                if target_path.parent != procedures_root.resolve() \
                        or target_path.suffix != ".md":
                    raise TaskScopeError(
                        f"task scope {identifier} procedure {label!r} must name "
                        f"a runnable system/procedures/*.md file")
                if not target_path.is_file():
                    raise TaskScopeError(
                        f"task scope {identifier} procedure {label!r} names a "
                        f"missing transcript: {relative}")
                if anchor not in _heading_slugs(target_path):
                    raise TaskScopeError(
                        f"task scope {identifier} procedure {label!r} names an "
                        f"anchor that does not exist: {relative}#{anchor}")
            procedures.append(ProcedureLink(
                label=label.strip(), target=target, path=relative, anchor=anchor))
        procedure_text = row.get("procedure_text")
        if procedure_text is not None and (
            not isinstance(procedure_text, str) or not procedure_text.strip()
        ):
            raise TaskScopeError(
                f"task scope {identifier} has an invalid procedure_text")
        if not procedures and not procedure_text:
            raise TaskScopeError(
                f"task scope {identifier} names no procedure and no boundary text")
        if procedures and procedure_text:
            raise TaskScopeError(
                f"task scope {identifier} declares both a procedure and a "
                f"boundary text")
        scope = row.get("scope") or []
        if not isinstance(scope, list) or not scope:
            raise TaskScopeError(f"task scope {identifier} declares no scope")
        for document in scope:
            # A scope entry is a whole binding document or one of its
            # level-2 sections (`path#anchor`, the anchor rule procedures
            # use), so a task can bind the section it needs instead of the
            # whole document.
            relative, _, anchor = document.partition("#") if isinstance(document, str) \
                else ("", "", "")
            if relative not in binding:
                raise TaskScopeError(
                    f"task scope {identifier} scopes {document!r}, which is not "
                    f"a current binding document")
            operator_document(identifier, relative)
            # Checked where the document is present, as procedure anchors
            # are where the transcripts are: a synthetic repository carries
            # the contracts without the prose they scope.
            if anchor and (root / relative).is_file() \
                    and anchor not in _heading_slugs(root / relative):
                raise TaskScopeError(
                    f"task scope {identifier} scopes a section that does not "
                    f"exist: {document}")
        declared[identifier] = TaskScope(
            id=identifier,
            task=task.strip(),
            entry_read=entry_read.strip(),
            entry_verb=entry_verb,
            procedures=tuple(procedures),
            procedure_text=procedure_text.strip() if procedure_text else None,
            scope=tuple(scope),
        )
    for document in corpus.documents:
        if document.applies_to is None:
            continue
        actual = set(document.applies_to)
        unknown = actual - declared.keys()
        if unknown:
            raise TaskScopeError(
                f"corpus document {document.path} applies to unknown tasks: "
                f"{', '.join(sorted(unknown))}")
        expected = {task.id for task in declared.values()
                    if document.path in scoped_paths(task.scope)}
        if actual != expected:
            raise TaskScopeError(
                f"corpus document {document.path} applicability disagrees with "
                f"task scopes: missing={sorted(expected - actual)}, "
                f"extra={sorted(actual - expected)}")
    return declared


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _relative_target(target: str, parent: str) -> str:
    path, _, anchor = target.partition("#")
    relative = posixpath.relpath(path, parent)
    return f"{relative}#{anchor}" if anchor else relative


def render_entry_table(tasks: dict[str, TaskScope], *, owner: str = OPERATOR_RELATIVE) -> str:
    """The operator entry table, as the contract declares it."""
    parent = posixpath.dirname(owner) or "."
    rows = ["| Task | Entry read | Executable procedure |", "|---|---|---|"]
    for task in tasks.values():
        if task.procedures:
            links = ", ".join(
                f"[{_cell(link.label)}]({_relative_target(link.target, parent)})"
                for link in task.procedures
            )
        else:
            links = _cell(task.procedure_text or "")
        rows.append(f"| {_cell(task.task)} | {_cell(task.entry_read)} | {links} |")
    return "\n".join(rows) + "\n"


def operator_entry_table(root: Path, *, owner: str = OPERATOR_RELATIVE) -> str | None:
    """The entry table as it stands in the operator contract, or None."""
    path = root / owner
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if ENTRY_HEADING not in text:
        return None
    section = text.split(ENTRY_HEADING, 1)[1].split("\n## ", 1)[0]
    lines = [line for line in section.splitlines() if line.startswith("|")]
    if not lines:
        return None
    return "\n".join(lines) + "\n"
