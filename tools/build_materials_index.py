#!/usr/bin/env python3
"""Build a human-browsable index of the materials tree.

Emits two disposable navigation aids into ``LearningOS/materials/``:

* ``INDEX.html`` — a self-contained, searchable page. Open it in a browser
  (double-click in Finder) and every material is one search away; each file
  links to the real file on disk via a relative path, so a click opens it.
* ``README.md`` — a plain-text / grep-able map of the same content.

Neither is canonical. They are pure VIEWS over what is physically on disk plus
the human titles in ``sources/`` — nothing here is a source of truth, and both
files can be deleted and rebuilt at any time:

    python tools/build_materials_index.py

No third-party deps beyond PyYAML (already a repo dependency). Folders are
labelled with their registered source title when a ``.flat/source-*`` symlink
points at them; everything else is shown by folder name. Files are never moved,
so ``material://`` URIs, the source registry and the .flat farm keep working.
"""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import yaml

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent                      # LearningOS/repository
MATERIALS = REPO.parent / "materials"    # LearningOS/materials
SOURCES = REPO / "sources"

SKIP_DIRS = {".flat", ".git", "__pycache__"}
SKIP_FILES = {".DS_Store", "INDEX.html", "README.md"}

# Friendly names + one-line hints for the top-level buckets.
DOMAIN_LABELS = {
    "ML": ("Machine Learning", "AML + AMLS course materials (slides, exams, papers, notes)"),
    "Math": ("Mathematics", "Analysis (M2.1) + Statistik & Datenanalyse — Skript, slides, drill"),
    "CS-Theory": ("CS Theory", "Algo 2 / AlgoDat II — practice exams"),
    "Programming": ("Programming", "Python, Rust, Git working references"),
    "Books": ("Books — reference library", "Textbooks grouped by field (analysis, stats, ml, algorithms)"),
    "Degree": ("Degree admin", "StuPO / regulations"),
    "Foundations": ("Foundations archive", "Undergrad / general reference — NOT registered sources, browse only"),
}
DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming", "Books", "Degree", "Foundations"]


