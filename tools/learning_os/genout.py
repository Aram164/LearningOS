"""Deterministic generation of all derived outputs (BUILD-SPEC Step 5).

Outputs (all under generated/, gitignored, rebuildable, never canonical):
  manifest.json, concept-index.md, source-index.md (incl. per-lecture and
  per-concept selector views), module-view.md, coordination-view.md,
  backlinks.json, nebula.md (the Garden index — §14), reports/health.md.

Fully deterministic for a given committed tree: all collections sorted by ID;
Git-derived neglect signals depend only on repository state; the generation
timestamp is the last-commit timestamp, so regeneration without new commits
is byte-for-byte reproducible.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath

from . import __version__
from .loader import Repo

LECTURE_KEY_RE = re.compile(r"^(?:VL\s*)?L?\d{1,2}\b")

SELECTOR_ROLES = ("first-learning", "review", "implementation")


def mermaid_node_ids(ids) -> dict[str, str]:
    """Map concept IDs to unique, Mermaid-safe node identifiers.

    Sanitizing an ID to Mermaid's allowed character set can map distinct IDs to
    the same token (e.g. 'concept-a-b' and 'concept-a.b' both collapse to
    'concept_a_b'). Emitting two nodes with an identical identifier silently
    merges them in the rendered graph. Assigning a disambiguating suffix on
    collision guarantees every input ID gets its own node. Deterministic:
    inputs are processed in sorted order.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for cid in sorted(ids):
        base = re.sub(r"[^0-9A-Za-z_]", "_", cid)
        if not base or not (base[0].isalpha() or base[0] == "_"):
            base = "n_" + base
        name = base
        i = 2
        while name in used:
            name = f"{base}__{i}"
            i += 1
        used.add(name)
        mapping[cid] = name
    return mapping


def _md_header(title: str, generated_at: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "> ⚠️ GENERATED file — a disposable VIEW over the canonical records, not "
        "part of the canonical architecture. Never edit; edit canonical inputs "
        f"instead. Rebuilt by `python tools/generate.py` (learning_os v{__version__}) "
        "from: knowledge/, sources/, records/, work/.",
        f"> Generated: {generated_at}",
        "",
    ]


def _json_header(generated_at: str) -> dict:
    return {
        "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py",
        "generator": f"learning_os v{__version__}",
        "generated_at": generated_at,
    }


def _slug(heading: str) -> str:
    """GitHub-style anchor for a Markdown heading."""
    s = heading.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in " -")
    return s.replace(" ", "-")


def _letter_toc(entries: list[tuple[str, str]]) -> list[str]:
    """Compact letter-grouped table of contents.

    entries: (display text, heading text used for the anchor), pre-sorted.
    Returns one line per starting letter: 'A: [x](#x) · [y](#y)'.
    """
    lines: list[str] = []
    by_letter: dict[str, list[str]] = {}
    for display, heading in entries:
        letter = display[:1].upper() if display else "#"
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append(f"[{display}](#{_slug(heading)})")
    for letter in sorted(by_letter):
        lines.append(f"**{letter}:** " + " · ".join(by_letter[letter]))
        lines.append("")
    return lines


def _git_last_commit(root: Path, rel: str) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                             cwd=root, capture_output=True, text=True, timeout=30)
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def stable_generated_at(root: Path) -> str:
    """Reproducible generation timestamp: the repository's last-commit time.

    Regenerating without new commits yields byte-for-byte identical output
    (improvement: no wall-clock noise in generated files). Falls back to a
    fixed marker when Git is unavailable (e.g. synthetic test repos).
    """
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI"],
                             cwd=root, capture_output=True, text=True, timeout=30)
        ts = out.stdout.strip()
        if out.returncode == 0 and ts:
            return f"{ts} (last commit)"
    except Exception:  # noqa: BLE001
        pass
    return "(no Git history available)"


