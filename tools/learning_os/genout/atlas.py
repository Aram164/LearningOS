"""Cross-domain atlas: every domain, its notes, shelves and excluded strata."""

from __future__ import annotations

from ..loader import Repo
from pathlib import Path
from .common import _md_header

ATLAS_DOMAINS = [
    "mathematics", "machine-learning", "systems", "data-systems",
    "algorithms", "programming", "cross-domain",
]


ATLAS_COLLECTION_DOMAIN = {
    "math-bookshelf": "mathematics", "math-lecture-series": "mathematics",
    "ml-bookshelf": "machine-learning", "ml-lecture-series": "machine-learning",
    "ml-explainers": "machine-learning", "ml-broaden-later": "machine-learning",
    "papers-shelf": "machine-learning",
    "ml-systems-bookshelf": "systems", "ml-systems-lecture-series": "systems",
    "algorithms-bookshelf": "algorithms", "algorithms-lecture-series": "algorithms",
    "programming-bookshelf": "programming", "programming-video-courses": "programming",
    "python-internals-shelf": "programming", "project-toolbox": "programming",
}


_ATLAS_SKIP_NAMES = {".DS_Store", "INDEX.html", "README.md", "FILES.txt"}


def _atlas_short(text: str, limit: int = 220) -> str:
    """Collapse a collection description to one compact line."""
    s = " ".join(str(text).split())
    if len(s) <= limit:
        return s
    cut = s.rfind(" ", 0, limit)
    return s[: cut if cut > 0 else limit].rstrip(" ,;—-") + " …"


_ATLAS_ROLE_ORDER = {"crosswalk": 0, "reference": 1, "synthesis": 2,
                     "exercise-bank": 3, "mock-exam": 4}


def _atlas_role_order(role: str) -> tuple[int, str]:
    return (_ATLAS_ROLE_ORDER.get(role, 9), role)


def _atlas_note_link(note, repo: Repo) -> str:
    """One navigable atlas row for a note: title link, id, and state."""
    title = note.meta.get("title", note.id)
    try:
        rel = note.path.relative_to(repo.root).as_posix()
        label = f"[{title}](../{rel})"
    except ValueError:  # note outside the repo root — degrade to plain text
        label = str(title)
    state = note.meta.get("state")
    return f"{label} — `{note.id}`" + (f" · {state}" if state else "")


def _count_material_files(base: Path) -> int:
    """Files under a materials subtree (view signal only; hidden/support-skip
    names excluded). Returns 0 when the subtree does not exist."""
    if not base.is_dir():
        return 0
    n = 0
    for f in base.rglob("*"):
        if not f.is_file() or f.name in _ATLAS_SKIP_NAMES:
            continue
        rel = f.relative_to(base)
        if any(part.startswith(".") for part in rel.parts):
            continue
        n += 1
    return n


