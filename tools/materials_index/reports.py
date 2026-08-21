"""The plain-text surfaces: README.md and FILES.txt."""

from __future__ import annotations

from .config import DOMAIN_LABELS, MODULE_LABEL, SOURCES_DOMAIN_ORDER, TYPE_GROUP, TYPE_GROUP_ORDER
from .registry import human_size, type_label
from .render import render_unregistered
from .tree import collect_loose_files


def build_files_listing(roots) -> str:
    """materials/FILES.txt (ADR-005): a names-only, grep-able listing of every
    UNREGISTERED file in the materials tree — the Foundations archive and any
    other loose material. Registered sources are deliberately absent (they are
    findable via the registry / source-index / INDEX.html); this file exists so
    "do I own something on X?" is answerable without registering 200+ archive
    files. Promotion path when a hit matters: WORKFLOWS §6a."""
    loose: list[str] = []
    for r in roots:
        collect_loose_files(r, loose)
    loose.sort()
    header = [
        "# GENERATED file - do not edit. Rebuilt by `make materials`",
        "# (tools/build_materials_index.py).",
        "# Unregistered (loose) materials only - registered sources live in the",
        "# registry and source-index. Names-only grep surface; nothing here is",
        "# canonical. Register a file the moment it becomes relevant (WORKFLOWS §6a).",
        f"# {len(loose)} unregistered files.",
        "",
    ]
    return "\n".join(header + loose) + "\n"


def build_readme(modules_by_domain, library_local_by_domain, online_by_domain,
                 missing_by_domain, roots_by_name, nlocal, n_online, n_missing,
                 ncontent, nsupport, total):
    lines = [
        "# Materials — catalogue",
        "",
        "> Plain-text companion to **INDEX.html** (Sources view = Modules + Library-by-type; ",
        "> Files view = raw disk tree; flat search). ",
        f"> {nlocal} local sources · {n_online} online · {n_missing} missing URLs · "
        f"{ncontent} files ({nsupport} support hidden) · {human_size(total)}. ",
        "> Rebuild with `make materials`. Local links in INDEX.html are relative to `materials/`. ",
        "> Unregistered file names are grep-able in `FILES.txt`.",
        "",
    ]

    def src_line(n):
        url = f" — <{n['url']}>" if n["url"] else ""
        typ = f" · {type_label(n['stype'])}" if n["stype"] else ""
        arch = " · archived" if n["archived"] else ""
        lines.append(f"  - **{n['title'] or n['name']}** "
                     f"({n['nfiles'] - n['nsupport']} file(s){typ}{arch}){url}")

    def online_line(m):
        typ = f" · {type_label(m['type'])}" if m.get("type") else ""
        if m.get("url"):
            lines.append(f"  - [{m['title']}]({m['url']}){typ}")
        else:
            lines.append(f"  - {m['title']} — MISSING URL{typ}")

    for dom in SOURCES_DOMAIN_ORDER:
        mods = modules_by_domain.get(dom, {})
        lib = library_local_by_domain.get(dom, [])
        onl = online_by_domain.get(dom, [])
        mis = missing_by_domain.get(dom, [])
        phys = roots_by_name.get(dom)
        loose = render_unregistered(phys)[1] if phys is not None else 0
        if not (mods or lib or onl or mis or loose):
            continue
        label, hint = DOMAIN_LABELS.get(dom, (dom, ""))
        lines.append(f"\n## {label}")
        if hint:
            lines.append(f"*{hint}*  \n")

        if mods:
            lines.append("### Modules")
            for m in sorted(mods, key=str.lower):
                lines.append(f"- **{MODULE_LABEL.get(m, m)}** _(module)_")
                for n in sorted(mods[m], key=lambda n: (n["title"] or n["name"]).lower()):
                    src_line(n)

        buckets: dict[str, list] = {}
        for n in lib:
            buckets.setdefault(TYPE_GROUP.get(n["stype"], "Other"), []).append(("card", n))
        for m in onl:
            buckets.setdefault(TYPE_GROUP.get(m.get("type", ""), "Other"), []).append(("online", m))
        if buckets or mis:
            lines.append("\n### Library — by type")
            for g in TYPE_GROUP_ORDER:
                items = buckets.get(g)
                if not items:
                    continue
                lines.append(f"\n**{g}**")
                for kind, obj in sorted(items, key=lambda it: (it[1].get("title") or it[1].get("name") or "").lower()):
                    src_line(obj) if kind == "card" else online_line(obj)
            if mis:
                lines.append(f"\n**Missing URLs ({len(mis)})**")
                for m in sorted(mis, key=lambda m: (m.get("title") or "").lower()):
                    online_line(m)
        if loose:
            lines.append(f"\n_Plus {loose} loose/unregistered file(s) — see the Files view._")

    lines.append("")
    return "\n".join(lines)
