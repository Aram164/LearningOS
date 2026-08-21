"""Source index and collection views."""

from __future__ import annotations

from ..loader import Repo
from .common import LECTURE_KEY_RE, SELECTOR_ROLES, _letter_toc, _md_header
from .concepts import _eval_line, _evals_for_concept


def _lecture_entries(repo: Repo) -> list[tuple[str, str, str, dict]]:
    """(lecture_label, source_id, section_note, evaluation) for lecture-series sources.

    A lecture entry is any evaluation on a type=lecture source whose
    useful_sections carry a lecture-shaped key (e.g. 'L05 — Logistic Regression').
    """
    entries = []
    for sid in sorted(repo.sources):
        source = repo.sources[sid]
        if source.get("type") != "lecture":
            continue
        for ev in source.get("evaluations", []) or []:
            for section in ev.get("useful_sections", []) or []:
                for key, desc in sorted(section.items()):
                    if LECTURE_KEY_RE.match(key):
                        entries.append((key, sid, desc, ev))
    entries.sort(key=lambda e: (e[1], e[0]))
    return entries


def build_collection_view(repo: Repo, name: str, doc: dict, generated_at: str) -> str:
    """Render one curated collection (sources/collections/<name>.yaml) as a
    readable list, grouped by first appearance of `group`."""
    lines = _md_header(doc.get("title", name), generated_at)
    if doc.get("description"):
        lines.append(str(doc["description"]).strip())
        lines.append("")
    current_group = object()  # sentinel: first entry always opens its section
    for entry in doc.get("entries", []) or []:
        if not isinstance(entry, dict):
            continue
        group = entry.get("group")
        if group != current_group:
            current_group = group
            if group:
                lines.append(f"## {group}")
                lines.append("")
        sid = str(entry.get("source", ""))
        s = repo.sources.get(sid, {})
        title = s.get("title", sid)
        url = s.get("url")
        head = f"**[{title}]({url})**" if url else f"**{title}**"
        ident = [s.get("type", ""),
                 ", ".join(s.get("authors", []) or []) or s.get("organization", ""),
                 str(s.get("year", "") or "")]
        ident_str = " · ".join(x for x in ident if x)
        lines.append(f"- {head}" + (f" ({ident_str})" if ident_str else "") + f" — `{sid}`")
        if entry.get("why"):
            lines.append(f"  - {entry['why']}")
        if s.get("material"):
            lines.append(f"  - local: `{s['material']}`")
        for key, val in (s.get("identifiers") or {}).items():
            lines.append(f"  - {key}: {val}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"Canonical input: `sources/collections/{name}.yaml` — source judgments "
                 "live in the source records (see source-index.md), not here.")
    return "\n".join(lines)


