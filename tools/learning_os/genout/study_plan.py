"""The study-plan view: every stage, every material option, and why each one.

The repository has always been able to answer "what sources exist" (the Library)
and "what should I do next" (the coordination view). It could not answer the
question a learner actually asks when sitting down with one lecture: *these are
my options for this stage — what does each one give me that the others do not?*
That answer existed only inside `study-map.yaml` files nobody reads directly.

So this view enumerates rather than counts (ADR: every surface lists and links
its items). For each unit it prints every stage in order and, under each stage,
every routed material with:

  * what kind of use it is (read / watch / practise / reference),
  * the exact locator — the chapter and page range you open,
  * the one-line `angle`, rendered inline, and
  * the long `angle_detail`, attached as a hover.

The hover is a plain `<span title="…">`, which Obsidian's reading view and every
browser render natively. That is deliberate: no script, no dependency, and the
text stays visible to grep and to a plain-text reader who never hovers at all.
"""

from __future__ import annotations

from ..loader import Repo
from .common import _md_header

_KIND_MARK = {
    "read": "read",
    "watch": "watch",
    "practise": "practise",
    "reference": "reference",
}

_TRIAGE_ORDER = {"required-now": 0, "helpful-now": 1, "deferred": 2, "reference-only": 3}


def _escape_attr(text: str) -> str:
    """A tooltip lives in an HTML attribute; quotes and angle brackets break it."""
    return (str(text)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", " ")
            .strip())


def _resource_line(resource: dict, sources: dict) -> str:
    label = str(resource.get("label") or "").strip() or "(unnamed)"
    source_id = resource.get("source_id")
    kind = _KIND_MARK.get(str(resource.get("kind") or ""), "read")
    triage = str(resource.get("scope_triage") or "")
    locator = str(resource.get("locator") or "").strip()
    angle = str(resource.get("angle") or "").strip()
    detail = str(resource.get("angle_detail") or "").strip()

    title = label
    if detail:
        # The hover carries the long judgment. Keeping the short angle in the
        # visible text means the line still says something without it.
        title = f'<span title="{_escape_attr(detail)}">{label}</span>'

    parts = [f"- **{title}** · `{kind}`"]
    if triage:
        parts.append(f" · {triage}")
    if source_id:
        source = sources.get(source_id)
        source_title = (source.get("title") if isinstance(source, dict) else None) or source_id
        parts.append(f" · [{source_title}](source-index.md#{source_id})")
    line = "".join(parts)
    if locator:
        line += f"\n  - where: {locator}"
    if angle:
        line += f"\n  - angle: {angle}"
    elif detail:
        line += "\n  - angle: (hover the title)"
    else:
        line += "\n  - angle: **not recorded** — this row does not say why it is here"
    return line


def build_study_plan_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Study plans — every stage, every option, every angle",
                       generated_at)
    lines += [
        "",
        "Each unit's current study map, expanded. Under every stage is the full set",
        "of routed materials — not a chosen few — with the exact place to start and",
        "the angle that material takes. **Hover a material's name to read the long",
        "form of its angle.**",
        "",
    ]

    sources = repo.sources
    units_by_module: dict[str, list] = {}
    for unit in repo.units.values():
        units_by_module.setdefault(unit.module_id, []).append(unit)

    total_units = 0
    total_stages = 0
    total_rows = 0
    without_angle = 0

    body: list[str] = []
    for module_id in sorted(units_by_module):
        module = repo.modules.get(module_id)
        module_title = (module.data.get("title") if module and hasattr(module, "data")
                        else None) or module_id
        module_lines: list[str] = []
        for unit in sorted(units_by_module[module_id],
                           key=lambda u: (u.data.get("order") or 0, u.id)):
            map_id = unit.data.get("current_study_map")
            study_map = repo.study_maps.get(map_id) if map_id else None
            if study_map is None:
                continue
            stages = study_map.data.get("stages") or []
            if not stages:
                continue
            total_units += 1
            module_lines += [
                "",
                f"### {unit.data.get('title') or unit.id}",
                "",
                f"`{unit.id}` · study map `{map_id}` · "
                f"{len(stages)} stage(s)",
            ]
            for stage in stages:
                total_stages += 1
                resources = [r for r in (stage.get("resources") or [])
                             if isinstance(r, dict)]
                resources.sort(key=lambda r: (
                    _TRIAGE_ORDER.get(str(r.get("scope_triage") or ""), 9),
                    str(r.get("label") or ""),
                ))
                module_lines += [
                    "",
                    f"#### {stage.get('number', '')}. {stage.get('title') or stage.get('id')}",
                    "",
                    f"{stage.get('objective') or ''}",
                    "",
                ]
                if not resources:
                    module_lines.append("*(no material routed to this stage)*")
                    continue
                for resource in resources:
                    total_rows += 1
                    if not str(resource.get("angle") or "").strip():
                        without_angle += 1
                    module_lines.append(_resource_line(resource, sources))
        if module_lines:
            body += ["", f"## {module_title}", "", f"`{module_id}`"] + module_lines

    lines += [
        "## At a glance",
        "",
        f"- units with a current study map: **{total_units}**",
        f"- stages: **{total_stages}**",
        f"- material options across all stages: **{total_rows}**",
        f"- options with no angle recorded: **{without_angle}**"
        + (" — every option says why it is there" if not without_angle else ""),
        "",
        "Coverage is reported rather than hidden: an option with no angle is a row",
        "that names a source and does not say what it is for, and the count above is",
        "the honest size of that debt.",
    ]
    lines += body
    return "\n".join(lines)