# --------------------------------------------------------------------- build
def build_manifest(repo: Repo, generated_at: str) -> dict:
    """The COMPLETE machine-readable projection of the repository (ADR-001):
    every canonical record (notes incl. attachments/evidence/contexts, concepts,
    sources, modules incl. attempts, workspaces, coordination) plus all
    relations. A consumer needing repository state should read this file, not
    parse the tree."""
    records = []
    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        records.append({
            "id": note.id, "type": "note",
            "title": note.meta.get("title", ""),
            "path": str(note.path.relative_to(repo.root)),
            "role": note.meta.get("role", "synthesis"),
            "state": note.meta.get("state"),
            "authorship": note.meta.get("authorship"),
            "concepts": sorted(note.meta.get("concepts", []) or []),
            "sources": sorted(note.meta.get("sources", []) or []),
            "contexts": sorted(note.meta.get("contexts", []) or []),
            "attachments": list(note.meta.get("attachments", []) or []),
            "evidence": list(note.meta.get("evidence", []) or []),
            "supersedes": sorted(note.meta.get("supersedes", []) or []),
            "reviewed": note.meta.get("reviewed"),
        })
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        records.append({
            "id": cid, "type": "concept", "title": c.get("label", ""),
            "path": str(repo.concept_origins.get(cid, "").relative_to(repo.root))
            if repo.concept_origins.get(cid) else "knowledge/concepts.yaml",
            "aliases": sorted(c.get("aliases", []) or []),
            "deprecated": bool(c.get("deprecated", False)),
        })
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        records.append({
            "id": sid, "type": "source", "title": s.get("title", ""),
            "path": str(repo.source_origins.get(sid, "").relative_to(repo.root))
            if repo.source_origins.get(sid) else "sources/sources.yaml",
            "source_type": s.get("type", ""),
        })
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        records.append({
            "id": mid, "type": "module", "title": m.get("title", ""),
            "path": "records/modules.yaml", "status": m.get("status", ""),
            "institution": m.get("institution"), "code": m.get("code"),
            "credits": m.get("credits"), "semester": m.get("semester"),
            "components": list(m.get("components", []) or []),
            "examination": m.get("examination"),
            "attempts": list(m.get("attempts", []) or []),
            "grade": m.get("grade"),
        })
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        records.append({
            "id": name, "type": "collection",
            "title": doc.get("title", name),
            "path": f"sources/collections/{name}.yaml",
            "sources": [str(e.get("source", "")) for e in doc.get("entries", []) or []
                        if isinstance(e, dict)],
        })
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        records.append({
            "id": ws.id, "type": "workspace", "title": ws.meta.get("title", ""),
            "path": str(ws.path.relative_to(repo.root)),
            "status": ws.status, "standing": ws.standing, "archived": ws.archived,
            "deadline": ws.meta.get("deadline"),
            "concepts": sorted(ws.meta.get("concepts", []) or []),
            "notes": sorted(ws.meta.get("notes", []) or []),
            "sources": sorted(ws.meta.get("sources", []) or []),
        })
    if repo.coordination is not None:
        records.append({
            "id": "coordination", "type": "coordination",
            "path": "work/COORDINATION.md",
            "sections": {h: (repo.coordination.section(h) or "")
                         for h in ("Commitments", "Priorities", "Dependencies", "Deferrals")},
        })
    relations = [
        {"from": r.get("from"), "type": r.get("type"), "to": r.get("to"),
         "context": r.get("context"), "source": r.get("source")}
        for r in sorted(repo.relations,
                        key=lambda r: (str(r.get("from")), str(r.get("type")), str(r.get("to"))))
    ]
    return {
        "_generated": _json_header(generated_at),
        "records": records,
        "relations": relations,
        "counts": {
            "notes": len(repo.notes), "concepts": len(repo.concepts),
            "sources": len(repo.sources), "collections": len(repo.collections),
            "modules": len(repo.modules),
            "workspaces_active": len(repo.active_workspaces()),
            "workspaces_archived": len(repo.archived_workspaces()),
            "relations": len(repo.relations),
        },
    }


