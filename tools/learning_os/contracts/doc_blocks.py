"""Documentation projections from their declared owners (PLAN 5.2, SPEC 16).

Callers supply semantic registry names at their own layer. CLI names come from
the same request metadata as the generated parser; the tool also binds them to
the actual parser. Checking never writes, and rewriting preflights every owner
and marker before changing any block interior.
"""
from __future__ import annotations

import json
import posixpath
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import normative_corpus
from .capability_catalog import CapabilityCatalogError, load_capability_catalog

OWNERS = {
    "capability-count": "system/AI-ACTIONS.md",
    "predicate-count": "system/SEMANTIC-CONTRACT.md",
    "cli-command-list": "README.md",
    "procedure-index": "system/OPERATOR.md",
}
INDEX = "system/procedures/INDEX.yaml"
REQUESTS = "system/schema/requests"
_OPEN = re.compile(r"<!-- los:generated name=([a-z][a-z0-9-]*) -->")
_END = "<!-- /los:generated -->"


class DocBlockError(ValueError):
    """A required owner or marker cannot be trusted."""

    def __init__(self, message: str, path: str):
        self.message = message
        self.path = path
        super().__init__(f"{path}: {message}")


@dataclass(frozen=True)
class DocBlockIssue:
    message: str
    path: str
    code: str = "DOC-BLOCK-STALE"


@dataclass(frozen=True)
class ProcedureRow:
    doc: str
    heading: str
    transcript: str | None = None
    untranscribable: str | None = None


@dataclass(frozen=True)
class BlockValues:
    write_capabilities: int
    queries: int
    predicate_names: tuple[str, ...]
    cli_command_names: tuple[str, ...]
    procedures: tuple[ProcedureRow, ...]


@dataclass(frozen=True)
class _Block:
    name: str
    start: int
    end: int


def _read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise DocBlockError("owner escapes repository", relative)
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocBlockError(f"cannot read required owner: {exc}", relative) from exc


def applies(root: Path) -> bool:
    """Unmarked learner-data fixtures without the documentation spine exempt.

    README alone is common in synthetic learner-data tests. Any production
    spine owner, INDEX, or actual generated marker activates strict checking.
    Removing one owner or marker from production cannot turn this check off.
    """
    if any((root / relative).exists() for relative in (
        INDEX, "system/OPERATOR.md", "system/SEMANTIC-CONTRACT.md", "system/AI-ACTIONS.md"
    )):
        return True
    return any("<!-- los:generated" in _read(root, relative)
               or _END in _read(root, relative)
               for relative in normative_corpus.corpus_files(root))


def _blocks(text: str, relative: str) -> tuple[_Block, ...]:
    found = []
    active = None
    seen = set()
    offset = 0
    for line in text.splitlines(keepends=True):
        value = line.rstrip("\r\n")
        candidate = value.lstrip()
        if candidate.startswith(("<!-- los:generated", "<!-- /los:generated")):
            opening = _OPEN.fullmatch(value)
            if opening:
                name = opening.group(1)
                if name not in OWNERS:
                    raise DocBlockError(f"unknown generated block {name!r}", relative)
                if active is not None:
                    raise DocBlockError("nested generated block", relative)
                if name in seen:
                    raise DocBlockError(f"duplicate generated block {name!r}", relative)
                if relative != OWNERS[name]:
                    raise DocBlockError(f"{name} belongs in {OWNERS[name]}", relative)
                seen.add(name)
                active = (name, offset + len(line))
            elif value == _END:
                if active is None:
                    raise DocBlockError("unmatched generated block end", relative)
                found.append(_Block(active[0], active[1], offset))
                active = None
            else:
                raise DocBlockError("malformed generated block marker", relative)
        offset += len(line)
    if active is not None:
        raise DocBlockError("generated block has no closing marker", relative)
    return tuple(found)


def _documents(root: Path) -> dict[str, tuple[str, tuple[_Block, ...]]]:
    try:
        corpus = normative_corpus.load(root)
    except (normative_corpus.NormativeCorpusError, UnicodeError) as exc:
        raise DocBlockError(str(exc), normative_corpus.CORPUS_RELATIVE) from exc
    indexed = {doc.path for doc in corpus.documents}
    documents = {}
    for relative in sorted(indexed | set(OWNERS.values())):
        if relative not in indexed and relative in OWNERS.values():
            raise DocBlockError("generated block owner is absent from normative corpus", relative)
        if relative not in OWNERS.values() and not (root / relative).is_file():
            # The normative-corpus validator separately reports absent prose.
            continue
        text = _read(root, relative)
        documents[relative] = (text, _blocks(text, relative))
    for name, relative in OWNERS.items():
        if not any(block.name == name for block in documents[relative][1]):
            raise DocBlockError(f"required generated block {name!r} is missing", relative)
    return documents


def _names(values: Iterable[str], owner: str) -> tuple[str, ...]:
    names = tuple(values)
    if not names or any(not isinstance(name, str) or not name.strip() for name in names):
        raise DocBlockError("registry names must be nonempty strings", owner)
    if len(set(names)) != len(names):
        raise DocBlockError("registry names must be unique", owner)
    return tuple(sorted(names))


