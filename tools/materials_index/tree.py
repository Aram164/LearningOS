"""Walking the materials tree into domains, leaves and loose files."""

from __future__ import annotations

from .config import ARCHIVE_RE, ASSET_DIRS, BOOKS_SUBFOLDER_DOMAIN, DOMAIN_ORDER, HARD_SUPPORT_EXT, MATERIALS, MODULE_DOMAINS, SKIP_DIRS, SKIP_FILES
from .render import href_for

def build_tree(sources, flatmap):
    """Physical tree; registered-source context inherited into nested items.

    Each file gets ``support`` (web/font asset — hidden by default) and
    ``archived`` flags; counts split content vs support.
    """

    def node_for(path, inherited, archived_ctx, asset_ctx):
        rel = str(path.relative_to(MATERIALS))
        sid = flatmap.get(rel)
        meta = sources.get(sid) if sid else None
        ctx = ({
            "id": sid,
            "title": meta.get("title") if meta else None,
            "type": (meta.get("type", "") if meta else ""),
            "url": (meta.get("url", "") if meta else ""),
            "blob": (meta.get("blob", "") if meta else ""),
        } if sid else inherited)

        own_archived = archived_ctx or bool(ARCHIVE_RE.search(path.name))
        own_asset = asset_ctx or (path.name.lower() in ASSET_DIRS)

        node = {
            "name": path.name, "rel": rel, "source_id": sid,
            "title": meta.get("title") if meta else None,
            "stype": (ctx.get("type", "") if ctx else ""),
            "url": meta.get("url", "") if meta else "",
            "org": meta.get("organization", "") if meta else "",
            "year": meta.get("year") if meta else None,
            "authors": meta.get("authors") if meta else None,
            "ctx": ctx, "archived": own_archived,
            "dirs": [], "files": [], "nfiles": 0, "nsupport": 0, "bytes": 0,
        }
        for e in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if e.name.startswith(".") or e.name in SKIP_DIRS or e.name in SKIP_FILES:
                continue
            if e.is_dir():
                child = node_for(e, ctx, own_archived, own_asset)
                node["dirs"].append(child)
                node["nfiles"] += child["nfiles"]
                node["nsupport"] += child["nsupport"]
                node["bytes"] += child["bytes"]
            elif e.is_file():
                try:
                    size = e.stat().st_size
                except OSError:
                    size = 0
                ext = e.suffix.lower().lstrip(".")
                support = ext in HARD_SUPPORT_EXT or own_asset
                node["files"].append({
                    "name": e.name, "rel": str(e.relative_to(MATERIALS)),
                    "ext": ext, "size": size,
                    "support": support, "archived": own_archived,
                })
                node["nfiles"] += 1
                node["nsupport"] += 1 if support else 0
                node["bytes"] += size
        node["dirs"].sort(key=lambda d: (d["archived"], d["name"].lower()))
        return node

    roots = []
    for name in DOMAIN_ORDER:
        p = MATERIALS / name
        if p.is_dir():
            roots.append(node_for(p, None, False, False))
    for p in sorted(MATERIALS.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name not in DOMAIN_ORDER and not p.name.startswith(".") \
                and p.name not in SKIP_DIRS:
            roots.append(node_for(p, None, False, False))
    return roots


def empty_domain(name):
    return {"name": name, "dirs": [], "files": [], "nfiles": 0, "nsupport": 0,
            "bytes": 0, "ctx": None, "archived": False, "source_id": None,
            "title": None, "stype": "", "url": "", "org": "", "year": None,
            "authors": None}


def collect_leaves(node, crumb, out):
    ctype = (node["ctx"] or {}).get("type", "") or ""
    cblob = (node["ctx"] or {}).get("blob", "") or ""
    for f in node["files"]:
        out.append({
            "n": f["name"], "c": " ▸ ".join(crumb), "h": href_for(f["rel"]),
            "k": "local", "t": ctype, "s": 1 if f["support"] else 0,
            "a": 1 if f["archived"] else 0,
            "q": f"{f['name']} {' '.join(crumb)} {f['rel']} {cblob}".lower(),
        })
    for d in node["dirs"]:
        label = d["title"] if d["source_id"] else d["name"]
        collect_leaves(d, crumb + [label], out)


def collect_source_nodes(node, acc):
    if node["source_id"]:
        acc.append(node)
        return
    for d in node["dirs"]:
        collect_source_nodes(d, acc)


def classify_source_node(node):
    """(view_domain, module_or_None) for a LOCAL registered-source folder."""
    parts = node["rel"].split("/")
    top = parts[0]
    if top == "Books":
        sub = parts[1] if len(parts) > 1 else ""
        return BOOKS_SUBFOLDER_DOMAIN.get(sub, "ML"), None
    if top in MODULE_DOMAINS:
        return top, (parts[1] if len(parts) > 1 else None)
    return top, None


def collect_types(sources, local_ids, online_ids):
    types = set()
    for sid in list(local_ids) + list(online_ids):
        t = (sources.get(sid) or {}).get("type")
        if t:
            types.add(t)
    return sorted(types)


def collect_loose_files(node, out):
    """Relative paths of UNREGISTERED (loose) content files: everything not
    inside a registered source's folder, support assets skipped. Mirrors
    render_unregistered's pruning (registered subtrees are cut whole)."""
    for f in node["files"]:
        if not f["support"]:
            out.append(f["rel"])
    for d in node["dirs"]:
        if d["source_id"]:
            continue
        collect_loose_files(d, out)
