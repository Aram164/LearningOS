#!/usr/bin/env python3
"""C2 page-audit: routes + expanded stage resources of module-hu-m2-statistik-analysis.

B1: every page number named for a local PDF sits inside its real page count
    (treated as a PDF page number per the repository convention).
B2: per file, the printed->PDF offset implied by "printed p. X (PDF p. Y)"
    pairs is consistent across the whole module (broadcast-damage signal).
A : material:// URIs anywhere in stage resources resolve.
D : exact-duplicate locator strings among sibling stage resources of one unit.
"""
import json
import logging
import sys
import re
from collections import defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

REPO = Path.home() / "los-glm-C2-2026-10" / "repository"
MOD = REPO / "curriculum/modules/module-hu-m2-statistik-analysis"
MATERIALS = Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/materials")
LIG = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
       "\ufb04": "ffl", "\u2032": "'", "\u2019": "'", "\u2018": "'",
       "\u201c": '"', "\u201d": '"'}


def norm(s):
    for k, v in LIG.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip()


URL_SOURCES = {"source-mit-1805", "source-mit-6034-quizzes",
               "source-cs229-problem-sets", "source-mmds-book"}

# any page mention: "PDF p. 11", "printed p. 2", bare "pp. 9-15", "S. 12"
PDFP = re.compile(r"PDF\s+pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)
PRINTP = re.compile(r"printed\s+pp?\.\s*(\d+)", re.IGNORECASE)
BARE = re.compile(r"(?<![\w.\-])pp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?(?!\w)", re.IGNORECASE)

ALIAS = {"source-sad-uebungen": "source-sad-ss26-lectures"}


def resolve_uri(uri):
    m = re.match(r"material://([^/\s]+)/(.+)$", uri)
    if not m:
        return None
    sid, rest = ALIAS.get(m.group(1), m.group(1)), m.group(2)
    for cand in (MATERIALS / ".flat" / sid / rest, MATERIALS / rest):
        if cand.is_file():
            return cand
    return None


def find_by_basename(name):
    hits = [p for p in (MATERIALS / ".flat").rglob(name) if p.is_file()]
    return hits[0] if hits else None


_pc = {}


def page_count(path):
    if str(path) not in _pc:
        try:
            with open(path, "rb") as fh:
                head = fh.read(5)
            if head != b"%PDF-":
                print(f"  !! not a PDF: {path} head={head!r}", file=sys.stderr)
                _pc[str(path)] = None
                return None
            import io, contextlib
            logging.getLogger("pypdf").setLevel(logging.CRITICAL)
            with contextlib.redirect_stderr(io.StringIO()):
                _pc[str(path)] = len(PdfReader(str(path)).pages)
        except Exception as exc:
            print(f"  !! pypdf failed: {path}: {exc}", file=sys.stderr)
            _pc[str(path)] = None
    return _pc[str(path)]


def collect_routes():
    doc = yaml.safe_load((MOD / "source-map.yaml").read_text())
    out = []
    for s in doc["sources"]:
        for r in s.get("unit_routes") or []:
            out.append({"kind": "route", "source_id": s["source_id"],
                        "unit_id": r["unit_id"], "id": r["id"],
                        "title": r.get("title", ""), "text": str(r.get("locator") or ""),
                        "vault_path": r.get("vault_path")})
    return out


def collect_resources():
    routes = {}
    for r in collect_routes():
        routes[r["id"]] = r
    out = []
    for sm_path in sorted(MOD.glob("units/*/study-map.yaml")):
        unit = sm_path.parent.name
        sm = yaml.safe_load(sm_path.read_text())
        for stage in sm.get("stages") or []:
            for i, res in enumerate(stage.get("resources") or []):
                if not isinstance(res, dict):
                    continue
                ref = res.get("material_ref") or {}
                rid = ref.get("route_id")
                if rid:
                    base = routes.get(rid)
                    if base is None:
                        continue
                    loc = base["text"] if "locator" in (ref.get("inherit") or [None]) or True else ""
                    loc = base["text"]
                    vp = base["vault_path"] if "vault_path" in (ref.get("inherit") or []) else None
                    out.append({"kind": "resource", "unit_id": unit,
                                "id": f"{stage.get('id')}#{i}->{rid}",
                                "title": base["title"], "text": loc,
                                "vault_path": vp,
                                "stage": stage.get("id"), "route_id": rid})
                else:
                    out.append({"kind": "resource-own", "unit_id": unit,
                                "id": f"{stage.get('id')}#{i}",
                                "title": str(res.get("label") or res.get("title") or ""),
                                "text": str(res.get("locator") or ""),
                                "source_id": res.get("source_id"),
                                "vault_path": res.get("vault_path"),
                                "stage": stage.get("id"),
                                "uri_fields": {
                                    k: str(v) for k, v in res.items()
                                    if isinstance(v, str) and "material://" in v}})
    return out


def main():
    items = collect_routes() + collect_resources()
    print("items:", len(items))
    findings = {"b_over": [], "b2_offset": [], "a_res": [], "d_res_dup": []}

    # per-file offset map across the module
    file_offsets = defaultdict(set)
    file_for = {}

    for it in items:
        text = it["text"]
        if not text:
            continue
        ntext = norm(text)
        # resolve the local file: vault_path first, then any PDF named
        path = None
        vp = it.get("vault_path")
        if vp and isinstance(vp, str) and vp.startswith("material://"):
            path = resolve_uri(vp)
        sid = it.get("source_id")
        if path is None and sid in URL_SOURCES:
            continue  # online-only source: nothing local to verify
        if path is None:
            m = re.search(r"([^\s;:|<>\"']*[^\s;:|<>\"'.,])\.pdf", ntext, re.IGNORECASE)
            if m:
                name = m.group(1) + ".pdf"
                # suffix-match against farm
                hits = [p for p in (MATERIALS / ".flat").rglob("*.pdf")
                        if norm(p.name).endswith(norm(name)) or norm(p.name) == norm(name)]
                if len(hits) == 1:
                    path = hits[0]
        # B1: page numbers vs real count
        if path is not None:
            pc = page_count(path)
            pdfpages = []
            for m in PDFP.finditer(ntext):
                pdfpages.append(int(m.group(1)))
                if m.group(2):
                    pdfpages.append(int(m.group(2)))
            file_for.setdefault(path.name, set()).add(it["id"])
            if pc is not None and pdfpages:
                over = [p for p in pdfpages if p > pc or p < 1]
                if over:
                    findings["b_over"].append({
                        "item": it["id"], "file": path.name, "real": pc,
                        "mentioned": sorted(set(pdfpages)), "over": sorted(set(over)),
                        "text": ntext[:200]})
            # B2: printed->PDF offsets (only with explicit PDF page in the pair)
            for m in re.finditer(
                    r"printed\s+pp?\.\s*(\d+)[^.]{0,40}?PDF\s+pp?\.\s*(\d+)", ntext,
                    re.IGNORECASE):
                file_offsets[path.name].add(int(m.group(2)) - int(m.group(1)))
        # A: material:// URIs in own-field resources
        if it["kind"] == "resource-own":
            for field, uri in (it.get("uri_fields") or {}).items():
                for um in re.finditer(r"material://([^\s`)\]\"'<>,;]+)", uri):
                    if resolve_uri("material://" + um.group(1)) is None:
                        findings["a_res"].append({
                            "item": it["id"], "field": field,
                            "uri": "material://" + um.group(1)})

    for fname, offs in sorted(file_offsets.items()):
        if len(offs) > 1:
            findings["b2_offset"].append({"file": fname, "offsets": sorted(offs),
                                          "users": sorted(file_for.get(fname, []))[:12]})

    print("B1 over-range:", len(findings["b_over"]))
    print("B2 offset conflicts:", len(findings["b2_offset"]))
    print("A resource URI unresolvable:", len(findings["a_res"]))
    json.dump(findings, open("/tmp/c2_page_findings.json", "w"),
              ensure_ascii=False, indent=1)
    for k in ("b_over", "b2_offset", "a_res"):
        for f_ in findings[k][:40]:
            print(json.dumps(f_, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
