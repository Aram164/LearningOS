"""The Library, as a folder tree (ADR-007 + ADR-009).

Why this file changed shape
---------------------------
The faceted Library answered one question the alphabetical index could not:
*how do I find a source when I do not already know its name?* It answered it by
projecting the same sources five ways — domain, topic, purpose, form, current
use — and letting the counts overlap, on the argument that the useful sources
refuse to declare one home. Goodfellow is deep learning AND optimization AND
generative modelling; forcing a pick throws away two thirds of the answer. That
argument was right, and this file used to end it with "if a number here looks
too big to be a folder, that is the point — it is not a folder."

It was right about overlap and wrong about folders. A set of counted buckets has
no *place* in it: nowhere to stand, nothing to walk down, and no way to see that
a module has exercise sheets but no past papers. What folders actually require
is not that a source has one home — it is that a source can be in several, which
is exactly what a file manager already does, and calls an alias.

So the projection is now a tree, and the overlap is kept rather than resolved:

    Library/
      <Domain>/                     one per thematic group (ADR-007)
        Modules/                    the modules taught from this domain
          <Module>/
            Lecture Slides/ · Past Exams & Mocks/ · Exercise Sheets/
            Recordings/ · Books & Reading/ · Courses/
            Documentation & Tools/ · Websites & Links/ · Other/
        Lecture Slides/ Books/ Courses/ Videos/ Papers/
        Documentation/ Websites & Links/ Software & Tools/ Other/
      Skill Tracks/                 modules carrying no domain
      Curated Packs/ · Catalogues/
      Unfiled/                      sources carrying no domain

Three properties make it trustworthy, and they are the design:

1. **Partition where a partition is meaningful.** Within one domain the nine
   material-type folders are disjoint and exhaustive (`type` is a single value;
   a missing one lands in `Other`). Within one module the nine study buckets are
   likewise disjoint, because `_bucket_for` takes the FIRST match in a fixed
   priority order. A folder's count is therefore a count.
2. **Aliases where overlap is the truth.** Across domains a source may appear
   more than once, and each such entry is marked, so it reads as one record seen
   twice rather than two copies.
3. **Totality.** Every source is reachable or lands in `Unfiled`. The coverage
   line at the top states this rather than asking to be trusted.

Only a DECLARED folder may be empty — a domain from the taxonomy, a module from
the curriculum. Both exist whether or not anything is filed against them, and
saying so is a documented absence. A derived folder (a bucket, a shelf) is
emitted only when something is in it.

The facet tallies the previous view existed for are not lost: they are the
appendix, which is the right size for them once there is somewhere to stand.

Kept in step with the app
-------------------------
`obsidian-ui/src/features/library/finder-tree.ts` renders the same tree for the
Obsidian app, from the same records via `generated/manifest.json`. The two
taxonomies — `MATERIAL_TYPES`, `MODULE_BUCKETS` and the bucket priority — are
deliberately identical and must be changed together; a learner who saw a
different shelf in each surface would rightly stop trusting both.
"""

from __future__ import annotations

from ..loader import Repo
from .common import _md_header, _slug

# The nine material types, in the order the Library shows them.
MATERIAL_TYPES: tuple[tuple[str, str], ...] = (
    ("lecture", "Lecture Slides"),
    ("book", "Books"),
    ("course", "Courses"),
    ("video", "Videos"),
    ("paper", "Papers"),
    ("documentation", "Documentation"),
    ("website", "Websites & Links"),
    ("software", "Software & Tools"),
    ("other", "Other"),
)

MATERIAL_TYPE_LABELS = dict(MATERIAL_TYPES)

# The study buckets inside a module, in PRIORITY order — `_bucket_for` returns
# the first match, so a past-paper collection whose roles also include
# `exercise` files under `Past Exams & Mocks`, the more specific claim, and
# there only. `Lecture Slides` leads because a module's own decks are reached
# for by form rather than by purpose.
MODULE_BUCKETS: tuple[tuple[str, str], ...] = (
    ("lecture-slides", "Lecture Slides"),
    ("past-exams", "Past Exams & Mocks"),
    ("exercises", "Exercise Sheets"),
    ("recordings", "Recordings"),
    ("reading", "Books & Reading"),
    ("courses", "Courses"),
    ("reference", "Documentation & Tools"),
    ("links", "Websites & Links"),
    ("other", "Other"),
)