def build_backlinks(repo: Repo, generated_at: str) -> dict:
    concept_to_notes: dict[str, list] = {}
    source_to_notes: dict[str, list] = {}
    note_incoming: dict[str, list] = {}
    workspace_to_notes: dict[str, list] = {}
    concept_relations: dict[str, dict] = {}
    module_to_workspaces: dict[str, list] = {}

    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        for cid in note.meta.get("concepts", []) or []:
            concept_to_notes.setdefault(cid, []).append(note.id)
        for sid in note.meta.get("sources", []) or []:
            source_to_notes.setdefault(sid, []).append(note.id)
        for wid in note.meta.get("contexts", []) or []:
            workspace_to_notes.setdefault(wid, []).append(note.id)
        for target in note.meta.get("supersedes", []) or []:
            note_incoming.setdefault(target, []).append(
                {"from": note.id, "kind": "superseded-by"})
        for m in re.finditer(r"note://(note-[a-z0-9-]+)", note.body):
            if m.group(1) != note.id:
                note_incoming.setdefault(m.group(1), []).append(
                    {"from": note.id, "kind": "mentions"})
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        for nid in ws.meta.get("notes", []) or []:
            lst = workspace_to_notes.setdefault(ws.id, [])
            if nid not in lst:
                lst.append(nid)
        for m in re.finditer(r"\bmodule-[a-z0-9]+(?:-[a-z0-9]+)*\b", ws.body):
            lst = module_to_workspaces.setdefault(m.group(0), [])
            if ws.id not in lst:
                lst.append(ws.id)
    for rel in repo.relations:
        frm, to, rtype = rel.get("from"), rel.get("to"), rel.get("type")
        concept_relations.setdefault(frm, {"outgoing": [], "incoming": []})
        concept_relations.setdefault(to, {"outgoing": [], "incoming": []})
        concept_relations[frm]["outgoing"].append({"type": rtype, "to": to})
        concept_relations[to]["incoming"].append({"type": rtype, "from": frm})
    for d in concept_relations.values():
        d["outgoing"].sort(key=lambda e: (e["type"], e["to"]))
        d["incoming"].sort(key=lambda e: (e["type"], e["from"]))
    for m in (concept_to_notes, source_to_notes, workspace_to_notes, module_to_workspaces):
        for k in m:
            m[k] = sorted(set(m[k])) if all(isinstance(x, str) for x in m[k]) else m[k]
    return {
        "_generated": _json_header(generated_at),
        "concept_to_notes": dict(sorted(concept_to_notes.items())),
        "source_to_notes": dict(sorted(source_to_notes.items())),
        "note_incoming": dict(sorted(note_incoming.items())),
        "workspace_to_notes": dict(sorted(workspace_to_notes.items())),
        "concept_relations": dict(sorted(concept_relations.items())),
        "module_to_workspaces": dict(sorted(module_to_workspaces.items())),
    }


def _evals_for_concept(repo: Repo, cid: str) -> list[tuple[str, dict, dict]]:
    """(source_id, source, evaluation) pairs whose evaluation targets cid."""
    out = []
    for sid in sorted(repo.sources):
        source = repo.sources[sid]
        for ev in source.get("evaluations", []) or []:
            if cid in (ev.get("concepts") or []):
                out.append((sid, source, ev))
    return out


def _eval_line(sid: str, source: dict, ev: dict) -> str:
    bits = []
    if ev.get("roles"):
        bits.append("roles: " + ", ".join(ev["roles"]))
    if ev.get("level"):
        bits.append(f"level: {ev['level']}")
    if ev.get("strengths"):
        bits.append(ev["strengths"][0])
    detail = " — ".join(bits)
    return f"**{source.get('title', sid)}** (`{sid}`)" + (f" — {detail}" if detail else "")


