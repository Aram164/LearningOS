"""In-memory SQLite References Validation Mixin (Role A Spike).

Drop-in replacement for learning_os.derive.validation.references.ChecksReferences.
Delegates all structural reference checks across all 15 families to an ephemeral
in-memory SQLite database, guaranteeing exact ordered diagnostic parity.

Fail-closed contract:
- sqlite3.Error halts execution with an explanatory RuntimeError; never converted
  into a false Issue diagnostic.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from learning_os.domain.validation import markdown_link_targets
from learning_os.domain.vocabulary import EVIDENCE_SCHEMES

from spike_validation_exporter import (
    ParsedReference,
    export_repo_to_sqlite,
    parse_reference_uri,
)
from spike_validation_queries import run_validation_queries
from spike_validation_schema import init_validation_db


@dataclass(frozen=True)
class ClassifiedLink:
    kind: Literal["skip", "uri", "relative"]
    target: str


def classify_markdown_link(target: str) -> ClassifiedLink:
    """Classify a Markdown target before any filesystem or registry lookup."""
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return ClassifiedLink("skip", target)
    if parse_reference_uri(target) is not None:
        return ClassifiedLink("uri", target)
    relative = target.split("#", 1)[0]
    return ClassifiedLink("relative" if relative else "skip", relative)


class ChecksReferences:
    """Mixed into Validator; provides SQLite-backed check_references and link checks."""

    def check_references(self):
        """Run all structural reference checks via an ephemeral in-memory SQLite database."""
        conn = sqlite3.connect(":memory:")
        try:
            init_validation_db(conn)
            export_repo_to_sqlite(self.repo, conn)
            issues = run_validation_queries(conn)
            self.issues.extend(issues)
        except sqlite3.Error as exc:
            # Per failure contract §6: fail-closed refusal, never a fabricated Issue
            raise RuntimeError(f"Reference validation database failed: {exc}") from exc
        finally:
            conn.close()

    def check_solution_exposure(self, routes_by_id: dict) -> None:
        """Compatibility hook; solution exposure is evaluated inside check_references via SQL."""
        pass

    def check_links(self):
        for f, text in self._canonical_texts():
            if f.suffix != ".md":
                continue
            for target in markdown_link_targets(text):
                self._check_link(target, f)

    def _check_link(self, target: str, source_file: Path):
        where = self._rel(source_file)
        classified = classify_markdown_link(target)
        if classified.kind == "skip":
            return
        if classified.kind == "uri":
            if target.startswith("github://"):
                return
            self._check_uri(target, where)
            return
        resolved = (source_file.parent / classified.target).resolve()
        try:
            resolved.relative_to(self.repo.root.resolve())
        except ValueError:
            self.err(
                "LINK-ESCAPE",
                f"internal link escapes the repository: '{target}'",
                where,
            )
            return
        if not resolved.exists():
            self.err("LINK-BROKEN", f"internal link does not resolve: '{target}'", where)

    def _check_uri(self, ref: str, where: str):
        r = self.repo
        parsed = parse_reference_uri(ref)
        if parsed is None:
            return
        if parsed.scheme == "note":
            if parsed.target not in r.notes:
                self.err("URI-NOTE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "concept":
            if parsed.target not in r.concepts:
                self.err("URI-CONCEPT", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "source":
            if parsed.target not in r.sources:
                self.err("URI-SOURCE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "workspace":
            wid = parsed.target
            if wid not in r.workspaces and wid not in r.quarantined_workspace_ids:
                self.err("URI-WORKSPACE", f"'{ref}' does not resolve", where)
        elif parsed.scheme == "material":
            if (r.learningos_root / "materials").is_dir():
                if not (r.materials_root / parsed.target).exists():
                    self.warn("URI-MATERIAL",
                              f"'{ref}' does not resolve on disk", where)
        elif parsed.scheme == "project":
            if not (r.projects_root / parsed.target).exists():
                self.warn("URI-PROJECT", f"'{ref}' does not resolve on disk", where)