MODULE_BUCKET_LABELS = dict(MODULE_BUCKETS)


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


def _roles(source: dict) -> set[str]:
    return {
        role
        for ev in (source.get("evaluations", []) or [])
        for role in (ev.get("roles", []) or [])
    }


def _type_of(source: dict) -> str:
    """The one material type a source has. Total: an unknown type is `other`."""
    kind = str(source.get("type") or "").strip().lower()
    return kind if kind in MATERIAL_TYPE_LABELS else "other"


def _bucket_for(source: dict) -> str:
    """The one module bucket a source belongs to. First match wins."""
    kind = _type_of(source)
    if kind == "lecture":
        return "lecture-slides"
    roles = _roles(source)
    if "mock-exam" in roles:
        return "past-exams"
    if "exercise" in roles or "practice" in roles:
        return "exercises"
    if kind == "video":
        return "recordings"
    if kind in ("book", "paper"):
        return "reading"
    if kind == "course":
        return "courses"
    if kind in ("documentation", "software"):
        return "reference"
    if kind == "website":
        return "links"
    return "other"


def _where(source: dict) -> str:
    """Whether this is something you have, or something you reach."""
    if source.get("material"):
        return "local"
    if source.get("url"):
        return "online"
    return "registry entry"


def _byline(source: dict) -> str:
    authors = source.get("authors", []) or []
    if authors:
        who = f"{authors[0]} et al." if len(authors) > 2 else " & ".join(authors)
    else:
        who = str(source.get("organization") or "")
    year = str(source.get("year") or "")
    return " · ".join(part for part in (who, year) if part)


def _entry_line(sid: str, source: dict, homes: int) -> str:
    """One source, as a file in a listing."""
    facts = [fact for fact in (_byline(source), _where(source)) if fact]
    if homes > 1:
        facts.append(f"also in {homes - 1} other domain{'' if homes == 2 else 's'}")
    suffix = f" — {' · '.join(facts)}" if facts else ""
    return f"  - {source.get('title', sid)} `{sid}`{suffix}"


def _title(record: dict | None, fallback: str) -> str:
    if not record:
        return fallback
    return str(record.get("title") or fallback)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}{'' if count == 1 else 's'}"


def _anchor(name: str) -> str:
    """The GitHub anchor for a `#### <name>/` heading."""
    return _slug(f"{name}/")


def _module_body(
    repo: Repo,
    module_id: str,
    routed: list[str],
    homes: dict[str, int],
    indent: str,
) -> list[str]:
    """A module's buckets, or the statement that nothing is routed to it yet."""
    if not routed:
        return [
            f"{indent}*No source is routed to this module yet — a module exists "
            "because the curriculum declares it, not because material has "
            "arrived.*",
            "",
        ]
    lines: list[str] = []
    for bucket, label in MODULE_BUCKETS:
        members = [sid for sid in routed if _bucket_for(repo.sources[sid]) == bucket]
        if not members:
            continue
        lines.append(f"{indent}**{label}/** ({len(members)})")
        lines += [
            _entry_line(sid, repo.sources[sid], homes.get(sid, 0)) for sid in members
        ]
        lines.append("")
    return lines


