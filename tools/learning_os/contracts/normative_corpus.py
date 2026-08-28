"""The bindingness and supersession index over the normative corpus.

CRITIQUE-POINTS §3 diagnosed the failure precisely: the rules do not
contradict each other, but nothing says which of them are rules. ~7,800 lines
of prose under ``system/`` carry contracts, adapters, procedures, reasoning,
frozen history and dated reviews in one undifferentiated pile, so every agent
reads a different subset and returns a different picture.

``system/contracts/normative-corpus.yaml`` is that missing statement. This
module makes it executable, which is the whole difference between an index and
a promise: an index nobody checks drifts exactly the way the corpus did.

What is enforced, and why each check exists
-------------------------------------------
``MISSING``      a ``system/*.md`` / ``system/adr/*.md`` file nobody indexed.
                 Without this the corpus can grow silently again, which is how
                 it reached 7,800 lines in the first place.
``ORPHAN``       an index entry naming a file that does not exist.
``DUPLICATE``    one path indexed twice, so two rows could disagree.
``EDGE``         a supersession edge to a path outside the index; the retired
                 document would keep reading as current.
``CYCLE``        A supersedes B supersedes A — no resolvable current rule.
``STATUS``       a document retired by an edge but still marked ``current``,
                 or marked ``superseded`` with nothing retiring it.
``AUTHORITY``    a retired or frozen document still marked ``binding``.
``NO-NOTICE``    the audit CP §3 said the review owed: a retired document that
                 does not say so in its own text. ADR-010 and ADR-012 carry
                 such a notice; whether every retired document did was
                 unmeasured. It is measured here, on every run, because an
                 agent that opens the file directly never sees this index.
``ENTRYPOINT``   the declared entry point missing, retired, or non-binding.

Edge direction follows the repository's own convention for canonical notes
(ARCHITECTURE, note identity): the forward edge is authored on the successor
and the reverse link is derived, never stored.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

CORPUS_RELATIVE = "system/contracts/normative-corpus.yaml"
SCHEMA_RELATIVE = "system/contracts/normative-corpus.schema.json"

#: The two globs that define the corpus. A document under ``system/`` outside
#: these is not normative prose (schemas, templates, skills, contracts).
CORPUS_GLOBS = ("system/*.md", "system/adr/*.md")

RETIRED_STATUSES = frozenset({"superseded", "frozen"})


class NormativeCorpusError(ValueError):
    """The index itself cannot be read."""


@dataclass(frozen=True)
class Document:
    path: str
    doc_class: str
    status: str
    authority: str
    owner: str
    summary: str
    supersedes: tuple[str, ...] = ()
    amends: tuple[str, ...] = ()


@dataclass
class Corpus:
    corpus_version: int
    entrypoint: str
    documents: tuple[Document, ...]

    #: Derived, never stored — see the module docstring.
    superseded_by: dict[str, tuple[str, ...]] = field(default_factory=dict)
    amended_by: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def by_path(self) -> dict[str, Document]:
        return {doc.path: doc for doc in self.documents}

    def retired_by(self, path: str) -> tuple[str, ...]:
        """Every document that retires ``path``, wholly or in part."""
        return self.superseded_by.get(path, ()) + self.amended_by.get(path, ())


@dataclass(frozen=True)
class CorpusIssue:
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"NORMATIVE-CORPUS-{self.code}: {self.message}{location}"


def load(root: Path) -> Corpus:
    """Read and schema-validate the index. Raises rather than guessing."""
    corpus_path = root / CORPUS_RELATIVE
    if not corpus_path.is_file():
        raise NormativeCorpusError(
            f"no {CORPUS_RELATIVE} — nothing declares which documents under "
            "system/ bind and which are retired"
        )
    try:
        raw = yaml.safe_load(corpus_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise NormativeCorpusError(f"cannot read {CORPUS_RELATIVE}: {exc}") from exc
    if not isinstance(raw, dict):
        raise NormativeCorpusError(f"{CORPUS_RELATIVE} is not a mapping")

    _schema_check(root, raw)

    documents = tuple(
        Document(
            path=str(entry["path"]),
            doc_class=str(entry["class"]),
            status=str(entry["status"]),
            authority=str(entry["authority"]),
            owner=str(entry["owner"]),
            summary=str(entry["summary"]).strip(),
            supersedes=tuple(entry.get("supersedes") or ()),
            amends=tuple(entry.get("amends") or ()),
        )
        for entry in raw.get("documents") or ()
    )
    corpus = Corpus(
        corpus_version=int(raw["corpus_version"]),
        entrypoint=str(raw["entrypoint"]),
        documents=documents,
    )
    corpus.superseded_by = _reverse(documents, "supersedes")
    corpus.amended_by = _reverse(documents, "amends")
    return corpus


def _schema_check(root: Path, raw: dict) -> None:
    """Validate against the sibling schema. A missing schema is a closed door.

    The schema lives beside the index under ``system/contracts/`` rather than
    in ``system/schema/`` on purpose: the data contract fingerprints
    ``system/schema/*.schema.json`` and would read a prose-governing schema as
    a change to the stored record format.
    """
    schema_path = root / SCHEMA_RELATIVE
    if not schema_path.is_file():
        raise NormativeCorpusError(
            f"missing {SCHEMA_RELATIVE} — the index has no declared shape"
        )
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NormativeCorpusError(f"cannot read {SCHEMA_RELATIVE}: {exc}") from exc

    errors = sorted(
        Draft202012Validator(schema).iter_errors(raw),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return
    details = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors[:8]
    ]
    raise NormativeCorpusError(
        f"{CORPUS_RELATIVE} contract violation: {'; '.join(details)}")


def _reverse(documents: tuple[Document, ...], edge: str) -> dict[str, tuple[str, ...]]:
    reverse: dict[str, list[str]] = {}
    for doc in documents:
        for target in getattr(doc, edge):
            reverse.setdefault(target, []).append(doc.path)
    return {target: tuple(sorted(sources)) for target, sources in reverse.items()}


def corpus_files(root: Path) -> list[str]:
    """Every file the index must account for, repository-relative and sorted."""
    found: set[str] = set()
    for glob in CORPUS_GLOBS:
        for path in root.glob(glob):
            if path.is_file():
                found.add(path.relative_to(root).as_posix())
    return sorted(found)


def _mentions(root: Path, path: str, others: tuple[str, ...]) -> list[str]:
    """Which of ``others`` the text of ``path`` names. Stem match, case-blind.

    An ADR names its successor as "ADR-013", never by full path, so the stem's
    identifying prefix is what a notice actually contains.
    """
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return []
    unnamed = []
    for other in others:
        stem = Path(other).stem
        adr = re.match(r"^(ADR-\d+)", stem)
        needle = adr.group(1) if adr else stem
        if needle.lower() not in text.lower():
            unnamed.append(other)
    return unnamed


def check(root: Path) -> list[CorpusIssue]:
    """Every way the index and the corpus can disagree. Empty list = agreed.

    A repository with no normative prose at all has no corpus to govern, and
    the check does not apply. That is a synthetic fixture — the mini-repos the
    test suite and `module.plan.import --check` build to validate a proposed
    change in isolation — never the system: the real repository carries 35
    documents, and `test_every_system_document_on_disk_is_classified` pins
    that it is not silently in the empty state.
    """
    if not corpus_files(root):
        return []
    try:
        corpus = load(root)
    except NormativeCorpusError as exc:
        return [CorpusIssue("UNREADABLE", str(exc), CORPUS_RELATIVE)]

    issues: list[CorpusIssue] = []
    indexed = [doc.path for doc in corpus.documents]
    by_path = corpus.by_path()

    for path in sorted({p for p in indexed if indexed.count(p) > 1}):
        issues.append(CorpusIssue(
            "DUPLICATE",
            f"'{path}' is indexed {indexed.count(path)} times; two rows can "
            "disagree about what binds",
            CORPUS_RELATIVE,
        ))

    on_disk = corpus_files(root)
    for path in on_disk:
        if path not in by_path:
            issues.append(CorpusIssue(
                "MISSING",
                "normative prose that nothing classifies — add it to "
                f"{CORPUS_RELATIVE} with its class, status, authority and owner",
                path,
            ))
    for path in indexed:
        if path not in set(on_disk):
            issues.append(CorpusIssue(
                "ORPHAN",
                f"indexed but not on disk: '{path}'",
                CORPUS_RELATIVE,
            ))

    for doc in corpus.documents:
        for edge_name, targets in (("supersedes", doc.supersedes), ("amends", doc.amends)):
            for target in targets:
                if target not in by_path:
                    issues.append(CorpusIssue(
                        "EDGE",
                        f"{edge_name} '{target}', which is not indexed; the "
                        "retired document would keep reading as current",
                        doc.path,
                    ))
                elif target == doc.path:
                    issues.append(CorpusIssue(
                        "CYCLE", f"{edge_name} itself", doc.path))

    issues.extend(_cycles(corpus))

    for doc in corpus.documents:
        retired_by = corpus.superseded_by.get(doc.path, ())
        if retired_by and doc.status == "current":
            issues.append(CorpusIssue(
                "STATUS",
                f"retired whole by {', '.join(retired_by)} but still marked "
                "'current'",
                doc.path,
            ))
        if doc.status == "superseded" and not retired_by:
            issues.append(CorpusIssue(
                "STATUS",
                "marked 'superseded' but no indexed document supersedes it; "
                "name the successor's `supersedes:` edge",
                doc.path,
            ))
        if doc.status in RETIRED_STATUSES and doc.authority == "binding":
            issues.append(CorpusIssue(
                "AUTHORITY",
                f"status '{doc.status}' cannot carry authority 'binding' — a "
                "retired document is never a current rule",
                doc.path,
            ))

        # The audit CP §3 said the review owed. An agent that opens a document
        # directly never sees this index, so the notice has to be in the text.
        retiring = corpus.retired_by(doc.path)
        if retiring:
            unnamed = _mentions(root, doc.path, retiring)
            if unnamed:
                issues.append(CorpusIssue(
                    "NO-NOTICE",
                    "retired by " + ", ".join(unnamed) + " but its own text "
                    "never names it; a reader who opens this file directly "
                    "reads a retired rule as current",
                    doc.path,
                ))

    entry = by_path.get(corpus.entrypoint)
    if entry is None:
        issues.append(CorpusIssue(
            "ENTRYPOINT",
            f"declared entry point '{corpus.entrypoint}' is not indexed",
            CORPUS_RELATIVE,
        ))
    else:
        if entry.status != "current":
            issues.append(CorpusIssue(
                "ENTRYPOINT",
                f"entry point is '{entry.status}', not 'current'", entry.path))
        if entry.authority != "binding":
            issues.append(CorpusIssue(
                "ENTRYPOINT",
                f"entry point has authority '{entry.authority}'; the one "
                "document every operator enters through must bind",
                entry.path,
            ))

    return issues


def _cycles(corpus: Corpus) -> list[CorpusIssue]:
    """Depth-first search over both edge kinds; report each cycle once."""
    graph: dict[str, list[str]] = {}
    for doc in corpus.documents:
        graph[doc.path] = sorted(set(doc.supersedes) | set(doc.amends))

    issues: list[CorpusIssue] = []
    seen: set[str] = set()
    reported: set[frozenset[str]] = set()

    def walk(node: str, stack: list[str]) -> None:
        if node in stack:
            cycle = stack[stack.index(node):] + [node]
            key = frozenset(cycle)
            if key not in reported:
                reported.add(key)
                issues.append(CorpusIssue(
                    "CYCLE",
                    "supersession cycle " + " → ".join(cycle) +
                    "; no rule in it can be resolved as current",
                    cycle[0],
                ))
            return
        if node in seen:
            return
        seen.add(node)
        for nxt in graph.get(node, ()):
            walk(nxt, stack + [node])

    for path in sorted(graph):
        walk(path, [])
    return issues


def summary(root: Path) -> dict[str, int]:
    """Counts for a release report. Never used to decide anything."""
    corpus = load(root)
    counts: dict[str, int] = {"documents": len(corpus.documents)}
    for doc in corpus.documents:
        counts[f"authority:{doc.authority}"] = counts.get(f"authority:{doc.authority}", 0) + 1
        counts[f"status:{doc.status}"] = counts.get(f"status:{doc.status}", 0) + 1
    return counts
