"""Coordination view, adoption counts and repository health."""

from __future__ import annotations

from ..loader import Repo
from .atlas import ATLAS_COLLECTION_DOMAIN
from .common import _first_para, _git_last_commit, _md_header
from .materials import _materials_queue_rows
from .modules_view import _exam_spine_lines


def adoption_counts(repo: Repo) -> dict:
    """Adoption of the existing note review/evidence fields (no new schema —
    the fields have been in note.schema.json since v3; the gap is usage).
    Shared by the health report, the reading room, and `los.py status`."""
    notes = repo.notes.values()
    total = len(repo.notes)
    reviewed = sorted(n.id for n in notes if n.meta.get("reviewed"))
    with_evidence = sorted(n.id for n in notes if n.meta.get("evidence"))
    by_state: dict[str, int] = {}
    for n in notes:
        s = str(n.meta.get("state", "(unset)"))
        by_state[s] = by_state.get(s, 0) + 1
    # A reviewed note whose last Git touch postdates its review date has
    # drifted past its review; uncommitted edits count as drifted too.
    changed_since_review: list[str] = []
    for n in repo.notes.values():
        rev = n.meta.get("reviewed")
        if not rev:
            continue
        last = _git_last_commit(repo.root, n.path.relative_to(repo.root).as_posix())
        if not last or str(last) > str(rev):
            changed_since_review.append(n.id)
    return {
        "notes_total": total,
        "notes_reviewed": len(reviewed),
        "notes_with_evidence": len(with_evidence),
        "changed_since_review": sorted(changed_since_review),
        "by_state": by_state,
    }


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
    queue_rows = _materials_queue_rows(repo)
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

    # Source wiring / visibility debt (ADR-005). A source surfaces in concept
    # retrieval only through a concept-linked evaluation, on a shelf only
    # through a collection, and via notes only through note `sources:` links.
    # This is a maintenance SIGNAL, never a backlog: debt is repaid on use
    # (WORKFLOWS §6a "wire on use"), not as a bulk project.
    in_collection: set[str] = set()
    for doc in repo.collections.values():
        for e in doc.get("entries") or []:
            if isinstance(e, dict) and e.get("source"):
                in_collection.add(str(e["source"]))
    note_linked = {str(s) for n in repo.notes.values()
                   for s in (n.meta.get("sources") or [])}
    with_eval: set[str] = set()
    concept_wired: set[str] = set()
    for sid, s in repo.sources.items():
        evs = [ev for ev in (s.get("evaluations") or []) if isinstance(ev, dict)]
        if evs:
            with_eval.add(sid)
        if any(ev.get("concepts") for ev in evs):
            concept_wired.add(sid)
    least = sorted(sid for sid in repo.sources
                   if sid not in concept_wired and sid not in in_collection
                   and sid not in note_linked)
    lines.append("## Source wiring (visibility debt)")
    lines.append("")
    lines.append(f"- sources with ≥1 evaluation: {len(with_eval)}/{len(repo.sources)}")
    lines.append(f"- concept-wired (≥1 evaluation naming concepts — visible to "
                 f"concept retrieval): {len(concept_wired)}/{len(repo.sources)}")
    lines.append(f"- on ≥1 shelf (collections): {len(in_collection & set(repo.sources))}"
                 f"/{len(repo.sources)}")
    lines.append(f"- referenced by ≥1 note: {len(note_linked & set(repo.sources))}"
                 f"/{len(repo.sources)}")
    lines.append(f"- **least visible** (no concept link, no shelf, no note): "
                 f"{len(least)}")
    if least:
        by_origin: dict[str, list[str]] = {}
        for sid in least:
            origin = repo.source_origins.get(sid)
            key = origin.name if origin else "(unknown origin)"
            by_origin.setdefault(key, []).append(sid)
        lines.append("")
        for key in sorted(by_origin):
            ids = " · ".join(f"`{sid}`" for sid in by_origin[key])
            lines.append(f"  - {key}: {ids}")
    lines.append("")
    lines.append("*Wire on use (WORKFLOWS §6a): when one of these actually comes "
                 "up in a session, add the minimal evaluation stub — concepts + "
                 "roles + one strengths line. Never bulk-backfill.*")
    lines.append("")

    # Atlas shelf placement (review 2026-09-09). A collection the shelf→domain
    # map does not name renders under `cross-domain`: counts stay right,
    # placement is wrong, and nothing else flags it. A maintenance SIGNAL,
    # never a backlog: give the shelf an explicit domain in
    # ATLAS_COLLECTION_DOMAIN (genout/atlas.py).
    unmapped = sorted(name for name in repo.collections
                      if name not in ATLAS_COLLECTION_DOMAIN)
    lines.append("## Atlas shelf placement")
    lines.append("")
    if unmapped:
        lines.append("- shelves without an explicit atlas domain "
                     f"(shown as cross-domain): {len(unmapped)}")
        lines.extend(f"  - `{name}`" for name in unmapped)
    else:
        lines.append("- every shelf has an explicit atlas domain "
                     "(none falling back to cross-domain)")
    lines.append("")

    # Review & evidence adoption (2026-08-03). The fields (`reviewed`,
    # `evidence`, `state`) have existed in note.schema.json since v3 — this
    # section surfaces how far they are actually used. Adopt on touch
    # (WORKFLOWS §13 review a note, §8 record evidence); never bulk-backfill.
    ad = adoption_counts(repo)
    lines.append("## Review & evidence adoption")
    lines.append("")
    lines.append(f"- notes with a `reviewed` date: {ad['notes_reviewed']}"
                 f"/{ad['notes_total']}")
    if ad["changed_since_review"]:
        lines.append("  - changed after their last review (Git postdates "
                     "`reviewed`, or uncommitted): "
                     + " · ".join(f"`{nid}`" for nid in ad["changed_since_review"]))
    lines.append(f"- notes with `evidence` entries: {ad['notes_with_evidence']}"
                 f"/{ad['notes_total']}")
    lines.append("- note states: "
                 + " · ".join(f"{k}: {ad['by_state'][k]}"
                              for k in sorted(ad["by_state"])))
    lines.append("")
    lines.append("*The schema already has these fields; the gap is adoption. "
                 "Set `reviewed` when a semantic review actually happens "
                 "(WORKFLOWS §13 — file modification is not review) and attach "
                 "`evidence` when a derivation/exercise/implementation exists "
                 "(§8). On-touch only — never as a bulk project.*")
    lines.append("")
    lines.append("*Run `python tools/validate.py` for the full rule check.*")
    lines.append("")
    return "\n".join(lines)