def build_library(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Library — folders", generated_at)
    lines += [
        "One folder per domain; inside it, the modules taught from that domain "
        "and a folder for each kind of material. A source may appear in more "
        "than one folder — that is one record seen from two domains, not a "
        "copy, and every such entry says so.",
        "",
    ]

    sources = repo.sources
    groups = repo.thematic_groups
    routes = _module_routes(repo)
    total = len(sources)

    # Which domains does each source actually live in? A group id nothing
    # defines is not a home, so it does not count as one.
    homes: dict[str, int] = {}
    by_group: dict[str, list[str]] = {}
    unfiled: list[str] = []
    for sid in sorted(sources):
        own = [gid for gid in (sources[sid].get("thematic_group_ids") or []) if gid in groups]
        homes[sid] = len(own)
        if own:
            for gid in own:
                by_group.setdefault(gid, []).append(sid)
        else:
            unfiled.append(sid)

    modules_by_group: dict[str, list[str]] = {}
    ungrouped_modules: list[str] = []
    for mid in sorted(repo.modules):
        own = [gid for gid in (repo.modules[mid].get("thematic_group_ids") or []) if gid in groups]
        if own:
            for gid in own:
                modules_by_group.setdefault(gid, []).append(mid)
        else:
            ungrouped_modules.append(mid)

    routed_by_module: dict[str, list[str]] = {}
    for sid, mids in routes.items():
        if sid not in sources:
            continue
        for mid in mids:
            routed_by_module.setdefault(mid, []).append(sid)
    for members in routed_by_module.values():
        members.sort()

    reached = len(set().union(*by_group.values()) if by_group else set()) + len(unfiled)
    lines += [
        f"**{total} sources.** "
        + (
            f"All {total} are reachable in these folders."
            if reached >= total
            else f"{reached} of {total} are reachable — {total - reached} cannot be browsed."
        ),
        "",
        # Registered sources are what this file can account for. Material that
        # sits on disk beside a registered path without a record of its own —
        # the exercise slides next to a claimed lecture folder — is real, is
        # not here, and is not silently implied to be absent: the app's folder
        # browser reads the filesystem and shows it under "Not in the
        # registry". Saying so beats a completeness claim this file cannot
        # actually check.
        "*That count is of registered sources. Material present on disk but "
        "claimed by no source record is not listed here; the app's Library "
        "shows it under **Not in the registry**.*",
        "",
    ]

    ordered_groups = sorted(groups, key=lambda gid: (groups[gid].get("order", 0), gid))

    # module id -> the domain that rendered its material in full.
    rendered_modules: dict[str, str] = {}

    # ---------------------------------------------------------------- the tree
    for gid in ordered_groups:
        group = groups[gid]
        members = by_group.get(gid, [])
        module_ids = modules_by_group.get(gid, [])
        lines += [f"## {_title(group, gid)}/", ""]
        if group.get("description"):
            lines += [str(group["description"]), ""]
        lines += [
            "*"
            + " · ".join(
                part
                for part in (
                    _plural(len(members), "source"),
                    _plural(len(module_ids), "module") if module_ids else "",
                )
                if part
            )
            + "*",
            "",
        ]

        if not members and not module_ids:
            lines += [
                "*Nothing filed here yet. A domain exists because the taxonomy "
                "declares it (ADR-007), so this is an absence on the record "
                "rather than a folder gone missing.*",
                "",
            ]
            continue

        if module_ids:
            lines += ["### Modules/", ""]
            for mid in module_ids:
                module = repo.modules[mid]
                routed = routed_by_module.get(mid, [])
                name = _title(module, mid)
                lines += [f"#### {name}/", ""]

                # A module taught from two domains is one module, and the app
                # shows it under both because you only ever stand in one folder
                # at a time. A document is read straight through, so the second
                # appearance points at the first instead of repeating forty
                # lines — the alias, said the way a document can say it.
                first_seen = rendered_modules.get(mid)
                if first_seen:
                    lines += [
                        f"*Also taught from {first_seen}. Its material is listed "
                        f"there — see [{name}/](#{_anchor(name)}).*",
                        "",
                    ]
                    continue
                rendered_modules[mid] = _title(group, gid)

                code = str(module.get("code") or "")
                facts = [part for part in (code, _plural(len(routed), "source")) if part]
                lines += [f"*{' · '.join(facts)}*", ""]
                lines += _module_body(repo, mid, routed, homes, "")

        for kind, label in MATERIAL_TYPES:
            in_bucket = [sid for sid in members if _type_of(sources[sid]) == kind]
            if not in_bucket:
                continue
            lines += [f"### {label}/ ({len(in_bucket)})", ""]
            lines += [_entry_line(sid, sources[sid], homes.get(sid, 0)) for sid in in_bucket]
            lines.append("")

    # ------------------------------------------------------------- the shelves
    if ungrouped_modules:
        lines += [
            "## Skill Tracks/",
            "",
            "Modules with no thematic group of their own. They are here rather "
            "than guessed into a domain; their sources still appear under every "
            "domain they are registered in.",
            "",
        ]
        for mid in ungrouped_modules:
            module = repo.modules[mid]
            routed = routed_by_module.get(mid, [])
            lines += [f"### {_title(module, mid)}/", ""]
            lines += [f"*{_plural(len(routed), 'source')}*", ""]
            lines += _module_body(repo, mid, routed, homes, "")

    packs = {cid: c for cid, c in repo.collections.items()
             if c.get("collection_kind") == "topic-pack"}
    catalogues = {cid: c for cid, c in repo.collections.items()
                  if c.get("collection_kind") != "topic-pack"}

    for title, shelf, note in (
        ("Curated Packs", packs,
         "Narrow, manually ordered collections. The order is the argument, so "
         "it is kept rather than alphabetised."),
        ("Catalogues", catalogues,
         "Standing shelves that cut across domains."),
    ):
        if not shelf:
            continue
        lines += [f"## {title}/", "", note, ""]
        for cid in sorted(shelf):
            record = shelf[cid]
            entries, seen = [], set()
            for entry in record.get("entries", []) or []:
                sid = entry.get("source") if isinstance(entry, dict) else entry
                if sid and sid not in seen and sid in sources:
                    seen.add(sid)
                    entries.append(sid)
            lines += [f"### {_title(record, cid)}/ ({len(entries)})", ""]
            if record.get("purpose"):
                lines += [str(record["purpose"]), ""]
            lines += [_entry_line(sid, sources[sid], homes.get(sid, 0)) for sid in entries]
            lines.append("")

    if unfiled:
        lines += [
            "## Unfiled/",
            "",
            "Sources with no thematic group recorded. Nothing is lost here — "
            "this folder is what lets the tree hold everything, and it empties "
            "as domains are recorded.",
            "",
        ]
        lines += [_entry_line(sid, sources[sid], 0) for sid in unfiled]
        lines.append("")

    # -------------------------------------------------------------- other ways
    # The facets this view used to be made of. They are still true and still
    # useful — a source IS good for several purposes at once — but they are a
    # way of slicing the shelf, not a way of standing on it.
    lines += [
        "## Other ways in",
        "",
        "The same sources, cut by the facets the folders do not use. The counts "
        "overlap on purpose: a source is good for several things at once.",
        "",
    ]

    by_purpose: dict[str, int] = {}
    by_topic: dict[str, int] = {}
    untopiced = 0
    for source in sources.values():
        for role in _roles(source):
            by_purpose[role] = by_purpose.get(role, 0) + 1
        topics = source.get("topics", []) or []
        if topics:
            for tid in topics:
                by_topic[tid] = by_topic.get(tid, 0) + 1
        else:
            untopiced += 1

    lines += ["**By purpose** — what a source is good FOR.", ""]
    for role in sorted(by_purpose, key=lambda k: (-by_purpose[k], k)):
        lines.append(f"- {role}: {by_purpose[role]}")
    lines.append("")

    lines += [
        "**By topic** — medium-grained subjects (ADR-009), populated **on use, "
        "never in bulk**.",
        "",
    ]
    if by_topic:
        for tid in sorted(by_topic, key=lambda k: (-by_topic[k], k)):
            label = repo.topics.get(tid, {}).get("title", tid)
            lines.append(f"- {label}: {by_topic[tid]}")
    else:
        lines.append("*Nothing carries a topic yet.*")
    lines.append("")

    if untopiced:
        lines += [
            f"{untopiced} of {total} sources carry no topic. This is the expected "
            "state under on-use population, not a backlog to clear in one pass: "
            "assigning topics to a source nobody has opened would be inventing a "
            "judgment (ADR-005). They gain topics the first time they are "
            "actually used — and unlike the old faceted view, an untopiced "
            "source is not thereby harder to find, because it still sits in its "
            "domain's folder.",
            "",
        ]

    return "\n".join(lines).rstrip() + "\n"