def build_concept_index(repo: Repo, backlinks: dict, generated_at: str) -> str:
    lines = _md_header("Concept index", generated_at)
    toc_entries = []
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        heading = label + (" *(deprecated)*" if c.get("deprecated") else "")
        toc_entries.append((label, heading))
    toc_entries.sort(key=lambda e: e[0].lower())
    lines.append("## Contents")
    lines.append("")
    lines.extend(_letter_toc(toc_entries))
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        dep = " *(deprecated)*" if c.get("deprecated") else ""
        lines.append(f"## {label}{dep}")
        lines.append("")
        lines.append(f"`{cid}`")
        if c.get("aliases"):
            lines.append("")
            lines.append("Aliases: " + " · ".join(sorted(c["aliases"])))
        if c.get("description"):
            lines.append("")
            lines.append(f"*{c['description']}*")
        if c.get("replaced_by"):
            lines.append("")
            lines.append(f"Replaced by: `{c['replaced_by']}`")
        note_ids = backlinks["concept_to_notes"].get(cid, [])
        if note_ids:
            lines.append("")
            lines.append("**Notes:**")
            lines.append("")
            for nid in note_ids:
                note = repo.notes.get(nid)
                role = note.meta.get("role", "synthesis") if note else "?"
                title = note.meta.get("title", nid) if note else nid
                lines.append(f"- `{nid}` — {title} *(role: {role})*")
        rels = backlinks["concept_relations"].get(cid)
        if rels and (rels["outgoing"] or rels["incoming"]):
            lines.append("")
            lines.append("**Related concepts:**")
            lines.append("")
            for e in rels["outgoing"]:
                lines.append(f"- {e['type']} → `{e['to']}`")
            for e in rels["incoming"]:
                lines.append(f"- ← {e['type']} from `{e['from']}`")
        evals = _evals_for_concept(repo, cid)
        if evals:
            lines.append("")
            lines.append("**Contextual sources:**")
            lines.append("")
            for sid, source, ev in evals:
                lines.append(f"- {_eval_line(sid, source, ev)}")
        lines.append("")
    return "\n".join(lines)


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


def _exam_spine(repo: Repo) -> list[tuple[str, str, dict, dict]]:
    """(date, module_id, module, attempt) for attempts with result=registered."""
    spine = []
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        for att in module.get("attempts", []) or []:
            if att.get("result") == "registered" and att.get("date"):
                spine.append((str(att["date"]), mid, module, att))
    spine.sort()
    return spine


def _exam_spine_lines(repo: Repo) -> list[str]:
    lines = []
    spine = _exam_spine(repo)
    if spine:
        lines.append("| Date | Module | Termin | Notes |")
        lines.append("|---|---|---|---|")
        for date, mid, module, att in spine:
            lines.append(f"| {date} | {module.get('title', mid)} (`{mid}`) "
                         f"| {att.get('termin', '')} | {att.get('notes', '')} |")
    else:
        lines.append("(no registered attempts in records/modules.yaml)")
    # Enrolled modules with no registered attempt: surface the sitting facts
    # recorded in examination.notes so upcoming decisions stay visible.
    pending = []
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        if module.get("status") != "enrolled":
            continue
        attempts = module.get("attempts", []) or []
        if any(a.get("result") == "registered" for a in attempts):
            continue
        note = (module.get("examination") or {}).get("notes", "")
        pending.append((mid, module, " ".join(str(note).split())))
    if pending:
        lines.append("")
        lines.append("**Enrolled, no registered attempt yet** "
                     "(sitting facts from records/modules.yaml examination notes):")
        lines.append("")
        for mid, module, note in pending:
            lines.append(f"- **{module.get('title', mid)}** (`{mid}`)"
                         + (f" — {note}" if note else ""))
    return lines


def build_module_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Module view", generated_at)
    lines.append("## Upcoming exam spine (registered attempts, sorted by date)")
    lines.append("")
    lines.extend(_exam_spine_lines(repo))
    lines.append("")
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        lines.append(f"## {m.get('title', mid)}")
        lines.append("")
        ident = [f"`{mid}`", m.get("institution", ""), m.get("code", "")]
        lines.append(" · ".join(str(x) for x in ident if x))
        lines.append("")
        facts = []
        if m.get("credits") is not None:
            facts.append(f"credits: {m['credits']}")
        if m.get("semester"):
            facts.append(f"semester: {m['semester']}")
        facts.append(f"status: {m.get('status', '')}")
        if m.get("examination"):
            ex = m["examination"]
            facts.append(f"examination: {ex.get('type', '')}"
                         + (f" ({ex.get('notes')})" if ex.get("notes") else ""))
        if m.get("grade") is not None:
            facts.append(f"final grade: {m['grade']}")
        lines.append(" · ".join(facts))
        if m.get("components"):
            lines.append("")
            lines.append("Components (one grade): " + " + ".join(m["components"]))
        attempts = m.get("attempts", []) or []
        if attempts:
            lines.append("")
            lines.append("| # | Termin | Date | Result | Grade | Notes |")
            lines.append("|---|---|---|---|---|---|")
            for i, att in enumerate(attempts, 1):
                lines.append(f"| {i} | {att.get('termin', '')} | {att.get('date', '')} "
                             f"| {att.get('result', '')} | {att.get('grade', '')} "
                             f"| {att.get('notes', '')} |")
        lines.append("")
    return "\n".join(lines)


