#!/usr/bin/env python3
"""Build a human-browsable CATALOGUE of the materials tree + the source registry.

RETIRED SURFACE (2026-08-03, ADR-006 addendum 4): ``INDEX.html`` is no longer
written. Browsing sources is the interface layer's job — the Obsidian UI's
Source Explorer reads the same facts out of ``generated/manifest.json`` (which
now carries ``url``, ``material_path``, ``roles`` and ``evaluations``), with
search, facets, evaluations and one-click open. Keeping a second, separately
built browser meant two implementations of "how do I find a source". The
generator below still exists and can emit the page again with
``--html`` if the interface ever regresses; ``README.md`` and ``FILES.txt``
remain as the plain-text/grep surfaces.

Emits into ``LearningOS/materials/``:

* ``INDEX.html`` (only with ``--html``) — a self-contained, searchable page
  with TWO switchable views:
    - **Sources** (default): source-first. Each domain lists its registered
      sources directly as clean, collapsed cards (the ``course/practice-extern``
      storage scaffolding is flattened away); expand a card to see its files.
      Online sources and "Missing URLs" (registered, no link yet) sit in their
      own labelled groups, and loose/unregistered files in another.
    - **Files**: the raw local filesystem tree, for seeing exactly what is on
      disk. Support assets (css/js/fonts/images from web mirrors) are hidden
      until you tick "Show supporting files"; archived folders are badged.
  Domains open by default, everything inside collapsed — the landing screen is
  a scannable map, not a wall.

  Search shows a FLAT, relevance-ranked result list with breadcrumbs (it does
  not explode the tree). Space-separated terms are ANDed; matches are
  highlighted; results page in 200 at a time. Keyboard: ``/`` or ``⌘K`` focus,
  ``↑``/``↓`` move, ``⏎`` open (``⌘⏎`` new tab), ``Esc`` clear. Type chips are
  multi-select; "Online only", "Support files" and "Hide archived" are
  independent toggles. Local links are RELATIVE to this file — keep INDEX.html
  in ``materials/`` or the file links break.
* ``README.md`` — a plain-text / grep-able map of the same content.
* ``FILES.txt`` — names-only listing of every UNREGISTERED file (ADR-005), so
  "do I own something on X?" is grep-able without registering archive dumps.

Neither is canonical. They are pure VIEWS over what is physically on disk plus
the registered sources in ``sources/``. Rebuild any time:

    python tools/build_materials_index.py      # or: make materials

Files are never moved, so ``material://`` URIs, the registry and the .flat farm
keep working. No third-party deps beyond PyYAML (already a repo dependency).
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import yaml

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent                      # LearningOS/repository
MATERIALS = REPO.parent / "materials"    # LearningOS/materials

# INDEX.html was retired 2026-08-03 (the Obsidian Source Explorer replaced it).
# Pass --html to build it anyway; the builder is kept as a fallback, not a
# maintained surface.
HTML_ENABLED = "--html" in sys.argv
SOURCES = REPO / "sources"

SKIP_DIRS = {".flat", ".git", "__pycache__"}
SKIP_FILES = {".DS_Store", "INDEX.html", "README.md", "FILES.txt"}

# A file is a "support asset" (hidden by default) if its extension is web/font
# tech, or if any ancestor folder up to the source root is an asset directory.
HARD_SUPPORT_EXT = {"css", "js", "mjs", "cjs", "mts", "map", "scss", "sass",
                    "less", "woff", "woff2", "ttf", "otf", "eot", "ico", "sample"}
ASSET_DIRS = {"assets", "static", "_static", "_files", "fonts", "font", "css",
              "js", "img", "images", "_resources", "static_shared"}
ARCHIVE_RE = re.compile(r"(older|archive|deprecated|superseded|backup|previous"
                        r"|(?:^|[-_])old(?:[-_]|$))", re.I)

TYPE_LABEL = {"lecture": "Lecture", "book": "Book", "course": "Course",
              "paper": "Paper", "website": "Website", "video": "Video",
              "software": "Software", "documentation": "Docs", "other": "Other"}

DOMAIN_LABELS = {
    "ML": ("Machine Learning", "AML + AMLS course materials (slides, exams, papers, notes)"),
    "Math": ("Mathematics", "Analysis (M2.1) + Statistik & Datenanalyse — Skript, slides, drill"),
    "CS-Theory": ("CS Theory", "Algo 2 / AlgoDat II — practice exams"),
    "Programming": ("Programming", "Python, Rust, Git working references"),
    "Books": ("Books — reference library", "Textbooks grouped by field (analysis, stats, ml, algorithms)"),
    "Degree": ("Degree admin", "StuPO / regulations"),
    "Foundations": ("Foundations archive", "Undergrad / general reference — NOT registered sources, browse only"),
    "DegreePlanning": ("Degree planning — future-module anchors",
                       "Cross-module carrier books & courses registered for modules you'll take later (browse/plan)"),
    "Online": ("Online — other registered links", "Registered external sources not tied to a subject bucket"),
}
DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming", "Books", "Degree", "Foundations"]
EXTRA_ONLINE_ORDER = ["DegreePlanning", "Online"]

COLLECTION_DOMAIN = {
    "ml-bookshelf": "ML", "ml-lecture-series": "ML", "ml-explainers": "ML",
    "ml-broaden-later": "ML", "papers-shelf": "ML",
    "ml-systems-bookshelf": "ML", "ml-systems-lecture-series": "ML",
    "math-bookshelf": "Math", "math-lecture-series": "Math",
    "algorithms-bookshelf": "CS-Theory", "algorithms-lecture-series": "CS-Theory",
    "programming-bookshelf": "Programming", "programming-video-courses": "Programming",
    "python-internals-shelf": "Programming", "project-toolbox": "Programming",
    "degree-module-anchors": "DegreePlanning",
}
LOW_PRIORITY_COLLECTIONS = {"degree-module-anchors"}

ONLINE_DOMAIN_OVERRIDE = {
    "source-caltech-lfd": "ML",
    "source-cs229-problem-sets": "ML",
    "source-islp-community-solutions": "ML",
    "source-mit-6034-quizzes": "ML",
    "source-mit-6006": "CS-Theory",
    "source-sad-uebungen": "Math",
}

# ---- Sources-view structure: each domain = Modules + Library-by-type -------
# Local source folders physically under one of these domains are MODULE
# coursework; the module is the next path segment (ML/AML/…, Math/SaD/…).
MODULE_DOMAINS = {"ML", "Math", "CS-Theory", "Programming"}
# Shared Books/<subfield>/ folders are re-homed into their subject domain's
# Library (the standalone "Books" domain is dropped from the Sources view).
BOOKS_SUBFOLDER_DOMAIN = {"analysis": "Math", "stats": "Math", "ml": "ML",
                          "algorithms": "CS-Theory"}
MODULE_LABEL = {"python": "Python", "git": "Git", "rust": "Rust"}
# fine-grained source type -> display group used inside "Library — by type"
TYPE_GROUP = {"book": "Books", "course": "Courses & lectures", "lecture": "Courses & lectures",
              "video": "Videos", "paper": "Papers", "documentation": "Docs",
              "software": "Software", "website": "Websites", "other": "Other", "": "Other"}
TYPE_GROUP_ORDER = ["Books", "Courses & lectures", "Videos", "Papers", "Docs",
                    "Software", "Websites", "Other"]
# Sources view domain order (NO standalone Books — its books re-home by subject).
SOURCES_DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming", "Degree",
                        "Foundations", "DegreePlanning", "Online"]


# ------------------------------------------------------------ registry loading

def _authors_str(a) -> str:
    if isinstance(a, list):
        return ", ".join(str(x) for x in a)
    return str(a) if a else ""


def _pick_url(rec: dict) -> str:
    """The registered link for a source: url/homepage, else first http identifier."""
    u = rec.get("url") or rec.get("homepage")
    if u:
        return u
    idf = rec.get("identifiers")
    if isinstance(idf, dict):
        for v in idf.values():
            if str(v).startswith("http"):
                return str(v)
    return ""


def _source_blob(rec: dict) -> str:
    parts = [
        rec.get("id"), rec.get("title"), rec.get("type"), rec.get("url"),
        rec.get("organization"), str(rec.get("year") or ""), _authors_str(rec.get("authors")),
    ]
    idf = rec.get("identifiers")
    if isinstance(idf, dict):
        for k, v in idf.items():
            parts += [str(k), str(v)]
    elif idf:
        parts.append(str(idf))
    return " ".join(p for p in parts if p)


def load_sources() -> dict[str, dict]:
    out: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("id") and node.get("title"):
                sid = node["id"]
                if sid not in out:
                    out[sid] = {
                        "id": sid,
                        "title": node.get("title"),
                        "type": node.get("type", ""),
                        "url": _pick_url(node),
                        "authors": node.get("authors"),
                        "organization": node.get("organization", ""),
                        "year": node.get("year"),
                        "identifiers": node.get("identifiers"),
                    }
                    out[sid]["blob"] = _source_blob(out[sid])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for yf in SOURCES.rglob("*.yaml"):
        if yf.parent.name == "collections":
            continue
        try:
            walk(yaml.safe_load(yf.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! skipped {yf.name}: {exc}")
    return out


def load_collection_domains() -> dict[str, str]:
    coll = SOURCES / "collections"
    out: dict[str, str] = {}
    if not coll.is_dir():
        return out
    files = sorted(coll.glob("*.yaml"),
                   key=lambda p: (p.stem in LOW_PRIORITY_COLLECTIONS, p.stem))
    for cf in files:
        dom = COLLECTION_DOMAIN.get(cf.stem)
        if not dom:
            continue
        try:
            data = yaml.safe_load(cf.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        for e in (data.get("entries") or data.get("sources") or []):
            sid = (e.get("source") or e.get("id")) if isinstance(e, dict) else e
            if sid:
                out.setdefault(sid, dom)
    return out


def domain_for_online(sid: str, coll_domains: dict[str, str]) -> str:
    return ONLINE_DOMAIN_OVERRIDE.get(sid) or coll_domains.get(sid) or "Online"


def load_flat_map() -> dict[str, str]:
    flat = MATERIALS / ".flat"
    out: dict[str, str] = {}
    if not flat.is_dir():
        return out
    for link in flat.iterdir():
        if not link.is_symlink():
            continue
        resolved = (flat / os.readlink(link)).resolve()
        try:
            rel = resolved.relative_to(MATERIALS.resolve())
        except ValueError:
            continue
        out[str(rel)] = link.name
    return out


def human_size(n: int) -> str:
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB"):
        if n < step:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= step
    return f"{n:.1f} TB"


def type_label(t: str) -> str:
    return TYPE_LABEL.get(t, t.title() if t else "")


# -------------------------------------------------------------- tree building

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


# ------------------------------------------------------------- flat-search data

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


# ---------------------------------------------------------------- HTML render

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


def collect_types(sources, local_ids, online_ids):
    types = set()
    for sid in list(local_ids) + list(online_ids):
        t = (sources.get(sid) or {}).get("type")
        if t:
            types.add(t)
    return sorted(types)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Materials — catalogue</title>
<style>
/* ---- tokens: one accent, a neutral ramp, nothing else --------------------
   Contrast-checked (WCAG 2.1 AA, both modes):
     ink 17.3 / 13.9 · ink-2 6.9 / 6.7 · ink-3 5.1 / 5.2 (4.7 / 4.8 on panel-2)
     accent-on-soft 6.9 / 7.6 · amber-on-soft 5.2 / 6.7 · mark 15.1 / 8.3
   --line is a decorative divider only. Anything that bounds a CONTROL
   (input, chip, button) uses --ctl, which clears 3:1 per SC 1.4.11.        */
:root{
 --bg:#fbfbfa; --panel:#fff; --panel-2:#f7f7f5;
 --ink:#1b1b19; --ink-2:#5a5a54; --ink-3:#6f6f68;
 --line:#e8e7e3; --line-2:#f1f0ec; --ctl:#949490;
 --accent:#4338ca; --accent-soft:#eeeefb; --accent-line:#c9c7f2;
 --amber:#965612; --amber-soft:#fbf3e2;
 --hit:#fdf0b8;
 --r:10px; --r-sm:7px;
 --sh:0 1px 2px rgba(20,20,18,.04);
}
@media(prefers-color-scheme:dark){:root{
 --bg:#141416; --panel:#1c1c1f; --panel-2:#232327;
 --ink:#e8e8ea; --ink-2:#a2a2a8; --ink-3:#8e8e95;
 --line:#2a2a2f; --line-2:#232327; --ctl:#67676c;
 --accent:#a5b4fc; --accent-soft:#242438; --accent-line:#3b3b6b;
 --amber:#d7ac63; --amber-soft:#332a16;
 --hit:#4a4113;
 --sh:none;
}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
 font:14.5px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
 -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}

/* ---- header -------------------------------------------------------------- */
header{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line)}
.hrow{display:flex;align-items:center;gap:14px;padding:13px 0 0}
h1{margin:0;font-size:15px;font-weight:640;letter-spacing:-.01em;white-space:nowrap}
.stat{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}
.seg{display:inline-flex;background:var(--panel-2);border:1px solid var(--ctl);
 border-radius:8px;padding:2px;gap:2px}
.seg button{font:inherit;font-size:12.5px;padding:5px 12px;border:0;border-radius:6px;
 background:transparent;color:var(--ink-2);cursor:pointer;transition:background .12s,color .12s}
.seg button:hover{color:var(--ink)}
.seg button[aria-selected="true"]{background:var(--panel);color:var(--ink);font-weight:560;box-shadow:var(--sh)}

.searchbar{position:relative;display:flex;align-items:center;margin:11px 0 0}
.searchbar svg{position:absolute;left:12px;width:15px;height:15px;stroke:var(--ink-3);
 fill:none;stroke-width:2;pointer-events:none}
#q{width:100%;padding:10px 78px 10px 35px;font:inherit;font-size:14px;
 border:1px solid var(--ctl);border-radius:var(--r);background:var(--panel);color:var(--ink);
 transition:border-color .12s,box-shadow .12s}
#q::placeholder{color:var(--ink-3)}
#q:focus{outline:0;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.kbd{position:absolute;right:11px;font-size:11px;color:var(--ink-3);border:1px solid var(--ctl);
 border-radius:5px;padding:1px 6px;background:var(--panel-2);pointer-events:none;
 font-family:ui-monospace,Menlo,monospace}
.clr{position:absolute;right:9px;border:0;background:var(--panel-2);color:var(--ink-2);
 width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:12px;line-height:1;display:none}
.clr:hover{background:var(--line);color:var(--ink)}

.chiprow{display:flex;align-items:center;gap:6px;padding:10px 0 11px;flex-wrap:wrap}
/* controls: >=24px high per SC 2.5.8, >=3:1 border per SC 1.4.11 */
.chip{font:inherit;font-size:12px;padding:5px 11px;border-radius:999px;border:1px solid var(--ctl);
 background:var(--panel);color:var(--ink-2);cursor:pointer;user-select:none;white-space:nowrap;
 min-height:26px;transition:background .12s,color .12s,border-color .12s}
.chip:hover{border-color:var(--ink-2);color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);
 color:var(--accent);font-weight:560}
.sep{width:1px;height:18px;background:var(--ctl);margin:0 4px}
.tools{margin-left:auto;display:flex;gap:6px}
button.t{font:inherit;font-size:12px;padding:5px 10px;border-radius:var(--r-sm);min-height:26px;
 border:1px solid var(--ctl);background:var(--panel);color:var(--ink-2);cursor:pointer}
button.t:hover{border-color:var(--ink-2);color:var(--ink)}

/* ---- main ---------------------------------------------------------------- */
main{padding:18px 0 80px}
.domain{margin:0 0 12px}
details{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);
 margin:0 0 8px;box-shadow:var(--sh)}
details details{border:0;border-top:1px solid var(--line-2);border-radius:0;margin:0;
 background:transparent;box-shadow:none}
summary{cursor:pointer;padding:9px 13px;list-style:none;display:flex;align-items:center;
 gap:8px;flex-wrap:wrap;border-radius:var(--r)}
summary::-webkit-details-marker{display:none}
summary:hover{background:var(--panel-2)}
details details>summary{border-radius:0}
summary::before{content:"";width:0;height:0;flex:none;margin-top:1px;
 border:4px solid transparent;border-left:5px solid var(--ink-3);
 transition:transform .14s ease;align-self:flex-start;margin-top:6px}
details[open]>summary::before{transform:rotate(90deg) translateX(1px)}
.dlabel{font-weight:640;font-size:14.5px;letter-spacing:-.005em}
.dhint{color:var(--ink-3);font-size:11.5px}
.card>summary{align-items:flex-start}
.title{font-weight:560}
.metaline{flex-basis:100%;color:var(--ink-3);font-size:11.5px;padding-left:17px;margin-top:1px}
.slug{color:var(--ink-3);font-size:11.5px;font-family:ui-monospace,Menlo,monospace}
.fname{font-weight:530}
.badge{font-size:11px;background:var(--panel-2);color:var(--ink-2);padding:1px 7px;
 border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.badge-archived{color:var(--ink-3)}
.group-modules>summary,.group-library>summary{background:var(--panel-2)}
.group-modules>summary .fname,.group-library>summary .fname{font-weight:620}
.group-type>summary .fname,.module>summary .fname{font-weight:580}
.group-missing>summary .fname{color:var(--amber)}
.group-unreg>summary .fname{color:var(--ink-3)}
.ext-link-btn{font-size:11px;color:var(--accent);text-decoration:none;border:1px solid var(--accent-line);
 border-radius:999px;padding:2px 8px;white-space:nowrap;background:var(--accent-soft)}
.ext-link-btn:hover{filter:brightness(.97)}
.count{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 align-self:flex-start;margin-top:2px;font-variant-numeric:tabular-nums}
.body{padding:1px 8px 7px 19px}
details details .body{padding-left:15px}

a.file,span.file{display:flex;align-items:center;gap:9px;padding:6px 9px;border-radius:var(--r-sm);
 text-decoration:none;color:var(--ink);font-size:13.5px;min-height:28px}
a.file:hover{background:var(--accent-soft)}
span.file.nolink{color:var(--ink-2)}
.fn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.src-meta{color:var(--ink-3);font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sz{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 font-variant-numeric:tabular-nums}

/* file-type tags: monochrome by default; colour reserved for real signals */
.ext{font-size:11px;text-transform:uppercase;letter-spacing:.03em;font-weight:600;
 color:var(--ink-3);background:transparent;border:1px solid var(--line);border-radius:4px;
 padding:0 5px;min-width:42px;text-align:center;flex:none;
 font-family:ui-monospace,Menlo,monospace}
.ext-link{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.ext-missing{color:var(--amber);border-color:var(--amber);background:var(--amber-soft)}

mark{background:var(--hit);color:inherit;border-radius:2px;padding:0 1px}
.hide{display:none!important}
.empty{color:var(--ink-3);padding:44px 20px;text-align:center;font-size:13.5px;line-height:1.7}
.empty kbd,footer kbd{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;
 border:1px solid var(--line);border-radius:4px;padding:1px 5px;background:var(--panel-2)}

/* ---- flat search results ------------------------------------------------- */
#results{padding-top:2px}
.reshdr{color:var(--ink-3);font-size:11.5px;padding:2px 2px 8px;
 display:flex;align-items:center;gap:10px;font-variant-numeric:tabular-nums}
.res{display:flex;align-items:baseline;gap:11px;padding:7px 10px;border-radius:var(--r-sm);
 text-decoration:none;color:var(--ink);scroll-margin:120px}
.res+.res{border-top:1px solid var(--line-2)}
.res:hover{background:var(--panel-2)}
.res.sel{background:var(--accent-soft);box-shadow:inset 2px 0 0 var(--accent)}
.res .rn{font-weight:540;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 max-width:52%;font-size:13.5px}
.res .rc{color:var(--ink-3);font-size:11.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.res .rk{margin-left:auto;font-size:11px;text-transform:uppercase;letter-spacing:.03em;
 color:var(--ink-3);border:1px solid var(--line);border-radius:4px;padding:0 5px;
 white-space:nowrap;flex:none;font-family:ui-monospace,Menlo,monospace}
.res .rk.online{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.res .rk.missing{color:var(--amber);border-color:var(--amber);background:var(--amber-soft)}
.more{width:100%;margin-top:10px;padding:9px;font:inherit;font-size:12.5px;cursor:pointer;
 border:1px dashed var(--ctl);border-radius:var(--r-sm);background:transparent;color:var(--ink-2)}
.more:hover{border-color:var(--ink-2);color:var(--ink)}

footer{border-top:1px solid var(--line);color:var(--ink-3);font-size:11.5px;
 padding:16px 0 40px;line-height:1.8}
footer code{font-family:ui-monospace,Menlo,monospace;background:var(--panel-2);
 border:1px solid var(--line);border-radius:4px;padding:0 4px}

@media(max-width:720px){
 .wrap{padding:0 14px}
 .hrow{flex-wrap:wrap;gap:10px}
 .stat{margin-left:0;flex-basis:100%;white-space:normal}
 .chiprow{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
 .chiprow::-webkit-scrollbar{display:none}
 .tools{margin-left:8px}
 .res .rn{max-width:100%}
 .kbd{display:none}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
</style></head>
<body>
<header><div class="wrap">
 <div class="hrow">
  <h1>Materials</h1>
  <div class="seg" role="tablist" aria-label="View">
   <button id="vSources" role="tab" aria-selected="true">Sources</button>
   <button id="vFiles" role="tab" aria-selected="false">Files</button>
  </div>
  <span class="stat">⟪SUMMARY⟫</span>
 </div>
 <div class="searchbar">
  <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
  <input id="q" type="search" autocomplete="off" spellcheck="false"
   placeholder="Search titles, filenames, folders, authors, URLs — space-separated terms all must match"
   aria-label="Search materials" autofocus>
  <kbd class="kbd" id="kbd">/</kbd>
  <button class="clr" id="clear" aria-label="Clear search" title="Clear (Esc)">✕</button>
 </div>
 <div class="chiprow" role="group" aria-label="Filters">
  <button class="chip" data-type="*" aria-pressed="true">All</button>⟪CHIPS⟫
  <span class="sep" aria-hidden="true"></span>
  <button class="chip" id="onlineChip" aria-pressed="false">Online only</button>
  <button class="chip" id="supportChip" aria-pressed="false">Support files</button>
  <button class="chip" id="archChip" aria-pressed="false">Hide archived</button>
  <span class="tools">
   <button class="t" id="expand" title="Expand everything in this view">Expand</button>
   <button class="t" id="collapse" title="Collapse back to the domain map">Collapse</button>
  </span>
 </div>
</div></header>
<main class="wrap">
<div id="view-sources">⟪VIEWSOURCES⟫</div>
<div id="view-files" class="hide">⟪VIEWFILES⟫</div>
<div id="results" class="hide"></div>
<div id="treeEmpty" class="empty hide">Nothing matches these filters.</div>
</main>
<footer class="wrap">
 Generated ⟪DATE⟫ · rebuild with <code>make materials</code>. Disposable view — never the source of truth.<br>
 Local file links are relative to this page: keep <code>INDEX.html</code> inside <code>materials/</code> or they break.<br>
 <kbd>/</kbd> or <kbd>⌘K</kbd> search · <kbd>↑↓</kbd> move · <kbd>⏎</kbd> open ·
 <kbd>⌘⏎</kbd> new tab · <kbd>Esc</kbd> clear
</footer>
<script>
const LEAVES=⟪LEAVES⟫;
const $=id=>document.getElementById(id);
const q=$('q'), vs=$('view-sources'), vf=$('view-files'), res=$('results'),
      treeEmpty=$('treeEmpty'), clr=$('clear'), kbd=$('kbd');

let view='sources', types=new Set(), onlineOnly=false, showSupport=false, hideArchived=false;
let terms=[], hits=[], shown=0, sel=-1;
const PAGE_SIZE=200;

/* cache the DOM node lists once — the old build re-queried on every keystroke */
const CACHE={};
function nodes(root){
 const k=root.id;
 if(!CACHE[k]) CACHE[k]={leaves:[...root.querySelectorAll('.leaf')],
                         details:[...root.querySelectorAll('details')],
                         domains:[...root.querySelectorAll('section.domain')]};
 return CACHE[k];
}

function passes(k,t,sup,arch){
 if(types.size&&!types.has(t))return false;
 if(onlineOnly&&k==='local')return false;
 if(!showSupport&&sup)return false;
 if(hideArchived&&arch)return false;
 return true;
}
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

/* escape + <mark> every matched term, without corrupting entities */
function hl(text){
 if(!terms.length)return esc(text);
 const low=(text||'').toLowerCase(); const sp=[];
 for(const t of terms){let i=low.indexOf(t);while(i!==-1){sp.push([i,i+t.length]);i=low.indexOf(t,i+1);}}
 if(!sp.length)return esc(text);
 sp.sort((a,b)=>a[0]-b[0]);
 const m=[];
 for(const s of sp){const l=m[m.length-1];
  if(l&&s[0]<=l[1])l[1]=Math.max(l[1],s[1]);else m.push([s[0],s[1]]);}
 let out='',pos=0;
 for(const [a,b] of m){out+=esc(text.slice(pos,a))+'<mark>'+esc(text.slice(a,b))+'</mark>';pos=b;}
 return out+esc(text.slice(pos));
}

/* relevance: filename prefix > filename hit > path hit > metadata hit */
function score(L){
 const n=L.n.toLowerCase(), c=(L.c||'').toLowerCase();
 let s=0;
 for(const t of terms){
  if(n.startsWith(t))s+=100; else if(n.includes(t))s+=45;
  else if(c.includes(t))s+=12; else s+=2;
 }
 if(L.k==='local')s+=4;
 if(L.a)s-=18;
 if(L.s===1)s-=30;
 return s;
}

function filterTree(root){
 const N=nodes(root); let visible=0;
 for(const f of N.leaves){
  const ok=passes(f.dataset.kind,f.dataset.type,f.dataset.support==='1',f.dataset.archived==='1');
  f.classList.toggle('hide',!ok); if(ok)visible++;
 }
 for(const d of N.details) d.classList.toggle('hide',!d.querySelector('.leaf:not(.hide)'));
 for(const s of N.domains) s.classList.toggle('hide',!s.querySelector('.leaf:not(.hide)'));
 return visible;
}

function rowHTML(L){
 const kind=L.k==='local'?(L.t||'file'):L.k;
 const cls=L.k==='online'?'rk online':L.k==='missing'?'rk missing':'rk';
 const tag=L.h?'a':'span';
 const attrs=L.h?` href="${esc(L.h)}"${L.k==='online'?' target="_blank" rel="noopener"':''}`:'';
 return `<${tag} class="res"${attrs} title="${esc(L.c)}"><span class="rn">${hl(L.n)}</span>`+
        `<span class="rc">${hl(L.c)}</span><span class="${cls}">${esc(kind)}</span></${tag}>`;
}

function paint(){
 const head=`<div class="reshdr"><strong>${hits.length}</strong> match${hits.length===1?'':'es'}`+
   (hits.length>shown?` · showing ${shown}`:'')+`</div>`;
 if(!hits.length){
  res.innerHTML='<div class="empty">No matches.<br>Try fewer or shorter terms — every space-separated word has to match.</div>';
  return;
 }
 let html=head;
 for(let i=0;i<shown;i++) html+=rowHTML(hits[i]);
 if(hits.length>shown) html+=`<button class="more" id="more">Show ${Math.min(PAGE_SIZE,hits.length-shown)} more of ${hits.length-shown}</button>`;
 res.innerHTML=html;
 const more=$('more'); if(more)more.onclick=()=>{shown=Math.min(shown+PAGE_SIZE,hits.length);paint();};
 mark();
}
function rows(){return [...res.querySelectorAll('.res')];}
function mark(){rows().forEach((r,i)=>r.classList.toggle('sel',i===sel));}
function move(d){
 const r=rows(); if(!r.length)return;
 sel=Math.max(0,Math.min(r.length-1,sel+d)); mark();
 r[sel].scrollIntoView({block:'nearest'});
}

function search(){
 const scored=[];
 for(const L of LEAVES){
  if(!passes(L.k,L.t,L.s===1,L.a===1))continue;
  let ok=true; for(const t of terms){if(!L.q.includes(t)){ok=false;break;}}
  if(ok)scored.push([score(L),L]);          /* score once, not per comparison */
 }
 scored.sort((a,b)=>b[0]-a[0]||a[1].n.localeCompare(b[1].n));
 hits=scored.map(p=>p[1]);
 shown=Math.min(PAGE_SIZE,hits.length); sel=-1;
 paint();
}

function update(){
 const raw=q.value.trim();
 terms=raw.toLowerCase().split(/\\s+/).filter(Boolean);
 clr.style.display=raw?'block':'none';
 kbd.style.display=raw?'none':'';
 if(terms.length){
  vs.classList.add('hide'); vf.classList.add('hide'); treeEmpty.classList.add('hide');
  res.classList.remove('hide'); search();
 }else{
  res.classList.add('hide');
  vs.classList.toggle('hide',view!=='sources');
  vf.classList.toggle('hide',view!=='files');
  const n=filterTree(view==='sources'?vs:vf);
  treeEmpty.classList.toggle('hide',n>0);
 }
}
let timer; const debounced=()=>{clearTimeout(timer);timer=setTimeout(update,90);};

function setView(v){
 view=v;
 $('vSources').setAttribute('aria-selected',v==='sources');
 $('vFiles').setAttribute('aria-selected',v==='files');
 update();
}
function toggle(btn,val){btn.setAttribute('aria-pressed',String(val));}

q.addEventListener('input',debounced);
$('vSources').onclick=()=>setView('sources');
$('vFiles').onclick=()=>setView('files');
clr.onclick=()=>{q.value='';update();q.focus();};

/* type chips: multi-select ("All" clears the set) */
const typeChips=[...document.querySelectorAll('.chip[data-type]')];
for(const c of typeChips) c.addEventListener('click',()=>{
 const t=c.dataset.type;
 if(t==='*') types.clear();
 else {types.has(t)?types.delete(t):types.add(t);}
 for(const x of typeChips){
  toggle(x, x.dataset.type==='*' ? types.size===0 : types.has(x.dataset.type));
 }
 update();
});
$('onlineChip').addEventListener('click',e=>{
 onlineOnly=!onlineOnly; toggle(e.currentTarget,onlineOnly);
 if(onlineOnly&&view==='files')setView('sources');else update();
});
$('supportChip').addEventListener('click',e=>{
 showSupport=!showSupport; toggle(e.currentTarget,showSupport); update();
});
$('archChip').addEventListener('click',e=>{
 hideArchived=!hideArchived; toggle(e.currentTarget,hideArchived); update();
});
$('expand').onclick=()=>{const r=view==='sources'?vs:vf;
 for(const d of nodes(r).details) d.open=true;};
$('collapse').onclick=()=>{const r=view==='sources'?vs:vf;
 for(const d of nodes(r).details) d.open=false;
 for(const s of nodes(r).domains){const d=s.querySelector(':scope > details'); if(d)d.open=true;}
 window.scrollTo({top:0});};

document.addEventListener('keydown',e=>{
 const typing=/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
 if((e.key==='k'&&(e.metaKey||e.ctrlKey))||(e.key==='/'&&!typing)){
  e.preventDefault(); q.focus(); q.select(); return;
 }
 if(e.key==='Escape'){ if(q.value){q.value='';update();} q.blur(); return; }
 if(res.classList.contains('hide'))return;
 if(e.key==='ArrowDown'){e.preventDefault();move(1);}
 else if(e.key==='ArrowUp'){e.preventDefault();move(-1);}
 else if(e.key==='Enter'&&sel>=0){
  const r=rows()[sel]; if(!r||r.tagName!=='A')return;
  e.preventDefault();
  if(e.metaKey||e.ctrlKey)window.open(r.href,'_blank','noopener');else r.click();
 }
});
if(navigator.platform&&/Mac/.test(navigator.platform))kbd.textContent='⌘K';
update();
</script>
</body></html>
"""


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
            stale.unlink()
            print("  removed stale materials/INDEX.html (retired 2026-08-03)")
    (MATERIALS / "README.md").write_text(
        build_readme(modules_by_domain, library_local_by_domain, online_by_domain,
                     missing_by_domain, roots_by_name, len(local_ids), n_online,
                     n_missing, ncontent, nsupport, total), encoding="utf-8")
    files_txt = build_files_listing(roots)
    (MATERIALS / "FILES.txt").write_text(files_txt, encoding="utf-8")
    print(f"  wrote materials/README.md")
    print(f"  wrote materials/FILES.txt  ({files_txt.count(chr(10)) - 7} unregistered files)")
    print(f"  {summary}")


if __name__ == "__main__":
    main()
