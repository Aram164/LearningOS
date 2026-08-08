"""The faceted Library view (ADR-009).

One question this answers that `source-index.md` cannot: *how do I find a source
when I do not already know its name?* The index is an alphabetical list, and an
alphabetical list of 239 items is a haystack. The subject tree (ADR-007) is
better, but it still asks each source to declare one primary home — and the
useful ones refuse to. Goodfellow is deep learning AND optimization AND
generative modelling; forcing a pick throws away two thirds of the answer.

So this view does not organise sources. It *projects* them, four ways over the
same objects, and lets the counts overlap:

    domain  = thematic_group_ids   (ADR-007, coarse, ~8)
    topic   = topics               (ADR-009, medium, 20-40, the only new field)
    purpose = evaluations[].roles  (what a source is good FOR)
    form    = type                 (book, course, paper, video, …)
    use     = module source-maps + stage resources (where it is live right now)

Only `topics` was added for this. The other four already existed and were
already populated — which is why the faceted Library is mostly a rendering
problem rather than a data-model one.

Sparsity is expected and is not a defect. Topics are populated on use, never by
bulk backfill (ADR-005), so most sources will carry none for a long time. The
view therefore reports what is unclassified instead of quietly implying the
Library is smaller than it is.
"""

from __future__ import annotations

from ..loader import Repo
from .common import _md_header


def _module_routes(repo: Repo) -> dict[str, set[str]]:
    """source_id -> {module_id}, from BOTH module source-maps and stage resources.

    A source can be routed by a module's source-map without any stage citing it
    yet, and a stage can cite a source the map never listed. Either one means
    "in use", so both are counted.
    """
    routes: dict[str, set[str]] = {}
    for mid, source_map in repo.module_source_maps.items():
        for entry in source_map.get("sources", []) or []:
            sid = entry.get("source_id")
            if sid:
                routes.setdefault(sid, set()).add(mid)
    for study_map in repo.study_maps.values():
        mid = getattr(study_map, "module_id", None) or study_map.data.get("module_id")
        if not mid:
            continue
        for stage in study_map.data.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for resource in stage.get("resources", []) or []:
                if isinstance(resource, dict) and resource.get("source_id"):
                    routes.setdefault(resource["source_id"], set()).add(mid)
    return routes


def _facet_section(title: str, note: str, buckets: dict[str, list[str]],
                   labels: dict[str, str] | None = None) -> list[str]:
    """Render one facet as counted buckets. Counts overlap by design."""
    lines = [f"## {title}", "", note, ""]
    if not buckets:
        lines += ["*Nothing classified along this facet yet.*", ""]
        return lines
    width = max((len(labels.get(k, k) if labels else k) for k in buckets), default=0)
    for key in sorted(buckets, key=lambda k: (-len(buckets[k]), k)):
        label = labels.get(key, key) if labels else key
        lines.append(f"- **{label.ljust(width)}**  {len(buckets[key])}")
    lines.append("")
    return lines


def build_library(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Library — faceted", generated_at)
    lines += [
        "Same sources, four projections. **The counts overlap on purpose**: a source",
        "participates in several domains, topics and purposes rather than living in",
        "one of them. If a number here looks too big to be a folder, that is the",
        "point — it is not a folder.",
        "",
    ]

    sources = repo.sources
    routes = _module_routes(repo)
    total = len(sources)

    by_domain: dict[str, list[str]] = {}
    by_topic: dict[str, list[str]] = {}
    by_purpose: dict[str, list[str]] = {}
    by_form: dict[str, list[str]] = {}
    by_use: dict[str, list[str]] = {}
    untopiced: list[str] = []

    for sid in sorted(sources):
        source = sources[sid]
        for gid in source.get("thematic_group_ids", []) or []:
            by_domain.setdefault(gid, []).append(sid)
        topics = source.get("topics", []) or []
        if topics:
            for tid in topics:
                by_topic.setdefault(tid, []).append(sid)
        else:
            untopiced.append(sid)
        roles = {r for ev in (source.get("evaluations", []) or [])
                 for r in (ev.get("roles", []) or [])}
        for role in roles:
            by_purpose.setdefault(role, []).append(sid)
        by_form.setdefault(str(source.get("type") or "unspecified"), []).append(sid)
        for mid in routes.get(sid, set()) or {"(no current module)"}:
            by_use.setdefault(mid, []).append(sid)

    group_titles = {gid: g.get("title", gid) for gid, g in repo.thematic_groups.items()}
    topic_titles = {tid: t.get("title", tid) for tid, t in repo.topics.items()}

    lines += [f"**{total} sources.**", ""]
    lines += _facet_section(
        "By domain", "Coarse intellectual areas (ADR-007). Every source carries at least one.",
        by_domain, group_titles)
    lines += _facet_section(
        "By topic",
        "Medium-grained subjects (ADR-009). Populated **on use, never in bulk** — a "
        "source gains topics the first time it is actually used, so this section grows "
        "as you work rather than from a backfill that would invent judgments.",
        by_topic, topic_titles)
    lines += _facet_section(
        "By purpose", "What a source is good FOR, from its contextual evaluations.",
        by_purpose)
    lines += _facet_section(
        "By form", "What kind of artifact it is.", by_form)
    lines += _facet_section(
        "By current use", "Which module routes it today. Sources with no route are not "
        "waste — they are the shelf you reach for when a question arrives.",
        by_use)

    if untopiced:
        lines += [
            "## Not yet classified by topic",
            "",
            f"**{len(untopiced)} of {total} sources** carry no topic yet. This is the "
            "expected state under on-use population, not a backlog to clear in one pass: "
            "assigning topics to a source nobody has opened would be inventing a judgment "
            "(ADR-005). They gain topics the first time they are actually used.",
            "",
        ]

    # The enumerate-don't-count rule: a facet that reports only totals is a
    # dead end. Every bucket must be openable, so list the members.
    lines += ["## Members", "", "Every bucket above, enumerated.", ""]
    for title, buckets, labels in (
        ("Domains", by_domain, group_titles),
        ("Topics", by_topic, topic_titles),
        ("Purposes", by_purpose, None),
        ("Forms", by_form, None),
        ("Current use", by_use, None),
    ):
        lines += [f"### {title}", ""]
        if not buckets:
            lines += ["*(none yet)*", ""]
            continue
        for key in sorted(buckets):
            label = labels.get(key, key) if labels else key
            members = ", ".join(f"`{s}`" for s in sorted(buckets[key]))
            lines += [f"**{label}** ({len(buckets[key])}) — {members}", ""]

    return "\n".join(lines).rstrip() + "\n"