def _first_para(text: str | None) -> str:
    if not text:
        return ""
    for block in text.split("\n\n"):
        block = " ".join(block.split())
        if block:
            return block
    return ""


def build_coordination_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Coordination view", generated_at)
    lines.append("*Assembled from: the exam spine in records/modules.yaml, workspace "
                 "frontmatter, the facts in work/COORDINATION.md, and Git-derived "
                 "neglect signals. Disposable — rebuild anytime.*")
    lines.append("")

    lines.append("## Exam spine")
    lines.append("")
    lines.extend(_exam_spine_lines(repo))
    lines.append("")

    lines.append("## Active workspaces")
    lines.append("")
    active = sorted(repo.active_workspaces(), key=lambda w: w.id)
    if active:
        lines.append("| Workspace | Status | Standing | Deadline | Next action |")
        lines.append("|---|---|---|---|---|")
        for ws in active:
            na = _first_para(ws.section("Next Action"))
            deadline = ws.meta.get("deadline", "") or ""
            lines.append(f"| `{ws.id}` — {ws.meta.get('title', '')} | {ws.status} "
                         f"| {'yes' if ws.standing else ''} | {deadline} | {na} |")
    else:
        lines.append("(no active workspaces)")
    lines.append("")

    lines.append("## Coordination facts (work/COORDINATION.md)")
    lines.append("")
    if repo.coordination is not None:
        for heading in ("Commitments", "Priorities", "Dependencies", "Deferrals"):
            body = repo.coordination.section(heading)
            lines.append(f"### {heading}")
            lines.append("")
            lines.append(body if body else "(none)")
            lines.append("")
    else:
        lines.append("(work/COORDINATION.md missing)")
        lines.append("")

    lines.append("## Materials queues (pending human decisions)")
    lines.append("")
    queue_rows = []
    materials = repo.root.parent / "materials"
    for qname in ("_unsorted", "_duplicates-for-review"):
        qdir = materials / qname
        if qdir.is_dir():
            n = sum(1 for f in qdir.rglob("*")
                    if f.is_file() and f.name != ".DS_Store")
            if n:
                queue_rows.append(f"- `materials/{qname}/` — **{n} files** "
                                  "awaiting a register-or-discard decision")
    if queue_rows:
        lines.extend(queue_rows)
        lines.append("")
        lines.append("*Same failure mode as an unread inbox — these piles are "
                     "invisible unless surfaced. Register on first canonical "
                     "citation (WORKFLOWS §6a) or discard deliberately.*")
    else:
        lines.append("(empty — nothing awaits a decision)")
    lines.append("")

    lines.append("## Neglect signals (Git)")
    lines.append("")
    rows = []
    for ws in active:
        if ws.standing:
            continue
        rel = str(ws.path.parent.relative_to(repo.root))
        last = _git_last_commit(repo.root, rel)
        rows.append((ws.id, last))
    if rows:
        lines.append("| Workspace | Last commit touching it |")
        lines.append("|---|---|")
        for wid, last in rows:
            lines.append(f"| `{wid}` | {last or '(not yet committed)'} |")
        lines.append("")
        lines.append("*A workspace untouched for 21+ days is flagged by the validator "
                     "(WS-NEGLECT).*")
    else:
        lines.append("(no non-standing active workspaces)")
    lines.append("")
    return "\n".join(lines)


PREREQ_TYPES = ("requires", "builds-on")


