"""The one-page reading room home."""

from __future__ import annotations

from ..loader import Repo
from .common import _first_para, _git_last_commit, _md_header
from .coordination import adoption_counts
from .materials import _materials_queue_rows
from .modules_view import _academic_deadlines

def build_reading_room(repo: Repo, generated_at: str) -> str:
    """The human home page (ADR-006): one generated screen that composes the
    deeper views and links into them. Interface layers (Obsidian, GitHub
    mobile, a bare editor) open THIS file first. It deliberately duplicates no
    canonical fact — everything is drawn from the same inputs as the views it
    links, and it is disposable like every generated file. Deterministic:
    dates come from Git, never the wall clock (no countdowns — VALIDATION's
    byte-identical rule, human-operability review #11)."""
    lines = _md_header("Reading room", generated_at)
    lines.append("*The human home page — start here. Everything below is a "
                 "link into a deeper view; rebuild anytime with `make views` "
                 "(or `python tools/los.py generate`).*")
    lines.append("")

    # Academic dates include available sittings before registration and the
    # windows that gate them; all facts still live in the owning module.
    lines.append("## Academic dates")
    lines.append("")
    deadlines = _academic_deadlines(repo)
    if deadlines:
        for row in deadlines:
            date = row["start_date"]
            if row.get("end_date") != date:
                date += f" to {row['end_date']}"
            if row["kind"] == "registration-window":
                titles = ", ".join(module["title"] for module in row["modules"])
                lines.append(f"- **{date}** — {row['label']}: {titles}")
            else:
                lines.append(f"- **{date}** — {row['title']} ({row['label']}; "
                             f"{row['registration_state']})")
    else:
        lines.append("(no structured academic dates in module records)")
    lines.append("")
    lines.append("Full spine, priorities and neglect signals: "
                 "[coordination-view.md](coordination-view.md)")
    lines.append("")

    # Active workspaces with their next actions (from frontmatter + CONTEXT).
    active = sorted(repo.active_workspaces(), key=lambda w: w.id)
    lines.append(f"## Active workspaces ({len(active)})")
    lines.append("")
    if active:
        for ws in active:
            na = _first_para(ws.section("Next Action"))
            standing = " · standing" if ws.standing else ""
            lines.append(f"- `{ws.id}` ({ws.status}{standing})"
                         + (f" — next: {na}" if na else ""))
    else:
        lines.append("(no active workspaces)")
    lines.append("")

    # Recently changed notes: uncommitted first (most in need of a commit),
    # then newest last-commit date. Same Git-derived idiom as the Nebula.
    lines.append("## Recently changed notes")
    lines.append("")
    dated = []
    for n in repo.notes.values():
        rel = n.path.relative_to(repo.root).as_posix()
        dated.append((_git_last_commit(repo.root, rel), n))
    uncommitted = sorted((n for d, n in dated if not d), key=lambda n: n.id)
    committed = sorted(((d, n) for d, n in dated if d),
                       key=lambda t: (t[0], t[1].id), reverse=True)
    shown = 0
    for n in uncommitted[:10]:
        rel = n.path.relative_to(repo.root).as_posix()
        lines.append(f"- `uncommitted` — [{n.meta.get('title', n.id)}](../{rel}) "
                     f"· {n.meta.get('state', '')}")
        shown += 1
    for d, n in committed[: max(0, 10 - shown)]:
        rel = n.path.relative_to(repo.root).as_posix()
        lines.append(f"- `{d}` — [{n.meta.get('title', n.id)}](../{rel}) "
                     f"· {n.meta.get('state', '')}")
    if not dated:
        lines.append("(no notes yet)")
    lines.append("")

    # Queues that want a decision or a harvest.
    lines.append("## Queues")
    lines.append("")
    inbox = repo.root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir()
                   if not f.name.startswith(".")]) if inbox.is_dir() else 0
    lines.append(f"- inbox: {n_inbox} item(s) in `work/inbox/` "
                 "(the operator routes; trend toward empty)")
    lines.append(f"- garden: {len(repo.garden_notes)} idea(s) gestating — "
                 "[nebula.md](nebula.md)")
    lines.extend(_materials_queue_rows(repo)
                 or ["- materials queues: empty (nothing awaits a decision)"])
    lines.append("")

    # Review & evidence adoption, one line; details live in the health report.
    ad = adoption_counts(repo)
    lines.append("## Review & evidence adoption")
    lines.append("")
    lines.append(f"- reviewed: {ad['notes_reviewed']}/{ad['notes_total']} · "
                 f"with evidence: {ad['notes_with_evidence']}/{ad['notes_total']} · "
                 "details: [reports/health.md](reports/health.md)")
    lines.append("")

    lines.append("## All views")
    lines.append("")
    lines.append("[domain-atlas.md](domain-atlas.md) (cross-domain map) · "
                 "[concept-index.md](concept-index.md) · "
                 "[concept-map.md](concept-map.md) · "
                 "[concept-canvas.canvas](concept-canvas.canvas) (Obsidian) · "
                 "[source-index.md](source-index.md) · "
                 "[dependency-report.md](dependency-report.md) · "
                 "[module-view.md](module-view.md) · "
                 "[nebula.md](nebula.md) · "
                 "[reports/health.md](reports/health.md) · "
                 "[reports/validation-report.md](reports/validation-report.md)")
    lines.append("")
    return "\n".join(lines)