def collect(root: Path, *, predicate_names: Iterable[str],
            cli_command_names: Iterable[str] | None = None) -> BlockValues:
    """Load strict metadata owners; never infer an empty missing registry."""
    root = Path(root)
    _documents(root)
    catalog_path = "system/contracts/capabilities.yaml"
    try:
        catalog = load_capability_catalog(root)
    except (CapabilityCatalogError, OSError, UnicodeError) as exc:
        raise DocBlockError(str(exc), catalog_path) from exc
    for section in ("commands", "queries"):
        if not isinstance(catalog.get(section), dict):
            raise DocBlockError(f"capability catalogue {section} must be a mapping", catalog_path)
    requests = root / REQUESTS
    if not requests.is_dir():
        raise DocBlockError("request-schema directory is missing", REQUESTS)
    commands = []
    for path in sorted(requests.glob("*.schema.json")):
        relative = path.relative_to(root).as_posix()
        try:
            schema = json.loads(_read(root, relative))
        except ValueError as exc:
            raise DocBlockError(f"cannot parse request schema: {exc}", relative) from exc
        if not isinstance(schema, dict):
            raise DocBlockError("request schema must be an object", relative)
        binding = schema.get("x-los-cli-command")
        if binding is not None:
            if not isinstance(binding, dict) or not isinstance(binding.get("name"), str):
                raise DocBlockError("CLI binding has no command name", relative)
            commands.append(binding["name"])
    names = _names(commands, REQUESTS)
    if cli_command_names is not None and names != _names(cli_command_names, REQUESTS):
        raise DocBlockError("actual parser command names differ from schema bindings", REQUESTS)
    try:
        index = yaml.safe_load(_read(root, INDEX))
    except yaml.YAMLError as exc:
        raise DocBlockError(f"cannot parse procedure index: {exc}", INDEX) from exc
    if not isinstance(index, dict) or index.get("schema") != 1 \
            or not isinstance(index.get("sections"), list):
        raise DocBlockError("procedure index must declare schema 1 and sections", INDEX)
    procedures = []
    seen = set()
    for row in index["sections"]:
        if not isinstance(row, dict) or row.get("class") not in ("procedure", "rule"):
            raise DocBlockError("procedure index has an invalid section", INDEX)
        doc, heading = row.get("doc"), row.get("heading")
        if not isinstance(doc, str) or not isinstance(heading, str) or not heading.startswith("## "):
            raise DocBlockError("procedure index requires doc and top-level heading", INDEX)
        if (doc, heading) in seen:
            raise DocBlockError("procedure index has a duplicate section", INDEX)
        seen.add((doc, heading))
        _read(root, doc)
        if row["class"] != "procedure":
            continue
        transcript, reason = row.get("transcript"), row.get("untranscribable")
        if bool(transcript) == bool(reason) or any(
            value is not None and (not isinstance(value, str) or not value.strip())
            for value in (transcript, reason)
        ):
            raise DocBlockError("procedure requires exactly one transcript or boundary reason", INDEX)
        if transcript:
            target = (root / transcript).resolve()
            procedures_root = (root / "system/procedures").resolve()
            if target.parent != procedures_root or target.suffix != ".md":
                raise DocBlockError(
                    "transcript must name a runnable system/procedures/*.md file", INDEX)
            _read(root, transcript)
        procedures.append(ProcedureRow(doc, heading, transcript, reason))
    if not procedures:
        raise DocBlockError("procedure index contains no procedures", INDEX)
    return BlockValues(len(catalog.get("commands", {})), len(catalog.get("queries", {})),
                       _names(predicate_names, "tools/learning_os/semantics/predicates.py"),
                       names, tuple(procedures))


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _render(name: str, values: BlockValues, relative: str) -> str:
    if name == "capability-count":
        return f"{values.write_capabilities} write capabilities, {values.queries} queries\n"
    if name == "predicate-count":
        return f"{len(values.predicate_names)} predicates\n"
    if name == "cli-command-list":
        return ", ".join(values.cli_command_names) + "\n"
    rows = ["| Source | Procedure | Execution |", "|---|---|---|"]
    parent = posixpath.dirname(relative) or "."
    for row in values.procedures:
        source = posixpath.relpath(row.doc, parent)
        execution = (f"[Transcript]({posixpath.relpath(row.transcript, parent)})"
                     if row.transcript else f"Untranscribable: {_cell(row.untranscribable or '')}")
        rows.append(f"| [{row.doc}]({source}) | {_cell(row.heading[3:])} | {execution} |")
    return "\n".join(rows) + "\n"


def _replacements(root: Path, values: BlockValues) -> dict[str, str]:
    replacements = {}
    for relative, (text, blocks) in _documents(root).items():
        revised = text
        for block in reversed(blocks):
            revised = revised[:block.start] + _render(block.name, values, relative) + revised[block.end:]
        if revised != text:
            replacements[relative] = revised
    return replacements


def check(root: Path, values: BlockValues) -> list[DocBlockIssue]:
    """Report stale or structurally invalid blocks without writes."""
    try:
        return [DocBlockIssue("generated documentation differs from its owners; run "
                              "`.venv/bin/python tools/doc_blocks.py --write`", relative)
                for relative in _replacements(root, values)]
    except DocBlockError as exc:
        return [DocBlockIssue(exc.message, exc.path)]


def write(root: Path, values: BlockValues) -> tuple[Path, ...]:
    """Rewrite interiors only, after all documents pass structural preflight."""
    replacements = _replacements(root, values)
    for relative, text in replacements.items():
        (root / relative).write_bytes(text.encode("utf-8"))
    return tuple(root / relative for relative in replacements)