def build_dependency_report(repo: Repo, backlinks: dict, generated_at: str) -> str:
    """Concept/module dependency view (ADR-001): direct + transitive
    prerequisites per concept, a layered study order over the prerequisite
    subgraph, and the module -> workspace -> concept graph."""
    prereqs: dict[str, set] = {}
    for rel in repo.relations:
        if rel.get("type") in PREREQ_TYPES:
            prereqs.setdefault(str(rel["from"]), set()).add(str(rel["to"]))

    def closure(cid: str) -> list[str]:
        seen, stack = set(), sorted(prereqs.get(cid, ()))
        while stack:
            c = stack.pop()
            if c in seen or c == cid:
                continue
            seen.add(c)
            stack.extend(sorted(prereqs.get(c, ())))
        return sorted(seen)

    lines = _md_header("Dependency report", generated_at)
    lines.append("*Prerequisite semantics = `requires` + `builds-on` edges from "
                 "the relation registry. `motivates`/`applies-in`/`contrasts-with` "
                 "edges are context, not prerequisites, and are excluded.*")
    lines.append("")

    lines.append("## Prerequisites per concept (direct → transitive)")
    lines.append("")
    for cid in sorted(repo.concepts):
        direct = sorted(prereqs.get(cid, ()))
        if not direct:
            continue
        label = repo.concepts[cid].get("label", cid)
        lines.append(f"- **{label}** (`{cid}`)")
        lines.append(f"  - direct: " + ", ".join(f"`{c}`" for c in direct))
        trans = [c for c in closure(cid) if c not in direct]
        if trans:
            lines.append(f"  - transitive: " + ", ".join(f"`{c}`" for c in trans))
    lines.append("")

    # Layered study order (Kahn levels over the prerequisite subgraph)
    lines.append("## Layered study order")
    lines.append("")
    lines.append("Concepts in the same layer are independent; every concept's "
                 "prerequisites live in earlier layers. Concepts with no "
                 "prerequisite edges in the registry are omitted unless someone "
                 "depends on them.")
    lines.append("")
    involved = set(prereqs)
    for deps in prereqs.values():
        involved |= deps
    remaining = dict((c, set(d for d in prereqs.get(c, ()) if d in involved))
                     for c in involved)
    layer_no = 0
    while remaining:
        ready = sorted(c for c, deps in remaining.items() if not deps)
        if not ready:  # cycle guard — report and stop
            lines.append(f"- ⚠️ cycle detected among: "
                         + ", ".join(f"`{c}`" for c in sorted(remaining)))
            break
        layer_no += 1
        labels = [f"`{c}`" for c in ready]
        lines.append(f"- **Layer {layer_no}:** " + " · ".join(labels))
        for c in ready:
            remaining.pop(c)
        for deps in remaining.values():
            deps.difference_update(ready)
    lines.append("")

    lines.append("## Modules → workspaces → concepts")
    lines.append("")
    m2w = backlinks.get("module_to_workspaces", {})
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        lines.append(f"- **{module.get('title', mid)}** (`{mid}`)")
        wids = m2w.get(mid, [])
        if not wids:
            lines.append("  - (no workspace references it)")
            continue
        for wid in wids:
            ws = repo.workspaces.get(wid)
            if ws is None:
                continue
            cids = sorted(ws.meta.get("concepts", []) or [])
            tail = (": " + ", ".join(f"`{c}`" for c in cids)) if cids else ""
            state = "archived" if ws.archived else ws.status
            lines.append(f"  - `{wid}` ({state}){tail}")
    lines.append("")
    return "\n".join(lines)


