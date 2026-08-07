"""Garden nebula view."""

from __future__ import annotations

from ..loader import Repo
from .common import _git_last_commit, _md_header

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
