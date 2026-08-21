"""HTML fragment rendering for the retired INDEX.html surface."""

from __future__ import annotations

import html
from urllib.parse import quote

from .config import DOMAIN_LABELS, MODULE_LABEL, TYPE_GROUP, TYPE_GROUP_ORDER
from .registry import _authors_str, human_size, type_label


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def href_for(rel: str) -> str:
    return "/".join(quote(part) for part in rel.split("/"))


def searchable(*parts) -> str:
    return esc(" ".join(p for p in parts if p).lower())


def link_out(url: str) -> str:
    if not url:
        return ""
    return (f'<a class="ext-link-btn" href="{esc(url)}" target="_blank" '
            f'rel="noopener" title="{esc(url)}" onclick="event.stopPropagation()">↗ link</a>')


def ext_badge(ext: str) -> str:
    return f'<span class="ext ext-{esc(ext or "x")}">{esc(ext or "file")}</span>'


def render_files(files, ctx):
    rows = []
    for f in files:
        s = searchable(f["name"], (ctx or {}).get("title", ""), f["rel"], (ctx or {}).get("blob", ""))
        cls = "file leaf" + (" support" if f["support"] else "")
        badge = ext_badge(f["ext"])
        arch = ' <span class="badge badge-archived">archived</span>' if f["archived"] else ""
        rows.append(
            f'<a class="{cls}" data-s="{s}" data-kind="local" '
            f'data-type="{esc((ctx or {}).get("type") or "unregistered")}" '
            f'data-support="{1 if f["support"] else 0}" data-archived="{1 if f["archived"] else 0}" '
            f'href="{href_for(f["rel"])}" title="{esc(f["rel"])}">'
            f'{badge}<span class="fn">{esc(f["name"])}</span>{arch}'
            f'<span class="sz">{human_size(f["size"])}</span></a>'
        )
    return "".join(rows)


def render_online_entry(m, kind):
    url = m.get("url") or ""
    typ = m.get("type") or "link"
    authors = _authors_str(m.get("authors"))
    meta_bits = " · ".join(x for x in [authors, str(m.get("year") or "")] if x)
    s = searchable(m.get("title") or m.get("id"), m.get("blob", ""))
    fn = esc(m.get("title") or m.get("id"))
    metahtml = f'<span class="src-meta">{esc(meta_bits)}</span>' if meta_bits else ""
    if kind == "online" and url:
        badge = '<span class="ext ext-link">link</span>'
        return (f'<a class="file leaf" data-s="{s}" data-kind="online" data-type="{esc(typ)}" '
                f'data-support="0" data-archived="0" href="{esc(url)}" target="_blank" '
                f'rel="noopener" title="{esc(url)}">{badge}<span class="fn">{fn}</span>'
                f'{metahtml}<span class="sz">{esc(type_label(typ))} ↗</span></a>')
    badge = '<span class="ext ext-missing">no url</span>'
    return (f'<span class="file leaf nolink" data-s="{s}" data-kind="missing" data-type="{esc(typ)}" '
            f'data-support="0" data-archived="0" title="registered — no URL yet">{badge}'
            f'<span class="fn">{fn}</span>{metahtml}'
            f'<span class="sz">{esc(type_label(typ))}</span></span>')


def render_group(title, inner, count, kind, open_default=False):
    oa = " open" if open_default else ""
    return (f'<details class="group group-{kind}" data-s="{esc(title.lower())}"{oa}>'
            f'<summary><span class="fname">{esc(title)}</span>'
            f'<span class="count">{count}</span></summary>'
            f'<div class="body">{inner}</div></details>')


def render_dir(node, depth=0):
    """Generic folder (used inside source cards and the Files-view tree)."""
    is_source = bool(node["source_id"])
    ncontent = node["nfiles"] - node["nsupport"]
    if is_source:
        head = (f'<span class="title">{esc(node["title"] or node["name"])}</span>'
                f'<span class="slug">{esc(node["name"])}</span>')
        if node["stype"]:
            head += f'<span class="badge">{esc(type_label(node["stype"]))}</span>'
        if node["url"]:
            head += link_out(node["url"])
    else:
        head = f'<span class="fname">{esc(node["name"])}</span>'
        if node["archived"]:
            head += ' <span class="badge badge-archived">archived</span>'
    head += f'<span class="count">{ncontent}</span>'

    inner = [render_dir(d, depth + 1) for d in node["dirs"]]
    inner.append(render_files(node["files"], node["ctx"]))
    ds = searchable(node["title"] or "", node["name"], node["rel"], (node["ctx"] or {}).get("blob", ""))
    cls = "dir source" if is_source else "dir"
    return (f'<details class="{cls}" data-s="{ds}"><summary>{head}</summary>'
            f'<div class="body">{"".join(inner)}</div></details>')


def render_source_card(node):
    ncontent = node["nfiles"] - node["nsupport"]
    primary = node["org"] or _authors_str(node["authors"])
    bits = [primary, str(node["year"]) if node["year"] else "",
            type_label(node["stype"]), f"{ncontent} files"]
    metaline = " · ".join(b for b in bits if b)
    head = f'<span class="title">{esc(node["title"] or node["name"])}</span>'
    if node["archived"]:
        head += ' <span class="badge badge-archived">archived</span>'
    if node["url"]:
        head += link_out(node["url"])
    head += f'<span class="count">{ncontent}</span>'
    inner = [render_dir(d, 1) for d in node["dirs"]]
    inner.append(render_files(node["files"], node["ctx"]))
    ds = searchable(node["title"] or "", node["name"], (node["ctx"] or {}).get("blob", ""))
    return (f'<details class="dir source card" data-s="{ds}"><summary>{head}'
            f'<div class="metaline">{esc(metaline)}</div></summary>'
            f'<div class="body">{"".join(inner)}</div></details>')