def build_concept_map(repo: Repo, generated_at: str) -> str:
    """Mermaid rendering of the prerequisite graph (requires + builds-on).

    Human-facing counterpart of the dependency report: GitHub and VS Code
    render the diagram natively. Context edges (motivates/applies-in/
    contrasts-with) are excluded, same as the dependency report.
    """
    lines = _md_header("Concept map (prerequisite graph)", generated_at)
    lines.append("*Arrows point from prerequisite to dependent — follow the "
                 "arrows to get a study order. Solid = `requires`, "
                 "dotted = `builds-on`. Textual version: "
                 "`dependency-report.md`.*")
    lines.append("")

    edges = sorted(
        (str(r["to"]), str(r["from"]), str(r["type"]))
        for r in repo.relations if r.get("type") in PREREQ_TYPES)
    if not edges:
        lines.append("(no prerequisite edges in the relation registry)")
        lines.append("")
        return "\n".join(lines)

    involved = sorted({c for e in edges for c in e[:2]})
    nodes = mermaid_node_ids(involved)
    lines.append("```mermaid")
    lines.append("graph LR")
    for cid in involved:
        label = str(repo.concepts.get(cid, {}).get("label", cid)).replace('"', "'")
        lines.append(f'    {nodes[cid]}["{label}"]')
    for pre, dep, rtype in edges:
        arrow = "-->" if rtype == "requires" else "-.->"
        lines.append(f"    {nodes[pre]} {arrow} {nodes[dep]}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def build_health(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Health report", generated_at)
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- notes: {len(repo.notes)}")
    by_role: dict[str, int] = {}
    for n in repo.notes.values():
        by_role[n.meta.get("role", "synthesis")] = by_role.get(n.meta.get("role", "synthesis"), 0) + 1
    for role in sorted(by_role):
        lines.append(f"  - {role}: {by_role[role]}")
    lines.append(f"- concepts: {len(repo.concepts)}")
    lines.append(f"- concept relations: {len(repo.relations)}")
    lines.append(f"- sources: {len(repo.sources)}")
    lines.append(f"- modules: {len(repo.modules)}")
    lines.append(f"- active workspaces: {len(repo.active_workspaces())} "
                 f"(standing: {sum(1 for w in repo.active_workspaces() if w.standing)})")
    lines.append(f"- archived workspaces: {len(repo.archived_workspaces())}")
    inbox = repo.root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir() if not f.name.startswith(".")]) if inbox.is_dir() else 0
    lines.append(f"- inbox items: {n_inbox}")
    lines.append("")
    lines.append("## Notes without concept links")
    lines.append("")
    orphans = [n.id for n in sorted(repo.notes.values(), key=lambda n: n.id)
               if not n.meta.get("concepts")]
    lines.extend(f"- `{nid}`" for nid in orphans) if orphans else lines.append("(none)")
    lines.append("")
    lines.append("## Concepts without notes")
    lines.append("")
    linked = {c for n in repo.notes.values() for c in (n.meta.get("concepts") or [])}
    unlinked = [c for c in sorted(repo.concepts) if c not in linked]
    lines.extend(f"- `{c}`" for c in unlinked) if unlinked else lines.append("(none)")
    lines.append("")
    lines.append("*Run `python tools/validate.py` for the full rule check.*")
    lines.append("")
    return "\n".join(lines)


def _garden_relpath(repo: Repo, note) -> str:
    """Markdown link from generated/nebula.md to a garden note (both local)."""
    return "../" + note.path.relative_to(repo.root).as_posix()


def build_nebula(repo: Repo, generated_at: str) -> str:
    """The Nebula: a disposable index of the Garden (CLAUDE.md §14).

    Every free-form note in knowledge/garden/, grouped by inline #tag and
    annotated with a harvest-pressure signal — its last-touched date per Git, or
    'uncommitted' when it is not yet in history. Within each tag the loosest ends
    float up (uncommitted first, then oldest committed) so the ideas most in need
    of a harvest-commit-or-prune decision surface at the top.

    The Garden is deliberately unvalidated; this view is the only lens on it and,
    like every generated file, is disposable and never canonical. Deterministic:
    notes are sorted and dates come from Git, never the wall clock.
    """
    lines = _md_header("Nebula — the Garden of unvalidated ideas", generated_at)

    if not repo.garden_notes:
        lines.append(
            "The Garden is empty. Drop half-formed ideas into `knowledge/garden/` "
            "as plain Markdown (sprinkle `#tags` like `#chaos`, `#philosophy`); "
            "they gestate there — exempt from `make check` — until you say "
            '"Harvest the Garden" to promote the ripe ones into `knowledge/notes/`.')
        lines.append("")
        return "\n".join(lines)

    # One Git call per note, memoized: '' means uncommitted (not yet in history).
    dates = {
        n.path: _git_last_commit(repo.root, n.path.relative_to(repo.root).as_posix())
        for n in repo.garden_notes
    }

    total = len(repo.garden_notes)
    uncommitted = sum(1 for n in repo.garden_notes if not dates[n.path])
    lines.append(
        f"*{total} idea(s) gestating"
        + (f", {uncommitted} not yet committed" if uncommitted else "")
        + ". A disposable lens on an **unvalidated** layer — nothing here is "
        'canonical or link-checked. Say **"Harvest the Garden"** to promote ripe '
        "ideas into the fortress; let the rest gestate or prune them. Dates are "
        "last-touched per Git — **uncommitted and oldest first = ripest for "
        "harvest-or-discard**.*")
    lines.append("")

    # Group by tag (a note appears under each of its tags); untagged bucket last.
    by_tag: dict[str, list] = {}
    for n in repo.garden_notes:
        for k in (n.tags or ["(untagged)"]):
            by_tag.setdefault(k, []).append(n)

    for tag in sorted(by_tag, key=lambda t: (t == "(untagged)", t)):
        heading = "(untagged)" if tag == "(untagged)" else f"#{tag}"
        notes = by_tag[tag]
        lines.append(f"## {heading} · {len(notes)}")
        lines.append("")
        # '' (uncommitted) sorts before any ISO date, then oldest date first.
        for n in sorted(notes, key=lambda n: (dates[n.path], n.slug)):
            stamp = dates[n.path] or "uncommitted"
            others = [t for t in (n.tags or []) if t != tag]
            extra = ("  · " + " ".join(f"#{t}" for t in others)) if others else ""
            lines.append(f"- `{stamp}` — [{n.title}]({_garden_relpath(repo, n)}){extra}")
        lines.append("")

    return "\n".join(lines)