def build_source_index(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Source index", generated_at)

    if repo.collections:
        lines.append("## Collections (curated lists)")
        lines.append("")
        for name in sorted(repo.collections):
            doc = repo.collections[name]
            n = len(doc.get("entries", []) or [])
            lines.append(f"- [{doc.get('title', name)}](collections/{name}.md) — "
                         f"{n} entries (`sources/collections/{name}.yaml`)")
        lines.append("")

    lines.append("## Registry")
    lines.append("")
    toc_entries = sorted(
        ((str(repo.sources[sid].get("title", sid)), str(repo.sources[sid].get("title", sid)))
         for sid in repo.sources),
        key=lambda e: e[0].lower())
    lines.extend(_letter_toc(toc_entries))
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        lines.append(f"### {s.get('title', sid)}")
        lines.append("")
        ident = [f"`{sid}`", s.get("type", "")]
        if s.get("authors"):
            ident.append(", ".join(s["authors"]))
        if s.get("organization"):
            ident.append(s["organization"])
        if s.get("year"):
            ident.append(str(s["year"]))
        lines.append(" · ".join(str(x) for x in ident if x))
        loc = s.get("material") or s.get("url")
        if loc:
            lines.append("")
            lines.append(f"Location: `{loc}`")
        for ev in s.get("evaluations", []) or []:
            lines.append("")
            scope = ", ".join(f"`{c}`" for c in ev.get("concepts", []) or []) or "global"
            lines.append(f"- **Evaluation** ({scope})")
            if ev.get("roles"):
                lines.append(f"  - roles: {', '.join(ev['roles'])}")
            if ev.get("level"):
                lines.append(f"  - level: {ev['level']}")
            if ev.get("audience"):
                lines.append(f"  - audience: {', '.join(ev['audience'])}")
            if ev.get("prerequisites"):
                lines.append(f"  - prerequisites: {', '.join(ev['prerequisites'])}")
            for st in ev.get("strengths", []) or []:
                lines.append(f"  - strength: {st}")
            for wk in ev.get("weaknesses", []) or []:
                lines.append(f"  - weakness: {wk}")
            for section in ev.get("useful_sections", []) or []:
                for key, desc in sorted(section.items()):
                    lines.append(f"  - section — {key}: {desc}")
        lines.append("")

    # ---------------------------------------------------- per-lecture selector
    lines.append("---")
    lines.append("")
    lines.append("## Selector view — per lecture")
    lines.append("")
    lines.append("For each lecture of a registered lecture-series source: its concepts, and "
                 "for each concept the recommended sources for first learning / review / "
                 "implementation (from contextual source evaluations).")
    lines.append("")
    for key, sid, desc, ev in _lecture_entries(repo):
        lines.append(f"### {sid} — {key}")
        lines.append("")
        if desc:
            lines.append(f"*{desc}*")
            lines.append("")
        concepts = sorted(ev.get("concepts", []) or [])
        if not concepts:
            lines.append("(no concepts registered for this lecture)")
            lines.append("")
            continue
        for cid in concepts:
            label = repo.concepts.get(cid, {}).get("label", cid)
            lines.append(f"**{label}** (`{cid}`)")
            lines.append("")
            evals = [(s, src, e) for (s, src, e) in _evals_for_concept(repo, cid) if s != sid]
            self_evals = [(s, src, e) for (s, src, e) in _evals_for_concept(repo, cid) if s == sid]
            for role in SELECTOR_ROLES:
                picks = [(s, src, e) for (s, src, e) in evals if role in (e.get("roles") or [])]
                if picks:
                    lines.append(f"- *{role}:* " + " · ".join(_eval_line(s, src, e)
                                                              for s, src, e in picks))
            other = [(s, src, e) for (s, src, e) in evals
                     if not set(e.get("roles") or []) & set(SELECTOR_ROLES)]
            for s, src, e in other:
                roles = ", ".join(e.get("roles") or ["unspecified"])
                lines.append(f"- *{roles}:* {_eval_line(s, src, e)}")
            for s, src, e in self_evals:
                lines.append(f"- *lecture:* {_eval_line(s, src, e)}")
            note_ids = sorted(n.id for n in repo.notes.values()
                              if cid in (n.meta.get("concepts") or []))
            if note_ids:
                lines.append("- *notes:* " + " · ".join(f"`{n}`" for n in note_ids))
            lines.append("")
        lines.append("")

    # ---------------------------------------------------- per-concept selector
    lines.append("---")
    lines.append("")
    lines.append("## Selector view — per concept")
    lines.append("")
    for cid in sorted(repo.concepts):
        evals = _evals_for_concept(repo, cid)
        if not evals:
            continue
        label = repo.concepts.get(cid, {}).get("label", cid)
        lines.append(f"### {label} (`{cid}`)")
        lines.append("")
        for role, heading in (("first-learning", "Best for first learning"),
                              ("review", "Best for review"),
                              ("implementation", "Best for implementation")):
            picks = [(s, src, e) for (s, src, e) in evals if role in (e.get("roles") or [])]
            if picks:
                lines.append(f"**{heading}:**")
                lines.append("")
                for s, src, e in picks:
                    lines.append(f"- {_eval_line(s, src, e)}")
                lines.append("")
        other = [(s, src, e) for (s, src, e) in evals
                 if not set(e.get("roles") or []) & set(SELECTOR_ROLES)]
        if other:
            lines.append("**Other contexts:**")
            lines.append("")
            for s, src, e in other:
                roles = ", ".join(e.get("roles") or ["unspecified"])
                lines.append(f"- ({roles}) {_eval_line(s, src, e)}")
            lines.append("")
    return "\n".join(lines)
