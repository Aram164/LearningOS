"""Registry records, collections and ownership."""

from __future__ import annotations

import re

from ..loader import PREREQUISITE_RELATIONS, RELATION_TYPES
from .common import (
    CANONICAL_TREES,
    COORDINATION_SECTIONS,
    ISO_DATE_RE,
    JUDGMENT_HEADERS,
    _in_garden,
    _in_quarantine,
)


class ChecksRegistries:
    """Mixed into Validator; see rules/core.py."""
    def check_registries(self):
        r = self.repo
        seen_edges = set()
        for i, rel in enumerate(r.relations):
            rtype = rel.get("type")
            if rtype not in RELATION_TYPES:
                self.err("REL-TYPE", f"relation[{i}] type '{rtype}' is not one of the eight supported types",
                         "knowledge/concept-relations.yaml")
            edge = (rel.get("from"), rtype, rel.get("to"))
            if edge in seen_edges:
                self.err("REL-DUP", f"duplicate relation edge {edge}", "knowledge/concept-relations.yaml")
            seen_edges.add(edge)
        self._prerequisite_cycle()
        # Alias collisions. Normalize with strip().casefold() so that stray
        # whitespace or case ('Erwartungswert', ' erwartungswert ') still
        # collides; empty keys are ignored rather than colliding vacuously.
        alias_map: dict[str, list[str]] = {}
        for concept in r.concepts.values():
            cid = str(concept.get("id"))
            for alias in concept.get("aliases", []) or []:
                key = str(alias).strip().casefold()
                if key:
                    alias_map.setdefault(key, []).append(cid)
            label = str(concept.get("label", "")).strip().casefold()
            if label:
                alias_map.setdefault(label, []).append(cid)
        for key, owners in sorted(alias_map.items()):
            distinct = sorted(set(owners))
            if len(distinct) > 1:
                located = ", ".join(f"{oid} ({self._origin_for('concept', oid)})"
                                    for oid in distinct)
                self.warn("ALIAS-COLLISION",
                          f"alias/label '{key}' maps to multiple concepts: {located}")
        # Duplicate sources
        seen_ident: dict[tuple, str] = {}
        seen_url: dict[str, str] = {}
        for source in r.sources.values():
            sid = str(source.get("id"))
            key = (str(source.get("title", "")).casefold(),
                   tuple(a.casefold() for a in source.get("authors", []) or []))
            if key in seen_ident and key[0]:
                self.warn("SOURCE-DUP", f"sources '{seen_ident[key]}' and '{sid}' share title+authors")
            seen_ident.setdefault(key, sid)
            url = source.get("url")
            if url:
                if url in seen_url:
                    self.warn("SOURCE-DUP", f"sources '{seen_url[url]}' and '{sid}' share URL {url}")
                seen_url.setdefault(url, sid)

    def _prerequisite_cycle(self):
        """No cycle among `requires` / `builds-on` (ADR-016 decision 4).

        Only the strict subgraph defines learning order, so only the strict
        subgraph has to be acyclic. Semantic relations may cycle freely — two
        concepts can motivate each other without either coming first.

        The report is deterministic on purpose. Concepts are walked in sorted
        order and neighbours in sorted order, and the first cycle found is the
        one reported, so the same repository always yields the same message. A
        cycle error that names a different path on each run is one nobody can
        act on, and reporting every cycle would bury the shortest.

        Runs after `check_references`, which resolves endpoints: a cycle walk
        over an unresolvable `to` reports nonsense.
        """
        r = self.repo
        prereqs: dict[str, set[str]] = {}
        for rel in r.relations:
            if str(rel.get("type")) not in PREREQUISITE_RELATIONS:
                continue
            frm, to = str(rel.get("from", "")), str(rel.get("to", ""))
            if frm in r.concepts and to in r.concepts:
                prereqs.setdefault(frm, set()).add(to)

        WHITE, GREY, BLACK = 0, 1, 2
        colour: dict[str, int] = {}

        def walk(node: str, stack: list[str]) -> list[str] | None:
            colour[node] = GREY
            stack.append(node)
            for nxt in sorted(prereqs.get(node, ())):
                state = colour.get(nxt, WHITE)
                if state == GREY:
                    return stack[stack.index(nxt):] + [nxt]
                if state == WHITE:
                    found = walk(nxt, stack)
                    if found:
                        return found
            stack.pop()
            colour[node] = BLACK
            return None

        for start in sorted(prereqs):
            if colour.get(start, WHITE) != WHITE:
                continue
            cycle = walk(start, [])
            if cycle:
                self.err(
                    "REL-PREREQ-CYCLE",
                    "prerequisite cycle: " + " -> ".join(cycle),
                    "knowledge/concept-relations.yaml",
                )
                return

    def check_collections(self):
        """Collections (sources/collections/*.yaml) are curated lists OVER the
        registry: filename kebab-case, every entry resolves, no duplicates."""
        name_re = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        for name, doc in self.repo.collections.items():
            where = f"sources/collections/{name}.yaml"
            for gid in doc.get("thematic_group_ids", []) or []:
                if gid not in self.repo.thematic_groups:
                    self.err(
                        "REF-THEMATIC-GROUP",
                        f"collection '{name}' references unknown thematic group '{gid}'",
                        where,
                    )
            if not name_re.match(name):
                self.err("COLLECTION-NAME",
                         f"collection filename '{name}' is not kebab-case", where)
            seen: set[str] = set()
            for i, entry in enumerate(doc.get("entries", []) or []):
                if not isinstance(entry, dict):
                    continue  # schema check reports the shape error
                sid = str(entry.get("source", ""))
                if sid and sid not in self.repo.sources:
                    self.err("COLLECTION-REF",
                             f"entries[{i}] references unknown source '{sid}'", where)
                if sid in seen:
                    self.warn("COLLECTION-DUP",
                              f"source '{sid}' listed more than once", where)
                seen.add(sid)

    def check_ownership(self):
        r = self.repo
        # No canonical file references generated/ as input
        for tree in CANONICAL_TREES:
            base = r.root / tree
            if not base.is_dir():
                continue
            for f in sorted(base.rglob("*")):
                if f.suffix.lower() not in (".md", ".yaml", ".yml") or not f.is_file():
                    continue
                if _in_garden(r.root, f) or _in_quarantine(r.root, f):
                    continue
                text = f.read_text(encoding="utf-8", errors="replace")
                # Only the repository's own generated/ tree counts — 'generated/'
                # inside URLs or longer paths (e.g. sklearn.org/modules/generated/)
                # must not be preceded by a slash or word character.
                if re.search(r"(?<![\w/])generated/", text):
                    self.err("GEN-INPUT",
                             "canonical file references 'generated/' — generated files are never inputs",
                             self._rel(f))
        # No file under generated/ tracked by git (except .gitkeep)
        tracked = self._git(["ls-files", "generated/"])
        for line in tracked.splitlines():
            if line.strip() and not line.strip().endswith(".gitkeep"):
                self.err("GEN-TRACKED", f"file under generated/ is tracked by Git: {line.strip()}")
        # COORDINATION: no exam-date duplication, no status restatements, only allowed sections
        if r.coordination is not None:
            attempt_dates = set()
            for module in r.modules.values():
                for att in module.get("attempts", []) or []:
                    if att.get("date"):
                        attempt_dates.add(str(att["date"]))
            body = r.coordination.body
            for date in ISO_DATE_RE.findall(body):
                if date in attempt_dates:
                    self.err("COORD-EXAM-DATE",
                             f"COORDINATION.md contains ISO date {date} equal to a modules.yaml "
                             "attempt date (exam dates are owned by records/modules.yaml)",
                             "work/COORDINATION.md")
            if re.search(r"^\s*status\s*:", body, re.MULTILINE | re.IGNORECASE):
                self.err("COORD-STATUS",
                         "COORDINATION.md restates workspace status (owned by workspace frontmatter)",
                         "work/COORDINATION.md")
            headings = re.findall(r"^##\s+(.+?)\s*$", body, re.MULTILINE)
            for h in headings:
                if h not in COORDINATION_SECTIONS:
                    self.err("COORD-SECTION",
                             f"COORDINATION.md contains unexpected section '{h}' "
                             f"(allowed: {', '.join(COORDINATION_SECTIONS)})",
                             "work/COORDINATION.md")
        # Crosswalk judgment-table heuristic (warning)
        for note in r.notes.values():
            if note.meta.get("role") != "crosswalk":
                continue
            for line in note.body.splitlines():
                if not line.lstrip().startswith("|"):
                    continue
                cells = {c.strip().casefold() for c in line.strip().strip("|").split("|")}
                if cells & JUDGMENT_HEADERS:
                    self.warn("CROSSWALK-TABLE",
                              f"crosswalk note '{note.id}' contains a Markdown table with evaluation "
                              "vocabulary headers — judgments belong in source records",
                              self._rel(note.path))
                    break