def load_titles() -> dict[str, dict]:
    """id -> {title, type, url} from every YAML under sources/."""
    out: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("id") and node.get("title"):
                sid = node["id"]
                out.setdefault(sid, {
                    "title": node.get("title"),
                    "type": node.get("type", ""),
                    "url": node.get("url") or node.get("homepage") or "",
                })
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for yf in SOURCES.rglob("*.yaml"):
        try:
            walk(yaml.safe_load(yf.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001 - a bad file must not kill the map
            print(f"  ! skipped {yf.name}: {exc}")
    return out


def load_flat_map() -> dict[str, str]:
    """materials-relative dir path -> source-id, from the .flat symlink farm."""
    flat = MATERIALS / ".flat"
    out: dict[str, str] = {}
    if not flat.is_dir():
        return out
    for link in flat.iterdir():
        if not link.is_symlink():
            continue
        target = os.readlink(link)
        resolved = (flat / target).resolve()
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
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= step
    return f"{n:.1f} TB"


def build_tree(titles, flatmap):
    """Nested dict describing the materials tree, annotated with source titles."""

    def node_for(path: Path):
        rel = str(path.relative_to(MATERIALS))
        sid = flatmap.get(rel)
        meta = titles.get(sid, {}) if sid else {}
        node = {
            "name": path.name,
            "rel": rel,
            "source_id": sid,
            "title": meta.get("title"),
            "stype": meta.get("type", ""),
            "url": meta.get("url", ""),
            "dirs": [],
            "files": [],
            "nfiles": 0,
            "bytes": 0,
        }
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        for e in entries:
            if e.name.startswith(".") or e.name in SKIP_DIRS or e.name in SKIP_FILES:
                continue
            if e.is_dir():
                child = node_for(e)
                node["dirs"].append(child)
                node["nfiles"] += child["nfiles"]
                node["bytes"] += child["bytes"]
            elif e.is_file():
                try:
                    size = e.stat().st_size
                except OSError:
                    size = 0
                node["files"].append({
                    "name": e.name,
                    "rel": str(e.relative_to(MATERIALS)),
                    "ext": e.suffix.lower().lstrip("."),
                    "size": size,
                })
                node["nfiles"] += 1
                node["bytes"] += size
        return node

    roots = []
    for name in DOMAIN_ORDER:
        p = MATERIALS / name
        if p.is_dir():
            roots.append(node_for(p))
    # any bucket not in the known order
    for p in sorted(MATERIALS.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name not in DOMAIN_ORDER and not p.name.startswith(".") \
                and p.name not in SKIP_DIRS:
            roots.append(node_for(p))
    return roots


# ---------------------------------------------------------------- HTML render

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def href_for(rel: str) -> str:
    return "/".join(quote(part) for part in rel.split("/"))


def searchable(*parts) -> str:
    return esc(" ".join(p for p in parts if p).lower())


def render_files(files, source_title, stype):
    rows = []
    for f in files:
        s = searchable(f["name"], source_title or "", f["rel"])
        badge = f'<span class="ext ext-{esc(f["ext"] or "x")}">{esc(f["ext"] or "file")}</span>'
        rows.append(
            f'<a class="file" data-s="{s}" data-type="{esc(stype or "unregistered")}" '
            f'href="{href_for(f["rel"])}" title="{esc(f["rel"])}">'
            f'{badge}<span class="fn">{esc(f["name"])}</span>'
            f'<span class="sz">{human_size(f["size"])}</span></a>'
        )
    return "".join(rows)


def render_dir(node, depth=0):
    is_source = bool(node["source_id"])
    if is_source:
        head = (
            f'<span class="title">{esc(node["title"] or node["name"])}</span>'
            f'<span class="slug">{esc(node["name"])}</span>'
        )
        if node["stype"]:
            head += f'<span class="badge">{esc(node["stype"])}</span>'
    else:
        head = f'<span class="fname">{esc(node["name"])}</span>'
    head += f'<span class="count">{node["nfiles"]}</span>'

    inner = []
    for d in node["dirs"]:
        inner.append(render_dir(d, depth + 1))
    inner.append(render_files(node["files"], node["title"], node["stype"]))

    ds = searchable(node["title"] or "", node["name"], node["rel"])
    open_attr = " open" if depth == 0 else ""
    cls = "dir source" if is_source else "dir"
    return (
        f'<details class="{cls}" data-s="{ds}"{open_attr}>'
        f'<summary>{head}</summary>'
        f'<div class="body">{"".join(inner)}</div>'
        f'</details>'
    )


def render_domain(node):
    label, hint = DOMAIN_LABELS.get(node["name"], (node["name"], ""))
    inner = []
    for d in node["dirs"]:
        inner.append(render_dir(d, 1))
    inner.append(render_files(node["files"], node["title"], node["stype"]))
    ds = searchable(label, node["name"])
    return (
        f'<section class="domain" data-s="{ds}">'
        f'<details open><summary>'
        f'<span class="dlabel">{esc(label)}</span>'
        f'<span class="dhint">{esc(hint)}</span>'
        f'<span class="count">{node["nfiles"]} files · {human_size(node["bytes"])}</span>'
        f'</summary><div class="body">{"".join(inner)}</div></details>'
        f'</section>'
    )


def collect_types(roots):
    types = set()

    def walk(n):
        if n["stype"]:
            types.add(n["stype"])
        for d in n["dirs"]:
            walk(d)
    for r in roots:
        walk(r)
    return sorted(types)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Materials — browse & search</title>
<style>
:root{--bg:#fbfbfa;--card:#fff;--ink:#1c1c1a;--soft:#6b6b66;--line:#e7e6e2;
--accent:#6b5cff;--chip:#f0eff9;--hit:#fff6d6;}
@media(prefers-color-scheme:dark){:root{--bg:#17171a;--card:#1f1f23;--ink:#e9e9ec;
--soft:#9a9aa2;--line:#2c2c31;--accent:#9b8dff;--chip:#26263a;--hit:#3a3410;}}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
padding:16px 22px 12px;z-index:5}
h1{margin:0 0 2px;font-size:19px}
.sub{color:var(--soft);font-size:13px;margin-bottom:11px}
#q{width:100%;padding:11px 13px;font-size:15px;border:1px solid var(--line);
border-radius:10px;background:var(--card);color:var(--ink)}
#q:focus{outline:2px solid var(--accent);border-color:transparent}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.chip{font-size:12px;padding:4px 10px;border-radius:999px;border:1px solid var(--line);
background:var(--card);color:var(--soft);cursor:pointer;user-select:none}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.tools{margin-left:auto;display:flex;gap:6px}
.chiprow{display:flex;align-items:center;gap:6px;margin-top:10px}
main{padding:14px 22px 60px;max-width:1000px}
.domain{margin:0 0 10px}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:8px 0}
details details{border:0;border-top:1px solid var(--line);border-radius:0;margin:0;background:transparent}
summary{cursor:pointer;padding:10px 14px;list-style:none;display:flex;align-items:center;gap:9px;flex-wrap:wrap}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸";color:var(--soft);font-size:11px;transition:transform .12s}
details[open]>summary::before{transform:rotate(90deg)}
.dlabel{font-weight:650;font-size:15px}
.dhint{color:var(--soft);font-size:12px}
.title{font-weight:600}
.slug{color:var(--soft);font-size:12px;font-family:ui-monospace,Menlo,monospace}
.fname{font-weight:550}
.badge{font-size:11px;background:var(--chip);color:var(--accent);padding:1px 8px;border-radius:999px}
.count{margin-left:auto;color:var(--soft);font-size:12px;white-space:nowrap}
.body{padding:2px 8px 8px 20px}
details details .body{padding-left:16px}
a.file{display:flex;align-items:center;gap:9px;padding:6px 10px;border-radius:8px;
text-decoration:none;color:var(--ink)}
a.file:hover{background:var(--chip)}
.fn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sz{margin-left:auto;color:var(--soft);font-size:12px;white-space:nowrap}
.ext{font-size:10px;text-transform:uppercase;letter-spacing:.03em;color:#fff;
background:var(--soft);border-radius:4px;padding:1px 5px;min-width:34px;text-align:center}
.ext-pdf{background:#c0392b}.ext-epub{background:#8e44ad}.ext-html{background:#d35400}
.ext-md{background:#2c3e50}.ext-zip{background:#7f8c8d}.ext-ipynb{background:#e67e22}
.ext-mp4,.ext-mkv,.ext-mov{background:#16a085}
mark{background:var(--hit);color:inherit;border-radius:2px}
.hide{display:none!important}
.empty{color:var(--soft);padding:20px;text-align:center}
button.t{font-size:12px;padding:4px 10px;border-radius:8px;border:1px solid var(--line);
background:var(--card);color:var(--soft);cursor:pointer}
</style></head>
<body>
<header>
<h1>Materials library</h1>
<div class="sub">⟪SUMMARY⟫ · rebuild with <code>python tools/build_materials_index.py</code> · generated ⟪DATE⟫</div>
<input id="q" placeholder="Search titles, filenames, folders…  (e.g. islp, klausur, logistic, rust)" autofocus>
<div class="chiprow"><span class="chip on" data-type="*">All</span>⟪CHIPS⟫
<span class="tools"><button class="t" id="expand">Expand all</button><button class="t" id="collapse">Collapse all</button></span></div>
</header>
<main id="tree">⟪TREE⟫<div class="empty hide" id="nohits">No materials match your search.</div></main>
<script>
const q=document.getElementById('q'), tree=document.getElementById('tree');
const files=[...document.querySelectorAll('a.file')];
const dets=[...document.querySelectorAll('#tree details')];
const secs=[...document.querySelectorAll('section.domain')];
let typeFilter='*';
function apply(){
 const s=q.value.trim().toLowerCase();
 files.forEach(f=>{
   const okT=typeFilter==='*'||f.dataset.type===typeFilter;
   const okS=!s||f.dataset.s.includes(s);
   f.classList.toggle('hide',!(okT&&okS));
 });
 dets.forEach(d=>{
   const hasFile=d.querySelector('a.file:not(.hide)');
   d.classList.toggle('hide',!hasFile);
   if(s&&hasFile)d.open=true;
 });
 secs.forEach(sec=>{
   const vis=sec.querySelector('a.file:not(.hide)');
   sec.classList.toggle('hide',!vis);
 });
 document.getElementById('nohits').classList.toggle('hide',!!document.querySelector('a.file:not(.hide)'));
}
q.addEventListener('input',apply);
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{
 document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
 c.classList.add('on');typeFilter=c.dataset.type;apply();
}));
document.getElementById('expand').onclick=()=>dets.forEach(d=>d.open=true);
document.getElementById('collapse').onclick=()=>dets.forEach(d=>{if(!d.closest('section')||d.parentElement.id!=='tree')d.open=false;});
</script>
</body></html>
"""


def build_readme(roots, titles, nsrc, nfiles, total):
    lines = [
        "# Materials — map",
        "",
        f"> Plain-text companion to **INDEX.html** (open that in a browser to search & click). ",
        f"> {nsrc} registered sources · {nfiles} files · {human_size(total)}. ",
        "> Generated view — rebuild with `python tools/build_materials_index.py`. ",
        "> Files are never moved by this tool; `material://` URIs and the registry are unaffected.",
        "",
    ]

    def walk(node, depth):
        pad = "  " * depth
        if node["source_id"]:
            lines.append(f"{pad}- **{node['title'] or node['name']}** "
                         f"(`{node['rel']}`) — {node['nfiles']} file(s)"
                         + (f" · {node['stype']}" if node["stype"] else ""))
        else:
            if node["dirs"] or node["files"]:
                lines.append(f"{pad}- {node['name']}/")
        for d in node["dirs"]:
            walk(d, depth + 1)

    for r in roots:
        label, hint = DOMAIN_LABELS.get(r["name"], (r["name"], ""))
        lines.append(f"\n## {label}")
        if hint:
            lines.append(f"*{hint}*  \n")
        for d in r["dirs"]:
            walk(d, 0)
        if r["files"]:
            for f in r["files"]:
                lines.append(f"- {f['name']} (`{f['rel']}`)")
    lines.append("")
    return "\n".join(lines)


def main():
    if not MATERIALS.is_dir():
        raise SystemExit(f"materials not found at {MATERIALS}")
    titles = load_titles()
    flatmap = load_flat_map()
    roots = build_tree(titles, flatmap)

    nfiles = sum(r["nfiles"] for r in roots)
    total = sum(r["bytes"] for r in roots)
    nsrc = len(flatmap)
    types = collect_types(roots)

    chips = "".join(f'<span class="chip" data-type="{esc(t)}">{esc(t)}</span>' for t in types)
    summary = f"{nsrc} registered sources · {nfiles} files · {human_size(total)}"
    tree_html = "".join(render_domain(r) for r in roots)

    page = (PAGE
            .replace("⟪SUMMARY⟫", esc(summary))
            .replace("⟪DATE⟫", datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("⟪CHIPS⟫", chips)
            .replace("⟪TREE⟫", tree_html))

    (MATERIALS / "INDEX.html").write_text(page, encoding="utf-8")
    (MATERIALS / "README.md").write_text(
        build_readme(roots, titles, nsrc, nfiles, total), encoding="utf-8")
    print(f"  wrote materials/INDEX.html  ({len(page)//1024} KB)")
    print(f"  wrote materials/README.md")
    print(f"  {summary}")


if __name__ == "__main__":
    main()