def build_domain_atlas(repo: Repo, generated_at: str) -> str:
    """The cross-domain map (ADR-005): every domain's note coverage, curated
    shelves and wiring hubs on one page, plus the strata deliberately OUTSIDE
    retrieval — so no session's field of view collapses to the active
    workspace's domain.

    The **At a glance** block is sized to be read at every session start
    (CLAUDE.md §2); the full sections are opened on demand (CLAUDE.md §7).
    Judgments are harvested from canonical fields (collection descriptions,
    note titles) — this view authors nothing.
    """
    lines = _md_header("Domain atlas — the cross-domain map", generated_at)

    # -- gather ------------------------------------------------------------
    notes_dir = repo.root / "knowledge" / "notes"
    notes_by_domain: dict[str, list] = {}
    for n in repo.notes.values():
        try:
            bucket = n.path.relative_to(notes_dir).parts[0]
        except ValueError:
            bucket = "cross-domain"
        if bucket.endswith(".md"):  # note directly under notes/ (unbucketed)
            bucket = "cross-domain"
        notes_by_domain.setdefault(bucket, []).append(n)

    shelves_by_domain: dict[str, list[tuple[str, dict, int]]] = {}
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        entries = [e for e in (doc.get("entries") or []) if isinstance(e, dict)]
        dom = ATLAS_COLLECTION_DOMAIN.get(name, "cross-domain")
        shelves_by_domain.setdefault(dom, []).append((name, doc, len(entries)))

    domains = list(ATLAS_DOMAINS)
    for extra in sorted(set(notes_by_domain) | set(shelves_by_domain)):
        if extra not in domains:  # future bucket: appears, never dropped
            domains.append(extra)

    def role_counts(notes: list) -> dict[str, int]:
        out: dict[str, int] = {}
        for n in notes:
            r = n.meta.get("role", "synthesis")
            out[r] = out.get(r, 0) + 1
        return out

    # -- At a glance (the session-start block, CLAUDE.md §2) ---------------
    lines.append("## At a glance")
    lines.append("")
    for dom in domains:
        notes = notes_by_domain.get(dom, [])
        shelves = shelves_by_domain.get(dom, [])
        n_entries = sum(c for _, _, c in shelves)
        n_cross = sum(1 for n in notes if n.meta.get("role") == "crosswalk")
        bits = []
        noun = "note" if len(notes) == 1 else "notes"
        bits.append(f"{len(notes)} {noun}" + (f" ({n_cross} crosswalk)" if n_cross else ""))
        bits.append(f"{len(shelves)} shelves ({n_entries} entries)" if shelves
                    else "no shelves yet")
        lines.append(f"- **{dom}** — " + " · ".join(bits))
    lines.append(
        "- **Outside this map (deliberate):** Foundations archive (unregistered; "
        "names in `materials/FILES.txt`) · Master's Planning quarantine "
        "(boundary only) · frozen `legacy/` · quarantined `Job/` "
        "(CLAUDE.md §13) — details in the last section.")
    lines.append("")
    lines.append(
        "*Per-domain shelves and wiring hubs below · per-concept joins → "
        "`concept-index.md` · full source detail → `source-index.md` · wiring "
        "debt → `reports/health.md`.*")
    lines.append("")

    # -- full per-domain sections ------------------------------------------
    for dom in domains:
        notes = sorted(notes_by_domain.get(dom, []), key=lambda n: n.id)
        shelves = shelves_by_domain.get(dom, [])
        lines.append(f"## {dom}")
        lines.append("")
        if notes:
            rc = role_counts(notes)
            parts = " · ".join(f"{r} {rc[r]}" for r in sorted(rc))
            lines.append(f"Notes: {len(notes)} — {parts}")
        else:
            lines.append("Notes: none yet")
        cross = [n for n in notes if n.meta.get("role") == "crosswalk"]
        if cross:
            lines.append("")
            lines.append("Wiring hubs (crosswalks):")
            lines.append("")
            for n in cross:
                lines.append(f"- {_atlas_note_link(n, repo)}")
        if notes:
            # A map that only counts its territory is not a map: every note is
            # listed and linked, grouped by role, so the atlas can be navigated
            # instead of merely skimmed (ADR-005 asks for reach, not a census).
            lines.append("")
            lines.append("Notes by role:")
            lines.append("")
            by_role: dict[str, list] = {}
            for n in notes:
                by_role.setdefault(n.meta.get("role", "synthesis"), []).append(n)
            for role in sorted(by_role, key=_atlas_role_order):
                lines.append(f"- **{role}** ({len(by_role[role])})")
                for n in sorted(by_role[role], key=lambda x: str(x.meta.get("title", x.id))):
                    lines.append(f"  - {_atlas_note_link(n, repo)}")
        lines.append("")
        if shelves:
            lines.append("Shelves:")
            lines.append("")
            for name, doc, count in shelves:
                title = doc.get("title", name)
                desc = _atlas_short(doc.get("description", "")) if doc.get("description") else ""
                lines.append(f"- **[{title}](collections/{name}.md)** ({count})"
                             + (f" — {desc}" if desc else ""))
        else:
            lines.append("Shelves: none yet — sources for this domain surface only "
                         "through concept links and note references.")
        lines.append("")

    # -- deliberately excluded strata --------------------------------------
    lines.append("## Not in this map — deliberately excluded strata")
    lines.append("")
    materials = repo.learningos_root / "materials"
    if materials.is_dir():
        n_found = _count_material_files(materials / "Foundations")
        if n_found:
            lines.append(
                f"- **Foundations archive** — {n_found} files under "
                "`materials/Foundations/` (undergrad/general reference, NOT "
                "registered sources; browse only). Names are greppable in "
                "`materials/FILES.txt` (`make materials`); promotion path is "
                "WORKFLOWS §6a when one becomes relevant.")
        n_unsorted = _count_material_files(materials / "_unsorted")
        if n_unsorted:
            lines.append(
                f"- **materials/_unsorted** — {n_unsorted} files awaiting "
                "registration (WORKFLOWS §6a).")
    else:
        lines.append("- **Materials tree** — not reachable from this checkout; "
                     "archive counts unavailable.")
    lines.append(
        "- **Master's Planning** — Git-tracked operational quarantine; only its "
        "boundary record is normally loadable. Content, counts and menus are "
        "excluded until deliberate future promotion (WORKFLOWS §27).")
    if (repo.root.parent.parent / "legacy").is_dir():
        lines.append(
            "- **Legacy tree** — the frozen pre-v3 history beside `LearningOS/` "
            "(tag `pre-v3-baseline`); historical context only, never canonical, "
            "never retrieved by default (ARCHITECTURE §2.4).")
    lines.append(
        "- **`Job/`** — quarantined (CLAUDE.md §13); outside every map by design.")
    lines.append("")
    return "\n".join(lines)
