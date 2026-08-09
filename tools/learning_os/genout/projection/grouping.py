"""The two coarse facets — thematic groups and topics — and their ordering.

Authored records own membership; the registry owns display order. Everything
that needs group ids in canonical order goes through here so that rule is
stated once.
"""

from __future__ import annotations

from ...loader import Repo


def ordered_thematic_group_ids(repo: Repo, values) -> list[str]:
    """Return unique group ids in the canonical registry order.

    Authored records own membership; the registry owns display order. Unknown
    ids remain at the end so a generated snapshot does not silently erase an
    invalid authored reference before validation reports it.
    """
    unique = {str(value) for value in (values or []) if value}
    order = {
        gid: (int(group.get("order", 0)), gid)
        for gid, group in repo.thematic_groups.items()
    }
    return sorted(unique, key=lambda gid: order.get(gid, (10**9, gid)))


def source_thematic_groups(repo: Repo) -> dict[str, list[str]]:
    """Project the source's own coarse intellectual classification.

    ADR-007/009 keep source identity/classification independent from the
    contexts that currently use it. A collection may curate a source and a
    module may route it, but neither relationship changes what the source is
    about. Those contextual relationships are projected separately — most
    notably through ``indexes.source_to_modules`` for Library "Current use".

    The interface therefore receives authored source membership here and never
    has to undo module/collection context that leaked into Domain.
    """
    return {
        sid: ordered_thematic_group_ids(
            repo,
            source.get("thematic_group_ids", []) or [],
        )
        for sid, source in repo.sources.items()
    }


def project_thematic_groups(repo: Repo) -> list[dict]:
    return [
        {
            "id": gid,
            "title": group.get("title", gid),
            "description": " ".join(str(group.get("description", "")).split()),
            "order": group.get("order", 0),
        }
        for gid, group in sorted(
            repo.thematic_groups.items(),
            key=lambda item: (int(item[1].get("order", 0)), item[0]),
        )
    ]


def project_topics(repo: Repo) -> list[dict]:
    """The topic vocabulary itself, so an interface can render titles and group
    topics under their display domain instead of showing bare ids. `domain` is a
    display grouping only — never a constraint on which sources may carry a
    topic (ADR-009)."""
    return [
        {
            "id": tid,
            "title": topic.get("title", tid),
            "domain": topic.get("domain"),
        }
        for tid, topic in sorted(repo.topics.items())
    ]