def render_unregistered(node, depth=1):
    """(html, nloose) for the domain subtree with registered-source subtrees pruned."""
    parts, nloose = [], 0
    for d in node["dirs"]:
        if d["source_id"]:
            continue
        sub_html, sub_n = render_unregistered(d, depth + 1)
        if sub_n:
            head = f'<span class="fname">{esc(d["name"])}</span>'
            if d["archived"]:
                head += ' <span class="badge badge-archived">archived</span>'
            head += f'<span class="count">{sub_n}</span>'
            parts.append(f'<details class="dir" data-s="{searchable(d["name"], d["rel"])}">'
                         f'<summary>{head}</summary><div class="body">{sub_html}</div></details>')
            nloose += sub_n
    parts.append(render_files(node["files"], node["ctx"]))
    nloose += len(node["files"])
    return "".join(parts), nloose


def render_module_folder(module_label, nodes):
    nodes = sorted(nodes, key=lambda n: (n["title"] or n["name"]).lower())
    ncontent = sum(n["nfiles"] - n["nsupport"] for n in nodes)
    head = (f'<span class="fname">{esc(module_label)}</span>'
            f'<span class="badge">module</span>'
            f'<span class="count">{len(nodes)} src · {ncontent} files</span>')
    body = "".join(render_source_card(n) for n in nodes)
    return (f'<details class="dir module" data-s="{searchable(module_label, "module")}">'
            f'<summary>{head}</summary><div class="body">{body}</div></details>')


def render_type_group(group_name, items):
    """items: list of ('card', node) | ('online', meta)."""
    def keyf(it):
        obj = it[1]
        return (obj.get("title") or obj.get("name") or "").lower()
    body = []
    for kind, obj in sorted(items, key=keyf):
        body.append(render_source_card(obj) if kind == "card"
                    else render_online_entry(obj, "online"))
    return render_group(group_name, "".join(body), len(items), "type")


def render_domain_sources(name, phys_node, modules, library_local, online_list, missing_list):
    label, hint = DOMAIN_LABELS.get(name, (name, ""))
    body = []

    # --- Modules section ---------------------------------------------------
    if modules:
        mods = "".join(render_module_folder(MODULE_LABEL.get(m, m), modules[m])
                       for m in sorted(modules, key=str.lower))
        body.append(render_group("Modules", mods, len(modules), "modules"))

    # --- Library — by type -------------------------------------------------
    lib_items: dict[str, list] = {}
    for n in library_local:
        lib_items.setdefault(TYPE_GROUP.get(n["stype"], "Other"), []).append(("card", n))
    for m in online_list:
        lib_items.setdefault(TYPE_GROUP.get(m.get("type", ""), "Other"), []).append(("online", m))
    lib_html = [render_type_group(g, lib_items[g]) for g in TYPE_GROUP_ORDER if lib_items.get(g)]
    if missing_list:
        lib_html.append(render_group(
            "Missing URLs (registered, no link yet)",
            "".join(render_online_entry(m, "missing") for m in
                    sorted(missing_list, key=lambda m: (m.get("title") or "").lower())),
            len(missing_list), "missing"))
    n_lib = sum(len(v) for v in lib_items.values())
    if lib_html:
        body.append(render_group("Library — by type", "".join(lib_html),
                                 n_lib, "library"))

    # --- loose / unregistered files ---------------------------------------
    nloose = 0
    if phys_node is not None:
        unreg_html, nloose = render_unregistered(phys_node)
        if nloose:
            body.append(render_group("Other / unregistered files", unreg_html, nloose, "unreg"))

    if not body:
        return ""
    cparts = []
    if modules:
        cparts.append(f"{len(modules)} modules")
    if n_lib:
        cparts.append(f"{n_lib} materials")
    if missing_list:
        cparts.append(f"{len(missing_list)} missing")
    if nloose:
        cparts.append(f"{nloose} loose")
    counts = " · ".join(cparts) or "—"
    ds = searchable(label, name)
    return (f'<section class="domain" data-s="{ds}"><details open><summary>'
            f'<span class="dlabel">{esc(label)}</span>'
            f'<span class="dhint">{esc(hint)}</span>'
            f'<span class="count">{esc(counts)}</span></summary>'
            f'<div class="body">{"".join(body)}</div></details></section>')


def render_domain_files(node):
    label, hint = DOMAIN_LABELS.get(node["name"], (node["name"], ""))
    inner = [render_dir(d, 1) for d in node["dirs"]]
    inner.append(render_files(node["files"], node["ctx"]))
    ncontent = node["nfiles"] - node["nsupport"]
    extra = f" · {node['nsupport']} support" if node["nsupport"] else ""
    ds = searchable(label, node["name"])
    return (f'<section class="domain" data-s="{ds}"><details open><summary>'
            f'<span class="dlabel">{esc(label)}</span>'
            f'<span class="dhint">{esc(hint)}</span>'
            f'<span class="count">{ncontent} files{extra} · {human_size(node["bytes"])}</span>'
            f'</summary><div class="body">{"".join(inner)}</div></details></section>')
