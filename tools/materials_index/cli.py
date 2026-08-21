"""Entry point: build every surface and report what was written."""

from __future__ import annotations

import json
from datetime import datetime

from .config import DOMAIN_LABELS, HTML_ENABLED, MATERIALS, SOURCES_DOMAIN_ORDER
from .page import PAGE
from .registry import (
    domain_for_online,
    human_size,
    load_collection_domains,
    load_flat_map,
    load_sources,
    type_label,
)
from .render import esc, render_domain_files, render_domain_sources
from .reports import build_files_listing, build_readme
from .tree import (
    build_tree,
    classify_source_node,
    collect_leaves,
    collect_source_nodes,
    collect_types,
)


def main():
    if not MATERIALS.is_dir():
        raise SystemExit(f"materials not found at {MATERIALS}")
    sources = load_sources()
    flatmap = load_flat_map()
    coll_domains = load_collection_domains()
    roots = build_tree(sources, flatmap)
    roots_by_name = {r["name"]: r for r in roots}

    local_ids = set(flatmap.values())
    online_ids = [sid for sid in sources if sid not in local_ids]

    online_by_domain: dict[str, list] = {}
    missing_by_domain: dict[str, list] = {}
    for sid in online_ids:
        dom = domain_for_online(sid, coll_domains)
        (online_by_domain if sources[sid].get("url") else missing_by_domain).setdefault(dom, []).append(sources[sid])

    # flat-search leaves: local files (once) + online + missing
    leaves: list[dict] = []
    for r in roots:
        label = DOMAIN_LABELS.get(r["name"], (r["name"], ""))[0]
        collect_leaves(r, [label], leaves)
    for dom, ms in online_by_domain.items():
        label = DOMAIN_LABELS.get(dom, (dom, ""))[0]
        for m in ms:
            leaves.append({"n": m["title"], "c": f"{label} ▸ Online", "h": m["url"],
                           "k": "online", "t": m.get("type", ""), "s": 0, "a": 0,
                           "q": f"{m['title']} {m.get('blob','')}".lower()})
    for dom, ms in missing_by_domain.items():
        label = DOMAIN_LABELS.get(dom, (dom, ""))[0]
        for m in ms:
            leaves.append({"n": m["title"], "c": f"{label} ▸ Missing URL", "h": "",
                           "k": "missing", "t": m.get("type", ""), "s": 0, "a": 0,
                           "q": f"{m['title']} {m.get('blob','')}".lower()})

    nlocal_files = sum(r["nfiles"] for r in roots)
    nsupport = sum(r["nsupport"] for r in roots)
    ncontent = nlocal_files - nsupport
    total = sum(r["bytes"] for r in roots)
    n_online = sum(len(v) for v in online_by_domain.values())
    n_missing = sum(len(v) for v in missing_by_domain.values())
    types = collect_types(sources, local_ids, online_ids)

    chips = "".join(f'<button class="chip" data-type="{esc(t)}" aria-pressed="false">'
                    f'{esc(type_label(t))}</button>' for t in types)
    summary = (f"{len(local_ids)} local sources · {n_online} online · {n_missing} missing URLs · "
               f"{ncontent} files ({nsupport} support hidden) · {human_size(total)}")

    # classify local sources -> module coursework vs library (books re-homed)
    all_src: list[dict] = []
    for r in roots:
        collect_source_nodes(r, all_src)
    modules_by_domain: dict[str, dict[str, list]] = {}
    library_local_by_domain: dict[str, list] = {}
    for n in all_src:
        dom, mod = classify_source_node(n)
        if mod:
            modules_by_domain.setdefault(dom, {}).setdefault(mod, []).append(n)
        else:
            library_local_by_domain.setdefault(dom, []).append(n)

    # Sources view: each domain = Modules + Library-by-type (Books re-homed)
    src_sections = []
    for dom in SOURCES_DOMAIN_ORDER:
        html_sec = render_domain_sources(
            dom, roots_by_name.get(dom),
            modules_by_domain.get(dom, {}),
            library_local_by_domain.get(dom, []),
            online_by_domain.get(dom, []),
            missing_by_domain.get(dom, []))
        if html_sec:
            src_sections.append(html_sec)
    view_sources = "".join(src_sections)

    # Files view: physical filesystem only
    view_files = "".join(render_domain_files(r) for r in roots)

    leaves_json = json.dumps(leaves, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE
            .replace("⟪SUMMARY⟫", esc(summary))
            .replace("⟪DATE⟫", datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("⟪CHIPS⟫", chips)
            .replace("⟪VIEWSOURCES⟫", view_sources)
            .replace("⟪VIEWFILES⟫", view_files)
            .replace("⟪LEAVES⟫", leaves_json))

    if HTML_ENABLED:
        (MATERIALS / "INDEX.html").write_text(page, encoding="utf-8")
        print(f"  wrote materials/INDEX.html  ({len(page)//1024} KB)")
    else:
        stale = MATERIALS / "INDEX.html"
        if stale.exists():
            # Tidying a retired artifact must never abort the rebuild. materials/
            # is routinely reached through mounts that allow writes but forbid
            # unlink, and the file can also be held open by a viewer; an
            # unhandled error here kills the catalogue *before* README.md and
            # FILES.txt are written, so the fix silently ages out the very index
            # that tells you what is unregistered.
            try:
                stale.unlink()
                print("  removed stale materials/INDEX.html (retired 2026-08-03)")
            except OSError as exc:
                print(f"  NOTE could not remove stale materials/INDEX.html "
                      f"({exc.strerror}) — delete it by hand; continuing")
    (MATERIALS / "README.md").write_text(
        build_readme(modules_by_domain, library_local_by_domain, online_by_domain,
                     missing_by_domain, roots_by_name, len(local_ids), n_online,
                     n_missing, ncontent, nsupport, total), encoding="utf-8")
    files_txt = build_files_listing(roots)
    (MATERIALS / "FILES.txt").write_text(files_txt, encoding="utf-8")
    print("  wrote materials/README.md")
    print(f"  wrote materials/FILES.txt  ({files_txt.count(chr(10)) - 7} unregistered files)")
    print(f"  {summary}")