def generate_all(repo: Repo, generated_at: str | None = None) -> dict[str, str]:
    """Build all outputs; returns {relative path: content}.

    The default timestamp is the last-commit time (stable_generated_at), so
    repeated generation over the same committed tree is byte-for-byte identical.
    """
    generated_at = generated_at or stable_generated_at(repo.root)
    manifest = build_manifest(repo, generated_at)
    backlinks = build_backlinks(repo, generated_at)
    outputs = {
        "manifest.json": json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "backlinks.json": json.dumps(backlinks, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "concept-index.md": build_concept_index(repo, backlinks, generated_at) + "\n",
        "source-index.md": build_source_index(repo, generated_at) + "\n",
        "module-view.md": build_module_view(repo, generated_at) + "\n",
        "coordination-view.md": build_coordination_view(repo, generated_at) + "\n",
        "dependency-report.md": build_dependency_report(repo, backlinks, generated_at) + "\n",
        "concept-map.md": build_concept_map(repo, generated_at) + "\n",
        "reports/health.md": build_health(repo, generated_at) + "\n",
        "nebula.md": build_nebula(repo, generated_at) + "\n",
    }
    for name in sorted(repo.collections):
        outputs[f"collections/{name}.md"] = build_collection_view(
            repo, name, repo.collections[name], generated_at) + "\n"
    return outputs


# Files under generated/ that write_outputs must never delete: repo scaffolding,
# OS noise, and the validator's own report (written by tools/validate.py).
_KEEP_NAMES = {".gitkeep", ".DS_Store"}
_KEEP_REPORT_PREFIX = "validation-report"


def write_outputs(repo: Repo, outputs: dict[str, str]) -> None:
    """Write all outputs AND delete stale generated files, so that generated/
    exactly reflects the canonical data (e.g. views of deleted collections
    do not linger)."""
    gen = repo.root / "generated"
    (gen / "reports").mkdir(parents=True, exist_ok=True)
    for rel, content in outputs.items():
        target = gen / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _remove_stale(gen, outputs)


def _remove_stale(gen: Path, outputs: dict[str, str]) -> None:
    expected = {PurePosixPath(rel) for rel in outputs}
    stale_dirs: list[Path] = []
    for f in sorted(gen.rglob("*")):
        if f.is_dir():
            stale_dirs.append(f)
            continue
        if f.name in _KEEP_NAMES:
            continue
        rel = PurePosixPath(f.relative_to(gen).as_posix())
        if rel.parts and rel.parts[0] == "reports" \
                and f.name.startswith(_KEEP_REPORT_PREFIX):
            continue
        if rel not in expected:
            f.unlink()
    # Prune directories left empty by the deletions (deepest first);
    # rmdir refuses non-empty directories, so this is safe.
    for d in sorted(stale_dirs, reverse=True):
        if d.name == "reports":
            continue
        try:
            d.rmdir()
        except OSError:
            pass
